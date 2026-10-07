# Spec Delta

## ADDED Requirements

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
