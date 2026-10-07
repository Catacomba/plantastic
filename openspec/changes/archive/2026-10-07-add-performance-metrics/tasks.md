# Tasks

## 1. Server

- [x] 1.1 Add `visits` to `Changes`, incremented in `World.step` for every call to `_advance` and summed by `merge`; verify unit tests for one unobstructed tip (1), a speed-2 tip (2), a speed-0.25 tip that does not move (0), a blocked tip (1), a merged batch equal to the sum of its iterations, and two same-seed worlds reporting equal counts every iteration
- [x] 1.2 Time the simulation steps in `Room.tick` and `Room._step` with `time.perf_counter` and add `stats` (`iterations`, `step_ms`, `visits`) to growth updates, `stats: null` to other updates, and `tick_ms` to the welcome; verify unit tests for a clock tick (1 iteration), grow 25 (25 iterations and summed visits), plant, cut, slice, pause, and resume carrying `null`, and `tick_ms` of 500 for the default interval
- [x] 1.3 Add a unit test that two same-seed rooms given the same commands have identical boards after every command, and a websocket test that growth updates carry `stats` with a non-negative `step_ms`; verify both pass
- [x] 1.4 Document `stats` and `tick_ms` in `docs/protocol.md`; verify the document matches what the room sends

## 2. Client measurement

- [x] 2.1 Add `frontend/js/metrics.js` with `enabled`, `frame(now)`, `update(...)`, and `snapshot()`: frames per second over the last second, latest and 10-update average per-iteration time, share of `tick_ms`, the last multi-iteration batch, and pass-through counts; verify in Node that 61 frames 16.67 ms apart report 60 FPS, that a batch of 100 iterations and 400 ms reports 4 ms each, that 50 ms of 500 reports 10 percent, and that nothing is recorded while disabled
- [x] 2.2 Have `net.js` pass each update's arrival time and message length to `onUpdate`, and keep `tick_ms` and the latest `stats` in its state; verify in the browser console that `stats` is present after a tick and `null` after planting
- [x] 2.3 Call `metrics.frame` from the render loop and `metrics.update` after `redraw` in `main.js`, counting tips, waiting tips, cells, and plants from the client's state only while the metrics are on; verify in the browser that the snapshot's counts match the board and that no measurement is taken while off

## 3. Settings menu and panel

- [x] 3.1 Add the top-right column to `index.html` and `css/style.css`: the settings menu with a header button and a body, and the metrics panel below it; move the hex size slider from the top bar into the menu body below a "Performance metrics" checkbox; verify the top bar no longer has the slider and the column does not block clicks on the board around it
- [x] 3.2 Wire the menu in `ui.js`: the header toggles minimized and expanded with `aria-expanded`, starts minimized on a first visit, and remembers its state in `localStorage`; verify expand, minimize, reload, keyboard use of the header, and a first visit with storage cleared
- [x] 3.3 Wire the metrics switch: it shows and hides the panel, sets `metrics.enabled`, starts and stops the 250 ms refresh timer, starts off on a first visit, and is remembered in `localStorage`; verify on, off, reload with it on, and that the panel stays when the menu is minimized
- [x] 3.4 Render the panel rows from `metrics.snapshot()` with grouped thousands, one decimal for milliseconds, the percentage of the time available, and the "Last grow" row hidden until a batch has run; verify on an empty running board, during branching growth, with blocked tips, while paused, and after growing for 100 iterations
- [x] 3.5 Verify the hex size setting end to end after the move: the slider in the menu changes the size, the wheel moves the slider, the wheel works with the menu minimized, and the size survives a reload
- [x] 3.6 Update `README.md` with the settings menu, what each metric means, and the notes that tips drive server cost, cells drive redraw cost, and frame rate is capped by the display and stops in a background tab; verify the text matches the panel

## 4. Integration check

- [x] 4.1 Run the full backend test suite and confirm it passes
- [x] 4.2 Play through in a browser with the metrics on: plant a straight vine and a branch-heavy custom plant, watch the counts and times rise, grow for 100 iterations, pause, cut, and turn the metrics off and on; confirm the numbers agree with the board and that planting, cutting, mowing, panning, and the clock controls still work
