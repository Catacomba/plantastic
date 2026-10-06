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

### Requirement: Keyboard panning
While the player holds W, A, S, or D, or an arrow key, the view SHALL pan up, left, down, or right respectively, continuously and smoothly until the key is released. Keys SHALL be recognized by their position on the keyboard, not by the letter they produce. Panning speed on screen SHALL be the same at every hex size and in every direction, including diagonals, and SHALL be faster while Shift is held. Keyboard panning SHALL have no limit and SHALL NOT change the game.

#### Scenario: Hold a key
- **WHEN** the player holds D
- **THEN** the view moves steadily to the right, so the board's contents slide left on screen, until D is released

#### Scenario: Arrow keys
- **WHEN** the player holds the up arrow
- **THEN** the view pans exactly as it does for W

#### Scenario: Diagonal
- **WHEN** the player holds W and D together
- **THEN** the view pans diagonally up and to the right at the same on-screen speed as a single key

#### Scenario: Opposite keys
- **WHEN** the player holds A and D together
- **THEN** the view does not move horizontally

#### Scenario: Same speed at any hex size
- **WHEN** the player holds a key for one second at a small hex size and again at a large hex size
- **THEN** the view moves the same distance on screen both times

#### Scenario: Faster with Shift
- **WHEN** the player holds Shift together with a pan key
- **THEN** the view pans noticeably faster than without Shift

#### Scenario: Another keyboard layout
- **WHEN** a player whose keyboard layout puts different letters on the W, A, S, and D key positions holds those keys
- **THEN** the view pans as it does on a QWERTY layout

#### Scenario: Board is unchanged
- **WHEN** the player pans with the keyboard
- **THEN** no plant gains, loses, or moves a cell, no tool is used, and nothing is sent to the server

### Requirement: Keyboard panning does not interfere with typing or shortcuts
Pan keys SHALL be ignored while keyboard focus is in a text field, number field, slider, or selection list, and when pressed together with Ctrl, Alt, or the Windows or Command key. Panning SHALL stop when the page loses focus.

#### Scenario: Typing a speed
- **WHEN** the player types in the speed field, including characters that are pan keys
- **THEN** the text is entered and the view does not move

#### Scenario: Arrow keys in a field
- **WHEN** the player presses an arrow key while the iteration field, the hex size slider, or the species picker has focus
- **THEN** the control responds as it normally does and the view does not move

#### Scenario: Browser shortcut
- **WHEN** the player presses Ctrl together with a pan key
- **THEN** the browser's shortcut behaves as usual and the view does not move

#### Scenario: Focus on a button
- **WHEN** the player has just clicked a button such as Pause or a tool and then holds a pan key
- **THEN** the view pans

#### Scenario: Window loses focus while a key is held
- **WHEN** the player switches to another window while holding a pan key and releases the key there
- **THEN** the view is not moving when the player returns

### Requirement: Hover follows keyboard panning
While the view pans from the keyboard with the cursor resting over the board, the hover highlight SHALL stay on the hex that is currently under the cursor.

#### Scenario: Board moves under the cursor
- **WHEN** the player holds a pan key while the cursor rests over the board
- **THEN** the highlight moves from hex to hex as different hexes pass under the cursor

#### Scenario: Click after panning
- **WHEN** the player pans with the keyboard and then clicks without moving the mouse
- **THEN** the tool is used on the highlighted hex

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
