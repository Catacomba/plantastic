# Spec Delta

## ADDED Requirements

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
