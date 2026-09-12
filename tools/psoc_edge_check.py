"""Read-only PSoC Edge E84 connection and protocol check."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import this small module directly so the hardware checker does not load the
# GUI/scanning dependency tree before it can inspect the serial device.
PSOC_EDGE_DIR = ROOT / "core" / "hardware" / "psoc_edge"
if str(PSOC_EDGE_DIR) not in sys.path:
    sys.path.insert(0, str(PSOC_EDGE_DIR))

from device import EdgeSerialTransport, discover_edge_ports


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", help="Explicit KitProg3 UART COM port")
    args = parser.parse_args()

    ports = [args.port] if args.port else discover_edge_ports()
    if not ports:
        print(json.dumps({"connected": False, "reason": "no_infineon_usb_uart"}))
        return 2
    if len(ports) != 1:
        print(json.dumps({"connected": False, "reason": "ambiguous_ports", "ports": ports}))
        return 3

    try:
        with EdgeSerialTransport(ports[0]) as controller:
            info = controller.get_info()
            status_value = controller.get_status()
            self_test, self_test_fields = controller.command("SELF_TEST")
            diagnostics_value = controller.get_diagnostics()
            ping_ok = controller.ping()
            print(json.dumps({
                "connected": True,
                "port": ports[0],
                "board": info.board_id,
                "firmware": info.firmware_version,
                "protocol": info.protocol_version,
                "hardware_verified": info.hardware_verified,
                "status": {
                    "state": status_value.state.value,
                    "hardware_verified": status_value.hardware_verified,
                    "outputs_locked": status_value.outputs_locked,
                    "fault": status_value.fault_code,
                },
                "self_test": {"response": self_test, **self_test_fields},
                "diagnostics": {
                    "board_ok": diagnostics_value.board_ok,
                    "uart_ok": diagnostics_value.uart_ok,
                    "probe_power": diagnostics_value.probe_power,
                    "probe_input": diagnostics_value.probe_input,
                    "probe_control": diagnostics_value.probe_control,
                },
                "ping_ok": ping_ok,
            }, indent=2))
    except Exception as exc:
        print(json.dumps({
            "connected": False,
            "port": ports[0],
            "reason": "protocol_handshake_failed",
            "error": str(exc),
        }, indent=2))
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
