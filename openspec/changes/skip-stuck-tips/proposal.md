# Proposal

## Why

On a crowded board most tips are stuck. In a measured run, 12,893 of 13,691 tips were waiting behind occupied hexes, and the count of waiting tips only ever rises. Every iteration the server still adds progress to each of them, sorts them, and visits them to fail again, and every update re-sends all of them to the browser, which is why updates grew to about 1 MB. A stuck tip can only become unstuck when a cell is removed, so all of that work is wasted until a cut, a slice, or a clear.

## What Changes

- **Sleeping tips.** A waiting tip falls asleep when nothing but a removed cell could let it move again:
  - its next hex is occupied, and
  - it either lost its persistence roll or has no free 60- or 120-degree turn.

  A sleeping tip gets no progress and no visits, and is left out of the per-iteration work entirely. It wakes when the hex ahead of it is emptied. It also wakes when one of its turn hexes is emptied, if it has not yet rolled for this hex. It wakes on a clear, and when the optimization is switched off.
- **Same game either way.** Cells, tips, random draws and replays are identical whether the optimization is on or off. Only the cost differs:
  - Fewer tip visits are reported, because sleeping tips are not visited.
  - A tip that waits only because the board is full stays awake, since the room pauses itself then anyway.
- **Updates carry only awake tips.** Each update lists only the awake tips. A tip is sent once when it falls asleep, and again when it leaves the sleeping set, whether it woke up or was cut away. The welcome lists all sleeping tips once. With the optimization off, nothing sleeps, and updates look exactly as they do today, with every tip listed.
- **Protocol:**
  - New fields: `sleeping` on `welcome`; `slept` and `woke` on `update`; `skip_stuck` on both.
  - New command `skip_stuck` with `enabled: true|false`. A room starts with it on.
  - `tips` keeps its meaning of all awake tips.
- **Settings menu.** A **Skip stuck tips** switch, on by default and remembered in the browser like the metrics switch. The client sends it when it connects, and whenever it changes.
- **Metrics panel.** The Tips row also shows how many tips are asleep.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `plant-simulation`: new behaviour for stuck tips (sleep and wake). The visit requirement now says sleeping tips are not visited.
- `game-rooms`: the `skip_stuck` command and flag, and state synchronization that sends sleeping tips once.
- `game-client`: the Settings switch, keeping sleeping tips between updates, and the asleep count in the metrics.

## Impact

- `backend/plantastic/sim/world.py`:
  - tips are split into awake and sleeping, with a watch index from each hex to the sleeping tips waiting on it
  - waking happens in `_remove_cells` and `clear`
  - `step` touches only awake tips
  - `Changes` records which tips slept and which woke
- `backend/plantastic/server/protocol.py` and `rooms.py`: the `skip_stuck` command, and the `sleeping`, `slept`, `woke` and `skip_stuck` fields.
- Frontend:
  - `frontend/js/net.js`: keeps the sleeping set, and draws awake and sleeping tips together
  - `frontend/js/ui.js`, `frontend/index.html`: the switch
  - `frontend/js/main.js`: the counts
- `docs/protocol.md` and `README.md`.
- Tests:
  - an equivalence test, the same seed with the optimization on and off, every iteration
  - wake cases
  - the visit counts
  - the `ClientBoard` helper in `backend/tests/test_app.py` learns the sleeping set
