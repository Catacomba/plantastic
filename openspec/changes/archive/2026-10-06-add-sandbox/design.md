# Design

## Context

The repository is empty apart from OpenSpec scaffolding. Python 3.13 and Node are installed on the development machine; `uv` is not. See proposal.md for motivation and scope.

Three facts about the future shape this design even though they are not built here:

- The game will be hosted for other players.
- Two competitive modes are planned: a race on separate boards with the same puzzle, and a shared board where players' plants compete for space.
- More species are planned, some with randomness, and a light source that some species grow toward or away from.

## Goals / Non-Goals

**Goals:**

- A simulation core with no knowledge of networking, time, or rendering, so that species rules are unit-testable and a session can be replayed.
- A species interface that later species (random, light-seeking) fit without changes to the core loop.
- A room abstraction where the sandbox is one mode among several, so multiplayer adds players and modes rather than replacing structure.
- A client that only renders and sends intentions.

**Non-Goals:**

- Reconnecting to a room, persistence, accounts, lobbies, or horizontal scaling.
- Client-side prediction. Actions appear when the server confirms them.
- Light, levels, win conditions, and per-owner cutting rules.
- A frontend build pipeline or framework.

## Decisions

### 1. Repository layout

```
backend/
  pyproject.toml
  plantastic/
    sim/        hex.py, world.py, species.py     (pure, no I/O)
    server/     app.py, rooms.py, protocol.py
  tests/
frontend/
  index.html
  css/
  js/           main.js, net.js, board.js, hex.js, ui.js
  vendor/       three.module.js (pinned copy)
```

The backend serves `frontend/` as static files, so one process runs the whole game. Python tooling is `venv` + `pip` with dependencies declared in `pyproject.toml`.

*Alternative considered:* a separate frontend dev server with a bundler. Rejected for now: the frontend is a handful of ES modules, and one process is simpler to run and host.

### 2. Hex coordinates

Axial coordinates `(q, r)` with pointy-top hexagons. The six directions are indexed 0 to 5 clockwise starting at east, so "forward-left" and "forward-right" of direction `d` are `(d - 1) mod 6` and `(d + 1) mod 6`. The same convention is implemented once in Python and once in JS (`hex.js`), and the hex-to-pixel conversion lives only in JS.

*Alternative considered:* cube or offset coordinates. Axial is the smallest representation that keeps neighbor math uniform, and it serializes as two integers.

### 3. World state

The board is a dictionary from `(q, r)` to a cell. A cell records its plant, its kind (`root`, `segment`, `stump`), and its parent hex (the neighbor toward the root). A plant records its id, species, speed, owner, and creation order. A tip records its id, plant, the cell it sits on, its heading, and its progress.

Parent links make the two cut operations cheap: walking two cells back is two lookups, and the severed part is the set of cells reachable from the cut cell through child links. A per-cell list of children is kept alongside the parent link to avoid scanning neighbors.

Ids are integers issued in creation order, which doubles as the tie-break order required by the collision rule.

### 4. Species as two rules

A species is an object with:

- `grow(tip, world) -> list of headings`: the headings the tip continues with when it is due to advance. The straight vine returns the tip's current heading. One heading means continue, several mean branch, none means the tip ends.
- `on_cut(plant, stump_hex, world) -> list of (cell, heading)`: the new tips to create.
- `default_speed`, `id`, `name`.

Both rules receive the world, which is how a later light source or neighboring plants become visible to a species without changing the loop. Rules needing randomness take it from the world's seeded generator and nowhere else.

*Alternative considered:* a data-only description (for example a table of turn probabilities). Rejected because cut responses and light-seeking are not naturally tabular; plain Python functions stay readable and testable.

### 5. Iteration algorithm

An iteration runs in two parts:

1. Every tip gains progress equal to its plant's speed. A tip that is blocked is capped at a progress of 1.
2. Rounds: tips are visited in order of (plant creation, tip creation). A tip with progress of at least 1 asks its species for headings and tries to enter the target hex. If the hex is empty it is claimed, a segment is created, the tip moves, and progress drops by 1. If it is occupied the tip is marked blocked and its progress is capped at 1. Rounds repeat until no tip advanced.

Visiting tips in a fixed order makes "the earliest plant wins" fall out of the loop with no separate conflict pass, and rounds let a speed-2 plant and a speed-1 plant interleave fairly, one hex at a time.

Speeds and progress are `fractions.Fraction`. Speeds arrive from the client as strings (`"0.25"`, `"1/4"`) and are parsed exactly. The allowed range is greater than 0 and at most 10, which bounds the rounds per iteration.

*Alternative considered:* floats with an epsilon. Rejected: a speed of 0.1 would drift, and race mode needs two servers' boards to match exactly.

### 6. Blocked tips wait rather than die

A blocked tip stays alive and resumes when its target hex empties. This makes cutting useful for opening space, which matters on a shared board later. The cap on banked progress prevents a long-blocked tip from bursting forward.

