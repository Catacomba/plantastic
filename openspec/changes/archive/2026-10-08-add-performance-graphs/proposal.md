# Proposal

## Why

The performance metrics panel shows only the latest values, so a spike in the time the browser takes to handle an update is gone 250 ms later, and there is no way to see whether that time is climbing as a board grows. Seeing the recent history next to the number of tips makes the trend, and what moves with it, visible at a glance.

## What Changes

- **Two small graphs in a new box directly below the metrics panel**:
  - **Update handling time**: the milliseconds the browser took to read each update from the server and rebuild the board. This is the same value the panel's Update row shows as "to handle".
  - **Tips**: the number of growing tips after each update.
- Both graphs plot one point per update from the server and share the same horizontal axis, so a point in one lines up with the point for the same update in the other.
- Each graph shows its latest value and the largest value in view, and scales its height to that largest value.
- The graphs follow the existing **Performance metrics** switch. There is no separate switch. With the metrics off, the box is hidden, the history is discarded, and nothing is recorded.

Decisions made while writing this up that were proposed during exploration and not explicitly confirmed: one point per update instead of one per unit of time; a history of the last 120 updates (about a minute at the default clock speed); the vertical scale fitting the largest value in view; and each graph showing its latest and largest values as text.

Out of scope: a graph of the server's iteration time, a cell-count graph, a floating or draggable window, and any change to how updates are handled.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `game-client`: adds the performance graphs shown below the metrics panel.

## Impact

- Frontend: `js/metrics.js` (history of recent updates), `js/main.js` (passes the tip count with each update), `js/ui.js` (draws the graphs), `index.html`, `css/style.css`.
- Docs: `README.md`, in the performance metrics section.
- No backend or protocol change, and no new dependency.
