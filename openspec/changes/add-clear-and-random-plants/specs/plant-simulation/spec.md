# Spec Delta

## ADDED Requirements

### Requirement: Clearing the board
The simulation SHALL allow the whole board to be cleared in one action, removing every plant, cell, and tip. Clearing SHALL NOT change the iteration number, and plants planted afterwards SHALL get identifiers that were never used before on that board. Clearing an empty board SHALL be allowed and SHALL change nothing.

#### Scenario: Clear a crowded board
- **WHEN** a board holding several plants, including stumps and waiting tips, is cleared
- **THEN** it has no plants, no cells, and no tips, and every hex is empty

#### Scenario: Iteration number is kept
- **WHEN** a board at iteration 40 is cleared
- **THEN** it is still at iteration 40, and the next iteration is 41

#### Scenario: Planting after a clear
- **WHEN** a board that has held three plants is cleared and a seed is planted
- **THEN** the new plant's identifier differs from those of the three earlier plants, and it grows normally

#### Scenario: Clear an empty board
- **WHEN** an empty board is cleared
- **THEN** it is still empty and nothing else has changed

### Requirement: Scattering random seeds
The simulation SHALL allow a number of seeds to be planted at once at random empty hexes inside a given region. Each seed's species SHALL be drawn at random, independently of the others, from the species that take no settings, and each seed SHALL use its species' default speed and a random starting direction. No two seeds SHALL share a hex, and no seed SHALL be placed on an occupied hex or outside the region. Each seed SHALL record the player who scattered it as its owner.

#### Scenario: Scatter on an empty region
- **WHEN** 20 seeds are scattered in a region of several hundred empty hexes
- **THEN** 20 new plants exist, each on a different hex inside the region, each with one tip and its species' default speed

#### Scenario: Species are drawn from those without settings
- **WHEN** many seeds are scattered
- **THEN** every one is of a species that takes no settings, none is a custom plant, and every such species appears among them

#### Scenario: The mix is not balanced
- **WHEN** 7 seeds are scattered many times over
- **THEN** some of those scatters contain the same species more than once

#### Scenario: Occupied hexes are avoided
- **WHEN** seeds are scattered in a region where some hexes are occupied
- **THEN** every new seed is on a hex that was empty, and no existing cell is changed

#### Scenario: Scattered plants grow like any other
- **WHEN** seeds are scattered and the board advances
- **THEN** each plant grows by its species' rules

### Requirement: Scattering plants as many as fit
When a region has fewer empty hexes than the number of seeds asked for, or the board reaches its size limit, scattering SHALL plant as many seeds as fit and SHALL report how many it planted. Planting none SHALL NOT be an error.

#### Scenario: Not enough room
- **WHEN** 50 seeds are scattered in a region with 12 empty hexes
- **THEN** exactly 12 seeds are planted, one on each of those hexes, and the result reports 12

#### Scenario: Full region
- **WHEN** seeds are scattered in a region with no empty hex
- **THEN** nothing is planted, the board is unchanged, and the result reports 0

#### Scenario: Board limit
- **WHEN** seeds are scattered on a board that has room for only 3 more cells
- **THEN** exactly 3 seeds are planted

### Requirement: Scattering is reproducible
The positions, species, and starting directions chosen when scattering SHALL derive from the board's random seed, so that two boards with the same seed that receive the same actions scatter identically.

#### Scenario: Same seed, same scatter
- **WHEN** two boards with the same random seed each scatter 30 seeds in the same region
- **THEN** both have the same species on the same hexes heading in the same directions

#### Scenario: Different seed, different scatter
- **WHEN** two boards with different random seeds each scatter 30 seeds in the same region
- **THEN** their plants differ
