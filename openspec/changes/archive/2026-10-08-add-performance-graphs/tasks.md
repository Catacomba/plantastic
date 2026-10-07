# Tasks

## 1. History in the metrics module

- [x] 1.1 In `frontend/js/metrics.js`, add the 120-entry handling-time and tip-count histories, record one entry of each in `update()` before the early return for updates without `stats`, empty both in `reset()`, and return them from `snapshot()` as `history`; verify in the browser console that with `plantastic.metrics.enabled = true`, calling `plantastic.metrics.update({ bytes: 1, handleMs: 2, tips: 3, stats: null })` 130 times leaves both `snapshot().history` arrays at length 120, and that setting `enabled = false` empties them
- [x] 1.2 In `frontend/js/main.js`, pass `tips: state.tips.length` in the `metrics.update` call inside `redraw`; verify with the metrics on and a plant growing that the last entry of `plantastic.metrics.snapshot().history.tips` equals `plantastic.net.state.tips.length` after each update, and that with the metrics off the arrays stay empty while the game runs

## 2. Graphs box

- [x] 2.1 Add the `#graphs` box after `#metrics` in `frontend/index.html`, with a label row and a canvas for each graph (accessible names and `title` tooltips in the style of the panel rows), and style it in `frontend/css/style.css` to match the metrics panel; verify with the `hidden` attribute removed by hand that the box sits directly under the metrics panel at the same width and that the board beside the column still takes clicks
- [x] 2.2 In `frontend/js/ui.js`, show and hide `#graphs` in `setMetrics` together with the metrics panel; verify that the switch shows and hides both, that a reload with the metrics on shows both, and that minimizing the settings menu leaves both visible
- [x] 2.3 Add `drawGraphs(history)` to `ui.js` as designed (canvas sized from its CSS box and `devicePixelRatio`, newest point at the right edge, zero-based scale fitted to the largest value in view, colors from the CSS variables) and call it from `showMetrics`; verify with a Burst growing that both lines advance from the right one point per update, that the tips line rises, and that the lines stay sharp at 100% and 200% browser zoom
- [x] 2.4 Fill in each graph's label with its latest value and the largest value in view, using the panel's existing number formatting; verify the labels against `plantastic.metrics.snapshot().history` in the console, and that an empty board shows a flat tips line with a largest value of 0
- [x] 2.5 Describe the graphs in the performance metrics section of `README.md`, including that the horizontal axis is one point per update and that the switch governs them; verify the text matches the behavior

## 3. Integration check

- [x] 3.1 Play through in a browser with the metrics on and confirm each spec scenario: scatter 200 and watch both graphs fill and scroll past 120 points; pause and confirm the graphs stand still, then plant a seed and confirm one new point; Grow for 100 and confirm one new point; Clear and confirm the tips graph drops to zero; turn the metrics off and on and confirm the graphs restart empty
- [x] 3.2 Run `.venv\Scripts\python -m pytest backend` and confirm it still passes, and confirm that planting, cutting, mowing, panning, and the metrics panel rows behave as before
