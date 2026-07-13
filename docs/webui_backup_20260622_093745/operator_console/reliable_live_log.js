(function () {
  "use strict";

  if (window.SPM_RELIABLE_LOG_INSTALLED) return;
  window.SPM_RELIABLE_LOG_INSTALLED = true;

  const MAX_LINES = 700;
  const memory = [];

  function stamp() {
    return new Date().toLocaleTimeString();
  }

  function body() {
    return document.getElementById("operator-log");
  }

  function render() {
    const el = body();
    if (!el) return;
    el.innerHTML = "";
    for (const item of memory.slice(-MAX_LINES)) {
      const row = document.createElement("div");
      row.className = "log-line";
      row.textContent = item;
      el.appendChild(row);
    }
    el.scrollTop = el.scrollHeight;
  }

  function line(message) {
    const clean = String(message || "").trim();
    if (!clean) return;
    memory.push(`[${stamp()}] ${clean}`);
    if (memory.length > MAX_LINES) memory.splice(0, memory.length - MAX_LINES);
    render();
  }

  function payload(json) {
    if (!json) return;
    if (json.message) line(`MESSAGE ${json.message}`);
    if (json.status || json.mode) line(`STATE status=${json.status || ""} mode=${json.mode || ""} ok=${json.ok}`);
    if (json.port || json.position) line(`HW port=${json.port || ""} position=${json.position || ""}`);

    const lines = [];
    if (Array.isArray(json.log_lines)) lines.push(...json.log_lines);
    if (json.hardware && Array.isArray(json.hardware.log_lines)) lines.push(...json.hardware.log_lines);

    const seen = new Set();
    for (const entry of lines) {
      const text = String(entry || "").trim();
      if (!text || seen.has(text)) continue;
      seen.add(text);
      line(text);
    }
  }

  function download() {
    const blob = new Blob([memory.join("\n") + "\n"], { type: "text/plain" });
    const a = document.createElement("a");
    const ts = new Date().toISOString().replace(/[:.]/g, "-");
    a.href = URL.createObjectURL(blob);
    a.download = `spm_live_log_${ts}.txt`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }

  function clear() {
    memory.length = 0;
    line("Log cleared.");
  }

  function openTab() {
    localStorage.setItem("spmLiveLogSnapshot", memory.join("\n"));
    window.open("/?window=log-window&standalone=1", "_blank", "noopener,noreferrer");
  }

  function hydrateStandaloneLogWindow() {
    const params = new URLSearchParams(window.location.search);
    if (params.get("window") !== "log-window") return;
    const snapshot = localStorage.getItem("spmLiveLogSnapshot") || "";
    const out = document.getElementById("external-log-snapshot");
    if (out) out.textContent = snapshot ? snapshot + "\n" : "[log snapshot empty]\n";
  }

  window.spmReliableLogLine = line;
  window.spmVisibleLogLine = line;
  window.spmVisibleLogPayload = payload;
  window.spmReliableLogDownload = download;
  window.spmReliableLogClear = clear;
  window.spmReliableLogOpenTab = openTab;
  window.spmReliableLogText = () => memory.join("\n");

  const oldFetch = window.fetch.bind(window);
  window.fetch = function (input, init) {
    const url = typeof input === "string" ? input : (input && input.url) || "";
    const isApi = url.includes("/api/");
    const started = performance.now();
    if (isApi) line(`REQUEST ${url}`);

    return oldFetch(input, init)
      .then((response) => {
        if (isApi) line(`RESPONSE HTTP ${response.status} ${url} ${Math.round(performance.now() - started)}ms`);
        if (isApi) response.clone().json().then(payload).catch((error) => line(`JSON READ ERROR ${error}`));
        return response;
      })
      .catch((error) => {
        if (isApi) line(`FETCH ERROR ${url} ${error}`);
        throw error;
      });
  };

  document.addEventListener("DOMContentLoaded", function () {
    line("SPM live log ready.");
    hydrateStandaloneLogWindow();
  });
})();
