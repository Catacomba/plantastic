# Spec Delta

## MODIFIED Requirements

### Requirement: Species catalog
The game SHALL offer a catalog of plant species. Each species SHALL have a unique identifier, a display name, a default speed, a growth pattern, a cut response, and a description of the settings a player may choose for it, which is empty for a species without settings. Every plant SHALL belong to exactly one species from the catalog. The catalog SHALL contain the straight vine, zigzag, spiral, fern, wanderer, hydra, burst, and custom species.

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

## ADDED Requirements

### Requirement: Shared cut responses
The game SHALL define four cut responses that species may use. **Fork** is the straight vine's response: two tips, forward-left and forward-right, from the cell two back from the stump. **Regrow** sprouts one tip from the cell behind the stump, in a direction chosen at random among that cell's empty neighbors. **None** sprouts nothing. **Multiply** forks forward-left and forward-right from both of the two cells behind the stump. Every sprout SHALL need an empty first hex, and a cell missing because the root is nearer SHALL simply contribute no sprouts.

#### Scenario: Regrow
- **WHEN** a plant with the regrow response is cut and the cell behind the stump has empty neighbors
- **THEN** exactly one new tip sits on the cell behind the stump, heading into one of its empty neighbors

#### Scenario: Regrow with no room
- **WHEN** a plant with the regrow response is cut and every neighbor of the cell behind the stump is occupied
- **THEN** no new tip is created

#### Scenario: None
- **WHEN** a plant with the none response is cut
- **THEN** the cut cell becomes a stump, the severed part is removed, and no new tip is created

#### Scenario: Multiply
- **WHEN** a straight plant with the multiply response, grown east through cells 1 to 6, is cut at cell 5
- **THEN** cell 4 and cell 3 each have two new tips, one heading north-east and one heading south-east

#### Scenario: Multiply next to the root
- **WHEN** a plant with the multiply response is cut at the cell adjacent to its root
- **THEN** only the root has new tips, heading forward-left and forward-right

### Requirement: Zigzag
The zigzag SHALL travel in a wavy line: a tip takes its first step in its starting direction, its next step turned 60 degrees to one side, the next back in the starting direction, and so on, always turning to the same side. A seed's tip SHALL turn to the right. When a zigzag is cut, the plant's turning side SHALL flip, and one new tip SHALL sprout from the cell behind the stump, heading 60 degrees to the new turning side of the direction to the stump and zigzagging to that side.

#### Scenario: Wavy line
- **WHEN** a zigzag seeded heading east grows unobstructed for 6 steps
- **THEN** its steps head east, south-east, east, south-east, east, south-east

#### Scenario: Cut mirrors the zigzag
- **WHEN** a zigzag that has only ever turned right is cut
- **THEN** one new tip sits on the cell behind the stump, heading 60 degrees left of the direction to the stump, and its later steps alternate between that direction and 60 degrees further left

#### Scenario: Second cut flips back
- **WHEN** the same zigzag is cut a second time
- **THEN** the new tip turns to the right

### Requirement: Spiral
The spiral SHALL wind outward: a tip grows in straight runs and turns 60 degrees to the same side after each run, with runs of 1, 1, 2, 2, 3, 3 cells and so on, one cell longer after every second turn. A seed's tip SHALL turn to the right. Unobstructed, a spiral SHALL never run into its own earlier cells. When a spiral is cut, the plant's turning side SHALL flip, and one new tip SHALL sprout from the cell behind the stump, heading 60 degrees to the new turning side of the direction to the stump and starting again from a run of 1.

#### Scenario: Run lengths
- **WHEN** a spiral seeded heading east grows unobstructed for 12 steps
- **THEN** it takes 1 step east, 1 south-east, 2 south-west, 2 west, 3 north-west, and 3 north-east

#### Scenario: Never crosses itself
- **WHEN** a spiral grows unobstructed for 1000 steps
- **THEN** it has gained 1000 cells and no tip was ever blocked

#### Scenario: Cut reverses the winding
- **WHEN** a right-turning spiral is cut
- **THEN** one new tip sits on the cell behind the stump, heading 60 degrees left of the direction to the stump, and it turns left after runs of 1, 1, 2, 2 cells and so on

### Requirement: Fern
The fern SHALL grow a straight stem that never turns. Every third cell of the stem SHALL sprout one side branch, heading 60 degrees off the stem, on alternating sides starting with the left. A side branch SHALL grow straight for exactly 3 cells and then stop, and SHALL never branch. The fern's cut response SHALL be none.

#### Scenario: Stem and side branches
- **WHEN** a fern grows unobstructed for 13 iterations at speed 1
- **THEN** its stem is 13 cells long in the starting direction, cells 3 and 9 of the stem each carry a 3-cell side branch to the left, cell 6 carries a 3-cell side branch to the right, and cell 12 has a new tip heading off to the right that has not grown yet

#### Scenario: Side branch length
- **WHEN** a side branch has grown its third cell
- **THEN** it has no tip from that moment and never grows again

#### Scenario: Cut is final
- **WHEN** the stem of a fern is cut
- **THEN** no new tip appears, the stem never grows again, and side branches behind the cut that were still growing finish their 3 cells

### Requirement: Wanderer
The wanderer SHALL grow mostly straight: on each step a tip has a 20 percent chance of turning 60 degrees, to the left or the right with equal chance, and otherwise keeps its direction. It SHALL never branch on its own. The wanderer's cut response SHALL be regrow.

#### Scenario: Gentle turns only
- **WHEN** many wanderers each grow until they are blocked
- **THEN** every step any of them took is either in the same direction as the one before or 60 degrees away from it, and between 15 and 25 percent of all the steps are turns

