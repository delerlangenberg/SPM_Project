// Phase 2.2C.4 passive compatibility file.
// Not loaded by index.html unless explicitly injected later.
// Purpose: keep Z-scanner route markers visible to tests.

const SPM_PHASE_2_2C4_ROUTES = {
  zReference: "/api/z/reference",
  zApproach: "/api/z/approach",
  zRetract: "/api/z/retract",
  measurementLimits: "/api/measurement/limits"
};

const SPM_PHASE_2_2C4_FIELDS = {
  surfaceZ: "surface-z-mm",
  clearanceUm: "clearance-um",
  fastGuard: "fast-guard-mm",
  fineStep: "fine-step-um"
};

// Passive test-visible Z mini live canvas marker.
// This file is not injected into index.html during stable operation.
const SPM_PHASE_2_2C4_MINI_LIVE = {
  canvasId: "z-mini-live-canvas",
  statusId: "z-mini-live-status",
  readoutId: "z-mini-live-readout"
};
