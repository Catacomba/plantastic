// The connection to the game server and the client's copy of the board.
// The client only applies what the server reports; it never predicts.

import { hexKey } from "./hex.js";

export function connect(handlers) {
  const state = {
    connected: false,
    room: null,
    mode: null,
    seed: null,
    species: [],
    clock: "paused",
    speed: 1, // 1, 2, 5, 10, or "max"
    tick: 0,
    cells: new Map(),
    tips: [], // awake tips, sent in full with every message
    sleeping: new Map(), // tip id -> tip: stuck tips, sent once when they fall asleep
    skipStuck: true, // whether the room lets stuck tips sleep
    plants: new Map(), // plant id -> { id, species, speed, settings }
    tickMs: null, // time available per iteration at the current speed; null at max
    stats: null, // cost of the iterations the latest update advanced, if any
    scattered: null, // { asked, planted } when the latest update answered a scatter
  };

  // Set by the page while the performance metrics are on. When it is off,
  // messages are not timed or measured.
  let measuring = false;

  const scheme = location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${scheme}://${location.host}/ws`);

  function setCell(cell) {
    state.cells.set(hexKey(cell.q, cell.r), cell);
  }

  function applyBoard(message) {
    for (const plant of message.plants) state.plants.set(plant.id, plant);
    state.tick = message.tick;
    state.clock = message.clock;
    state.speed = message.speed;
    state.tickMs = message.tick_ms;
    state.tips = message.tips;
    state.skipStuck = message.skip_stuck;
  }

  // Sleeping tips are not resent, so they are kept here between updates.
  // `woke` goes first: a tip can wake and fall asleep again within one update.
  function applySleeping(message) {
    for (const id of message.woke) state.sleeping.delete(id);
    for (const tip of message.slept) state.sleeping.set(tip.id, tip);
  }

  // Tells the server an iteration is on screen. At max speed the server waits
  // for this before the next iteration, so the page never falls behind. The
  // animation frame runs just before the frame that shows the update, and the
  // timeout runs once that frame has been painted. Hidden tabs get no frames,
  // so a game at max speed waits while the tab is hidden.
  function acknowledgeOnceDrawn(tick) {
    requestAnimationFrame(() => setTimeout(() => send({ type: "ack", tick })));
  }

  // A plant with no cells left has been removed.
  function forgetGonePlants() {
    const alive = new Set();
    for (const cell of state.cells.values()) alive.add(cell.plant);
    for (const id of state.plants.keys()) {
      if (!alive.has(id)) state.plants.delete(id);
    }
  }

  socket.addEventListener("message", (event) => {
    const meta = measuring ? { arrived: performance.now(), bytes: event.data.length } : null;
    const message = JSON.parse(event.data);
    switch (message.type) {
      case "welcome":
        state.connected = true;
        state.room = message.room;
        state.mode = message.mode;
        state.seed = message.seed;
        state.species = message.species;
        state.cells.clear();
        state.plants.clear();
        state.sleeping = new Map(message.sleeping.map((tip) => [tip.id, tip]));
        message.cells.forEach(setCell);
        applyBoard(message);
        console.info(
          `Plantastic: joined ${message.mode} room ${message.room} (seed ${message.seed}); species:`,
          message.species,
        );
        handlers.onWelcome?.(state);
        break;
      case "update":
        if (message.cleared) {
          // The whole board went at once; the cells are not listed.
          state.cells.clear();
          state.plants.clear();
          state.sleeping.clear();
        }
        applySleeping(message);
        for (const [q, r] of message.removed) state.cells.delete(hexKey(q, r));
        message.added.forEach(setCell);
        message.changed.forEach(setCell);
        applyBoard(message);
        if (message.removed.length) forgetGonePlants();
        state.stats = message.stats;
        state.scattered = message.scattered;
        handlers.onUpdate?.(state, meta);
        if (message.stats) acknowledgeOnceDrawn(message.tick);
        break;
      case "error":
        handlers.onError?.(message);
        break;
      case "notice":
        handlers.onNotice?.(message);
        break;
    }
  });

  socket.addEventListener("close", () => {
    state.connected = false;
    handlers.onDisconnect?.(state);
  });

  function send(message) {
    if (!state.connected) return false;
    socket.send(JSON.stringify(message));
    return true;
  }

  return {
    state,
    set measuring(value) {
      measuring = Boolean(value);
    },
    // `settings` is left out for species that have none, and `persistence`
    // for each species' default.
    plant: (q, r, species, speed, settings, persistence) =>
      send({ type: "plant", q, r, species, speed, settings, persistence }),
    cut: (q, r) => send({ type: "cut", q, r }),
    slice: (hexes) => send({ type: "slice", hexes }),
    clear: () => send({ type: "clear" }),
    // `region` is { q, r, half_width, half_height }.
    scatter: (count, region, persistence) => send({ type: "scatter", count, ...region, persistence }),
    pause: () => send({ type: "pause" }),
    resume: () => send({ type: "resume" }),
    step: (n) => send({ type: "step", n }),
    skipStuck: (enabled) => send({ type: "skip_stuck", enabled }),
    // `speed` is 1, 2, 5, 10, or "max".
    speed: (speed) => send({ type: "speed", speed }),
  };
}
