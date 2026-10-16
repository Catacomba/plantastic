# plant-simulation Specification

## Purpose

Defines the world plants live in and the rules by which they grow and are cut: an unbounded hexagonal grid advanced one iteration at a time, with results that are fully reproducible.

## Requirements

### Requirement: Unbounded hexagonal grid
The simulation SHALL model the board as a hexagonal grid with no edges, in which every hex has exactly six neighbors and any hex can be addressed. A hex SHALL be either empty or occupied by exactly one cell of exactly one plant.

#### Scenario: Growth far from the origin
- **WHEN** a plant grows for any number of iterations in one direction with nothing in its way
- **THEN** it keeps gaining cells and never stops because of a board boundary

#### Scenario: One occupant per hex
- **WHEN** a hex is already occupied by a plant cell
- **THEN** no other cell, of the same or another plant, can be placed in that hex

### Requirement: Planting a seed
The simulation SHALL allow a seed of a chosen species and speed to be planted in an empty hex, together with settings when the species has them. Planting SHALL create a new plant consisting of a root cell in that hex and one growing tip at the root. The tip's starting direction SHALL be chosen at random from the six directions unless a direction is given. Each plant SHALL record the player who owns it. A plant's species, speed, and settings SHALL be fixed when it is planted and SHALL never change afterwards.

#### Scenario: Seed in an empty hex
- **WHEN** a seed is planted in an empty hex without a direction
- **THEN** a new plant exists with a root in that hex, one tip heading in one of the six directions, and the planting player as its owner

#### Scenario: Seed in an occupied hex
- **WHEN** a seed is planted in a hex that is already occupied
- **THEN** the planting is rejected and the board is unchanged

#### Scenario: Seed with settings
- **WHEN** a seed of a species that has settings is planted with valid settings
- **THEN** the new plant holds exactly those settings

#### Scenario: Settings for a species without any
- **WHEN** a seed of a species that has no settings is planted with settings
- **THEN** the planting is rejected and the board is unchanged

#### Scenario: Later seeds do not affect earlier plants
- **WHEN** two seeds of the same species are planted with different settings, one after the other
- **THEN** each plant grows by its own settings for as long as it exists

### Requirement: Growth by speed
Each plant SHALL have a speed, a positive number of hexagons per iteration that may be fractional or greater than one. Each iteration, every tip SHALL accumulate progress equal to its plant's speed and SHALL advance one hex for each whole unit of progress, carrying any remainder forward. Speeds SHALL be applied exactly, with no rounding drift.

#### Scenario: Fractional speed
- **WHEN** a plant with speed 0.25 grows unobstructed for 8 iterations
- **THEN** its tip has advanced exactly 2 hexes, one at iteration 4 and one at iteration 8

#### Scenario: Speed above one
- **WHEN** a plant with speed 2 grows unobstructed for 3 iterations
- **THEN** its tip has advanced exactly 6 hexes

#### Scenario: Remainder carries over
- **WHEN** a plant with speed 0.3 grows unobstructed for 10 iterations
- **THEN** its tip has advanced exactly 3 hexes, at iterations 4, 7, and 10

#### Scenario: Invalid speed
- **WHEN** a seed is planted with a speed that is zero, negative, not a number, or above the allowed maximum
- **THEN** the planting is rejected and the board is unchanged

### Requirement: Blocked tips wait
A tip whose next hex is occupied, and that does not take another path around it, SHALL NOT advance and SHALL NOT turn. It SHALL remain a tip, and SHALL advance on a later iteration once that hex is empty. While blocked, a tip SHALL NOT bank more than one hex of progress.

#### Scenario: Tip runs into another plant
- **WHEN** a tip of a plant with persistence 0 finds its next hex occupied by any cell
- **THEN** the tip stays where it is for as long as that hex is occupied

#### Scenario: Obstacle is removed
- **WHEN** the cell blocking a waiting tip is removed by a cut
- **THEN** the tip advances into the freed hex on the next iteration and continues at its normal speed, without a burst of catch-up growth

### Requirement: Tips turn, branch, and end
On each step a tip's species SHALL decide whether the tip continues in a new or unchanged direction, sprouts further tips, or ends. A tip created by branching SHALL sit on the cell it branched from, SHALL start with no progress, and SHALL be created only if the hex it would grow into is empty and its plant has no tip on that cell with that direction. A tip that ends SHALL be removed, and the cells it grew SHALL remain.

#### Scenario: Turn
- **WHEN** a species turns a tip on a step
- **THEN** the tip's next cell is in the new direction, joined to the cell it left

#### Scenario: Branch
- **WHEN** a species branches a tip that continues straight and sprouts one tip to the side
- **THEN** the original tip advances, and a second tip sits on the cell it left, heading to the side with no progress

#### Scenario: Branch without room
- **WHEN** a species sprouts a tip toward a hex that is occupied at that moment
- **THEN** that tip is not created and the rest of the step is unaffected

#### Scenario: End
- **WHEN** a species ends a tip
- **THEN** the tip no longer exists, its cells remain on the board, and the plant's other tips keep growing

