
(function () {
  "use strict";

  const state = {
    connected: false,
    safeRetracted: true,
    motionVerified: false,
    appliedPort: localStorage.getItem("spmAppliedPort") || "",
    appliedMode: "hardware_readonly"
  };

  function log(level, event, details) {
    if (window.spmHardwareDevLog) {
      window.spmHardwareDevLog(level, event, details || {});
    } else {
      console.log("[SPM]", level, event, details || {});
    }
  }

  // Phase 2.2E visible live-log repair
  function visibleLogLine(line) {
    const msg = String(line || "").trim();
    if (!msg) return;

    if (window.spmVisibleLogLine) {
      window.spmVisibleLogLine(msg);
      return;
    }

    const el = document.getElementById("operator-log");
    if (!el) return;
    const row = document.createElement("div");
    row.className = "log-line";
    row.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
    el.appendChild(row);
    el.scrollTop = el.scrollHeight;
  }

  function visibleLogPayload(json) {
    const lines = [];
    if (json && Array.isArray(json.log_lines)) lines.push(...json.log_lines);
    if (json && json.hardware && Array.isArray(json.hardware.log_lines)) {
      lines.push(...json.hardware.log_lines);
    }

    const seen = new Set();
    for (const line of lines) {
      const msg = String(line || "").trim();
      if (!msg || seen.has(msg)) continue;
      seen.add(msg);
      visibleLogLine(msg);
    }
  }

  function api(path) {
    log("API", "main_system_request", { path });
    return fetch(path)
      .then((r) => r.json())
      .then((json) => {
        if (window.spmVisibleLogPayload) window.spmVisibleLogPayload(json);
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
        updateHardwareState(json);
        
        resetActionButtons();
        return json;
      })
      .catch((err) => {
        resetActionButtons();
        setConnectionState();
        log("ERROR", "api_failed", { path, error: String(err) });
        throw err;
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
      height: "42px",
      minHeight: "42px",
      maxHeight: "42px",
      borderRadius: "10px",
      color: "#e5f2ff",
      whiteSpace: "nowrap",
      overflow: "hidden",
      textOverflow: "ellipsis",
      fontSize: "12px",
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

  // Phase 2.2E stable action-button reset
  function resetActionButtons() {
    const retract = document.getElementById("spm-main-safe-retract-button");
    const standby = document.getElementById("spm-main-safe-standby-button");
    const diagnose = document.getElementById("spm-main-diagnostics-button");

    if (retract) {
      retract.textContent = "Z SAFE RETRACT";
      retract.disabled = false;
    }

    if (standby) {
      standby.textContent = "SAFE STANDBY";
      standby.disabled = false;
    }

    if (diagnose) {
      diagnose.textContent = "DIAGNOSE";
      diagnose.disabled = false;
    }
  }

  function setConnectionState() {
    const connectBtn = document.getElementById("spm-main-connect-button");
    const disconnectBtn = document.getElementById("spm-main-disconnect-button");

    if (connectBtn) {
      connectBtn.textContent = state.connected ? "CONNECTED" : "CONNECT";
      connectBtn.disabled = state.connected;
      connectBtn.style.opacity = state.connected ? "0.45" : "1.0";
    }

    if (disconnectBtn) {
      disconnectBtn.textContent = "DISCONNECT";
      disconnectBtn.disabled = !state.connected;
      disconnectBtn.style.opacity = state.connected ? "1.0" : "0.45";
    }
  }

  function updateHardwareState(json) {
    if (!json) return;
    const status = document.getElementById("spm-main-hardware-state");
    if (!status) return;

    const diag = json.position_diagnostic;
    const verified = Boolean(json.motion_verified || (diag && diag.ok));
    state.motionVerified = verified;

    const pos = json.position || (json.hardware && json.hardware.position) || "";
    const lines = [];
    lines.push(`Connection: ${json.connected || json.ok ? "online" : "not ready"}`);
    lines.push(`Motion state: ${verified ? "verified" : "blocked / needs sync"}`);
    if (pos) lines.push(`Position: ${pos}`);
    if (diag && Array.isArray(diag.mismatches) && diag.mismatches.length) {
      lines.push(...diag.mismatches.slice(0, 3));
    } else if (diag && diag.message) {
      lines.push(diag.message);
    } else if (json.message) {
      lines.push(json.message);
    }

    status.textContent = lines.join("\n");
    status.dataset.state = verified ? "verified" : "blocked";
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
    state.motionVerified = Boolean(json.motion_verified);
    setConnectionState();
    return json;
  }

  async function diagnostics() {
    const json = await api("/api/system/diagnostics");
    state.motionVerified = Boolean(json.motion_verified);
    setConnectionState();
    return json;
  }

  async function diagnoseAndHealthTest() {
    const diagnostic = await diagnostics();
    if (!diagnostic || diagnostic.ok === false) return diagnostic;
    return healthTest("short");
  }

  async function syncPosition() {
    const msg = [
      "Sync logical position to stepper counts?",
      "",
      "This sends G92 only. It does not move the hardware.",
      "Use this after the printer reports logical coordinates that do not match Count X/Y/Z."
    ].join("\n");

    if (!window.confirm(msg)) {
      log("CANCEL", "sync_position_cancelled_by_operator", {});
      return;
    }

    const json = await api("/api/system/sync-position");
    state.motionVerified = Boolean(json.motion_verified);
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

  async function safeStandby() {
    const msg = [
      "Move hardware to Safe Standby?",
      "",
      "Target: X125 Y105 Z120.",
      "Sequence: verify M114 counts, keep/lift Z safe, center XY, park Z, verify final M114.",
      "",
      "Clear the scanner path and watch the hardware. Click OK only when it is safe to move."
    ].join("\n");

    if (!window.confirm(msg)) {
      log("CANCEL", "safe_standby_cancelled_by_operator", {});
      resetActionButtons();
      setConnectionState();
      return;
    }

    const json = await api("/api/system/safe-standby");
    state.safeRetracted = Boolean(json.ok && json.safe_retracted !== false);
    state.motionVerified = Boolean(json.ok);
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

  async function healthTest(profile = "short") {
    const msg = [
      "Phase 2.1 hardware diagnostic will run a visible XYZ axes movement test.",
      "",
      "Clear the scan range and watch the printer.",
      "The software already checks firmware identity, M114 position, Count X/Y/Z, and safe envelope before movement.",
      "Real hardware motion will be sent: X +/-10 mm, Y +/-10 mm, Z +/-10 mm.",
      "",
      "Click OK to start the movement verification."
    ].join("\n");

    if (!window.confirm(msg)) {
      log("CANCEL", "health_test_cancelled_by_operator", {});
      resetActionButtons();
      setConnectionState();
      return;
    }

    const json = await api("/api/system/health-test?confirmed=1&motion=1&profile=" + encodeURIComponent(profile));
    for (const line of (json.log_lines || [])) {
      log("HEALTH", "health_test_line", { line });
    }
    return json;
  }

  function installFinalMainSystem() {
    const panel = document.querySelector(".main-panel") || findMainSystemPanel();

    if (document.getElementById("spm-main-system-final-controls")) {
      setConnectionState();
      return;
    }

    Array.from(panel.querySelectorAll(".status-card, .main-controls, .field-stack")).forEach((el) => {
      el.style.display = "none";
    });

    const box = document.createElement("div");
    box.id = "spm-main-system-final-controls";
    css(box, {
      display: "grid",
      gap: "10px",
      marginTop: "0",
      padding: "10px",
      borderRadius: "14px",
      background: "linear-gradient(180deg, rgba(15,23,42,0.68), rgba(15,23,42,0.36))",
      border: "1px solid rgba(148,163,184,0.24)"
    });

    const title = document.createElement("div");
    title.textContent = "System Control";
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
      /* mode is not persisted; prevents stale dry-run lock */
      await api("/api/system/config/mode?mode=" + encodeURIComponent(state.appliedMode));
    };
    addSelectRow(box, modeSelect, modeApply);

    const diagnosticRow = document.createElement("div");
    css(diagnosticRow, {
      display: "grid",
      gridTemplateColumns: "1fr 1fr",
      gap: "8px",
      alignItems: "center"
    });

    const diagnoseBtn = makeButton("spm-main-diagnostics-button", "DIAGNOSE", "blue");
    diagnoseBtn.title = "Run read-only diagnostics, then the verified XYZ axes health movement test.";
    diagnoseBtn.onclick = diagnoseAndHealthTest;
    const syncBtn = makeButton("spm-main-sync-position-button", "SYNC POSITION", "blue");
    syncBtn.onclick = syncPosition;
    diagnosticRow.appendChild(diagnoseBtn);
    diagnosticRow.appendChild(syncBtn);
    box.appendChild(diagnosticRow);

    const hardwareState = document.createElement("pre");
    hardwareState.id = "spm-main-hardware-state";
    hardwareState.textContent = "Connection: not ready\nMotion state: not verified";
    css(hardwareState, {
      margin: "0",
      minHeight: "92px",
      maxHeight: "140px",
      overflow: "auto",
      whiteSpace: "pre-wrap",
      borderRadius: "9px",
      padding: "9px",
      background: "#020617",
      border: "1px solid rgba(148,163,184,0.35)",
      color: "#dbeafe",
      fontSize: "11px",
      lineHeight: "1.45"
    });
    box.appendChild(hardwareState);

    const specState = document.createElement("pre");
    specState.id = "spm-main-spec-state";
    specState.textContent = "Machine specification: loading...";
    css(specState, {
      margin: "0",
      minHeight: "112px",
      maxHeight: "160px",
      overflow: "auto",
      whiteSpace: "pre-wrap",
      borderRadius: "9px",
      padding: "9px",
      background: "#020617",
      border: "1px solid rgba(148,163,184,0.35)",
      color: "#dbeafe",
      fontSize: "11px",
      lineHeight: "1.45"
    });
    box.appendChild(specState);
    fetch("/mk4s_motion_limits.json")
      .then((r) => r.json())
      .then((limits) => {
        specState.textContent = [
          `Machine: ${limits.machine}`,
          `Physical envelope: X 0..${limits.x_build_mm} mm, Y 0..${limits.y_build_mm} mm, Z 0..${limits.z_build_mm} mm`,
          `Safe scan envelope: X ${limits.x_safe_min_mm}..${limits.x_safe_max_mm} mm, Y ${limits.y_safe_min_mm}..${limits.y_safe_max_mm} mm`,
          `Safe standby: X${limits.safe_center_x_mm} Y${limits.safe_center_y_mm} Z${limits.safe_parking_z_mm}`,
          `Motion command resolution: XY ${limits.xy_command_resolution_um} um, Z ${limits.z_command_resolution_um} um`,
          `Diagnostic speed: ${limits.recommended_xy_health_test_speed_mm_s} mm/s; scan speed ${limits.recommended_scan_speed_min_mm_s}..${limits.recommended_scan_speed_max_mm_s} mm/s`,
          "Loadcell: present on MK4S, not yet verified as scanner contact feedback."
        ].join("\n");
      })
      .catch(() => {
        specState.textContent = "Machine specification: unavailable.";
      });


    const actionRow = document.createElement("div");
    css(actionRow, {
      display: "grid",
      gridTemplateColumns: "1fr 1fr",
      gap: "8px",
      alignItems: "center"
    });

    const standbyBtn = makeButton("spm-main-safe-standby-button", "SAFE STANDBY", "blue");
    standbyBtn.title = "Repair unsafe edge positions by moving to X125 Y105 Z120 after M114/count verification.";
    standbyBtn.onclick = safeStandby;

    const retractBtn = makeButton("spm-main-safe-retract-button", "Z SAFE RETRACT", "blue");
    retractBtn.title = "Move or confirm Z only. Use Safe Standby to center XY as well.";
    retractBtn.onclick = safeRetract;

    const disconnectBtn = makeButton("spm-main-disconnect-button", "DISCONNECT", "disconnect");
    disconnectBtn.onclick = disconnect;

    actionRow.appendChild(standbyBtn);
    actionRow.appendChild(retractBtn);
    box.appendChild(actionRow);

    const disconnectRow = document.createElement("div");
    css(disconnectRow, {
      display: "grid",
      gridTemplateColumns: "1fr",
      gap: "8px"
    });
    disconnectRow.appendChild(disconnectBtn);
    box.appendChild(disconnectRow);

    const header = panel.querySelector(".panel-header");
    if (header) header.insertAdjacentElement("afterend", box);
    else panel.insertBefore(box, panel.firstChild);
    setConnectionState();

    log("UI", "main_system_final_layout_ready", {
      layout: "connect_port_mode_safe_standby_retract_disconnect",
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


  // Phase 2.2E responsive button feedback
  document.addEventListener("click", function (ev) {
    const btn = ev.target;
    if (!btn || !btn.id) return;

    if (btn.id === "spm-main-connect-button") {
      btn.textContent = "CONNECTING";
      btn.disabled = true;
    }

    if (btn.id === "spm-main-safe-retract-button") {
      btn.textContent = "CHECKING";
      btn.disabled = true;
    }

    if (btn.id === "spm-main-safe-standby-button") {
      btn.textContent = "MOVING";
      btn.disabled = true;
    }

    if (btn.id === "spm-main-disconnect-button") {
      btn.textContent = "DISCONNECT";
      btn.disabled = true;
    }

    if (btn.id === "spm-main-diagnostics-button") {
      btn.textContent = "RUNNING";
      btn.disabled = true;
    }
  }, true);

  document.addEventListener("DOMContentLoaded", function () {
    setTimeout(installFinalMainSystem, 250);
  });
})();
