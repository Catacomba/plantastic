# Proposal

## Why

Trying things out in the sandbox means setting up a board over and over: planting many seeds one click at a time, and removing them one root at a time when the board gets crowded. With the performance metrics now in place, the natural experiment is "fill the board, watch the numbers, wipe it, try again", and neither half of that is quick today.

## What Changes

- **A Clear button** that removes every plant from the board in one action. The iteration counter keeps counting and the clock keeps its state, so clearing a running game leaves it running on an empty board. There is no confirmation prompt.
- **A Random plants control**: a number field and a button that plant that many seeds at random empty positions inside the area the player is looking at.
  - Each seed's species is drawn at random from the seven species that need no settings (every species except custom). Each draw is independent, so the mix is not balanced.
  - Each seed uses its species' default speed and a random starting direction.
  - The count is from 1 to 500. If the area has fewer empty hexes than requested, or the board fills up, as many as fit are planted and the player is told how many.
- **Two new commands**, `clear` and `scatter`, which a room's mode may permit or forbid. The sandbox permits both.
- **Updates can say the board was cleared**, as a single flag instead of a list of every emptied hex.
- The server makes every random choice from the room's seeded generator, so a session with random plants still replays exactly.

Decisions made while writing this up that were proposed during exploration and not explicitly confirmed: positions are within the visible area; the server, not the browser, picks positions and species; the 1 to 500 range; default speeds; clear keeping the iteration counter and clock and having no confirmation; and both controls living in the top bar.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `plant-simulation`: adds clearing the board and scattering random seeds within a region.
- `game-rooms`: the sandbox permits clearing and scattering; adds the two commands and the cleared flag on updates.
- `game-client`: adds the Clear button and the Random plants control.

## Impact

- Backend: `sim/world.py` (clear, scatter, a cleared flag on `Changes`), `server/protocol.py` and `server/rooms.py` (two commands), tests.
- Frontend: `index.html`, `css/style.css`, `ui.js`, `net.js`, `main.js`.
- Docs: `docs/protocol.md` and `README.md`.
- The `update` message gains a `cleared` field; existing fields are unchanged.
