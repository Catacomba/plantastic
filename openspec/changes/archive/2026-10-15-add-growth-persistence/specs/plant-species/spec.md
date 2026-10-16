# Spec Delta

## ADDED Requirements

### Requirement: Preset persistence
Each species without settings SHALL have a fixed persistence that every one of its plants uses. The values SHALL be: straight vine 0, fern 0, zigzag 30, spiral 30, burst 30, wanderer 60, and hydra 80.

#### Scenario: Plants that still stop
- **WHEN** a straight vine or a fern runs into an occupied hex
- **THEN** its tip waits and never takes another path

#### Scenario: Persistent hydra
- **WHEN** many hydras each meet one obstacle with both side hexes empty
- **THEN** between 70 and 90 percent of them take another path

#### Scenario: Scattered plants keep their species' persistence
- **WHEN** seeds are scattered and grow into one another
- **THEN** each plant takes another path at its species' persistence

### Requirement: Patterns after taking another path
After a tip takes another path, each species SHALL continue its own pattern from the hex the tip entered. Species that grow along their current heading SHALL carry on in the new direction. The zigzag SHALL keep alternating around its starting direction, so a detour shifts its line sideways by one hex without changing where it heads.

#### Scenario: Zigzag sidesteps
- **WHEN** a zigzag seeded heading east takes another path around an obstacle
- **THEN** its later steps still alternate between east and south-east

#### Scenario: Burst arm turns
- **WHEN** an arm of a burst takes another path
- **THEN** that arm grows on in its new direction and still fans after every 4 cells it grows

## MODIFIED Requirements

### Requirement: Species catalog
The game SHALL offer a catalog of plant species. Each species SHALL have a unique identifier, a display name, a default speed, a persistence, a growth pattern, a cut response, and a description of the settings a player may choose for it, which is empty for a species without settings. Every plant SHALL belong to exactly one species from the catalog. The catalog SHALL contain the straight vine, zigzag, spiral, fern, wanderer, hydra, burst, and custom species.

#### Scenario: Catalog contents
- **WHEN** the catalog is requested
- **THEN** it lists every available species with its identifier, display name, and default speed, and it includes the straight vine

#### Scenario: Unknown species
- **WHEN** a seed is planted with a species identifier that is not in the catalog
- **THEN** the planting is rejected and the board is unchanged

#### Scenario: All eight species
- **WHEN** the catalog is requested
- **THEN** it lists exactly the straight vine, zigzag, spiral, fern, wanderer, hydra, burst, and custom species

#### Scenario: Settings are described
- **WHEN** the catalog is requested
- **THEN** the custom species lists each of its settings with a name, the kind of value, the allowed range or choices, and a default, and every other species lists no settings

#### Scenario: Persistence is listed
- **WHEN** the catalog is requested
- **THEN** every species without settings lists its fixed persistence, and the custom species lists none because each custom plant takes its persistence from its settings

### Requirement: Hydra
The hydra SHALL grow in a straight line as the straight vine does, but with its own persistence. The hydra's cut response SHALL be multiply.

#### Scenario: Straight growth
- **WHEN** a hydra grows unobstructed for 5 iterations at speed 1
- **THEN** it is a straight line of 5 cells with a single tip at the far end

#### Scenario: Cut multiplies
- **WHEN** a hydra grown east through cells 1 to 6 is cut at cell 5
- **THEN** it has four new tips: north-east and south-east from cell 4, and north-east and south-east from cell 3

### Requirement: Wanderer
The wanderer SHALL grow mostly straight: on each step a tip has a 20 percent chance of turning 60 degrees, to the left or the right with equal chance, and otherwise keeps its direction. It SHALL never branch on its own. The wanderer's cut response SHALL be regrow.

#### Scenario: Gentle turns only
- **WHEN** many wanderers each grow until they stop
- **THEN** every step a wanderer chose for itself, rather than a detour around an obstacle, is either in the same direction as the one before or 60 degrees away from it, and between 15 and 25 percent of those steps are turns

#### Scenario: Detours never double back
- **WHEN** many wanderers each grow until they stop, taking other paths around obstacles
- **THEN** no step is more than 120 degrees away from the one before

#### Scenario: Runs into itself
- **WHEN** a wanderer's path leads it into one of its own cells and it does not take another path
- **THEN** the tip waits there like any other blocked tip, and the plant stops growing until it is cut

#### Scenario: Same seed, same path
- **WHEN** two boards with the same random seed each grow a wanderer planted in the same hex
- **THEN** both wanderers follow the same path

#### Scenario: Cut regrows one tip
- **WHEN** a wanderer is cut
- **THEN** one new tip sprouts from the cell behind the stump in a random free direction

### Requirement: Custom plant settings
The custom species SHALL take these settings when planted: branch chance, turn chance, and persistence, each a whole percentage from 0 to 100; branches minimum and maximum, whole numbers from 1 to 4 with minimum not above maximum; calm minimum, a whole number from 0 to 1000; calm maximum, either never or a whole number from calm minimum to 1000; and cut response, one of fork, regrow, none, and multiply. Settings that are missing, out of range, or inconsistent SHALL make the planting fail.

#### Scenario: Valid settings
- **WHEN** a custom seed is planted with every setting inside its range
- **THEN** the plant is created with exactly those settings

#### Scenario: Out of range
- **WHEN** a custom seed is planted with a branch chance of 150, a persistence of 101, 5 branches, or a cut response that does not exist
- **THEN** the planting is rejected and the board is unchanged

#### Scenario: Inconsistent
- **WHEN** a custom seed is planted with branches minimum above maximum, or calm maximum below calm minimum
- **THEN** the planting is rejected and the board is unchanged

#### Scenario: Missing settings
- **WHEN** a custom seed is planted without settings, or without a persistence
- **THEN** the planting is rejected and the board is unchanged

#### Scenario: Persistence is used
- **WHEN** two custom plants that differ only in persistence, 0 and 100, each run into an obstacle with an empty side hex
- **THEN** the plant with persistence 0 waits and the plant with persistence 100 takes another path
