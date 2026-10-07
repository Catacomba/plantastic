"""Rooms own the boards, the clock, and the rules about who may do what."""

from __future__ import annotations

import asyncio
import secrets
import time
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
                {
                    "id": species.id,
                    "name": species.name,
                    "default_speed": str(species.default_speed),
                    "settings": [setting.describe() for setting in species.settings],
                }
                for species in board.catalog.values()
            ],
            "clock": self.clock,
            "tick": board.tick,
            # Time available for one iteration while the clock runs.
            "tick_ms": round(self.tick_interval * 1000),
            "cells": board.cells_snapshot(),
            "tips": board.tips_snapshot(),
            "plants": board.plants_snapshot(),
        }

    def _update(self, changes: Changes, stats: dict | None = None) -> dict:
        board = self.board
        return {
            "type": "update",
            "tick": board.tick,
            "added": changes.added,
            "removed": changes.removed,
            "changed": changes.changed,
            "plants": changes.plants,
            "tips": board.tips_snapshot(),
            "clock": self.clock,
            # The cost of the iterations this update advanced, or None if it advanced none.
            "stats": stats,
        }

    def _grow(self, iterations: int) -> list[dict]:
        """Advance the board, timing the work, and return the messages to send.

        The clock is read only here, around the simulation, and never by it,
        so measuring cannot change the game.
        """
        changes = Changes()
        done = 0
        started = time.perf_counter()
        for _ in range(iterations):
            changes.merge(self.board.step())
            done += 1
            if changes.full:
                break
        elapsed_ms = (time.perf_counter() - started) * 1000
        stats = {"iterations": done, "step_ms": round(elapsed_ms, 2), "visits": changes.visits}

        if not changes.full:
            return [self._update(changes, stats)]
        # The board filled up: pause the room and say why.
        self._set_running(False)
        return [
            self._update(changes, stats),
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
                    (command.q, command.r),
                    command.species,
                    command.speed,
                    player,
                    settings=command.settings,
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
        return self._grow(count)

    def tick(self) -> list[dict]:
        """Advance one iteration on the clock."""
        return self._grow(1)

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
