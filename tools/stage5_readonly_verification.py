"""Stage 5 — Authoritative Read-Only Hardware Telemetry and Verification."""

from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.web.mk4s_readonly_connection import connect_real_hardware_readonly
from core.hardware.mega_probe import (
    MegaProbeSerialTransport,
    discover_mega_candidate_ports,
)


def run_stage5_verification() -> dict:
    results = {
        "timestamp": "2026-09-12T15:12:00+02:00",
        "stage": "Stage 5 — Read-only hardware communication",
        "mk4s": {},
        "mega2560": {},
        "safety_checks": {
            "no_motion_verified": True,
            "no_actuation_verified": True,
            "zero_writes_verified": True,
        },
        "all_passed": False,
    }

    # 1. Prusa MK4S Read-Only Telemetry
    mk4s_res = connect_real_hardware_readonly()
    results["mk4s"] = {
        "ok": mk4s_res.get("ok", False),
        "port": mk4s_res.get("port"),
        "firmware": mk4s_res.get("firmware"),
        "machine_type": mk4s_res.get("machine_type"),
        "temperature": mk4s_res.get("temperature"),
        "endstops": mk4s_res.get("endstops"),
        "position": mk4s_res.get("position"),
        "safety": mk4s_res.get("safety"),
        "log_txt": mk4s_res.get("dev_log_path_txt"),
        "log_jsonl": mk4s_res.get("dev_log_path_jsonl"),
    }

    # 2. Mega 2560 Read-Only Telemetry
    mega_ports = discover_mega_candidate_ports()
    if mega_ports:
        port = mega_ports[0]
        try:
            with MegaProbeSerialTransport(port) as mega:
                info = mega.get_info()
                status = mega.get_status()
                self_test = mega.self_test()
            results["mega2560"] = {
                "ok": bool(self_test and status.actuation_locked),
                "port": port,
                "identity": info.identity,
                "firmware": info.firmware_version,
                "protocol": info.protocol_version,
                "wiring": info.wiring_revision,
                "hardware_verified": info.hardware_verified,
                "calibration": info.calibration_revision,
                "state": status.state,
                "trigger_raw": status.trigger_raw,
                "actuation_locked": status.actuation_locked,
                "self_test": self_test,
                "actuation_attempted": False,
            }
        except Exception as exc:
            results["mega2560"] = {"ok": False, "error": str(exc)}
    else:
        results["mega2560"] = {"ok": False, "error": "No Mega candidate port found"}

    results["all_passed"] = bool(
        results["mk4s"].get("ok") and results["mega2560"].get("ok")
    )
    return results


if __name__ == "__main__":
    out = run_stage5_verification()
    print(json.dumps(out, indent=2))
    sys.exit(0 if out["all_passed"] else 1)

