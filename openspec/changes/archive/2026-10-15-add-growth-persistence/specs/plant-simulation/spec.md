# Spec Delta

## ADDED Requirements

### Requirement: Blocked tips may take another path
Each plant SHALL have a persistence, a whole percentage from 0 to 100, fixed when it is planted. When a tip's next hex is occupied by any cell, including one of its own plant, and the board is not full, the tip SHALL roll its persistence once. If the roll succeeds and the hex 60 degrees to the left or right of its heading is empty, the tip SHALL turn into one such hex and advance into it at once, choosing at random when both are empty.

#### Scenario: Persistence of zero
- **WHEN** a tip of a plant with persistence 0 finds its next hex occupied
- **THEN** it waits without turning, exactly as a blocked tip did before persistence existed

#### Scenario: Persistence of one hundred
- **WHEN** a tip of a plant with persistence 100 heading east finds its next hex occupied, with the north-east hex occupied and the south-east hex empty
- **THEN** the tip turns south-east and enters that hex in the same iteration

#### Scenario: Both sides empty
- **WHEN** tips of plants with persistence 100 are blocked many times with both side hexes empty
- **THEN** each detour goes 60 degrees left or right, and both sides occur

#### Scenario: Blocked by its own plant
- **WHEN** a tip of a plant with persistence 100 runs into one of its own plant's cells and a side hex is empty
- **THEN** it takes another path just as it would around another plant

#### Scenario: No empty side
- **WHEN** a blocked tip's forward-left and forward-right hexes are both occupied
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

## MODIFIED Requirements

### Requirement: Blocked tips wait
A tip whose next hex is occupied, and that does not take another path around it, SHALL NOT advance and SHALL NOT turn. It SHALL remain a tip, and SHALL advance on a later iteration once that hex is empty. While blocked, a tip SHALL NOT bank more than one hex of progress.

#### Scenario: Tip runs into another plant
- **WHEN** a tip of a plant with persistence 0 finds its next hex occupied by any cell
- **THEN** the tip stays where it is for as long as that hex is occupied

#### Scenario: Obstacle is removed
- **WHEN** the cell blocking a waiting tip is removed by a cut
- **THEN** the tip advances into the freed hex on the next iteration and continues at its normal speed, without a burst of catch-up growth

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
