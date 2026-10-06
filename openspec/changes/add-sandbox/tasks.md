# Tasks

## 1. Project setup

- [x] 1.1 Create `backend/pyproject.toml` (Python 3.13, FastAPI, uvicorn, pydantic, pytest, httpx2) and the `plantastic/sim`, `plantastic/server`, and `tests` packages; verify `pip install -e backend[dev]` succeeds in a fresh venv and `pytest` runs with zero tests collected
- [x] 1.2 Create `frontend/` with `index.html`, `css/`, `js/`, and a pinned `vendor/three.module.js` loaded through an import map; verify the file opens in a browser with no console errors
- [x] 1.3 Add `.gitignore` (venv, caches) and a `README.md` with install and run commands; verify the commands work as written

## 2. Hex grid and world state

- [x] 2.1 Implement axial hex coordinates, the six clockwise directions, neighbor lookup, and left/right turns in `sim/hex.py`; verify with unit tests that six steps of right turns return to the start heading and that opposite directions cancel
- [x] 2.2 Implement the world: sparse cell map, plants (species, speed, owner, creation order), cells (kind, parent, children), tips (heading, progress), and the seeded random generator; verify with unit tests that a hex holds at most one cell
- [x] 2.3 Implement planting: root plus one tip, random or given direction, rejection on an occupied hex, and speed parsing to exact fractions with the 0 to 10 range; verify with unit tests covering each rejection and both `"0.25"` and `"1/4"` inputs

## 3. Species

- [x] 3.1 Implement the species interface (`grow`, `on_cut`, id, name, default speed) and the catalog with lookup by id; verify a unit test rejects an unknown species id
- [x] 3.2 Implement the straight vine growth rule; verify a unit test that 5 unobstructed iterations at speed 1 give a straight 5-cell line with one tip

## 4. Growth

- [x] 4.1 Implement the iteration step: progress accumulation, ordered rounds, carry-over of remainders; verify unit tests for speeds 0.25 (hexes at iterations 4 and 8), 2 (6 hexes in 3 iterations), and 0.3 (hexes at iterations 4, 7, 10)
- [x] 4.2 Implement blocked tips: no advance, no turn, progress capped at 1, resume when the hex empties; verify a unit test that a tip blocked for 20 iterations advances exactly one hex on the iteration after the obstacle is removed
- [x] 4.3 Implement collision order (earliest plant, then earliest tip); verify a unit test where two plants are due to enter the same hex and the first-planted one gets it
- [x] 4.4 Implement the board limit: growth and planting stop at the maximum and the step reports "full"; verify with a unit test using a small limit, including growth resuming after a cut frees space
- [x] 4.5 Add a determinism test: two worlds with the same seed and the same scripted plantings and cuts are identical after every iteration, and differ in seed directions when the seeds differ

## 5. Cutting

- [x] 5.1 Implement the generic cut: segment becomes a stump, descendants (cells, stumps, tips) are removed, root cut removes the whole plant, stump and empty hex are rejected; verify unit tests for each case including a severed part that contains branches
- [x] 5.2 Implement the straight vine cut response: sprout cell two back (or the root), forward-left and forward-right headings relative to the path toward the stump, zero starting progress; verify unit tests for the cell-5 example in the spec, a cut adjacent to the root, and a cut on a branch that has a bend at the sprout cell
- [x] 5.3 Implement sprout suppression when the target hex is occupied or a matching tip exists; verify unit tests for one side occupied and both sides occupied
- [x] 5.4 Make world mutations return a change record (added, removed, changed cells) for the server to broadcast; verify a unit test that replaying change records onto an empty copy reproduces the world

## 6. Rooms and server

- [x] 6.1 Define the protocol messages as pydantic models with the error codes from the design, and document them in `docs/protocol.md`; verify unit tests that malformed and unknown messages fail validation
- [x] 6.2 Implement the room (boards, players, mode, seed) and the sandbox mode permission object; verify a unit test that a command not permitted by a stub mode is rejected with `not_permitted`
- [x] 6.3 Implement command handling for plant, cut, pause, resume, and step, each returning an update or an error; verify unit tests for step while running, step out of range, and cut while paused producing an update with no tick advance
- [x] 6.4 Implement the room clock as an asyncio task with a configurable interval, pausing the room and emitting a notice when the board is full; verify with a test using a short interval that ticks advance while running and stop while paused
- [x] 6.5 Implement the FastAPI app: `/ws` creating a sandbox room per connection, the welcome snapshot, update broadcast, room removal on disconnect, and static serving of `frontend/`; verify with a websocket test that plants a seed, receives growth updates, cuts, and ends with a client-side board equal to the server's
- [x] 6.6 Add a run command (`python -m plantastic.server`) with host, port, and tick interval options; verify the server starts and `/` returns the frontend page

## 7. Client: board and navigation

- [x] 7.1 Implement `hex.js` (same directions as the backend, hex to pixel and pixel to hex, pointy-top); verify in the browser console with a small self-check that pixel to hex inverts hex to pixel for a sample of coordinates
- [x] 7.2 Set up the three.js scene with an orthographic top-down camera and render loop, and draw hex outlines only for the visible area; verify the grid fills the window and follows resizing
- [x] 7.3 Implement drag to pan with a click-versus-drag threshold; verify the grid continues without edges in every direction
- [x] 7.4 Implement the hex size slider and mouse wheel as one value, saved to `localStorage`, with outlines fading at small sizes; verify the wheel moves the slider and the size survives a reload

## 8. Client: game

- [x] 8.1 Implement `net.js`: connect to `/ws`, apply the welcome snapshot and updates to a client cell map, expose send functions; verify in the browser that the welcome message arrives and logs the species catalog
- [x] 8.2 Render cells, parent links, stumps, and roots from the cell map with distinct styles and per-plant color; verify a planted seed grows visibly as a connected vine
- [x] 8.3 Render tips with the progress-proportional extension, eased between updates, and no extension when blocked; verify a speed 0.25 plant visibly creeps between hexes
- [x] 8.4 Implement the seed tool with species picker and speed field, and the scissors tool, with a hover highlight on the hex under the cursor; verify planting at speed 0.25 and cutting mid-vine show the stump and two diverging forks
- [x] 8.5 Implement the clock controls: pause and resume toggle, iteration field with grow button disabled while running, iteration counter; verify pausing, growing 10, and resuming behave as specified
- [x] 8.6 Implement feedback: brief messages for server errors, a board-full notice, and a disconnected state that blocks actions; verify by planting on an occupied hex and by stopping the server

## 9. Integration check

- [x] 9.1 Run the full backend test suite and confirm it passes
- [x] 9.2 Play through the sandbox in a browser end to end: plant several seeds at different speeds, pause, grow N, cut near the root, cut a branch, cut a root, block one plant with another and free it; confirm each matches the specs and record any mismatch as a fix before closing the change
