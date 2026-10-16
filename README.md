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
- **Persistence % / Override** (next to Speed): tick **Override** and every seed you plant, of any species, gets the persistence you enter (0 to 100) instead of its species' own. This applies to **Random** seeds too. Unticked, each plant gets its species' persistence from the table below.
- **Scissors**: click a plant cell to cut it, or drag to cut every cell the cursor passes while the game keeps running. A cut cell becomes a stump and everything beyond it is removed.
- **Mower**: press to pause the game, drag to mark a path, and release to cut the whole path at once. The game resumes if it was running. Escape cancels the path.
- A drag never cuts a root. To remove a whole plant, click its root with the scissors or the mower.
- **Random**: enter a number and press **Plant** to scatter that many seeds at random empty places in the part of the board you can see. Each is a random pick from the seven plants that need no settings, so the mix varies. Zoom out first for a wider spread.
- **Clear** removes every plant at once. It does not ask first, and it leaves the clock and the iteration counter as they are.
- **Pause / Resume** stops and starts the clock. While paused, **Grow** advances the board by the number of iterations you enter.
- **1x / 2x / 5x / 10x / Max** set the game speed. 1x is one iteration per tick interval (0.5 s by default), and 2x to 10x shorten that wait. **Max** has no fixed wait: the server runs the next iteration as soon as the page has drawn the last one, so the game goes as fast as the slower of the two and the page never falls behind. Browsers stop drawing hidden tabs, so at Max the game waits while its tab is in the background. The speed stays as set through pauses.
- **Drag with the right or middle mouse button** to pan, or hold **W A S D** or the **arrow keys**. Hold **Shift** to pan faster.
- The mouse wheel changes how large the hexagons are drawn. The same setting is a slider in the **Settings** menu.

## Settings and performance metrics

The **Settings** menu sits at the top right. Click its header to expand or minimize it. It holds the hex size slider, a switch for the performance metrics, and **Skip stuck tips**. The menu's state and both switches are remembered in your browser.

**Skip stuck tips** (on by default) lets the server stop working on tips that cannot move. A tip falls asleep when the hex ahead of it is taken and it either lost its persistence roll or has no free turn; it wakes when a cut or **Clear** empties that hex, or one of its turns. The game plays out exactly the same either way, with the same plants and the same random choices; only the work changes. Sleeping tips are not visited, and each update sends a stuck tip once instead of every time, so on a crowded board both the iteration time and the update size drop sharply. Remember that cutting a cell leaves a stump in its place: to free a stuck tip, cut the plant in its way at its root or further back.

With **Performance metrics** on, a panel below the menu shows:

| Row | Meaning |
|---|---|
| FPS | Frames drawn per second. Capped by your display, and it stops while the tab is in the background. |
| Iteration | The server's compute time for the latest iteration, and its share of the time available per iteration at the current speed (500 ms at 1x by default, 50 ms at 10x). At Max no time is set aside, so only the compute time is shown. |
| Last 10 | The average compute time per iteration over the last 10 growth updates. |
| Tip visits | How many times the latest iteration tried to move a tip that was due, whether or not it moved. Sleeping tips are not visited. |
| Tips | Growing tips, how many are waiting behind an occupied hex, and how many of those are asleep. |
| Cells | Occupied hexes. |
| Plants | Plants on the board. |
| Update | The size of the latest update from the server, and how long the browser took to read it and rebuild the board. |
| Last grow | For the last **Grow**: iterations, total compute time, and the average per iteration. |

What drives cost: the server works per **tip**, not per plant. With **Skip stuck tips** off, a waiting tip is visited on every iteration just like a growing one, and every update carries the full list of tips; with it on, only awake tips cost anything, and a stuck tip is sent once. The browser redraws per **cell**, and it still draws every tip, awake or asleep. A straight vine has one tip however long it is; a Burst or a branch-heavy custom plant can have thousands.

Below the panel are two graphs of the last 120 updates from the server, newest on the right:

- **Update handling**: how long the browser took to read each update and rebuild the board, the same time the Update row shows.
- **Tips**: the number of growing tips after each update.

Each graph plots one point per update, not per second, so both stand still while the game is paused and a **Grow** adds a single point. A point in one graph lines up with the point for the same update in the other. Each graph is scaled to the largest value it currently shows, which is printed beside it as the peak. The graphs follow the **Performance metrics** switch, and turning it off discards their history.

The metrics only measure. Nothing is limited apart from the board's 100,000 cells. While the switch is off the browser measures nothing.

## Plants

| Plant | How it grows | Persistence | When cut |
|---|---|---|---|
| Straight vine | In a straight line | 0% | Forks from two cells behind the stump, one fork to each side |
| Zigzag | In a wavy line, turning the same way every other step | 30% | Regrows from behind the stump, zigzagging the other way |
| Spiral | Winds outward in runs of 1, 1, 2, 2, 3, 3 cells and so on | 30% | Regrows from behind the stump, winding the other way |
| Fern | A straight stem with a 3-cell side branch every third cell, on alternating sides | 0% | Nothing: the stump is final |
| Wanderer | Mostly straight, turning at random one step in five | 60% | One new tip in a random direction |
| Hydra | In a straight line | 80% | Forks from both of the two cells behind the stump |
| Burst | Splits into a three-way fan every 4 cells | 30% | Forks like the straight vine |
| Custom | By the settings below | By its setting | By the "When cut" setting |

**Persistence** is what a plant does when a tip runs into an occupied hex, whether another plant or its own. It rolls its persistence once: on a hit the tip turns into an empty hex, 60 degrees left or right if it can and otherwise a sharper 120 degrees, never straight back, and keeps growing from there; otherwise it waits, as a straight vine always does, until the hex is cut free. A tip with none of those four hexes free waits without rolling. Each new obstacle gets a new roll. A zigzag that goes around something shifts its line sideways but keeps its direction; the other plants carry on in the new direction. The table gives each plant's default; **Override** replaces it for the seeds you plant while it is ticked. A plant keeps the persistence it was planted with, and pointing at it shows that value.

### Custom plant

Choosing **Custom** in the species list shows its settings next to the speed field:

- **Branch chance %**: the chance that a tip branches on each new hex.
- **Branches min / max**: how many new tips one branching produces, from 1 to 4.
- **Calm stretch min**: hexes after a branch or turn in which nothing can happen.
- **Calm stretch max**: after this many hexes with no branch or turn, one is forced. Tick **never** for no limit.
- **Turn chance %**: the chance that a tip turns 60 degrees on a new hex when it does not branch.
- **Persistence %**: the chance that a blocked tip takes another path; see above. While **Override** is ticked in the tool bar, its value is used instead of this one.
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
