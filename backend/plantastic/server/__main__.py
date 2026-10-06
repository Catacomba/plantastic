"""Run the game server: ``python -m plantastic.server``."""

import argparse

import uvicorn

from .app import create_app
from .rooms import DEFAULT_TICK_INTERVAL


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m plantastic.server", description="Run the Plantastic server.")
    parser.add_argument("--host", default="127.0.0.1", help="address to listen on (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="port to listen on (default: 8000)")
    parser.add_argument(
        "--tick-interval",
        type=float,
        default=DEFAULT_TICK_INTERVAL,
        help=f"seconds per iteration while a room is running (default: {DEFAULT_TICK_INTERVAL})",
    )
    args = parser.parse_args()
    if args.tick_interval <= 0:
        parser.error("--tick-interval must be above 0")

    uvicorn.run(create_app(tick_interval=args.tick_interval), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
