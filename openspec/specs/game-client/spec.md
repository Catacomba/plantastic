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
The client SHALL provide a hex size setting, adjustable with a slider in the settings menu and with the mouse wheel, that changes how large each hexagon is drawn. Changing it SHALL take effect immediately, SHALL NOT change the game, and SHALL NOT be sent to the server. The chosen size SHALL be remembered in the same browser between visits.

#### Scenario: Smaller hexes
- **WHEN** the player lowers the hex size
- **THEN** hexagons are drawn smaller, more of the board fits in view, and no plant gains, loses, or moves a cell

#### Scenario: Wheel and slider agree
- **WHEN** the player turns the mouse wheel over the board
- **THEN** the hex size changes and the slider shows the new value

#### Scenario: Setting is remembered
- **WHEN** the player reloads the page after changing the hex size
- **THEN** the board is drawn at the previously chosen size

#### Scenario: Slider lives in the settings menu
- **WHEN** the player expands the settings menu
- **THEN** the hex size slider is inside it, below the performance metrics switch, and the top bar has no hex size slider

#### Scenario: Wheel works with the menu minimized
- **WHEN** the settings menu is minimized and the player turns the mouse wheel over the board
- **THEN** the hex size changes, and the slider shows the new value when the menu is next expanded

### Requirement: Settings menu
The client SHALL show a settings menu at the top right of the board, below the top bar. Its header SHALL always be visible, and using the header SHALL switch the menu between minimized, where only the header shows, and expanded, where its settings show below the header. The menu SHALL start minimized on a first visit, and whether it is minimized SHALL be remembered in the same browser between visits. The menu SHALL be usable with the keyboard.

#### Scenario: Expand and minimize
- **WHEN** the player uses the header of the minimized menu, and then uses it again
- **THEN** the menu expands to show its settings, and then returns to showing only its header

#### Scenario: State is remembered
- **WHEN** the player expands the menu and reloads the page
- **THEN** the menu is expanded

#### Scenario: First visit
- **WHEN** a player opens the game in a browser that has never opened it
- **THEN** the menu is minimized

#### Scenario: Does not get in the way
- **WHEN** the menu is minimized
- **THEN** the board beneath the area the expanded menu would cover can be clicked and dragged as usual

### Requirement: Performance metrics switch
The settings menu SHALL contain a switch that turns the performance metrics on and off. The metrics SHALL be off on a first visit, and the choice SHALL be remembered in the same browser between visits. While the metrics are off the metrics panel SHALL NOT be shown and the client SHALL NOT take measurements for it.

#### Scenario: Turn on
- **WHEN** the player turns the switch on
- **THEN** the metrics panel appears and starts showing values

#### Scenario: Turn off
- **WHEN** the player turns the switch off
- **THEN** the metrics panel disappears

#### Scenario: Remembered
- **WHEN** the player turns the metrics on and reloads the page
- **THEN** the metrics panel is shown

#### Scenario: Panel outlives the menu
- **WHEN** the metrics are on and the player minimizes the settings menu
- **THEN** the metrics panel stays visible

### Requirement: Performance metrics panel
While the metrics are on, the client SHALL show a panel below the settings menu with: frames per second; the server's compute time for the latest iteration in milliseconds, its share of the time available per iteration, and an average over recent iterations; the tip visits of the latest iteration; the number of tips and how many are waiting; the number of cells and of plants; the size of the latest update; and the time the client took to handle it. The values SHALL refresh several times a second and SHALL stay readable while they change. The time available SHALL be the one the server last reported for the current speed. At Max, when no time is available, the panel SHALL show the compute time without a share.

#### Scenario: Idle board
- **WHEN** the metrics are on and the board is empty and running
- **THEN** the panel shows a frame rate, an iteration time near zero, and zero tips, tip visits, cells, and plants

#### Scenario: Growth raises the counts
- **WHEN** a branching plant grows for many iterations with the metrics on
- **THEN** the tips, tip visits, cells, and update size shown all rise as the plant grows

#### Scenario: Waiting tips
- **WHEN** some of a plant's tips are blocked
- **THEN** the panel shows the total number of tips and, beside it, how many are waiting

#### Scenario: Share of the time available
- **WHEN** the server reports 50 milliseconds for an iteration and 500 milliseconds available per iteration
- **THEN** the panel shows 50 ms and 10 percent

#### Scenario: Share at a higher speed
- **WHEN** the speed is 10x and the server reports 25 milliseconds for an iteration and 50 milliseconds available
- **THEN** the panel shows 25 ms and 50 percent

#### Scenario: Max speed
- **WHEN** the speed is Max
- **THEN** the panel shows the iteration's compute time and no share of the time available

#### Scenario: Paused
- **WHEN** the game is paused
- **THEN** the frame rate keeps updating and the iteration values keep showing the last iteration that ran

### Requirement: Grow for N in the metrics
After the player grows for N iterations, the metrics panel SHALL show the number of iterations of that batch, the server's total compute time for it, and the average per iteration, and SHALL use that average as the latest iteration time.

#### Scenario: Grow 100
- **WHEN** the player grows for 100 iterations and the server reports 400 milliseconds in total
- **THEN** the panel shows 100 iterations, 400 ms in total, and 4 ms per iteration

