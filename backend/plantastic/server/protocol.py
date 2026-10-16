"""Websocket messages. See docs/protocol.md for the reference."""

from __future__ import annotations

from typing import Annotated, Any, Literal, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictFloat,
    StrictInt,
    TypeAdapter,
    ValidationError,
)

COORD_LIMIT = 2**31
MAX_SLICE_HEXES = 512
MAX_SCATTER = 500
MAX_REGION_HALF = 150
# Game speeds: how many times faster than the room's base interval the clock ticks.
SPEEDS = (1, 2, 5, 10)
# The speed at which the clock waits for the client instead of a fixed interval.
MAX_SPEED = "max"

Coord = Annotated[StrictInt, Field(ge=-COORD_LIMIT, le=COORD_LIMIT)]
# A persistence for new seeds, or None for each species' default. The range is
# checked by the simulation, so a value out of range reports bad_persistence.
Persistence = Union[StrictInt, None]


class GameError(Exception):
    """A rejected message or command, reported to the sender only."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class _Command(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PlantCommand(_Command):
    type: Literal["plant"]
    q: Coord
    r: Coord
    species: str = Field(max_length=64)
    # Sent as a string ("0.25" or "1/4") so the value stays exact.
    speed: Union[Annotated[str, Field(max_length=32)], StrictInt, StrictFloat]
    # Only for species that have settings. The species checks the contents.
    settings: Union[dict[str, Any], None] = None
    persistence: Persistence = None


class CutCommand(_Command):
    type: Literal["cut"]
    q: Coord
    r: Coord


class SliceCommand(_Command):
    type: Literal["slice"]
    # The hexes of a stroke, in the order the cursor passed them.
    hexes: list[tuple[Coord, Coord]] = Field(min_length=1, max_length=MAX_SLICE_HEXES)


class ClearCommand(_Command):
    type: Literal["clear"]


class ScatterCommand(_Command):
    type: Literal["scatter"]
    count: Annotated[StrictInt, Field(ge=1, le=MAX_SCATTER)]
    # The region: a centre hex, and how far it reaches in hex widths and in rows.
    q: Coord
    r: Coord
    half_width: Annotated[StrictInt, Field(ge=0, le=MAX_REGION_HALF)]
    half_height: Annotated[StrictInt, Field(ge=0, le=MAX_REGION_HALF)]
    persistence: Persistence = None


class PauseCommand(_Command):
    type: Literal["pause"]


class ResumeCommand(_Command):
    type: Literal["resume"]


class StepCommand(_Command):
    type: Literal["step"]
    # Range and whole-number checks happen in the room so they report bad_step.
    n: Union[StrictInt, StrictFloat]


class SpeedCommand(_Command):
    type: Literal["speed"]
    # 1, 2, 5, 10, or "max". Checked in the room so anything else reports bad_game_speed.
    speed: Any


class AckCommand(_Command):
    type: Literal["ack"]
    # The iteration the client has applied and drawn.
    tick: Annotated[StrictInt, Field(ge=0)]


class SkipStuckCommand(_Command):
    type: Literal["skip_stuck"]
    # Whether stuck tips sleep instead of being worked on every iteration.
    enabled: StrictBool


Command = Annotated[
    Union[
        PlantCommand,
        CutCommand,
        SliceCommand,
        ClearCommand,
        ScatterCommand,
        PauseCommand,
        ResumeCommand,
        StepCommand,
        SpeedCommand,
        AckCommand,
        SkipStuckCommand,
    ],
    Field(discriminator="type"),
]

_command_adapter = TypeAdapter(Command)


def parse_command(raw: str | bytes) -> Command:
    try:
        return _command_adapter.validate_json(raw)
    except ValidationError as error:
        first = error.errors()[0]
        where = ".".join(str(part) for part in first["loc"]) or "message"
        raise GameError("bad_message", f"Invalid message ({where}): {first['msg']}") from None


def game_speed(value: Any) -> int | str:
    """Check a game speed from a ``speed`` command: 1, 2, 5, 10, or "max"."""
    if value == MAX_SPEED or (type(value) is int and value in SPEEDS):
        return value
    allowed = ", ".join(f"{speed}x" for speed in SPEEDS)
    raise GameError("bad_game_speed", f"The game speed must be {allowed}, or max.")


def error_message(code: str, message: str) -> dict:
    return {"type": "error", "code": code, "message": message}


def notice_message(code: str, message: str) -> dict:
    return {"type": "notice", "code": code, "message": message}
