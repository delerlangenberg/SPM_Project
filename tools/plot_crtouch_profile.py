from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.z_control.crtouch_contact_profile import (
    ContactProfilePoint,
    ContactProfileReading,
    write_profile_plot,
)


def load_profile(path: Path) -> list[ContactProfileReading]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return [
        ContactProfileReading(
            point=ContactProfilePoint(
                index=int(row["point"]),
                row=int(row["row"]),
                column=int(row["column"]),
                nozzle_x_mm=float(row["nozzle_x_mm"]),
                nozzle_y_mm=float(row["nozzle_y_mm"]),
            ),
            trigger_z_mm=float(row["trigger_z_mm"]),
            trigger_edges=int(row["trigger_edges"]),
            temperature_state=row["temperature_state"],
        )
        for row in rows
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Plot a CR Touch 1D profile CSV.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or args.csv_path.with_suffix(".png")
    readings = load_profile(args.csv_path)
    write_profile_plot(output, readings)
    print(output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
