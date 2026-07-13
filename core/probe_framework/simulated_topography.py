from __future__ import annotations

import csv
import io
import math
from typing import List


def simulated_topography(width: int = 32, height: int = 32) -> List[List[float]]:
    if width < 2 or height < 2:
        raise ValueError("width and height must be >= 2")

    data: List[List[float]] = []
    for y in range(height):
        row: List[float] = []
        for x in range(width):
            nx = x / (width - 1)
            ny = y / (height - 1)
            hill = math.exp(-18.0 * ((nx - 0.52) ** 2 + (ny - 0.46) ** 2))
            wave = 0.12 * math.sin(6.0 * math.pi * nx) * math.cos(4.0 * math.pi * ny)
            slope = 0.08 * nx + 0.04 * ny
            row.append(round(hill + wave + slope, 6))
        data.append(row)
    return data


def topography_csv_text(data: List[List[float]]) -> str:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["y_index", "x_index", "height_simulated"])
    for y, row in enumerate(data):
        for x, value in enumerate(row):
            writer.writerow([y, x, value])
    return out.getvalue()
