"""Local web operator console server for the Prusa MK4S SPM project."""

from __future__ import annotations

import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

# Phase 2.2E: script-launch import path fix
from pathlib import Path as _SPM_Path
import sys as _SPM_sys

_SPM_PROJECT_ROOT = _SPM_Path(__file__).resolve().parents[2]
if str(_SPM_PROJECT_ROOT) not in _SPM_sys.path:
    _SPM_sys.path.insert(0, str(_SPM_PROJECT_ROOT))

from core.ai.academic_ai_client import build_ai_recommendation, get_academic_ai_status
from core.web.spm_scan_simulation import build_scan_line, profile_from_query, scan_profile_payload
from core.web.system_control import dry_run_startup_plan, system_close, system_off, system_on, system_status


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = PROJECT_ROOT / "web" / "operator_console"


PHASE_MAP: list[dict[str, str]] = [
    {
        "phase": "2.0",
        "name": "Web operator console shell",
        "status": "implemented",
        "purpose": "Browser-based SPM Prusa operator console foundation.",
    },
    {
        "phase": "2.1",
        "name": "System power / professional layout cleanup",
        "status": "implemented",
        "purpose": "Clean main page, status area, log area, and first operator controls.",
    },
    {
        "phase": "2.2",
        "name": "Z scanner / Academic AI advisory layer",
        "status": "implemented",
        "purpose": "Advisory-only AI assistant and Z scanner shell.",
    },
    {
        "phase": "2.3",
        "name": "XY scanner / non-blocking scan measurement windows",
        "status": "implemented",
        "purpose": "Non-blocking View/Open/Tools windows, line mode, topography, and measurement workflow shell.",
    },
    {
        "phase": "2.4",
        "name": "Live scan / hardware-backed scan integration",
        "status": "planned",
        "purpose": "Connect proven old Z approach, XY raster, CSV, PNG, and Gwyddion export services.",
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

    def do_GET(self) -> None:  # noqa: N802
        # === Phase 2.2D smart main system routes start ===
        from urllib.parse import urlparse as _spm_urlparse, parse_qs as _spm_parse_qs
        _spm_parsed = _spm_urlparse(self.path)
        _spm_path = _spm_parsed.path
        _spm_qs = _spm_parse_qs(_spm_parsed.query)
        
        def _spm_first(name, default=""):
            values = _spm_qs.get(name, [])
            return values[0] if values else default

        def _spm_first_any(names, default=""):
            for name in names:
                values = _spm_qs.get(name, [])
                if values:
                    return values[0]
            return default
        
        def _spm_send_json(payload, status_code=200):
            import json as _spm_json
            data = _spm_json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        
        if _spm_path == "/api/system/on":
            from core.web.system_control import system_on
            _spm_send_json(system_on(mode=_spm_first("mode", "dry_run"), port=_spm_first("port", "")))
            return
        
        if _spm_path in {"/api/system/off", "/api/system/disconnect"}:
            from core.web.system_control import system_disconnect
            _spm_send_json(system_disconnect())
            return
        
        if _spm_path in {"/api/system/safe-retract", "/api/system/safe_retract"}:
            from core.web.system_control import system_safe_retract
            _spm_send_json(system_safe_retract())
            return

        if _spm_path in {"/api/system/safe-standby", "/api/system/safe_standby"}:
            from core.web.system_control import system_safe_standby
            _spm_send_json(system_safe_standby())
            return
        
        if _spm_path == "/api/system/close":
            from core.web.system_control import system_close
            _spm_send_json(system_close())
            return
        
        if _spm_path == "/api/system/status":
            from core.web.system_control import system_status
            _spm_send_json(system_status())
            return

        if _spm_path == "/api/system/diagnostics":
            from core.web.system_control import system_diagnostics
            _spm_send_json(system_diagnostics())
            return

        if _spm_path == "/api/system/sync-position":
            from core.web.system_control import system_sync_logical_position
            _spm_send_json(system_sync_logical_position())
            return
        
        if _spm_path == "/api/system/config/port":
            from core.web.system_control import system_apply_port
            _spm_send_json(system_apply_port(_spm_first("port", "")))
            return
        
        if _spm_path == "/api/system/config/mode":
            from core.web.system_control import system_apply_mode
            _spm_send_json(system_apply_mode(_spm_first("mode", "hardware_readonly")))
            return

        if _spm_path == "/api/z/reference":
            from core.web.z_scanner_control import z_reference_payload
            _spm_send_json(z_reference_payload())
            return

        if _spm_path == "/api/z/read":
            from core.web.z_scanner_control import z_read_status
            _spm_send_json(z_read_status(port=_spm_first("port", "") or None))
            return

        if _spm_path == "/api/z/auto-preview":
            from core.web.z_scanner_control import z_auto_preview
            _spm_send_json(z_auto_preview(
                setpoint_distance_mm=float(_spm_first_any(("setpoint_distance_mm", "setpoint_mm"), "0") or 0),
                retract_after=_spm_first("retract_after", "0") == "1",
            ))
            return

        if _spm_path == "/api/z/auto-approach":
            from core.web.z_scanner_control import z_auto_approach
            try:
                _spm_send_json(z_auto_approach(
                    setpoint_distance_mm=float(_spm_first_any(("setpoint_distance_mm", "setpoint_mm"), "0") or 0),
                    retract_after=_spm_first("retract_after", "0") == "1",
                    confirmed=_spm_first("confirmed", "0") == "1",
                ))
            except Exception as exc:
                _spm_send_json({
                    "ok": False,
                    "status": "failed",
                    "message": f"Z auto approach failed: {exc}",
                    "log_lines": [f"Z auto approach failed: {exc}"],
                }, 500)
            return

        if _spm_path == "/api/z/move-to-setpoint":
            from core.web.z_scanner_control import z_move_to_setpoint
            try:
                _spm_send_json(z_move_to_setpoint(
                    target_z_mm=float(_spm_first_any(("target_z_mm", "setpoint_mm"), "0") or 0),
                    confirmed=_spm_first("confirmed", "0") == "1",
                ))
            except Exception as exc:
                _spm_send_json({
                    "ok": False,
                    "status": "failed",
                    "message": f"Apply Target Z failed: {exc}",
                    "log_lines": [f"Apply Target Z failed: {exc}"],
                }, 500)
            return

        if _spm_path == "/api/z/manual-step":
            from core.web.z_scanner_control import z_manual_step
            try:
                _spm_send_json(z_manual_step(
                    direction=_spm_first("direction", "down"),
                    step_mm=float(_spm_first("step_mm", "0.1") or 0.1),
                    confirmed=_spm_first("confirmed", "0") == "1",
                ))
            except Exception as exc:
                _spm_send_json({
                    "ok": False,
                    "status": "failed",
                    "message": f"Manual Z move failed: {exc}",
                    "log_lines": [f"Manual Z move failed: {exc}"],
                }, 500)
            return

        if _spm_path == "/api/z/retract":
            from core.web.z_scanner_control import z_retract
            try:
                _spm_send_json(z_retract(confirmed=_spm_first("confirmed", "0") == "1"))
            except Exception as exc:
                _spm_send_json({
                    "ok": False,
                    "status": "failed",
                    "message": f"Z retract failed: {exc}",
                    "log_lines": [f"Z retract failed: {exc}"],
                }, 500)
            return

        if _spm_path == "/api/z/stop":
            from core.web.z_scanner_control import z_stop_now
            _spm_send_json(z_stop_now())
            return

        if _spm_path == "/api/measurement/limits":
            from core.web.z_scanner_control import measurement_limits_payload
            _spm_send_json(measurement_limits_payload())
            return
        # === Phase 2.2D smart main system routes end ===
        parsed = urlparse(self.path)

        if parsed.path == "/api/scan/plan":
            from core.web.spm_scan_plan_api import build_scan_plan_from_query
            self._send_json(build_scan_plan_from_query(parsed.query))
            return

        # Phase 2.2E health-test top route
        if parsed.path == "/api/system/health-test":
            from core.web.system_control import system_health_test
            confirmed = "1" if "confirmed=1" in parsed.query else "0"
            motion = "1" if "motion=1" in parsed.query else "0"
            profile = "long" if "profile=long" in parsed.query else "short"
            self._send_json(system_health_test(confirmed=confirmed, motion=motion, profile=profile))
            return

        query = parse_qs(parsed.query)
        route = parsed.path

        if route == "/api/system/status":
            self._send_json(system_status())
            return

        if route == "/api/system/on":
            mode = query.get("mode", ["dry_run"])[0]
            self._send_json(system_on(mode=mode))
            return

        if route == "/api/system/off":
            self._send_json(system_off())
            return

        if route == "/api/system/close":
            self._send_json(system_close())
            return

        if route == "/api/system/dry-run":
            self._send_json(dry_run_startup_plan())
            return

        if route == "/api/status":
            self._send_json(
                {
                    "project": "SPM Prusa MK4S",
                    "console": "web_operator_console",
                    "phase": "2.3B",
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
                    "measurement": {
                        "approach_required_before_scan": True,
                        "start_pause_stop": "simulation_shell",
                        "default_center": "simulation_shell",
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

