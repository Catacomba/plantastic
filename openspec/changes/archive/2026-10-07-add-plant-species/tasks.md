# Tasks

## 1. Engine groundwork

- [x] 1.1 Add `Tip.state`, `Tip.decided`, `Plant.state`, and `Plant.settings`, and the `Shoot` and `Sprout` types; change the `Species` interface to `start`, `grow(tip, plant, world) -> list[Shoot]`, `on_cut -> list[Sprout]`, `settings`, and `validate`; port `StraightVine` to it; verify the whole existing backend suite passes without editing any existing test
- [x] 1.2 Rework `World._advance` so `grow` is called once per hex (`decided`), shoots update the tip's heading and state and create further tips through `can_sprout`, an empty result ends the tip, and `last=True` removes the tip right after its move; verify unit tests with small stub species for turn, branch, branch without room, end, and `last`
- [x] 1.3 Add unit tests for one decision per hex using a stub species that counts its `grow` calls and draws from `world.rng`: a tip blocked by a cell and a tip stopped by the board limit are each asked exactly once across 20 iterations and advance as decided afterwards; verify they pass
- [x] 1.4 Move the vine's cut logic to a shared `fork` function and add `regrow`, `no_response`, and `multiply`; verify unit tests for each scenario in "Shared cut responses", including regrow with no room and multiply next to the root
- [x] 1.5 Extend `plant_seed` to take settings, call the species' `validate`, store the result on the plant, and reject settings for a species without any with `bad_settings`; verify unit tests for both rejections and that a rejected planting leaves the world unchanged

## 2. Preset species

- [x] 2.1 Implement Zigzag (growth, handedness flip on cut, mirrored sprout); verify unit tests for the wavy line, the first cut mirroring, and the second cut flipping back
- [x] 2.2 Implement Spiral (run schedule, handedness flip on cut, restart at run 1); verify unit tests for the 12-step run lengths, 1000 unobstructed steps with no blocked tip, and the reversed winding after a cut
- [x] 2.3 Implement Fern (stem, alternating 3-cell side branches, no cut response); verify unit tests for the 13-iteration layout, a side branch losing its tip on its third cell, and a stem cut being final while unfinished side branches complete
- [x] 2.4 Implement Wanderer (20 percent turns, regrow); verify unit tests that over 500 steps every step is straight or a 60-degree turn with between 60 and 140 turns, that two same-seed worlds give the same path, and that two different seeds give different paths
- [x] 2.5 Implement Hydra (straight, multiply); verify unit tests for straight growth and the four tips after a cut at cell 5
- [x] 2.6 Implement Burst (fan every 4 cells, fork); verify unit tests for the layout after 6 iterations, nine tips after 10 iterations, and the fork after a cut; if a count is off by an iteration, correct the scenario in the delta spec and note it
- [x] 2.7 Register all species in the catalog and add a determinism test that plants one of each preset in a seeded world, applies scripted cuts, and compares two runs after every iteration; verify it passes

## 3. Custom plant

- [x] 3.1 Define the custom species' setting descriptions (ids, labels, kinds, ranges, defaults) and `validate`; verify unit tests for valid settings, each out-of-range value, minimum above maximum for both pairs, missing keys, unknown keys, and non-whole or boolean values
- [x] 3.2 Implement custom growth (calm counter, forced event, branch and turn rolls, skipped rolls at 0 and 100); verify unit tests for calm minimum 5 with chances of 100, calm maximum 3 with chances of 0 turning every 3 hexes, calm maximum never with chances of 0 staying straight with one tip, and branch chance 100 branching every step
- [x] 3.3 Implement custom branching (random count in range, distinct free side directions, fewer when room is short, new tips starting calm at zero); verify unit tests for a fixed count of 2, a 1-to-3 range producing each count over many branchings, and a single free side hex giving one tip
- [x] 3.4 Wire the custom cut response to the shared functions; verify a unit test that four custom plants differing only in cut response each respond as defined
- [x] 3.5 Add a unit test that two custom plants with different settings planted one after the other each keep growing by their own settings, and a same-seed replay test with custom plants and a blocked period; verify both pass

## 4. Protocol and rooms

- [x] 4.1 Add optional `settings` to the `plant` command and pass it to the board; verify unit tests that valid custom settings plant, invalid ones return `bad_settings` with the board unchanged, and a vine without settings still plants
- [x] 4.2 Add `settings` descriptions to catalog entries in `welcome`, a `plants` list to `welcome`, and created plants to `update` (recorded in `Changes` so merged updates carry them); verify unit tests for the eight-species catalog, the custom species' descriptions, and a new plant's details in its update
- [x] 4.3 Extend the websocket test client to track plant details and add a test that plants a vine and a custom plant, grows, cuts a root, and ends knowing the details of exactly the plants that still have cells; verify it passes
- [x] 4.4 Document the `plant` settings, the catalog `settings` descriptions, the `plants` fields, and `bad_settings` in `docs/protocol.md`; verify the document matches the models

## 5. Client

- [x] 5.1 Keep plant details in `net.js` (`state.plants`), filled from `welcome` and `update` and pruned of plants with no cells; verify in the browser console that the map matches the plants on the board after planting and after cutting a root
- [x] 5.2 Build the settings panel in `ui.js` from the selected species' descriptions (number, optional number with a never option, choice), hidden for species without settings and for other tools, with values kept per species for the visit; verify in the browser that the custom species shows seven controls at their defaults, the vine shows none, and a changed value survives switching species and back
- [x] 5.3 Send the panel's values as `settings` when planting a species that has them; verify in the browser that a custom plant with branch chance 100 branches on every step, one with both chances 0 grows straight, and settings with minimum above maximum show the server's message and plant nothing
- [x] 5.4 Show the hovered plant's species name, speed, and settings in a readout in the top bar, cleared over empty hexes and off the board; verify in the browser with two custom plants of different settings and with a vine
- [x] 5.5 Style the panel and readout in `css/style.css` so the tool bar wraps cleanly at narrow widths; verify at a 1000-pixel-wide window
- [x] 5.6 Update `README.md` with the species list, one line on each, and the custom plant's settings; verify the text matches the behavior

## 6. Integration check

- [x] 6.1 Run the full backend test suite and confirm it passes
- [x] 6.2 Play through in a browser: plant one of every species and watch each pattern, cut each one and watch its response, plant two custom plants with different settings and compare them by hovering, change the settings and confirm the earlier plants are unaffected, and confirm the scissors, mower, panning, and clock controls still work
