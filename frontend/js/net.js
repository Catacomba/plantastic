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
    tick: 0,
    cells: new Map(),
    tips: [],
    plants: new Map(), // plant id -> { id, species, speed, settings }
    tickMs: null, // time available per iteration while the clock runs
    stats: null, // cost of the iterations the latest update advanced, if any
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
    state.tips = message.tips;
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
        state.tickMs = message.tick_ms;
        state.cells.clear();
        state.plants.clear();
        message.cells.forEach(setCell);
        applyBoard(message);
        console.info(
          `Plantastic: joined ${message.mode} room ${message.room} (seed ${message.seed}); species:`,
          message.species,
        );
        handlers.onWelcome?.(state);
        break;
      case "update":
        for (const [q, r] of message.removed) state.cells.delete(hexKey(q, r));
        message.added.forEach(setCell);
        message.changed.forEach(setCell);
        applyBoard(message);
        if (message.removed.length) forgetGonePlants();
        state.stats = message.stats;
        handlers.onUpdate?.(state, meta);
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
    // `settings` is left out for species that have none.
    plant: (q, r, species, speed, settings) => send({ type: "plant", q, r, species, speed, settings }),
    cut: (q, r) => send({ type: "cut", q, r }),
    slice: (hexes) => send({ type: "slice", hexes }),
    pause: () => send({ type: "pause" }),
    resume: () => send({ type: "resume" }),
    step: (n) => send({ type: "step", n }),
  };
}
