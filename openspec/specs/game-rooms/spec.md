# game-rooms Specification

## Purpose

Defines how players reach a running game on the server: rooms that own boards and a clock, the commands players may send in each room mode, and how the board state is kept in sync with every connected client.

## Requirements

### Requirement: Server-authoritative rooms
The server SHALL host games in rooms. Each room SHALL own its board, its clock, its random seed, and its players, and SHALL be the only authority over that state. Clients SHALL change the game only by sending commands, and the server SHALL validate every command before applying it.

#### Scenario: Invalid command
- **WHEN** a client sends a command that is malformed, unknown, or fails validation
- **THEN** the server leaves the game unchanged and replies to that client with an error that identifies the reason

#### Scenario: Rooms are isolated
- **WHEN** two rooms exist at the same time
- **THEN** commands and growth in one room have no effect on the other

### Requirement: Joining a sandbox room
When a client connects, the server SHALL create a new sandbox room with that client as its only player and SHALL send the client the room's mode, the species catalog with each species' settings description, the clock state, and a complete snapshot of the board including the details of every plant on it. The room SHALL be discarded when its player disconnects.

#### Scenario: First connection
- **WHEN** a client connects
- **THEN** it receives a welcome containing the sandbox mode, the species catalog, the clock state, and an empty board

#### Scenario: Disconnect
- **WHEN** the player of a sandbox room disconnects
- **THEN** the room and its board no longer exist on the server

#### Scenario: Catalog describes settings
- **WHEN** a client connects
- **THEN** the catalog in the welcome lists eight species, and the custom species carries a description of each of its settings

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

### Requirement: Planting with settings
The plant command SHALL accept settings for the seed. The room SHALL pass them to the board with the species and speed, and SHALL reject the command with an error that identifies the problem when the settings are missing for a species that needs them, given for a species that has none, out of range, or inconsistent. A rejected command SHALL leave the board unchanged.

#### Scenario: Custom seed
- **WHEN** a player plants a custom seed with valid settings
- **THEN** the plant is created and clients are told its settings

#### Scenario: Invalid settings
- **WHEN** a player plants a custom seed with a branch chance of 150
- **THEN** the player receives an error saying the settings are invalid, and no plant is created

#### Scenario: Seed without settings still works
- **WHEN** a player plants a straight vine with no settings
- **THEN** the plant is created as before

### Requirement: Plant details are synchronized
The server SHALL tell every client in a room the identifier, species, speed, and settings of each plant on the board: all of them when the client joins, and each new plant in the update that reports its planting.

#### Scenario: New plant
- **WHEN** a seed is planted
- **THEN** the update that adds its root also carries the plant's identifier, species, speed, and settings

#### Scenario: Details match the server
- **WHEN** a client has applied the welcome and every update since
- **THEN** it knows the species, speed, and settings of every plant that has a cell on its board

### Requirement: Slice command
A player SHALL be able to send an ordered list of hexes to be cut along a path, between 1 and a maximum number of hexes, in a single command. The room SHALL apply the path to its board immediately, in both clock states, and SHALL send its clients one update containing every resulting change. A path that cuts nothing SHALL NOT produce an error.

#### Scenario: Slice while running
- **WHEN** a player slices across two vines while the clock is running
- **THEN** every client receives one update with both stumps, the removed hexes, and the new tips, and the clock is still running

#### Scenario: Slice while paused
- **WHEN** a player slices while the clock is paused
- **THEN** the cuts appear immediately, the iteration number does not change, and the clock is still paused

#### Scenario: Nothing to cut
- **WHEN** a player slices along a path of empty hexes
- **THEN** the board is unchanged and the player receives no error

#### Scenario: Several slices while paused
- **WHEN** a player sends several slice commands one after another while the clock is paused
- **THEN** all of their cuts take effect on the same iteration

#### Scenario: Invalid slice
- **WHEN** a player sends a slice with no hexes, with more hexes than the maximum, or with a hex that is not a pair of whole-number coordinates
- **THEN** the command is rejected with an error and the board is unchanged

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

### Requirement: Clock
A room's clock SHALL be either running or paused. While running, the room SHALL advance its board by one iteration at a fixed interval. While paused, the board SHALL NOT advance on its own. A sandbox room SHALL start running. Planting and cutting SHALL be permitted in both states and SHALL take effect immediately.

#### Scenario: Pause
- **WHEN** a player pauses a running room
- **THEN** the iteration count stops increasing and clients are told the clock is paused

#### Scenario: Resume
- **WHEN** a player resumes a paused room
- **THEN** iterations continue at the fixed interval and clients are told the clock is running

#### Scenario: Cut while paused
- **WHEN** a player cuts a plant while the room is paused
- **THEN** the cut and the species' cut response appear immediately, and no iteration elapses

### Requirement: Grow for N iterations
While a room is paused, a player SHALL be able to advance the board by a chosen whole number of iterations, between 1 and a maximum, in a single command. The room SHALL remain paused afterward.

#### Scenario: Step while paused
- **WHEN** a player in a paused room at iteration 10 asks to grow for 25 iterations
- **THEN** the board is at iteration 35, reflects exactly 25 iterations of growth, and the clock is still paused

#### Scenario: Step while running
- **WHEN** a player asks to grow for N iterations while the clock is running
- **THEN** the command is rejected with an error

#### Scenario: Step count out of range
- **WHEN** a player asks to grow for zero, a negative number, a fractional number, or more than the maximum number of iterations
- **THEN** the command is rejected with an error and the board does not advance

### Requirement: State synchronization
The server SHALL keep every client in a room up to date. After each iteration and after each applied command, it SHALL send the changes to the board, the current iteration number, and the progress of growing tips, so that a client applying those changes in order holds the same board as the server.

#### Scenario: Growth is pushed
- **WHEN** an iteration adds cells to the board
- **THEN** every client in the room receives the added cells with their hex, plant, and kind, along with the new iteration number

#### Scenario: Cut is pushed
- **WHEN** a cut is applied
- **THEN** every client in the room receives the new stump, the removed hexes, and any new tips

#### Scenario: Client matches server
- **WHEN** a client has applied the welcome snapshot and every update sent since
- **THEN** its board is identical to the server's board

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

### Requirement: Full board pauses the room
When a room's board reaches its maximum size, the room SHALL pause its clock and SHALL tell its clients that the board is full.

#### Scenario: Board fills while running
- **WHEN** a running room's board reaches its maximum size
- **THEN** the clock becomes paused and clients receive a notice that the board is full
