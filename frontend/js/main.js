import { Board, MAX_HEX_SIZE, MIN_HEX_SIZE } from "./board.js";
import * as hex from "./hex.js";
import { connect } from "./net.js";
import { setupUi } from "./ui.js";

const HEX_SIZE_KEY = "plantastic.hexSize";
const DEFAULT_HEX_SIZE = 28;
const DRAG_THRESHOLD = 5; // pixels a press may move and still count as a click
const HOVER_COLORS = { seed: 0x5fbf7a, scissors: 0xd9654f };

function loadHexSize() {
  try {
    const saved = Number(localStorage.getItem(HEX_SIZE_KEY));
    if (saved >= MIN_HEX_SIZE && saved <= MAX_HEX_SIZE) return saved;
  } catch {
    // Storage can be unavailable; the default is fine.
  }
  return DEFAULT_HEX_SIZE;
}

function saveHexSize(size) {
  try {
    localStorage.setItem(HEX_SIZE_KEY, String(size));
  } catch {
    // Not remembered this time.
  }
}

const problems = hex.selfCheck();
if (problems.length) console.error("Plantastic: hex self-check failed", problems);

const canvas = document.getElementById("board");
const board = new Board(canvas, loadHexSize());

function redraw(state) {
  board.setCells(state.cells);
  board.setTips(state.tips);
  ui.sync();
}

const net = connect({
  onWelcome(state) {
    ui.welcome();
    redraw(state);
  },
  onUpdate: redraw,
  onError: (message) => ui.toast(message.message),
  onNotice: (message) => ui.toast(message.message),
  onDisconnect() {
    board.setHover(null);
    ui.disconnected();
  },
});

// The slider and the mouse wheel drive the same value.
function setHexSize(size, anchorX, anchorY) {
  const applied = board.setHexSize(size, anchorX, anchorY);
  ui.showHexSize(applied);
  saveHexSize(applied);
}

const ui = setupUi({ net, onHexSize: (size) => setHexSize(size) });
ui.showHexSize(board.hexSize);
ui.sync();
board.start();

// -- pointer input: a short press uses the tool, a longer one pans ---------

let press = null;

function useTool(clientX, clientY) {
  if (!net.state.connected) return;
  const [q, r] = board.hexAt(clientX, clientY);
  if (ui.tool === "scissors") {
    net.cut(q, r);
  } else if (ui.speed === "") {
    ui.toast("Enter a speed for the seed.");
  } else {
    net.plant(q, r, ui.species, ui.speed);
  }
}

function showHover(event) {
  if (!net.state.connected || (press && press.dragging)) {
    board.setHover(null);
    return;
  }
  board.setHover(board.hexAt(event.clientX, event.clientY), HOVER_COLORS[ui.tool]);
}

canvas.addEventListener("pointerdown", (event) => {
  if (event.button !== 0) return;
  canvas.setPointerCapture(event.pointerId);
  press = { startX: event.clientX, startY: event.clientY, lastX: event.clientX, lastY: event.clientY, dragging: false };
});

canvas.addEventListener("pointermove", (event) => {
  if (press) {
    const moved = Math.hypot(event.clientX - press.startX, event.clientY - press.startY);
    if (!press.dragging && moved > DRAG_THRESHOLD) {
      press.dragging = true;
      canvas.classList.add("panning");
    }
    if (press.dragging) {
      board.panBy(event.clientX - press.lastX, event.clientY - press.lastY);
      press.lastX = event.clientX;
      press.lastY = event.clientY;
    }
  }
  showHover(event);
});

function endPress(event, completed) {
  if (!press) return;
  const wasClick = completed && !press.dragging;
  press = null;
  canvas.classList.remove("panning");
  if (wasClick) useTool(event.clientX, event.clientY);
  showHover(event);
}

canvas.addEventListener("pointerup", (event) => endPress(event, true));
canvas.addEventListener("pointercancel", (event) => endPress(event, false));
canvas.addEventListener("pointerleave", () => {
  if (!press) board.setHover(null);
});

canvas.addEventListener(
  "wheel",
  (event) => {
    event.preventDefault();
    setHexSize(board.hexSize * Math.exp(-event.deltaY * 0.0015), event.clientX, event.clientY);
  },
  { passive: false },
);

// For poking at the game from the browser console.
window.plantastic = { board, net, hex };