Sprouts created by a cut are different: a sprout whose target hex is occupied at the moment of the cut is not created at all. Creating it anyway would let repeated cuts stack several waiting tips on one cell. A sprout is also skipped when the plant already has a tip at that cell with that heading.

### 7. Cut semantics

- Segment: the cell becomes a stump, its descendants (cells, stumps, tips) are removed, then `on_cut` runs.
- Root: the whole plant is removed. In the sandbox this is the way to delete a plant.
- Stump or empty hex: rejected.

For the straight vine, `on_cut` walks up to two parent links from the stump, stopping at the root. "Forward" is the direction from the sprouting cell to its child on the path to the stump, which gives the right answer on bends and at the root without special cases.

### 8. Rooms, modes, and the clock

A room holds a list of boards (one in the sandbox), a mode, a seeded random generator, its players, and a clock. The mode is an object answering "may this player send this command?" and supplying defaults such as whether the room starts running. The sandbox mode allows everything. The race and shared-board modes will be further mode objects.

The clock is an asyncio task per room that, while running, calls the board's step once every 500 ms and broadcasts the result. The interval is a server setting. "Grow N" (1 to 1000) runs N steps back to back and sends one combined update. All commands and ticks for a room run on the event loop, so a room needs no locks.

Each websocket connection creates its own sandbox room, removed on disconnect. The room seed is generated at creation and included in the welcome message so a session can be reproduced.

The board limit is 20,000 occupied hexes per board. The step function stops claiming hexes at the limit and returns a "full" flag; the room pauses and notifies clients.

*Alternative considered:* the client drives the clock by requesting each step. Rejected because competitive modes need a clock no player controls, and one clock implementation is better than two.

### 9. Protocol

JSON text frames over one websocket at `/ws`.

Client to server: `plant {q, r, species, speed}`, `cut {q, r}`, `pause`, `resume`, `step {n}`.

Server to client:

- `welcome {room, mode, seed, species[], clock, tick, cells[], tips[]}`
- `update {tick, added[], removed[], changed[], tips[], clock}` where `tips` is the complete current list of tips with their progress. Tips are few compared with cells, so sending them whole avoids tip-level diffing.
- `error {code, message}` with stable codes such as `occupied`, `nothing_to_cut`, `bad_speed`, `unknown_species`, `not_paused`, `bad_step`, `not_permitted`, `board_full`.
- `notice {code}` for `board_full`.

Fractions are sent as strings. Every message carries a `type` field. Messages are validated with pydantic models.

### 10. Server stack

FastAPI with uvicorn: websockets, static file serving, and request validation in one dependency set, and a common target for hosting. Tests use pytest; the websocket layer is tested with FastAPI's test client.

### 11. Rendering

three.js with an orthographic camera looking straight down. Hex size is the world-to-screen scale of that camera, so the slider, the mouse wheel, and "zoom" are one value (range 6 to 80 pixels, stored in `localStorage`).

- Cells: one `InstancedMesh` per cell kind, with per-instance color by plant. Instances are rebuilt from the client's cell map when an update arrives.
- Vines: a line from each cell to its parent, so the plant reads as a vine and not as filled tiles.
- Tips: a line from the tip's cell toward the next hex, scaled by progress. Between updates the client eases toward the reported progress.
- Grid: hex outlines generated only for the hexes inside the camera's view, regenerated on pan and size change. Below a size threshold the outlines fade out to avoid a moiré of lines.
- Input: a pointer press that moves less than a few pixels is a click and uses the selected tool on the hex under the cursor; anything longer pans.

three.js is vendored as a pinned ES module and loaded through an import map, so the game has no CDN dependency at runtime.

*Alternative considered:* a 2D canvas. three.js was the stated choice, and it leaves room for a tilted board or plants with height later.

## Risks / Trade-offs

- [Update size on large boards] → Updates carry only changed cells plus the tip list; the 20,000-hex limit bounds the snapshot. Viewport-based culling on the server is deferred until a mode needs it.
- [Grid outline cost at small hex sizes] → Outlines are limited to the view and fade out below a threshold.
- [Hex math duplicated in Python and JS] → Both follow the convention in decision 2, and a shared table of direction vectors is covered by a test on each side.
- [One room per connection loses the board on refresh] → Accepted for the sandbox. The seed is exposed so a session can be re-created; reconnection belongs with accounts.
- [Blocked tips waiting forever cost work every iteration] → The cost is one lookup per blocked tip per iteration, bounded by the board limit.
- [No client prediction makes actions lag on slow connections] → Accepted. Cuts and plantings are applied on receipt, not on the next tick, so the delay is one round trip.

## Open Questions

- Colors and visual style of plants, stumps, and tips. Any readable palette works for the sandbox.
- Whether the tick interval should be adjustable from the sandbox UI. It is a server setting for now.
