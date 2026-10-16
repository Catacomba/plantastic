# Spec Delta

## ADDED Requirements

### Requirement: Game speed
A room SHALL have a game speed of 1x, 2x, 5x, 10x, or Max, starting at 1x. A player SHALL be able to set the speed at any time, whether the clock is running or paused. Setting it SHALL NOT pause, resume, or advance the board. The speed SHALL stay as set until it is changed, including across pausing and resuming and a full-board pause. Any other speed SHALL be rejected with an error and leave the room unchanged.

#### Scenario: Faster speed
- **WHEN** a player sets a running room with a 500 millisecond base interval to 5x
- **THEN** the room advances one iteration about every 100 milliseconds, and clients are told the speed is 5x

#### Scenario: Set while paused
- **WHEN** a player sets a paused room to 10x
- **THEN** the room stays paused at the same iteration, and when it is resumed it runs at 10x

#### Scenario: Invalid speed
- **WHEN** a player asks for a speed of 3x, 0, or a value that is not one of the allowed speeds
- **THEN** the command is rejected with an error and the speed is unchanged

### Requirement: Max speed waits for the client
At Max the room SHALL NOT wait a fixed interval between iterations. After sending the update for a clock iteration, it SHALL wait until its client acknowledges that it has drawn that iteration or a later one, and SHALL then advance the next iteration at once. Acknowledgements for earlier iterations SHALL NOT release the wait. While waiting, the room SHALL still handle every other command.

#### Scenario: Paced by the client
- **WHEN** a room runs at Max and its client acknowledges each update as soon as it has drawn it
- **THEN** the room sends exactly one update for each acknowledgement, and never more than one update is waiting for acknowledgement

#### Scenario: No acknowledgement
- **WHEN** a room runs at Max and its client stops acknowledging
- **THEN** the room advances no further iterations, and planting, cutting, and pausing still work

#### Scenario: Stale acknowledgement
- **WHEN** a room switches to Max and receives an acknowledgement for an iteration before the latest one it sent
- **THEN** it keeps waiting for the acknowledgement of the latest iteration

#### Scenario: Leaving Max
- **WHEN** a player switches a room from Max to 2x while it waits for an acknowledgement
- **THEN** the room stops waiting and continues at 2x

## MODIFIED Requirements

### Requirement: Clock
A room's clock SHALL be either running or paused. While running, the room SHALL advance its board one iteration at a time, paced by its game speed. While paused, the board SHALL NOT advance on its own. A sandbox room SHALL start running. Planting and cutting SHALL be permitted in both states and SHALL take effect immediately.

#### Scenario: Pause
- **WHEN** a player pauses a running room
- **THEN** the iteration count stops increasing and clients are told the clock is paused

#### Scenario: Resume
- **WHEN** a player resumes a paused room
- **THEN** iterations continue at the room's current game speed and clients are told the clock is running

#### Scenario: Cut while paused
- **WHEN** a player cuts a plant while the room is paused
- **THEN** the cut and the species' cut response appear immediately, and no iteration elapses

### Requirement: Updates report iteration cost
Every update that advances the board, whether from the clock or from growing for N iterations, SHALL carry the number of iterations advanced, the time the server spent computing them in milliseconds, and the number of tip visits they made. An update that advances nothing SHALL carry no iteration cost. The welcome and every update SHALL carry the room's game speed and the time available per iteration at that speed, which is the base interval divided by the speed, or none at Max. Measuring SHALL NOT affect the game: the board after any sequence of commands SHALL be the same as it would be without it.

#### Scenario: Clock tick
- **WHEN** a running room advances one iteration
- **THEN** the update reports 1 iteration, a compute time of zero or more milliseconds, and that iteration's tip visits

#### Scenario: Grow for N
- **WHEN** a player in a paused room grows for 25 iterations
- **THEN** the update reports 25 iterations, the total compute time for all of them, and the sum of their tip visits

#### Scenario: Update without growth
- **WHEN** a player plants a seed, cuts, slices, pauses, resumes, or sets the speed
- **THEN** the update carries no iteration cost

#### Scenario: Time available per iteration
- **WHEN** a client connects to a server running at two iterations per second at 1x
- **THEN** the welcome reports 1x and 500 milliseconds available per iteration

#### Scenario: Time available follows the speed
- **WHEN** a player sets that room to 10x, and then to Max
- **THEN** the first update reports 10x and 50 milliseconds, and the second reports Max and no time available

#### Scenario: Measuring does not change the game
- **WHEN** two rooms with the same random seed receive the same commands
- **THEN** their boards are identical after every command, whatever compute times were measured and whatever speeds were set
