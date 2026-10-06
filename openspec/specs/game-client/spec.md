# game-client Specification

## Purpose

Defines what a player sees and does in the browser: the rendered hex board, moving around it, the tools for planting and cutting, and the controls for the clock.

## Requirements

### Requirement: Board rendering
The client SHALL draw the board as a hexagonal grid seen from above, showing the grid lines of the visible area and every plant cell in view. Roots, vine segments, stumps, and growing tips SHALL be visually distinguishable from one another. The client SHALL draw only what the server has reported.

#### Scenario: Plant appears as it grows
- **WHEN** the server reports new cells for a plant
- **THEN** those cells appear on the board connected to the rest of the plant

#### Scenario: Stump after a cut
- **WHEN** the server reports that a cell became a stump and others were removed
- **THEN** the stump is shown in the stump style and the removed cells disappear

### Requirement: Tips show partial growth
A growing tip SHALL be drawn reaching partway toward its next hex in proportion to its progress, so that slow plants are seen to creep between iterations. A blocked tip SHALL be drawn without that extension.

#### Scenario: Slow plant
- **WHEN** a plant with speed 0.25 is two iterations into its next hex
- **THEN** its tip is drawn extending about halfway toward the next hex

### Requirement: Unbounded board navigation
The player SHALL be able to pan the view in any direction without limit by dragging. The grid SHALL appear to continue in every direction wherever the view is moved.

#### Scenario: Pan away from the plants
- **WHEN** the player drags the board far from any plant
- **THEN** the view shows empty grid, and dragging back brings the plants into view unchanged

#### Scenario: Drag is not a click
- **WHEN** the player drags the board with a tool selected
- **THEN** the view pans and the tool is not used

### Requirement: Hex size setting
The client SHALL provide a hex size setting, adjustable with a slider and with the mouse wheel, that changes how large each hexagon is drawn. Changing it SHALL take effect immediately, SHALL NOT change the game, and SHALL NOT be sent to the server. The chosen size SHALL be remembered in the same browser between visits.

#### Scenario: Smaller hexes
- **WHEN** the player lowers the hex size
- **THEN** hexagons are drawn smaller, more of the board fits in view, and no plant gains, loses, or moves a cell

#### Scenario: Wheel and slider agree
- **WHEN** the player turns the mouse wheel over the board
- **THEN** the hex size changes and the slider shows the new value

#### Scenario: Setting is remembered
- **WHEN** the player reloads the page after changing the hex size
- **THEN** the board is drawn at the previously chosen size

### Requirement: Seed tool
The client SHALL provide a seed tool with a species picker filled from the server's catalog and a speed field that starts at the chosen species' default speed. With the seed tool selected, clicking a hex SHALL ask the server to plant a seed of that species and speed there.

#### Scenario: Plant a seed
- **WHEN** the player selects the seed tool and clicks an empty hex
- **THEN** a seed appears in that hex and begins growing in a direction the player did not choose

#### Scenario: Custom speed
- **WHEN** the player sets the speed field to 0.25 and plants a seed
- **THEN** the resulting plant gains one hex every 4 iterations

### Requirement: Scissors tool
The client SHALL provide a scissors tool. With it selected, clicking a hex SHALL ask the server to cut the plant cell in that hex, whatever plant it belongs to.

#### Scenario: Cut a vine
- **WHEN** the player selects the scissors and clicks a cell in the middle of a vine
- **THEN** the board shows the stump, the missing severed part, and the plant's new tips

### Requirement: Clock controls
The client SHALL provide a pause and resume control, a field for a number of iterations with a control to grow for that many, and a display of the current iteration number. The grow control SHALL be usable only while the clock is paused. The controls SHALL always reflect the clock state reported by the server.

#### Scenario: Pause and grow
- **WHEN** the player pauses, enters 10, and uses the grow control
- **THEN** the board advances by 10 iterations and stays paused

#### Scenario: Grow control while running
- **WHEN** the clock is running
- **THEN** the grow control is disabled

### Requirement: Feedback on problems
The client SHALL tell the player when the server rejects an action, when the board is full, and when the connection to the server is lost. A rejected action SHALL leave the displayed board unchanged.

#### Scenario: Seed on an occupied hex
- **WHEN** the player clicks an occupied hex with the seed tool
- **THEN** no seed appears and a brief message says the hex is occupied

#### Scenario: Connection lost
- **WHEN** the connection to the server drops
- **THEN** the client shows that it is disconnected and stops accepting board actions
