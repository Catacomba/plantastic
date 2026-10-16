# Design

## Context

`World.step()` adds speed to every tip, then repeatedly sorts all tips by `(plant_id, id)` and calls `_advance` on each due one until nothing moves. `_advance` returns False for a blocked tip and pins its progress at 1. `_detour` returns `None` when the tip has already given up, when no 60- or 120-degree turn is free (no draw), or when the roll fails (which sets `gave_up`). Cells are removed only by `cut`, `slice` (through `cut`), and `clear`, and only in `_remove_cells` or `clear`. `Room._update` sends `board.tips_snapshot()`, the full list, in every update. The browser replaces its tip list with it and draws it. See proposal.md for the motivation.

## Goals / Non-Goals

**Goals:**
- Exact equivalence: the same cells, tips, plants and random draws with skipping on or off. Only visits and message sizes differ.
- Per-iteration work, and per-update tip data, proportional to the awake tips rather than all tips.

**Non-Goals:**
- Putting full-board waits to sleep. The room pauses on a full board, so there is nothing to save.
- Sending tip deltas for awake tips. They change progress every iteration anyway.
- Optimizing `cut` or `clear` themselves.

## Decisions

### Why equivalence holds
A blocked tip that is decided, with progress pinned at 1, changes state in only two ways:
- When its target hex is empty, it advances.
- When it has not given up and a turn hex is free, it rolls.

Both conditions can only become true when a cell is removed, because growth only adds cells. Until then, every visit to it is a no-op that draws nothing. So skipping those visits, and waking the tip exactly when one of the hexes it depends on is removed, gives the same sequence of states. A woken tip keeps `decided`, `gave_up`, and its progress of 1. The next `step` gives it `min(1 + speed, 1)` as before, and it is processed in the same `(plant_id, id)` order as any awake tip. Wakes only happen inside commands, never in the middle of a `step`.

### Data structures
- `World.skip_stuck: bool = True`.
- `World._sleeping: dict[int, Tip]` holds the sleeping tips. `World._awake` is an insertion-ordered dict of the other tips. `self.tips` still holds every tip, so `cut`, `_tips_on`, and `can_sprout`'s duplicate check are unchanged.
- `World._watchers: dict[Hex, set[int]]` maps a hex to the ids of the sleeping tips that wake if it is emptied. `Tip.watching: tuple[Hex, ...]` is kept so the tip can unsubscribe.
- `Tip.asleep` is not sent to clients. `blocked` stays True while asleep.

### Falling asleep
In `_advance`, when the target is occupied, the board is not full, and `_detour` returned `None`, put the tip to sleep if `skip_stuck` is on. The tip watches its target hex, plus all four turn hexes when it has not given up (that is, it had no free turn). It moves from `_awake` to `_sleeping`, and `changes.sleep(tip)` records `tip.to_dict()`. The `step` loop iterates over `_awake` only. A tip that falls asleep mid-step is gone from later passes because each pass reads `_awake`. The initial progress loop also covers `_awake` only.

### Waking
`_wake(tip, changes)` unsubscribes the tip's watched hexes, moves it back to `_awake`, and records `changes.wake(tip.id)`.
- **A cell is removed:** `_remove_cells` wakes the watchers of every removed hex before the cells and tips are dropped. Tips on removed cells are then dropped as usual.
- **A tip is dropped:** `_drop_tip` on a sleeping tip unsubscribes it and records `wake(id)`. On the wire, `woke` means "no longer in the sleeping set", which covers both waking and removal.
- **`clear()`:** empties all three structures. The client already empties everything on `cleared`.
- **`set_skip_stuck(False)`:** wakes every sleeping tip. Switching it back on does nothing immediately: waiting tips fall asleep again on their next visit.

### Recording in `Changes`
`Changes` gains `_slept: dict[int, dict]` and `_woke: set[int]`.
- `sleep(tip)` sets `_slept[id] = dict`.
- `wake(id)` deletes the id from `_slept` if it fell asleep within these changes. Otherwise it adds the id to `_woke`.
- `merge` applies the other's wakes and then its sleeps, in that order.
- `cleared` resets both.

Clients apply `woke` before `slept`. That ordering makes a tip that woke and fell asleep again in one batch come out right.

### Wire format
- `welcome`: `tips` (awake), `sleeping` (list of tip dicts), `skip_stuck`.
- `update`: `tips` (all awake tips), `slept` (tip dicts), `woke` (ids), `skip_stuck`.
- Command `{"type": "skip_stuck", "enabled": true|false}`, with `enabled` a `StrictBool`. It returns one update with no cost.

With skipping off, `sleeping`, `slept` and `woke` are always empty and `tips` is every tip, so the messages look exactly as they do today plus the new fields.

### Client
- `net.state.sleeping` is a `Map` of id to tip, filled from `welcome.sleeping` and updated with `woke` and then `slept` on every update, and emptied on `cleared`.
- `redraw` passes `[...state.tips, ...state.sleeping.values()]` to `board.setTips`.
- The switch goes in the settings menu below Performance metrics, labelled **Skip stuck tips**. It uses `loadFlag` with a default of true (a new optional default argument) and `saveFlag`.
- The client sends `skip_stuck` in `onWelcome` and on change. The checkbox reflects `state.skipStuck` after each message.
- `boardCounts` returns `asleep: sleeping.size`, and counts waiting tips as blocked awake tips plus asleep ones. The Tips row reads `13,691 (12,893 waiting, 12,850 asleep)`.

## Risks / Trade-offs

- [A wrong watch set would leave a tip asleep forever, which is a visible behaviour change] → An equivalence test compares long seeded scripts with skipping on and off, every iteration. It includes cuts of obstacles, cuts of turn hexes, slices, clears, scatters, and switching skipping part way through.
- [The client still rebuilds its tip drawing from all tips on every update] → Unchanged from today, and out of scope. Network and server costs drop. Browser handling time may drop less.
- [Older clients ignore `slept`, `woke` and `sleeping` and would lose stuck tips] → The bundled client is the only client and is updated in the same change. `docs/protocol.md` documents the fields.
- [Visits are lower with skipping on, which shifts the meaning of the Tip visits metric] → The README says sleeping tips are not visited.
