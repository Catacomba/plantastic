// The controls around the board: clock, hex size, tools, and messages.

import { MAX_HEX_SIZE, MIN_HEX_SIZE } from "./board.js";
import { HISTORY } from "./metrics.js";

const MAX_STEP = 1000;
const MAX_SCATTER = 500;
const TOAST_MS = 2600;
const METRICS_REFRESH_MS = 250;
const MENU_OPEN_KEY = "plantastic.menuOpen";
const METRICS_KEY = "plantastic.metrics";
const SKIP_STUCK_KEY = "plantastic.skipStuck";

// Remembered yes/no choices. Storage can be unavailable, in which case the
// choice simply lasts for the visit.
function loadFlag(key, fallback = false) {
  try {
    const saved = localStorage.getItem(key);
    return saved === null ? fallback : saved === "1";
  } catch {
    return fallback;
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
  const speedButtons = [...document.querySelectorAll("#speeds button")];
  const stepCount = $("step-count");
  const scatterCount = $("scatter-count");
  const scatterButton = $("scatter");
  const clearButton = $("clear");
  const hexSize = $("hex-size");
  const species = $("species");
  const speed = $("speed");
  const persistence = $("persistence");
  const persistenceOverride = $("persistence-override");
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
    // The persistence the plant really has, which may not be its species' default.
    // A custom plant's persistence setting is left out so the value shows once.
    if (plant.persistence != null) parts.push(`persistence ${plant.persistence}%`);
    if (entry && plant.settings) {
      const shown = entry.settings.filter((setting) => setting.id !== "persistence");
      parts.push(...shown.map((setting) => settingText(setting, plant.settings[setting.id])));
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
    for (const button of speedButtons) {
      button.disabled = !connected;
      button.setAttribute("aria-checked", String(button.dataset.speed === String(net.state.speed)));
    }
    skipStuckToggle.disabled = !connected;
    skipStuckToggle.checked = connected ? net.state.skipStuck : skipStuckWanted;
    // Persistence applies to Random seeds too, so it stays usable with any tool.
    persistenceOverride.disabled = !connected;
    persistence.disabled = !connected || !persistenceOverride.checked;
    $("tick").textContent = tick;
    $("cell-count").textContent = cells.size;
  }

  persistenceOverride.addEventListener("change", sync);

  // The highlight moves only once the server reports the new speed.
  for (const button of speedButtons) {
    button.addEventListener("click", () => {
      const { speed } = button.dataset;
      net.speed(speed === "max" ? speed : Number(speed));
    });
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
  const skipStuckToggle = $("skip-stuck-toggle");
  // What this browser asks rooms for. The switch itself shows what the room reports.
  let skipStuckWanted = loadFlag(SKIP_STUCK_KEY, true);
  const metricsPanel = $("metrics");
  const graphsPanel = $("graphs");
  const graphs = [
    { series: "handleMs", canvas: $("g-handle"), label: $("g-handle-label"), color: "--text", format: millis },
    { series: "tips", canvas: $("g-tips"), label: $("g-tips-label"), color: "--accent", format: whole },
  ];

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
    // At max speed no time is set aside per iteration, so there is no share.
    $("m-iteration").textContent =
      now.iterationMs === null
        ? none
        : now.tickMs === null
          ? millis(now.iterationMs)
          : `${millis(now.iterationMs)} (${percent(now.budgetPercent)} of ${whole(now.tickMs)} ms)`;
    $("m-recent").textContent = now.recentMs === null ? none : millis(now.recentMs);
    $("m-visits").textContent = now.visits === null ? none : whole(now.visits);
    $("m-tips").textContent =
      `${whole(counts.tips)} (${whole(counts.waiting)} waiting, ${whole(counts.asleep)} asleep)`;
    $("m-cells").textContent = whole(counts.cells);
    $("m-plants").textContent = whole(counts.plants);
    $("m-update").textContent =
      now.updateBytes === null ? none : `${kilobytes(now.updateBytes)}, ${millis(now.handleMs)} to handle`;
    $("m-grow-row").hidden = now.grow === null;
    if (now.grow) {
      $("m-grow").textContent =
        `${whole(now.grow.iterations)} iterations, ${millis(now.grow.totalMs)}, ${millis(now.grow.eachMs)} each`;
    }
    drawGraphs(now.history);
  }

  // One line per graph, a point per update. The newest point sits at the
  // right edge in both, so the same update lines up between them.
  function drawGraphs(history) {
    const style = getComputedStyle(document.documentElement);
    for (const graph of graphs) {
      const values = history[graph.series];
      const peak = values.length ? Math.max(...values) : 0;
      graph.label.textContent = values.length
        ? `${graph.format(values[values.length - 1])} (peak ${graph.format(peak)})`
        : "–";

      // Sized from the box each time, so it stays sharp when the zoom changes.
      const { canvas } = graph;
      const ratio = window.devicePixelRatio || 1;
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;
      canvas.width = Math.round(width * ratio);
      canvas.height = Math.round(height * ratio);
      const context = canvas.getContext("2d");
      context.scale(ratio, ratio);
      if (!values.length) continue;

      const color = style.getPropertyValue(graph.color).trim();
      const scale = peak || 1; // all zeros draw along the bottom
      const step = width / (HISTORY - 1);
      const x = (i) => width - (values.length - 1 - i) * step;
      const y = (value) => height - 1 - (value / scale) * (height - 2);
      context.fillStyle = color;
      context.strokeStyle = color;
      if (values.length === 1) {
        context.beginPath();
        context.arc(width - 1.5, y(values[0]), 1.5, 0, 2 * Math.PI);
        context.fill();
        continue;
      }
      context.beginPath();
      values.forEach((value, i) => context.lineTo(x(i), y(value)));
      context.lineWidth = 1.5;
      context.lineJoin = "round";
      context.stroke();
      context.lineTo(width, height);
      context.lineTo(x(0), height);
      context.globalAlpha = 0.15;
      context.fill();
    }
  }

  // Off means off: no panel, no timer, and nothing measured.
  function setMetrics(on) {
    metricsToggle.checked = on;
    metricsPanel.hidden = !on;
    graphsPanel.hidden = !on;
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
  skipStuckToggle.addEventListener("change", () => {
    skipStuckWanted = skipStuckToggle.checked;
    saveFlag(SKIP_STUCK_KEY, skipStuckWanted);
    net.skipStuck(skipStuckWanted);
  });
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
    // Whether this browser wants rooms to skip stuck tips.
    get skipStuck() {
      return skipStuckWanted;
    },
    // The persistence new seeds would be sent with: a number while Override is
    // ticked, or undefined for each species' default. Null when the field does
    // not hold a whole number, after telling the player so; send nothing then.
    get persistence() {
      if (!persistenceOverride.checked) return undefined;
      const value = Number(persistence.value);
      if (persistence.value.trim() === "" || !Number.isInteger(value)) {
        toast("Persistence must be a whole number from 0 to 100.");
        return null;
      }
      return value;
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
