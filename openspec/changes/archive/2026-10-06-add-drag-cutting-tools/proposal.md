# Proposal

## Why

Cutting is the core action of the game, but today each cut is a separate click on a single hex. Shaping a plant with several branches, or trimming several plants, takes many precise clicks while everything keeps growing. Cutting along a dragged path makes this one gesture, and offering it in two forms lets the player choose between cutting in real time and cutting with the game held still.

## What Changes

- **Scissors become a live drag tool.** Pressing cuts the hex under the cursor, and dragging cuts every hex the cursor passes while the game keeps running.
- **New Mower tool.** Pressing pauses the game, dragging draws a preview of the stroke without cutting anything, and releasing applies every cut at once and resumes the game if it was running when the press began. Escape, or an interrupted pointer, cancels the stroke with nothing cut.
- **Strokes are forgiving.** Empty hexes and stumps in a stroke are skipped without an error message, and a stroke never cuts a root. Removing a whole plant still takes a deliberate single click on its root, with either tool.
- **New `slice` command** that carries the hexes of a stroke to the server, which applies the cuts in order and reports one update.
- **BREAKING: panning moves off the left mouse button.** Dragging with the right or middle button pans the view; dragging with the left button now belongs to the selected tool. The browser's context menu no longer appears over the board. Keyboard panning is unchanged.
- The seed tool is unchanged in effect: it plants one seed per press and does not paint seeds along a drag.

Out of scope: touch input (which has no right button and so loses drag panning), and how the Mower should work in the planned competitive modes, where a player cannot pause the game.

Assumptions from exploration that were proposed and not explicitly confirmed: roots are protected in strokes, strokes skip uncuttable hexes silently, the Mower shows a preview and can be cancelled, the Mower leaves an already paused game paused, the middle button pans as well as the right, and the seed tool does not paint.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `game-client`: panning changes from left-drag to right-drag or middle-drag; the scissors tool cuts along a drag; the seed tool's behavior during a drag is defined; a Mower tool is added.
- `game-rooms`: the sandbox mode permits slicing; a slice command is added.
- `plant-simulation`: adds cutting along a path, with its ordering, silent skips, and root protection.

## Impact

- Backend: `sim/world.py` (slicing), `server/protocol.py` and `server/rooms.py` (the `slice` command), with tests.
- Frontend: pointer handling in `main.js`, a stroke preview in `board.js`, hex line interpolation in `hex.js`, the tool bar in `index.html` and `ui.js`, and `net.js`.
- Docs: `docs/protocol.md` and the controls section of `README.md`.
- Anyone used to left-drag panning has to relearn it; there are no stored data or API consumers to migrate.
