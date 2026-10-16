# Tasks

## 1. Engine

- [x] 1.1 In `World._detour`, collect the free 60-degree turns, then the free 120-degree turns. Wait without rolling when both lists are empty, and after a successful roll take the first non-empty tier, choosing at random between two. Update `test_no_empty_side_waits_without_drawing` in `backend/tests/test_growth.py` to block all four turns. Add tests: only the north-west sharp turn free gives a north-west detour in the same iteration; both sharp turns free give both sides over many seeds; one gentle turn plus both sharp turns free always gives the gentle one. Verify by running `pytest backend` with everything green, including the unchanged wanderer "never doubles back" test.

## 2. Docs and check

- [x] 2.1 Update the detour wording in `README.md` (the Persistence paragraph) and `docs/protocol.md` (the catalog `persistence` description) to say a tip turns 60 degrees if it can, otherwise 120, and never back. Verify both texts match `_detour`.
- [x] 2.2 In the running app, tick Override at 100 and plant a straight vine heading into a wall of other plants, so that only a sharp corner is free. Confirm that it turns the sharp corner instead of stopping. Run `openspec validate widen-detour-turns --strict`.
