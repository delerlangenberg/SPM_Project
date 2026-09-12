"""Read-only Arduino Mega CR Touch controller functionality check."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.hardware.mega_probe import (
    MegaProbeSerialTransport,
    discover_mega_candidate_ports,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Identify and test the locked SPM Mega probe controller."
    )
    parser.add_argument("--port", help="Specific COM port; otherwise discover candidates")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output")
    args = parser.parse_args()

    candidates = [args.port] if args.port else discover_mega_candidate_ports()
    if not candidates:
        payload = {
            "ok": False,
            "error": "No Arduino Mega candidate port found",
            "actuation_attempted": False,
        }
        print(json.dumps(payload) if args.json else payload["error"])
        return 2

    failures: list[str] = []
    for port in candidates:
        try:
            with MegaProbeSerialTransport(port) as mega:
                info = mega.get_info()
                status = mega.get_status()
                self_test = mega.self_test()
            payload = {
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
            if args.json:
                print(json.dumps(payload, indent=2))
            else:
                print(
                    f"{info.identity} found on {port}\n"
                    f"Firmware: {info.firmware_version} · Wiring: {info.wiring_revision}\n"
                    f"State: {status.state} · Trigger raw: {int(status.trigger_raw)}\n"
                    f"Actuation locked: {int(status.actuation_locked)} · "
                    f"Self-test: {'PASS' if self_test else 'FAIL'}"
                )
            return 0 if payload["ok"] else 1
        except Exception as exc:
            failures.append(f"{port}: {exc}")

    payload = {
        "ok": False,
        "error": "No candidate returned the SPM Mega identity",
        "failures": failures,
        "actuation_attempted": False,
    }
    print(json.dumps(payload, indent=2) if args.json else f"{payload['error']}: {'; '.join(failures)}")
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
