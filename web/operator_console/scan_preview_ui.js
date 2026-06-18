(function(){
  "use strict";

  function el(tag, text, cls){
    const n=document.createElement(tag);
    if(text!==undefined) n.textContent=text;
    if(cls) n.className=cls;
    return n;
  }

  function val(id){
    const n=document.getElementById(id);
    return n ? n.value : "";
  }

  function currentQuery(){
    return new URLSearchParams({
      x_min:val("spm-plan-x-min"),
      x_max:val("spm-plan-x-max"),
      y_min:val("spm-plan-y-min"),
      y_max:val("spm-plan-y-max"),
      nx:val("spm-plan-nx"),
      ny:val("spm-plan-ny"),
      surface_z:val("spm-plan-surface-z"),
      clearance_um:val("spm-plan-clearance-um"),
      seconds_per_point:val("spm-plan-sec-point"),
      mode:(document.getElementById("spm-plan-mode")||{}).value || "four_image"
    });
  }

  function drawLineSvg(points){
    const svg=document.createElementNS("http://www.w3.org/2000/svg","svg");
    svg.setAttribute("viewBox","0 0 320 120");
    svg.classList.add("spm-preview-svg");

    if(!points || points.length<2){
      return svg;
    }

    const xs=points.map(p=>p.x_mm);
    const ys=points.map(p=>p.y_mm);
    const xmin=Math.min(...xs), xmax=Math.max(...xs);
    const ymin=Math.min(...ys), ymax=Math.max(...ys);

    function sx(x){ return 20 + ((x-xmin)/Math.max(0.0001,xmax-xmin))*280; }
    function sy(y){ return 100 - ((y-ymin)/Math.max(0.0001,ymax-ymin))*80; }

    const poly=document.createElementNS("http://www.w3.org/2000/svg","polyline");
    poly.setAttribute("points", points.map(p=>sx(p.x_mm)+","+sy(p.y_mm)).join(" "));
    poly.setAttribute("fill","none");
    poly.setAttribute("stroke","currentColor");
    poly.setAttribute("stroke-width","3");
    svg.appendChild(poly);

    for(const p of points){
      const c=document.createElementNS("http://www.w3.org/2000/svg","circle");
      c.setAttribute("cx",sx(p.x_mm));
      c.setAttribute("cy",sy(p.y_mm));
      c.setAttribute("r","3");
      c.setAttribute("fill","currentColor");
      svg.appendChild(c);
    }

    return svg;
  }

  function imageBox(name, summary){
    const box=el("div","","spm-image-placeholder");
    box.appendChild(el("strong",name));
    box.appendChild(el("span",summary.nx+" x "+summary.ny+" points"));
    box.appendChild(el("span","pending live data"));
    return box;
  }

  async function updatePreview(out){
    out.textContent="Loading raster preview...";
    const r=await fetch("/api/scan/plan?"+currentQuery().toString());
    const json=await r.json();

    out.innerHTML="";

    if(!json.ok){
      out.textContent="BLOCKED:\n"+(json.errors||[]).join("\n");
      return;
    }

    const s=json.summary;
    const head=el("div","","spm-preview-summary");
    head.textContent =
      "Raster preview: " + s.mode +
      " | " + s.total_points + " points" +
      " | " + s.image_count + " images" +
      " | pitch X " + s.x_step_um.toFixed(1) + " µm, Y " + s.y_step_um.toFixed(1) + " µm";
    out.appendChild(head);

    const lineTitle=el("h3","Current line preview");
    out.appendChild(lineTitle);

    const firstDir=json.directions[0];
    const points=json.first_lines[firstDir] || [];
    out.appendChild(el("div","Direction: "+firstDir,"spm-preview-direction"));
    out.appendChild(drawLineSvg(points));

    const grid=el("div","","spm-image-grid");
    for(const name of ["x_plus","x_minus","y_plus","y_minus"]){
      if(json.directions.includes(name)){
        grid.appendChild(imageBox(name,s));
      }
    }
    out.appendChild(grid);
  }

  function install(){
    if(document.getElementById("spm-raster-preview-panel")) return;

    const panel=el("section","","spm-card");
    panel.id="spm-raster-preview-panel";
    panel.appendChild(el("h2","SPM Raster Preview"));
    panel.appendChild(el("p","Visualizes the current line and directional image slots. No hardware movement."));

    const btn=el("button","UPDATE RASTER PREVIEW");
    const out=el("div","No raster preview generated yet.","spm-raster-preview-output");
    btn.onclick=function(){ updatePreview(out); };

    panel.appendChild(btn);
    panel.appendChild(out);

    const planner=document.getElementById("spm-scan-plan-panel");
    if(planner && planner.parentNode){
      planner.parentNode.insertBefore(panel, planner.nextSibling);
    } else {
      (document.querySelector("main") || document.body).appendChild(panel);
    }
  }

  document.addEventListener("DOMContentLoaded", install);
})();
