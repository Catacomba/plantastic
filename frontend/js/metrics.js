// Performance measurements for the metrics panel. Pure bookkeeping: no DOM,
// and nothing is recorded while it is switched off.

const FRAME_WINDOW_MS = 1000;
const RECENT_UPDATES = 10;
export const HISTORY = 120; // updates kept for the graphs

export function createMetrics() {
  let enabled = false;
  let frames = []; // timestamps of the frames in the last second
  let recent = []; // per-iteration compute time of the last few growth updates
  let iteration = null; // { ms, visits } of the latest iteration
  let grow = null; // { iterations, totalMs, eachMs } of the last multi-iteration batch
  let update = null; // { bytes, handleMs } of the latest update
  let tickMs = null;
  // One entry per update, oldest first, for the graphs.
  let handleHistory = [];
  let tipHistory = [];

  function reset() {
    frames = [];
    recent = [];
    iteration = null;
    grow = null;
    update = null;
    handleHistory = [];
    tipHistory = [];
  }

  return {
    get enabled() {
      return enabled;
    },
    set enabled(value) {
      enabled = Boolean(value);
      if (!enabled) reset();
    },

    // Called once per rendered frame with a millisecond timestamp.
    frame(now) {
      if (!enabled) return;
      frames.push(now);
      while (frames[0] < now - FRAME_WINDOW_MS) frames.shift();
    },

    // Called after an update from the server has been applied and drawn.
    // `stats` is the server's { iterations, step_ms, visits }, or null when
    // the update advanced nothing. `tips` is the number of tips after it.
    update({ bytes, handleMs, stats, tips, tickMs: available }) {
      if (!enabled) return;
      update = { bytes, handleMs };
      handleHistory.push(handleMs);
      tipHistory.push(tips);
      if (handleHistory.length > HISTORY) {
        handleHistory.shift();
        tipHistory.shift();
      }
      // null at max speed, where no time is set aside per iteration.
      if (available !== undefined) tickMs = available;
      if (!stats || !stats.iterations) return;
      const eachMs = stats.step_ms / stats.iterations;
      iteration = { ms: eachMs, visits: Math.round(stats.visits / stats.iterations) };
      recent.push(eachMs);
      if (recent.length > RECENT_UPDATES) recent.shift();
      if (stats.iterations > 1) {
        grow = { iterations: stats.iterations, totalMs: stats.step_ms, eachMs };
      }
    },

    snapshot() {
      const span = frames.length > 1 ? frames[frames.length - 1] - frames[0] : 0;
      return {
        fps: span > 0 ? ((frames.length - 1) * 1000) / span : null,
        iterationMs: iteration ? iteration.ms : null,
        // Share of the time available per iteration, in percent.
        budgetPercent: iteration && tickMs ? (iteration.ms / tickMs) * 100 : null,
        tickMs,
        recentMs: recent.length ? recent.reduce((sum, ms) => sum + ms, 0) / recent.length : null,
        visits: iteration ? iteration.visits : null,
        updateBytes: update ? update.bytes : null,
        handleMs: update ? update.handleMs : null,
        grow,
        // Read-only: the same update is at the same index in both.
        history: { handleMs: handleHistory, tips: tipHistory },
      };
    },
  };
}
