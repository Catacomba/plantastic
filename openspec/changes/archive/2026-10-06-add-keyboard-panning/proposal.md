# Proposal

## Why

The board is endless, but the only way to move around it is to drag with the mouse, which interrupts planting and cutting because the same mouse button does both. Panning from the keyboard lets the player keep the mouse on the tool while moving the view with the other hand.

## What Changes

- Holding W, A, S, or D pans the view up, left, down, or right, smoothly for as long as the key is held.
- The arrow keys do the same. This was suggested during exploration and not explicitly confirmed; it is included as an assumption and is easy to drop.
- Holding Shift pans faster.
- Keys are ignored while the player is typing in a field, and when combined with Ctrl, Alt, or the Windows/Command key, so text entry and browser shortcuts keep working.
- Panning stops when the window loses focus, so the view cannot drift from a key release the page never saw.
- The hover highlight follows the hex under the cursor while the view moves beneath it.

Dragging to pan is unchanged. The server, the protocol, and the simulation are not touched.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `game-client`: adds a requirement for panning the view from the keyboard. The existing "Unbounded board navigation" requirement (panning by dragging) is not changed.

## Impact

- `frontend/js/main.js` and `frontend/js/board.js`, plus one small new module for the key handling.
- `README.md` controls section.
- No backend, protocol, or dependency changes.
