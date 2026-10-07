# Design

## Context

See proposal.md for motivation. The relevant current state of the code:

- A `Species` has `grow(tip, world) -> list[int]` (headings: one continues, several branch, none ends) and `on_cut(plant, stump, world) -> list[(cell, heading)]`. Only `StraightVine` exists.
- A `Tip` holds `id`, `plant_id`, `cell`, `heading`, `progress`, `blocked`. It has no memory. A `Plant` holds `id`, `species_id`, `speed`, `owner`, `root`.
- `World._advance` calls `grow` every time a due tip is not flagged `blocked`. A tip stopped by the board limit is not flagged, so it is asked again on the next iteration. That is harmless for the vine and wrong for any species that counts steps or rolls dice.
- The `plant` command carries `q`, `r`, `species`, `speed`. `welcome` and `update` carry cells and tips; clients learn nothing about a plant except its id.
- The seed tool's species picker is already filled from the catalog in `welcome`.

## Goals / Non-Goals

**Goals:**

- Species stay small, readable Python objects, each testable in isolation with a seeded world.
- Every random choice comes from `world.rng`, and the number of draws is the same on every replay.
- The custom plant's settings are described once, on the server, and the client builds its panel from that description.

**Non-Goals:**

- Species-specific rendering.
- Editing a plant after planting, or saving named setting presets.
- A general scripting or expression language for growth rules. The custom plant is a fixed set of knobs.
- Tips that steer around obstacles; a blocked tip still waits.

## Decisions

### 1. Tip state, plant state, plant settings

- `Tip.state`: a small dict owned by the tip's species (for example `{"run": 2, "left": 1}` for a spiral, `{"calm": 4}` for a custom plant).
- `Plant.state`: a small dict owned by the species, used for the handedness that zigzag and spiral flip on each cut.
- `Plant.settings`: the validated settings the plant was planted with, or `None`. Set once in `plant_seed` and never written again; nothing in the simulation or the protocol offers a way to change it.

Tip and plant state are internal and are not sent to clients. Settings are sent (decision 7).

*Alternative considered:* deriving everything from geometry (for example counting cells back along the parent chain). Rejected: it is slower, breaks after cuts, and cannot represent dice already rolled.

### 2. Species interface

```
class Species:
    id, name, default_speed
    settings: list[Setting] = []          # description for the catalog
    def validate(self, raw) -> dict|None  # raises SettingsError; the world reports bad_settings
    def new_plant_state(self) -> dict                          # what it remembers per plant
    def new_tip_state(self, plant, heading) -> dict            # for the seed's tip and any stateless shoot or sprout
    def grow(self, tip, plant, world) -> list[Shoot]
    def on_cut(self, plant, stump, world) -> list[Sprout]
```

- `Shoot(heading, state=None, last=False)`: the first shoot is the tip itself (its new heading, its replaced state when given, and `last=True` to remove the tip right after it enters its next hex). Further shoots are new tips on the same cell. An empty list ends the tip immediately.
- `Sprout(cell, heading, state=None)`: a new tip after a cut.

`last` lets a fern's side branch lose its tip the moment its third cell exists, instead of an iteration later.

The existing `StraightVine` is ported to the new signatures with no change in behavior; its tests must pass untouched.

### 3. One decision per hex

`Tip` gains `decided: bool`. `_advance` calls `grow` only when it is false, applies the result (heading, state, new tips), and sets it. It is cleared when the tip actually enters a hex. A tip stopped by an occupied hex or by the board limit therefore keeps its heading and state, and draws no further random numbers, however long it waits. `blocked` keeps its current meaning (next hex occupied) because the client draws blocked tips differently.

New tips from a branch are created at decision time, through the existing `can_sprout` check (first hex empty, no duplicate tip on that cell and heading).

Two things were added while building this. A waiting tip (`decided` and not yet moved) banks at most one hex of progress, whether it waits behind a cell or behind the board limit; before, only cell-blocked tips were capped. And the world keeps an index of tips by the cell they sit on, because branching species made the duplicate check, which used to scan every tip, the slowest part of an iteration.

### 4. Cut responses as shared functions