### Requirement: Performance graphs
While the metrics are on, the client SHALL show two graphs directly below the metrics panel: the time the client took to handle each update from the server, in milliseconds, and the number of tips after each update. Each graph SHALL plot one point per update, oldest on the left and newest on the right, for the most recent 120 updates. The two graphs SHALL cover the same updates, so that points for the same update line up vertically.

#### Scenario: Graphs fill as updates arrive
- **WHEN** the metrics are on and the game is running
- **THEN** each update adds one point at the right of both graphs

#### Scenario: Oldest points drop off
- **WHEN** more than 120 updates have arrived since the metrics were turned on
- **THEN** each graph shows the most recent 120 and the oldest are no longer drawn

#### Scenario: Tips graph follows the board
- **WHEN** a branching plant grows for many iterations and the board is then cleared
- **THEN** the tips graph rises as the plant grows and drops to zero at the update that cleared the board

#### Scenario: Paused
- **WHEN** the game is paused and the player sends no commands
- **THEN** both graphs stay as they are

#### Scenario: Command while paused
- **WHEN** the game is paused and the player plants a seed
- **THEN** both graphs gain one point for the update that followed

#### Scenario: Grow for N
- **WHEN** the player grows for 100 iterations and the server answers with one update
- **THEN** both graphs gain one point, not 100

#### Scenario: Nothing to draw yet
- **WHEN** the metrics have just been turned on and no update has arrived since
- **THEN** both graphs are shown empty

### Requirement: Performance graph scale
Each graph SHALL be labelled with what it shows, its latest value, and the largest value among the points in view. Each graph's vertical axis SHALL start at zero and SHALL be scaled so that the largest value in view fits within the graph.

#### Scenario: Peak is shown
- **WHEN** the handling times in view range from 1 ms to 8 ms and the latest is 2 ms
- **THEN** the handling time graph is labelled with 2 ms as the latest value and 8 ms as the largest

#### Scenario: Scale follows the points in view
- **WHEN** a single slow update of 40 ms is followed by more than 120 updates of about 2 ms
- **THEN** once the slow update has dropped off, the graph rescales so the 2 ms line is no longer flat against the bottom

#### Scenario: All zeros
- **WHEN** every point in view on the tips graph is zero
- **THEN** the graph shows a flat line along the bottom and a largest value of zero

### Requirement: Performance graphs follow the metrics switch
The graphs SHALL be shown only while the performance metrics are on, and SHALL have no switch of their own. While the metrics are off the client SHALL NOT record points for the graphs. Turning the metrics off SHALL discard the points recorded so far.

#### Scenario: Turn on
- **WHEN** the player turns the metrics switch on
- **THEN** the graphs appear below the metrics panel

#### Scenario: Turn off
- **WHEN** the player turns the metrics switch off
- **THEN** the graphs disappear together with the metrics panel

#### Scenario: History does not survive being off
- **WHEN** the player turns the metrics off after the graphs have filled, lets the game run, and turns them on again
- **THEN** the graphs start empty and show only updates that arrived after they were turned back on

#### Scenario: Graphs outlive the menu
- **WHEN** the metrics are on and the player minimizes the settings menu
- **THEN** the graphs stay visible

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
The client SHALL provide a pause and resume control, speed buttons, a field for a number of iterations with a control to grow for that many, and a display of the current iteration number. The grow control SHALL be usable only while the clock is paused. The controls SHALL always reflect the clock state and speed reported by the server.

#### Scenario: Pause and grow
- **WHEN** the player pauses, enters 10, and uses the grow control
- **THEN** the board advances by 10 iterations and stays paused

#### Scenario: Grow control while running
- **WHEN** the clock is running
- **THEN** the grow control is disabled

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

### Requirement: Feedback on problems
The client SHALL tell the player when the server rejects an action, when the board is full, and when the connection to the server is lost. A rejected action SHALL leave the displayed board unchanged.

#### Scenario: Seed on an occupied hex
- **WHEN** the player clicks an occupied hex with the seed tool
- **THEN** no seed appears and a brief message says the hex is occupied

#### Scenario: Connection lost
- **WHEN** the connection to the server drops
- **THEN** the client shows that it is disconnected and stops accepting board actions

### Requirement: Speed buttons
The client SHALL provide speed buttons for 1x, 2x, 5x, 10x, and Max in the clock bar, next to the pause control. Pressing one SHALL ask the server for that speed. The button for the speed last reported by the server SHALL be highlighted, and the buttons SHALL be usable whether the clock is running or paused, but not while disconnected.

#### Scenario: Speed up
- **WHEN** the player presses 10x while the game runs
- **THEN** the 10x button becomes highlighted once the server confirms it, and the board grows about ten times as fast

#### Scenario: Highlight follows the server
- **WHEN** the client connects to a room whose speed is 1x
- **THEN** the 1x button is highlighted and no other is

### Requirement: Client acknowledges drawn updates
After the client has applied an update that advanced the board and drawn the result on screen, it SHALL acknowledge that update's iteration number to the server. It SHALL NOT acknowledge an update before it has been drawn.

#### Scenario: Max keeps pace with the browser
- **WHEN** the game runs at Max on a busy board
- **THEN** the board keeps growing, the page stays responsive to panning and cutting, and updates do not pile up waiting to be handled

#### Scenario: Background tab
- **WHEN** the game runs at Max and the tab is hidden, then shown again
- **THEN** the board does not advance while hidden and resumes growing when shown
