# Spec Delta

## MODIFIED Requirements

### Requirement: Room mode decides permitted commands
Every room SHALL have a mode, and the mode SHALL decide which commands its players may use. The sandbox mode SHALL permit planting seeds of any species at any valid speed, cutting any plant regardless of owner, slicing along a path through any plants regardless of owner, pausing, resuming, and stepping. A command the mode does not permit SHALL be rejected with an error.

#### Scenario: Sandbox player cuts any plant
- **WHEN** the player of a sandbox room cuts a living cell of any plant on the board
- **THEN** the cut is applied

#### Scenario: Sandbox player slices any plants
- **WHEN** the player of a sandbox room slices along a path that crosses living cells of several plants
- **THEN** every one of those cells is cut

#### Scenario: Mode that forbids slicing
- **WHEN** a player slices in a room whose mode does not permit slicing
- **THEN** the command is rejected with an error and the board is unchanged

## ADDED Requirements

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
