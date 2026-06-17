(function () {
  "use strict";

  const state = {
    rasterLines: [],
    currentLineIndex: 0,
    runningRaster: false
  };

  function byId(id) {
    return document.getElementById(id);
  }

  function log(message) {
    if (window.SPMConsoleLog) {
      window.SPMConsoleLog(message);
    }
  }

  function getScanParams() {
    const params = {
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
    };

    return new URLSearchParams(params);
  }

  async function checkScanProfile() {
    const response = await fetch(`/api/scan/profile?${getScanParams().toString()}`);
    const payload = await response.json();

    if (payload.status === "error") {
      log(`Profile error: ${payload.message}`);
      return;
    }

    log(`Scan profile OK: ${payload.x_points} X points × ${payload.y_points} Y lines; ${payload.scan_principle}.`);
  }

  function resetRaster() {
    state.rasterLines = [];
    state.currentLineIndex = 0;
    state.runningRaster = false;

    byId("line-status").textContent = "0 / 0";
    byId("topography-status").textContent = "empty";
    byId("line-json").textContent = "No line scan yet.";

    redrawAll();
    log("Raster reset.");
  }

  async function fetchScanLine(lineIndex) {
    const params = getScanParams();
    params.set("line_index", String(lineIndex));

    const response = await fetch(`/api/scan/line?${params.toString()}`);
    const payload = await response.json();

    if (payload.status === "error") {
      throw new Error(payload.message);
    }

    return payload;
  }

  async function stepOneLine() {
    const yPoints = Number(byId("scan-y-points").value);

    if (state.currentLineIndex >= yPoints) {
      log("Raster complete; no more Y lines.");
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

    drawLine(line, "line-canvas");
    drawLine(line, "live-line-canvas");
    drawTopography("topography-canvas");
    drawTopography("live-topography-canvas");

    log(`Line ${line.line_index + 1}/${line.line_count} scanned at Y=${line.y}; direction=${line.direction}.`);
  }

  async function runRasterSimulation() {
    if (state.runningRaster) {
      log("Raster simulation already running.");
      return;
    }

    state.runningRaster = true;
    log("Raster simulation started: X line scan → Y step → accumulated topography.");

    try {
      const yPoints = Number(byId("scan-y-points").value);

      while (state.runningRaster && state.currentLineIndex < yPoints) {
        await stepOneLine();
        await new Promise((resolve) => setTimeout(resolve, 80));
      }

      log("Raster simulation complete.");
    } catch (error) {
      log(`Raster simulation failed: ${error.message}`);
    } finally {
      state.runningRaster = false;
    }
  }

  function drawLine(line, canvasId) {
    const canvas = byId(canvasId);
    if (!canvas || !line) return;

    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;

    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = "#020617";
    ctx.fillRect(0, 0, w, h);

    const values = line.points.map((p) => p.z_feedback);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = Math.max(max - min, 1e-9);

    ctx.strokeStyle = "#38bdf8";
    ctx.lineWidth = 3;
    ctx.beginPath();

    values.forEach((v, i) => {
      const x = (i / Math.max(values.length - 1, 1)) * (w - 40) + 20;
      const y = h - 24 - ((v - min) / range) * (h - 48);

      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });

    ctx.stroke();

    ctx.fillStyle = "#e5e7eb";
    ctx.font = "16px Segoe UI";
    ctx.fillText(`Line ${line.line_index + 1}/${line.line_count} · Y=${line.y} · Z feedback`, 20, 24);
  }

  function drawTopography(canvasId) {
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
      ctx.font = "18px Segoe UI";
      ctx.fillText("No topography lines yet.", 24, 40);
      return;
    }

    const allHeights = state.rasterLines.flatMap((line) => line.points.map((p) => p.surface_height));
    const min = Math.min(...allHeights);
    const max = Math.max(...allHeights);
    const range = Math.max(max - min, 1e-9);

    const xPoints = state.rasterLines[0].points.length;
    const yLines = Number(byId("scan-y-points").value);
    const cellW = w / xPoints;
    const cellH = h / yLines;

    state.rasterLines.forEach((line, rowIndex) => {
      line.points.forEach((point, colIndex) => {
        const normalized = (point.surface_height - min) / range;
        const hue = 250 - normalized * 190;
        const light = 25 + normalized * 35;
        ctx.fillStyle = `hsl(${hue}, 85%, ${light}%)`;
        ctx.fillRect(colIndex * cellW, rowIndex * cellH, Math.ceil(cellW), Math.ceil(cellH));
      });
    });

    ctx.fillStyle = "#e5e7eb";
    ctx.font = "16px Segoe UI";
    ctx.fillText(`Accumulated topography: ${state.rasterLines.length}/${yLines} Y lines`, 20, 24);
  }

  function redrawAll() {
    const latestLine = state.rasterLines[state.rasterLines.length - 1];

    if (latestLine) {
      drawLine(latestLine, "line-canvas");
      drawLine(latestLine, "live-line-canvas");
    }

    drawTopography("topography-canvas");
    drawTopography("live-topography-canvas");
  }

  window.SPMRaster = {
    checkScanProfile,
    resetRaster,
    stepOneLine,
    runRasterSimulation,
    redrawAll
  };
})();
