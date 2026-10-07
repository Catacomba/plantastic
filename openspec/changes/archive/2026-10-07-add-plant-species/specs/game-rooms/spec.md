# Spec Delta

## MODIFIED Requirements

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

## ADDED Requirements

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
