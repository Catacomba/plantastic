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
  };

  const scheme = location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${scheme}://${location.host}/ws`);

  function setCell(cell) {
    state.cells.set(hexKey(cell.q, cell.r), cell);
  }

  function applyBoard(message) {
    state.tick = message.tick;
    state.clock = message.clock;
    state.tips = message.tips;
  }

  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    switch (message.type) {
      case "welcome":
        state.connected = true;
        state.room = message.room;
        state.mode = message.mode;
        state.seed = message.seed;
        state.species = message.species;
        state.cells.clear();
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
        handlers.onUpdate?.(state);
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
    plant: (q, r, species, speed) => send({ type: "plant", q, r, species, speed }),
    cut: (q, r) => send({ type: "cut", q, r }),
    slice: (hexes) => send({ type: "slice", hexes }),
    pause: () => send({ type: "pause" }),
    resume: () => send({ type: "resume" }),
    step: (n) => send({ type: "step", n }),
  };
}
