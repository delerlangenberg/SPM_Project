(function () {
  "use strict";

  let zIndex = 400;

  function log(message) {
    if (window.SPMConsoleLog) window.SPMConsoleLog(message);
  }

  function closeMenus() {
    for (const group of document.querySelectorAll(".menu-group.open")) {
      group.classList.remove("open");
    }
  }

  function makeDraggable(win) {
    const header = win.querySelector(".window-header");
    if (!header || win.dataset.draggableReady === "true") return;

    let dragging = false;
    let startX = 0;
    let startY = 0;
    let startLeft = 0;
    let startTop = 0;

    header.addEventListener("mousedown", (event) => {
      if (document.body.classList.contains("standalone-window-mode")) return;
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
      log(`Window not found: ${id}`);
      return;
    }

    win.hidden = false;
    win.setAttribute("aria-hidden", "false");
    win.style.zIndex = String(++zIndex);

    makeDraggable(win);

    if (!win.style.left && !document.body.classList.contains("standalone-window-mode")) {
      win.style.left = `${80 + (zIndex % 6) * 24}px`;
      win.style.top = `${120 + (zIndex % 6) * 18}px`;
    }

    if (window.SPMRaster) window.SPMRaster.redrawAll();
    if (window.SPMZLive) window.SPMZLive.redraw();

    log(`Opened ${id}.`);
  }

  function close(win) {
    win.hidden = true;
    win.setAttribute("aria-hidden", "true");
    log(`Closed ${win.id}.`);
  }

  function closeAll() {
    for (const win of document.querySelectorAll(".floating-window")) {
      close(win);
    }
  }

  function initializeFromUrl() {
    const params = new URLSearchParams(window.location.search);
    const requestedWindow = params.get("window");
    const standalone = params.get("standalone") === "1";

    if (standalone) {
      document.body.classList.add("standalone-window-mode");
    }

    if (requestedWindow) {
      setTimeout(() => open(requestedWindow), 100);
    }
  }

  document.addEventListener("click", (event) => {
    const menuButton = event.target.closest(".menu-button");
    if (menuButton) {
      const group = menuButton.closest(".menu-group");
      const wasOpen = group.classList.contains("open");
      closeMenus();
      if (!wasOpen) group.classList.add("open");
      event.stopPropagation();
      return;
    }

    const realTabLink = event.target.closest("a[data-open-tab]");
    if (realTabLink) {
      closeMenus();
      log(`Opening ${realTabLink.dataset.openTab} in a browser tab.`);
      return;
    }

    const openButton = event.target.closest("[data-open-window]");
    if (openButton) {
      open(openButton.dataset.openWindow);
      closeMenus();
      return;
    }

    const closeButton = event.target.closest("[data-close-window]");
    if (closeButton) {
      const win = closeButton.closest(".floating-window");
      if (win) close(win);
      return;
    }

    if (!event.target.closest(".dropdown")) {
      closeMenus();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeMenus();
      if (!document.body.classList.contains("standalone-window-mode")) {
        closeAll();
      }
    }
  });

  window.SPMWindows = {
    open,
    closeAll
  };

  initializeFromUrl();
})();
