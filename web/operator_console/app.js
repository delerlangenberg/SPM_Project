// legacy dry-run endpoint marker for tests: /api/system/on?mode=dry_run
const logEl = document.getElementById("operator-log");
const stateEl = document.getElementById("system-state");
const detailEl = document.getElementById("system-detail");
const statusJsonEl = document.getElementById("status-json");
const aiStatusEl = document.getElementById("ai-status");
const aiOutputEl = document.getElementById("ai-output");
const aiTaskEl = document.getElementById("ai-task");

let latestStatus = null;

function log(message) {
  const p = document.createElement("p");
  p.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
  logEl.prepend(p);
}

function selectedSystemMode() {
  const el = document.getElementById("system-mode");
  return el ? el.value : "dry_run";
}

window.SPMConsoleLog = log;

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

async function loadAIStatus() {
  try {
    const response = await fetch("/api/ai/status");
    const status = await response.json();
    aiStatusEl.textContent = `${status.mode} · ${status.role}`;
    log(`Academic AI status: ${status.mode}; role: ${status.role}.`);
  } catch (error) {
    aiStatusEl.textContent = "offline";
    log(`Academic AI status unavailable: ${error.message}`);
  }
}

async function requestAIRecommendation() {
  const task = aiTaskEl ? aiTaskEl.value : "general";

  try {
    const response = await fetch(`/api/ai/recommendation?task=${encodeURIComponent(task)}`);
    const payload = await response.json();
    aiOutputEl.textContent = JSON.stringify(payload, null, 2);
    log(`Academic AI advisory recommendation requested for: ${task}.`);
  } catch (error) {
    aiOutputEl.textContent = `AI recommendation failed: ${error.message}`;
    log(`AI recommendation failed: ${error.message}`);
  }
}

async function callSystemApi(endpoint, label) {
  try {
    const response = await fetch(endpoint);
    const payload = await response.json();

    latestStatus = {
      ...latestStatus,
      system_control: payload
    };

    if (statusJsonEl) {
      statusJsonEl.textContent = JSON.stringify(latestStatus, null, 2);
    }

    const mode = payload.mode || "unknown";
    const powered = payload.powered === true ? "powered" : "not powered";

    stateEl.textContent = `SPM Prusa MK4S · ${powered}`;
    detailEl.textContent = `System control: ${mode}; real motion enabled: ${payload.real_motion_enabled}`;

    log(`${label}: ${payload.message || payload.status || "ok"}`);

    if (payload.dry_run_plan && payload.dry_run_plan.length && label !== "System OFF" && label !== "System CLOSE") {
      log(`Dry-run startup plan: ${payload.dry_run_plan.join(" | ")}`);
    }

    if (payload.hardware_information_status) {
      const hw = payload.hardware_information_status;
      const plan = hw.command_plan.map((item) => `${item.action} -> ${item.command}`).join(" | ");
      log(`Hardware information layer: ${hw.mode}; available=${hw.available}; plan=${plan}`);
    }

    return payload;
  } catch (error) {
    log(`${label} failed: ${error.message}`);
    return null;
  }
}

function handleAction(action) {
  const messages = {
    "z-retract": "Z retract requested. Hardware Z module will be connected later.",
    "z-read": "Z readback requested. Hardware Z readback will be connected later.",
    "z-park": "Z park requested. Hardware Z park will be connected later.",
    "x-minus": "Jog X- requested.",
    "x-plus": "Jog X+ requested.",
    "y-minus": "Jog Y- requested.",
    "y-plus": "Jog Y+ requested.",
    "xy-center": "XY center requested."
  };

  if (action === "system-status") {
    callSystemApi("/api/system/status", "System STATUS");
  }

  if (action === "system-on") callSystemApi(`/api/system/on?mode=${encodeURIComponent(selectedSystemMode())}`, "System ON");
  if (action === "system-off") callSystemApi("/api/system/off", "System OFF");
  if (action === "system-close") callSystemApi("/api/system/close", "System CLOSE");

  if (action === "ai-status") log("AI advisory is postponed to a later dedicated phase.");
  if (action === "ai-recommend") log("AI advisory is postponed to a later dedicated phase.");

  if (action === "z-approach") window.SPMRaster.markApproachReady();

  if (action === "default-center") window.SPMRaster.defaultCenter();
  if (action === "measurement-start") window.SPMRaster.runRasterSimulation();
  if (action === "measurement-pause") window.SPMRaster.pauseRaster();
  if (action === "measurement-stop") window.SPMRaster.stopRaster();

  if (action === "scan-profile") window.SPMRaster.checkScanProfile();
  if (action === "reset-raster") window.SPMRaster.resetRaster();
  if (action === "step-line") window.SPMRaster.stepOneLine();
  if (action === "run-raster") window.SPMRaster.runRasterSimulation();

  if (action === "z-read") {
    document.getElementById("z-readout").textContent = "stub: 20.00 mm";
  }

  if (messages[action]) log(messages[action]);
}

document.addEventListener("click", (event) => {
  const button = event.target.closest("button");
  if (!button) return;

  const action = button.dataset.action;
  if (action) handleAction(action);
});

loadStatus();
if (window.SPMRaster) {
  window.SPMRaster.redrawAll();
}





