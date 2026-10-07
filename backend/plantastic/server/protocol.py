"""Websocket messages. See docs/protocol.md for the reference."""

from __future__ import annotations

from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt, TypeAdapter, ValidationError

COORD_LIMIT = 2**31
MAX_SLICE_HEXES = 512

Coord = Annotated[StrictInt, Field(ge=-COORD_LIMIT, le=COORD_LIMIT)]


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


class CutCommand(_Command):
    type: Literal["cut"]
    q: Coord
    r: Coord


class SliceCommand(_Command):
    type: Literal["slice"]
    # The hexes of a stroke, in the order the cursor passed them.
    hexes: list[tuple[Coord, Coord]] = Field(min_length=1, max_length=MAX_SLICE_HEXES)


class PauseCommand(_Command):
    type: Literal["pause"]


class ResumeCommand(_Command):
    type: Literal["resume"]


class StepCommand(_Command):
    type: Literal["step"]
    # Range and whole-number checks happen in the room so they report bad_step.
    n: Union[StrictInt, StrictFloat]


Command = Annotated[
    Union[PlantCommand, CutCommand, SliceCommand, PauseCommand, ResumeCommand, StepCommand],
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


def error_message(code: str, message: str) -> dict:
    return {"type": "error", "code": code, "message": message}


def notice_message(code: str, message: str) -> dict:
    return {"type": "notice", "code": code, "message": message}
