from __future__ import annotations

import csv
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import serial

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.run_crtouch_magnet_profile import (
    full_retract,
    mega_command,
    move_z,
    printer_command,
    printer_position,
    probe_status,
    wait_for_motion,
)


FEEDS_MM_MIN = (3, 6, 12, 24, 48)
CENTER_X = 125.5
CENTER_Y = 105.0


def write_outputs(csv_path: Path, plot_path: Path, rows: list[dict]) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    figure, axis = plt.subplots(figsize=(8, 5))
    speeds = [float(row["speed_mm_s"]) for row in rows]
    triggers = [float(row["trigger_z_mm"]) for row in rows]
    axis.plot(speeds, triggers, marker="o", linewidth=2)
    axis.set(
        title="CR Touch Tapping Speed Characterization — One Iteration",
        xlabel="Approach speed within each 0.05 mm step (mm/s)",
        ylabel="Detected trigger Z (mm)",
    )
    axis.grid(True, alpha=0.3)
    for speed, trigger in zip(speeds, triggers):
        axis.annotate(f"{trigger:.3f}", (speed, trigger), xytext=(0, 8),
                      textcoords="offset points", ha="center")
    figure.tight_layout()
    figure.savefig(plot_path, dpi=160)
    plt.close(figure)


def run() -> int:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = PROJECT_ROOT / "data" / "crtouch_profiles"
    csv_path = output_dir / f"crtouch_speed_sweep_{stamp}.csv"
    plot_path = output_dir / f"crtouch_speed_sweep_{stamp}.png"
    summary_path = output_dir / f"crtouch_speed_sweep_{stamp}_summary.json"
    rows: list[dict] = []

    with serial.Serial("COM6", 115200, timeout=0.4) as printer, serial.Serial(
        "COM8", 115200, timeout=0.4
    ) as mega:
        time.sleep(2.5)
        printer.reset_input_buffer()
        mega.reset_input_buffer()
        try:
            _, _, z = printer_position(printer)
            if z < 19.7:
                raise RuntimeError(f"Unsafe start Z{z}.")
            identity = " ".join(mega_command(mega, "INFO"))
            if "firmware=0.8.5-lcd-rgb-approach" not in identity:
                raise RuntimeError("Required firmware is not loaded.")
            printer_command(printer, "G90", 5)
            printer_command(printer, f"G1 X{CENTER_X:.3f} Y{CENTER_Y:.3f} F1200", 10)
            wait_for_motion(printer, 30)

            for iteration, feed in enumerate(FEEDS_MM_MIN, start=1):
                print(
                    f"SPEED_TEST_BEGIN {iteration}/{len(FEEDS_MM_MIN)} "
                    f"speed_mm_s={feed / 60.0:.3f}",
                    flush=True,
                )
                move_z(printer, 19.7, 240)
                mega_command(mega, "RESET")
                mega_command(mega, "STOW")
                mega_command(mega, "CLEAR_TRIGGER")
                mega_command(mega, "DEPLOY")
                mega_command(mega, "CLEAR_TRIGGER")
                baseline = probe_status(mega)
                if baseline["D3_raw"] or baseline["trigger_latched"]:
                    raise RuntimeError("Unsafe trigger baseline.")
                move_z(printer, 17.8, 60)

                evidence = baseline
                contact_z = None
                started = time.perf_counter()
                for step in range(1, 33):
                    target_z = round(17.8 - step * 0.05, 2)
                    move_z(printer, target_z, feed)
                    evidence = probe_status(mega)
                    if evidence["trigger_latched"]:
                        contact_z = printer_position(printer)[2]
                        break
                elapsed = time.perf_counter() - started
                if contact_z is None:
                    raise RuntimeError(
                        f"No trigger at speed {feed / 60.0:.3f} mm/s."
                    )

                row = {
                    "iteration": iteration,
                    "feed_mm_min": feed,
                    "speed_mm_s": f"{feed / 60.0:.3f}",
                    "step_mm": "0.050",
                    "trigger_z_mm": f"{contact_z:.3f}",
                    "edges": evidence["edges"],
                    "elapsed_s": f"{elapsed:.3f}",
                }
                rows.append(row)
                write_outputs(csv_path, plot_path, rows)
                print("SPEED_TEST_PASS", json.dumps(row), flush=True)
                mega_command(mega, "STOW")
                move_z(printer, 19.7, 240)

            full_retract(printer, mega, "SPEED_SWEEP_COMPLETE")
            trigger_values = [float(row["trigger_z_mm"]) for row in rows]
            summary_path.write_text(
                json.dumps(
                    {
                        "status": "PASS",
                        "iterations_per_speed": 1,
                        "step_mm": 0.05,
                        "speeds_mm_s": [feed / 60.0 for feed in FEEDS_MM_MIN],
                        "trigger_range_mm": max(trigger_values) - min(trigger_values),
                        "csv": str(csv_path),
                        "plot": str(plot_path),
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            print("SPEED_SWEEP_PASS", summary_path, flush=True)
            return 0
        except Exception as exc:
            print("SPEED_SWEEP_FAULT", repr(exc), flush=True)
            try:
                full_retract(printer, mega, "SPEED_SWEEP_FAULT")
            except Exception as retract_exc:
                print("RETRACT_FAULT", repr(retract_exc), flush=True)
            return 2


if __name__ == "__main__":
    raise SystemExit(run())
