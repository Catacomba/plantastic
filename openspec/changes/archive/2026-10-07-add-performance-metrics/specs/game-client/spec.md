# Spec Delta

## MODIFIED Requirements

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

## ADDED Requirements

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
While the metrics are on, the client SHALL show a panel below the settings menu with: frames per second; the server's compute time for the latest iteration in milliseconds, its share of the time available per iteration, and an average over recent iterations; the tip visits of the latest iteration; the number of tips and how many are waiting; the number of cells and of plants; the size of the latest update; and the time the client took to handle it. The values SHALL refresh several times a second and SHALL stay readable while they change.

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

#### Scenario: Paused
- **WHEN** the game is paused
- **THEN** the frame rate keeps updating and the iteration values keep showing the last iteration that ran

### Requirement: Grow for N in the metrics
After the player grows for N iterations, the metrics panel SHALL show the number of iterations of that batch, the server's total compute time for it, and the average per iteration, and SHALL use that average as the latest iteration time.

#### Scenario: Grow 100
- **WHEN** the player grows for 100 iterations and the server reports 400 milliseconds in total
- **THEN** the panel shows 100 iterations, 400 ms in total, and 4 ms per iteration
