# Design

## Context

`World._detour` in `backend/plantastic/sim/world.py` builds `sides` from `turn_left(heading)` and `turn_right(heading)`, keeping those whose hex is empty. It returns `None` without rolling when none are free, rolls with `_roll`, and then picks the only side, or `rng.choice` between two. See proposal.md for the motivation.

## Goals / Non-Goals

**Goals:**
- Keep the random draws exactly as they are whenever a 60-degree turn is free, so boards that never hit the new case replay as before.
- Still one roll per obstacle, and no draw when there is nowhere to go.

**Non-Goals:**
- Reversing 180 degrees, which the user chose against.
- Looking more than one hex ahead.

## Decisions

### Tiers, chosen after the roll
Compute two tiers: `gentle` holds the free headings at ±60 degrees and `sharp` the free headings at ±120 (`(heading ± 2) % 6`). The tip has a way out if either tier is non-empty. If neither is, return `None` with no roll, as today. Otherwise roll. If the roll succeeds, take the first non-empty tier, then the only member or `rng.choice` of two, exactly as now.

Rolling before choosing a tier keeps one roll per obstacle and makes the persistence percentage the chance of getting out at all, whichever tier is used. Checking `sharp` only adds a dictionary lookup per blocked visit, and only when no gentle turn is free.

Alternative considered: a separate, lower chance for sharp turns. That adds a parameter nobody asked for, and the user wants 100% to mean "try everything".

### Order of the candidates
Within a tier, the order is `[left, right]`, the same as today, so `rng.choice` sees the same list and existing seeds replay identically whenever a gentle turn is free.

## Risks / Trade-offs

- [Boards fill a little more densely: tips squeeze into pockets they used to leave alone] → Intended. The 100,000-cell cap still applies.
- [Spirals and zigzags may now fold back on themselves more after a sharp detour] → Accepted as emergent behaviour. Each species continues its pattern from its new heading, as specified.
- [Replays differ only where a tip previously waited with a sharp turn free] → Accepted. Sessions are not persisted across versions.
