from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import serial


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.z_control.crtouch_contact_profile import (
    ContactProfileConfig,
    ContactProfileReading,
    profile_statistics,
    write_profile_csv,
    write_profile_plot,
)


def read_until(port, predicate, timeout_s: float, label: str) -> list[str]:
    deadline = time.time() + timeout_s
    lines: list[str] = []
    while time.time() < deadline:
        line = port.readline().decode("utf-8", "replace").strip()
        if line:
            print(label, line, flush=True)
            lines.append(line)
            if predicate(line):
                return lines
    raise TimeoutError(f"{label} response timeout")


def printer_command(port, command: str, timeout_s: float = 20) -> list[str]:
    print("MK4S SEND", command, flush=True)
    port.write((command + "\n").encode())
    return read_until(
        port,
        lambda line: line.lower().startswith("ok") or line.startswith("Error"),
        timeout_s,
        "MK4S",
    )


def mega_command(port, command: str, timeout_s: float = 5) -> list[str]:
    print("MEGA SEND", command, flush=True)
    port.write((command + "\n").encode())
    if command in {"RESET", "STOW", "DEPLOY"}:
        predicate = lambda line: line.startswith("CONTROL_COMPLETE")
    elif command == "CLEAR_TRIGGER":
        predicate = lambda line: line.startswith("CLEAR_TRIGGER_COMPLETE")
    elif command.startswith("APPROACH "):
        predicate = lambda line: line.startswith("APPROACH_DISPLAY_COMPLETE")
    elif command == "RETRACTING":
        predicate = lambda line: line.startswith("RETRACTING_DISPLAY_COMPLETE")
    elif command == "FAULT":
        predicate = lambda line: line.startswith("FAULT_DISPLAY_COMPLETE")
    else:
        predicate = lambda line: line.startswith(command)
    return read_until(port, predicate, timeout_s, "MEGA")


def printer_position(port) -> tuple[float, float, float]:
    text = " ".join(printer_command(port, "M114", 5))
    match = re.search(r"X:([-\d.]+)\s+Y:([-\d.]+)\s+Z:([-\d.]+)", text)
    if not match:
        raise RuntimeError("Could not parse MK4S M114 position.")
    return tuple(map(float, match.groups()))


def probe_status(port) -> dict[str, int]:
    text = " ".join(mega_command(port, "STATUS", 3))
    values = {
        key: int(value)
        for key, value in re.findall(
            r"(D3_raw|trigger_latched|edges|rising|falling)=(\d+)", text
        )
    }
    if "D8=HIGH_IMPEDANCE" not in text or "trigger_latched" not in values:
        raise RuntimeError("Invalid or unsafe Mega probe status.")
    return values


def wait_for_motion(port, timeout_s: float = 75) -> None:
    printer_command(port, "M400", timeout_s)


def move_z(port, z_mm: float, feed_mm_min: float) -> None:
    printer_command(port, f"G1 Z{z_mm:.3f} F{feed_mm_min:.0f}", 10)
    wait_for_motion(port)


def safe_probe_reset(port) -> None:
    mega_command(port, "RESET")
    mega_command(port, "STOW")
    mega_command(port, "CLEAR_TRIGGER")
    mega_command(port, "STOW")


def full_retract(printer, mega, reason: str) -> None:
    print(f"SAFETY_RETRACT reason={reason}", flush=True)
    try:
        mega_command(mega, "RETRACTING")
    except Exception as exc:
        print("DISPLAY_WARNING", repr(exc), flush=True)
    printer_command(printer, "G90", 5)
    move_z(printer, 120.0, 300)
    safe_probe_reset(mega)
    print("SAFE_AT_Z120", printer_position(printer), flush=True)


