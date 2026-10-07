# Tasks

## 1. Simulation

- [x] 1.1 Add `World.clear()` and a `cleared` flag on `Changes` that `merge` treats as a reset and `apply_to` honors; verify unit tests for clearing a crowded board (stumps and waiting tips included), the tick being kept, a plant planted afterwards getting an unused id and growing, clearing an empty board, and a merged record containing a clear replaying onto a client map correctly
- [x] 1.2 Add the region test (`|dr| <= half_height` and `|dq + dr / 2| <= half_width`) and `World.scatter(count, region, owner)` as designed; verify unit tests that 20 seeds land on 20 different empty hexes inside the region with default speeds and the scattering player as owner, that occupied hexes are never used and existing cells are untouched, and that the plants grow
- [x] 1.3 Add unit tests for the species draw: over many scattered seeds every species without settings appears and `custom` never does, and repeated scatters of 7 seeds include repeats of a species; verify they pass
- [x] 1.4 Add unit tests for shortfalls: 50 asked with 12 empty hexes plants exactly those 12, a full region plants none and leaves the board unchanged, and a board with room for 3 more cells plants 3; each reports `asked` and `planted`; verify they pass
- [x] 1.5 Add unit tests that two same-seed worlds scatter identically and two different seeds differ; verify they pass

## 2. Protocol and rooms

- [x] 2.1 Add the `clear` and `scatter` command models (`count` 1 to 500, half-sizes 0 to 150, bounded coordinates); verify unit tests that valid commands parse and that a zero, oversized, fractional, or missing count and an oversized region fail with `bad_message`
- [x] 2.2 Handle both commands in the room with mode permission checks, add `cleared` and `scattered` to every update, and leave the clock and tick untouched; verify unit tests for clear while running and while paused, the cleared update listing no hexes on a board with thousands of cells, scatter reporting asked and planted, scatter while paused, and a stub mode rejecting both with `not_permitted`
- [x] 2.3 Extend the websocket test client to honor `cleared` and add a test that scatters, grows, clears, scatters again, and ends with the client's board and plant details equal to the server's; verify it passes
- [x] 2.4 Document `clear`, `scatter`, `cleared`, and `scattered` in `docs/protocol.md`, including the region rule; verify the document matches the models

## 3. Client

- [x] 3.1 Add the Random group (number field starting at 10, Plant button) and the Clear button to the top bar in `index.html` and `css/style.css`, with Clear set apart and styled as a quieter destructive action; verify the layout at a wide and a 1000-pixel-wide window
- [x] 3.2 Handle `cleared` and `scattered` in `net.js` and add `clear()` and `scatter(...)` send functions; verify in the browser console that after `clear()` the cell and plant maps are empty
- [x] 3.3 Compute the visible region in `main.js` from the area between the two bars and wire the Plant button, including the invalid-count message; verify in the browser that every new root is on screen and clear of both bars at a large and a small hex size, and that zooming out spreads the next scatter wider
- [x] 3.4 Wire the Clear button and the disabled state of both controls while disconnected; verify clearing while running and while paused, that the cell count reads zero and the plant readout empties, and that tools work on the empty board afterwards
- [x] 3.5 Show the shortfall messages from `scattered`; verify "12 of 50", none planted, and no message when all are planted
- [x] 3.6 Update `README.md` with the two controls; verify the text matches the behavior

## 4. Integration check

- [x] 4.1 Run the full backend test suite and confirm it passes
- [x] 4.2 Play through in a browser with the metrics on: scatter 50, watch them grow, clear, scatter 200 zoomed out, clear while running, and confirm planting, cutting, mowing, panning, the clock controls, and the metrics panel still behave
