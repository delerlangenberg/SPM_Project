from __future__ import annotations

import csv
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.education.config_loader import load_config, get_prusa_backend_kwargs, get_safe_feedrates
from core.motion.prusa_gcode_backend import PrusaGcodeBackend


@dataclass
class AxisCheckRow:
    step: str
    axis: str
    target: float
    actual_x: float | None
    actual_y: float | None
    actual_z: float | None
    result: str


def position_from_state(state: dict) -> tuple[float | None, float | None, float | None]:
    position = state.get("position", {})
    return (
        position.get("x"),
        position.get("y"),
        position.get("z"),
    )


def make_row(step: str, axis: str, target: float, state: dict, result: str = "PASS") -> AxisCheckRow:
    actual_x, actual_y, actual_z = position_from_state(state)
    return AxisCheckRow(
        step=step,
        axis=axis,
        target=target,
        actual_x=actual_x,
        actual_y=actual_y,
        actual_z=actual_z,
        result=result,
    )


def write_rows(path: Path, rows: list[AxisCheckRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(asdict(rows[0]).keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def main() -> int:
    config = load_config()
    limits = config["motion_limits"]
    safe_feedrates = get_safe_feedrates(config)
    backend_kwargs = get_prusa_backend_kwargs(config)
    backend = PrusaGcodeBackend(**backend_kwargs)
    rows: list[AxisCheckRow] = []

    output_file = Path("data/axis_limit_check_2026_06_11.csv")

    x_min, x_max = float(limits["x"][0]), float(limits["x"][1])
    y_min, y_max = float(limits["y"][0]), float(limits["y"][1])
    z_min, z_max = float(limits["z"][0]), float(limits["z"][1])
    x_center = (x_min + x_max) / 2
    y_center = (y_min + y_max) / 2
    z_safe = 20.0

    print("SPM axis limit check")
    print("Physical movement will stay inside configured SPM-safe limits:")
    print(f"X {x_min:g}..{x_max:g}, Y {y_min:g}..{y_max:g}, Z {z_min:g}..{z_max:g}")
    print(f"Output file: {output_file}")

    try:
        backend.connect()
        print("Connected:", backend.get_state())

        print(f"Move to safe Z={z_safe:g}")
        backend.move_to(z=z_safe, feedrate=safe_feedrates["z"])
        rows.append(make_row("safe_z_before_xy", "Z", z_safe, backend.get_state()))
        time.sleep(0.4)

        print(f"Center XY at X{x_center:g} Y{y_center:g}")
        backend.move_to(x=x_center, y=y_center, feedrate=safe_feedrates["xy"])
        rows.append(make_row("center_xy", "XY", x_center, backend.get_state()))
        time.sleep(0.4)

        for label, target in (("x_min", x_min), ("x_max", x_max), ("x_center", x_center)):
            print(f"Move X to {target:g}")
            backend.move_to(x=target, feedrate=safe_feedrates["xy"])
            state = backend.get_state()
            rows.append(make_row(label, "X", target, state))
            print("State:", state)
            time.sleep(0.6)

        for label, target in (("y_min", y_min), ("y_max", y_max), ("y_center", y_center)):
            print(f"Move Y to {target:g}")
            backend.move_to(y=target, feedrate=safe_feedrates["xy"])
            state = backend.get_state()
            rows.append(make_row(label, "Y", target, state))
            print("State:", state)
            time.sleep(0.6)

        for label, target in (("z_min", z_min), ("z_max", z_max), ("z_safe_return", z_safe)):
            print(f"Move Z to {target:g}")
            backend.move_to(z=target, feedrate=safe_feedrates["z"])
            state = backend.get_state()
            rows.append(make_row(label, "Z", target, state))
            print("State:", state)
            time.sleep(0.8)

        write_rows(output_file, rows)
        print("Saved:", output_file)
        return 0
    except Exception as error:
        print(f"ERROR: {error}")
        if rows:
            write_rows(output_file, rows)
            print("Saved partial results:", output_file)
        return 2
    finally:
        backend.disconnect()
        print("Disconnected")


if __name__ == "__main__":
    raise SystemExit(main())