Four module-level functions take `(plant, stump, world)` and return sprouts: `fork` (the vine's current logic, moved), `regrow`, `no_response`, and `multiply`. `multiply` is `fork` applied at one cell back and at two cells back, stopping at the root. `regrow` lists the empty neighbors of the cell behind the stump in direction order and picks one with `world.rng`; it draws no random number when there are none.

Species reference these functions; the custom plant looks its function up by the `cut_response` setting. Zigzag and spiral have their own `on_cut`, which flips `plant.state["hand"]` and returns one sprout with fresh state.

### 5. The six species

| Species | Tip state | `grow` |
|---|---|---|
| Zigzag | `base` heading, `hand`, `step` | heading is `base` on even steps and `base + hand` on odd steps |
| Spiral | `hand`, `run`, `left`, `turns` | when `left` is 0, turn by `hand`, count the turn, lengthen `run` after every second turn, reset `left` |
| Fern | stem: `n`; side branch: `life` | stem goes straight and, when `n` is a multiple of 3, adds a shoot to the left or right by `n // 3` parity with `life = 3`; a side branch goes straight and returns `last=True` on its third cell |
| Wanderer | none | one `rng.randrange(100)`; below 20, a second draw picks left or right |
| Hydra | none | straight |
| Burst | `n` | straight; when `n` reaches 4, add forward-left and forward-right shoots and reset `n` |

The spiral's run schedule was checked for 5000 steps in both hands and all six starting directions: it never revisits a cell.

### 6. Custom plant

Settings and their catalog description:

| id | kind | range | default |
|---|---|---|---|
| `branch_chance` | percent | 0 to 100 | 10 |
| `branch_min` | int | 1 to 4 | 1 |
| `branch_max` | int | 1 to 4 | 1 |
| `calm_min` | int | 0 to 1000 | 2 |
| `calm_max` | optional int (`null` is never) | 0 to 1000 | `null` |
| `turn_chance` | percent | 0 to 100 | 10 |
| `cut_response` | choice | `fork`, `regrow`, `none`, `multiply` | `fork` |

`validate` checks types strictly (whole numbers, no booleans), ranges, `branch_min <= branch_max`, `calm_min <= calm_max`, and rejects unknown or missing keys. Percentages are whole numbers so that chance rolls are exact integer comparisons.

`grow`, with `calm` the hexes entered since the last event:

1. `calm < calm_min`: straight, `calm + 1`.
2. `calm_max` is set and `calm >= calm_max`: forced. Branch if `rng.randrange(branch_chance + turn_chance) < branch_chance`; if both chances are 0, turn.
3. Otherwise roll for a branch (`rng.randrange(100) < branch_chance`); if that fails, roll for a turn the same way; if that fails, straight.

A branch draws `n = rng.randint(branch_min, branch_max)`, lists the forward-left, forward-right, back-left, and back-right headings whose hexes pass `can_sprout`, and takes `rng.sample` of `min(n, len(free))`. The tip continues straight. Branch and turn both reset `calm` to 0, and new tips start at 0.

A rule fixed here so replays are stable: a roll is skipped, not drawn and ignored, when its chance is 0 or 100.

### 7. Protocol

- `plant` gains optional `settings` (an object). The room passes it through; `World.plant_seed` calls the species' `validate`, which raises `SimError("bad_settings", ...)` with a message naming the setting. A species with no settings rejects any non-null `settings`.
- Catalog entries in `welcome.species` gain `settings`: a list of `{id, label, kind, min, max, default, choices}` (fields present as relevant to the kind).
- `welcome` gains `plants`: `[{id, species, speed, settings}]`. `update` gains `plants` with the plants created by that update (usually empty). `Changes` records added plants so merged updates carry them too.
- New error code `bad_settings`.

Clients drop a plant's details when its last cell is removed; no "plant removed" message is needed.

*Alternative considered:* sending settings inside every cell. Rejected as wasteful; plants are few and cells are many.

### 8. Client

- `net.js` keeps `state.plants`, a map from plant id to details, filled from `welcome.plants` and `update.plants` and pruned after each update of ids that no longer have a cell.
- `ui.js` builds the settings panel from the selected species' `settings` list: number inputs for `percent` and `int`, a number input with a "never" checkbox for `optional_int`, a `select` for `choice`. Values live in a per-species object in memory for the visit, starting from the defaults. The panel sits in the tool bar and is hidden when the list is empty or another tool is selected.
- Planting sends the panel's current values as `settings` when the species has any. The client does no range checking beyond the inputs' own `min` and `max`; the server's `bad_settings` message is shown as a toast, like other errors.
- Hover details: `main.js` already knows the hex under the cursor. When it holds a cell, a readout in the top bar shows the plant's species name, speed, and each setting as "label value". It clears otherwise.

### 9. Tests

Each species gets its own test module driving a seeded `World` with a given starting direction. Random species are tested by properties (allowed headings, bounds on counts over many steps, equality across same-seed runs, difference across seeds), not by exact paths. The custom plant is tested at its deterministic corners (chances of 0 and 100, `calm_min == calm_max`, fixed branch counts) plus range and distribution checks.

## Risks / Trade-offs

- [Branch-heavy custom settings fill the board in seconds] → The 20,000-cell limit pauses the room, and sprouts need an empty hex, so growth is bounded by space. The settings panel does not warn about it.
- [Many waiting tips cost work each iteration] → One lookup per waiting tip, and waiting tips draw nothing. Bounded by the board limit.
- [Wanderers and custom plants can trap themselves against their own cells] → Accepted as part of how those plants behave; a cut frees them.
- [The species interface changes under the existing vine] → The vine's tests are the regression check and must pass unchanged.
- [Some spec timings may be off by an iteration] → The fern and burst scenarios state iteration counts worked out by hand. If implementation shows an off-by-one, the scenario is corrected in the delta spec during apply and called out, not papered over in code.
- [All species look alike] → Per-plant colors and the hover readout tell them apart for now.

## Open Questions

- Whether species should eventually differ in appearance (thickness, leaf marks). Deferred; it does not affect any rule here.