### Requirement: One growth decision per hex
A tip SHALL make its growth decision once for each hex it enters. A tip that cannot advance, because its next hex is occupied or because the board is full, SHALL keep the decision it made and SHALL NOT decide again or sprout further tips until it has advanced. Apart from its single persistence roll for that hex, it SHALL NOT draw further random numbers while it waits.

#### Scenario: Blocked after deciding to turn
- **WHEN** a tip of a plant with persistence 0 decides to turn and finds the hex in its new direction occupied
- **THEN** it waits heading in that direction, and advances that way once the hex is empty

#### Scenario: Board full
- **WHEN** a tip of a species that branches at random cannot advance for 20 iterations because the board is full
- **THEN** it has sprouted nothing and changed nothing during those iterations, and when room is made it advances as it had decided before the wait

#### Scenario: Waiting does not disturb replay
- **WHEN** two boards with the same random seed receive the same actions, including a period in which tips are blocked and some take another path
- **THEN** the boards are identical after every iteration

### Requirement: Deterministic collisions
When more than one tip is due to enter the same empty hex in the same iteration, exactly one SHALL enter it and the others SHALL be blocked. The tip of the plant planted earliest SHALL win; between tips of the same plant, the tip created earliest SHALL win. A tip that loses SHALL then be treated like any other blocked tip, including its persistence roll.

#### Scenario: Two plants reach the same hex
- **WHEN** tips of two different plants are both due to enter the same empty hex in one iteration
- **THEN** the tip of the plant that was planted first occupies the hex and the other tip is blocked

#### Scenario: The loser takes another path
- **WHEN** the losing tip of a contested hex belongs to a plant with persistence 100 and one of its side hexes is empty
- **THEN** it enters that side hex in the same iteration

### Requirement: Cutting a plant
Cutting a hex that holds a living, non-root plant cell SHALL turn that cell into a stump and SHALL immediately remove every cell and tip of that plant that was connected to the root only through the cut cell. A stump SHALL keep occupying its hex and SHALL never grow. The plant SHALL then respond to the cut as its species defines.

#### Scenario: Cut in the middle of a vine
- **WHEN** a cell in the middle of a vine is cut
- **THEN** that cell becomes a stump, all cells beyond it are removed and their hexes become empty, and the cells between the root and the stump are unchanged

#### Scenario: Cut the cell a tip sits on
- **WHEN** the leading cell of a vine is cut
- **THEN** that cell becomes a stump and its tip no longer exists

#### Scenario: Severed part contained branches and stumps
- **WHEN** the part beyond a cut contains side branches or older stumps
- **THEN** all of them are removed along with the rest of the severed part

### Requirement: Cutting the root, a stump, or an empty hex
Cutting a plant's root cell SHALL remove the entire plant, including its stumps. Cutting a stump or an empty hex SHALL be rejected and SHALL leave the board unchanged.

#### Scenario: Cut the root
- **WHEN** the root cell of a plant is cut
- **THEN** every cell and tip of that plant is removed and all of its hexes become empty

#### Scenario: Cut a stump
- **WHEN** a hex holding a stump is cut
- **THEN** the cut is rejected and the board is unchanged

#### Scenario: Cut an empty hex
- **WHEN** an empty hex is cut
- **THEN** the cut is rejected and the board is unchanged

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

### Requirement: Reproducible simulation
The simulation SHALL be deterministic: starting from the same random seed and applying the same actions at the same iterations SHALL always produce the same board. All random choices SHALL derive from that seed.

#### Scenario: Replaying a session
- **WHEN** two boards are created with the same random seed and receive the same plantings and cuts at the same iterations
- **THEN** both boards are identical after every iteration, including the random starting directions of seeds

### Requirement: Board size limit
A board SHALL have a maximum number of occupied hexes. Growth and planting SHALL NOT take the board beyond that maximum, and the simulation SHALL report when the maximum has been reached.

#### Scenario: Limit reached during growth
- **WHEN** an iteration would take the number of occupied hexes above the maximum
- **THEN** growth stops at the maximum, and the simulation reports that the board is full

#### Scenario: Space freed by cutting
- **WHEN** a full board has cells removed by a cut
- **THEN** growth can continue on later iterations

### Requirement: Iterations report their work
Each iteration SHALL report the number of tip visits it made, where a tip visit is one attempt to move a tip that was due to advance, whether or not the tip then moved. The count SHALL depend only on the state of the board, so that two boards in the same state report the same count, and counting SHALL NOT change the outcome of the iteration.

#### Scenario: One growing tip
- **WHEN** a board with a single unobstructed tip of speed 1 advances one iteration
- **THEN** the iteration reports 1 tip visit

#### Scenario: Fast tip
- **WHEN** a board with a single unobstructed tip of speed 2 advances one iteration
- **THEN** the iteration reports 2 tip visits, one for each hex entered

#### Scenario: Slow tip that is not due
- **WHEN** a board with a single tip of speed 0.25 advances one iteration in which the tip does not move
- **THEN** the iteration reports 0 tip visits

