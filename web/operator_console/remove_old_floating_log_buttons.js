(function(){
  "use strict";
  function removeOldFloatingLogButtons(){
    const labels=["DOWNLOAD HARDWARE LOG","CLEAR LIVE LOG"];
    const buttons=Array.from(document.querySelectorAll("button"));
    for(const b of buttons){
      const txt=String(b.textContent||"").trim().toUpperCase();
      if(labels.includes(txt)){
        const reliable=b.closest("#spm-reliable-live-log-panel");
        if(reliable) continue;
        const panel=b.closest("section,article,aside,div") || b;
        panel.style.display="none";
        panel.dataset.spmOldFloatingLogHidden="1";
      }
    }
  }
  document.addEventListener("DOMContentLoaded",function(){
    setTimeout(removeOldFloatingLogButtons,100);
    setTimeout(removeOldFloatingLogButtons,800);
    setTimeout(removeOldFloatingLogButtons,2000);
  });
  window.spmRemoveOldFloatingLogButtons=removeOldFloatingLogButtons;
})();
