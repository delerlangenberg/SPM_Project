"""Adaptive 2D planning and projection for coarse CR Touch contact maps."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MapPoint:
    index: int
    x_mm: float
    y_mm: float
    role: str


@dataclass(frozen=True)
class MapReading:
    point: MapPoint
    contact: bool
    trigger_z_mm: float | None
    edges: int


def adaptive_points(
    center_x_mm: float = 125.5,
    center_y_mm: float = 105.0,
) -> tuple[MapPoint, ...]:
    """Return sparse interior plus dense taper/outside control sampling."""
    candidates: list[tuple[float, float, str]] = [(center_x_mm, center_y_mm, "CENTER")]

    # A 5 mm Cartesian grid across the 40 x 40 mm field.
    for y_offset in range(-20, 21, 5):
        for x_offset in range(-20, 21, 5):
            if x_offset == 0 and y_offset == 0:
                continue
            if math.hypot(x_offset, y_offset) > 12.5:
                continue
            candidates.append(
                (center_x_mm + x_offset, center_y_mm + y_offset, "FIELD_GRID")
            )

    # Dense polar rings resolve the tapered rim and verify the outside.
    for radius, role in (
        (13.0, "INNER_RIM"),
        (13.6, "TAPER_START"),
        (14.0, "TAPER"),
        (15.2, "OUTSIDE_CONTROL"),
    ):
        for angle_index in range(18):
            angle = 2.0 * math.pi * angle_index / 18.0
            candidates.append(
                (
                    center_x_mm + radius * math.cos(angle),
                    center_y_mm + radius * math.sin(angle),
                    role,
                )
            )

    unique: dict[tuple[float, float], tuple[float, float, str]] = {}
    for x_mm, y_mm, role in candidates:
        unique[(round(x_mm, 3), round(y_mm, 3))] = (x_mm, y_mm, role)
    return tuple(
        MapPoint(index, x_mm, y_mm, role)
        for index, (x_mm, y_mm, role) in enumerate(unique.values(), start=1)
    )


def write_map_csv(path: str | Path, readings: list[MapReading]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["point", "x_mm", "y_mm", "role", "contact", "trigger_z_mm", "edges"]
        )
        for reading in readings:
            writer.writerow(
                [
                    reading.point.index,
                    f"{reading.point.x_mm:.3f}",
                    f"{reading.point.y_mm:.3f}",
                    reading.point.role,
                    int(reading.contact),
                    (
                        f"{reading.trigger_z_mm:.3f}"
                        if reading.trigger_z_mm is not None
                        else ""
                    ),
                    reading.edges,
                ]
            )
    return output


def load_map_csv(path: str | Path) -> list[MapReading]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return [
        MapReading(
            point=MapPoint(
                index=int(row["point"]),
                x_mm=float(row["x_mm"]),
                y_mm=float(row["y_mm"]),
                role=row["role"],
            ),
            contact=row["contact"] == "1",
            trigger_z_mm=(
                float(row["trigger_z_mm"]) if row["trigger_z_mm"] else None
            ),
            edges=int(row["edges"]),
        )
        for row in rows
    ]


def render_map(
    path: str | Path,
    readings: list[MapReading],
    center_x_mm: float = 125.5,
    center_y_mm: float = 105.0,
) -> Path:
    if not readings:
        raise ValueError("At least one map reading is required.")
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    import numpy as np

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    contact = [reading for reading in readings if reading.contact]
    no_contact = [reading for reading in readings if not reading.contact]

    figure, axis = plt.subplots(figsize=(8, 7))
    sample_xy = np.array(
        [
            [
                reading.point.x_mm - center_x_mm,
                reading.point.y_mm - center_y_mm,
            ]
            for reading in readings
        ]
    )
    occupancy = np.array([1.0 if reading.contact else 0.0 for reading in readings])
    grid_axis = np.linspace(-20.0, 20.0, 40)
    grid_x, grid_y = np.meshgrid(grid_axis, grid_axis)
    grid_xy = np.column_stack((grid_x.ravel(), grid_y.ravel()))
    sample_distance_sq = (
        (grid_xy[:, None, :] - sample_xy[None, :, :]) ** 2
    ).sum(axis=2)
    sample_weights = 1.0 / (sample_distance_sq + 0.35)
    projected_occupancy = (
        (sample_weights * occupancy[None, :]).sum(axis=1)
        / sample_weights.sum(axis=1)
    ).reshape(grid_x.shape)
    if contact:
        contact_xy = np.array(
            [
                [
                    reading.point.x_mm - center_x_mm,
                    reading.point.y_mm - center_y_mm,
                ]
                for reading in contact
            ]
        )
        contact_z = np.array([reading.trigger_z_mm for reading in contact])
        contact_distance_sq = (
            (grid_xy[:, None, :] - contact_xy[None, :, :]) ** 2
        ).sum(axis=2)
        contact_weights = 1.0 / (contact_distance_sq + 0.35)
        projected_height = (
            (contact_weights * contact_z[None, :]).sum(axis=1)
            / contact_weights.sum(axis=1)
        ).reshape(grid_x.shape)
        boundary_readings = [
            reading
            for reading in readings
            if reading.point.role
            in {"INNER_RIM", "TAPER_START", "TAPER", "OUTSIDE_CONTROL"}
        ]
        sector_count = 18
        sector_radii: list[float] = []
        for sector in range(sector_count):
            sector_samples = []
            for reading in boundary_readings:
                dx = reading.point.x_mm - center_x_mm
                dy = reading.point.y_mm - center_y_mm
                angle_sector = int(
                    round(
                        (math.atan2(dy, dx) % (2.0 * math.pi))
                        / (2.0 * math.pi)
                        * sector_count
                    )
                ) % sector_count
                if angle_sector == sector:
                    sector_samples.append((math.hypot(dx, dy), reading.contact))
            contact_radii = [radius for radius, hit in sector_samples if hit]
            outside_radii = [radius for radius, hit in sector_samples if not hit]
            if contact_radii and outside_radii:
                boundary = (max(contact_radii) + min(outside_radii)) / 2.0
            elif contact_radii:
                boundary = min(15.5, max(contact_radii) + 0.2)
            elif outside_radii:
                boundary = max(13.5, min(outside_radii) - 0.2)
            else:
                boundary = 14.6
            sector_radii.append(boundary)
        sector_angles = np.arange(sector_count) * 2.0 * np.pi / sector_count
        extended_angles = np.concatenate(
            ([sector_angles[-1] - 2.0 * np.pi], sector_angles, [2.0 * np.pi])
        )
        extended_radii = np.array(
            [sector_radii[-1], *sector_radii, sector_radii[0]]
        )
        grid_radius = np.hypot(grid_x, grid_y)
        grid_angle = np.mod(np.arctan2(grid_y, grid_x), 2.0 * np.pi)
        measured_boundary = np.interp(
            grid_angle.ravel(), extended_angles, extended_radii
        ).reshape(grid_x.shape)
        projected_height = np.ma.masked_where(
            grid_radius > measured_boundary, projected_height
        )
        image = axis.imshow(
            projected_height,
            origin="lower",
            extent=(-20, 20, -20, 20),
            cmap="viridis",
            alpha=0.72,
            interpolation="nearest",
        )
        figure.colorbar(image, ax=axis, label="Projected trigger Z (mm)")
    if contact:
        axis.scatter(
            [reading.point.x_mm - center_x_mm for reading in contact],
            [reading.point.y_mm - center_y_mm for reading in contact],
            facecolors="none",
            edgecolors="white",
            linewidths=0.8,
            s=28,
            label="Measured contact",
        )
    if no_contact:
        axis.scatter(
            [reading.point.x_mm - center_x_mm for reading in no_contact],
            [reading.point.y_mm - center_y_mm for reading in no_contact],
            marker="x",
            color="#d62728",
            s=38,
            label="No contact by safety floor",
        )
    axis.add_patch(
        plt.Circle((0, 0), 14.6, fill=False, linestyle="--", color="#555555")
    )
    axis.set(
        title="CR Touch 40×40 Projection — Measurement Locations Overlaid",
        xlabel="X from calibrated center (mm)",
        ylabel="Y from calibrated center (mm)",
        xlim=(-20.5, 20.5),
        ylim=(-20.5, 20.5),
        aspect="equal",
    )
    axis.grid(True, alpha=0.25)
    axis.legend(loc="upper right")
    figure.tight_layout()
    figure.savefig(output, dpi=160)
    plt.close(figure)
    return output
