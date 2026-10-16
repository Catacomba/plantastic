# Tasks

## 1. Persistence on species

- [x] 1.1 Add `persistence = 0` and `persistence_of(plant)` to `Species` in `backend/plantastic/sim/species.py`, and set the preset values: zigzag 30, spiral 30, burst 30, wanderer 60, hydra 80; straight vine and fern stay 0. Verify with a new test in `backend/tests/test_species_presets.py` asserting each preset's value.
- [x] 1.2 Add the `persistence` setting to `Custom` (percent, 0 to 100, default 50, after `turn_chance`) and override `persistence_of` to read it. Add `persistence` to every Custom settings fixture in `backend/tests` (`test_custom.py`, `test_cut_responses.py`, `test_app.py`, `test_rooms.py`, `test_species_presets.py`). Verify with tests for an out-of-range value (101), a missing value, and the setting description, then run `pytest backend`.

## 2. Detour in the engine

- [x] 2.1 Add `gave_up` to `Tip`. In `World._advance`, implement the occupied-target branch from design.md: board full and no empty side wait without drawing; otherwise roll with `_roll`, then either give up or turn into the one empty side (or a random choice of two) and advance. Clear `gave_up` on advance. Verify with new tests in `backend/tests/test_growth.py`: persistence 100 detours into the only empty side in the same iteration; both sides occur over many seeds; no empty side and a full board leave the rng state unchanged; own-plant obstacles count.
- [x] 2.2 Cover the per-obstacle roll: a tip that gives up keeps its heading and leaves the rng untouched for 20 iterations, resumes its original direction when the obstacle is cut, and rolls again at a second obstacle after a detour. Cover the roughly 30 percent rate over many seeds, and a `last` tip that detours and then ends. Verify with new tests in `backend/tests/test_engine.py` using a scripted test species with a configurable persistence.
- [x] 2.3 Cover collisions and replay: a contested-hex loser with persistence 100 enters a side hex in the same iteration, and two same-seed boards with detours stay identical every iteration. Verify with tests in `backend/tests/test_growth.py`.
- [x] 2.4 Update existing tests that assume blocked presets never turn so they use persistence-0 plants. Rework the wanderer "gentle turns" statistic to exclude detour steps, and the "runs into itself" test to cover the case with no detour. Verify by running `pytest backend` with everything green.

## 3. Species patterns after a detour

- [x] 3.1 Add tests in `backend/tests/test_species_presets.py`: a zigzag that detours keeps alternating east and south-east; a burst arm that detours continues in its new direction and still fans after 4 cells; a hydra keeps its new direction; straight vine and fern never detour. Verify by running `pytest backend/tests/test_species_presets.py`.

## 4. Catalog, client, and docs

- [x] 4.1 Add `persistence` to each catalog entry in `backend/plantastic/server/rooms.py` (the value for presets, `null` for custom). Verify by updating the welcome-message expectations in `backend/tests/test_rooms.py` and running them.
- [x] 4.2 Show `persistence N%` for preset plants in `describePlant` in `frontend/js/ui.js`. Verify by running the server and hovering over a hydra and a custom plant in the browser: the hydra shows `persistence 80%`, and the custom plant shows `Persistence % <value>` once.
- [x] 4.3 Document the change. In `docs/protocol.md`, add the `persistence` field and the new custom setting. In `README.md`, add a persistence column or note to the plant table, update the wanderer description, and add **Persistence %** to the custom plant list. Verify that the documented setting names match `Custom.settings` and the catalog output.

## 5. Integration check

- [x] 5.1 Scatter 50 random plants on a running board and let it grow until most tips wait. Confirm that straight vines and ferns stop at obstacles while hydras and wanderers visibly work around them, and that the waiting-tips metric still counts waiting tips. Run `openspec validate add-growth-persistence --strict`.
