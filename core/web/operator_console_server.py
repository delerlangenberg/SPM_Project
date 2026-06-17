"""Local web operator console server for the Prusa MK4S SPM project.

Phase 2.0 foundation:
- standard-library only
- serves web/operator_console
- exposes small JSON API stubs
- later phases will connect these endpoints to real MK4S/Z/XY scanner services
"""

from __future__ import annotations

import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = PROJECT_ROOT / "web" / "operator_console"


PHASE_MAP: list[dict[str, str]] = [
    {
        "phase": "2.0",
        "name": "Web operator console shell",
        "status": "implemented",
        "purpose": "Create browser-based main workspace with menu, main controls, Z scanner controls, and XY scanner controls.",
    },
    {
        "phase": "2.1",
        "name": "System power/status integration",
        "status": "planned",
        "purpose": "Connect ON/OFF/CLOSE/STATUS buttons to existing workstation and hardware command services.",
    },
    {
        "phase": "2.2",
        "name": "Z scanner integration",
        "status": "planned",
        "purpose": "Inject proven Z approach, retract, Z readback, and safe auto-approach logic from the old projects.",
    },
    {
        "phase": "2.3",
        "name": "XY scanner integration",
        "status": "planned",
        "purpose": "Inject proven XY jog, raster scan, scan profile, and plot/export logic.",
    },
    {
        "phase": "2.4",
        "name": "Live scan visualization",
        "status": "planned",
        "purpose": "Add live measurement window, signal preview, CSV output, PNG preview, and Gwyddion-compatible export.",
    },
    {
        "phase": "2.5",
        "name": "Professional operator workflow",
        "status": "planned",
        "purpose": "Finalize guided workflow: connect, initialize, approach, preview, scan, export, park, shutdown.",
    },
]


def json_response(payload: dict[str, Any] | list[dict[str, Any]]) -> bytes:
    return json.dumps(payload, indent=2).encode("utf-8")


class OperatorConsoleHandler(SimpleHTTPRequestHandler):
    """HTTP handler serving static UI and local API stubs."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def _send_json(self, payload: dict[str, Any] | list[dict[str, Any]], status: int = 200) -> None:
        body = json_response(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - required by http.server
        if self.path == "/api/status":
            self._send_json(
                {
                    "project": "SPM Prusa MK4S",
                    "console": "web_operator_console",
                    "phase": "2.0",
                    "status": "ok",
                    "hardware": {
                        "mk4s": "not_connected_stub",
                        "z_scanner": "not_connected_stub",
                        "xy_scanner": "not_connected_stub",
                    },
                    "safety": {
                        "real_motion_enabled": False,
                        "default_mode": "simulation_stub",
                    },
                }
            )
            return

        if self.path == "/api/phase-map":
            self._send_json(PHASE_MAP)
            return

        if self.path == "/":
            self.path = "/index.html"

        super().do_GET()


def run_server(host: str = "127.0.0.1", port: int = 8787) -> None:
    if not WEB_ROOT.exists():
        raise FileNotFoundError(f"Web root does not exist: {WEB_ROOT}")

    server = ThreadingHTTPServer((host, port), OperatorConsoleHandler)
    print(f"SPM Prusa web operator console running at http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local SPM Prusa web operator console.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()
    run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
