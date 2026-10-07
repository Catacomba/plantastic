# Spec Delta

## ADDED Requirements

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
