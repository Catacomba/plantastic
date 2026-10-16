# Design

## Context

After `add-growth-persistence`, `World._detour` asks the species for `persistence_of(plant)`. That returns the class value for presets and `plant.settings["persistence"]` for Custom. `Plant.to_dict` sends `{id, species, speed, settings}`, and the hover text adds the catalog's preset persistence. `plant_seed` and `scatter` take no persistence. In the browser, the tool bar holds the Seed tool, the species picker, the Speed field, and the settings panel for Custom.

## Goals / Non-Goals

**Goals:**
- One place decides a plant's persistence, at planting, so the engine never needs to know whether it was overridden.
- Clients that never send `persistence` behave exactly as today.

**Non-Goals:**
- Changing an existing plant's persistence. Like speed and settings, it is fixed at planting.
- Remembering the control between visits. It starts unticked at 50 on every load, like the Speed field.

## Decisions

### Resolve once, store on the plant
`Plant` gains `persistence: int`. `plant_seed(..., persistence=None)` validates it and stores `persistence if persistence is not None else species.persistence_of(plant)`. The plant is built first, so Custom can read its own settings. `_detour` then reads `plant.persistence` instead of asking the species. `Plant.to_dict` adds `"persistence"`.

Alternative considered: store only the override (`None` by default) and resolve it in `_detour`. That keeps two sources of truth, and the client would need the catalog to know the real value. Resolving once makes the plant details self-describing.

Validation: `world.plant_seed` raises `SimError("bad_persistence", ...)` unless the value is `None` or an `int` (not `bool`) from 0 to 100. In the protocol, `persistence: Annotated[StrictInt, Field(ge=-COORD_LIMIT ...)] | None`: a strict int or null, with the range checked in the simulation, so 150 reports `bad_persistence` while `50.5` or `"50"` report `bad_message`. This mirrors how `n` and `bad_step` already work.

### Scatter
`scatter(..., persistence=None)` passes the value to every `plant_seed` call. It is validated once at the start, so a bad value plants nothing. That matters because `scatter` draws random numbers before planting, and a value rejected halfway would leave a partial scatter. Validating first also leaves the random generator untouched on rejection.

### Client control
The control goes after the Speed field in `index.html`: `<label class="field"><span>Persistence %</span><input id="persistence" type="number" min="0" max="100" step="1" value="50"></label>` and `<label class="never"><input id="persistence-override" type="checkbox"> Override</label>`. The number is disabled while the box is unticked. `ui` exposes a `persistence` getter that returns the number when ticked and `undefined` otherwise. `undefined` is dropped by `JSON.stringify`, so `net.plant` and `net.scatter` simply pass it through. The value is not checked in the browser: the server's `bad_persistence` message reaches the player through the existing error toast, which satisfies the spec's "brief message".

### Hover text
`describePlant` shows `persistence ${plant.persistence}%` from the plant details for every plant, and drops the Custom `persistence` setting from the settings list, so the value appears once and is always the real one. The catalog-based line added by `add-growth-persistence` is removed.

## Risks / Trade-offs

- [Tests that compare plant details for equality break because of the new key] → Update them. Each is a one-line change.
- [The Custom form still shows its own Persistence % while Override is ticked, which may confuse] → The hover shows the actual value. The README states that Override wins. Greying out the Custom field while Override is on is a possible follow-up.
- [This change modifies "Preset persistence", a requirement that only enters the main specs when `add-growth-persistence` is archived] → Archive that change first. The proposal states the dependency.
