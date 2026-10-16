# Spec Delta

## ADDED Requirements

### Requirement: Persistence in plant and scatter commands
The plant and scatter commands SHALL accept an optional persistence, a whole number from 0 to 100, and the room SHALL pass it to the board. A command that leaves it out, or gives none, SHALL plant with each species' default. A persistence out of range SHALL be rejected with an error naming persistence, and a value that is not a whole number SHALL be rejected as an invalid message. Either way the board SHALL stay unchanged.

#### Scenario: Plant with a persistence
- **WHEN** a player plants a straight vine with persistence 90
- **THEN** the plant is created, and clients are told its persistence is 90

#### Scenario: Scatter with a persistence
- **WHEN** a player scatters 10 seeds with persistence 40
- **THEN** every client receives the details of 10 new plants, each with persistence 40

#### Scenario: Out of range
- **WHEN** a player plants or scatters with persistence 150
- **THEN** the player receives an error saying the persistence is invalid, and nothing is planted

## MODIFIED Requirements

### Requirement: Plant details are synchronized
The server SHALL tell every client in a room the identifier, species, speed, settings, and persistence of each plant on the board: all of them when the client joins, and each new plant in the update that reports its planting.

#### Scenario: New plant
- **WHEN** a seed is planted
- **THEN** the update that adds its root also carries the plant's identifier, species, speed, settings, and persistence

#### Scenario: Details match the server
- **WHEN** a client has applied the welcome and every update since
- **THEN** it knows the species, speed, settings, and persistence of every plant that has a cell on its board
