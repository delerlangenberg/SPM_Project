const logEl = document.getElementById("operator-log");
const stateEl = document.getElementById("system-state");
const detailEl = document.getElementById("system-detail");
const zReadoutEl = document.getElementById("z-readout");
const phaseMapEl = document.getElementById("phase-map");

function log(message) {
  const p = document.createElement("p");
  p.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
  logEl.prepend(p);
}

async function loadStatus() {
  try {
    const response = await fetch("/api/status");
    const status = await response.json();
    stateEl.textContent = `${status.project} · ${status.status}`;
    detailEl.textContent = `Mode: ${status.safety.default_mode}; real motion enabled: ${status.safety.real_motion_enabled}`;
    log("Status loaded from local API stub.");
  } catch (error) {
    stateEl.textContent = "Offline static view";
    detailEl.textContent = "Server API not reachable. Static layout is still visible.";
    log(`Status API unavailable: ${error.message}`);
  }
}

async function loadPhaseMap() {
  try {
    const response = await fetch("/api/phase-map");
    const phases = await response.json();

    phaseMapEl.innerHTML = "";
    for (const item of phases) {
      const card = document.createElement("article");
      card.className = "phase-card";
      card.innerHTML = `
        <h3>Phase ${item.phase}: ${item.name}</h3>
        <p><strong>Status:</strong> ${item.status}</p>
        <p>${item.purpose}</p>
      `;
      phaseMapEl.appendChild(card);
    }
  } catch (error) {
    phaseMapEl.innerHTML = "<p>Phase map API unavailable.</p>";
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

  log(messages[action] || `Menu/action clicked: ${action}`);
}

document.addEventListener("click", (event) => {
  const button = event.target.closest("button");
  if (!button) return;

  const action = button.dataset.action || button.dataset.menu;
  if (action) {
    handleAction(action);
  }
});

loadStatus();
loadPhaseMap();
