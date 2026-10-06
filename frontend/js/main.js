import { Board, MAX_HEX_SIZE, MIN_HEX_SIZE } from "./board.js";
import * as hex from "./hex.js";
import { panOffset, trackHeldKeys } from "./keys.js";
import { connect } from "./net.js";
import { setupUi } from "./ui.js";

const HEX_SIZE_KEY = "plantastic.hexSize";
const DEFAULT_HEX_SIZE = 28;
const MAX_SLICE_HEXES = 512; // the most hexes the server accepts in one slice
const HOVER_COLORS = { seed: 0x5fbf7a, scissors: 0xd9654f, mower: 0xd9654f };

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
    stroke = null;
    board.setStroke([]);
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

// -- pointer input -------------------------------------------------------
// The left button uses the selected tool; the right or middle button pans.
// A second button pressed while one is held arrives as a pointermove, not a
// pointerdown, so everything is derived from the `buttons` mask.

const LEFT = 1;
const PAN_BUTTONS = 2 | 4; // right, middle

let buttons = 0;
let pointer = null; // where the cursor last was over the board, or null when it is elsewhere
let stroke = null; // the cutting stroke in progress, if any

function showHover() {
  if (!pointer || !net.state.connected) {
    board.setHover(null);
    return;
  }
  board.setHover(board.hexAt(pointer.x, pointer.y), HOVER_COLORS[ui.tool]);
}

function sendSlice(hexes) {
  for (let i = 0; i < hexes.length; i += MAX_SLICE_HEXES) {
    net.slice(hexes.slice(i, i + MAX_SLICE_HEXES));
  }
}

function beginTool() {
  if (!net.state.connected) return;
  const start = board.hexAt(pointer.x, pointer.y);
  if (ui.tool === "seed") {
    if (ui.speed === "") ui.toast("Enter a speed for the seed.");
    else net.plant(start[0], start[1], ui.species, ui.speed);
    return;
  }
  stroke = {
    tool: ui.tool,
    start,
    last: start,
    leftStart: false,
    hexes: [start],
    marked: new Set([start.join()]),
    wasRunning: false,
  };
  if (stroke.tool === "scissors") {
    net.slice([start]);
  } else {
    // The mower holds the game still while the path is drawn.
    stroke.wasRunning = net.state.clock === "running";
    if (stroke.wasRunning) net.pause();
    board.setStroke(stroke.hexes);
  }
}

// Adds every hex between the last stroke hex and the one now under the cursor.
function extendStroke() {
  if (!stroke) return;
  const current = board.hexAt(pointer.x, pointer.y);
  if (current[0] === stroke.last[0] && current[1] === stroke.last[1]) return;
  const passed = hex.hexLine(stroke.last, current).slice(1);
  stroke.last = current;
  stroke.leftStart = true;
  if (stroke.tool === "scissors") {
    sendSlice(passed);
    return;
  }
  for (const next of passed) {
    if (stroke.marked.has(next.join())) continue;
    stroke.marked.add(next.join());
    stroke.hexes.push(next);
  }
  board.setStroke(stroke.hexes);
}

// A stroke never cuts a root. Removing a plant takes a press and release on
// its root without the cursor leaving that hex.
function isRootClick(ended) {
  if (ended.leftStart) return false;
  return net.state.cells.get(hex.hexKey(...ended.start))?.kind === "root";
}

function endTool() {
  if (!stroke) return;
  const ended = stroke;
  stroke = null;
  if (ended.tool === "scissors") {
    if (isRootClick(ended)) net.cut(...ended.start);
    return;
  }
  board.setStroke([]);
  if (isRootClick(ended)) net.cut(...ended.start);
  else sendSlice(ended.hexes);
  if (ended.wasRunning) net.resume();
}

// Drops the stroke without cutting. The rest of the current press is ignored.
function cancelStroke() {
  if (!stroke) return;
  const cancelled = stroke;
  stroke = null;
  if (cancelled.tool !== "mower") return;
  board.setStroke([]);
  if (cancelled.wasRunning) net.resume();
}

function onPointer(event) {
  const previous = buttons;
  const last = pointer;
  buttons = event.buttons;
  pointer = { x: event.clientX, y: event.clientY };

  if (buttons & PAN_BUTTONS && previous & PAN_BUTTONS && last) {
    board.panBy(pointer.x - last.x, pointer.y - last.y);
  }
  canvas.classList.toggle("panning", Boolean(buttons & PAN_BUTTONS));

  if (buttons & LEFT) {
    if (previous & LEFT) extendStroke();
    // Only a real press starts the tool, not a move that arrives with the
    // button already down (as after a cancelled stroke).
    else if (event.button === 0) beginTool();
  } else if (previous & LEFT) {
    endTool();
  }
  showHover();
}

canvas.addEventListener("pointerdown", (event) => {
  canvas.setPointerCapture(event.pointerId);
  onPointer(event);
});
canvas.addEventListener("pointermove", onPointer);
canvas.addEventListener("pointerup", onPointer);
canvas.addEventListener("pointercancel", (event) => {
  cancelStroke();
  onPointer(event);
});
canvas.addEventListener("pointerleave", () => {
  if (buttons) return;
  pointer = null;
  showHover();
});

// Right-drag pans, so the context menu and middle-button autoscroll stay out of the way.
canvas.addEventListener("contextmenu", (event) => event.preventDefault());
canvas.addEventListener("mousedown", (event) => {
  if (event.button === 1) event.preventDefault();
});

window.addEventListener("keydown", (event) => {
  if (event.code === "Escape") cancelStroke();
});
window.addEventListener("blur", cancelStroke);

canvas.addEventListener(
  "wheel",
  (event) => {
    event.preventDefault();
    setHexSize(board.hexSize * Math.exp(-event.deltaY * 0.0015), event.clientX, event.clientY);
  },
  { passive: false },
);

// -- keyboard: WASD and the arrow keys pan while held ----------------------

const heldKeys = trackHeldKeys();

board.start((seconds) => {
  const [dx, dy] = panOffset(heldKeys, seconds);
  if (dx === 0 && dy === 0) return;
  // panBy moves the board's contents, so the view goes the opposite way.
  board.panBy(-dx, -dy);
  // Hexes sliding under a held cutting tool join its stroke.
  if (pointer && buttons & LEFT) extendStroke();
  showHover();
});

// For poking at the game from the browser console.
window.plantastic = { board, net, hex, heldKeys };
