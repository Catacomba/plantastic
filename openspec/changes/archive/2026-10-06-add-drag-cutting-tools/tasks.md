# Tasks

## 1. Simulation

- [x] 1.1 Add `World.slice(hexes)` that cuts each living non-root cell in order, skips empty hexes, stumps, and roots, and returns one merged `Changes`; verify with unit tests for a path across two vines with empty hexes between, a path of only empty hexes and stumps, and a path that leaves the tick unchanged
- [x] 1.2 Add unit tests for ordering along one vine: root-to-tip leaves a stump at the first visited cell, tip-to-root leaves a stump only at the last visited cell; verify both pass
- [x] 1.3 Add unit tests for root protection: a path over a root, and a one-hex path on a root, both leave the plant intact while other hexes in the path are still cut; verify both pass
- [x] 1.4 Add a unit test that replaying the `Changes` from a slice onto a client-style cell map reproduces the world; verify it passes

## 2. Protocol and rooms

- [x] 2.1 Add the `slice` command model with 1 to 512 hexes of bounded whole-number coordinate pairs; verify unit tests that an empty list, 513 hexes, a non-pair, and fractional coordinates fail validation with `bad_message`
- [x] 2.2 Handle `slice` in the room: check the mode's permission, apply `World.slice`, return one update; verify unit tests for slicing while running and while paused (tick unchanged, clock unchanged), a path that cuts nothing returning an update and no error, and a stub mode rejecting it with `not_permitted`
- [x] 2.3 Add a websocket test that pauses, sends two slices, and resumes, and that ends with the client-side board equal to the server's and both slices applied on the same tick; verify it passes
- [x] 2.4 Document `slice` in `docs/protocol.md`, including the hex limit and that it never returns `nothing_to_cut`; verify the document matches the models

## 3. Client building blocks

- [x] 3.1 Add `hexDistance` and `hexLine(from, to)` to `hex.js` and extend `selfCheck`; verify in Node that every line starts and ends on its endpoints, has distance + 1 hexes, and has only neighboring consecutive hexes, for a sample of endpoint pairs
- [x] 3.2 Add `slice(hexes)` to `net.js`; verify in the browser console that calling it across a vine produces a stump
- [x] 3.3 Add `Board.setStroke(hexes)` drawing translucent hexagons between the grid and the plants, cleared by an empty list; verify in the browser that a list of hexes is highlighted and then cleared
- [x] 3.4 Add the Mower button to the tool bar in `index.html` and `ui.js`, with tooltips on the three tools naming what press and drag do; verify the three buttons behave as one radio group and that species and speed are enabled only for the seed tool

## 4. Pointer handling and tools

- [x] 4.1 Rework pointer handling in `main.js` to derive state from `event.buttons`: right or middle held pans by the pointer delta, left rising and falling start and end the tool action; prevent the context menu and middle-button autoscroll on the canvas and remove the drag threshold; verify in the browser that right-drag and middle-drag pan, left-drag does not, and no context menu appears
- [x] 4.2 Seed tool: plant on left press at the pressed hex and ignore the rest of the drag; verify that dragging with the seed tool plants exactly one seed
- [x] 4.3 Scissors: slice the pressed hex on press, slice the hexes from `hexLine` (minus the starting hex) on each move, and on release send `cut` when the cursor never left a starting hex that holds a root; verify in the browser a drag across several branches while running, a fast drag with widely spaced positions leaving no gap, a stroke over a root leaving the plant, and a click on a root removing it
- [x] 4.4 Mower: on press record whether the clock is running and send `pause` if so; collect the stroke without repeats and preview it; on release send `cut` for a single root hex or else `slice` in chunks of 512, then `resume` if it was running; verify in the browser that nothing is cut during the drag, all cuts land on one tick at release, the game resumes afterwards, and an already paused game stays paused
- [x] 4.5 Mower cancel: Escape, `pointercancel`, and window blur clear the preview, cut nothing, resume if the clock was running at the press, and make the later button release do nothing; verify each of the three in the browser
- [x] 4.6 Extend an active stroke from the keyboard pan callback and from right-drag panning, so hexes passing under the cursor join the stroke; verify by holding a cutting tool still while panning with WASD across a vine
- [x] 4.7 Update the controls section of `README.md` for the scissors, the mower, and right or middle button panning; verify the text matches the behavior

## 5. Integration check

- [x] 5.1 Run the full backend test suite and confirm it passes
- [x] 5.2 Play through in a browser: plant several seeds, cut live with the scissors while growing, mow across several plants, cancel a mow, click a root with each tool, pan with the right button, the middle button, and the keyboard, change hex size, and use Pause and Grow; confirm each matches the specs and that empty strokes show no error
