# Spec Delta

## ADDED Requirements

### Requirement: Persistence control
The tool bar SHALL offer a persistence field, a whole percentage from 0 to 100 that starts at 50, and an override checkbox that starts unticked, next to the seed speed field. While the box is ticked, every seed the player plants and every seed scattered by the random plants control SHALL be sent with the field's persistence. While it is unticked, seeds SHALL be sent without one, so each plant takes its species' default. The field SHALL be editable only while the box is ticked.

#### Scenario: Override ticked
- **WHEN** the player ticks override, sets 100, and plants a straight vine
- **THEN** the vine's persistence is 100 and its tips go around obstacles instead of stopping

#### Scenario: Override unticked
- **WHEN** the player leaves override unticked and plants a hydra
- **THEN** the hydra's persistence is 80

#### Scenario: Random plants follow the control
- **WHEN** the player ticks override with 20 and scatters 10 random plants
- **THEN** each of the 10 plants has persistence 20

#### Scenario: Custom plant
- **WHEN** override is ticked with 70 and the player plants a custom seed whose persistence setting is 10
- **THEN** the plant's persistence is 70

#### Scenario: Out of range
- **WHEN** override is ticked, the field holds 150, and the player plants a seed
- **THEN** no seed appears and a brief message states the allowed range

## MODIFIED Requirements

### Requirement: Plant details on hover
While the cursor rests on a hex that holds a plant cell, the client SHALL show that plant's species name, speed, persistence, and settings. The persistence shown SHALL be the plant's own, and SHALL appear once, in place of a custom plant's persistence setting. The details SHALL disappear when the cursor is over an empty hex or leaves the board.

#### Scenario: Compare two custom plants
- **WHEN** the player points at each of two custom plants planted with different settings
- **THEN** each shows its own settings

#### Scenario: Plant without settings
- **WHEN** the player points at a straight vine
- **THEN** its species name, speed, and persistence are shown, with no settings

#### Scenario: Overridden persistence
- **WHEN** the player points at a hydra that was planted with persistence 20
- **THEN** the details show persistence 20, not the hydra's default of 80

#### Scenario: Empty hex
- **WHEN** the player points at an empty hex
- **THEN** no plant details are shown
