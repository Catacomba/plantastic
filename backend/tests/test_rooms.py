import asyncio
import json

import pytest

from plantastic.server.protocol import GameError, parse_command
from plantastic.server.rooms import MAX_STEP, Mode, Room, SandboxMode

PLAYER = "player-1"
SPECIES_IDS = ["straight-vine", "zigzag", "spiral", "fern", "wanderer", "hydra", "burst", "custom"]


def command(**fields):
    return parse_command(json.dumps(fields))


def plant(q, r, speed="1"):
    return command(type="plant", q=q, r=r, species="straight-vine", speed=speed)


def paused_room(**kwargs) -> Room:
    room = Room(SandboxMode(), PLAYER, seed=1, **kwargs)
    room.handle(PLAYER, command(type="pause"))
    return room


def rejected(room: Room, cmd) -> str:
    before = (room.board.tick, room.board.cells_snapshot(), room.board.tips_snapshot(), room.clock)
    with pytest.raises(GameError) as error:
        room.handle(PLAYER, cmd)
    assert (room.board.tick, room.board.cells_snapshot(), room.board.tips_snapshot(), room.clock) == before
    return error.value.code


class LookOnlyMode(Mode):
    name = "look-only"
    starts_running = False

    def permits(self, player, command_type):
        return command_type == "pause"


def test_welcome_describes_the_room():
    room = Room(SandboxMode(), PLAYER, seed=42)
    welcome = room.welcome()

    assert welcome["type"] == "welcome"
    assert welcome["mode"] == "sandbox"
    assert welcome["seed"] == 42
    assert welcome["clock"] == "running"
    assert welcome["cells"] == [] and welcome["tips"] == []
    assert welcome["plants"] == []
    assert [species["id"] for species in welcome["species"]] == SPECIES_IDS
    assert welcome["species"][0] == {
        "id": "straight-vine",
        "name": "Straight vine",
        "default_speed": "1",
        "persistence": 0,
        "settings": [],
    }
    persistence = {species["id"]: species["persistence"] for species in welcome["species"]}
    assert persistence == {
        "straight-vine": 0,
        "zigzag": 30,
        "spiral": 30,
        "fern": 0,
        "wanderer": 60,
        "hydra": 80,
        "burst": 30,
        "custom": None,
    }


def test_mode_rejects_commands_it_does_not_permit():
    room = Room(LookOnlyMode(), PLAYER, seed=1)
    assert rejected(room, plant(0, 0)) == "not_permitted"
    assert rejected(room, command(type="step", n=1)) == "not_permitted"
    room.handle(PLAYER, command(type="pause"))


def test_plant_records_the_owner_and_returns_an_update():
    room = paused_room()
    (update,) = room.handle(PLAYER, plant(2, 3))

    assert update["type"] == "update"
    assert update["added"] == [{"q": 2, "r": 3, "plant": 1, "kind": "root", "parent": None}]
    assert update["plants"] == [{"id": 1, "species": "straight-vine", "speed": "1", "settings": None, "persistence": 0}]
    assert len(update["tips"]) == 1
    assert room.board.plants[1].owner == PLAYER


@pytest.mark.parametrize(
    "cmd, code",
    [
        (plant(0, 0), "occupied"),
        (plant(5, 5, speed="0"), "bad_speed"),
        (command(type="plant", q=5, r=5, species="triffid", speed="1"), "unknown_species"),
        (command(type="cut", q=9, r=9), "nothing_to_cut"),
    ],
)
def test_simulation_rejections_become_errors(cmd, code):
    room = paused_room()
    room.handle(PLAYER, plant(0, 0))
    assert rejected(room, cmd) == code


def test_pause_and_resume_report_the_clock():
    room = Room(SandboxMode(), PLAYER, seed=1)
    assert room.clock == "running"
    (update,) = room.handle(PLAYER, command(type="pause"))
    assert update["clock"] == "paused" and not room.running
    (update,) = room.handle(PLAYER, command(type="resume"))
    assert update["clock"] == "running" and room.running


