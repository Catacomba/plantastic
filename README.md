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
- **Scissors**: click a plant cell to cut it, or drag to cut every cell the cursor passes while the game keeps running. A cut cell becomes a stump and everything beyond it is removed.
- **Mower**: press to pause the game, drag to mark a path, and release to cut the whole path at once. The game resumes if it was running. Escape cancels the path.
- A drag never cuts a root. To remove a whole plant, click its root with the scissors or the mower.
- **Pause / Resume** stops and starts the clock. While paused, **Grow** advances the board by the number of iterations you enter.
- **Drag with the right or middle mouse button** to pan, or hold **W A S D** or the **arrow keys**. Hold **Shift** to pan faster.
- The mouse wheel changes how large the hexagons are drawn. The same setting is a slider in the **Settings** menu.

## Settings and performance metrics

The **Settings** menu sits at the top right. Click its header to expand or minimize it. It holds the hex size slider and a switch for the performance metrics. Both the menu's state and the switch are remembered in your browser.

With **Performance metrics** on, a panel below the menu shows:

| Row | Meaning |
|---|---|
| FPS | Frames drawn per second. Capped by your display, and it stops while the tab is in the background. |
| Iteration | The server's compute time for the latest iteration, and its share of the time available per iteration (500 ms by default). |
| Last 10 | The average compute time per iteration over the last 10 growth updates. |
| Tip visits | How many times the latest iteration tried to move a tip that was due, whether or not it moved. |
| Tips | Growing tips, and how many are waiting behind an occupied hex. |
| Cells | Occupied hexes. |
| Plants | Plants on the board. |
| Update | The size of the latest update from the server, and how long the browser took to read it and rebuild the board. |
| Last grow | For the last **Grow**: iterations, total compute time, and the average per iteration. |

What drives cost: the server works per **tip**, not per plant, and a waiting tip is visited on every iteration just like a growing one. The browser redraws per **cell**, and every update carries the full list of tips, so update size grows with the tip count. A straight vine has one tip however long it is; a Burst or a branch-heavy custom plant can have thousands.

The metrics only measure. Nothing is limited apart from the board's 100,000 cells. While the switch is off the browser measures nothing.

## Plants

| Plant | How it grows | When cut |
|---|---|---|
| Straight vine | In a straight line | Forks from two cells behind the stump, one fork to each side |
| Zigzag | In a wavy line, turning the same way every other step | Regrows from behind the stump, zigzagging the other way |
| Spiral | Winds outward in runs of 1, 1, 2, 2, 3, 3 cells and so on | Regrows from behind the stump, winding the other way |
| Fern | A straight stem with a 3-cell side branch every third cell, on alternating sides | Nothing: the stump is final |
| Wanderer | Mostly straight, turning at random one step in five; it stops when it runs into itself | One new tip in a random direction |
| Hydra | In a straight line | Forks from both of the two cells behind the stump |
| Burst | Splits into a three-way fan every 4 cells | Forks like the straight vine |
| Custom | By the settings below | By the "When cut" setting |

### Custom plant

Choosing **Custom** in the species list shows its settings next to the speed field:

- **Branch chance %**: the chance that a tip branches on each new hex.
- **Branches min / max**: how many new tips one branching produces, from 1 to 4.
- **Calm stretch min**: hexes after a branch or turn in which nothing can happen.
- **Calm stretch max**: after this many hexes with no branch or turn, one is forced. Tick **never** for no limit.
- **Turn chance %**: the chance that a tip turns 60 degrees on a new hex when it does not branch.
- **When cut**: fork, regrow, nothing, or multiply.

A plant keeps the settings it was planted with. Changing them affects only the seeds you plant afterwards, so several custom plants with different settings can grow side by side. Point at any plant to see its species, speed, and settings in the top bar.

High branch chances grow very fast. The board holds 100,000 cells and pauses itself when it is full.

## Tests

```
.venv\Scripts\python -m pytest backend
```

## Layout

- `backend/plantastic/sim/` is the simulation: the hex grid, growth, cutting, and species. It has no networking and is deterministic for a given seed.
- `backend/plantastic/server/` hosts rooms over a websocket and serves the frontend. The message reference is in [docs/protocol.md](docs/protocol.md).
- `frontend/` is the browser client: plain ES modules and a pinned copy of three.js, with no build step.
- `openspec/` holds the specs and change history.
