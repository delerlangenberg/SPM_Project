(function () {
  "use strict";

  const ROUTES = {
    zReference: "/api/z/reference",
    zRead: "/api/z/read",
    zAutoPreview: "/api/z/auto-preview",
    zAutoApproach: "/api/z/auto-approach",
    zMoveToSetpoint: "/api/z/move-to-setpoint",
    zManualStep: "/api/z/manual-step",
    zRetract: "/api/z/retract",
    zStop: "/api/z/stop",
    measurementLimits: "/api/measurement/limits"
  };

  window.SPM_PHASE_2_2C4_ROUTES = ROUTES;
  window.SPM_PHASE_2_2C4_MARKERS = [
    "z-mini-live-canvas",
    "spm-inline-signal-panel",
    "spm-topography-x-plus-panel",
    "spm-topography-x-minus-panel",
    "live-line-canvas",
    "live-topography-x-plus-canvas",
    "live-topography-x-minus-canvas",
    "Apply Target Z",
    "Auto Approach",
    "data-z-stop",
    "STOP"
  ];

  const zHistory = [];
  let zViewMode = localStorage.getItem("spmZViewMode") || "auto";
  let zZoomWindowMm = Number(localStorage.getItem("spmZZoomWindowMm") || "2");
  const LAYOUT_STORAGE_KEY = "spmOperatorCardLayoutV1";
  const HEIGHT_STORAGE_KEY = "spmOperatorCardHeightsV1";
  let activeMoveCard = null;

  function log(message) {
    if (window.spmVisibleLogLine) window.spmVisibleLogLine(message);
  }

  function qs(selector, root) {
    return (root || document).querySelector(selector);
  }

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function setText(id, value) {
    const node = document.getElementById(id);
    if (node) node.textContent = value;
  }

  function fmt(value, digits, suffix) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
    return Number(value).toFixed(digits) + (suffix || "");
  }

  function replaceHeader(panel, phase, title) {
    if (!panel) return;
    const phaseNode = qs(".phase-tag", panel);
    const titleNode = qs(".panel-header h2", panel);
    if (phaseNode) phaseNode.textContent = phase;
    if (titleNode) titleNode.textContent = title;
  }

  function readout(label, valueId, initial) {
    const box = el("div", "spm-readout");
    box.innerHTML = `<span>${label}</span><strong id="${valueId}">${initial || "--"}</strong>`;
    return box;
  }

  function field(labelText, id, value, step) {
    const label = el("label");
    label.textContent = labelText;
    const input = el("input");
    input.id = id;
    input.type = "number";
    input.value = value;
    if (step) input.step = step;
    label.appendChild(input);
    return label;
  }

  function fieldWithButton(labelText, id, value, step, buttonText) {
    const label = el("label", "spm-apply-field");
    const span = el("span", "", labelText);
    const row = el("div", "spm-apply-row");
    const input = el("input");
    const apply = button(buttonText, "primary");
    input.id = id;
    input.type = "number";
    input.value = value;
    if (step) input.step = step;
    apply.id = `${id}-apply`;
    row.appendChild(input);
    row.appendChild(apply);
    label.appendChild(span);
    label.appendChild(row);
    return { label, input, apply };
  }

  function button(text, className) {
    const b = el("button", className || "", text);
    b.type = "button";
    return b;
  }

  async function api(url) {
    const response = await fetch(url);
    const json = await response.json();
    renderZPayload(json);
    return json;
  }

  function installZPanel() {
    const panel = qs(".z-panel");
    if (!panel || qs("#spm-z-workstation", panel)) return;

    replaceHeader(panel, "Phase 2.2", "Z Scanner Control / Live Window Signal");
    Array.from(panel.children).forEach((child) => {
      if (!child.classList || !child.classList.contains("panel-header")) child.remove();
    });

    const box = el("div", "spm-work-card");
    box.id = "spm-z-workstation";
    box.appendChild(el("div", "spm-section-title", "Live Z state"));

    const readGrid = el("div", "spm-read-grid");
    readGrid.appendChild(readout("Current Z", "spm-z-current", "-- mm"));
    readGrid.appendChild(readout("Count Z", "spm-z-count", "--"));
    readGrid.appendChild(readout("Clearance", "spm-z-clearance", "-- um"));
    box.appendChild(readGrid);

    const canvas = el("canvas", "spm-z-live");
    canvas.id = "z-mini-live-canvas";
    canvas.width = 720;
    canvas.height = 170;
    box.appendChild(canvas);

    const scaleBar = el("div", "spm-z-scale-bar");
    scaleBar.innerHTML = [
      '<span>Z display</span>',
      '<button type="button" data-z-scale="full">Full</button>',
      '<button type="button" data-z-scale="auto">Auto</button>',
      '<button type="button" data-z-scale="zoom">Zoom</button>',
      '<label>Window mm <input id="spm-z-zoom-mm" type="number" value="2.000" min="0.010" step="0.010"></label>'
    ].join("");
    box.appendChild(scaleBar);

    box.appendChild(el("div", "spm-section-title", "Approach parameters"));
    const fields = el("div", "spm-field-grid");
    const targetField = fieldWithButton("Target Z mm", "spm-z-target-z-mm", "57.000", "0.0025", "Apply");
    fields.appendChild(targetField.label);
    fields.appendChild(field("Surface clearance mm", "spm-z-setpoint-mm", "1.000", "0.0025"));
    box.appendChild(fields);

    const commands = el("div", "spm-command-grid");
    const read = button("Read Z");
    const preview = button("Preview Auto");
    const auto = button("Auto Approach", "primary");
    const retract = button("Retract");
    const stop = button("STOP", "spm-stop");
    stop.dataset.zStop = "1";

    read.onclick = () => api(ROUTES.zRead);
    targetField.apply.onclick = () => applyTargetZ();
    targetField.input.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") {
        ev.preventDefault();
        applyTargetZ();
      }
    });
    preview.onclick = () => autoPreview();
    auto.onclick = () => autoApproach();
    retract.onclick = () => zRetract();
    stop.onclick = () => api(ROUTES.zStop);
    Array.from(scaleBar.querySelectorAll("[data-z-scale]")).forEach((btn) => {
      btn.onclick = () => {
        zViewMode = btn.dataset.zScale || "auto";
        localStorage.setItem("spmZViewMode", zViewMode);
        updateZScaleButtons();
        drawZCanvas();
      };
    });
    const zoomInput = qs("#spm-z-zoom-mm", scaleBar);
    if (zoomInput) {
      zoomInput.value = zZoomWindowMm.toFixed(3);
      zoomInput.addEventListener("change", () => {
        zZoomWindowMm = Math.max(0.01, Number(zoomInput.value || "2"));
        localStorage.setItem("spmZZoomWindowMm", String(zZoomWindowMm));
        drawZCanvas();
      });
    }

    [read, preview, auto, retract, stop].forEach((b) => commands.appendChild(b));
    box.appendChild(commands);

    const consoleBox = el("pre", "spm-console");
    consoleBox.id = "spm-z-console";
    consoleBox.textContent = "Z scanner ready. Read Z before manual or auto approach.";
    box.appendChild(consoleBox);

    panel.appendChild(box);
    updateZScaleButtons();
    api(ROUTES.zReference).catch(() => {});
    drawZCanvas();
  }

  function zSetpoint() {
    return Number(qs("#spm-z-setpoint-mm")?.value || "0");
  }

  function zTarget() {
    return Number(qs("#spm-z-target-z-mm")?.value || "0");
  }

  async function autoPreview() {
    await api(`${ROUTES.zAutoPreview}?setpoint_distance_mm=${encodeURIComponent(zSetpoint())}`);
  }

  async function applyTargetZ() {
    const target = zTarget();
    const ok = window.confirm(`Move Z to absolute target ${target.toFixed(4)} mm?\n\nWatch the nozzle and use STOP immediately if anything is wrong.`);
    if (!ok) {
      log("Apply Target Z cancelled.");
      return;
    }
    await api(`${ROUTES.zMoveToSetpoint}?target_z_mm=${encodeURIComponent(target)}&confirmed=1`);
    await api(ROUTES.zRead).catch(() => {});
  }

  async function autoApproach() {
    const ok = window.confirm(`Run software-position Z auto approach to declared surface plus ${zSetpoint().toFixed(4)} mm?`);
    if (!ok) {
      log("Z auto approach cancelled.");
      return;
    }
    await api(`${ROUTES.zAutoApproach}?setpoint_distance_mm=${encodeURIComponent(zSetpoint())}&confirmed=1`);
  }

  async function zRetract() {
    const ok = window.confirm("Retract Z to the configured safe retract target?");
    if (!ok) {
      log("Z retract cancelled.");
      return;
    }
    await api(`${ROUTES.zRetract}?confirmed=1`);
  }

  function renderZPayload(json) {
    if (!json) return;
    const current = json.current || {};
    const z = current.z;
    const countZ = current.count_z;
    if (z !== undefined) {
      setText("spm-z-current", fmt(z, 3, " mm"));
      setText("z-readout", fmt(z, 3, " mm"));
      setText("z-live-readout", fmt(z, 3, " mm"));
      zHistory.push(Number(z));
      if (zHistory.length > 120) zHistory.shift();
      drawZCanvas();
    }
    if (countZ !== undefined) setText("spm-z-count", fmt(countZ, 0, ""));
    if (json.clearance_um !== undefined) setText("spm-z-clearance", fmt(json.clearance_um, 1, " um"));
    const out = qs("#spm-z-console");
    if (out) {
      const lines = [];
      if (json.status) lines.push(`status: ${json.status}`);
      if (json.message) lines.push(json.message);
      if (json.position) lines.push(json.position);
      if (Array.isArray(json.commands) && json.commands.length) lines.push("commands:\n" + json.commands.join("\n"));
      out.textContent = lines.join("\n") || "Z route responded.";
    }
  }

  function updateZScaleButtons() {
    Array.from(document.querySelectorAll("[data-z-scale]")).forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.zScale === zViewMode);
    });
  }

  function drawZCanvas() {
    const canvas = qs("#z-mini-live-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = "#030711";
    ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = "rgba(148,163,184,0.28)";
    ctx.lineWidth = 1;
    for (let i = 1; i < 5; i += 1) {
      const y = (h / 5) * i;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }
    ctx.fillStyle = "#9fb0c3";
    ctx.font = "13px Consolas, monospace";
    ctx.fillText(`Live Z visual (${zViewMode})`, 14, 22);
    if (!zHistory.length) {
      ctx.fillText("Read Z to start trace", 14, 48);
      return;
    }
    const latest = zHistory[zHistory.length - 1];
    let min = Math.min(...zHistory);
    let max = Math.max(...zHistory);
    if (zViewMode === "full") {
      min = 0;
      max = 220;
    } else if (zViewMode === "zoom") {
      const half = Math.max(0.005, zZoomWindowMm / 2);
      min = latest - half;
      max = latest + half;
    } else {
      const pad = Math.max((max - min) * 0.18, 0.05);
      min -= pad;
      max += pad;
    }
    const span = Math.max(max - min, 0.01);
    ctx.strokeStyle = "#5fd0ff";
    ctx.lineWidth = 2;
    ctx.beginPath();
    zHistory.forEach((value, i) => {
      const x = (i / Math.max(zHistory.length - 1, 1)) * (w - 24) + 12;
      const normalized = (value - min) / span;
      const y = h - 18 - Math.max(0, Math.min(1, normalized)) * (h - 48);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
    ctx.fillStyle = "#dceeff";
    ctx.fillText(`view ${min.toFixed(3)}..${max.toFixed(3)} mm   current ${latest.toFixed(3)} mm`, 14, h - 12);
  }

  function installInlineSignalPanel() {
    const zPanel = qs(".z-panel");
    const workspace = qs(".workspace");
    if (!zPanel || !workspace || qs("#spm-inline-signal-panel")) return;

    const panel = el("section", "panel spm-inline-signal-panel");
    panel.id = "spm-inline-signal-panel";
    panel.innerHTML = [
      '<div class="panel-header">',
      '  <div><span class="phase-tag">Phase 2.2</span><h2>Line Signal / Z Feedback</h2></div>',
      '  <div class="spm-panel-actions"><button type="button" id="spm-step-signal-line">Step Line</button><button type="button" id="spm-reset-signal">Reset</button></div>',
      '</div>',
      '<div class="spm-signal-window-grid">',
      '  <div class="spm-signal-window spm-line-window">',
      '    <div class="spm-signal-title"><span>Line signal</span><strong>Z feedback</strong></div>',
      '    <canvas id="live-line-canvas" width="760" height="210"></canvas>',
      '  </div>',
      '</div>'
    ].join("");

    zPanel.insertAdjacentElement("afterend", panel);

    const step = qs("#spm-step-signal-line", panel);
    const reset = qs("#spm-reset-signal", panel);
    if (step) {
      step.onclick = () => {
        if (window.SPMRaster && window.SPMRaster.stepOneLine) window.SPMRaster.stepOneLine();
        else log("Signal line step unavailable: raster module not loaded.");
      };
    }
    if (reset) {
      reset.onclick = () => {
        if (window.SPMRaster && window.SPMRaster.resetRaster) window.SPMRaster.resetRaster();
      };
    }

    drawSignalPlaceholders();
  }

  function installTopographyPanels() {
    const measurement = qs(".measurement-panel");
    if (!measurement || qs("#spm-topography-x-plus-panel")) return;

    const plus = buildTopographyPanel({
      id: "spm-topography-x-plus-panel",
      canvasId: "live-topography-x-plus-canvas",
      title: "Topography X+",
      subtitle: "Phase 2.3 accumulated scan image",
      areaClass: "spm-topography-plus-panel"
    });
    const minus = buildTopographyPanel({
      id: "spm-topography-x-minus-panel",
      canvasId: "live-topography-x-minus-canvas",
      title: "Topography X-",
      subtitle: "Phase 2.3 reverse-direction accumulation",
      areaClass: "spm-topography-minus-panel"
    });

    measurement.insertAdjacentElement("afterend", minus);
    measurement.insertAdjacentElement("afterend", plus);
    drawSignalPlaceholders();
  }

  function buildTopographyPanel(options) {
    const panel = el("section", `panel spm-topography-panel ${options.areaClass}`);
    panel.id = options.id;
    panel.innerHTML = [
      '<div class="panel-header">',
      `  <div><span class="phase-tag">Phase 2.3</span><h2>${options.title}</h2></div>`,
      '  <div class="spm-panel-actions"><button type="button" data-spm-step-line>Step Line</button><button type="button" data-spm-open-topography>Open Tab</button></div>',
      '</div>',
      '<div class="spm-signal-window">',
      `  <div class="spm-signal-title"><span>${options.subtitle}</span><strong>Z feedback derived</strong></div>`,
      `  <canvas id="${options.canvasId}" width="700" height="280"></canvas>`,
      '</div>'
    ].join("");

    const step = qs("[data-spm-step-line]", panel);
    const open = qs("[data-spm-open-topography]", panel);
    if (step) {
      step.onclick = () => {
        if (window.SPMRaster && window.SPMRaster.stepOneLine) window.SPMRaster.stepOneLine();
      };
    }
    if (open) {
      open.onclick = () => window.open("/?window=topography-window&standalone=1", "_blank", "noopener,noreferrer");
    }
    return panel;
  }

  function drawSignalPlaceholders() {
    [
      ["live-line-canvas", "Line signal waits for scan data"],
      ["live-topography-x-plus-canvas", "X+ topography waits for accumulated lines"],
      ["live-topography-x-minus-canvas", "X- topography waits for accumulated lines"]
    ].forEach(([id, text]) => {
      const canvas = qs(`#${id}`);
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      ctx.fillStyle = "#030711";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.strokeStyle = "rgba(148,163,184,0.28)";
      ctx.strokeRect(0.5, 0.5, canvas.width - 1, canvas.height - 1);
      ctx.fillStyle = "#9fb0c3";
      ctx.font = "14px Consolas, monospace";
      ctx.fillText(text, 16, 32);
    });
  }

  function installMeasurementPanel() {
    const panel = qs(".measurement-panel");
    if (!panel || qs("#spm-measurement-workstation", panel)) return;

    replaceHeader(panel, "Phase 2.3", "Measurement Control");
    Array.from(panel.children).forEach((child) => {
      if (!child.classList || !child.classList.contains("panel-header")) child.remove();
    });

    const box = el("div", "spm-work-card");
    box.id = "spm-measurement-workstation";
    box.appendChild(el("div", "spm-section-title", "Scan parameters"));

    const fields = el("div", "spm-measure-grid");
    [
      ["X size mm", "spm-scan-x-size", "60.000"],
      ["Y size mm", "spm-scan-y-size", "60.000"],
      ["X points", "spm-scan-x-points", "64"],
      ["Y lines", "spm-scan-y-lines", "32"],
      ["Line accumulation", "spm-scan-accumulation", "1"],
      ["Step size mm", "spm-scan-step-size", "0.127"],
      ["Scan speed mm/s", "spm-scan-speed", "5.000"],
      ["Raster direction", "spm-scan-direction", "0"]
    ].forEach(([label, id, value]) => fields.appendChild(field(label, id, value, "0.001")));
    box.appendChild(fields);

    const limits = el("div", "spm-read-grid");
    limits.appendChild(readout("X allowed", "spm-limit-x", "--"));
    limits.appendChild(readout("Y allowed", "spm-limit-y", "--"));
    limits.appendChild(readout("Z allowed", "spm-limit-z", "--"));
    limits.appendChild(readout("Command resolution", "spm-limit-resolution", "--"));
    limits.appendChild(readout("Recommended speed", "spm-limit-speed", "--"));
    limits.appendChild(readout("Safe center", "spm-limit-center", "--"));
    box.appendChild(limits);

    const signal = el("div", "spm-signal-strip");
    const line = button("Signal Line", "primary");
    const topo = button("Signal Topography");
    line.onclick = () => window.open("/?window=line-window&standalone=1", "_blank", "noopener,noreferrer");
    topo.onclick = () => window.open("/?window=topography-window&standalone=1", "_blank", "noopener,noreferrer");
    signal.appendChild(line);
    signal.appendChild(topo);
    box.appendChild(signal);

    const controls = el("div", "spm-command-grid");
    ["Default Center", "Start Scanning", "Pause", "Stop"].forEach((name) => {
      const b = button(name, name === "Start Scanning" ? "primary" : name === "Stop" ? "danger" : "");
      b.onclick = () => log(`Phase 2.3 ${name}: staged UI only until XY scanner execution is enabled.`);
      controls.appendChild(b);
    });
    box.appendChild(controls);
    panel.appendChild(box);

    fetch(ROUTES.measurementLimits).then((r) => r.json()).then(renderMeasurementLimits).catch(() => {});
  }

  function renderMeasurementLimits(json) {
    if (!json || !json.limits) return;
    const l = json.limits;
    setText("spm-limit-x", `${l.x_min}..${l.x_max} mm`);
    setText("spm-limit-y", `${l.y_min}..${l.y_max} mm`);
    setText("spm-limit-z", `${l.z_min}..${l.z_max} mm`);
    if (json.scanner && json.scanner.min_xy_step_mm) {
      const step = qs("#spm-scan-step-size");
      if (step) step.value = Number(json.scanner.min_xy_step_mm).toFixed(3);
    }
    if (json.scanner) {
      const scanSpeed = qs("#spm-scan-speed");
      if (scanSpeed) scanSpeed.value = Number(json.scanner.default_scan_speed_mm_s || 5).toFixed(3);
      setText("spm-limit-speed", `${json.scanner.recommended_scan_speed_min_mm_s}..${json.scanner.recommended_scan_speed_max_mm_s} mm/s`);
      setText("spm-limit-center", `X${json.scanner.safe_center_x_mm} Y${json.scanner.safe_center_y_mm} Z${json.scanner.safe_parking_z_mm}`);
    }
    if (json.machine) {
      setText("spm-limit-resolution", `XY ${json.machine.xy_command_resolution_um} um / Z ${json.machine.z_command_resolution_um} um`);
    }
  }

  function installLogPanel() {
    const panel = qs(".log-panel");
    const logBox = qs("#operator-log");
    if (!panel || !logBox || qs("#spm-log-toolbar", panel)) return;
    replaceHeader(panel, "Phase 2.4", "SPM Live Log / API / Hardware");
    const toolbar = el("div", "spm-log-toolbar");
    toolbar.id = "spm-log-toolbar";
    toolbar.appendChild(el("strong", "", "Timestamped event stream"));
    const actions = el("div");
    const clear = button("Clear Log");
    const download = button("Download Log");
    const open = button("Open Tab");
    const toggle = button("Show Log");
    clear.onclick = () => window.spmReliableLogClear && window.spmReliableLogClear();
    download.onclick = () => window.spmReliableLogDownload && window.spmReliableLogDownload();
    open.onclick = () => window.spmReliableLogOpenTab && window.spmReliableLogOpenTab();
    toggle.onclick = () => {
      panel.classList.toggle("spm-log-expanded");
      toggle.textContent = panel.classList.contains("spm-log-expanded") ? "Hide Log" : "Show Log";
    };
    actions.appendChild(open);
    actions.appendChild(clear);
    actions.appendChild(download);
    actions.appendChild(toggle);
    toolbar.appendChild(actions);
    logBox.insertAdjacentElement("beforebegin", toolbar);
    panel.classList.add("spm-log-drawer");
  }

  function installMovableCards() {
    const cards = [
      [".main-panel", "phase-2-1-system", "main"],
      [".z-panel", "phase-2-2-z", "z"],
      ["#spm-inline-signal-panel", "phase-2-2-line-signal", "signal"],
      [".measurement-panel", "phase-2-3-measurement", "measurement"],
      ["#spm-topography-x-plus-panel", "phase-2-3-topography-plus", "topo-plus"],
      ["#spm-topography-x-minus-panel", "phase-2-3-topography-minus", "topo-minus"],
      [".log-panel", "phase-2-4-log", "log"]
    ];

    const saved = loadSavedLayout();
    cards.forEach(([selector, id, area]) => {
      const panel = qs(selector);
      if (!panel) return;
      panel.dataset.layoutId = id;
      panel.dataset.defaultArea = area;
      panel.classList.add("spm-movable-card");
      panel.style.gridArea = saved[id] || area;
      wireMovableCard(panel);
    });
    wireGlobalCardMoveHandlers();
    installLayoutResetButton();
  }

  function installResizableCards() {
    const cards = [
      [".main-panel", "phase-2-1-system"],
      [".z-panel", "phase-2-2-z"],
      ["#spm-inline-signal-panel", "phase-2-2-line-signal"],
      [".measurement-panel", "phase-2-3-measurement"],
      ["#spm-topography-x-plus-panel", "phase-2-3-topography-plus"],
      ["#spm-topography-x-minus-panel", "phase-2-3-topography-minus"],
      [".log-panel", "phase-2-4-log"]
    ];
    const saved = loadSavedHeights();
    cards.forEach(([selector, id]) => {
      const panel = qs(selector);
      if (!panel) return;
      panel.dataset.resizeId = id;
      panel.classList.add("spm-resizable-card");
      if (saved[id]) panel.style.height = `${saved[id]}px`;
    });
    installResizeObserver();
    installHeightResetButton();
  }

  function loadSavedHeights() {
    try {
      return JSON.parse(window.localStorage?.getItem(HEIGHT_STORAGE_KEY) || "{}");
    } catch (_) {
      return {};
    }
  }

  function installResizeObserver() {
    if (window.SPM_CARD_RESIZE_OBSERVER_READY) return;
    window.SPM_CARD_RESIZE_OBSERVER_READY = true;
    if (!window.ResizeObserver) return;
    const observer = new ResizeObserver((entries) => {
      const heights = loadSavedHeights();
      entries.forEach((entry) => {
        const panel = entry.target;
        if (!panel.dataset.resizeId) return;
        heights[panel.dataset.resizeId] = Math.round(entry.contentRect.height);
      });
      try {
        window.localStorage?.setItem(HEIGHT_STORAGE_KEY, JSON.stringify(heights));
      } catch (_) {
        /* Resizing still works for this session when browser storage is blocked. */
      }
    });
    document.querySelectorAll(".spm-resizable-card[data-resize-id]").forEach((panel) => observer.observe(panel));
  }

  function installHeightResetButton() {
    if (qs("#spm-reset-card-heights")) return;
    const toolsDropdown = Array.from(document.querySelectorAll(".menu-group")).find((group) => {
      const buttonNode = qs(".menu-button", group);
      return buttonNode && buttonNode.textContent.trim() === "Tools";
    })?.querySelector(".dropdown");
    if (!toolsDropdown) return;
    const reset = document.createElement("button");
    reset.id = "spm-reset-card-heights";
    reset.type = "button";
    reset.textContent = "Reset Card Heights";
    reset.onclick = () => {
      try {
        window.localStorage?.removeItem(HEIGHT_STORAGE_KEY);
      } catch (_) {
        /* Browser storage may be unavailable in restricted contexts. */
      }
      document.querySelectorAll(".spm-resizable-card").forEach((panel) => {
        panel.style.height = "";
      });
      log("Operator card heights reset to default.");
    };
    toolsDropdown.appendChild(reset);
  }

  function loadSavedLayout() {
    try {
      return JSON.parse(window.localStorage?.getItem(LAYOUT_STORAGE_KEY) || "{}");
    } catch (_) {
      return {};
    }
  }

  function saveLayout() {
    const layout = {};
    document.querySelectorAll(".spm-movable-card[data-layout-id]").forEach((panel) => {
      layout[panel.dataset.layoutId] = panel.style.gridArea || panel.dataset.defaultArea;
    });
    try {
      window.localStorage?.setItem(LAYOUT_STORAGE_KEY, JSON.stringify(layout));
    } catch (_) {
      /* Layout still works for this session when browser storage is unavailable. */
    }
  }

  function wireMovableCard(panel) {
    const header = qs(".panel-header", panel);
    if (!header || header.dataset.movableReady === "1") return;
    header.dataset.movableReady = "1";
    header.title = "Hold and move this header onto another card, then release to swap positions.";

    header.addEventListener("pointerdown", (ev) => {
      if (ev.button !== 0) return;
      if (ev.target && ev.target.closest && ev.target.closest("button, input, select, a")) return;
      activeMoveCard = panel;
      panel.classList.add("spm-card-dragging");
      document.body.classList.add("spm-card-moving");
      if (header.setPointerCapture) {
        try {
          header.setPointerCapture(ev.pointerId);
        } catch (_) {
          /* Global pointer handlers still complete the move. */
        }
      }
      ev.preventDefault();
    });
  }

  function wireGlobalCardMoveHandlers() {
    if (document.body.dataset.spmGlobalMoveReady === "1") return;
    document.body.dataset.spmGlobalMoveReady = "1";

    document.addEventListener("pointermove", (ev) => {
      if (!activeMoveCard) return;
      const target = document.elementFromPoint(ev.clientX, ev.clientY)?.closest(".spm-movable-card");
      document.querySelectorAll(".spm-drop-target").forEach((node) => {
        if (node !== target) node.classList.remove("spm-drop-target");
      });
      if (target && target !== activeMoveCard) target.classList.add("spm-drop-target");
      ev.preventDefault();
    });

    document.addEventListener("pointerup", (ev) => {
      if (!activeMoveCard) return;
      const source = activeMoveCard;
      const target = document.elementFromPoint(ev.clientX, ev.clientY)?.closest(".spm-movable-card");
      finishCardMove(source, target);
      clearActiveCardMove();
      ev.preventDefault();
    });

    document.addEventListener("pointercancel", clearActiveCardMove);
  }

  function clearActiveCardMove() {
    if (activeMoveCard) activeMoveCard.classList.remove("spm-card-dragging");
    activeMoveCard = null;
    document.body.classList.remove("spm-card-moving");
    document.querySelectorAll(".spm-drop-target").forEach((node) => node.classList.remove("spm-drop-target"));
  }

  function finishCardMove(source, target) {
    if (!source || !target || source === target) return;
    const sourceArea = source.style.gridArea || source.dataset.defaultArea;
    const targetArea = target.style.gridArea || target.dataset.defaultArea;
    source.style.gridArea = targetArea;
    target.style.gridArea = sourceArea;
    saveLayout();
    log(`Layout changed: ${source.dataset.layoutId} swapped with ${target.dataset.layoutId}.`);
  }

  function installLayoutResetButton() {
    if (qs("#spm-reset-card-layout")) return;
    const toolsDropdown = Array.from(document.querySelectorAll(".menu-group")).find((group) => {
      const buttonNode = qs(".menu-button", group);
      return buttonNode && buttonNode.textContent.trim() === "Tools";
    })?.querySelector(".dropdown");
    if (!toolsDropdown) return;
    const reset = document.createElement("button");
    reset.id = "spm-reset-card-layout";
    reset.type = "button";
    reset.textContent = "Reset Card Layout";
    reset.onclick = () => {
      try {
        window.localStorage?.removeItem(LAYOUT_STORAGE_KEY);
      } catch (_) {
        /* Browser storage may be unavailable in restricted contexts. */
      }
      document.querySelectorAll(".spm-movable-card[data-default-area]").forEach((panel) => {
        panel.style.gridArea = panel.dataset.defaultArea;
      });
      log("Operator card layout reset to default.");
    };
    toolsDropdown.appendChild(reset);
  }

  function install() {
    document.body.classList.add("spm-functional-ui");
    replaceHeader(qs(".main-panel"), "Phase 2.1", "System Control");
    installZPanel();
    installInlineSignalPanel();
    installMeasurementPanel();
    installTopographyPanels();
    installLogPanel();
    installMovableCards();
    installResizableCards();
    log("Modern operator UI restored: Phase 2.1 system, Phase 2.2 Z, Phase 2.3 measurement, Phase 2.4 log.");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", install);
  } else {
    install();
  }
})();
