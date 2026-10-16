# Proposal

## Why

A running room advances one iteration every 0.5 seconds, so watching a board fill up takes minutes. **Grow** can jump ahead only while the game is paused, and only by a set number of iterations. Players want to speed the live game up and watch it grow faster, without the browser falling behind and stalling.

## What Changes

- Rooms get a **game speed**, one of 1x, 2x, 5x, 10x and Max. It starts at 1x and stays as set across pause and resume, the mower's pause, and a full-board pause.
- At 1x to 10x the clock waits the room's base interval divided by the speed between iterations: 500, 250, 100 and 50 ms by default. Each iteration still sends its own update.
- At Max the clock does not wait at all. After each clock update it waits for the browser to acknowledge that it has applied and drawn that update, then runs the next iteration. The game therefore runs as fast as the slower of the server and the browser, and the browser never falls behind. A browser tab in the background stops drawing, so a Max room effectively waits until the tab is visible again.
- New client commands: `speed` sets the game speed, and `ack` reports the iteration the client has drawn. The welcome and every update carry the room's `speed`, and the time available per iteration, which is `null` at Max.
- The clock bar gets a row of speed buttons, 1x, 2x, 5x, 10x and Max, with the current one highlighted. The metrics panel works out its "share of the time available" from the current speed and shows no share at Max.
- **Grow** while paused is unchanged.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `game-rooms`: "Clock" gains speeds and Max pacing driven by the client's acknowledgements. "Updates report iteration cost" now reports the time available per iteration on every update, depending on speed.
- `game-client`: "Clock controls" gains the speed buttons. The client acknowledges each drawn update, and the metrics panel's share of the time available follows the speed.

## Impact

- `backend/plantastic/server/protocol.py`: `SpeedCommand` and `AckCommand`, and a `bad_game_speed` error.
- `backend/plantastic/server/rooms.py`: speed state, interval per speed, and `run_clock` waiting for an acknowledgement at Max. `speed` and `tick_ms` go into `welcome` and `_update`.
- `frontend/index.html`, `frontend/js/ui.js`, `frontend/js/net.js`, `frontend/js/main.js`, `frontend/js/metrics.js`, `frontend/css/style.css`: the speed buttons, sending `ack` after drawing, and the metrics budget.
- `docs/protocol.md` and `README.md`: the new commands, fields and controls.
- Tests: `backend/tests/test_rooms.py` and `backend/tests/test_app.py` for speed pacing, Max acknowledgements, validation, and reporting.
- Server and browser load rise with speed. That is the point, and the metrics panel shows it.
