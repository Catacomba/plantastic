# Spec Delta

## ADDED Requirements

### Requirement: Skip stuck tips switch
The settings menu SHALL contain a switch that turns skipping stuck tips on and off. It SHALL be on on a first visit, and the choice SHALL be remembered in the same browser between visits. On joining a room, and whenever the player changes it, the client SHALL ask the server for the chosen setting. The switch SHALL always show the setting the server last reported.

#### Scenario: First visit
- **WHEN** a player opens the game in a browser that has never opened it
- **THEN** the switch is on and the room skips stuck tips

#### Scenario: Remembered off
- **WHEN** the player turns the switch off and reloads the page
- **THEN** the switch is off and the new room does not skip stuck tips

#### Scenario: Board looks the same
- **WHEN** the player turns the switch on and off while plants grow
- **THEN** the board, including stuck tips, is drawn the same either way

### Requirement: Client keeps sleeping tips
The client SHALL keep the sleeping tips it has been sent, drop each one the server says has woken or been removed, empty them on a clear, and draw them together with the awake tips, so that stuck tips stay visible while they are not resent.

#### Scenario: Stuck tips stay drawn
- **WHEN** many tips are asleep and the board advances
- **THEN** every stuck tip is still drawn without an extension, as a blocked tip

## MODIFIED Requirements

### Requirement: Performance metrics panel
While the metrics are on, the client SHALL show a panel below the settings menu with: frames per second; the server's compute time for the latest iteration in milliseconds, its share of the time available per iteration, and an average over recent iterations; the tip visits of the latest iteration; the number of tips, how many are waiting, and how many of those are asleep; the number of cells and of plants; the size of the latest update; and the time the client took to handle it. The values SHALL refresh several times a second and SHALL stay readable while they change. The time available SHALL be the one the server last reported for the current speed. At Max, when no time is available, the panel SHALL show the compute time without a share.

#### Scenario: Idle board
- **WHEN** the metrics are on and the board is empty and running
- **THEN** the panel shows a frame rate, an iteration time near zero, and zero tips, tip visits, cells, and plants

#### Scenario: Growth raises the counts
- **WHEN** a branching plant grows for many iterations with the metrics on
- **THEN** the tips, tip visits, cells, and update size shown all rise as the plant grows

#### Scenario: Waiting tips
- **WHEN** some of a plant's tips are blocked
- **THEN** the panel shows the total number of tips and, beside it, how many are waiting and how many are asleep

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
