# Spec Delta

## MODIFIED Requirements

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

## ADDED Requirements

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
A tip SHALL make its growth decision once for each hex it enters. A tip that cannot advance, because its next hex is occupied or because the board is full, SHALL keep the decision it made and SHALL NOT decide again, draw further random numbers, or sprout further tips until it has advanced.

#### Scenario: Blocked after deciding to turn
- **WHEN** a tip decides to turn and finds the hex in its new direction occupied
- **THEN** it waits heading in that direction, and advances that way once the hex is empty

#### Scenario: Board full
- **WHEN** a tip of a species that branches at random cannot advance for 20 iterations because the board is full
- **THEN** it has sprouted nothing and changed nothing during those iterations, and when room is made it advances as it had decided before the wait

#### Scenario: Waiting does not disturb replay
- **WHEN** two boards with the same random seed receive the same actions, including a period in which tips are blocked
- **THEN** the boards are identical after every iteration
