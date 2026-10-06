# Spec Delta

## MODIFIED Requirements

### Requirement: Unbounded board navigation
The player SHALL be able to pan the view in any direction without limit by dragging with the right or the middle mouse button. Dragging with the left mouse button SHALL NOT pan. The browser's context menu SHALL NOT appear over the board. The grid SHALL appear to continue in every direction wherever the view is moved.

#### Scenario: Pan away from the plants
- **WHEN** the player drags the board with the right mouse button far from any plant
- **THEN** the view shows empty grid, and dragging back brings the plants into view unchanged

#### Scenario: Middle button
- **WHEN** the player drags the board with the middle mouse button
- **THEN** the view pans exactly as it does with the right button

#### Scenario: Drag is not a click
- **WHEN** the player drags the board with the right or middle mouse button with a tool selected
- **THEN** the view pans and the tool is not used

#### Scenario: No context menu
- **WHEN** the player clicks or drags with the right mouse button over the board
- **THEN** no context menu appears and the tool is not used

#### Scenario: Left drag does not pan
- **WHEN** the player drags with the left mouse button
- **THEN** the view does not move

#### Scenario: Pan during a stroke
- **WHEN** the player holds the left button with a cutting tool and pans with the right button or the keyboard
- **THEN** the view moves and the stroke continues, covering the hexes that pass under the cursor

### Requirement: Seed tool
The client SHALL provide a seed tool with a species picker filled from the server's catalog and a speed field that starts at the chosen species' default speed. With the seed tool selected, pressing the left mouse button on a hex SHALL ask the server to plant a seed of that species and speed there. Dragging with the seed tool SHALL NOT plant further seeds.

#### Scenario: Plant a seed
- **WHEN** the player selects the seed tool and clicks an empty hex
- **THEN** a seed appears in that hex and begins growing in a direction the player did not choose

#### Scenario: Custom speed
- **WHEN** the player sets the speed field to 0.25 and plants a seed
- **THEN** the resulting plant gains one hex every 4 iterations

#### Scenario: Drag with the seed tool
- **WHEN** the player presses the left button on an empty hex with the seed tool and drags across other hexes before releasing
- **THEN** exactly one seed is planted, in the hex where the press began

### Requirement: Scissors tool
The client SHALL provide a scissors tool that cuts while the game keeps running. With it selected, pressing the left mouse button SHALL cut the plant cell in the hex under the cursor, whatever plant it belongs to, and dragging SHALL cut the cell in every hex the cursor passes, in the order passed, as the cursor reaches it. No hex between two cursor positions SHALL be missed, however fast the cursor moves. The scissors SHALL NOT pause or resume the game.

#### Scenario: Cut a vine
- **WHEN** the player selects the scissors and clicks a cell in the middle of a vine
- **THEN** the board shows the stump, the missing severed part, and the plant's new tips

#### Scenario: Drag across several branches
- **WHEN** the player drags the scissors across three branches while the game is running
- **THEN** each branch is cut as the cursor reaches it, plants keep growing during the drag, and the clock is still running afterwards

#### Scenario: Fast drag
- **WHEN** the player drags the scissors quickly, so that the cursor is reported at positions several hexes apart
- **THEN** every hex on the line between those positions is cut as if the cursor had visited it

#### Scenario: Regrowth during a drag
- **WHEN** a plant grows into a hex the scissors already passed, and the cursor passes that hex again in the same drag
- **THEN** the new cell is cut

## ADDED Requirements

### Requirement: Mower tool
The client SHALL provide a mower tool that cuts along a path with the game held still. Pressing the left mouse button with the mower selected SHALL pause the game. Dragging SHALL mark every hex the cursor passes, missing none, and SHALL show the marked hexes as a preview without cutting anything. Releasing the button SHALL cut the marked hexes in the order they were marked, all on the same iteration, and SHALL then resume the game if it was running when the button was pressed.

#### Scenario: Mow while running
- **WHEN** the player presses with the mower while the game is running, drags across three branches, and releases
- **THEN** the game pauses at the press, nothing is cut during the drag, all three branches are cut together at the release, and the game is running again afterwards

#### Scenario: Preview
- **WHEN** the player is dragging the mower
- **THEN** every hex marked so far is highlighted, and the highlight disappears when the stroke ends

#### Scenario: Mow while already paused
- **WHEN** the player uses the mower while the game is already paused
- **THEN** the cuts are applied at the release and the game stays paused

#### Scenario: Click with the mower
- **WHEN** the player clicks a single cell with the mower without dragging
- **THEN** that cell is cut, and the game is running or paused as it was before the click

### Requirement: Cancelling a mower stroke
While a mower stroke is in progress, pressing Escape SHALL cancel it. A stroke SHALL also be cancelled if the pointer is interrupted or the page loses focus before the button is released. A cancelled stroke SHALL cut nothing, SHALL remove the preview, and SHALL resume the game if it was running when the button was pressed.

#### Scenario: Escape
- **WHEN** the player presses Escape while dragging the mower, having pressed while the game was running
- **THEN** no cell is cut, the preview disappears, the game is running again, and releasing the mouse button afterwards cuts nothing

#### Scenario: Focus lost mid-stroke
- **WHEN** the page loses focus while a mower stroke is in progress
- **THEN** the stroke is cancelled as it is for Escape

### Requirement: Strokes are forgiving
A stroke made with the scissors or the mower SHALL skip hexes that are empty or hold a stump without showing an error message, and SHALL NOT cut a root. A root SHALL be cut, removing its plant, only when the player presses and releases the left button on the root's hex without the cursor leaving that hex, with either cutting tool.

#### Scenario: Stroke over empty board
- **WHEN** the player drags a cutting tool across hexes that hold nothing
- **THEN** nothing changes and no error message appears

#### Scenario: Stroke passes over a root
- **WHEN** the player drags a cutting tool across a plant's root and on across one of its branches
- **THEN** the branch is cut and the root and the plant remain

#### Scenario: Click a root
- **WHEN** the player clicks a plant's root with the scissors or the mower without dragging
- **THEN** the whole plant is removed

#### Scenario: Stroke starts on a root
- **WHEN** the player presses a cutting tool on a root and drags away to other hexes before releasing
- **THEN** the root and the plant remain
