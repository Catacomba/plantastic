# Design

## Context

See proposal.md for the motivation. Each websocket connection creates its own `Room` (`backend/plantastic/server/app.py`). Two tasks share it: `run_clock`, which waits on `_resumed`, sleeps `tick_interval` and then ticks, and the receive loop, which calls `room.handle` for each message. Sends go through a shared lock. `tick_interval` comes from `--tick-interval` (0.5 s by default) and reaches the client as `welcome.tick_ms`, which the metrics panel uses for its budget share. The client handles updates in `net.js`, and the board redraws on a `requestAnimationFrame` loop.

## Goals / Non-Goals

**Goals:**
- Speeding up never changes the outcome of the game: the board depends only on commands and iterations, never on timing.
- At Max, at most one clock update is waiting for acknowledgement at any time.
- Pause, resume, mower, Grow, Clear and full-board behaviour are unchanged.

**Non-Goals:**
- Combining several iterations into one update while running (the "batched" option). Grow already does this while paused.
- Rooms with several clients. Each connection has its own room today. If rooms are shared later, Max would have to wait for every client or for one leader, which is left for then.
- Saving the speed between sessions or reconnects. A new room always starts at 1x.

## Decisions

### Wire format
- `{"type": "speed", "speed": 1 | 2 | 5 | 10 | "max"}`. Anything else is rejected with `bad_game_speed`. `bad_speed` already means a bad plant speed.
- `{"type": "ack", "tick": <int>}`, a non-negative whole number. It never produces a reply, not even an update. An ack is accepted at any speed and while paused, and ignored when nothing is waiting, so the client doesn't need to track the server's state.
- `welcome` and every `update` carry `speed`, encoded the same way, and `tick_ms`: `round(tick_interval * 1000 / speed)`, or `null` at Max. Putting `tick_ms` on updates as well lets the metrics follow speed changes without a separate message.

Alternative considered: a free numeric multiplier. A fixed set keeps the UI to a row of buttons and makes validation trivial.

### Clock pacing
`Room` gains `speed` (int or `"max"`), `_sent_tick` (the iteration of the last clock update awaiting acknowledgement, or `None`), `_acked_tick`, and a `_wake: asyncio.Event` that is set on ack, speed change, pause and resume.

```
loop:
  wait _resumed
  if speed == "max":
      while running and speed == "max" and _sent_tick is not None and _acked_tick < _sent_tick:
          _wake.clear(); await _wake.wait()
      if not running or speed != "max": continue
  else:
      await sleep(tick_interval / speed)
      if not running: continue
  messages = tick();  _sent_tick = board.tick (if speed == "max", else None)
  broadcast(messages)
```

Rules: setting the speed and resuming both reset `_sent_tick` to `None`, so the first Max iteration after a switch or a resume runs at once. A stale ack, lower than `_sent_tick`, wakes the loop, which checks the condition and goes back to waiting. A wait already under way when the speed changes is cut short by a separate `_retimed` event, which only `speed` sets, so a new speed applies at once. Acks deliberately do not interrupt it: the client acknowledges at every speed, and an ack must not shorten a 1x–10x interval. Without this, a switch from 1x to Max would wait out the current interval, which for a long `--tick-interval` could be a long time.

Alternative considered: a timeout at Max (for example 1 s) in case acks are lost. It's not needed. A websocket doesn't drop messages, and stalling is the right behaviour when the tab is hidden. Pause and other commands still work while stalled.

### Acknowledging after the draw
In `net.js`, after applying an update whose `stats` is not null (it advanced the board), schedule `requestAnimationFrame(() => setTimeout(() => net.ack(message.tick)))`. The animation frame runs just before the frame that shows the new state is painted, and the zero timeout runs after that paint. This is what "drawn" means. The client acknowledges at every speed. That is cheap, it keeps the client free of speed checks, and the server ignores acks unless it is at Max. Browsers stop animation frames in hidden tabs, which produces the specified background-tab stall with no extra code.

### UI
The clock bar gets five buttons, 1x, 2x, 5x, 10x and Max, as one group after Pause, styled like the existing tool buttons with an "active" state. `ui.js` highlights the one matching `net.state.speed` on every update. The buttons are disabled while disconnected, the same rule the Pause button uses. In `metrics.js`, `tickMs` takes the latest value, including `null`. With `null`, the Iteration row shows only the compute time.

## Risks / Trade-offs

- [10x with a 50 ms interval on a large board: computing and sending an iteration takes longer than 50 ms, so updates queue on the websocket] → The interval is a sleep after each tick, not a fixed schedule, so the server never runs ahead of its own work. The browser can still fall behind, and Max is the remedy. The metrics show a share over 100% when this happens.
- [The receive loop handles commands one at a time, so a slow ack delays nothing else; but a client that floods acks costs one cheap handler call each] → Acceptable. Each ack is O(1) and sends nothing back.
- [Max with a tiny board can run hundreds of iterations per second, and fast plants fill the 100,000-cell board in seconds] → Already covered by the full-board pause and notice.
- [Existing tests construct `Room` with `tick_interval` and read `welcome["tick_ms"]`] → The defaults keep 1x, so these hold. New tests cover the other speeds.
