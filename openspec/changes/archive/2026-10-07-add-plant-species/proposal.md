# Proposal

## Why

The sandbox has one species, a vine that only grows straight, so there is little to compare and the cutting tools have little to work against. The game's premise is that different plants grow and react to cuts in different ways. Adding a varied set of species, plus one whose behavior the player can dial in, turns the sandbox into a place to find out which growth patterns are worth building levels around.

## What Changes

- **Six new species**, each with its own growth pattern and cut response:
  - **Zigzag**: travels in a wavy line; a cut restarts it from behind the stump, mirrored.
  - **Spiral**: winds outward in ever longer runs; a cut restarts it winding the other way.
  - **Fern**: a straight stem with short side branches on alternating sides; a cut is final.
  - **Wanderer**: mostly straight with occasional random turns; a cut regrows one tip in a random direction.
  - **Hydra**: straight like the vine; a cut makes it fork from both of the two cells behind the stump.
  - **Burst**: splits into a three-way fan every few cells; forks like the vine when cut.
- **A custom plant** whose settings the player chooses before planting: speed, branch chance, minimum and maximum branches per branching, minimum and maximum calm stretch between events, turn chance, and cut response.
- **Settings are fixed at planting.** Changing them affects only seeds planted afterwards; a growing plant can never be edited.
- **Tips can now turn, branch, and end** as their species dictates, and remember what they need to between hexes.
- **A settings panel** in the seed tool for species that have settings, built from what the server's catalog describes.
- **Plant details on hover**: pointing at a plant shows its species, speed, and settings, so custom plants planted side by side can be told apart.
- The `plant` command carries optional settings, and the server tells clients each plant's species, speed, and settings.

The straight vine is unchanged. Out of scope: giving each species its own look (all are still told apart only by per-plant color), light-seeking plants, and saving or naming custom setting presets.

Decisions made while writing this up that were proposed during exploration and not explicitly confirmed, or that changed:

- "Branches on each new hex" and "min/max branches on a specific hex" are treated as one pair of settings.
- Turn chance and cut response are additions to the custom plant's requested settings.
- **Hydra changed.** The explored version ("three tips, one straight past the stump") cannot work, because the hex straight ahead is the stump. It now forks from both of the two cells behind the stump, giving up to four tips.
- Plant details on hover is an addition, included because comparing custom plants needs it.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `plant-species`: the catalog grows to eight species and describes each species' settings; requirements are added for the six new species, the shared cut responses, and the custom plant.
- `plant-simulation`: planting accepts settings that are fixed for the plant's life; tips may turn, branch, and end; a tip makes its growth decision once per hex.
- `game-rooms`: the welcome and updates carry plant details; planting with settings is validated.
- `game-client`: the seed tool gains a settings panel; plant details are shown on hover.

## Impact

- Backend: `sim/species.py` grows substantially; `sim/world.py` gains tip and plant state, settings, and one-decision-per-hex; `server/protocol.py` and `server/rooms.py` carry settings and plant details. New tests per species.
- Frontend: `ui.js`, `index.html`, and `css/style.css` for the settings panel and the hover readout; `net.js` and `main.js` for plant details.
- Docs: `docs/protocol.md` and `README.md`.
- The `plant` command and the `welcome` and `update` messages gain fields. Existing fields keep their meaning, so nothing that works today breaks.
- Branch-heavy custom settings grow exponentially and will reach the existing 20,000-cell board limit quickly; the limit already pauses the room.
