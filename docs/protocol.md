# Websocket protocol

The client connects to `/ws`. Every message is a JSON object in a text frame with a `type` field. The server is the only authority over the game: the client sends commands and applies what the server reports.

Hexes are axial coordinates `q`, `r` on a pointy-top grid. Directions are numbered 0 to 5 clockwise on screen from east: `(1,0)`, `(0,1)`, `(-1,1)`, `(-1,0)`, `(0,-1)`, `(1,-1)`.

Exact numbers (speeds and progress) are strings such as `"0.25"` or `"1/4"`.

## Client to server

| Type | Fields | Meaning |
|---|---|---|
| `plant` | `q`, `r`, `species`, `speed`, `settings`, `persistence` | Plant a seed. `speed` is hexagons per iteration, above 0 and at most 10. `settings` is an object, required for a species that has settings and left out (or `null`) for one that has none. `persistence` is optional; see below. |
| `cut` | `q`, `r` | Cut the plant cell in that hex. |
| `slice` | `hexes` | Cut along a path. `hexes` is a list of 1 to 512 `[q, r]` pairs in the order to cut. |
| `clear` | | Remove every plant from the board. |
| `scatter` | `count`, `q`, `r`, `half_width`, `half_height`, `persistence` | Plant `count` random seeds (1 to 500) inside a region. `persistence` is optional; see below. |
| `pause` | | Stop the clock. |
| `resume` | | Start the clock. |
| `step` | `n` | Grow for `n` iterations (a whole number from 1 to 1000). Only while paused. |
| `speed` | `speed` | Set the game speed: `1`, `2`, `5`, `10`, or `"max"`. Allowed while running or paused; it neither pauses nor resumes. |
| `ack` | `tick` | Report that the update for iteration `tick` (a whole number, 0 or more) has been applied and drawn. Never answered. |
| `skip_stuck` | `enabled` | `true` or `false`: whether stuck tips sleep. Allowed while running or paused. A room starts with it on. |

Unknown fields are rejected.

`speed` paces the clock. At `1` to `10` the room waits its base interval (0.5 s by default) divided by the speed between iterations, and sends one update per iteration. At `"max"` it does not wait a fixed time: after each clock update it waits for an `ack` of that iteration or a later one, then runs the next iteration at once, so it never sends more than one unacknowledged update. A client should send `ack` after drawing every update that has `stats`, at any speed; acks that nothing is waiting for are ignored. A room starts at `1`, and the speed lasts until changed, through pauses and a full board.

`skip_stuck` lets the server stop working on tips that cannot move. A tip **falls asleep** when the hex ahead of it is occupied, the board is not full, and it either lost its persistence roll or has no empty hex 60 or 120 degrees to either side. Only a removed cell can free it, so until then it gains no progress and is not visited (it adds nothing to `visits`). It **wakes** when the hex ahead of it is emptied, or, if it has not lost its roll, when one of those turn hexes is; and every sleeping tip wakes when `skip_stuck` is switched off. Cutting a cell leaves a stump, so only cutting a root, or cutting further back, empties a hex. The game is identical with it on or off: the same cells, tips, and random draws. The answer is an `update` with `skip_stuck` set and, when switching off, every woken tip listed in `woke` and back in `tips`.

`slice` cuts each hex that holds a living, non-root cell when its turn comes, and skips every other hex: empty hexes, stumps, and roots. It never returns `nothing_to_cut`, and a path that cuts nothing still gets an `update`. All cuts of one `slice` land on the same iteration. Removing a whole plant takes a `cut` on its root.

`persistence` on `plant` and `scatter` is a whole number from 0 to 100 that every new seed gets in place of its species' default, including a custom seed, whose own `persistence` setting it overrides. Leave it out, or send `null`, for each species' default. A number out of range is rejected with `bad_persistence`; anything that is not a whole number or `null` is `bad_message`.

`clear` empties the board and nothing else: the iteration number, the clock, and plant numbering carry on.

`scatter` plants seeds on random empty hexes of a region. The region is a rectangle as seen on screen, centred on hex `q`, `r`: a hex at `q + dq`, `r + dr` is inside when `|dr| <= half_height` and `|dq + dr / 2| <= half_width`. Both half-sizes are whole numbers from 0 to 150. Each seed's species is drawn at random, independently, from the species with no settings, and it gets that species' default speed and a random direction. If the region or the board has room for fewer seeds, as many as fit are planted; that is not an error. The choices come from the room's random seed.

## Server to client

### `welcome`

Sent once after connecting.

| Field | Meaning |
|---|---|
| `room` | Room id |
| `mode` | Room mode, `"sandbox"` |
| `seed` | The room's random seed |
| `species` | List of `{id, name, default_speed, persistence, settings}`; see below |
| `clock` | `"running"` or `"paused"` |
| `speed` | The game speed: `1`, `2`, `5`, `10`, or `"max"` |
| `tick` | Current iteration number |
| `tick_ms` | Milliseconds available for one iteration while the clock runs at this speed, or `null` at `"max"` |
| `cells` | Every cell on the board |
| `tips` | Every awake tip |
| `sleeping` | Every sleeping tip. Keep these: they are not sent again until they wake or are removed |
| `skip_stuck` | Whether stuck tips sleep |
| `plants` | Every plant on the board, as `{id, species, speed, settings, persistence}` |

