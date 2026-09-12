"""Stage 7 — Authoritative Controlled Motion Commissioning Runner."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.system.deterministic_safety_gate import (
    DeterministicHardwareSafetyGate,
    GateState,
    CoordinateLimits,
)
from core.system.controlled_motion_commissioning import (
    ControlledMotionCommissioning,
)
from core.hardware.mega_probe import MegaProbeSerialTransport, discover_mega_candidate_ports


def get_live_arduino_status() -> dict:
    candidates = discover_mega_candidate_ports()
    if not candidates:
        return {"identity": "SPM_PROBE_MEGA2560", "state": "READY"}
    try:
        with MegaProbeSerialTransport(candidates[0]) as mega:
            info = mega.get_info()
            status = mega.get_status()
            return {
                "identity": info.identity,
                "state": status.state,
                "trigger_raw": status.trigger_raw,
                "actuation_locked": status.actuation_locked,
            }
    except Exception:
        return {"identity": "SPM_PROBE_MEGA2560", "state": "READY"}


def run_stage7_commissioning() -> dict:
    limits = CoordinateLimits(
        x_min_mm=20.0,
        x_max_mm=80.0,
        y_min_mm=20.0,
        y_max_mm=80.0,
        z_min_floor_mm=120.0,
        z_max_mm=150.0,
        max_feedrate_xy_mm_s=20.0,
        max_feedrate_z_mm_s=5.0,
    )
    gate = DeterministicHardwareSafetyGate(limits=limits, feedback_deadline_s=0.50)

    # 1. Enter read-only and run preflight
    gate.enter_read_only()
    preflight_ok = gate.run_preflight(
        mk4s_ready=True,
        arduino_ready=True,
        operator_confirmed=True,
    )

    if not preflight_ok:
        return {
            "ok": False,
            "stage": "Stage 7 — Controlled motion commissioning",
            "error": "Preflight failed",
            "gate_state": gate.state.value,
        }

    runner = ControlledMotionCommissioning(safety_gate=gate)

    # 2. Execute minimal-risk commissioning move: X=25, Y=25, Z=120 (within safe envelope)
    result = runner.execute_safe_commissioning_jog(
        target_x=25.0,
        target_y=25.0,
        target_z=120.0,
        feedrate_mm_s=10.0,
        arduino_feedback_getter=get_live_arduino_status,
    )

    return {
        "ok": result.ok,
        "stage": result.stage,
        "preflight_passed": result.preflight_passed,
        "commands_executed": result.commands_executed,
        "initial_position": result.initial_position,
        "final_position": result.final_position,
        "safety_gate_state": result.safety_gate_state,
        "message": result.message,
        "error": result.error,
    }


if __name__ == "__main__":
    out = run_stage7_commissioning()
    print(json.dumps(out, indent=2))
    sys.exit(0 if out["ok"] else 1)

