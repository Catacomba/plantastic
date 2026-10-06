# Spec Delta

## Purpose

Defines the plant species available in the game and how each one behaves: the path its tips take as they grow and how the plant responds when it is cut.

## ADDED Requirements

### Requirement: Species catalog
The game SHALL offer a catalog of plant species. Each species SHALL have a unique identifier, a display name, a default speed, a growth pattern, and a cut response. Every plant SHALL belong to exactly one species from the catalog.

#### Scenario: Catalog contents
- **WHEN** the catalog is requested
- **THEN** it lists every available species with its identifier, display name, and default speed, and it includes the straight vine

#### Scenario: Unknown species
- **WHEN** a seed is planted with a species identifier that is not in the catalog
- **THEN** the planting is rejected and the board is unchanged

### Requirement: Straight vine growth
The straight vine SHALL grow in a straight line: every tip SHALL keep the direction it started with for as long as it exists, and SHALL never branch on its own.

#### Scenario: Unobstructed growth
- **WHEN** a straight vine with speed 1 grows unobstructed for 5 iterations
- **THEN** the plant is a straight line of 5 cells leading away from its root in the tip's starting direction, with a single tip at the far end

### Requirement: Straight vine cut response
When a straight vine is cut, it SHALL sprout two new tips from the cell two cells back from the stump along the vine toward the root. Taking the direction in which the vine leaves that cell toward the stump as forward, one new tip SHALL head forward-left and the other forward-right, each 60 degrees from forward. New tips SHALL start with no progress.

#### Scenario: Fork after a cut
- **WHEN** a straight vine running east from its root through cells 1 to 6 is cut at cell 5
- **THEN** cell 5 is a stump, cell 6 is gone, and cell 3 has two new tips, one heading north-east and one heading south-east

#### Scenario: Forks keep their direction
- **WHEN** the two tips created by a cut continue to grow
- **THEN** each grows in a straight line in its own direction, diverging from the other

#### Scenario: Fork appears after one growth interval
- **WHEN** a straight vine with speed 0.5 is cut
- **THEN** each new tip occupies its first new hex 2 iterations later

### Requirement: Straight vine cut near the root
When a straight vine is cut fewer than two cells from its root, the new tips SHALL sprout from the root, using the direction from the root toward the stump as forward.

#### Scenario: Cut the first cell
- **WHEN** a straight vine is cut at the cell adjacent to its root
- **THEN** that cell is a stump and the root has two new tips, heading forward-left and forward-right of the direction from the root to the stump

### Requirement: Straight vine sprouts need room
A sprout from a straight vine cut SHALL be created only if the hex it would grow into is empty at the moment of the cut and the plant has no existing tip at the same cell with the same direction. The other sprout SHALL be unaffected.

#### Scenario: One side is occupied
- **WHEN** a straight vine is cut and the forward-left hex of the sprouting cell is occupied while the forward-right hex is empty
- **THEN** only the forward-right tip is created

#### Scenario: Both sides are occupied
- **WHEN** a straight vine is cut and both sprout hexes are occupied
- **THEN** the cut cell still becomes a stump and the severed part is still removed, but no new tips are created
