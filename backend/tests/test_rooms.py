import asyncio
import json

import pytest

from plantastic.server.protocol import GameError, parse_command
from plantastic.server.rooms import MAX_STEP, Mode, Room, SandboxMode

PLAYER = "player-1"


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
    assert welcome["species"] == [
        {"id": "straight-vine", "name": "Straight vine", "default_speed": "1"}
    ]


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
