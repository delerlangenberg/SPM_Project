from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt


# ------------------------------------------------------------
# Load raster CSV produced by the SPM scan launcher
# Expected columns:
# timestamp,target_x,target_y,actual_x,actual_y,actual_z,simulated_z_signal
# ------------------------------------------------------------
def load_raster_csv(input_file: str) -> tuple[list[float], list[float], list[list[float]]]:
    rows: list[dict[str, str]] = []

    with open(input_file, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            rows.append(row)

    if not rows:
        raise ValueError(f"No data rows found in CSV file: {input_file}")

    required_columns = {"actual_x", "actual_y", "simulated_z_signal"}
    missing_columns = required_columns - set(rows[0].keys())

    if missing_columns:
        raise ValueError(
            f"CSV file is missing required columns: {sorted(missing_columns)}"
        )

    x_values = sorted({float(row["actual_x"]) for row in rows})
    y_values = sorted({float(row["actual_y"]) for row in rows})

    signal_by_xy: dict[tuple[float, float], float] = {}

    for row in rows:
        x = float(row["actual_x"])
        y = float(row["actual_y"])
        signal = float(row["simulated_z_signal"])
        signal_by_xy[(x, y)] = signal

    z_matrix: list[list[float]] = []

    for y in y_values:
        z_row: list[float] = []
        for x in x_values:
            key = (x, y)
            if key not in signal_by_xy:
                raise ValueError(f"Missing raster point for X={x}, Y={y}")
            z_row.append(signal_by_xy[key])
        z_matrix.append(z_row)

    return x_values, y_values, z_matrix


# ------------------------------------------------------------
# Plot raster matrix using selected matplotlib color map
# ------------------------------------------------------------
def plot_raster(
    input_file: str,
    output_file: str,
    color_map: str = "viridis",
) -> None:
    x_values, y_values, z_matrix = load_raster_csv(input_file)

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(7, 6))
    plt.imshow(
        z_matrix,
        cmap=color_map,
        origin="lower",
        extent=[
            min(x_values),
            max(x_values),
            min(y_values),
            max(y_values),
        ],
        aspect="auto",
    )
    plt.colorbar(label="Simulated Z signal")
    plt.xlabel("X position")
    plt.ylabel("Y position")
    plt.title("Safe Educational SPM Raster Scan")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    print(f"Saved plot: {output_path}")


# ------------------------------------------------------------
# CLI entry point
# ------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot safe educational SPM raster CSV output."
    )
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output-file", required=True)
    parser.add_argument(
        "--color-map",
        default="viridis",
        choices=["viridis", "plasma", "inferno", "magma"],
    )

    args = parser.parse_args()

    plot_raster(
        input_file=args.input_file,
        output_file=args.output_file,
        color_map=args.color_map,
    )


if __name__ == "__main__":
    main()
