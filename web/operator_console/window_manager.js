(function () {
  "use strict";

  let zIndex = 400;

  function makeDraggable(win) {
    const header = win.querySelector(".window-header");
    if (!header || win.dataset.draggableReady === "true") return;

    let dragging = false;
    let startX = 0;
    let startY = 0;
    let startLeft = 0;
    let startTop = 0;

    header.addEventListener("mousedown", (event) => {
      if (event.target.closest("button")) return;

      dragging = true;
      startX = event.clientX;
      startY = event.clientY;
      startLeft = win.offsetLeft;
      startTop = win.offsetTop;
      win.style.zIndex = String(++zIndex);
      event.preventDefault();
    });

    document.addEventListener("mousemove", (event) => {
      if (!dragging) return;

      const dx = event.clientX - startX;
      const dy = event.clientY - startY;
      win.style.left = `${Math.max(0, startLeft + dx)}px`;
      win.style.top = `${Math.max(90, startTop + dy)}px`;
    });

    document.addEventListener("mouseup", () => {
      dragging = false;
    });

    win.dataset.draggableReady = "true";
  }

  function open(id) {
    const win = document.getElementById(id);
    if (!win) {
      if (window.SPMConsoleLog) window.SPMConsoleLog(`Window not found: ${id}`);
      return;
    }

    win.hidden = false;
    win.setAttribute("aria-hidden", "false");
    win.style.zIndex = String(++zIndex);

    makeDraggable(win);

    if (!win.style.left) {
      win.style.left = `${80 + (zIndex % 6) * 24}px`;
      win.style.top = `${120 + (zIndex % 6) * 18}px`;
    }

    if (window.SPMRaster) window.SPMRaster.redrawAll();
    if (window.SPMConsoleLog) window.SPMConsoleLog(`Opened ${id}.`);
  }

  function close(win) {
    win.hidden = true;
    win.setAttribute("aria-hidden", "true");
    if (window.SPMConsoleLog) window.SPMConsoleLog(`Closed ${win.id}.`);
  }

  function closeAll() {
    for (const win of document.querySelectorAll(".floating-window")) {
      close(win);
    }
  }

  document.addEventListener("click", (event) => {
    const openButton = event.target.closest("[data-open-window]");
    if (openButton) {
      open(openButton.dataset.openWindow);
      return;
    }

    const closeButton = event.target.closest("[data-close-window]");
    if (closeButton) {
      const win = closeButton.closest(".floating-window");
      if (win) close(win);
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeAll();
  });

  window.SPMWindows = {
    open,
    closeAll
  };
})();
