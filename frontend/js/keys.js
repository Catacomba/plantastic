// Keyboard panning: which keys are held, and how far the view should move.
// Keys are matched by physical position (event.code), so WASD sits under the
// same fingers on every keyboard layout.

export const PAN_SPEED = 700; // screen pixels per second
export const SHIFT_FACTOR = 2.5;

const UP = ["KeyW", "ArrowUp"];
const DOWN = ["KeyS", "ArrowDown"];
const LEFT = ["KeyA", "ArrowLeft"];
const RIGHT = ["KeyD", "ArrowRight"];
const PAN_KEYS = new Set([...UP, ...DOWN, ...LEFT, ...RIGHT]);
const SHIFT_KEYS = ["ShiftLeft", "ShiftRight"];

const any = (held, codes) => codes.some((code) => held.has(code));

// How far the view moves in `seconds`, in screen pixels with y pointing down.
// Opposite keys cancel, and a diagonal is as fast as a single direction.
export function panOffset(held, seconds) {
  const x = any(held, RIGHT) - any(held, LEFT);
  const y = any(held, DOWN) - any(held, UP);
  if (x === 0 && y === 0) return [0, 0];
  const speed = PAN_SPEED * (any(held, SHIFT_KEYS) ? SHIFT_FACTOR : 1);
  const distance = (speed * seconds) / Math.hypot(x, y);
  return [x * distance, y * distance];
}

function isTyping(target) {
  return target instanceof Element && target.matches("input, select, textarea, [contenteditable]");
}

// Returns the live set of held pan and Shift key codes.
export function trackHeldKeys() {
  const held = new Set();

  window.addEventListener("keydown", (event) => {
    if (SHIFT_KEYS.includes(event.code)) {
      held.add(event.code);
      return;
    }
    if (!PAN_KEYS.has(event.code)) return;
    // Leave typing and browser shortcuts alone.
    if (isTyping(event.target) || event.ctrlKey || event.altKey || event.metaKey) return;
    held.add(event.code);
    event.preventDefault(); // arrow keys would otherwise scroll
  });

  // Releases always count, wherever focus has moved since the press.
  window.addEventListener("keyup", (event) => held.delete(event.code));

  // A key released in another window never reports back, so forget them all.
  window.addEventListener("blur", () => held.clear());
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) held.clear();
  });

  return held;
}
