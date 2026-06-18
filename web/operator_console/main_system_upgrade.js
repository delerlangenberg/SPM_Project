
(function () {
  "use strict";

  const state = {
    connected: false,
    safeRetracted: true,
    appliedPort: localStorage.getItem("spmAppliedPort") || "",
    appliedMode: localStorage.getItem("spmAppliedMode") || "hardware_readonly"
  };

  function log(level, event, details) {
    if (window.spmHardwareDevLog) {
      window.spmHardwareDevLog(level, event, details || {});
    } else {
      console.log("[SPM]", level, event, details || {});
    }
  }

  function api(path) {
    log("API", "main_system_request", { path });
    return fetch(path)
      .then((r) => r.json())
      .then((json) => {
        log("API", "main_system_response", {
          path,
          ok: json.ok,
          status: json.status,
          mode: json.mode,
          message: json.message,
          port: json.port,
          position: json.position,
          safe_retracted: json.safe_retracted
        });
        return json;
      });
  }

  function css(el, obj) {
    Object.assign(el.style, obj);
    return el;
  }

  function findMainSystemPanel() {
    const all = Array.from(document.querySelectorAll("section, aside, article, div"));
    const scored = all
      .filter((el) => {
        const txt = String(el.textContent || "");
        return txt.includes("Main System") && (
          txt.includes("ON") || txt.includes("OFF") || txt.includes("STATUS") || txt.includes("CLOSE")
        );
      })
      .sort((a, b) => String(a.textContent || "").length - String(b.textContent || "").length);

    return scored[0] || document.querySelector("main") || document.body;
  }

  function hideLegacyMainSystemControls(panel) {
    const all = Array.from(panel.querySelectorAll("button, select, label, section, article, aside, div"));

    for (const el of all) {
      if (el.id === "spm-main-system-final-controls") continue;
      if (el.closest && el.closest("#spm-main-system-final-controls")) continue;

      const txt = String(el.textContent || "").trim();
      const low = txt.toLowerCase();

      const legacyButton =
        el.tagName === "BUTTON" &&
        ["on", "off", "status", "close", "connect", "disconnect", "safe retract / confirm", "apply"].includes(low);

      const legacyInfo =
        txt.includes("SPM Prusa MK4S") ||
        low.includes("powered") ||
        low.includes("system control:") ||
        low.includes("connection port") ||
        low.includes("operating mode");

      const legacySelect = el.tagName === "SELECT";

      if (legacyButton || legacyInfo || legacySelect) {
        el.style.display = "none";
      }
    }
  }

  function makeButton(id, text, kind) {
    const btn = document.createElement("button");
    btn.id = id;
    btn.type = "button";
    btn.textContent = text;

    const base = {
      width: "100%",
      minHeight: "42px",
      borderRadius: "10px",
      color: "#e5f2ff",
      fontWeight: "850",
      letterSpacing: "0.04em",
      cursor: "pointer",
      border: "1px solid rgba(148,163,184,0.50)",
      boxShadow: "inset 0 1px 0 rgba(255,255,255,0.08)"
    };

    if (kind === "connect") {
      base.background = "linear-gradient(180deg,#0f766e,#115e59)";
      base.border = "1px solid #2dd4bf";
    } else if (kind === "disconnect") {
      base.background = "linear-gradient(180deg,#991b1b,#7f1d1d)";
      base.border = "1px solid #f87171";
    } else {
      base.background = "linear-gradient(180deg,#1e3a8a,#1e40af)";
      base.border = "1px solid #60a5fa";
    }

    return css(btn, base);
  }

  function makeSelect(options, value, label) {
    const select = document.createElement("select");
    select.innerHTML = options;
    select.value = value;
    select.title = label;
    select.setAttribute("aria-label", label);

    return css(select, {
      width: "100%",
      minWidth: "120px",
      minHeight: "40px",
      borderRadius: "9px",
      background: "#020617",
      color: "#e5f2ff",
      border: "1px solid rgba(148,163,184,0.60)",
      padding: "0 12px",
      fontSize: "13px",
      fontWeight: "750"
    });
  }

  function makeApplyButton(label) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = "APPLY";
    btn.title = "Apply " + label;

    return css(btn, {
      minWidth: "78px",
      minHeight: "40px",
      borderRadius: "9px",
      background: "linear-gradient(180deg,#334155,#1e293b)",
      color: "#e5f2ff",
      border: "1px solid rgba(148,163,184,0.60)",
      fontSize: "12px",
      fontWeight: "850",
      cursor: "pointer"
    });
  }

  function addSelectRow(box, select, applyButton) {
    const row = document.createElement("div");
    css(row, {
      display: "grid",
      gridTemplateColumns: "minmax(140px, 1fr) 78px",
      gap: "8px",
      alignItems: "center"
    });

    row.appendChild(select);
    row.appendChild(applyButton);
    box.appendChild(row);
  }

  function setConnectionState() {
    const connectBtn = document.getElementById("spm-main-connect-button");
    const disconnectBtn = document.getElementById("spm-main-disconnect-button");

    if (connectBtn) {
      connectBtn.disabled = state.connected;
      connectBtn.style.opacity = state.connected ? "0.45" : "1.0";
    }

    if (disconnectBtn) {
      disconnectBtn.disabled = !state.connected;
      disconnectBtn.style.opacity = state.connected ? "1.0" : "0.45";
    }
  }

  function selectedPortParam() {
    return state.appliedPort ? "&port=" + encodeURIComponent(state.appliedPort) : "";
  }

  async function connect() {
    state.safeRetracted = false;
    const mode = state.appliedMode || "hardware_readonly";
    const json = await api("/api/system/on?mode=" + encodeURIComponent(mode) + selectedPortParam());
    state.connected = Boolean(json.connected || json.powered || json.ready || json.ok);
    state.safeRetracted = Boolean(json.safe_retracted);
    setConnectionState();
    return json;
  }

  async function safeRetract() {
    const json = await api("/api/system/safe-retract");
    state.safeRetracted = Boolean(json.ok && json.safe_retracted !== false);
    setConnectionState();
    return json;
  }

  async function disconnect() {
    if (!state.connected) {
      log("INFO", "disconnect_ignored_not_connected", {});
      return { ok: true, status: "already_disconnected" };
    }

    if (!state.safeRetracted) {
      log("INFO", "disconnect_runs_safe_retract_first", {});
      const retract = await safeRetract();
      if (!retract.ok) {
        alert("Disconnect blocked: safe retract was not confirmed. Check the live log.");
        return retract;
      }
    }

    const json = await api("/api/system/disconnect");
    state.connected = false;
    state.safeRetracted = true;
    setConnectionState();
    return json;
  }

  function installFinalMainSystem() {
    const panel = findMainSystemPanel();

    if (document.getElementById("spm-main-system-final-controls")) {
      setConnectionState();
      return;
    }

    hideLegacyMainSystemControls(panel);

    const box = document.createElement("div");
    box.id = "spm-main-system-final-controls";
    css(box, {
      display: "grid",
      gap: "10px",
      marginTop: "12px",
      padding: "10px",
      borderRadius: "14px",
      background: "linear-gradient(180deg, rgba(15,23,42,0.68), rgba(15,23,42,0.36))",
      border: "1px solid rgba(148,163,184,0.24)"
    });

    const title = document.createElement("div");
    title.textContent = "Connection Control";
    css(title, {
      color: "#93c5fd",
      fontSize: "12px",
      fontWeight: "850",
      textTransform: "uppercase",
      letterSpacing: "0.08em"
    });
    box.appendChild(title);

    const connectBtn = makeButton("spm-main-connect-button", "CONNECT", "connect");
    connectBtn.onclick = connect;
    box.appendChild(connectBtn);

    const portSelect = makeSelect(
      '<option value="">AUTO-DETECT</option>' + Array.from({ length: 10 }, (_, i) => `<option value="COM${i + 1}">COM${i + 1}</option>`).join(""),
      state.appliedPort,
      "Connection Port"
    );
    const portApply = makeApplyButton("Connection Port");
    portApply.onclick = async function () {
      state.appliedPort = portSelect.value;
      localStorage.setItem("spmAppliedPort", state.appliedPort);
      await api("/api/system/config/port?port=" + encodeURIComponent(state.appliedPort));
    };
    addSelectRow(box, portSelect, portApply);

    const modeSelect = makeSelect(
      [
        '<option value="hardware_readonly">READ-ONLY</option>',
        '<option value="dry_run">DRY-RUN</option>',
        '<option value="hardware_motion" disabled>MOTION LOCKED</option>'
      ].join(""),
      state.appliedMode,
      "Operating Mode"
    );
    const modeApply = makeApplyButton("Operating Mode");
    modeApply.onclick = async function () {
      state.appliedMode = modeSelect.value;
      localStorage.setItem("spmAppliedMode", state.appliedMode);
      await api("/api/system/config/mode?mode=" + encodeURIComponent(state.appliedMode));
    };
    addSelectRow(box, modeSelect, modeApply);

    const actionRow = document.createElement("div");
    css(actionRow, {
      display: "grid",
      gridTemplateColumns: "1fr 1fr",
      gap: "8px",
      alignItems: "center"
    });

    const retractBtn = makeButton("spm-main-safe-retract-button", "SAFE RETRACT", "blue");
    retractBtn.onclick = safeRetract;

    const disconnectBtn = makeButton("spm-main-disconnect-button", "DISCONNECT", "disconnect");
    disconnectBtn.onclick = disconnect;

    actionRow.appendChild(retractBtn);
    actionRow.appendChild(disconnectBtn);
    box.appendChild(actionRow);

    panel.appendChild(box);
    setConnectionState();

    log("UI", "main_system_final_layout_ready", {
      layout: "connect_port_mode_retract_disconnect",
      close_location: "browser_or_global_page_close_not_main_system",
      port: state.appliedPort || "AUTO-DETECT",
      mode: state.appliedMode
    });
  }

  window.addEventListener("beforeunload", function (ev) {
    if (state.connected && !state.safeRetracted) {
      const msg = "Disconnect first. Safe retract must be confirmed before closing.";
      log("BLOCK", "browser_close_blocked_disconnect_first", { message: msg });
      ev.preventDefault();
      ev.returnValue = msg;
      return msg;
    }
  });

  document.addEventListener("DOMContentLoaded", function () {
    setTimeout(installFinalMainSystem, 250);
  });
})();
