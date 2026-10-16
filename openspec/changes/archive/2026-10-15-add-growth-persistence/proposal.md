# Proposal

## Why

A tip that runs into an occupied hex waits there until the obstacle is cut, so a crowded board soon freezes into plants that never grow again. Giving each plant a chance to look for another way around an obstacle makes growth livelier: some plants still stop as they do now, while others keep pushing into whatever room is left.

## What Changes

- New growth rule: when a tip's next hex is occupied, by any plant including its own, the tip rolls its plant's **persistence**, a percentage chance from 0 to 100. On success it turns 60 degrees left or right into an empty hex and grows there at once. On failure, or when neither side is empty, it waits as it does today.
- One roll for each obstacle met. A tip that has given up does not roll again while it waits. It resumes in its original direction once the obstacle is removed, and the next obstacle it meets gets a fresh roll.
- Every preset species gets a fixed persistence. Straight vine and fern stay at 0, so they still stop. Zigzag, spiral and burst get 30, wanderer 60 and hydra 80.
- The custom species gets a new **Persistence %** setting (0 to 100, default 50). **BREAKING** for protocol clients: a `plant` command for a custom seed must now include `persistence`. The bundled client builds its form from the catalog, so it picks this up on its own.
- The catalog sent in `welcome` gives each species' persistence. The hover text in the top bar shows a preset plant's persistence. A custom plant's persistence already shows with its settings.
- Replays of earlier sessions with the same seed now differ wherever a plant with non-zero persistence was blocked.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `plant-simulation`: blocked tips may take another path. This loosens "Blocked tips wait" and "One growth decision per hex" so that each obstacle gets one persistence roll, and makes collision losers eligible to detour.
- `plant-species`: the catalog gives each species a persistence and fixes the preset values. Hydra now differs from the straight vine in persistence. The wanderer's turn statistics and its "runs into itself" behaviour account for detours. The custom species gains a persistence setting.

## Impact

- `backend/plantastic/sim/world.py`: the detour step in the tip-advance logic, and per-tip "gave up" state.
- `backend/plantastic/sim/species.py`: a persistence value per species, how Custom reads it from settings, and the new Custom setting.
- `backend/plantastic/server/rooms.py`: catalog entries in `welcome` gain `persistence`.
- `frontend/js/ui.js`: plant hover text shows persistence for presets.
- `docs/protocol.md` and `README.md`: the new field and setting, the plant table, and the wanderer description.
- Tests: Custom settings fixtures across `backend/tests` need the new key. Wanderer and blocked-tip tests need updating or pinning to persistence 0, and new detour tests are needed.
