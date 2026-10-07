# Design

## Context

See proposal.md for motivation and specs/game-client/spec.md for the required behavior. What the code does today:

- `metrics.js` is pure bookkeeping with no DOM access. It holds the latest values and a 10-entry list for the "Last 10" average. `reset()` runs when `enabled` is set to false.
- `net.js` stamps `performance.now()` and the message length on arrival, only while `measuring` is on. `main.js` `redraw(state, meta)` calls `metrics.update(...)` after the board is rebuilt, with `handleMs = performance.now() - meta.arrived`. `welcome` calls `redraw(state)` with no `meta`, so it is not measured.
- The tip count is not in `metrics.js`. `boardCounts()` in `main.js` counts from `net.state.tips` when the panel refreshes.
- `ui.js` `setMetrics(on)` shows or hides `#metrics`, calls `onMetrics`, and runs `showMetrics` on a 250 ms interval while on.
- `#side` is a right-aligned column of `.box` elements, 300 px wide. Colors come from CSS variables on `:root`.
- The frontend has no build step, no dependencies besides the vendored three.js, and no automated tests.

## Goals / Non-Goals

**Goals:**

- Keep `metrics.js` free of the DOM and keep "off means nothing measured" true for the graphs.
- Add no measurable cost to handling an update: recording a point is two array pushes.
- No new dependency.

**Non-Goals:**

- Hover read-outs, zooming, axes with tick marks, or a configurable history length.
- A frontend test framework.

## Decisions

### 1. History lives in `metrics.js` as two parallel arrays

`metrics.js` gains `HISTORY = 120` and two arrays, `handleHistory` and `tipHistory`. `update()` takes a new `tips` field and pushes one entry to each, shifting the oldest once the length passes `HISTORY`. The push happens before the existing early return for updates without `stats`, because command updates (plant, cut, clear) are handled and change the tip count too. `reset()` empties both, which gives "off discards the history" through the existing path.

`snapshot()` returns them as `history: { handleMs, tips }`, handing out the arrays themselves; the UI only reads them.

`main.js` passes `tips: state.tips.length` in the `metrics.update` call it already makes.

*Alternatives considered:* a typed-array ring buffer (no benefit at 120 entries, and it differs from the `recent` list already there); sampling the tip count from `boardCounts()` on the 250 ms timer (points would no longer line up with updates, and it would record while paused).

### 2. One point per update, not per unit of time

A point is recorded exactly when `metrics.update` runs. Both values belong to an update, so this is the only sampling that keeps the two graphs aligned and never invents or drops data. At the default 500 ms clock, 120 points is about a minute of running.

*Alternative considered:* a fixed time axis. It needs resampling or gaps, and repeats stale points while paused.

### 3. Drawn on two 2D canvases from the existing refresh timer

A new `<section id="graphs" class="box" hidden>` follows `#metrics` in `#side`. It holds, for each graph, a label row (name on the left, "latest (peak N)" on the right) and a `<canvas>` with `role="img"` and an `aria-label`. Text stays in the DOM so it uses the page font and the same number formatters as the panel (`millis`, `whole`).

`showMetrics()` calls a new `drawGraphs(history)` after it fills in the rows. `setMetrics(on)` hides or shows `#graphs` alongside `#metrics`. No second timer and no second switch.

Each canvas is sized once per draw from its CSS box and `devicePixelRatio`, so it stays sharp and follows a zoom change. The line is drawn with one path:

- x: point `i` of `n` sits at `width - (n - 1 - i) * step`, with `step = width / (HISTORY - 1)`. The newest point is always at the right edge and a partly filled history grows leftward from there. Both graphs use the same rule, which is what lines them up.
- y: `height - (value / scale) * height`, inset by 1 px top and bottom so the stroke is not clipped. `scale` is the largest value in view, or 1 when that is zero so an all-zero history is a flat line along the bottom instead of a division by zero.
- A translucent fill under the line, in the line's color.
- With fewer than two points, a single point is drawn as a dot and none leaves the canvas blank.

Colors are read from the CSS variables with `getComputedStyle`: `--accent` for tips, matching the green of the plants, and `--text` for handling time. Canvas height is 40 CSS px.

*Alternatives considered:* SVG polylines (rebuilding a points string four times a second is no simpler and no cheaper); drawing with three.js in the board's renderer (couples a diagnostic to the scene); a charting library (a new dependency for two polylines); redrawing on each update instead of on the timer (ties drawing cost to update rate, and the text beside it refreshes on the timer anyway).

### 4. Scale fits the largest value in view

Per the spec, the axis runs from zero to the largest value in view and the label states that value. There is no fixed reference line.

*Alternative considered:* a fixed scale or a 16.7 ms frame line for handling time. Handling time ranges from well under a millisecond on a small board to tens of milliseconds on a full one, so any fixed scale is wrong at one end.

## Risks / Trade-offs

- [An auto-fitting scale makes a flat 0.3 ms history look as tall as a 30 ms one] → The peak is printed beside each graph, and the Update row above still shows the exact latest value.
- [One slow update compresses the rest of the line until it scrolls off, up to 120 updates later] → Accepted. The spike is the thing worth seeing, and the label names its size.
- [The horizontal axis is updates, not seconds, so bursts of commands compress time] → Accepted and documented in the README.
- [The time spent drawing the graphs is not part of `handleMs`] → Correct by construction: drawing runs on the interval timer, outside the measured span, so the graphs do not inflate what they show.
- [No automated frontend tests] → `metrics.js` is checked from the browser console through `window.plantastic.metrics`, and the drawing by eye, as in earlier client changes.
