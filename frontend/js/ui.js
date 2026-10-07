// The controls around the board: clock, hex size, tools, and messages.

import { MAX_HEX_SIZE, MIN_HEX_SIZE } from "./board.js";

const MAX_STEP = 1000;
const MAX_SCATTER = 500;
const TOAST_MS = 2600;
const METRICS_REFRESH_MS = 250;
const MENU_OPEN_KEY = "plantastic.menuOpen";
const METRICS_KEY = "plantastic.metrics";

// Remembered yes/no choices. Storage can be unavailable, in which case the
// choice simply lasts for the visit.
function loadFlag(key) {
  try {
    return localStorage.getItem(key) === "1";
  } catch {
    return false;
  }
}

function saveFlag(key, on) {
  try {
    localStorage.setItem(key, on ? "1" : "0");
  } catch {
    // Not remembered this time.
  }
}

const whole = (value) => Math.round(value).toLocaleString("en-US");
const millis = (value) => `${value.toFixed(1)} ms`;

function percent(value) {
  if (value >= 10) return `${Math.round(value)}%`;
  return value >= 0.1 ? `${value.toFixed(1)}%` : "<0.1%";
}

function kilobytes(bytes) {
  const kb = bytes / 1024;
  return `${kb >= 10 ? whole(kb) : kb.toFixed(1)} KB`;
}

const $ = (id) => document.getElementById(id);

