import json

import pytest

from plantastic.server.protocol import (
    CutCommand,
    GameError,
    PauseCommand,
    PlantCommand,
    ResumeCommand,
    StepCommand,
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