def test_step_grows_exactly_n_iterations_and_stays_paused():
    room = paused_room()
    room.handle(PLAYER, plant(0, 0))
    room.handle(PLAYER, command(type="step", n=10))
    (update,) = room.handle(PLAYER, command(type="step", n=25))

    assert update["tick"] == 35
    assert len(update["added"]) == 25
    assert len(room.board.cells) == 36
    assert update["clock"] == "paused"


def test_step_while_running_is_rejected():
    room = Room(SandboxMode(), PLAYER, seed=1)
    assert rejected(room, command(type="step", n=5)) == "not_paused"


@pytest.mark.parametrize("count", [0, -3, 2.5, MAX_STEP + 1])
def test_step_out_of_range_is_rejected(count):
    room = paused_room()
    room.handle(PLAYER, plant(0, 0))
    assert rejected(room, command(type="step", n=count)) == "bad_step"


def test_cut_while_paused_applies_without_a_tick():
    room = paused_room()
    room.handle(PLAYER, plant(0, 0))
    room.handle(PLAYER, command(type="step", n=6))
    tip = room.board.tips_snapshot()[0]
    (update,) = room.handle(PLAYER, command(type="cut", q=tip["q"], r=tip["r"]))

    assert update["tick"] == 6
    assert [cell["kind"] for cell in update["changed"]] == ["stump"]
    assert len(update["tips"]) == 2
    assert update["clock"] == "paused"


def test_full_board_pauses_a_step_and_sends_a_notice():
    room = paused_room(max_cells=4)
    room.handle(PLAYER, plant(0, 0))
    update, notice = room.handle(PLAYER, command(type="step", n=50))

    assert len(room.board.cells) == 4
    assert update["clock"] == "paused"
    assert notice == {"type": "notice", "code": "board_full", "message": notice["message"]}


def run_clock_for(room: Room, script) -> list[dict]:
    """Run the room clock while ``script`` (a coroutine function) drives the room."""
    sent: list[dict] = []

    async def broadcast(message):
        sent.append(message)

    async def main():
        clock = asyncio.create_task(room.run_clock(broadcast))
        try:
            await script()
        finally:
            clock.cancel()

    asyncio.run(main())
    return sent


def test_clock_ticks_while_running_and_stops_while_paused():
    room = Room(SandboxMode(), PLAYER, seed=1, tick_interval=0.01)
    room.handle(PLAYER, plant(0, 0))
    ticks = {}

    async def script():
        await asyncio.sleep(0.2)
        room.handle(PLAYER, command(type="pause"))
        ticks["at_pause"] = room.board.tick
        await asyncio.sleep(0.15)
        ticks["after_pause"] = room.board.tick
        room.handle(PLAYER, command(type="resume"))
        await asyncio.sleep(0.2)
        ticks["after_resume"] = room.board.tick

    sent = run_clock_for(room, script)

    assert ticks["at_pause"] >= 3
    assert ticks["after_pause"] == ticks["at_pause"]
    assert ticks["after_resume"] > ticks["after_pause"]
    assert [message["tick"] for message in sent] == list(range(1, ticks["after_resume"] + 1))
    assert len(room.board.cells) == room.board.tick + 1


def test_clock_pauses_and_notifies_when_the_board_fills():
    room = Room(SandboxMode(), PLAYER, seed=1, tick_interval=0.01, max_cells=4)
    room.handle(PLAYER, plant(0, 0))

    async def script():
        await asyncio.sleep(0.3)

    sent = run_clock_for(room, script)

    assert not room.running
    assert len(room.board.cells) == 4
    assert sent[-1]["type"] == "notice" and sent[-1]["code"] == "board_full"
    assert sent[-2]["type"] == "update" and sent[-2]["clock"] == "paused"
    assert room.board.tick == 4


