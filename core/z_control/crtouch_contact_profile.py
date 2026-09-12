"""Planning and result handling for coarse CR Touch contact profiling."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, pstdev


@dataclass(frozen=True)
class ContactProfilePoint:
    index: int
    row: int
    column: int
    nozzle_x_mm: float
    nozzle_y_mm: float


@dataclass(frozen=True)
class ContactProfileConfig:
    center_nozzle_x_mm: float = 125.0
    center_nozzle_y_mm: float = 105.0
    target_height_mm: float = 10.8
    target_diameter_mm: float = 29.2
    grid_points_per_axis: int = 3
    scan_span_mm: float = 18.0
    edge_margin_mm: float = 1.5
    physical_contact_clearance_mm: float = 7.9
    electrical_trigger_clearance_mm: float = 5.9
    electrical_hard_floor_margin_mm: float = 0.5
    local_retract_z_mm: float = 25.0
    safe_retract_z_mm: float = 120.0
    fine_step_mm: float = 0.05
    fine_speed_mm_s: float = 0.05

    def line_points(
        self, count: int = 5, span_mm: float = 12.0
    ) -> tuple[ContactProfilePoint, ...]:
        """Return a centered X-axis line that stays well inside the round target."""
        self.validate()
        if count < 2:
            raise ValueError("A line profile requires at least two points.")
        usable_diameter = self.target_diameter_mm - 2.0 * self.edge_margin_mm
        if span_mm <= 0 or span_mm > usable_diameter:
            raise ValueError("Line profile extends outside the protected target area.")
        increment = span_mm / (count - 1)
        start_x = self.center_nozzle_x_mm - span_mm / 2.0
        return tuple(
            ContactProfilePoint(
                index=index + 1,
                row=0,
                column=index,
                nozzle_x_mm=start_x + index * increment,
                nozzle_y_mm=self.center_nozzle_y_mm,
            )
            for index in range(count)
        )

    def bidirectional_taper_points(self) -> tuple[ContactProfilePoint, ...]:
        """Center-to-left, then center-to-right scan with dense edge sampling."""
        radii = [
            0.75,
            1.50,
            2.25,
            3.00,
            3.75,
            4.50,
            5.25,
            6.00,
            6.75,
            7.50,
            8.25,
            9.00,
            9.75,
            10.50,
            11.25,
            12.00,
            13.00,
            13.60,
            14.00,
        ]
        offsets = [0.0, *(-radius for radius in radii), 0.0, *radii]
        return tuple(
            ContactProfilePoint(
                index=index,
                row=0 if index <= 20 else 1,
                column=index - 1,
                nozzle_x_mm=self.center_nozzle_x_mm + offset,
                nozzle_y_mm=self.center_nozzle_y_mm,
            )
            for index, offset in enumerate(offsets, start=1)
        )

    @property
    def estimated_physical_contact_z_mm(self) -> float:
        return self.target_height_mm + self.physical_contact_clearance_mm

    @property
    def expected_electrical_trigger_z_mm(self) -> float:
        return self.target_height_mm + self.electrical_trigger_clearance_mm

    @property
    def hard_floor_z_mm(self) -> float:
        return (
            self.expected_electrical_trigger_z_mm
            - self.electrical_hard_floor_margin_mm
        )

    @property
    def fine_handoff_z_mm(self) -> float:
        return self.estimated_physical_contact_z_mm + 1.0

    def validate(self) -> None:
        if self.grid_points_per_axis < 2:
            raise ValueError("Contact profile requires at least 2 points per axis.")
        if self.target_height_mm <= 0 or self.target_diameter_mm <= 0:
            raise ValueError("Target dimensions must be positive.")
        if self.scan_span_mm <= 0:
            raise ValueError("Scan span must be positive.")
        if self.fine_step_mm <= 0 or self.fine_step_mm > 0.05:
            raise ValueError("Pilot fine step must be no more than 0.05 mm.")
        if self.fine_speed_mm_s <= 0 or self.fine_speed_mm_s > 0.05:
            raise ValueError("Pilot fine speed must be no more than 0.05 mm/s.")
        if not (
            self.safe_retract_z_mm
            > self.local_retract_z_mm
            > self.fine_handoff_z_mm
            > self.estimated_physical_contact_z_mm
            > self.expected_electrical_trigger_z_mm
            > self.hard_floor_z_mm
            > self.target_height_mm
        ):
            raise ValueError("Invalid contact-profile Z safety ordering.")

        half_span = self.scan_span_mm / 2.0
        corner_radius = math.hypot(half_span, half_span)
        usable_radius = self.target_diameter_mm / 2.0 - self.edge_margin_mm
        if corner_radius > usable_radius:
            raise ValueError(
                "Square scan corners are outside the protected circular target area."
            )

    def points(self) -> tuple[ContactProfilePoint, ...]:
        self.validate()
        count = self.grid_points_per_axis
        increment = self.scan_span_mm / (count - 1)
        start_x = self.center_nozzle_x_mm - self.scan_span_mm / 2.0
        start_y = self.center_nozzle_y_mm - self.scan_span_mm / 2.0
        points: list[ContactProfilePoint] = []
        index = 1
        for row in range(count):
            columns = range(count) if row % 2 == 0 else range(count - 1, -1, -1)
            for column in columns:
                points.append(
                    ContactProfilePoint(
                        index=index,
                        row=row,
                        column=column,
                        nozzle_x_mm=start_x + column * increment,
                        nozzle_y_mm=start_y + row * increment,
                    )
                )
                index += 1
        return tuple(points)


@dataclass(frozen=True)
class ContactProfileReading:
    point: ContactProfilePoint
    trigger_z_mm: float
    trigger_edges: int
    temperature_state: str = "UNRECORDED"


def profile_statistics(readings: list[ContactProfileReading]) -> dict[str, float]:
    if not readings:
        raise ValueError("At least one contact reading is required.")
    z_values = [reading.trigger_z_mm for reading in readings]
    return {
        "count": float(len(z_values)),
        "mean_trigger_z_mm": mean(z_values),
        "min_trigger_z_mm": min(z_values),
        "max_trigger_z_mm": max(z_values),
        "range_mm": max(z_values) - min(z_values),
        "population_stddev_mm": pstdev(z_values),
    }


def write_profile_csv(
    path: str | Path,
    readings: list[ContactProfileReading],
    center_x_mm: float | None = None,
) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "point",
                "row",
                "column",
                "nozzle_x_mm",
                "nozzle_y_mm",
                "line_distance_mm",
                "trigger_z_mm",
                "relative_height_mm",
                "trigger_edges",
                "temperature_state",
            ]
        )
        reference = mean([reading.trigger_z_mm for reading in readings])
        if center_x_mm is None:
            center_x_mm = (
                min(reading.point.nozzle_x_mm for reading in readings)
                + max(reading.point.nozzle_x_mm for reading in readings)
            ) / 2.0
        for reading in readings:
            writer.writerow(
                [
                    reading.point.index,
                    reading.point.row,
                    reading.point.column,
                    f"{reading.point.nozzle_x_mm:.3f}",
                    f"{reading.point.nozzle_y_mm:.3f}",
                    f"{reading.point.nozzle_x_mm - center_x_mm:.3f}",
                    f"{reading.trigger_z_mm:.3f}",
                    f"{reading.trigger_z_mm - reference:.3f}",
                    reading.trigger_edges,
                    reading.temperature_state,
                ]
            )
    return output


def write_profile_plot(
    path: str | Path, readings: list[ContactProfileReading]
) -> Path:
    """Render a readable 1D contact-height profile from acquired readings."""
    if not readings:
        raise ValueError("At least one contact reading is required.")
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(readings, key=lambda reading: reading.point.nozzle_x_mm)
    center_x = (ordered[0].point.nozzle_x_mm + ordered[-1].point.nozzle_x_mm) / 2.0
    distances = [reading.point.nozzle_x_mm - center_x for reading in ordered]
    z_values = [reading.trigger_z_mm for reading in ordered]
    z_reference = mean(z_values)
    center_readings_by_row = {
        reading.point.row: reading.trigger_z_mm
        for reading in readings
        if abs(reading.point.nozzle_x_mm - center_x) < 0.001
    }
    bidirectional = len(center_readings_by_row) >= 2
    if bidirectional:
        heights_um = [
            (
                reading.trigger_z_mm
                - center_readings_by_row[reading.point.row]
            )
            * 1000.0
            for reading in ordered
        ]
        center_values = list(center_readings_by_row.values())
        center_drift_um = (max(center_values) - min(center_values)) * 1000.0
    else:
        heights_um = [(value - z_reference) * 1000.0 for value in z_values]
        center_drift_um = 0.0

    figure, axis = plt.subplots(figsize=(9, 5))
    axis.plot(distances, heights_um, marker="o", linewidth=2, color="#1769aa")
    axis.axhline(0, color="#555555", linewidth=1, linestyle="--")
    axis.set(
        title="CR Touch 1D Contact Profile — Whiteboard Magnet",
        xlabel="Signed distance from calibrated probe center (mm)",
        ylabel="Height relative to each sweep center (µm)",
    )
    axis.grid(True, alpha=0.3)
    axis.axvline(-13.6, color="#d97706", linestyle=":", linewidth=1.5)
    axis.axvline(13.6, color="#d97706", linestyle=":", linewidth=1.5)
    axis.text(-13.6, axis.get_ylim()[1], " taper", color="#9a5805", va="top")
    axis.text(13.6, axis.get_ylim()[1], "taper ", color="#9a5805", va="top", ha="right")
    minimum_index = heights_um.index(min(heights_um))
    maximum_index = heights_um.index(max(heights_um))
    for index, label, offset in (
        (minimum_index, f"Minimum {heights_um[minimum_index]:+.0f} µm", (8, 10)),
        (maximum_index, f"Maximum {heights_um[maximum_index]:+.0f} µm", (8, -28)),
    ):
        axis.annotate(
            label,
            (distances[index], heights_um[index]),
            textcoords="offset points",
            xytext=offset,
            ha="left",
            arrowprops={"arrowstyle": "->", "color": "#444444"},
        )
    axis.text(
        0.02,
        0.97,
        (
            f"Points: {len(readings)}\n"
            f"Mean trigger Z: {z_reference:.4f} mm\n"
            f"Center repeat difference: {center_drift_um:.0f} µm\n"
            f"Measured range: {max(heights_um) - min(heights_um):.0f} µm\n"
            "Command increment: 50 µm"
        ),
        transform=axis.transAxes,
        va="top",
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.9},
    )
    figure.tight_layout()
    figure.savefig(output, dpi=160)
    plt.close(figure)
    return output
