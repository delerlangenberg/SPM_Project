(function(){
  "use strict";
  if(window.SPM_RELIABLE_LOG_INSTALLED)return;
  window.SPM_RELIABLE_LOG_INSTALLED=true;
  const MAX_LINES=700;
  const memory=[];
  function stamp(){return new Date().toLocaleTimeString();}
  function hideOldLogs(){
    const nodes=Array.from(document.querySelectorAll("section,article,aside,div"));
    for(const el of nodes){
      const t=String(el.textContent||"");
      const old=t.includes("Status / Live Log")||t.includes("Phase 2.4");
      const mine=el.id==="spm-reliable-live-log-panel"||el.closest("#spm-reliable-live-log-panel");
      if(old&&!mine)el.style.display="none";
    }
  }
  function mount(){
    const main=document.querySelector("main")||document.body;
    const cards=Array.from(document.querySelectorAll("section,article,aside,div"));
    const ms=cards.find(x=>String(x.textContent||"").includes("Main System"));
    return ms&&ms.parentElement?ms.parentElement:main;
  }
  function panel(){
    let p=document.getElementById("spm-reliable-live-log-panel");
    if(p)return p.querySelector("pre");
    hideOldLogs();
    p=document.createElement("section");
    p.id="spm-reliable-live-log-panel";
    p.style.cssText="margin:14px 0;padding:0;border:1px solid #2563eb;border-radius:14px;background:#020617;color:#dbeafe;overflow:hidden;box-shadow:none";
    const h=document.createElement("div");
    h.style.cssText="display:flex;gap:8px;align-items:center;justify-content:space-between;padding:8px 10px;background:#0f172a";
    const title=document.createElement("div");
    title.textContent="SPM LIVE LOG - API / HARDWARE";
    title.style.cssText="color:#93c5fd;font:800 12px system-ui;letter-spacing:.06em";
    const tools=document.createElement("div");
    tools.id="spm-log-tools";
    tools.style.cssText="display:flex;gap:8px";
    h.appendChild(title);
    h.appendChild(tools);
    p.appendChild(h);
    mount().appendChild(p);
    return addBodyAndTools(p,tools);
  }
  function makeTool(text,fn){
    const b=document.createElement("button");
    b.type="button";
    b.textContent=text;
    b.style.cssText="height:28px;padding:0 10px;border-radius:8px;border:1px solid #475569;background:#1e293b;color:#e5f2ff;font:700 11px system-ui;cursor:pointer";
    b.onclick=fn;
    return b;
  }
  function addBodyAndTools(p,tools){
    const clear=makeTool("CLEAR LOG",function(){
      memory.length=0;
      body().textContent="["+stamp()+"] Log cleared.\n";
    });
    const down=makeTool("DOWNLOAD LOG",function(){
      const blob=new Blob([memory.join("\n")+"\n"],{type:"text/plain"});
      const a=document.createElement("a");
      const ts=new Date().toISOString().replace(/[:.]/g,"-");
      a.href=URL.createObjectURL(blob);
      a.download="spm_hardware_live_log_"+ts+".txt";
      a.click();
      setTimeout(()=>URL.revokeObjectURL(a.href),1500);
    });
    tools.appendChild(clear);
    tools.appendChild(down);
    const b=document.createElement("pre");
    b.id="spm-reliable-live-log-body";
    b.style.cssText="margin:0;padding:9px;height:260px;overflow:auto;white-space:pre-wrap;font:12px Consolas,monospace;background:#020617;color:#dbeafe";
    p.appendChild(b);
    return b;
  }
  function body(){
    return document.getElementById("spm-reliable-live-log-body")||panel();
  }
  function line(msg){
    const clean=String(msg||"").trim();
    if(!clean)return;
    const out="["+stamp()+"] "+clean;
    memory.push(out);
    if(memory.length>MAX_LINES)memory.splice(0,memory.length-MAX_LINES);
    const b=body();
    b.textContent=memory.join("\n")+"\n";
    b.scrollTop=b.scrollHeight;
  }
  function payload(j){
    if(!j)return;
    if(j.message)line("MESSAGE: "+j.message);
    if(j.status||j.mode)line("STATE: status="+j.status+" mode="+j.mode+" ok="+j.ok);
    if(j.port||j.position)line("HW: port="+(j.port||"")+" position="+(j.position||""));
    const a=Array.isArray(j.log_lines)?j.log_lines:[];
    const b=j.hardware&&Array.isArray(j.hardware.log_lines)?j.hardware.log_lines:[];
    a.concat(b).forEach(x=>line(x));
  }
  window.spmReliableLogLine=line;
  window.spmVisibleLogLine=line;
  window.spmVisibleLogPayload=payload;
  const oldFetch=window.fetch.bind(window);
  window.fetch=function(input,init){
    const url=typeof input==="string"?input:(input&&input.url)||"";
    const isApi=url.indexOf("/api/")>=0;
    const t=performance.now();
    if(isApi)line("REQUEST: "+url);
    return oldFetch(input,init).then(r=>{
      if(isApi)line("RESPONSE: HTTP "+r.status+" "+url+" "+Math.round(performance.now()-t)+"ms");
      if(isApi)r.clone().json().then(payload).catch(e=>line("JSON READ ERROR: "+e));
      return r;
    }).catch(e=>{line("FETCH ERROR: "+url+" "+e);throw e;});
  };
  document.addEventListener("DOMContentLoaded",function(){
    hideOldLogs();
    panel();
    line("Reliable in-page live log installed.");
  });
})();