def two_vine_room(running: bool) -> Room:
    """A room with two vines grown 6 cells from roots far enough apart never to meet."""
    room = paused_room()
    room.handle(PLAYER, plant(0, 0))
    room.handle(PLAYER, plant(0, 40))
    room.handle(PLAYER, command(type="step", n=6))
    if running:
        room.handle(PLAYER, command(type="resume"))
    return room


def slice_across(room: Room) -> list:
    """A path that crosses the third cell of every vine, with empty hexes in between."""
    segments = [cell for cell in room.board.cells.values() if cell.kind == "segment"]
    targets = []
    for plant_id in (1, 2):
        vine = [cell.hex for cell in segments if cell.plant_id == plant_id]
        targets.append(list(vine[2]))
    return [targets[0], [50, 50], [51, 50], targets[1]]


@pytest.mark.parametrize("running", [True, False])
def test_slice_applies_in_one_update_and_leaves_the_clock_alone(running):
    room = two_vine_room(running)
    path = slice_across(room)
    (update,) = room.handle(PLAYER, command(type="slice", hexes=path))

    assert update["type"] == "update"
    assert update["tick"] == 6
    assert update["clock"] == ("running" if running else "paused")
    assert sorted((cell["q"], cell["r"]) for cell in update["changed"]) == sorted(
        [tuple(path[0]), tuple(path[3])]
    )
    assert all(cell["kind"] == "stump" for cell in update["changed"])
    assert len(update["removed"]) == 6
    assert len(update["tips"]) == 4


def test_slice_that_cuts_nothing_is_not_an_error():
    room = two_vine_room(running=False)
    before = room.board.cells_snapshot()
    (update,) = room.handle(PLAYER, command(type="slice", hexes=[[50, 50], [0, 0], [51, 50]]))

    assert update["type"] == "update"
    assert update["added"] == update["changed"] == update["removed"] == []
    assert room.board.cells_snapshot() == before


def test_mode_can_forbid_slicing():
    room = Room(LookOnlyMode(), PLAYER, seed=1)
    assert rejected(room, command(type="slice", hexes=[[0, 0]])) == "not_permitted"


CUSTOM_SETTINGS = {
    "branch_chance": 40,
    "branch_min": 1,
    "branch_max": 2,
    "calm_min": 1,
    "calm_max": 8,
    "turn_chance": 15,
    "persistence": 70,
    "cut_response": "regrow",
}


def plant_custom(q, r, **changes):
    return command(type="plant", q=q, r=r, species="custom", speed="1", settings={**CUSTOM_SETTINGS, **changes})


def test_welcome_describes_the_custom_species_settings():
    room = Room(SandboxMode(), PLAYER, seed=1)
    custom = room.welcome()["species"][-1]

    assert custom["id"] == "custom"
    assert [setting["id"] for setting in custom["settings"]] == list(CUSTOM_SETTINGS)
    for setting in custom["settings"]:
        assert {"id", "label", "kind", "default"} <= set(setting)
        assert ("choices" in setting) == (setting["kind"] == "choice")
        assert ("min" in setting and "max" in setting) == (setting["kind"] != "choice")
    assert all(species["settings"] == [] for species in room.welcome()["species"][:-1])


def test_custom_seed_is_planted_with_its_settings():
    room = paused_room()
    (update,) = room.handle(PLAYER, plant_custom(0, 0))

    assert update["plants"] == [
        {"id": 1, "species": "custom", "speed": "1", "settings": CUSTOM_SETTINGS, "persistence": 70}
    ]
    assert room.board.plants[1].settings == CUSTOM_SETTINGS
    assert room.welcome()["plants"] == update["plants"]


@pytest.mark.parametrize(
    "cmd",
    [
        plant_custom(5, 5, branch_chance=150),
        plant_custom(5, 5, branch_min=3, branch_max=1),
        command(type="plant", q=5, r=5, species="custom", speed="1"),
        command(type="plant", q=5, r=5, species="straight-vine", speed="1", settings=CUSTOM_SETTINGS),
    ],
)
def test_invalid_settings_are_rejected_with_bad_settings(cmd):
    room = paused_room()
    room.handle(PLAYER, plant(0, 0))
    assert rejected(room, cmd) == "bad_settings"
    assert len(room.board.plants) == 1


