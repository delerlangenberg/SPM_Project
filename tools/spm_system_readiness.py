"""Read-only readiness report for Simulation, Dry Run and real measurement."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.hardware.psoc_edge import EdgeSerialTransport
from core.hardware.spm_system import (
    AcquisitionMode,
    discover_spm_ports,
    evaluate_spm_readiness,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=[mode.value for mode in AcquisitionMode],
        default=AcquisitionMode.REAL_MEASUREMENT.value,
    )
    args = parser.parse_args()
    requested_mode = AcquisitionMode(args.mode)

    port_map = discover_spm_ports()
    edge_info = None
    handshake_error = ""
    if len(port_map.edge) == 1:
        try:
            with EdgeSerialTransport(port_map.edge[0].device) as edge:
                edge_info = edge.get_info()
        except Exception as exc:
            handshake_error = str(exc)

    report = evaluate_spm_readiness(port_map, edge_info)
    payload = {
        "requested_mode": requested_mode.value,
        "allowed": report.allows(requested_mode),
        "ports": {
            "mk4s": [item.device for item in port_map.mk4s],
            "psoc_edge": [item.device for item in port_map.edge],
        },
        "usb_unambiguous": port_map.unambiguous,
        "edge_handshake": edge_info is not None,
        "edge_handshake_error": handshake_error,
        "real_measurement_ready": report.real_measurement_ready,
        "blockers": list(report.blockers),
    }
    print(json.dumps(payload, indent=2))
    return 0 if payload["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
