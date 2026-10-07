# Design

## Context

See proposal.md for motivation. The relevant current state:

- A plant is removed only by cutting its root; planting is one `plant` command per seed.
- `Changes` records added, changed, and removed cells, new plants, and tip visits, and can be merged and replayed onto a client-style cell map. A removal is listed hex by hex.
- The board limit is 100,000 cells, so a hex-by-hex clear could mean a very large update.
- `World.plant_seed` draws a random direction from `world.rng` when none is given, and validates species, speed, and settings.
- A species "takes no settings" when its `settings` tuple is empty. That is true of seven of the eight species; only `custom` has settings.
- The top bar holds Pause, Grow, the counters, and the plant readout. The grid is pointy-top with axial coordinates, so a hex's screen column is proportional to `q + r / 2` and its screen row to `r`.

## Goals / Non-Goals

**Goals:**

- One command and one small update for each action, whatever the size of the board.
- Random choices made on the server from the room's seeded generator.
- A region the browser can describe exactly without the server knowing anything about pixels.

**Non-Goals:**

- Undo for a clear, or a confirmation prompt.
- Scattering custom plants, choosing the species mix, or choosing speeds.
- Resetting the room (iteration counter, random seed, clock). Clear removes plants and nothing else.

## Decisions

### 1. `World.clear()` and a cleared flag on `Changes`

`clear` empties `cells`, `plants`, `tips`, and the tip index, and returns a `Changes` with `cleared = True`. The tick, the random generator, and the id counters are left alone, so later plants get fresh ids and a replay stays aligned.

`Changes.merge` treats a cleared record as a reset: it drops everything merged so far, then sets the flag. `Changes.apply_to` clears the target map first when the flag is set. The update message gains `"cleared": true|false`, and a client that sees `true` empties its cell and plant maps before applying the rest of the update.

*Alternative considered:* listing every removed hex, as cuts do. Rejected: up to 100,000 pairs for an action whose whole meaning is "everything".

### 2. The scatter region is a screen-aligned hex rectangle

A region is `{q, r, half_width, half_height}`. Hex `(q2, r2)` is inside when:

```
|r2 - r| <= half_height   and   |(q2 - q) + (r2 - r) / 2| <= half_width
```

For a pointy-top grid this is exactly a rectangle on screen: `half_height` counts rows above and below the center, and `half_width` counts hex widths to either side. The browser computes it from the visible board area between the two bars; the server needs no notion of pixels or zoom.

Both half-sizes are whole numbers from 0 to 150, which bounds a region at about 90,000 hexes.

*Alternative considered:* a center and a hex-distance radius. Rejected because a hexagonal disc inscribed in a wide screen leaves the sides empty, and one that covers the screen puts seeds out of view.

### 3. `World.scatter(count, region, owner)`

1. List the empty hexes of the region in a fixed order (row by row, then by `q`).
2. Take `min(count, free hexes, cells left before the board limit)`; if that is less than the number of free hexes, choose that many with `rng.sample`.
3. For each chosen hex in order: draw a species with `rng.choice` from the catalog's species with no settings (in catalog order), and call `plant_seed` with that species' default speed, which draws the direction.

It returns the merged `Changes` and records `asked` and `planted` on it. Enumerating up to 90,000 hexes is a few tens of milliseconds, acceptable for a button press.

Fixed enumeration order plus a fixed sequence of draws is what makes scattering reproducible. Drawing each species independently is what makes the mix unbalanced, as requested.

*Alternative considered:* rejection sampling of random hexes. Rejected: it is faster on an empty region but slows without bound as the region fills, and needs the enumeration as a fallback anyway.

### 4. Protocol

Client to server:

- `clear` with no fields.
- `scatter {count, q, r, half_width, half_height}` with `count` from 1 to 500. Out-of-range values fail validation as `bad_message`, like other malformed commands.

Server to client, on `update`:

- `cleared`: boolean, true only on the update for a `clear`.
- `scattered`: `{asked, planted}` on the update for a `scatter`, otherwise `null`. This lets the client report a shortfall without guessing which update answered its command, since clock ticks arrive in between.

The room checks the mode's permission for `"clear"` and `"scatter"`. Neither command touches the clock or advances the board, so both carry `stats: null`.

### 5. Client

- Top bar: after the counters, a "Random" group (number field starting at 10 and a "Plant" button) and, after a visible gap, the "Clear" button styled as a quieter destructive action. Both are disabled while disconnected, through the existing `sync`.
- Region: `main.js` takes the rectangle between the bottom of the top bar and the top of the tool bar, converts its center to a hex with `board.hexAt`, and derives `half_width` from the rectangle's half-width in pixels divided by the hex width (`sqrt(3) * hexSize`) and `half_height` from its half-height divided by the row height (`1.5 * hexSize`), each rounded down, less one so that roots sit fully inside, and clamped to 0 to 150.
- `net.js` empties its cell and plant maps when an update has `cleared`, and passes `scattered` through to the page.
- Messages: fewer planted than asked gives "Planted 12 of 50: the visible area ran out of empty space."; none gives "No empty space in view for new plants."; an invalid count gives "Enter a whole number of plants from 1 to 500."
- A mower or scissors stroke in progress is unaffected by a clear arriving: its hexes simply hold nothing by the time they are sliced.

## Risks / Trade-offs

- [Clear has no undo and no prompt] → Requested for a sandbox where clearing is frequent. The button is set apart and styled differently from the clock controls.
- [A large scatter of bursts and ferns fills the board fast] → That is the point of the control for load testing; the board limit still pauses the room.
- [At very small hex sizes the view exceeds the 150-hex half-size] → The region is clamped, so seeds land in the middle of the view. Still "within view", just not edge to edge.
- [Scatter enumerates the whole region each time] → Bounded at about 90,000 hexes and done once per button press.
- [The top bar gets more crowded] → It already wraps, and the settings menu follows its lower edge.

## Open Questions

- Whether a later change should let the player choose the species mix or scatter copies of the selected species. Left out here by request.