def test_bad_settings_message_names_the_problem():
    room = paused_room()
    with pytest.raises(GameError) as error:
        room.handle(PLAYER, plant_custom(0, 0, branch_chance=150))
    assert error.value.message == "Branch chance % must be from 0 to 100."


def test_updates_carry_only_newly_created_plants():
    room = paused_room()
    room.handle(PLAYER, plant(0, 0))
    (grow,) = room.handle(PLAYER, command(type="step", n=3))
    assert grow["plants"] == []
    (second,) = room.handle(PLAYER, plant_custom(0, 20))
    assert [details["id"] for details in second["plants"]] == [2]


def test_welcome_reports_the_time_available_per_iteration():
    assert Room(SandboxMode(), PLAYER, seed=1).welcome()["tick_ms"] == 500
    assert Room(SandboxMode(), PLAYER, seed=1, tick_interval=0.02).welcome()["tick_ms"] == 20


def test_clock_tick_reports_one_iteration_of_cost():
    room = paused_room()
    room.handle(PLAYER, plant(0, 0))
    (update,) = room.tick()

    assert update["stats"]["iterations"] == 1
    assert update["stats"]["visits"] == 1
    assert isinstance(update["stats"]["step_ms"], float) and update["stats"]["step_ms"] >= 0


def test_grow_reports_the_whole_batch():
    room = paused_room()
    room.handle(PLAYER, plant(0, 0, speed="2"))
    (update,) = room.handle(PLAYER, command(type="step", n=25))

    assert update["stats"]["iterations"] == 25
    assert update["stats"]["visits"] == 50
    assert update["stats"]["step_ms"] >= 0


def test_grow_cut_short_by_a_full_board_reports_the_iterations_it_ran():
    room = paused_room(max_cells=4)
    room.handle(PLAYER, plant(0, 0))
    update, _notice = room.handle(PLAYER, command(type="step", n=50))
    assert update["stats"]["iterations"] == 4


def test_updates_that_advance_nothing_carry_no_cost():
    room = paused_room()
    (planted,) = room.handle(PLAYER, plant(0, 0))
    room.handle(PLAYER, command(type="step", n=4))
    tip = room.board.tips_snapshot()[0]
    updates = [
        planted,
        *room.handle(PLAYER, command(type="slice", hexes=[[50, 50]])),
        *room.handle(PLAYER, command(type="cut", q=tip["q"], r=tip["r"])),
        *room.handle(PLAYER, command(type="resume")),
        *room.handle(PLAYER, command(type="pause")),
    ]
    assert len(updates) == 5
    assert all(update["stats"] is None for update in updates)


def test_measuring_does_not_change_the_game():
    def play() -> list:
        room = Room(SandboxMode(), PLAYER, seed=77)
        room.handle(PLAYER, command(type="pause"))
        history = []
        script = [
            command(type="plant", q=0, r=0, species="burst", speed="1"),
            command(type="plant", q=30, r=0, species="wanderer", speed="2"),
            command(type="step", n=12),
            command(type="slice", hexes=[[q, 0] for q in range(1, 8)]),
            command(type="step", n=9),
        ]
        for cmd in script:
            room.handle(PLAYER, cmd)
            history.append((room.board.tick, room.board.cells_snapshot(), room.board.tips_snapshot()))
        return history

    assert play() == play()


def scatter(count, q=0, r=0, half_width=20, half_height=20):
    return command(type="scatter", count=count, q=q, r=r, half_width=half_width, half_height=half_height)


@pytest.mark.parametrize("running", [True, False])
def test_clear_empties_the_board_and_leaves_the_clock_and_tick_alone(running):
    room = two_vine_room(running)
    (update,) = room.handle(PLAYER, command(type="clear"))

    assert update["cleared"] is True
    assert update["tick"] == 6
    assert update["clock"] == ("running" if running else "paused")
    assert update["added"] == update["removed"] == update["changed"] == update["tips"] == []
    assert update["stats"] is None
    assert not room.board.cells and not room.board.plants


