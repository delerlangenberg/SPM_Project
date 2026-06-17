from dataclasses import dataclass
from datetime import datetime


@dataclass
class RasterPoint:
    timestamp: str
    scan_direction: str
    target_x: float
    target_y: float
    actual_x: float
    actual_y: float
    actual_z: float
    simulated_z_signal: float


def linspace(start, stop, count):
    """Generate count evenly spaced values from start to stop, including both ends."""
    start = float(start)
    stop = float(stop)
    count = int(count)

    if count < 2:
        return [start]

    step = (stop - start) / (count - 1)
    return [round(start + i * step, 6) for i in range(count)]


def generate_grid(x_points, y_points):
    """Generate raster points row by row."""
    for y in y_points:
        for x in x_points:
            yield x, y


def generate_grid_from_scan_area(scan_area):
    """Generate raster points from scan-area min/max/resolution settings."""
    x_points = linspace(
        scan_area["x_min"],
        scan_area["x_max"],
        scan_area["x_resolution"],
    )
    y_points = linspace(
        scan_area["y_min"],
        scan_area["y_max"],
        scan_area["y_resolution"],
    )

    return list(generate_grid(x_points, y_points))


def generate_bidirectional_grid_from_scan_area(scan_area):
    """Generate forward/backward and upward/downward raster passes."""
    x_points = linspace(
        scan_area["x_min"],
        scan_area["x_max"],
        scan_area["x_resolution"],
    )
    y_points = linspace(
        scan_area["y_min"],
        scan_area["y_max"],
        scan_area["y_resolution"],
    )

    passes = []
    for y in y_points:
        passes.extend((x, y, "forward") for x in x_points)
        passes.extend((x, y, "backward") for x in reversed(x_points))

    for x in x_points:
        passes.extend((x, y, "upward") for y in y_points)
        passes.extend((x, y, "downward") for y in reversed(y_points))

    return passes


def make_raster_row(target_x, target_y, motion_state, z_signal, scan_direction="forward"):
    """Create one raster data row from target position, printer state, and Z signal."""
    pos = motion_state["position"]
    return RasterPoint(
        timestamp=datetime.now().isoformat(timespec="seconds"),
        scan_direction=str(scan_direction),
        target_x=float(target_x),
        target_y=float(target_y),
        actual_x=float(pos.get("x")),
        actual_y=float(pos.get("y")),
        actual_z=float(pos.get("z")),
        simulated_z_signal=float(z_signal),
    )
