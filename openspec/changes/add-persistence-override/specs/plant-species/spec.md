# Spec Delta

## MODIFIED Requirements

### Requirement: Preset persistence
Each species without settings SHALL have a fixed default persistence, which every one of its plants uses unless the plant was given its own persistence when planted. The values SHALL be: straight vine 0, fern 0, zigzag 30, spiral 30, burst 30, wanderer 60, and hydra 80.

#### Scenario: Plants that still stop
- **WHEN** a straight vine or a fern planted without its own persistence runs into an occupied hex
- **THEN** its tip waits and never takes another path

#### Scenario: Persistent hydra
- **WHEN** many hydras planted without their own persistence each meet one obstacle with both side hexes empty
- **THEN** between 70 and 90 percent of them take another path

#### Scenario: Scattered plants keep their species' persistence
- **WHEN** seeds are scattered without a persistence and grow into one another
- **THEN** each plant takes another path at its species' persistence