#### Scenario: Runs into itself
- **WHEN** a wanderer's path leads it into one of its own cells
- **THEN** the tip waits there like any other blocked tip, and the plant stops growing until it is cut

#### Scenario: Same seed, same path
- **WHEN** two boards with the same random seed each grow a wanderer planted in the same hex
- **THEN** both wanderers follow the same path

#### Scenario: Cut regrows one tip
- **WHEN** a wanderer is cut
- **THEN** one new tip sprouts from the cell behind the stump in a random free direction

### Requirement: Hydra
The hydra SHALL grow in a straight line exactly as the straight vine does. The hydra's cut response SHALL be multiply.

#### Scenario: Straight growth
- **WHEN** a hydra grows unobstructed for 5 iterations at speed 1
- **THEN** it is a straight line of 5 cells with a single tip at the far end

#### Scenario: Cut multiplies
- **WHEN** a hydra grown east through cells 1 to 6 is cut at cell 5
- **THEN** it has four new tips: north-east and south-east from cell 4, and north-east and south-east from cell 3

### Requirement: Burst
The burst SHALL fan out: a tip grows straight for 4 cells, and on reaching the fourth it sprouts two more tips, forward-left and forward-right, while itself continuing straight. Each of the three tips SHALL then repeat the pattern from a count of zero. The burst's cut response SHALL be fork.

#### Scenario: First fan
- **WHEN** a burst seeded heading east grows unobstructed for 6 iterations at speed 1
- **THEN** it has 6 cells in a line east of its root, one cell to the north-east and one to the south-east of the fourth cell, and three tips

#### Scenario: Fans repeat
- **WHEN** a burst grows unobstructed for 10 iterations at speed 1
- **THEN** each of the three arms has itself fanned into three after growing 4 cells, giving nine tips

#### Scenario: Cut forks
- **WHEN** a burst is cut
- **THEN** it forks forward-left and forward-right from two cells behind the stump, as the straight vine does

### Requirement: Custom plant settings
The custom species SHALL take these settings when planted: branch chance and turn chance, each a whole percentage from 0 to 100; branches minimum and maximum, whole numbers from 1 to 4 with minimum not above maximum; calm minimum, a whole number from 0 to 1000; calm maximum, either never or a whole number from calm minimum to 1000; and cut response, one of fork, regrow, none, and multiply. Settings that are missing, out of range, or inconsistent SHALL make the planting fail.

#### Scenario: Valid settings
- **WHEN** a custom seed is planted with every setting inside its range
- **THEN** the plant is created with exactly those settings

#### Scenario: Out of range
- **WHEN** a custom seed is planted with a branch chance of 150, with 5 branches, or with a cut response that does not exist
- **THEN** the planting is rejected and the board is unchanged

#### Scenario: Inconsistent
- **WHEN** a custom seed is planted with branches minimum above maximum, or calm maximum below calm minimum
- **THEN** the planting is rejected and the board is unchanged

#### Scenario: Missing settings
- **WHEN** a custom seed is planted without settings
- **THEN** the planting is rejected and the board is unchanged

### Requirement: Custom plant growth
A custom plant's tip SHALL count the hexes it has entered since it last branched or turned, or since it was created. On each step: below calm minimum it SHALL go straight; at calm maximum it SHALL be forced to branch or turn; otherwise it SHALL branch with the branch chance, and if it does not branch, turn with the turn chance, and otherwise go straight. A forced event SHALL be a branch or a turn in proportion to the two chances, and a turn if both are zero. A turn SHALL be 60 degrees left or right with equal chance.

#### Scenario: Calm minimum
- **WHEN** a custom plant with calm minimum 5 and branch and turn chances of 100 grows
- **THEN** every tip enters 5 hexes in a straight line after each branch or turn before the next one

#### Scenario: Calm maximum forces an event
- **WHEN** a custom plant with calm maximum 3, branch chance 0, and turn chance 0 grows unobstructed
- **THEN** its tip turns after every 3 hexes entered in a straight line

#### Scenario: Never
- **WHEN** a custom plant with calm maximum never and branch and turn chances of 0 grows
- **THEN** it grows in a straight line indefinitely with a single tip

#### Scenario: Chances of zero and one hundred
- **WHEN** a custom plant with calm minimum 0, branch chance 100, and branches minimum and maximum 1 grows unobstructed for 3 steps
- **THEN** it branches on every step

### Requirement: Custom plant branching
When a custom plant's tip branches, the tip itself SHALL continue straight, and a number of new tips chosen at random between branches minimum and maximum SHALL sprout from the cell it is leaving. Each new tip SHALL head in a different direction, chosen at random from the forward-left, forward-right, back-left, and back-right directions whose hexes are empty. If fewer such directions are empty than the number chosen, only that many tips SHALL sprout. A new tip SHALL start its own calm count at zero.

#### Scenario: Fixed number of branches
- **WHEN** a custom plant with branches minimum and maximum both 2 branches with all four side hexes empty
- **THEN** exactly two new tips sprout from that cell in two different side directions, and the original tip continues straight

#### Scenario: Range of branches
- **WHEN** a custom plant with branches minimum 1 and maximum 3 branches many times with room to spare
- **THEN** every branching produces 1, 2, or 3 new tips, and each of those counts occurs

#### Scenario: Not enough room
- **WHEN** a custom plant set to 4 branches branches where only one side hex is empty
- **THEN** exactly one new tip sprouts

### Requirement: Custom plant cut response
A custom plant SHALL respond to a cut with the cut response chosen in its settings.

#### Scenario: Chosen response is used
- **WHEN** four custom plants that differ only in cut response are each cut in the same place
- **THEN** each responds as the fork, regrow, none, and multiply responses define
