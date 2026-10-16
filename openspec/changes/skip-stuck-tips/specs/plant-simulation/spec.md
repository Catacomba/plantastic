# Spec Delta

## ADDED Requirements

### Requirement: Stuck tips sleep
While skipping stuck tips is on, which it is unless switched off, a tip that waits because its next hex is occupied SHALL fall asleep once it has lost its persistence roll for that hex or has no empty hex 60 or 120 degrees to either side. A sleeping tip SHALL gain no progress and SHALL not be visited. A tip waiting only because the board is full SHALL stay awake.

#### Scenario: Stuck tip falls asleep
- **WHEN** a straight vine with persistence 0 runs into another plant and the board advances
- **THEN** its tip is asleep, still a tip, still reported as blocked, and later iterations report no visits for it

#### Scenario: Full board keeps tips awake
- **WHEN** a tip waits only because the board is full
- **THEN** it stays awake and is visited every iteration

#### Scenario: Switched off
- **WHEN** skipping stuck tips is off
- **THEN** no tip sleeps, and every waiting tip is visited every iteration as before

### Requirement: Sleeping tips wake when room appears
A sleeping tip SHALL wake when the hex it is waiting to enter is emptied. A sleeping tip that has not lost its persistence roll for that hex SHALL also wake when one of its 60- or 120-degree turn hexes is emptied. Every sleeping tip SHALL wake when skipping stuck tips is switched off. A woken tip SHALL carry on exactly as a tip that had waited awake, with its decision and progress kept.

#### Scenario: Obstacle cut away
- **WHEN** the cell in front of a sleeping tip is cut away
- **THEN** the tip wakes and advances into the freed hex on the next iteration, without a burst of catch-up growth

#### Scenario: Turn hex freed
- **WHEN** a sleeping tip with persistence 100 had no free turn, and a cell at one of its turn hexes is cut away
- **THEN** the tip wakes, rolls its persistence on the next iteration, and turns into the freed hex

#### Scenario: Unrelated cut
- **WHEN** a cell that is neither ahead of a sleeping tip nor at one of its turn hexes is removed
- **THEN** the tip stays asleep

#### Scenario: Sleeping tip cut away
- **WHEN** the cell a sleeping tip sits on is removed by a cut or a clear
- **THEN** the tip is gone, like any other tip on a removed cell

### Requirement: Skipping stuck tips does not change the game
Skipping stuck tips SHALL NOT change any cell, tip, plant, or random number drawn. Two boards with the same random seed receiving the same actions SHALL be identical after every iteration, whether skipping is on, off, or switched part way through, apart from the reported tip visits.

#### Scenario: Same board on and off
- **WHEN** two boards with the same random seed, one skipping stuck tips and one not, receive the same plantings, scatters, cuts, and slices over many iterations
- **THEN** their cells, tips, and plants are identical after every iteration, and the skipping board reports no more tip visits than the other

#### Scenario: Switched part way
- **WHEN** skipping is switched on and off several times during a session
- **THEN** the board is identical after every iteration to one where it was never switched

## MODIFIED Requirements

### Requirement: Iterations report their work
Each iteration SHALL report the number of tip visits it made, where a tip visit is one attempt to move a tip that was due to advance, whether or not the tip then moved. Sleeping tips SHALL NOT be visited. The count SHALL depend only on the state of the board, so that two boards in the same state report the same count, and counting SHALL NOT change the outcome of the iteration.

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
- **WHEN** a board whose only tip is blocked, with skipping stuck tips off, advances one iteration
- **THEN** the iteration reports 1 tip visit, although nothing moved

#### Scenario: Sleeping tip does not count
- **WHEN** a board whose only tip has fallen asleep advances one iteration
- **THEN** the iteration reports 0 tip visits

#### Scenario: Same board, same count
- **WHEN** two boards with the same random seed receive the same actions
- **THEN** they report the same number of tip visits for every iteration

#### Scenario: Several iterations together
- **WHEN** several iterations are advanced as one batch
- **THEN** the reported tip visits are the sum of the visits of each iteration
