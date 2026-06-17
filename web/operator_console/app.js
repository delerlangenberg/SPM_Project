const logEl = document.getElementById("operator-log");
const stateEl = document.getElementById("system-state");
const detailEl = document.getElementById("system-detail");
const zReadoutEl = document.getElementById("z-readout");
const statusJsonEl = document.getElementById("status-json");
const windowLayer = document.getElementById("window-layer");

let latestStatus = null;

function log(message) {
  const p = document.createElement("p");
  p.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
  logEl.prepend(p);
}

function closeWindows() {
  windowLayer.hidden = true;
  for (const win of document.querySelectorAll(".floating-window")) {
    win.hidden = true;
  }
}

function openWindow(id) {
  closeWindows();
  const win = document.getElementById(id);
  if (!win) {
    log(`Window not found: ${id}`);
    return;
  }

  if (id === "status-window" && latestStatus) {
    statusJsonEl.textContent = JSON.stringify(latestStatus, null, 2);
  }

  windowLayer.hidden = false;
  win.hidden = false;
  log(`Opened ${id}.`);
}

async function loadStatus() {
  try {
    const response = await fetch("/api/status");
    const status = await response.json();
    latestStatus = status;

    stateEl.textContent = `${status.project} · ${status.status}`;
    detailEl.textContent = `Mode: ${status.safety.default_mode}; real motion enabled: ${status.safety.real_motion_enabled}`;

    document.getElementById("mk4s-status").textContent = status.hardware.mk4s;
    document.getElementById("z-status").textContent = status.hardware.z_scanner;
    document.getElementById("xy-status").textContent = status.hardware.xy_scanner;

    log("Status loaded from local API stub.");
  } catch (error) {
    stateEl.textContent = "Offline static view";
    detailEl.textContent = "Server API not reachable. Static layout is still visible.";
    log(`Status API unavailable: ${error.message}`);
  }
}

function handleAction(action) {
  const messages = {
    "system-on": "Phase 2.1 placeholder: system ON will connect to existing hardware command services.",
    "system-off": "Phase 2.1 placeholder: system OFF will safely disable hardware services.",
    "system-status": "Phase 2.1 placeholder: status refresh requested.",
    "system-close": "Phase 2.1 placeholder: close/shutdown workflow requested.",
    "z-approach": "Phase 2.2 placeholder: Z approach requested.",
    "z-retract": "Phase 2.2 placeholder: Z retract requested.",
    "z-read": "Phase 2.2 placeholder: Z readback requested.",
    "z-park": "Phase 2.2 placeholder: Z park requested.",
    "x-minus": "Phase 2.3 placeholder: jog X- requested.",
    "x-plus": "Phase 2.3 placeholder: jog X+ requested.",
    "y-minus": "Phase 2.3 placeholder: jog Y- requested.",
    "y-plus": "Phase 2.3 placeholder: jog Y+ requested.",
    "xy-center": "Phase 2.3 placeholder: move to XY center requested.",
    "preview-scan": "Phase 2.3 placeholder: preview scan requested.",
    "start-scan": "Phase 2.3 placeholder: real/dry scan start requested.",
    "stop-scan": "Phase 2.3 placeholder: scan stop requested.",
    "export-scan": "Phase 2.4 placeholder: export requested."
  };

  if (action === "z-read") {
    zReadoutEl.textContent = "stub: 20.00 mm";
  }

  if (action === "system-status") {
    openWindow("status-window");
  }

  log(messages[action] || `Action clicked: ${action}`);
}

document.addEventListener("click", (event) => {
  const closeButton = event.target.closest("[data-close-window]");
  if (closeButton) {
    closeWindows();
    log("Closed floating window.");
    return;
  }

  if (event.target === windowLayer) {
    closeWindows();
    log("Closed floating window.");
    return;
  }

  const openButton = event.target.closest("[data-open-window]");
  if (openButton) {
    openWindow(openButton.dataset.openWindow);
    return;
  }

  const button = event.target.closest("button");
  if (!button) return;

  const action = button.dataset.action;
  if (action) {
    handleAction(action);
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeWindows();
  }
});

loadStatus();
