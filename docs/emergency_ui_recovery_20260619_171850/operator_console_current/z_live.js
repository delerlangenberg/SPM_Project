(function () {
  "use strict";

  const state = {
    samples: []
  };

  function byId(id) {
    return document.getElementById(id);
  }

  function readSetpoint() {
    const input = byId("scan-z-setpoint");
    if (!input) return 0.10;

    const value = Number(input.value);
    return Number.isFinite(value) ? value : 0.10;
  }

  function pushSample(value) {
    state.samples.push(value);
    if (state.samples.length > 120) {
      state.samples.shift();
    }
  }

  function redraw() {
    const canvas = byId("z-live-canvas");
    if (!canvas) return;

    const setpoint = readSetpoint();
    const simulated = setpoint + 0.015 * Math.sin(Date.now() / 700);

    pushSample(simulated);

    const readout = byId("z-live-readout");
    if (readout) readout.textContent = `${simulated.toFixed(3)} mm`;

    const setpointEl = byId("z-live-setpoint");
    if (setpointEl) setpointEl.textContent = `${setpoint.toFixed(3)} mm`;

    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;

    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = "#020617";
    ctx.fillRect(0, 0, w, h);

    ctx.strokeStyle = "#64748b";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(20, h / 2);
    ctx.lineTo(w - 20, h / 2);
    ctx.stroke();

    if (state.samples.length < 2) {
      ctx.fillStyle = "#9ca3af";
      ctx.font = "16px Segoe UI";
      ctx.fillText("Z feedback live trace will appear here.", 20, 34);
      return;
    }

    const min = Math.min(...state.samples, setpoint - 0.05);
    const max = Math.max(...state.samples, setpoint + 0.05);
    const range = Math.max(max - min, 1e-9);

    ctx.strokeStyle = "#38bdf8";
    ctx.lineWidth = 3;
    ctx.beginPath();

    state.samples.forEach((value, index) => {
      const x = 20 + (index / Math.max(state.samples.length - 1, 1)) * (w - 40);
      const y = h - 24 - ((value - min) / range) * (h - 55);

      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });

    ctx.stroke();

    ctx.fillStyle = "#e5e7eb";
    ctx.font = "16px Segoe UI";
    ctx.fillText("Z feedback / fixed-distance setpoint monitor", 20, 28);
  }

  setInterval(() => {
    if (!document.hidden && !byId("live-window")?.hidden) {
      redraw();
    }
  }, 500);

  window.SPMZLive = {
    redraw
  };
})();
