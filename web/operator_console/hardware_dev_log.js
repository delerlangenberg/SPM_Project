(function () {
  "use strict";

  const sessionId = "WEB_" + new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14) + "_" + Math.random().toString(16).slice(2, 8).toUpperCase();
  const buffer = [];

  function nowStamp() {
    const d = new Date();
    return d.toLocaleTimeString() + "." + String(d.getMilliseconds()).padStart(3, "0");
  }

  function findLogTarget() {
    const selectors = [
      "#live-log",
      "#liveLog",
      "#system-log",
      "#systemLog",
      "#log",
      "#event-log",
      "#eventLog",
      ".live-log",
      ".system-log",
      ".event-log",
      "[data-live-log]",
      "textarea",
      "pre"
    ];

    for (const selector of selectors) {
      const el = document.querySelector(selector);
      if (el) return el;
    }

    let panel = document.getElementById("spm-hardware-dev-log");
    if (!panel) {
      panel = document.createElement("pre");
      panel.id = "spm-hardware-dev-log";
      panel.style.whiteSpace = "pre-wrap";
      panel.style.maxHeight = "45vh";
      panel.style.overflow = "auto";
      panel.style.border = "1px solid #777";
      panel.style.padding = "0.75rem";
      panel.style.margin = "1rem";
      panel.textContent = "";
      document.body.appendChild(panel);
    }
    return panel;
  }

  function appendToElement(el, line) {
    if (!el) return;

    if ("value" in el && (el.tagName || "").toLowerCase() === "textarea") {
      el.value += line + "\n";
      el.scrollTop = el.scrollHeight;
      return;
    }

    if ((el.tagName || "").toLowerCase() === "pre") {
      el.textContent += line + "\n";
      el.scrollTop = el.scrollHeight;
      return;
    }

    const div = document.createElement("div");
    div.textContent = line;
    el.appendChild(div);
    el.scrollTop = el.scrollHeight;
  }

  function hwLog(level, event, details) {
    const cleanDetails = details || {};
    const kv = Object.keys(cleanDetails)
      .sort()
      .map((k) => `${k}=${String(cleanDetails[k]).replace(/\n/g, "\\n")}`)
      .join(" ");

    const line = `[${nowStamp()}] [${String(level).toUpperCase()}] [${event}] web_session=${sessionId}${kv ? " " + kv : ""}`;
    buffer.push(line);

    try {
      localStorage.setItem("spmHardwareDevLog", buffer.join("\n"));
    } catch (err) {
      // Ignore storage quota/privacy errors.
    }

    appendToElement(findLogTarget(), line);
    return line;
  }

  function installToolbar() {
    if (document.getElementById("spm-hardware-log-toolbar")) return;

    const bar = document.createElement("div");
    bar.id = "spm-hardware-log-toolbar";
    bar.style.position = "fixed";
    bar.style.right = "12px";
    bar.style.bottom = "12px";
    bar.style.zIndex = "99999";
    bar.style.display = "flex";
    bar.style.gap = "8px";
    bar.style.background = "rgba(0,0,0,0.75)";
    bar.style.color = "white";
    bar.style.padding = "8px";
    bar.style.borderRadius = "8px";
    bar.style.fontFamily = "system-ui, sans-serif";
    bar.style.fontSize = "12px";

    const download = document.createElement("button");
    download.textContent = "Download hardware log";
    download.type = "button";
    download.onclick = function () {
      const text = buffer.join("\n") + "\n";
      const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `spm_hardware_live_log_${sessionId}.txt`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      hwLog("INFO", "frontend_log_downloaded", { lines: buffer.length });
    };

    const clear = document.createElement("button");
    clear.textContent = "Clear live log";
    clear.type = "button";
    clear.onclick = function () {
      buffer.length = 0;
      try {
        localStorage.removeItem("spmHardwareDevLog");
      } catch (err) {
        // Ignore.
      }
      const el = findLogTarget();
      if (el) {
        if ("value" in el && (el.tagName || "").toLowerCase() === "textarea") el.value = "";
        else el.textContent = "";
      }
      hwLog("INFO", "frontend_log_cleared", {});
    };

    bar.appendChild(download);
    bar.appendChild(clear);
    document.body.appendChild(bar);
  }

  function summarizeJson(json) {
    if (!json || typeof json !== "object") return {};
    const out = {};
    for (const key of ["ok", "ready", "powered", "system_powered", "mode", "message", "port", "machine_type", "position", "temperature", "dev_log_file", "dev_log_path_txt"]) {
      if (json[key] !== undefined && json[key] !== null && String(json[key]).length < 300) {
        out[key] = json[key];
      }
    }
    if (json.hardware && typeof json.hardware === "object") {
      for (const key of ["port", "machine_type", "position", "temperature", "dev_log_path_txt"]) {
        if (json.hardware[key] !== undefined && String(json.hardware[key]).length < 300) {
          out["hardware_" + key] = json.hardware[key];
        }
      }
    }
    return out;
  }

  const originalFetch = window.fetch;
  window.fetch = async function () {
    const url = arguments[0];
    const opts = arguments[1] || {};
    const label = typeof url === "string" ? url : (url && url.url) || "unknown";

    if (String(label).includes("/api/")) {
      hwLog("API", "request_start", { method: opts.method || "GET", url: label });
    }

    try {
      const response = await originalFetch.apply(this, arguments);

      if (String(label).includes("/api/")) {
        hwLog("API", "response_status", { url: label, status: response.status, ok: response.ok });

        const clone = response.clone();
        clone.json().then((json) => {
          hwLog("API", "response_json_summary", summarizeJson(json));

          if (Array.isArray(json.log_lines)) {
            for (const line of json.log_lines) {
              hwLog("BACKEND", "log_line", { text: line });
            }
          }

          if (json.hardware && Array.isArray(json.hardware.log_lines)) {
            for (const line of json.hardware.log_lines) {
              hwLog("BACKEND", "hardware_log_line", { text: line });
            }
          }
        }).catch(() => {
          clone.text().then((text) => {
            hwLog("API", "response_text", { url: label, text: text.slice(0, 500) });
          }).catch(() => {});
        });
      }

      return response;
    } catch (err) {
      if (String(label).includes("/api/")) {
        hwLog("FAIL", "request_failed", { url: label, error: err && err.message ? err.message : String(err) });
      }
      throw err;
    }
  };

  window.spmHardwareDevLog = hwLog;

  document.addEventListener("DOMContentLoaded", function () {
    installToolbar();
    hwLog("INFO", "hardware_dev_log_ready", {
      purpose: "share_this_live_log_for_hardware_testing",
      session: sessionId
    });
  });
})();