`persistence` is the percent chance, from 0 to 100, that a blocked tip of that species takes another path: it turns into an empty hex 60 degrees to either side, or if neither is empty 120 degrees to either side, instead of waiting. It never turns straight back. It is `null` for the custom species, whose plants each take it from their settings.

Each species lists its `settings`, which is empty for most. A setting is `{id, label, kind, default}` plus `min` and `max` for the kinds `percent`, `int`, and `optional_int`, or `choices` (a list of `{id, label}`) for the kind `choice`. An `optional_int` also accepts `null`. A `plant` command for such a species must give a value for every setting and nothing else.

The custom species has: `branch_chance`, `turn_chance`, and `persistence` (0 to 100), `branch_min` and `branch_max` (1 to 4, min not above max), `calm_min` (0 to 1000), `calm_max` (`null` for never, or `calm_min` to 1000), and `cut_response` (`fork`, `regrow`, `none`, `multiply`).

### `update`

Sent after every iteration and after every applied command. Apply `removed`, then `added`, then `changed`.

| Field | Meaning |
|---|---|
| `tick` | Current iteration number |
| `added` | New cells |
| `removed` | Hexes that became empty, as `[q, r]` pairs |
| `changed` | Cells whose kind changed (a segment that became a stump) |
| `plants` | Plants created by this update, as `{id, species, speed, settings, persistence}`; usually empty |
| `tips` | The complete current list of awake tips |
| `woke` | Ids of tips that are no longer asleep, because they woke or were removed. Drop them from your sleeping tips; a woken one is in `tips` |
| `slept` | Tips that fell asleep, as they were then. Add them to your sleeping tips, after applying `woke` |
| `skip_stuck` | Whether stuck tips sleep |
| `clock` | `"running"` or `"paused"` |
| `speed` | The game speed, as in `welcome` |
| `tick_ms` | Milliseconds available per iteration at this speed, or `null` at `"max"` |
| `stats` | The cost of the iterations this update advanced, or `null` if it advanced none |
| `cleared` | `true` when the whole board was emptied. Empty your cells and plants first, then apply the rest of the update. The emptied hexes are not listed in `removed`. |
| `scattered` | `{asked, planted}` on the update that answers a `scatter`, otherwise `null` |

`stats` is `{iterations, step_ms, visits}`. `iterations` is how many iterations the update advanced: 1 for a clock tick, up to `n` for a `step`. `step_ms` is the server's total compute time for them in milliseconds, to two decimals. It covers the simulation only, not building or sending the update. `visits` is the number of tip visits: attempts to move a tip that was due, whether or not it moved. A tip that is waiting is visited on every iteration. `visits` depends only on the board, so it is the same on every replay; `step_ms` is a measurement and varies.

A cell is `{q, r, plant, kind, parent}`. `kind` is `"root"`, `"segment"`, or `"stump"`. `parent` is the `[q, r]` of the neighbouring cell toward the root, or `null` for a root.

A plant's `persistence` is the one it actually uses: the value it was planted with, or else its species' default. A plant's species, speed, settings, and persistence never change after it is planted, and no message announces a plant's removal: a plant with no cells left is gone.

A tip is `{id, plant, q, r, heading, progress, blocked}`. It sits on the cell at `q`, `r` and grows toward the neighbour in direction `heading`. `progress` is how far it is toward its next hex, from 0 up to 1. `blocked` is true while the tip waits behind an occupied hex, and so for every sleeping tip. A sleeping tip never changes while asleep, so the copy you were sent stays right. Every tip on the board is either in `tips` or among your sleeping tips, never both; on `cleared`, forget the sleeping tips too. A tip that takes another path around the hex moves on in the same iteration and is not reported as blocked.

### `error`

Sent only to the client whose message was rejected. The game is unchanged.

| Code | Reason |
|---|---|
| `bad_message` | The message is not valid JSON, has an unknown type, or has missing or invalid fields |
| `not_permitted` | The room's mode does not allow this command |
| `occupied` | A seed was planted on an occupied hex |
| `unknown_species` | The species id is not in the catalog |
| `bad_speed` | The speed is not a number above 0 and at most 10 |
| `bad_settings` | The settings are missing, not wanted by the species, out of range, or inconsistent; `message` names the setting |
| `nothing_to_cut` | The hex is empty or holds a stump |
| `not_paused` | `step` was sent while the clock is running |
| `bad_step` | `n` is not a whole number from 1 to 1000 |
| `bad_game_speed` | `speed` is not `1`, `2`, `5`, `10`, or `"max"` |
| `bad_persistence` | `persistence` is not from 0 to 100 |
| `board_full` | A seed was planted on a board that has reached its size limit |

Every error also has a `message` suitable for showing to the player.

### `notice`

| Code | Meaning |
|---|---|
| `board_full` | The board reached its size limit (100,000 occupied hexes). The room pauses itself; the preceding `update` carries the paused clock. |
