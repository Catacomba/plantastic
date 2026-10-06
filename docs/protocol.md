# Websocket protocol

The client connects to `/ws`. Every message is a JSON object in a text frame with a `type` field. The server is the only authority over the game: the client sends commands and applies what the server reports.

Hexes are axial coordinates `q`, `r` on a pointy-top grid. Directions are numbered 0 to 5 clockwise on screen from east: `(1,0)`, `(0,1)`, `(-1,1)`, `(-1,0)`, `(0,-1)`, `(1,-1)`.

Exact numbers (speeds and progress) are strings such as `"0.25"` or `"1/4"`.

## Client to server

| Type | Fields | Meaning |
|---|---|---|
| `plant` | `q`, `r`, `species`, `speed` | Plant a seed. `speed` is hexagons per iteration, above 0 and at most 10. |
| `cut` | `q`, `r` | Cut the plant cell in that hex. |
| `slice` | `hexes` | Cut along a path. `hexes` is a list of 1 to 512 `[q, r]` pairs in the order to cut. |
| `pause` | | Stop the clock. |
| `resume` | | Start the clock. |
| `step` | `n` | Grow for `n` iterations (a whole number from 1 to 1000). Only while paused. |

Unknown fields are rejected.

`slice` cuts each hex that holds a living, non-root cell when its turn comes, and skips every other hex: empty hexes, stumps, and roots. It never returns `nothing_to_cut`, and a path that cuts nothing still gets an `update`. All cuts of one `slice` land on the same iteration. Removing a whole plant takes a `cut` on its root.

## Server to client

### `welcome`

Sent once after connecting.

| Field | Meaning |
|---|---|
| `room` | Room id |
| `mode` | Room mode, `"sandbox"` |
| `seed` | The room's random seed |
| `species` | List of `{id, name, default_speed}` |
| `clock` | `"running"` or `"paused"` |
| `tick` | Current iteration number |
| `cells` | Every cell on the board |
| `tips` | Every growing tip |

### `update`

Sent after every iteration and after every applied command. Apply `removed`, then `added`, then `changed`.

| Field | Meaning |
|---|---|
| `tick` | Current iteration number |
| `added` | New cells |
| `removed` | Hexes that became empty, as `[q, r]` pairs |
| `changed` | Cells whose kind changed (a segment that became a stump) |
| `tips` | The complete current list of tips |
| `clock` | `"running"` or `"paused"` |

A cell is `{q, r, plant, kind, parent}`. `kind` is `"root"`, `"segment"`, or `"stump"`. `parent` is the `[q, r]` of the neighbouring cell toward the root, or `null` for a root.

A tip is `{id, plant, q, r, heading, progress, blocked}`. It sits on the cell at `q`, `r` and grows toward the neighbour in direction `heading`. `progress` is how far it is toward its next hex, from 0 up to 1. `blocked` is true while that next hex is occupied.

### `error`

Sent only to the client whose message was rejected. The game is unchanged.

| Code | Reason |
|---|---|
| `bad_message` | The message is not valid JSON, has an unknown type, or has missing or invalid fields |
| `not_permitted` | The room's mode does not allow this command |
| `occupied` | A seed was planted on an occupied hex |
| `unknown_species` | The species id is not in the catalog |
| `bad_speed` | The speed is not a number above 0 and at most 10 |
| `nothing_to_cut` | The hex is empty or holds a stump |
| `not_paused` | `step` was sent while the clock is running |
| `bad_step` | `n` is not a whole number from 1 to 1000 |
| `board_full` | A seed was planted on a board that has reached its size limit |

Every error also has a `message` suitable for showing to the player.

### `notice`

| Code | Meaning |
|---|---|
| `board_full` | The board reached its size limit (20,000 occupied hexes). The room pauses itself; the preceding `update` carries the paused clock. |
