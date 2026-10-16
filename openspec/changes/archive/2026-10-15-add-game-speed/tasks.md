# Tasks

## 1. Protocol

- [x] 1.1 Add `SpeedCommand` (`speed`: 1, 2, 5, 10, or `"max"`) and `AckCommand` (`tick`: whole number, 0 or more) to `backend/plantastic/server/protocol.py`, rejecting other values with `bad_game_speed` and `bad_message`. Verify with new cases in `backend/tests/test_protocol.py` for each valid speed, for 3, 0, `"fast"`, `true`, and `2.5`, and for a negative or fractional ack tick.
- [x] 1.2 Document `speed` and `ack`, the `speed` and `tick_ms` fields on `welcome` and `update`, and the `bad_game_speed` error in `docs/protocol.md`. Verify that the documented fields match the messages built in `rooms.py`.

## 2. Room speed and pacing

- [x] 2.1 Add the speed state to `Room`. Handle `SpeedCommand`, which returns an update with no cost, and `AckCommand`, which returns no messages. Include `speed` and `tick_ms` (base divided by speed, or `null` at Max) in `welcome` and `_update`. Verify with tests in `backend/tests/test_rooms.py`: the default is 1x and 500 ms, setting 10x reports 50 ms, Max reports `null`, setting the speed while paused neither advances nor resumes, and the speed survives pause and resume.
- [x] 2.2 Rework `run_clock` to the pacing in design.md, with the `_wake` event, `_sent_tick`, and the reset on speed change and resume. Verify with `run_clock_for`-style tests: at 5x on a 0.05 s base the room ticks noticeably faster than at 1x; at Max with no acks exactly one tick is sent; each ack for the latest tick releases exactly one more tick; a stale ack releases nothing; switching from Max to 2x while waiting resumes ticking; pausing while waiting stops it; a full board at Max pauses and sends the notice.
- [x] 2.3 Add an end-to-end test in `backend/tests/test_app.py` over the websocket: set Max, then read and ack 20 updates in a loop. Check that the iteration numbers are consecutive and that a plant command sent in the middle is applied. Verify by running `pytest backend` with everything green.

## 3. Client

- [x] 3.1 In `frontend/js/net.js`, store `speed` and `tickMs` from `welcome` and every `update`, add `speed(value)` and `ack(tick)` senders, and acknowledge each update that carries `stats` after the next paint (animation frame, then a zero timeout). Verify in the browser at Max with the network panel: one `ack` follows each update, and updates arrive only after acks.
- [x] 3.2 Add the 1x, 2x, 5x, 10x and Max button group to the clock bar in `frontend/index.html` and `frontend/css/style.css`, and wire it in `frontend/js/ui.js`. Highlight the speed the server reports, and disable the buttons while disconnected. Verify in the browser: pressing each button highlights it after the server confirms, growth visibly speeds up, the highlight survives pause and resume, and the buttons are disabled when the server is stopped.
- [x] 3.3 Make `frontend/js/metrics.js` and the Iteration row in `ui.js` use the latest `tickMs`, including `null`. Verify in the browser with metrics on: at 10x the row reads "of 50 ms", and at Max it shows only the compute time.

## 4. Docs and integration

- [x] 4.1 Describe the speed buttons and Max's pacing by the browser, including the hidden-tab behaviour, in the Play section of `README.md`, and update the metrics table's Iteration row. Verify the README against the running app.
- [x] 4.2 Integration check: scatter 100 plants, run at Max for a minute with the metrics on, and confirm the page stays responsive to panning and cutting and that the update-handling graph shows no backlog. Then switch the tab away and back and confirm growth stalls and resumes. Run `openspec validate add-game-speed --strict`.
