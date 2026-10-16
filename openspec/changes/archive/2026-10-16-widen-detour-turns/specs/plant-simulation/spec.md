# Spec Delta

## MODIFIED Requirements

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
