# Spec Delta

## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Clock controls
The client SHALL provide a pause and resume control, speed buttons, a field for a number of iterations with a control to grow for that many, and a display of the current iteration number. The grow control SHALL be usable only while the clock is paused. The controls SHALL always reflect the clock state and speed reported by the server.

#### Scenario: Pause and grow
- **WHEN** the player pauses, enters 10, and uses the grow control
- **THEN** the board advances by 10 iterations and stays paused

#### Scenario: Grow control while running
- **WHEN** the clock is running
- **THEN** the grow control is disabled

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
