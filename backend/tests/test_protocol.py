import json

import pytest

from plantastic.server.protocol import (
    AckCommand,
    CutCommand,
    GameError,
    PauseCommand,
    PlantCommand,
    ResumeCommand,
    SpeedCommand,
    StepCommand,
    game_speed,
    parse_command,
)


@pytest.mark.parametrize(
    "message, expected",
    [
        ({"type": "plant", "q": 1, "r": -2, "species": "straight-vine", "speed": "1/4"}, PlantCommand),
        ({"type": "cut", "q": 0, "r": 0}, CutCommand),
        ({"type": "pause"}, PauseCommand),
        ({"type": "resume"}, ResumeCommand),
        ({"type": "step", "n": 10}, StepCommand),
    ],
)
def test_valid_commands_parse(message, expected):
    assert isinstance(parse_command(json.dumps(message)), expected)


@pytest.mark.parametrize(
    "raw",
    [
        "not json",
        "[]",
        "{}",
        json.dumps({"type": "explode"}),
        json.dumps({"type": "cut", "q": 0}),
        json.dumps({"type": "cut", "q": 0.5, "r": 0}),
        json.dumps({"type": "cut", "q": "0", "r": 0}),
        json.dumps({"type": "cut", "q": 2**40, "r": 0}),
        json.dumps({"type": "cut", "q": 0, "r": 0, "extra": 1}),
        json.dumps({"type": "plant", "q": 0, "r": 0, "species": "straight-vine"}),
        json.dumps({"type": "plant", "q": 0, "r": 0, "species": 5, "speed": "1"}),
        json.dumps({"type": "step"}),
        json.dumps({"type": "step", "n": "ten"}),
        json.dumps({"type": "step", "n": True}),
    ],
)
def test_malformed_and_unknown_messages_fail_validation(raw):
    with pytest.raises(GameError) as error:
        parse_command(raw)
    assert error.value.code == "bad_message"


def test_slice_parses_hex_pairs():
    command = parse_command(json.dumps({"type": "slice", "hexes": [[0, 0], [1, -1]]}))
    assert command.type == "slice"
    assert command.hexes == [(0, 0), (1, -1)]
    assert len(parse_command(json.dumps({"type": "slice", "hexes": [[0, 0]] * 512})).hexes) == 512


@pytest.mark.parametrize(
    "hexes",
    [
        [],
        [[0, 0]] * 513,
        [[0]],
        [[0, 0, 0]],
        [[0.5, 0]],
        [["0", 0]],
        [[2**40, 0]],
        [{"q": 0, "r": 0}],
        "0,0",
        None,
    ],
)
def test_invalid_slices_fail_validation(hexes):
    with pytest.raises(GameError) as error:
        parse_command(json.dumps({"type": "slice", "hexes": hexes}))
    assert error.value.code == "bad_message"


def test_clear_and_scatter_parse():
    assert parse_command(json.dumps({"type": "clear"})).type == "clear"
    scatter = parse_command(
        json.dumps({"type": "scatter", "count": 500, "q": 3, "r": -2, "half_width": 150, "half_height": 0})
    )
    assert (scatter.count, scatter.q, scatter.r, scatter.half_width, scatter.half_height) == (500, 3, -2, 150, 0)


@pytest.mark.parametrize(
    "change",
    [
        {"count": 0},
        {"count": 501},
        {"count": 2.5},
        {"count": "10"},
        {"count": True},
        {"count": None},
        {"half_width": 151},
        {"half_height": 151},
        {"half_width": -1},
        {"half_height": 1.5},
        {"q": 0.5},
        {"extra": 1},
    ],
)
def test_invalid_scatters_fail_validation(change):
    message = {"type": "scatter", "count": 10, "q": 0, "r": 0, "half_width": 5, "half_height": 5, **change}
    if change.get("count", 1) is None:
        del message["count"]
    with pytest.raises(GameError) as error:
        parse_command(json.dumps(message))
    assert error.value.code == "bad_message"


def test_clear_takes_no_fields():
    with pytest.raises(GameError):
        parse_command(json.dumps({"type": "clear", "all": True}))


@pytest.mark.parametrize("speed", [1, 2, 5, 10, "max"])
def test_valid_game_speeds(speed):
    command = parse_command(json.dumps({"type": "speed", "speed": speed}))
    assert isinstance(command, SpeedCommand)
    assert game_speed(command.speed) == speed


@pytest.mark.parametrize("speed", [3, 0, -1, "fast", "MAX", True, 2.5, 5.0, None, "5", [5]])
def test_invalid_game_speeds_report_bad_game_speed(speed):
    command = parse_command(json.dumps({"type": "speed", "speed": speed}))
    with pytest.raises(GameError) as error:
        game_speed(command.speed)
    assert error.value.code == "bad_game_speed"


def test_ack_parses_a_tick():
    command = parse_command(json.dumps({"type": "ack", "tick": 12}))
    assert isinstance(command, AckCommand) and command.tick == 12


@pytest.mark.parametrize(
    "message",
    [
        {"type": "ack"},
        {"type": "ack", "tick": -1},
        {"type": "ack", "tick": 1.5},
        {"type": "ack", "tick": "3"},
        {"type": "ack", "tick": True},
        {"type": "speed"},
        {"type": "speed", "speed": 2, "extra": 1},
    ],
)
def test_malformed_speed_and_ack_messages_fail_validation(message):
    with pytest.raises(GameError) as error:
        parse_command(json.dumps(message))
    assert error.value.code == "bad_message"


@pytest.mark.parametrize("persistence", [50.5, "50", True, [50]])
def test_persistence_that_is_not_a_whole_number_fails_validation(persistence):
    region = {"q": 0, "r": 0, "half_width": 1, "half_height": 1}
    for message in (
        {"type": "plant", "q": 0, "r": 0, "species": "hydra", "speed": "1", "persistence": persistence},
        {"type": "scatter", "count": 1, **region, "persistence": persistence},
    ):
        with pytest.raises(GameError) as error:
            parse_command(json.dumps(message))
        assert error.value.code == "bad_message"


def test_persistence_is_optional_and_may_be_null():
    plant = {"type": "plant", "q": 0, "r": 0, "species": "hydra", "speed": "1"}
    assert parse_command(json.dumps(plant)).persistence is None
    assert parse_command(json.dumps({**plant, "persistence": None})).persistence is None
    assert parse_command(json.dumps({**plant, "persistence": 150})).persistence == 150  # range is the board's


def test_skip_stuck_takes_a_strict_bool():
    assert parse_command(json.dumps({"type": "skip_stuck", "enabled": False})).enabled is False
    for value in (0, 1, "true", None):
        with pytest.raises(GameError) as error:
            parse_command(json.dumps({"type": "skip_stuck", "enabled": value}))
        assert error.value.code == "bad_message"
    with pytest.raises(GameError):
        parse_command(json.dumps({"type": "skip_stuck"}))
