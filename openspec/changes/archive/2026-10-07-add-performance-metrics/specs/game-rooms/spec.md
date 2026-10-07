# Spec Delta

## ADDED Requirements

### Requirement: Updates report iteration cost
Every update that advances the board, whether from the clock or from growing for N iterations, SHALL carry the number of iterations advanced, the time the server spent computing them in milliseconds, and the number of tip visits they made. An update that advances nothing SHALL carry no iteration cost. The welcome SHALL carry the time available per iteration while the clock runs. Measuring SHALL NOT affect the game: the board after any sequence of commands SHALL be the same as it would be without it.

#### Scenario: Clock tick
- **WHEN** a running room advances one iteration
- **THEN** the update reports 1 iteration, a compute time of zero or more milliseconds, and that iteration's tip visits

#### Scenario: Grow for N
- **WHEN** a player in a paused room grows for 25 iterations
- **THEN** the update reports 25 iterations, the total compute time for all of them, and the sum of their tip visits

#### Scenario: Update without growth
- **WHEN** a player plants a seed, cuts, slices, pauses, or resumes
- **THEN** the update carries no iteration cost

#### Scenario: Time available per iteration
- **WHEN** a client connects to a server running at two iterations per second
- **THEN** the welcome reports 500 milliseconds available per iteration

#### Scenario: Measuring does not change the game
- **WHEN** two rooms with the same random seed receive the same commands
- **THEN** their boards are identical after every command, whatever compute times were measured
