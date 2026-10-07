# Spec Delta

## ADDED Requirements

### Requirement: Clear board button
The client SHALL provide a Clear button that asks the server to remove every plant from the board, without asking for confirmation. The button SHALL be set apart from the clock controls so that it is not pressed by mistake, and SHALL be unusable while disconnected. After a clear the board SHALL show no plants, the cell count SHALL read zero, and the plant details readout SHALL be empty.

#### Scenario: Clear
- **WHEN** the player presses Clear on a board with several plants
- **THEN** every plant disappears, the cell count reads zero, and the iteration counter keeps its value

#### Scenario: Clear while running
- **WHEN** the player presses Clear while the game is running
- **THEN** the board empties and the game keeps running

#### Scenario: Tools after a clear
- **WHEN** the player clears the board and then uses the seed tool or a cutting tool
- **THEN** the tool works as usual on the empty board and shows no error

#### Scenario: Disconnected
- **WHEN** the connection to the server is lost
- **THEN** the Clear button is disabled

### Requirement: Random plants control
The client SHALL provide a number field and a button that ask the server to scatter that many random seeds within the area of the board the player can currently see, excluding the parts covered by the top bar and the tool bar. The field SHALL accept whole numbers from 1 to the server's maximum and SHALL start at 10. The control SHALL be unusable while disconnected.

#### Scenario: Plant random plants
- **WHEN** the player enters 10 and presses the button on an empty board
- **THEN** 10 plants of various species appear at different places within the visible board, and none of them is a custom plant

#### Scenario: Within view
- **WHEN** the player scatters plants
- **THEN** every new root is visible on screen without panning, and none is hidden beneath the top bar or the tool bar

#### Scenario: Zoomed out
- **WHEN** the player lowers the hex size and scatters plants again
- **THEN** the new plants are spread over the larger area now in view

#### Scenario: Invalid count
- **WHEN** the player enters zero, a fraction, nothing, or a number above the maximum and presses the button
- **THEN** nothing is planted and a brief message states the allowed range

#### Scenario: Works while paused
- **WHEN** the player scatters plants while the game is paused
- **THEN** the seeds appear at once and do not grow until the game runs

### Requirement: Feedback when fewer plants fit
When a scatter plants fewer seeds than the player asked for, the client SHALL say how many were planted and how many were asked for. When it plants all of them, the client SHALL show no message.

#### Scenario: Some fit
- **WHEN** the player asks for 50 random plants and only 12 are planted
- **THEN** a brief message says that 12 of 50 were planted because the visible area ran out of empty space

#### Scenario: None fit
- **WHEN** the player asks for random plants and none can be planted
- **THEN** a brief message says there is no empty space in view

#### Scenario: All fit
- **WHEN** every requested plant is planted
- **THEN** no message is shown