def test_clear_update_does_not_list_the_cells_it_removed():
    room = paused_room()
    room.handle(PLAYER, scatter(300, half_width=60, half_height=60))
    room.handle(PLAYER, command(type="step", n=15))
    assert len(room.board.cells) > 2000

    (update,) = room.handle(PLAYER, command(type="clear"))
    assert update["cleared"] is True and update["removed"] == []
    assert len(json.dumps(update)) < 400


def test_other_updates_are_not_marked_cleared():
    room = paused_room()
    (planted,) = room.handle(PLAYER, plant(0, 0))
    (grown,) = room.handle(PLAYER, command(type="step", n=2))
    assert planted["cleared"] is False and grown["cleared"] is False
    assert planted["scattered"] is None and grown["scattered"] is None


def test_scatter_plants_and_reports_asked_and_planted():
    room = paused_room()
    (update,) = room.handle(PLAYER, scatter(10))

    assert update["scattered"] == {"asked": 10, "planted": 10}
    assert len(update["added"]) == 10 and all(cell["kind"] == "root" for cell in update["added"])
    assert len(update["plants"]) == 10 and all(details["settings"] is None for details in update["plants"])
    assert len(update["tips"]) == 10
    assert update["tick"] == 0 and update["clock"] == "paused" and update["stats"] is None
    assert all(plant_.owner == PLAYER for plant_ in room.board.plants.values())


def test_scattered_seeds_stay_inside_the_region():
    room = paused_room()
    (update,) = room.handle(PLAYER, scatter(200, q=7, r=-3, half_width=9, half_height=4))
    for cell in update["added"]:
        dq, dr = cell["q"] - 7, cell["r"] + 3
        assert abs(dr) <= 4 and abs(dq + dr / 2) <= 9


def test_scatter_with_too_little_room_is_not_an_error():
    room = paused_room()
    (update,) = room.handle(PLAYER, scatter(50, half_width=1, half_height=1))
    assert update["scattered"] == {"asked": 50, "planted": 7}  # three in the middle row, two in each offset row
    (again,) = room.handle(PLAYER, scatter(5, half_width=1, half_height=1))
    assert again["scattered"] == {"asked": 5, "planted": 0}
    assert again["added"] == []


def test_mode_can_forbid_clearing_and_scattering():
    room = Room(LookOnlyMode(), PLAYER, seed=1)
    assert rejected(room, command(type="clear")) == "not_permitted"
    assert rejected(room, scatter(5)) == "not_permitted"


# -- game speed -----------------------------------------------------------------


def set_speed(room: Room, speed) -> dict:
    (update,) = room.handle(PLAYER, command(type="speed", speed=speed))
    return update


def ack(room: Room, tick: int) -> None:
    assert room.handle(PLAYER, command(type="ack", tick=tick)) == []


def test_speed_starts_at_one_and_reports_the_time_available():
    room = Room(SandboxMode(), PLAYER, seed=1)
    welcome = room.welcome()
    assert welcome["speed"] == 1 and welcome["tick_ms"] == 500

    update = set_speed(room, 10)
    assert update["speed"] == 10 and update["tick_ms"] == 50
    assert update["stats"] is None
    update = set_speed(room, "max")
    assert update["speed"] == "max" and update["tick_ms"] is None
    assert room.welcome()["speed"] == "max"


@pytest.mark.parametrize("speed", [3, 0, "fast", True, 2.5])
def test_invalid_speed_is_rejected(speed):
    room = Room(SandboxMode(), PLAYER, seed=1)
    set_speed(room, 5)
    assert rejected(room, command(type="speed", speed=speed)) == "bad_game_speed"
    assert room.speed == 5


def test_setting_the_speed_while_paused_neither_advances_nor_resumes():
    room = paused_room()
    room.handle(PLAYER, plant(0, 0))
    update = set_speed(room, 10)
    assert update["clock"] == "paused" and update["tick"] == 0
    assert not room.running and room.board.tick == 0


