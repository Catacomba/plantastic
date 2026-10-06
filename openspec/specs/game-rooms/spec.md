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
When a client connects, the server SHALL create a new sandbox room with that client as its only player and SHALL send the client the room's mode, the species catalog, the clock state, and a complete snapshot of the board. The room SHALL be discarded when its player disconnects.

#### Scenario: First connection
- **WHEN** a client connects
- **THEN** it receives a welcome containing the sandbox mode, the species catalog, the clock state, and an empty board

#### Scenario: Disconnect
- **WHEN** the player of a sandbox room disconnects
- **THEN** the room and its board no longer exist on the server

### Requirement: Room mode decides permitted commands
Every room SHALL have a mode, and the mode SHALL decide which commands its players may use. The sandbox mode SHALL permit planting seeds of any species at any valid speed, cutting any plant regardless of owner, pausing, resuming, and stepping. A command the mode does not permit SHALL be rejected with an error.

#### Scenario: Sandbox player cuts any plant
- **WHEN** the player of a sandbox room cuts a living cell of any plant on the board
- **THEN** the cut is applied

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

### Requirement: Full board pauses the room
When a room's board reaches its maximum size, the room SHALL pause its clock and SHALL tell its clients that the board is full.

#### Scenario: Board fills while running
- **WHEN** a running room's board reaches its maximum size
- **THEN** the clock becomes paused and clients receive a notice that the board is full