#### Scenario: Waiting tip still counts
- **WHEN** a board whose only tip is blocked advances one iteration
- **THEN** the iteration reports 1 tip visit, although nothing moved

#### Scenario: Same board, same count
- **WHEN** two boards with the same random seed receive the same actions
- **THEN** they report the same number of tip visits for every iteration

#### Scenario: Several iterations together
- **WHEN** several iterations are advanced as one batch
- **THEN** the reported tip visits are the sum of the visits of each iteration

### Requirement: Blocked tips may take another path
Each plant SHALL have a persistence, a whole percentage from 0 to 100, fixed when it is planted. When a tip's next hex is occupied by any cell, including one of its own plant, and the board is not full, the tip SHALL roll its persistence once, provided a hex 60 or 120 degrees to either side of its heading is empty. If the roll succeeds, the tip SHALL turn into the gentlest such hex and advance into it at once: a 60-degree turn when one is empty, otherwise a 120-degree turn, choosing at random between two equally sharp empty turns. It SHALL never turn straight back.

#### Scenario: Persistence of zero
- **WHEN** a tip of a plant with persistence 0 finds its next hex occupied
- **THEN** it waits without turning, exactly as a blocked tip did before persistence existed

#### Scenario: Persistence of one hundred
- **WHEN** a tip of a plant with persistence 100 heading east finds its next hex occupied, with the north-east hex occupied and the south-east hex empty
- **THEN** the tip turns south-east and enters that hex in the same iteration

#### Scenario: Both sides empty
- **WHEN** tips of plants with persistence 100 are blocked many times with both side hexes empty
- **THEN** each detour goes 60 degrees left or right, and both sides occur

#### Scenario: Only a sharp turn is free
- **WHEN** a tip of a plant with persistence 100 heading east finds its next hex, the north-east hex, and the south-east hex occupied, with the north-west hex empty and the south-west hex occupied
- **THEN** the tip turns north-west and enters that hex in the same iteration

#### Scenario: Both sharp turns free
- **WHEN** tips of plants with persistence 100 are blocked many times with both 60-degree turns occupied and both 120-degree turns empty
- **THEN** each detour goes 120 degrees left or right, and both sides occur

#### Scenario: Gentle turns come first
- **WHEN** a blocked tip of a plant with persistence 100 has one 60-degree turn and both 120-degree turns empty
- **THEN** it always takes the 60-degree turn

#### Scenario: Blocked by its own plant
- **WHEN** a tip of a plant with persistence 100 runs into one of its own plant's cells and a side hex is empty
- **THEN** it takes another path just as it would around another plant

#### Scenario: No empty side
- **WHEN** a blocked tip's hexes 60 and 120 degrees to both sides are all occupied
- **THEN** it waits, and no random number is drawn for it

#### Scenario: Board full
- **WHEN** a tip's next hex is occupied while the board is full
- **THEN** it waits, and no random number is drawn for it

#### Scenario: Rough rate
- **WHEN** many tips of plants with persistence 30 each meet one obstacle with both sides empty
- **THEN** between 20 and 40 percent of them take another path and the rest wait

### Requirement: One persistence roll per obstacle
A tip SHALL roll its persistence at most once for each hex it is due to enter. A tip whose roll fails SHALL give up on that hex: it SHALL wait without turning and without drawing further random numbers. Once that hex is empty it SHALL advance into it as decided before the wait. The next obstacle the tip meets after advancing SHALL get a new roll.

#### Scenario: Gives up and waits
- **WHEN** a tip's persistence roll fails and its next hex stays occupied for 20 iterations, while a side hex is empty
- **THEN** the tip stays where it is, heading the same way, and the board's random generator is not advanced on its behalf during those iterations

#### Scenario: Resumes after giving up
- **WHEN** the cell blocking a tip that gave up is cut away
- **THEN** the tip advances into the freed hex in its original direction on the next iteration

#### Scenario: Obstacle appears while waiting on a full board
- **WHEN** a tip waits because the board is full, and room is later made while its next hex is occupied
- **THEN** it rolls its persistence once at that point

#### Scenario: A fresh roll for each obstacle
- **WHEN** a tip that took another path around one obstacle later meets a second obstacle
- **THEN** it rolls its persistence again for the second obstacle

### Requirement: Growth continues after taking another path
Taking another path SHALL change only the direction of the hex the tip enters. It SHALL NOT be a growth decision of its own. The decision the tip made for that step, including any tips it sprouted and whether the tip ends after the hex, SHALL stand. From the new hex the tip's species SHALL decide its next step as usual, starting from the tip's new heading.

#### Scenario: Straight grower keeps its new direction
- **WHEN** a straight-growing tip with persistence 100 heading east takes another path to the south-east around an obstacle
- **THEN** it keeps growing south-east afterwards

#### Scenario: Last hex of a tip
- **WHEN** a tip that decided its next hex is its last takes another path
- **THEN** it enters the side hex and then ends, as it would have in its original direction
