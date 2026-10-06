"""Rooms own the boards, the clock, and the rules about who may do what."""

from __future__ import annotations

import asyncio
import secrets
from collections.abc import Awaitable, Callable

from ..sim.world import DEFAULT_MAX_CELLS, Changes, SimError, World
from .protocol import (
    CutCommand,
    GameError,
    PauseCommand,
    PlantCommand,
    ResumeCommand,
    SliceCommand,
    StepCommand,
    notice_message,
)

MAX_STEP = 1000
DEFAULT_TICK_INTERVAL = 0.5

Broadcast = Callable[[dict], Awaitable[None]]


class Mode:
    """Decides which commands a room's players may use."""

    name: str
    starts_running: bool

    def permits(self, player: str, command_type: str) -> bool:
        raise NotImplementedError


class SandboxMode(Mode):
    name = "sandbox"
    starts_running = True

    def permits(self, player: str, command_type: str) -> bool:
        return True


class Room:
    def __init__(
        self,
        mode: Mode,
        player: str,
        seed: int | None = None,
        tick_interval: float = DEFAULT_TICK_INTERVAL,
        max_cells: int = DEFAULT_MAX_CELLS,
    ):
        self.id = secrets.token_hex(4)
        self.mode = mode
        self.players = [player]
        self.seed = secrets.randbits(32) if seed is None else seed
        self.boards = [World(self.seed, max_cells=max_cells)]
        self.tick_interval = tick_interval
        self.running = mode.starts_running
        self._resumed = asyncio.Event()
        if self.running:
            self._resumed.set()

    @property
    def board(self) -> World:
        return self.boards[0]

    @property
    def clock(self) -> str:
        return "running" if self.running else "paused"

    # -- messages ----------------------------------------------------------

    def welcome(self) -> dict:
        board = self.board
        return {
            "type": "welcome",
            "room": self.id,
            "mode": self.mode.name,
            "seed": self.seed,
            "species": [
                {"id": species.id, "name": species.name, "default_speed": str(species.default_speed)}
                for species in board.catalog.values()
            ],
            "clock": self.clock,
            "tick": board.tick,
            "cells": board.cells_snapshot(),
            "tips": board.tips_snapshot(),
        }

    def _update(self, changes: Changes) -> dict:
        board = self.board
        return {
            "type": "update",
            "tick": board.tick,
            "added": changes.added,
            "removed": changes.removed,
            "changed": changes.changed,
            "tips": board.tips_snapshot(),
            "clock": self.clock,
        }

    def _after_growth(self, changes: Changes) -> list[dict]:
        """The messages for a growth result, pausing the room if the board filled up."""
        if not changes.full:
            return [self._update(changes)]
        self._set_running(False)
        return [
            self._update(changes),
            notice_message("board_full", "The board is full. Cut something to make room."),
        ]

    # -- commands ----------------------------------------------------------

    def handle(self, player: str, command) -> list[dict]:
        """Apply a command and return the messages to broadcast.

        Raises GameError when the command is rejected; the game is then unchanged.
        """
        if not self.mode.permits(player, command.type):
            raise GameError("not_permitted", f"'{command.type}' is not allowed in this room.")
        try:
            if isinstance(command, PlantCommand):
                changes = self.board.plant_seed(
                    (command.q, command.r), command.species, command.speed, player
                )
                return [self._update(changes)]
            if isinstance(command, CutCommand):
                return [self._update(self.board.cut((command.q, command.r)))]
            if isinstance(command, SliceCommand):
                return [self._update(self.board.slice(command.hexes))]
        except SimError as error:
            raise GameError(error.code, error.message) from None
        if isinstance(command, PauseCommand):
            self._set_running(False)
            return [self._update(Changes())]
        if isinstance(command, ResumeCommand):
            self._set_running(True)
            return [self._update(Changes())]
        if isinstance(command, StepCommand):
            return self._step(command.n)
        raise GameError("bad_message", "Unknown command.")

    def _step(self, count) -> list[dict]:
        if self.running:
            raise GameError("not_paused", "Pause the game before growing by a set number of iterations.")
        if not isinstance(count, int) or not 1 <= count <= MAX_STEP:
            raise GameError("bad_step", f"Iterations must be a whole number from 1 to {MAX_STEP}.")
        changes = Changes()
        for _ in range(count):
            changes.merge(self.board.step())
            if changes.full:
                break
        return self._after_growth(changes)

    def tick(self) -> list[dict]:
        """Advance one iteration on the clock."""
        return self._after_growth(self.board.step())

    # -- clock -------------------------------------------------------------

    def _set_running(self, running: bool) -> None:
        self.running = running
        if running:
            self._resumed.set()
        else:
            self._resumed.clear()

    async def run_clock(self, broadcast: Broadcast) -> None:
        """Tick at the room's interval while running. Runs until cancelled."""
        while True:
            await self._resumed.wait()
            await asyncio.sleep(self.tick_interval)
            if not self.running:
                continue
            for message in self.tick():
                await broadcast(message)
