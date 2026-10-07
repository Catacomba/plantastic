# Spec Delta

## MODIFIED Requirements

### Requirement: Seed tool
The client SHALL provide a seed tool with a species picker filled from the server's catalog and a speed field that starts at the chosen species' default speed. With the seed tool selected, pressing the left mouse button on a hex SHALL ask the server to plant a seed of that species and speed there, with the settings currently shown when the species has settings. Dragging with the seed tool SHALL NOT plant further seeds.

#### Scenario: Plant a seed
- **WHEN** the player selects the seed tool and clicks an empty hex
- **THEN** a seed appears in that hex and begins growing in a direction the player did not choose

#### Scenario: Custom speed
- **WHEN** the player sets the speed field to 0.25 and plants a seed
- **THEN** the resulting plant gains one hex every 4 iterations

#### Scenario: Drag with the seed tool
- **WHEN** the player presses the left button on an empty hex with the seed tool and drags across other hexes before releasing
- **THEN** exactly one seed is planted, in the hex where the press began

#### Scenario: Every species can be planted
- **WHEN** the player opens the species picker
- **THEN** it offers all eight species, and a seed of each one can be planted and grows

## ADDED Requirements

### Requirement: Species settings panel
When the species chosen in the seed tool has settings, the client SHALL show a control for each one, built from the catalog's description and starting at its default: a number control for percentages and counts, an option of never for a setting that allows it, and a list for a choice. The panel SHALL be hidden for a species without settings. The values SHALL be kept while the player switches tools or species during a visit.

#### Scenario: Custom species selected
- **WHEN** the player selects the custom species
- **THEN** controls appear for branch chance, branches minimum and maximum, calm minimum and maximum, turn chance, and cut response, each showing its default

#### Scenario: Species without settings
- **WHEN** the player selects the straight vine
- **THEN** no settings controls are shown

#### Scenario: Values are kept
- **WHEN** the player changes the branch chance, selects another species, and selects the custom species again
- **THEN** the branch chance shows the changed value

### Requirement: Settings apply only to new seeds
Changing a setting SHALL affect only seeds planted afterwards. The client SHALL offer no way to change the species, speed, or settings of a plant that has been planted.

#### Scenario: Change after planting
- **WHEN** the player plants a custom seed, raises the branch chance, and plants a second custom seed
- **THEN** the first plant keeps growing by the settings it was planted with and the second grows by the new ones

#### Scenario: Rejected settings
- **WHEN** the player plants a custom seed with branches minimum above maximum
- **THEN** no seed appears and a brief message says what is wrong with the settings

### Requirement: Plant details on hover
While the cursor rests on a hex that holds a plant cell, the client SHALL show that plant's species name, speed, and settings. The details SHALL disappear when the cursor is over an empty hex or leaves the board.

#### Scenario: Compare two custom plants
- **WHEN** the player points at each of two custom plants planted with different settings
- **THEN** each shows its own settings

#### Scenario: Plant without settings
- **WHEN** the player points at a straight vine
- **THEN** its species name and speed are shown, with no settings

#### Scenario: Empty hex
- **WHEN** the player points at an empty hex
- **THEN** no plant details are shown
