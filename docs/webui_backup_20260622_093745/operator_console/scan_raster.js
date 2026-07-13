(function () {
  "use strict";

  const state = {
    rasterLines: [],
    currentLineIndex: 0,
    runningRaster: false,
    centerReady: false,
    approachReady: false,
    runToken: 0
  };

  function byId(id) {
    return document.getElementById(id);
  }

  function log(message) {
    if (window.SPMConsoleLog) window.SPMConsoleLog(message);
  }

  function setText(id, value) {
    const el = byId(id);
    if (el) el.textContent = value;
  }

  function getScanParams() {
    return new URLSearchParams({
      x_min: byId("scan-x-min").value,
      x_max: byId("scan-x-max").value,
      y_min: byId("scan-y-min").value,
      y_max: byId("scan-y-max").value,
      x_points: byId("scan-x-points").value,
      y_points: byId("scan-y-points").value,
      z_setpoint: byId("scan-z-setpoint").value,
      feedback_gain: byId("feedback-gain-main").value,
      surface: byId("scan-surface").value,
      serpentine: "true"
    });
  }

  async function checkScanProfile() {
    const response = await fetch(`/api/scan/profile?${getScanParams().toString()}`);
    const payload = await response.json();

    if (payload.status === "error") {
      log(`Profile error: ${payload.message}`);
      return;
    }

    log(`Scan profile OK: ${payload.x_points} X points × ${payload.y_points} Y lines; ${payload.line_sequence}.`);
  }

  function defaultCenter() {
    state.centerReady = true;
    setText("center-status", "centered");
    setText("measurement-status", "centered");
    setText("xy-status", "centered_stub");
    log("Default Center complete in simulation: XY is now at configured center.");
  }

  function markApproachReady() {
    state.approachReady = true;
    setText("approach-status", "ready");
    log("Z approach complete in simulation: fixed-distance setpoint is ready.");
  }

  function pauseRaster() {
    if (!state.runningRaster) {
      setText("measurement-status", "paused");
      log("Pause requested: measurement is not currently running.");
      return;
    }

    state.runningRaster = false;
    state.runToken += 1;
    setText("measurement-status", "paused");
    log("Measurement paused. Raster loop interrupted.");
  }

  function stopRaster() {
    state.runningRaster = false;
    state.runToken += 1;
    setText("measurement-status", "stopped");
    log("Measurement stopped. Raster loop interrupted.");
  }

  function resetRaster() {
    state.rasterLines = [];
    state.currentLineIndex = 0;
    state.runningRaster = false;
    state.runToken += 1;

    setText("line-status", "0 / 0");
    setText("topography-status", "empty");
    setText("measurement-status", "idle");

    const lineJson = byId("line-json");
    if (lineJson) lineJson.textContent = "No line scan yet.";

    redrawAll();
    log("Raster reset.");
  }

  async function fetchScanLine(lineIndex) {
    const params = getScanParams();
    params.set("line_index", String(lineIndex));

    const response = await fetch(`/api/scan/line?${params.toString()}`);
    const payload = await response.json();

    if (payload.status === "error") throw new Error(payload.message);
    return payload;
  }

  async function stepOneLine(options = {}) {
    const manual = options.manual === true;
    const token = options.token ?? state.runToken;
    const yPoints = Number(byId("scan-y-points").value);

    if (state.currentLineIndex >= yPoints) {
      log("Raster complete; no more Y lines.");
      setText("measurement-status", "complete");
      return;
    }

    const line = await fetchScanLine(state.currentLineIndex);

    if (!manual && token !== state.runToken) {
      log("Line result discarded because measurement was paused/stopped.");
      return;
    }

    state.rasterLines.push(line);
    state.currentLineIndex += 1;

    const latestPoint = line.points[Math.floor(line.points.length / 2)];
    setText("z-readout", `${latestPoint.z_feedback.toFixed(3)} mm`);
    setText("line-status", `${state.currentLineIndex} / ${line.line_count}`);
    setText("topography-status", `${state.rasterLines.length} lines`);

    const lineJson = byId("line-json");
    if (lineJson) lineJson.textContent = JSON.stringify(line, null, 2);

    redrawAll();
    log(`Line ${line.line_index + 1}/${line.line_count} scanned at Y=${line.y}; direction=${line.direction}.`);
  }

  async function runRasterSimulation() {
    if (!state.centerReady) {
      setText("measurement-status", "blocked: center first");
      log("Measurement blocked: press Default Center before scanning.");
      return;
    }

    if (!state.approachReady) {
      setText("measurement-status", "blocked: approach first");
      log("Measurement blocked: perform Z Approach before scanning.");
      return;
    }

    if (state.runningRaster) {
      log("Measurement already running.");
      return;
    }

    state.runningRaster = true;
    state.runToken += 1;
    const token = state.runToken;

    setText("measurement-status", "running");
    log("Measurement started: fixed-distance line scan → Y step → topography accumulation.");

    try {
      const yPoints = Number(byId("scan-y-points").value);

      while (state.runningRaster && token === state.runToken && state.currentLineIndex < yPoints) {
        await stepOneLine({ token });
        await new Promise((resolve) => setTimeout(resolve, 80));
      }

      if (token !== state.runToken) {
        return;
      }

      if (state.currentLineIndex >= yPoints) {
        setText("measurement-status", "complete");
        log("Measurement complete.");
      }
    } catch (error) {
      if (token === state.runToken) {
        setText("measurement-status", "error");
        log(`Measurement failed: ${error.message}`);
      }
    } finally {
      if (token === state.runToken) {
        state.runningRaster = false;
      }
    }
  }

  function lineValues(line, variant) {
    if (!line) return [];

    const values = line.points.map((p) => p.z_feedback);

    if (variant === "x-minus" || variant === "y-minus") {
      return [...values].reverse();
    }

    if (variant === "y-plus" || variant === "y-minus") {
      return values.map((value, index) => value + 0.02 * Math.sin(index / 2));
    }

    return values;
  }

  function drawLine(line, canvasId, variant, title) {
    const canvas = byId(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;

    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = "#020617";
    ctx.fillRect(0, 0, w, h);

    if (!line) {
      ctx.fillStyle = "#9ca3af";
      ctx.font = "16px Segoe UI";
      ctx.fillText("No line scan yet.", 18, 35);
      return;
    }

    const values = lineValues(line, variant);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = Math.max(max - min, 1e-9);

    ctx.strokeStyle = "#38bdf8";
    ctx.lineWidth = 3;
    ctx.beginPath();

    values.forEach((v, i) => {
      const x = (i / Math.max(values.length - 1, 1)) * (w - 40) + 20;
      const y = h - 24 - ((v - min) / range) * (h - 55);

      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });

    ctx.stroke();

    ctx.fillStyle = "#e5e7eb";
    ctx.font = "15px Segoe UI";
    ctx.fillText(title, 18, 24);
  }

  function drawTopography(canvasId, variant, title) {
    const canvas = byId(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;

    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = "#020617";
    ctx.fillRect(0, 0, w, h);

    if (state.rasterLines.length === 0) {
      ctx.fillStyle = "#9ca3af";
      ctx.font = "16px Segoe UI";
      ctx.fillText("No topography lines yet.", 18, 35);
      return;
    }

    const rows = variant.includes("y-minus") ? [...state.rasterLines].reverse() : state.rasterLines;
    const allHeights = rows.flatMap((line) => line.points.map((p) => p.surface_height));
    const min = Math.min(...allHeights);
    const max = Math.max(...allHeights);
    const range = Math.max(max - min, 1e-9);

    const xPoints = rows[0].points.length;
    const yLines = Number(byId("scan-y-points").value);
    const cellW = w / xPoints;
    const cellH = h / yLines;

    rows.forEach((line, rowIndex) => {
      let points = line.points;
      if (variant.includes("x-minus")) points = [...points].reverse();

      points.forEach((point, colIndex) => {
        const normalized = (point.surface_height - min) / range;
        const hue = 250 - normalized * 190;
        const light = 25 + normalized * 35;
        ctx.fillStyle = `hsl(${hue}, 85%, ${light}%)`;
        ctx.fillRect(colIndex * cellW, rowIndex * cellH, Math.ceil(cellW), Math.ceil(cellH));
      });
    });

    ctx.fillStyle = "#e5e7eb";
    ctx.font = "15px Segoe UI";
    ctx.fillText(`${title}: ${state.rasterLines.length}/${yLines} lines`, 18, 24);
  }

  function redrawAll() {
    const latestLine = state.rasterLines[state.rasterLines.length - 1];

    drawLine(latestLine, "line-x-plus-canvas", "x-plus", "X+ line scan");
    drawLine(latestLine, "line-x-minus-canvas", "x-minus", "X- line scan");
    drawLine(latestLine, "line-y-plus-canvas", "y-plus", "Y+ line scan");
    drawLine(latestLine, "line-y-minus-canvas", "y-minus", "Y- line scan");
    drawLine(latestLine, "live-line-canvas", "x-plus", "Live X+ line scan");

    drawTopography("topography-x-plus-canvas", "x-plus", "X+ topography");
    drawTopography("topography-x-minus-canvas", "x-minus", "X- topography");
    drawTopography("topography-y-plus-canvas", "y-plus", "Y+ topography");
    drawTopography("topography-y-minus-canvas", "y-minus", "Y- topography");
    drawTopography("live-topography-canvas", "x-plus", "Live topography");
    drawTopography("live-topography-x-plus-canvas", "x-plus", "Live X+ topography");
    drawTopography("live-topography-x-minus-canvas", "x-minus", "Live X- topography");
  }

  window.SPMRaster = {
    checkScanProfile,
    defaultCenter,
    markApproachReady,
    resetRaster,
    stepOneLine: () => stepOneLine({ manual: true }),
    runRasterSimulation,
    pauseRaster,
    stopRaster,
    redrawAll
  };
})();
