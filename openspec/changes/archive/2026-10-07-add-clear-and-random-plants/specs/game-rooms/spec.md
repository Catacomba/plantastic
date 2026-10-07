# Spec Delta

## MODIFIED Requirements

### Requirement: Room mode decides permitted commands
Every room SHALL have a mode, and the mode SHALL decide which commands its players may use. The sandbox mode SHALL permit planting seeds of any species at any valid speed, cutting any plant regardless of owner, slicing along a path through any plants regardless of owner, clearing the board, scattering random seeds, pausing, resuming, and stepping. A command the mode does not permit SHALL be rejected with an error.

#### Scenario: Sandbox player cuts any plant
- **WHEN** the player of a sandbox room cuts a living cell of any plant on the board
- **THEN** the cut is applied

#### Scenario: Sandbox player slices any plants
- **WHEN** the player of a sandbox room slices along a path that crosses living cells of several plants
- **THEN** every one of those cells is cut

#### Scenario: Mode that forbids slicing
- **WHEN** a player slices in a room whose mode does not permit slicing
- **THEN** the command is rejected with an error and the board is unchanged

#### Scenario: Sandbox player clears and scatters
- **WHEN** the player of a sandbox room clears the board and then scatters seeds
- **THEN** both commands are applied

#### Scenario: Mode that forbids clearing or scattering
- **WHEN** a player clears the board or scatters seeds in a room whose mode does not permit it
- **THEN** the command is rejected with an error and the board is unchanged

## ADDED Requirements

### Requirement: Clear command
A player SHALL be able to clear the room's board with a single command, in both clock states. The room SHALL leave its clock state and iteration number unchanged, and SHALL send its clients one update that says the board was cleared, without listing the emptied hexes. A client applying that update SHALL hold an empty board with no plant details.

#### Scenario: Clear while running
- **WHEN** a player clears the board of a running room
- **THEN** every client receives one update marked as cleared, the clock is still running, and iterations continue on the empty board

#### Scenario: Clear while paused
- **WHEN** a player clears the board of a paused room at iteration 40
- **THEN** the update is marked as cleared, the clock is still paused, and the iteration number is still 40

#### Scenario: Update is small
- **WHEN** a board holding thousands of cells is cleared
- **THEN** the update does not list those cells

#### Scenario: Client matches server after a clear
- **WHEN** a client applies a cleared update and every update after it
- **THEN** its board and plant details are identical to the server's

### Requirement: Scatter command
A player SHALL be able to scatter a number of random seeds, from 1 to a maximum, within a region given as a center hex and the region's half-width and half-height in hexes, in both clock states. The room SHALL plant them as the simulation defines, with the player as owner, and SHALL send its clients one update carrying every new plant, its details, and the numbers of seeds asked for and planted. Planting fewer than asked for, or none, SHALL NOT be an error. A count or region out of range SHALL be rejected with an error and leave the board unchanged.

#### Scenario: Scatter
- **WHEN** a player scatters 10 seeds in a region with plenty of room
- **THEN** every client receives one update with 10 new roots, the details of 10 new plants, and the report that 10 were asked for and 10 planted

#### Scenario: Seeds stay inside the region
- **WHEN** a player scatters seeds in a region with a given center, half-width, and half-height
- **THEN** every new root lies no more than half-height rows from the center's row and no more than half-width hex widths to either side of the center

#### Scenario: Fewer than asked for
- **WHEN** a player scatters more seeds than the region has empty hexes
- **THEN** the update carries as many new plants as fit, reports both the number asked for and the smaller number planted, and the player receives no error

#### Scenario: Invalid scatter
- **WHEN** a player scatters zero seeds, more than the maximum, a fractional number, or gives a region larger than allowed
- **THEN** the command is rejected with an error and the board is unchanged

#### Scenario: Scatter while paused
- **WHEN** a player scatters seeds in a paused room
- **THEN** the seeds appear at once, no iteration elapses, and the clock is still paused
