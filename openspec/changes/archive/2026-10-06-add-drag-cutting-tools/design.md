# Design

## Context

See proposal.md for motivation. The relevant current state:

- `World.cut(hex)` cuts one hex and raises `SimError` for an empty hex or a stump. Cutting a root removes the plant.
- The protocol has a `cut` command; the room turns `SimError` into an `error` message that the client shows as a toast.
- `main.js` treats a left press that moves less than 5 pixels as a click and anything longer as a pan. It listens to `pointerdown`, `pointermove`, and `pointerup` and assumes one button.
- `Changes.merge` already combines several mutations into one replayable record, and the room already sends one `update` per command.
- The clock is owned by the server. The client can only ask for `pause` and `resume`.

## Goals / Non-Goals

**Goals:**

- One server-side definition of "cut along a path" that both tools use, so the tools differ only in the browser.
- Root protection and silent skipping enforced by the server, not only by the client.
- Pointer handling that stays correct when two buttons are held at once.

**Non-Goals:**

- Touch input.
- A Mower that works where pausing is not permitted.
- Correlating errors with the command that caused them, or any request ids in the protocol.
- A visible trail for the scissors.

## Decisions

### 1. `World.slice(hexes)` in the simulation

`slice` walks the list in order. For each hex it looks up the cell at that moment and skips it when it is missing, a stump, or a root; otherwise it calls the existing `cut` and merges the returned `Changes`. It returns one `Changes` and never raises for uncuttable hexes.

Looking the cell up at its turn, not up front, is what makes the ordering scenarios work: a hex removed by an earlier cut in the same path is simply empty by the time it is reached.

*Alternative considered:* having the client filter the path against its own copy of the board and send plain `cut` commands. Rejected because the client's copy can be a tick out of date, which would produce stray "nothing to cut" errors, and because root protection would then be only as trustworthy as the client.

### 2. Slices never cut roots; a click on a root is a plain `cut`

The server rule is unconditional: `slice` skips roots. The "single click removes the plant" behavior lives in the client, which sends the existing `cut` command when a press and release happen on the same hex without the cursor leaving it and that hex holds a root in the client's copy of the board.

*Alternative considered:* letting a one-hex slice cut a root. Rejected because the scissors send their first hex at the press, before it is known whether the gesture is a click or the start of a drag; a drag that begins on a root would delete the plant.

A consequence: clicking an empty hex or a stump with a cutting tool is now silent, where it used to show "There is nothing to cut there." The `cut` error path remains for the root click, where a stale client copy can still produce it.

### 3. The `slice` command

Client to server: `slice {hexes: [[q, r], ...]}` with 1 to 512 hexes, each a pair of whole numbers within the existing coordinate bounds. Validation failures are `bad_message`, like any other malformed command. The room checks the mode's permission for `"slice"`, applies `World.slice` to the board, and returns one `update`. No new server-to-client message and no new error code.

512 bounds the work one message can cause. The Mower splits a longer stroke into several messages; they are sent back to back while the room is paused, so all cuts still land on the same iteration.

### 4. Scissors: send as the cursor moves

On a left press the client sends `slice` with the hex under the cursor. On each later pointer position it computes the hexes between the last stroke hex and the current one, drops the starting hex, and sends the rest as one `slice`. Hexes are not deduplicated across the stroke, so re-crossing a hex cuts whatever has grown there since.

On release, if the cursor never left the starting hex and that hex holds a root, the client sends `cut` for it (decision 2).

### 5. Mower: pause, collect, release

- **Press:** remember whether the clock is running. If it is, send `pause`. Start a stroke with the hex under the cursor.
- **Drag:** append newly passed hexes to an ordered list without repeats, and show the list through `Board.setStroke`.
- **Release:** if the stroke is a single hex holding a root, send `cut`; otherwise send the list as `slice` messages of at most 512 hexes. Then send `resume` if the clock was running at the press. Clear the preview.
- **Cancel** (Escape, `pointercancel`, window `blur`): clear the preview, send `resume` if the clock was running at the press, and ignore the rest of the current press.

"Was running" is read from the client's last reported clock state at the press. Messages on one websocket are processed in order, so `pause`, the slices, and `resume` cannot interleave incorrectly. A tick already in flight when `pause` is sent can still land before the pause; that is harmless because nothing is cut until release.

*Alternative considered:* a dedicated server-side "mow" session that holds the pause. Rejected as more state for no benefit in the sandbox; it becomes relevant only when a mode needs a Mower without a global pause, which is out of scope.

### 6. Hex line interpolation

`hex.js` gains `hexLine(from, to)`, the standard cube-coordinate line: for N equal to the hex distance, sample N + 1 evenly spaced points between the two centers and round each to a hex. Consecutive results are always neighbors, so a stroke has no gaps. A tiny offset is added before rounding so that points exactly on an edge resolve consistently. The function is pure and is checked in Node, like the existing `selfCheck`.

Strokes are tracked in hex coordinates, not screen coordinates, so panning during a stroke needs no special handling: the next cursor position maps to a new hex and the line is drawn from the previous stroke hex.

### 7. Pointer handling by button state

A second button pressed while the first is held does not fire `pointerdown`; it arrives as a `pointermove` with a changed `buttons` mask. The handlers therefore derive state from `event.buttons` on every pointer event:

- bit 1 (left) rising starts the tool action, falling ends it;
- bits 2 and 4 (right, middle) held means pan by the pointer delta.

This replaces the click-versus-drag threshold, which is no longer needed. `contextmenu` on the canvas is always prevented, and the default action of a middle-button press (autoscroll) is prevented. Pointer capture is taken on the first button down and released when no buttons remain.

The keyboard pan callback, which already refreshes the hover highlight each frame, also extends an active stroke to the hex now under the cursor.

### 8. Stroke preview

`Board.setStroke(hexes)` fills an instanced mesh of translucent hexagons, reusing the `Instances` pool with a transparent material and a render order between the grid and the plants. Passing an empty list clears it. The hover highlight keeps working during a stroke.

### 9. Tool bar

A third radio button, Mower, joins Seed and Scissors. The hover color for the Mower matches the scissors. Species and speed stay disabled unless the seed tool is selected, as today.

## Risks / Trade-offs

- [The Mower's resume is lost if the tab closes or crashes mid-stroke] → The room is discarded when its only player disconnects, so nothing is left paused. This needs revisiting when rooms outlive a connection.
- [A long live scissors drag sends many small messages] → At most one per pointer event, each with a handful of hexes; the server cost per hex is a dictionary lookup.
- [Left-drag panning disappears with no on-screen hint] → README and the tool bar tooltips name the new controls. A first-run hint is not included.
- [Right-drag panning is awkward on some trackpads] → Keyboard panning already exists as the alternative.
- [Silent clicks on empty hexes give less feedback than before] → Accepted; an error on every stray click would be worse once dragging is the main way to cut.

## Open Questions

- Whether the scissors should leave a short fading trail. It is cosmetic and can be added without touching the specs.
