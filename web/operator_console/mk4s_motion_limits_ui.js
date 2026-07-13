(function () {
  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  }

  function targetPanel() {
    return document.querySelector(".measurement-panel") ||
           document.querySelector(".xy-panel");
  }

  function format(value, suffix) {
    return `${value}${suffix || ""}`;
  }
  function renderLimits(data) {
    const panel = targetPanel();
    if (!panel || document.querySelector("#mk4s-motion-limits-card")) return;

    const card = el("div", "mk4s-limits-card");
    card.id = "mk4s-motion-limits-card";

    const title = el("h3", null, "MK4S motion limits / scan envelope");
    const note = el(
      "p",
      "mk4s-limits-note",
      "Motion command limits only. Real SPM resolution requires verified sensor feedback."
    );

    card.appendChild(title);
    card.appendChild(note);
    card.appendChild(buildGrid(data));
    panel.appendChild(card);
  }
  function buildGrid(data) {
    const grid = el("div", "mk4s-limits-grid");

    const rows = [
      ["X travel", format(data.x_build_mm, " mm")],
      ["Y travel", format(data.y_build_mm, " mm")],
      ["Z travel", format(data.z_build_mm, " mm")],
      ["Safe scan X", `${data.x_safe_min_mm}-${data.x_safe_max_mm} mm`],
      ["Safe scan Y", `${data.y_safe_min_mm}-${data.y_safe_max_mm} mm`],
      ["Safe center", `X${data.safe_center_x_mm} Y${data.safe_center_y_mm} Z${data.safe_parking_z_mm}`],
      ["XY command resolution", format(data.xy_command_resolution_um, " µm")],
      ["Z command resolution", format(data.z_command_resolution_um, " µm")],
      ["Demo scan speed", `${data.recommended_scan_speed_min_mm_s}-${data.recommended_scan_speed_max_mm_s} mm/s`],
      ["Default scan speed", format(data.recommended_scan_speed_default_mm_s, " mm/s")],
      ["Z approach default", format(data.recommended_z_approach_default_mm_s, " mm/s")],
      ["Z manual step", format(data.recommended_z_manual_step_default_mm, " mm")]
    ];

    rows.forEach(([label, value]) => {
      const item = el("div", "mk4s-limit-item");
      item.innerHTML = `<span>${label}</span><strong>${value}</strong>`;
      grid.appendChild(item);
    });

    return grid;
  }
  async function loadLimits() {
    try {
      const response = await fetch("/mk4s_motion_limits.json");
      if (!response.ok) return;
      const data = await response.json();
      renderLimits(data);
    } catch (error) {
      console.warn("MK4S limits not loaded", error);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadLimits);
  } else {
    loadLimits();
  }
})();