def test_speed_survives_pause_and_resume():
    room = Room(SandboxMode(), PLAYER, seed=1)
    set_speed(room, 5)
    (paused,) = room.handle(PLAYER, command(type="pause"))
    (resumed,) = room.handle(PLAYER, command(type="resume"))
    assert paused["speed"] == resumed["speed"] == 5


def test_ack_sends_nothing_back_at_any_speed():
    room = paused_room()
    ack(room, 0)
    set_speed(room, "max")
    ack(room, 40)


def ticks_in(speed, seconds: float = 0.4) -> int:
    room = Room(SandboxMode(), PLAYER, seed=1, tick_interval=0.05)
    set_speed(room, speed)
    room.handle(PLAYER, plant(0, 0))

    async def script():
        await asyncio.sleep(seconds)

    run_clock_for(room, script)
    return room.board.tick


def test_higher_speed_ticks_faster():
    slow, fast = ticks_in(1), ticks_in(5)
    assert slow >= 4
    assert fast >= 2 * slow


def max_room(**kwargs) -> Room:
    room = Room(SandboxMode(), PLAYER, seed=1, tick_interval=3600, **kwargs)
    room.handle(PLAYER, plant(0, 0))
    set_speed(room, "max")
    return room


def test_max_without_acks_sends_exactly_one_tick():
    room = max_room()

    async def script():
        await asyncio.sleep(0.15)

    sent = run_clock_for(room, script)
    assert [message["tick"] for message in sent] == [1]


def test_each_ack_of_the_latest_tick_releases_exactly_one_more():
    room = max_room()
    seen = []

    async def script():
        for _ in range(5):
            await asyncio.sleep(0.03)
            seen.append(room.board.tick)
            ack(room, room.board.tick)
        await asyncio.sleep(0.03)
        seen.append(room.board.tick)

    sent = run_clock_for(room, script)
    assert seen == [1, 2, 3, 4, 5, 6]
    assert [message["tick"] for message in sent] == [1, 2, 3, 4, 5, 6]


def test_stale_ack_releases_nothing():
    room = max_room()

    async def script():
        await asyncio.sleep(0.03)
        ack(room, 1)
        await asyncio.sleep(0.03)
        assert room.board.tick == 2
        ack(room, 1)  # the client is behind: it has not drawn iteration 2
        ack(room, 0)
        await asyncio.sleep(0.05)

    run_clock_for(room, script)
    assert room.board.tick == 2


def test_leaving_max_while_waiting_resumes_ticking():
    room = max_room()
    room.tick_interval = 0.02

    async def script():
        await asyncio.sleep(0.05)
        assert room.board.tick == 1
        set_speed(room, 2)
        await asyncio.sleep(0.15)

    run_clock_for(room, script)
    assert room.board.tick >= 4


def test_pausing_at_max_stops_and_resuming_ticks_at_once():
    room = max_room()
    ticks = {}

    async def script():
        await asyncio.sleep(0.03)
        room.handle(PLAYER, command(type="pause"))
        ack(room, 1)
        await asyncio.sleep(0.05)
        ticks["paused"] = room.board.tick
        room.handle(PLAYER, command(type="resume"))
        await asyncio.sleep(0.03)
        ticks["resumed"] = room.board.tick

    run_clock_for(room, script)
    assert ticks == {"paused": 1, "resumed": 2}


def test_full_board_at_max_pauses_and_notifies():
    room = max_room(max_cells=4)

    async def script():
        for _ in range(20):
            await asyncio.sleep(0.01)
            ack(room, room.board.tick)

    sent = run_clock_for(room, script)
    assert not room.running and room.speed == "max"
    assert sent[-1]["type"] == "notice" and sent[-1]["code"] == "board_full"
    assert room.board.tick == 4


