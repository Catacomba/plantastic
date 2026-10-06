"""The HTTP and websocket entry point."""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from ..sim.world import DEFAULT_MAX_CELLS
from .protocol import GameError, error_message, parse_command
from .rooms import DEFAULT_TICK_INTERVAL, Room, SandboxMode

FRONTEND_DIR = Path(__file__).resolve().parents[3] / "frontend"


def create_app(
    tick_interval: float = DEFAULT_TICK_INTERVAL,
    max_cells: int = DEFAULT_MAX_CELLS,
    frontend_dir: Path | None = FRONTEND_DIR,
) -> FastAPI:
    app = FastAPI(title="Plantastic")
    app.state.rooms = {}

    @app.websocket("/ws")
    async def play(websocket: WebSocket) -> None:
        await websocket.accept()
        player = "player-1"
        room = Room(SandboxMode(), player, tick_interval=tick_interval, max_cells=max_cells)
        app.state.rooms[room.id] = room

        # The clock and the command loop both send, so sends take turns.
        send_lock = asyncio.Lock()

        async def send(message: dict) -> None:
            async with send_lock:
                await websocket.send_json(message)

        await send(room.welcome())
        clock = asyncio.create_task(room.run_clock(send))
        try:
            while True:
                raw = await websocket.receive_text()
                try:
                    messages = room.handle(player, parse_command(raw))
                except GameError as error:
                    messages = [error_message(error.code, error.message)]
                for message in messages:
                    await send(message)
        except WebSocketDisconnect:
            pass
        finally:
            clock.cancel()
            del app.state.rooms[room.id]

    if frontend_dir is not None:
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

    return app
