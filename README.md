# Plantastic

A game about steering growing plants by cutting them. Plants grow across a hexagonal grid, and each species responds to a cut in its own way.

This is the sandbox: an endless board for planting seeds, letting them grow, and trying out cuts.

## Run it

Requires Python 3.13 or newer. From the repository root:

```
python -m venv .venv
.venv\Scripts\python -m pip install -e "backend[dev]"
.venv\Scripts\python -m plantastic.server
```

On macOS or Linux use `.venv/bin/python` in place of `.venv\Scripts\python`.

Then open http://127.0.0.1:8000.

Server options:

| Option | Default | Meaning |
|---|---|---|
| `--host` | `127.0.0.1` | Address to listen on |
| `--port` | `8000` | Port to listen on |
| `--tick-interval` | `0.5` | Seconds per iteration while a room is running |

## Play

- **Seed**: click a hex to plant. The seed picks a random direction. Speed is in hexagons per iteration; `0.25` or `1/4` means one hexagon every 4 iterations.
- **Scissors**: click a plant cell to cut it. The cell becomes a stump and everything beyond it is removed. Cutting a root removes the whole plant.
- **Pause / Resume** stops and starts the clock. While paused, **Grow** advances the board by the number of iterations you enter.
- **Drag** to pan. The **hex size** slider and the mouse wheel change how large the hexagons are drawn.

The straight vine grows in a straight line. When cut, it forks from two cells behind the stump, one fork to each side.

## Tests

```
.venv\Scripts\python -m pytest backend
```

## Layout

- `backend/plantastic/sim/` is the simulation: the hex grid, growth, cutting, and species. It has no networking and is deterministic for a given seed.
- `backend/plantastic/server/` hosts rooms over a websocket and serves the frontend. The message reference is in [docs/protocol.md](docs/protocol.md).
- `frontend/` is the browser client: plain ES modules and a pinned copy of three.js, with no build step.
- `openspec/` holds the specs and change history.
