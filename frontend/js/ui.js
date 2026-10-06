// The controls around the board: clock, hex size, tools, and messages.

import { MAX_HEX_SIZE, MIN_HEX_SIZE } from "./board.js";

const MAX_STEP = 1000;
const TOAST_MS = 2600;

const $ = (id) => document.getElementById(id);

export function setupUi({ net, onHexSize }) {
  const pauseButton = $("pause");
  const growButton = $("grow");
  const stepCount = $("step-count");
  const hexSize = $("hex-size");
  const species = $("species");
  const speed = $("speed");
  const toolButtons = { seed: $("tool-seed"), scissors: $("tool-scissors") };
  const toastBox = $("toast");

  let tool = "seed";
  let toastTimer = null;

  hexSize.min = MIN_HEX_SIZE;
  hexSize.max = MAX_HEX_SIZE;

  function toast(message) {
    toastBox.textContent = message;
    toastBox.classList.add("visible");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toastBox.classList.remove("visible"), TOAST_MS);
  }

  function selectTool(name) {
    tool = name;
    for (const [key, button] of Object.entries(toolButtons)) {
      button.setAttribute("aria-checked", String(key === name));
    }
    species.disabled = speed.disabled = name !== "seed" || !net.state.connected;
  }

  function defaultSpeed() {
    const chosen = net.state.species.find((entry) => entry.id === species.value);
    if (chosen) speed.value = chosen.default_speed;
  }

  // Controls always show what the server last reported.
  function sync() {
    const { connected, clock, tick, cells } = net.state;
    const running = clock === "running";
    pauseButton.textContent = running ? "Pause" : "Resume";
    pauseButton.disabled = !connected;
    growButton.disabled = !connected || running;
    stepCount.disabled = !connected || running;
    growButton.title = running ? "Pause the game to grow by a set number of iterations." : "";
    $("tick").textContent = tick;
    $("cell-count").textContent = cells.size;
  }

  pauseButton.addEventListener("click", () => {
    if (net.state.clock === "running") net.pause();
    else net.resume();
  });

  function grow() {
    const count = Number(stepCount.value);
    if (!Number.isInteger(count) || count < 1 || count > MAX_STEP) {
      toast(`Enter a whole number of iterations from 1 to ${MAX_STEP}.`);
      return;
    }
    net.step(count);
  }
  growButton.addEventListener("click", grow);
  stepCount.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !growButton.disabled) grow();
  });

  hexSize.addEventListener("input", () => onHexSize(Number(hexSize.value)));
  toolButtons.seed.addEventListener("click", () => selectTool("seed"));
  toolButtons.scissors.addEventListener("click", () => selectTool("scissors"));
  species.addEventListener("change", defaultSpeed);

  return {
    toast,
    sync,
    get tool() {
      return tool;
    },
    get species() {
      return species.value;
    },
    get speed() {
      return speed.value.trim();
    },
    showHexSize(size) {
      hexSize.value = Math.round(size);
    },
    welcome() {
      species.replaceChildren(
        ...net.state.species.map((entry) => new Option(entry.name, entry.id)),
      );
      defaultSpeed();
      selectTool(tool);
      sync();
    },
    disconnected() {
      $("banner").hidden = false;
      selectTool(tool);
      sync();
    },
  };
}
