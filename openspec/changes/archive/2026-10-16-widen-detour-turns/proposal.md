# Proposal

## Why

A blocked tip that wins its persistence roll looks only at the two 60-degree turns. When both are taken, it waits, even at 100% persistence and even when a sharper 120-degree turn is free. This was reported for a straight vine at 100% running into a wall: it stops whenever only the sharp corner is open. A plant that is fully persistent should try every way out before it gives up.

## What Changes

- After a successful persistence roll, a blocked tip takes the gentlest free way out:
  - first the 60-degree turns, choosing at random when both are free, as now;
  - only if both of those are occupied, the 120-degree turns, again choosing at random when both are free.
- A tip never turns straight back (180 degrees).
- There is still exactly one roll per obstacle. As before, nothing is drawn when none of the four directions is free or the board is full.
- This applies to every plant with persistence above 0, presets included, not only 100%.
- No step can turn more than 120 degrees from the one before. A 180-degree change would lead into the cell the tip just left, which is always occupied. So the wanderer's "Detours never double back" scenario stays valid as written.
- Seeded games replay differently from before wherever a tip used to wait with only a sharp turn free.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `plant-simulation`: "Blocked tips may take another path" widens the detour to 120-degree turns when both 60-degree turns are occupied.

## Impact

- `backend/plantastic/sim/world.py`: `World._detour` chooses among the 60-degree sides, then the 120-degree sides.
- `backend/tests/test_growth.py`: the "no empty side" test must block all four turns. New tests cover the sharp turn, its two-sided choice, and the preference for 60 degrees.
- `README.md` and `docs/protocol.md`: the wording of "turns 60 degrees left or right".
