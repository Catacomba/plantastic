# Spec Delta

## ADDED Requirements

### Requirement: Persistence chosen at planting
A seed MAY be planted with a persistence, a whole percentage from 0 to 100, which the plant SHALL use instead of its species' default. Without one, the plant SHALL take its species' default: the fixed value of a species without settings, or the persistence setting of a custom plant. A persistence outside 0 to 100, or not a whole number, SHALL make the planting fail.

#### Scenario: Override on a preset
- **WHEN** a straight vine is planted with persistence 100 and its tip runs into an occupied hex with an empty side
- **THEN** the tip takes another path, although the straight vine's default is 0

#### Scenario: Override on a custom plant
- **WHEN** a custom seed with a persistence setting of 0 is planted with persistence 100
- **THEN** the plant's persistence is 100 and its settings still read 0

#### Scenario: No override
- **WHEN** a hydra is planted without a persistence
- **THEN** its persistence is 80

#### Scenario: Invalid persistence
- **WHEN** a seed is planted with a persistence of 101, of -1, or of 50.5
- **THEN** the planting is rejected and the board is unchanged

## MODIFIED Requirements

### Requirement: Planting a seed
The simulation SHALL allow a seed of a chosen species and speed to be planted in an empty hex, together with settings when the species has them and optionally a persistence. Planting SHALL create a new plant consisting of a root cell in that hex and one growing tip at the root. The tip's starting direction SHALL be chosen at random from the six directions unless a direction is given. Each plant SHALL record the player who owns it. A plant's species, speed, settings, and persistence SHALL be fixed when it is planted and SHALL never change afterwards.

#### Scenario: Seed in an empty hex
- **WHEN** a seed is planted in an empty hex without a direction
- **THEN** a new plant exists with a root in that hex, one tip heading in one of the six directions, and the planting player as its owner

#### Scenario: Seed in an occupied hex
- **WHEN** a seed is planted in a hex that is already occupied
- **THEN** the planting is rejected and the board is unchanged

#### Scenario: Seed with settings
- **WHEN** a seed of a species that has settings is planted with valid settings
- **THEN** the new plant holds exactly those settings

#### Scenario: Settings for a species without any
- **WHEN** a seed of a species that has no settings is planted with settings
- **THEN** the planting is rejected and the board is unchanged

#### Scenario: Later seeds do not affect earlier plants
- **WHEN** two seeds of the same species are planted with different settings or persistence, one after the other
- **THEN** each plant grows by its own settings and persistence for as long as it exists

### Requirement: Scattering random seeds
The simulation SHALL allow a number of seeds to be planted at once at random empty hexes inside a given region, optionally with one persistence for all of them. Each seed's species SHALL be drawn at random, independently of the others, from the species that take no settings, and each seed SHALL use its species' default speed, a random starting direction, and the given persistence or else its species' default. No two seeds SHALL share a hex, and no seed SHALL be placed on an occupied hex or outside the region. Each seed SHALL record the player who scattered it as its owner.

#### Scenario: Scatter on an empty region
- **WHEN** 20 seeds are scattered in a region of several hundred empty hexes
- **THEN** 20 new plants exist, each on a different hex inside the region, each with one tip and its species' default speed

#### Scenario: Species are drawn from those without settings
- **WHEN** many seeds are scattered
- **THEN** every one is of a species that takes no settings, none is a custom plant, and every such species appears among them

#### Scenario: The mix is not balanced
- **WHEN** 7 seeds are scattered many times over
- **THEN** some of those scatters contain the same species more than once

#### Scenario: Occupied hexes are avoided
- **WHEN** seeds are scattered in a region where some hexes are occupied
- **THEN** every new seed is on a hex that was empty, and no existing cell is changed

#### Scenario: Scattered plants grow like any other
- **WHEN** seeds are scattered and the board advances
- **THEN** each plant grows by its species' rules

#### Scenario: Scatter with a persistence
- **WHEN** 20 seeds are scattered with persistence 70
- **THEN** every new plant's persistence is 70, whatever its species

#### Scenario: Scatter without a persistence
- **WHEN** seeds are scattered without a persistence
- **THEN** each new plant's persistence is its species' default
