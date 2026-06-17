"""Local web operator console server for the Prusa MK4S SPM project."""

from __future__ import annotations

import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from core.ai.academic_ai_client import build_ai_recommendation, get_academic_ai_status
from core.web.spm_scan_simulation import build_scan_line, profile_from_query, scan_profile_payload


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
        "name": "System power / professional layout cleanup",
        "status": "implemented",
        "purpose": "Move roadmap to documentation and open scan/live/status/about tools as floating windows.",
    },
    {
        "phase": "2.2",
        "name": "Z scanner / Academic AI advisory layer",
        "status": "implemented",
        "purpose": "Add advisory-only AI assistant endpoints and GUI window.",
    },
    {
        "phase": "2.3",
        "name": "XY scanner / SPM raster scan model",
        "status": "implemented",
        "purpose": "Model constant-distance Z feedback line scans and accumulated topography.",
    },    {
        "phase": "2.4",
        "name": "Live scan / hardware-backed Z and XY integration",
        "status": "planned",
        "purpose": "Connect proven old project Z approach and XY scan services behind local safety gates.",
    },
    {
        "phase": "2.5",
        "name": "Professional operator workflow",
        "status": "planned",
        "purpose": "Finalize connect, initialize, approach, scan, export, park, and shutdown workflow.",
    },
]


def json_response(payload: dict[str, Any] | list[dict[str, Any]]) -> bytes:
    return json.dumps(payload, indent=2).encode("utf-8")


class OperatorConsoleHandler(SimpleHTTPRequestHandler):
    """HTTP handler serving static UI and local API endpoints."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def _send_json(self, payload: dict[str, Any] | list[dict[str, Any]], status: int = 200) -> None:
        body = json_response(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, message: str, status: int = 400) -> None:
        self._send_json({"status": "error", "message": message}, status=status)

    def do_GET(self) -> None:  # noqa: N802 - required by http.server
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        route = parsed.path

        if route == "/api/status":
            self._send_json(
                {
                    "project": "SPM Prusa MK4S",
                    "console": "web_operator_console",
                    "phase": "2.3",
                    "status": "ok",
                    "hardware": {
                        "mk4s": "not_connected_stub",
                        "z_scanner": "not_connected_stub",
                        "xy_scanner": "simulation_scan_model",
                    },
                    "safety": {
                        "real_motion_enabled": False,
                        "default_mode": "simulation_stub",
                    },
                    "scan_model": "constant_distance_z_feedback_raster",
                }
            )
            return

        if route == "/api/phase-map":
            self._send_json(PHASE_MAP)
            return

        if route == "/api/ai/status":
            status = get_academic_ai_status()
            self._send_json(
                {
                    "configured": status.configured,
                    "mode": status.mode,
                    "role": status.role,
                    "safety_rule": status.safety_rule,
                }
            )
            return

        if route == "/api/ai/recommendation":
            task = query.get("task", ["general"])[0]
            self._send_json(build_ai_recommendation(task=task, context={"source": "web_operator_console"}))
            return

        if route == "/api/scan/profile":
            try:
                profile = profile_from_query(query)
                self._send_json(scan_profile_payload(profile))
            except ValueError as error:
                self._send_error_json(str(error))
            return

        if route == "/api/scan/line":
            try:
                profile = profile_from_query(query)
                line_index = int(float(query.get("line_index", [0])[0]))
                self._send_json(build_scan_line(profile, line_index=line_index))
            except (TypeError, ValueError) as error:
                self._send_error_json(str(error))
            return

        if route == "/":
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

