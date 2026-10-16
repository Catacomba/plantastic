# Proposal

## Why

Persistence is fixed per species, and only Custom plants let the player choose it. To compare how stubborn plants shape a board, the player wants to set one persistence and plant any species with it, including from **Random**. Unticking the setting should restore each species' own default.

## What Changes

- The tool bar gets a **Persistence %** number (0 to 100, starting at 50) and an **Override** checkbox, next to the seed Speed field. The checkbox starts unticked, so the game behaves as today until the player opts in. The number can be edited only while the box is ticked.
- While ticked, every seed the player plants, of any species, gets the chosen persistence. That includes Custom, where it replaces the Custom **Persistence %** setting. So does every seed placed by **Random**.
- While unticked, a plant takes its species' default persistence: the preset's fixed value, or the Custom setting.
- A plant's persistence is fixed when it is planted and is now part of its details. The hover text shows each plant's actual persistence, and for Custom it replaces the setting's value in that text.
- Protocol: `plant` and `scatter` accept an optional `persistence` (a whole number 0 to 100, or `null` or left out for the species default). Plant details gain `persistence`. A value out of range is rejected with `bad_persistence`. Existing clients keep working unchanged.

**Depends on** `add-growth-persistence`, which is implemented but not yet archived. Archive it first so that its requirements exist in the main specs before this change's deltas modify them.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `plant-simulation`: planting and scattering accept a persistence that overrides the species default.
- `plant-species`: preset persistence becomes the default rather than a value every plant must use.
- `game-rooms`: the plant and scatter commands carry the optional persistence, and plant details report it.
- `game-client`: a persistence control in the tool bar, and hover details that show each plant's persistence.

## Impact

- `backend/plantastic/sim/world.py`: `Plant.persistence` is resolved at planting, `plant_seed` and `scatter` take `persistence`, and `_detour` reads the plant's value.
- `backend/plantastic/server/protocol.py` and `rooms.py`: the optional field on `plant` and `scatter`, passed through.
- `frontend/index.html`, `frontend/js/ui.js`, `frontend/js/net.js`, `frontend/js/main.js`: the control, sending it, and the hover text.
- `docs/protocol.md` and `README.md`.
- Tests: plant-details equality checks across `backend/tests` gain `persistence`, plus new override tests.
