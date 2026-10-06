# Spec Delta

## ADDED Requirements

### Requirement: Cutting along a path
The simulation SHALL accept an ordered list of hexes and cut, in that order, every hex that holds a living non-root cell at the moment its turn comes. Each such cut SHALL behave exactly as a single cut, including the species' cut response. Hexes that are empty or hold a stump at their turn SHALL be skipped without rejecting the path. All cuts of one path SHALL take effect within the same iteration.

#### Scenario: Path crosses two vines
- **WHEN** a path passes over one cell of each of two separate vines, with empty hexes in between
- **THEN** both cells become stumps, both severed parts are removed, both plants respond as their species defines, and the empty hexes have no effect

#### Scenario: Path of only empty hexes and stumps
- **WHEN** a path contains no living non-root cell
- **THEN** the board is unchanged and the path is not rejected

#### Scenario: Path runs along a vine away from the root
- **WHEN** a path visits several cells of one vine in order from the root end toward the tip
- **THEN** the first visited cell becomes a stump, everything beyond it is removed, and the later hexes of the path have no effect because they are empty by their turn

#### Scenario: Path runs along a vine toward the root
- **WHEN** a path visits several cells of one vine in order from the tip end toward the root
- **THEN** only the last visited cell remains as a stump, because each cut removes the stump left by the one before it

#### Scenario: Same iteration
- **WHEN** a path of any length is applied
- **THEN** the iteration number is the same before and after, and no plant grows in between the cuts

### Requirement: Paths never cut roots
A root cell SHALL NOT be cut by a path, whatever its position in the path and whatever the path's length. Removing a whole plant SHALL remain possible only through a single cut aimed at its root.

#### Scenario: Path passes over a root
- **WHEN** a path includes the hex of a plant's root
- **THEN** the root and the plant remain, and the other hexes of the path are cut as usual

#### Scenario: Path of one hex on a root
- **WHEN** a path consists of a single hex that holds a root
- **THEN** the board is unchanged
