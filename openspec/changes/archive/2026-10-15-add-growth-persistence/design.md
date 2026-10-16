# Design

## Context

Today `World._advance` (`backend/plantastic/sim/world.py`) works in two phases for a due tip. First it makes the growth decision once per hex, setting `tip.decided`. Then it either enters the target hex or, if the hex is occupied or the board is full, sets `blocked`, pins `progress` at 1 and returns. A blocked tip is revisited on every iteration, which the visit count and the "waiting tips" metric rely on, and it draws nothing from `world.rng`. Species already share `_roll` in `species.py`, which draws nothing for 0 and 100.

## Goals / Non-Goals

**Goals:**
- The detour lives in the engine, so every species gets it with no change to its `grow` rule.
- Replay stays exact: the number of random draws depends only on board state.
- Persistence 0 behaves exactly as today, including random draws, so straight vines, ferns and existing tests built on them are unaffected.

**Non-Goals:**
- Detours of more than 60 degrees, or searching several hexes ahead for a way around.
- Letting players change a preset species' persistence.
- Showing on the board which tips have given up. They draw like any other waiting tip.

## Decisions

### Detour in the engine, after the decision
The detour sits in `_advance` between the decision and the move. When the target is occupied, the engine checks the board-full condition first, then the tip's "gave up" flag, then the empty sides, then the roll:

```
target occupied?
  no  -> (full check as today) -> advance
  yes -> board full?         -> wait, no draw (stays eligible to roll later)
         tip.gave_up?        -> wait, no draw
         sides = [h-1, h+1] filtered to empty hexes
         no sides?           -> wait, no draw (stays eligible)
         _roll(persistence) fails -> tip.gave_up = True, wait
         succeeds -> heading = sides[0] if one side, else rng.choice(sides)
                     advance into it now
```

Rationale: putting it here keeps `grow` single-purpose and gives every species the behaviour for free. The species' decision (state, sprouted shoots, `last`) has already been applied, so the detour changes only `tip.heading` for this hex. That is what makes the zigzag sidestep (its `grow` recomputes the heading from `state["base"]`) while straight growers carry on in the new direction.

Alternative considered: a `Species.on_blocked` hook. It is more flexible, but every species would need it or inherit it, and the user asked for one uniform rule. A hook can still be added later without changing the specs.

### "Gave up" is per tip, cleared on advance
Add `gave_up: bool = False` to `Tip`, cleared together with `decided` when the tip advances. A tip that waits because the board is full, or because it has no empty side, does not set the flag. Those waits draw nothing, and the spec lets that tip roll once conditions change. The flag is not sent to clients: `Tip.to_dict` is unchanged, and `blocked` still means "waiting".

### Where persistence comes from
`Species` gains `persistence = 0` as a class attribute, and the presets override it. Test species such as `Scripted` and `Gambler` therefore default to 0 and keep their behaviour. `Species.persistence_of(plant) -> int` returns the class value. `Custom` overrides it to return `plant.settings["persistence"]`. The engine calls `persistence_of`, so it never needs to know which species has settings.

Custom gets `Setting("persistence", "Persistence %", "percent", 0, 100, 50)`, placed after `turn_chance` so the form keeps chances together. The default is 50, so a new Custom plant shows the feature without being unstoppable. This default is an assumption and easy to tune.

### Catalog field
`rooms.py` adds `"persistence": species.persistence` for species without settings and `None` for Custom, mirroring how the spec says Custom "lists none". `ui.js` `describePlant` appends `persistence N%` when the catalog entry has a non-null persistence. Custom already shows its setting through `settingText`.

### Visit counting
A detour is part of the same visit: one `_advance` call that moves the tip. Counting stays "one per attempt to move a due tip".

## Risks / Trade-offs

- [Denser boards and more cells per second] → The 100,000-cell cap already bounds the work. A detouring tip still has one tip, so per-iteration cost per tip is unchanged. Boards just stay alive longer.
- [Existing tests encode "blocked tips never turn" using presets with persistence > 0 (wanderer, and any test that blocks a hydra, zigzag, spiral or burst)] → Rewrite those to use the straight vine, or a test catalog with persistence 0. The wanderer statistics test excludes detour steps by comparing against the tip's pre-detour heading, or runs with persistence pinned to 0 through a test subclass.
- [Seeded sessions replay differently from before this change] → Accepted. Nothing persists sessions across versions.
- [Protocol break for custom `plant` commands without `persistence`] → The only client builds its form from the catalog. `docs/protocol.md` records the new required key.
- [Spiral with persistence 30 will now sometimes curl back into its own coils after a detour] → Accepted as emergent behaviour. The "never crosses itself" scenario is only about unobstructed growth.
