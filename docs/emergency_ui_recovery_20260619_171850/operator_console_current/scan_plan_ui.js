(function(){
  "use strict";

  function el(tag, text, cls){
    const n=document.createElement(tag);
    if(text!==undefined) n.textContent=text;
    if(cls) n.className=cls;
    return n;
  }

  function field(label, id, value){
    const wrap=el("label", "", "spm-plan-field");
    const span=el("span", label);
    const input=document.createElement("input");
    input.id=id;
    input.value=value;
    input.type="number";
    input.step="any";
    wrap.appendChild(span);
    wrap.appendChild(input);
    return wrap;
  }

  async function api(url){
    const r=await fetch(url);
    return await r.json();
  }

  function value(id){ return document.getElementById(id).value; }

  async function calculatePlan(out){
    const qs=new URLSearchParams({
      x_min:value("spm-plan-x-min"),
      x_max:value("spm-plan-x-max"),
      y_min:value("spm-plan-y-min"),
      y_max:value("spm-plan-y-max"),
      nx:value("spm-plan-nx"),
      ny:value("spm-plan-ny"),
      surface_z:value("spm-plan-surface-z"),
      clearance_um:value("spm-plan-clearance-um"),
      seconds_per_point:value("spm-plan-sec-point"),
      mode:document.getElementById("spm-plan-mode").value
    });

    out.textContent="Calculating scan plan...";
    const json=await api("/api/scan/plan?"+qs.toString());

    if(!json.ok){
      out.textContent="BLOCKED:\n"+(json.errors||[]).join("\n");
      return;
    }

    const s=json.summary;
    out.textContent =
      "OK SCAN PLAN\n" +
      "Mode: " + s.mode + "\n" +
      "Scan area: " + s.x_range_mm.toFixed(3) + " mm x " + s.y_range_mm.toFixed(3) + " mm\n" +
      "Resolution: " + s.nx + " x " + s.ny + " points\n" +
      "Pixel pitch: X " + s.x_step_um.toFixed(1) + " µm, Y " + s.y_step_um.toFixed(1) + " µm\n" +
      "Prusa executable resolution: X/Y 10.0 µm, Z 2.5 µm\n" +
      "Target Z: " + s.target_z_mm.toFixed(4) + " mm; rounded " + s.rounded_target_z_mm.toFixed(4) + " mm\n" +
      "Images: " + s.image_count + "\n" +
      "Total points: " + s.total_points + "\n" +
      "Estimated time: " + (s.estimated_seconds/60).toFixed(1) + " min\n" +
      "Directions: " + json.directions.join(", ");
  }

  function install(){
    if(document.getElementById("spm-scan-plan-panel")) return;

    const panel=el("section", "", "spm-card");
    panel.id="spm-scan-plan-panel";

    panel.appendChild(el("h2", "SPM Scan Planner"));
    panel.appendChild(el("p", "Calculates scan size, pixel pitch, Prusa-rounded motion resolution, point count, directions, and estimated time. No hardware movement."));

    const grid=el("div", "", "spm-plan-grid");
    grid.appendChild(field("X min mm", "spm-plan-x-min", "124.0"));
    grid.appendChild(field("X max mm", "spm-plan-x-max", "126.0"));
    grid.appendChild(field("Y min mm", "spm-plan-y-min", "104.0"));
    grid.appendChild(field("Y max mm", "spm-plan-y-max", "106.0"));
    grid.appendChild(field("X points", "spm-plan-nx", "11"));
    grid.appendChild(field("Y points", "spm-plan-ny", "11"));
    grid.appendChild(field("Surface Z mm", "spm-plan-surface-z", "55.0"));
    grid.appendChild(field("Clearance µm", "spm-plan-clearance-um", "500"));
    grid.appendChild(field("Seconds/point", "spm-plan-sec-point", "2.0"));

    const mode=document.createElement("select");
    mode.id="spm-plan-mode";
    for(const m of ["four_image","x_fast","y_fast"]){
      const opt=document.createElement("option");
      opt.value=m; opt.textContent=m;
      mode.appendChild(opt);
    }
    const modeWrap=el("label", "", "spm-plan-field");
    modeWrap.appendChild(el("span", "Mode"));
    modeWrap.appendChild(mode);
    grid.appendChild(modeWrap);

    panel.appendChild(grid);

    const btn=el("button", "CALCULATE SCAN PLAN");
    const out=el("pre", "No scan plan calculated yet.", "spm-plan-output");
    btn.onclick=function(){ calculatePlan(out); };

    panel.appendChild(btn);
    panel.appendChild(out);

    const main=document.querySelector("main") || document.body;
    main.appendChild(panel);
  }

  document.addEventListener("DOMContentLoaded", install);
})();
