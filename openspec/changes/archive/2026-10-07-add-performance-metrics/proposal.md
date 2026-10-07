# Proposal

## Why

With eight species, some of which branch without limit, a board can go from a handful of tips to thousands in seconds, and there is no way to see what that costs. A measurement taken while exploring showed that the cost follows the number of growing tips, not the number of plants, and that most of it is in what is sent to the browser, not in the simulation itself. Before limiting or optimizing anything, the game needs to show these numbers while it is played.

## What Changes

- **A performance metrics panel** in the browser showing:
  - frames per second;
  - the server's compute time for the latest iteration in milliseconds, its share of the time available per iteration, and a recent average;
  - the work done in that iteration, counted as tip visits (each attempt to move a tip that is due);
  - the number of tips, how many of them are waiting, and the number of cells and plants;
  - the size of the latest update and how long the browser took to handle it;
  - for "Grow N", the number of iterations, the total compute time, and the average per iteration.
- **A settings menu at the top right** that can be minimized to one line and expanded again. It holds a switch for the performance metrics and the hex size slider.
- **The hex size slider moves** from the top bar into the settings menu. The mouse wheel still changes hex size, and the slider follows it.
- **The metrics are off by default**, and the browser measures nothing while they are off. Whether the menu is minimized and whether metrics are on are remembered in the browser.
- The server counts tip visits in the simulation and times each iteration, and includes both in the updates it already sends.

This change only measures. It adds no limit on plants or tips and no optimization. The existing board limit of 20,000 cells is unchanged.

Decisions made while writing this up that were proposed during exploration and not explicitly confirmed: which extra numbers are shown beyond the three requested, the metrics panel being separate from the menu so that minimizing the menu does not hide it, and the menu starting minimized with metrics off.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `plant-simulation`: each iteration reports how many tip visits it made.
- `game-rooms`: updates that advance the board report the compute time, the number of iterations, and the tip visits; the welcome reports the time available per iteration.
- `game-client`: adds the settings menu and the performance metrics panel; the hex size slider moves into the menu.

## Impact

- Backend: a counter in `sim/world.py`; timing and a `stats` field in `server/rooms.py`; tests.
- Frontend: `index.html`, `css/style.css`, `ui.js`, `net.js`, `main.js`, and a new `metrics.js`.
- Docs: `docs/protocol.md` and `README.md`.
- The `update` and `welcome` messages gain fields; existing fields are unchanged.
- The simulation stays deterministic: the visit count is a pure function of the board, and timing is taken outside the simulation and never read by it.
