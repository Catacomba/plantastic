# Spec Delta

## ADDED Requirements

### Requirement: Skip stuck tips setting
A room SHALL skip stuck tips from the start. A player SHALL be able to switch skipping on or off at any time, in either clock state, without advancing the board. The welcome and every update SHALL say whether skipping is on.

#### Scenario: Default
- **WHEN** a client joins a new room
- **THEN** the welcome says skipping stuck tips is on

#### Scenario: Switch off
- **WHEN** a player switches skipping off while some tips are asleep
- **THEN** the update says skipping is off, every sleeping tip is woken and listed among the awake tips, and the iteration number is unchanged

## MODIFIED Requirements

### Requirement: State synchronization
The server SHALL keep every client in a room up to date. After each iteration and after each applied command, it SHALL send the changes to the board, the current iteration number, and every awake tip. A tip that falls asleep SHALL be sent once, in the update in which it falls asleep, and the update in which it wakes or is removed SHALL say so. The welcome SHALL list the sleeping tips. A client applying the welcome and every update in order SHALL hold the same board and tips as the server.

#### Scenario: Growth is pushed
- **WHEN** an iteration adds cells to the board
- **THEN** every client in the room receives the added cells with their hex, plant, and kind, along with the new iteration number

#### Scenario: Cut is pushed
- **WHEN** a cut is applied
- **THEN** every client in the room receives the new stump, the removed hexes, and any new tips

#### Scenario: Client matches server
- **WHEN** a client has applied the welcome snapshot and every update sent since
- **THEN** its board is identical to the server's board, and its awake and sleeping tips together are identical to the server's tips

#### Scenario: Sleeping tips are not resent
- **WHEN** a tip has fallen asleep and the board advances many iterations
- **THEN** the update in which it fell asleep carries it once, and later updates do not list it until it wakes or is removed

#### Scenario: Waking is pushed
- **WHEN** a cut wakes a sleeping tip
- **THEN** the update says the tip is no longer asleep and lists it among the awake tips
