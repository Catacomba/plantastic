# Design

## Context

See proposal.md for motivation. What the code does today, and what a measurement during exploration showed:

- `World.step` adds progress to every tip, then runs rounds: it sorts all tips and calls `_advance` on each tip that is due and has not stalled this iteration, repeating until no tip moved. Waiting tips are visited every iteration.
- `Room.tick` and `Room._step` call `World.step` and build an `update` that contains the changed cells and the complete list of tips.
- With six branch-heavy custom plants, an iteration at 10,000 tips took about 53 ms on the development machine and produced an update of about 930 KB. Compute was well inside the 500 ms tick; the update size was the larger cost. Over 90 percent of the tips were waiting.
- The browser redraws every cell on each update (`Board.setCells`) and every tip on each frame (`Board.drawTips`). Nothing measures either.
- The top bar holds the clock controls, the counters, the plant readout, and the hex size slider. The tool bar's species settings panel already uses the element id `settings`.

## Goals / Non-Goals

**Goals:**

- Show, while playing, what drives cost: tips for the server, cells and update size for the browser.
- Keep the simulation deterministic and the measurement free of side effects on the game.
- Cost nothing in the browser when the metrics are off.

**Non-Goals:**

- Any limit, throttle, or optimization. This change only measures.
- Profiling inside an iteration (per species, per phase), history graphs, or exporting measurements.
- Measuring the server's serialization and send time. The update size and the browser's handling time stand in for the cost of the update.

## Decisions

### 1. Tip visits are counted in `Changes`

`Changes` gains `visits: int`, incremented in `World.step` each time `_advance` is called. `Changes.merge` sums it. This is the user's "how many computations" number: it is exactly the number of times the loop did per-tip work, it needs no clock, and it is the same on every replay.

*Alternatives considered:* counting tips times rounds (overstates the work, since stalled and not-yet-due tips are skipped cheaply), or counting only successful moves (hides the cost of waiting tips, which is the main finding so far).

### 2. Timing is taken in the room, not in the simulation

`Room.tick` and `Room._step` wrap their calls to `World.step` in `time.perf_counter()`. The simulation never sees a clock. Growth updates gain:

```
"stats": {"iterations": 25, "step_ms": 12.37, "visits": 4810}
```

`step_ms` is rounded to two decimals and is the total for the batch. Updates that do not advance the board carry `"stats": null`. `welcome` gains `"tick_ms"`, the room's tick interval in milliseconds.

The tip, waiting, cell, and plant counts are not sent: the client already holds the tip list (with each tip's `blocked` flag), the cell map, and the plant map, and counts them itself.

*Alternative considered:* a separate `stats` message. Rejected; it would double the messages per tick for a handful of numbers.

### 3. Client measurement lives in `metrics.js`

A small module with no DOM access:

- `frame(now)`: called from the render loop; keeps the timestamps of the last second and reports frames per second.
- `update({bytes, handleMs, stats, tips, cells, plants})`: called after each update is applied and drawn.
- `snapshot()`: the values to display, including a rolling average of per-iteration time over the last 10 growth updates and the last "Grow N" batch.
- `enabled`: when false, `frame` and `update` return at once.

`net.js` records `performance.now()` and the message length when a message arrives and passes them to `onUpdate`; `main.js` calls `metrics.update` after `redraw`, so the handling time covers parsing, applying, and rebuilding the board's meshes. The actual GPU draw happens on the next frame and shows up in the frame rate instead.

Update size is the length of the message text in characters. The protocol is ASCII, so this equals bytes.

### 4. Display

`ui.js` refreshes the panel every 250 ms from `metrics.snapshot()` while the metrics are on, using a timer that is stopped when they are off. Rows:

| Row | Example |
|---|---|
| FPS | 60 |
| Iteration | 11.1 ms (2% of 500 ms) |
| Iteration, last 10 | 9.8 ms |
| Tip visits | 2,294 |
| Tips | 2,294 (1,616 waiting) |
| Cells | 2,805 |
| Plants | 6 |
| Update | 206 KB, 14 ms to handle |
| Last grow | 100 iterations, 400 ms, 4.0 ms each |

Numbers use tabular figures and fixed-width value cells so the panel does not jitter. "Last grow" is hidden until a batch has run.

### 5. Settings menu and layout

A fixed column at the top right, below the top bar, holds two boxes: the settings menu and the metrics panel.

- The menu's header is a `button` with `aria-expanded`; its body is hidden when minimized. The column itself ignores pointer events and only the boxes receive them, so the board stays usable around and beneath a minimized menu.
- The body holds a checkbox, "Performance metrics", and the hex size slider, which keeps its element id `hex-size` so the existing wiring in `ui.js` and `main.js` continues to work.
- The new elements use the ids `menu`, `menu-toggle`, `menu-body`, `metrics-toggle`, and `metrics`, avoiding the existing `settings` id of the species panel.
- Two `localStorage` keys, `plantastic.menuOpen` and `plantastic.metrics`, are read and written through the same try/catch helpers as the hex size.

The toast and the disconnect banner are centered and stay where they are; the column is narrow enough not to reach them at ordinary widths.

*Alternative considered:* a dropdown hanging off a gear button in the top bar. Rejected because the request was for a menu that stays in place and minimizes, and because the metrics panel needs a home that does not close when the menu does.

## Risks / Trade-offs

- [The panel covers part of the board at the top right] → It is off by default, narrow, and the menu minimizes to one line.
- [Counting tips and waiting tips on the client is itself work per update] → One pass over a list the client has just parsed, and only while the metrics are on.
- [`step_ms` varies with machine load] → It is a measurement, shown alongside a rolling average. The visit count is the stable number to compare across runs.
- [Frame rate is capped by the display and drops to nothing in a background tab] → Stated in the README, so a low number in a hidden tab is not read as a problem.
- [Handling time excludes the GPU draw] → Documented in the panel's tooltip; the frame rate reflects it.

## Open Questions

- Whether a later change should send only the tips that changed and skip waiting tips in the loop. The metrics from this change are what that decision would rest on.