export function setupUi({ net, metrics, boardCounts, onHexSize, onMetrics, onScatter }) {
  const pauseButton = $("pause");
  const growButton = $("grow");
  const stepCount = $("step-count");
  const scatterCount = $("scatter-count");
  const scatterButton = $("scatter");
  const clearButton = $("clear");
  const hexSize = $("hex-size");
  const species = $("species");
  const speed = $("speed");
  const toolButtons = { seed: $("tool-seed"), scissors: $("tool-scissors"), mower: $("tool-mower") };
  const toastBox = $("toast");
  const settingsBox = $("settings");
  const plantInfo = $("plant-info");

  // Settings chosen so far in this visit, by species. They are only ever sent
  // with a new seed; nothing here can change a plant that is already growing.
  const chosenSettings = {};

  let tool = "seed";
  let toastTimer = null;
  let metricsTimer = null;

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
    settingsBox.hidden = name !== "seed" || settingsBox.childElementCount === 0;
  }

  function selectedSpecies() {
    return net.state.species.find((entry) => entry.id === species.value);
  }

  function numberControl(setting, values) {
    const input = document.createElement("input");
    input.type = "number";
    input.min = setting.min;
    input.max = setting.max;
    input.step = 1;
    input.value = values[setting.id] ?? "";
    // An emptied field is sent as it is, and the server says what is wrong.
    const read = () => (input.value.trim() === "" ? null : Number(input.value));
    input.addEventListener("input", () => {
      values[setting.id] = read();
    });
    if (setting.kind !== "optional_int") return [input];

    const never = document.createElement("input");
    never.type = "checkbox";
    never.checked = values[setting.id] === null;
    input.disabled = never.checked;
    never.addEventListener("change", () => {
      input.disabled = never.checked;
      if (!never.checked && input.value.trim() === "") {
        input.value = Math.min(setting.max, Math.max(setting.min, 10));
      }
      values[setting.id] = never.checked ? null : read();
    });
    const wrap = document.createElement("label");
    wrap.className = "never";
    wrap.append(never, "never");
    return [input, wrap];
  }

  function control(setting, values) {
    const field = document.createElement("div");
    field.className = "field";
    const caption = document.createElement("label");
    caption.textContent = setting.label;
    field.append(caption);
    if (setting.kind === "choice") {
      const select = document.createElement("select");
      select.append(...setting.choices.map((choice) => new Option(choice.label, choice.id)));
      select.value = values[setting.id];
      select.addEventListener("change", () => {
        values[setting.id] = select.value;
      });
      field.append(select);
    } else {
      field.append(...numberControl(setting, values));
    }
    const first = field.querySelector("input, select");
    first.id = `setting-${setting.id}`;
    caption.htmlFor = first.id;
    return field;
  }

  // Shows a control for each setting of the selected species, or nothing.
  function buildSettings() {
    const entry = selectedSpecies();
    const list = entry ? entry.settings : [];
    settingsBox.replaceChildren();
    if (list.length) {
      chosenSettings[entry.id] ??= Object.fromEntries(list.map((setting) => [setting.id, setting.default]));
      settingsBox.append(...list.map((setting) => control(setting, chosenSettings[entry.id])));
    }
    settingsBox.hidden = tool !== "seed" || list.length === 0;
  }

  function settingText(setting, value) {
    if (value === null) return `${setting.label} never`;
    if (setting.kind === "choice") {
      const choice = setting.choices.find((option) => option.id === value);
      return `${setting.label} ${choice ? choice.label.toLowerCase() : value}`;
    }
    return `${setting.label} ${value}`;
  }

  function describePlant(plant) {
    const entry = net.state.species.find((candidate) => candidate.id === plant.species);
    const parts = [`Plant ${plant.id}: ${entry ? entry.name : plant.species}`, `speed ${plant.speed}`];
    if (entry && plant.settings) {
      parts.push(...entry.settings.map((setting) => settingText(setting, plant.settings[setting.id])));
    }
    return parts.join(" \u00b7 ");
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
    scatterCount.disabled = scatterButton.disabled = clearButton.disabled = !connected;
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

  function scatter() {
    const count = Number(scatterCount.value);
    if (scatterCount.value.trim() === "" || !Number.isInteger(count) || count < 1 || count > MAX_SCATTER) {
      toast(`Enter a whole number of plants from 1 to ${MAX_SCATTER}.`);
      return;
    }
    onScatter(count);
  }
  scatterButton.addEventListener("click", scatter);
  scatterCount.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !scatterButton.disabled) scatter();
  });
  clearButton.addEventListener("click", () => net.clear());
  stepCount.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !growButton.disabled) grow();
  });

  hexSize.addEventListener("input", () => onHexSize(Number(hexSize.value)));

  // -- settings menu and performance metrics ------------------------------

  const side = $("side");
  const menuToggle = $("menu-toggle");
  const menuBody = $("menu-body");
  const metricsToggle = $("metrics-toggle");
  const metricsPanel = $("metrics");

  function setMenuOpen(open) {
    menuBody.hidden = !open;
    menuToggle.setAttribute("aria-expanded", String(open));
    $("menu-mark").textContent = open ? "\u2212" : "+";
    saveFlag(MENU_OPEN_KEY, open);
  }

  function showMetrics() {
    const now = metrics.snapshot();
    const counts = boardCounts();
    const none = "\u2013";
    $("m-fps").textContent = now.fps === null ? none : whole(now.fps);
    $("m-iteration").textContent =
      now.iterationMs === null
        ? none
        : `${millis(now.iterationMs)} (${percent(now.budgetPercent)} of ${whole(now.tickMs)} ms)`;
    $("m-recent").textContent = now.recentMs === null ? none : millis(now.recentMs);
    $("m-visits").textContent = now.visits === null ? none : whole(now.visits);
    $("m-tips").textContent = `${whole(counts.tips)} (${whole(counts.waiting)} waiting)`;
    $("m-cells").textContent = whole(counts.cells);
    $("m-plants").textContent = whole(counts.plants);
    $("m-update").textContent =
      now.updateBytes === null ? none : `${kilobytes(now.updateBytes)}, ${millis(now.handleMs)} to handle`;
    $("m-grow-row").hidden = now.grow === null;
    if (now.grow) {
      $("m-grow").textContent =
        `${whole(now.grow.iterations)} iterations, ${millis(now.grow.totalMs)}, ${millis(now.grow.eachMs)} each`;
    }
  }

  // Off means off: no panel, no timer, and nothing measured.
  function setMetrics(on) {
    metricsToggle.checked = on;
    metricsPanel.hidden = !on;
    onMetrics(on);
    clearInterval(metricsTimer);
    metricsTimer = null;
    if (on) {
      showMetrics();
      metricsTimer = setInterval(showMetrics, METRICS_REFRESH_MS);
    }
    saveFlag(METRICS_KEY, on);
  }

  menuToggle.addEventListener("click", () => setMenuOpen(menuBody.hidden));
  metricsToggle.addEventListener("change", () => setMetrics(metricsToggle.checked));
  setMenuOpen(loadFlag(MENU_OPEN_KEY));
  setMetrics(loadFlag(METRICS_KEY));

  // The top bar grows when it wraps, so the column follows its lower edge.
  const clockBar = $("clock-bar");
  const placeSide = () => {
    side.style.top = `${clockBar.getBoundingClientRect().bottom + 8}px`;
  };
  new ResizeObserver(placeSide).observe(clockBar);
  placeSide();
  for (const [name, button] of Object.entries(toolButtons)) {
    button.addEventListener("click", () => selectTool(name));
  }
  species.addEventListener("change", () => {
    defaultSpeed();
    buildSettings();
  });

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
    // The settings a seed planted now would carry, or undefined for a species without any.
    get settings() {
      const entry = selectedSpecies();
      return entry && entry.settings.length ? { ...chosenSettings[entry.id] } : undefined;
    },
    // Shows the details of the plant under the cursor, or clears them.
    showPlant(plant) {
      const text = plant ? describePlant(plant) : "";
      plantInfo.textContent = text;
      plantInfo.title = text;
    },
    showHexSize(size) {
      hexSize.value = Math.round(size);
    },
    welcome() {
      species.replaceChildren(
        ...net.state.species.map((entry) => new Option(entry.name, entry.id)),
      );
      defaultSpeed();
      buildSettings();
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
