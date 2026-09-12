from __future__ import annotations

from dataclasses import dataclass
import csv

from tools.plot_safe_raster import load_raster_csv

MAX_TEXT_PREVIEW_WIDTH = 80


@dataclass(frozen=True)
class RasterAcquisitionFrame:
    x_values: list[float]
    y_values: list[float]
    z_matrix: list[list[float]]
    direction_counts: dict[str, int] | None = None

    @property
    def point_count(self) -> int:
        return len(self.x_values) * len(self.y_values)

    @property
    def latest_line(self) -> list[float]:
        if not self.z_matrix:
            return []
        return list(self.z_matrix[-1])

    def signal_range(self) -> tuple[float, float]:
        values = [value for row in self.z_matrix for value in row]
        if not values:
            return (0.0, 0.0)
        return (min(values), max(values))

    def line_scan_summary(self) -> str:
        if not self.latest_line:
            return "1D Line Scan\nNo line data loaded."
        low, high = self.signal_range()
        latest_y = self.y_values[-1] if self.y_values else 0.0
        x_start = self.x_values[0] if self.x_values else 0.0
        x_end = self.x_values[-1] if self.x_values else 0.0
        return (
            "1D Line Scan\n"
            f"Directions: {self.direction_summary()}\n"
            f"Latest Y line: {latest_y:.3f}\n"
            f"X sweep: {x_start:.3f} to {x_end:.3f}\n"
            f"Latest line points: {len(self.latest_line)}\n"
            f"Z/signal range: {low:.4f} to {high:.4f}\n"
            f"Last line preview: {', '.join(f'{value:.3f}' for value in _sample_values(self.latest_line, 12))}\n"
            f"Profile: {self.line_profile_bar()}"
        )

    def topography_summary(self) -> str:
        low, high = self.signal_range()
        return (
            "2D Topography Scan\n"
            f"Grid: {len(self.x_values)} x {len(self.y_values)}\n"
            f"Raster points: {self.point_count}\n"
            f"Directional samples: {sum(self.direction_counts.values()) if self.direction_counts else self.point_count}\n"
            f"Directions: {self.direction_summary()}\n"
            f"Signal range: {low:.4f} to {high:.4f}\n\n"
            f"{self.topography_map_text()}"
        )

    def z_feedback_summary(self) -> str:
        low, high = self.signal_range()
        center_value = self.z_matrix[len(self.z_matrix) // 2][len(self.x_values) // 2]
        return (
            "Z / Signal Feedback\n"
            f"Scan directions: {self.direction_summary()}\n"
            f"Live X range: {self.x_values[0]:.3f} to {self.x_values[-1]:.3f}\n"
            f"Live Y range: {self.y_values[0]:.3f} to {self.y_values[-1]:.3f}\n"
            f"Current channel: simulated surface signal\n"
            f"Center signal: {center_value:.4f}\n"
            f"Signal min/max: {low:.4f} / {high:.4f}\n"
            f"Z source: synthetic readback until CR-Touch contact probe is mounted"
        )

    def line_profile_bar(self) -> str:
        return _render_bar(self.latest_line)

    def direction_summary(self) -> str:
        if not self.direction_counts:
            return "legacy forward-only data"
        ordered = ["forward", "backward", "upward", "downward"]
        return ", ".join(f"{direction}={self.direction_counts.get(direction, 0)}" for direction in ordered)

    def topography_map_text(self) -> str:
        low, high = self.signal_range()
        lines = []
        for row in reversed(self.z_matrix):
            lines.append(_render_bar(row, low=low, high=high))
        return "\n".join(lines)


def load_raster_frame(input_file: str) -> RasterAcquisitionFrame:
    x_values, y_values, z_matrix = load_raster_csv(input_file)
    direction_counts: dict[str, int] = {}
    with open(input_file, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            direction = row.get("scan_direction", "forward")
            direction_counts[direction] = direction_counts.get(direction, 0) + 1
    return RasterAcquisitionFrame(
        x_values=x_values,
        y_values=y_values,
        z_matrix=z_matrix,
        direction_counts=direction_counts,
    )


def _sample_values(values: list[float], max_count: int) -> list[float]:
    if len(values) <= max_count:
        return list(values)
    step = (len(values) - 1) / (max_count - 1)
    return [values[round(index * step)] for index in range(max_count)]


def _render_bar(values: list[float], low: float | None = None, high: float | None = None) -> str:
    if not values:
        return ""

    palette = " .:-=+*#%@"
    values = _sample_values(values, MAX_TEXT_PREVIEW_WIDTH)
    low = min(values) if low is None else low
    high = max(values) if high is None else high

    if high == low:
        return palette[-1] * len(values)

    chars = []
    for value in values:
        normalized = (value - low) / (high - low)
        index = round(normalized * (len(palette) - 1))
        chars.append(palette[max(0, min(len(palette) - 1, index))])
    return "".join(chars)