def run() -> int:
    config = ContactProfileConfig()
    points = config.bidirectional_taper_points()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = PROJECT_ROOT / "data" / "crtouch_profiles"
    csv_path = output_dir / f"magnet_1d_40pt_{stamp}.csv"
    plot_path = output_dir / f"magnet_1d_40pt_{stamp}.png"
    summary_path = output_dir / f"magnet_1d_40pt_{stamp}_summary.json"
    readings: list[ContactProfileReading] = []

    with serial.Serial("COM6", 115200, timeout=0.4) as printer, serial.Serial(
        "COM8", 115200, timeout=0.4
    ) as mega:
        time.sleep(2.5)
        printer.reset_input_buffer()
        mega.reset_input_buffer()
        try:
            x, y, z = printer_position(printer)
            if z < 19.7 - 0.05:
                raise RuntimeError(
                    f"Unsafe start height X{x} Y{y} Z{z}; expected Z19.70 or higher."
                )
            identity = " ".join(mega_command(mega, "INFO"))
            if "firmware=0.8.5-lcd-rgb-approach" not in identity:
                raise RuntimeError("Required Mega approach firmware is not loaded.")
            printer_command(printer, "G90", 5)
            printer_command(printer, "G1 X125.000 Y105.000 F600", 10)
            wait_for_motion(printer, 30)

            for point in points:
                print(
                    f"POINT_BEGIN {point.index}/{len(points)} X={point.nozzle_x_mm:.2f} "
                    f"Y={point.nozzle_y_mm:.2f}",
                    flush=True,
                )
                move_z(printer, 19.7, 120)
                printer_command(
                    printer,
                    f"G1 X{point.nozzle_x_mm:.3f} Y{point.nozzle_y_mm:.3f} F600",
                    10,
                )
                wait_for_motion(printer, 30)

                mega_command(mega, "RESET")
                mega_command(mega, "STOW")
                mega_command(mega, "CLEAR_TRIGGER")
                mega_command(mega, "DEPLOY")
                mega_command(mega, "CLEAR_TRIGGER")
                baseline = probe_status(mega)
                if baseline["D3_raw"] != 0 or baseline["trigger_latched"] != 0:
                    raise RuntimeError(f"Point {point.index}: trigger baseline is not LOW.")

                # Stay above the highest observed trigger, then resolve contact in
                # 0.05 mm steps so tilted/raised areas are not reported late.
                move_z(printer, 17.8, 60)
                contact_z: float | None = None
                evidence: dict[str, int] | None = None

                targets = [round(17.8 - index * 0.05, 2) for index in range(1, 33)]
                for target_z in targets:
                    move_z(printer, target_z, 6)
                    estimated_gap = max(
                        0.0, target_z - config.estimated_physical_contact_z_mm
                    )
                    mega_command(
                        mega, f"APPROACH {target_z:.2f} {estimated_gap:.2f}"
                    )
                    evidence = probe_status(mega)
                    if evidence["trigger_latched"] == 1:
                        contact_z = printer_position(printer)[2]
                        break

                if contact_z is None or evidence is None:
                    mega_command(mega, "FAULT")
                    raise RuntimeError(
                        f"Point {point.index}: no trigger by hard floor "
                        f"Z{config.hard_floor_z_mm:.2f}."
                    )

                readings.append(
                    ContactProfileReading(
                        point=point,
                        trigger_z_mm=contact_z,
                        trigger_edges=evidence["edges"],
                        temperature_state="OPERATOR_MONITORED_COOL",
                    )
                )
                write_profile_csv(
                    csv_path, readings, center_x_mm=config.center_nozzle_x_mm
                )
                print(
                    f"POINT_PASS {point.index}/{len(points)} trigger_Z={contact_z:.3f} "
                    f"edges={evidence['edges']} csv={csv_path}",
                    flush=True,
                )
                mega_command(mega, "RETRACTING")
                mega_command(mega, "STOW")
                move_z(printer, 19.7, 120)

            full_retract(printer, mega, "PROFILE_COMPLETE")
            stats = profile_statistics(readings)
            write_profile_plot(plot_path, readings)
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            summary_path.write_text(
                json.dumps(
                    {
                        "status": "PASS",
                        "target_height_mm": config.target_height_mm,
                        "target_diameter_mm": config.target_diameter_mm,
                        "csv": str(csv_path),
                        "plot": str(plot_path),
                        "statistics": stats,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            print("PROFILE_PASS", json.dumps(stats), flush=True)
            print("PROFILE_CSV", csv_path, flush=True)
            print("PROFILE_PLOT", plot_path, flush=True)
            print("PROFILE_SUMMARY", summary_path, flush=True)
            return 0
        except Exception as exc:
            print("PROFILE_FAULT", repr(exc), flush=True)
            try:
                full_retract(printer, mega, "PROFILE_FAULT")
            except Exception as retract_exc:
                print("RETRACT_FAULT", repr(retract_exc), flush=True)
            return 2


if __name__ == "__main__":
    raise SystemExit(run())