def test_a_new_speed_cuts_short_a_wait_at_the_old_one():
    room = Room(SandboxMode(), PLAYER, seed=1, tick_interval=3600)
    room.handle(PLAYER, plant(0, 0))

    async def script():
        await asyncio.sleep(0.03)  # the clock is now waiting an hour at 1x
        set_speed(room, "max")
        await asyncio.sleep(0.03)

    sent = run_clock_for(room, script)
    assert [message["tick"] for message in sent if message["type"] == "update"] == [1]


# -- persistence override ---------------------------------------------------------


def test_plant_with_a_persistence_is_reported_with_it():
    room = paused_room()
    (update,) = room.handle(PLAYER, command(type="plant", q=0, r=0, species="straight-vine", speed="1", persistence=90))
    assert update["plants"][0]["persistence"] == 90
    (update,) = room.handle(PLAYER, plant(0, 9))  # left out: the species default
    assert update["plants"][0]["persistence"] == 0


def test_scatter_with_a_persistence_reports_it_on_every_plant():
    room = paused_room()
    region = {"q": 0, "r": 0, "half_width": 10, "half_height": 10}
    (update,) = room.handle(PLAYER, command(type="scatter", count=10, persistence=40, **region))
    assert len(update["plants"]) == 10
    assert {details["persistence"] for details in update["plants"]} == {40}


def test_persistence_out_of_range_is_rejected():
    room = paused_room()
    region = {"q": 0, "r": 0, "half_width": 10, "half_height": 10}
    hydra = command(type="plant", q=0, r=0, species="hydra", speed="1", persistence=150)
    assert rejected(room, hydra) == "bad_persistence"
    assert rejected(room, command(type="scatter", count=5, persistence=150, **region)) == "bad_persistence"
    assert not room.board.plants


# -- skipping stuck tips ----------------------------------------------------------


def test_welcome_says_skipping_is_on_and_lists_sleeping_tips():
    room = Room(SandboxMode(), PLAYER, seed=1)
    welcome = room.welcome()
    assert welcome["skip_stuck"] is True and welcome["sleeping"] == []


def test_a_tip_that_falls_asleep_is_sent_once():
    room = Room(SandboxMode(), PLAYER, seed=1, tick_interval=3600)
    room.handle(PLAYER, command(type="pause"))
    room.board.plant_seed((0, 0), "straight-vine", "1", PLAYER, direction=0)
    room.board.plant_seed((3, 0), "straight-vine", "1/1000", PLAYER, direction=0)
    vine = next(tip.id for tip in room.board.tips.values() if tip.plant_id == 1)

    updates = [room.handle(PLAYER, command(type="step", n=1))[0] for _ in range(6)]
    slept_in = [index for index, update in enumerate(updates) if any(tip["id"] == vine for tip in update["slept"])]
    assert len(slept_in) == 1
    for update in updates[slept_in[0]:]:
        assert all(tip["id"] != vine for tip in update["tips"])
    assert room.welcome()["sleeping"][0]["id"] == vine


def test_switching_off_wakes_sleeping_tips_in_one_update():
    room = Room(SandboxMode(), PLAYER, seed=1, tick_interval=3600)
    room.handle(PLAYER, command(type="pause"))
    room.board.plant_seed((0, 0), "straight-vine", "1", PLAYER, direction=0)
    room.board.plant_seed((3, 0), "straight-vine", "1/1000", PLAYER, direction=0)
    vine = next(tip.id for tip in room.board.tips.values() if tip.plant_id == 1)
    room.handle(PLAYER, command(type="step", n=5))
    assert room.board.sleeping_count == 1

    (update,) = room.handle(PLAYER, command(type="skip_stuck", enabled=False))
    assert update["skip_stuck"] is False and update["stats"] is None and update["tick"] == 5
    assert update["woke"] == [vine]
    assert any(tip["id"] == vine for tip in update["tips"])
    (update,) = room.handle(PLAYER, command(type="skip_stuck", enabled=True))
    assert update["skip_stuck"] is True and update["woke"] == [] and update["slept"] == []
