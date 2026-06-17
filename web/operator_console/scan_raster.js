(function () {
  "use strict";

  const state = {
    rasterLines: [],
    currentLineIndex: 0,
    runningRaster: false,
    approachReady: false
  };

  function byId(id) {
    return document.getElementById(id);
  }

  function log(message) {
    if (window.SPMConsoleLog) window.SPMConsoleLog(message);
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
    byId("measurement-status").textContent = "centered";
    log("Default Center requested: future hardware phase will move XY to the configured center.");
  }

  function markApproachReady() {
    state.approachReady = true;
    byId("approach-status").textContent = "ready";
    log("Z approach marked ready in simulation. Real Z approach will be connected in a later module.");
  }

  function pauseRaster() {
    state.runningRaster = false;
    byId("measurement-status").textContent = "paused";
    log("Measurement paused.");
  }

  function stopRaster() {
    state.runningRaster = false;
    byId("measurement-status").textContent = "stopped";
    log("Measurement stopped.");
  }

  function resetRaster() {
    state.rasterLines = [];
    state.currentLineIndex = 0;
    state.runningRaster = false;

    byId("line-status").textContent = "0 / 0";
    byId("topography-status").textContent = "empty";
    byId("line-json").textContent = "No line scan yet.";
    byId("measurement-status").textContent = "idle";

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

  async function stepOneLine() {
    const yPoints = Number(byId("scan-y-points").value);

    if (state.currentLineIndex >= yPoints) {
      log("Raster complete; no more Y lines.");
      byId("measurement-status").textContent = "complete";
      return;
    }

    const line = await fetchScanLine(state.currentLineIndex);
    state.rasterLines.push(line);
    state.currentLineIndex += 1;

    const latestPoint = line.points[Math.floor(line.points.length / 2)];
    byId("z-readout").textContent = `${latestPoint.z_feedback.toFixed(3)} mm`;

    byId("line-status").textContent = `${state.currentLineIndex} / ${line.line_count}`;
    byId("topography-status").textContent = `${state.rasterLines.length} lines`;
    byId("line-json").textContent = JSON.stringify(line, null, 2);

    redrawAll();
    log(`Line ${line.line_index + 1}/${line.line_count} scanned at Y=${line.y}; direction=${line.direction}.`);
  }

  async function runRasterSimulation() {
    if (!state.approachReady) {
      log("Measurement blocked: perform Z Approach first.");
      byId("measurement-status").textContent = "blocked: approach first";
      return;
    }

    if (state.runningRaster) {
      log("Measurement already running.");
      return;
    }

    state.runningRaster = true;
    byId("measurement-status").textContent = "running";
    log("Measurement started: fixed-distance line scan → Y step → topography accumulation.");

    try {
      const yPoints = Number(byId("scan-y-points").value);

      while (state.runningRaster && state.currentLineIndex < yPoints) {
        await stepOneLine();
        await new Promise((resolve) => setTimeout(resolve, 80));
      }

      if (state.currentLineIndex >= yPoints) {
        byId("measurement-status").textContent = "complete";
        log("Measurement complete.");
      }
    } catch (error) {
      byId("measurement-status").textContent = "error";
      log(`Measurement failed: ${error.message}`);
    } finally {
      state.runningRaster = false;
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
  }

  window.SPMRaster = {
    checkScanProfile,
    defaultCenter,
    markApproachReady,
    resetRaster,
    stepOneLine,
    runRasterSimulation,
    pauseRaster,
    stopRaster,
    redrawAll
  };
})();
