"""Stage 9 — Scientific Surface Metrology and Analysis.

Implements:
- Regular TopographyGrid data structure with physical units (mm / µm / nm).
- 1st-order plane leveling and 2nd-order polynomial background removal.
- Median despiking and Gaussian filtering.
- ISO 4287 / ISO 25178 surface roughness metrics (Sa, Sq, Sz, Sp, Sv, Ssk, Sku).
- Arbitrary line profile extraction with bilinear interpolation and step-height evaluation.
- Particle / island segmentation and volumetric feature analysis.
- Publication-quality 2D and 3D topography rendering.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import math
from pathlib import Path
import os
import tempfile
if "MPLCONFIGDIR" not in os.environ:
    mpl_temp = Path(tempfile.gettempdir()) / "matplotlib_spm"
    mpl_temp.mkdir(parents=True, exist_ok=True)
    os.environ["MPLCONFIGDIR"] = str(mpl_temp)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
import numpy as np


@dataclass
class TopographyGrid:
    """Represents a structured 2D surface height map."""

    x_coords: np.ndarray  # 1D array of X coordinates (mm)
    y_coords: np.ndarray  # 1D array of Y coordinates (mm)
    z_matrix: np.ndarray  # 2D array [len(y), len(x)] of Z heights (mm)
    unit_xy: str = "mm"
    unit_z: str = "mm"
    mask: Optional[np.ndarray] = None  # 2D boolean array (True = valid, False = masked/invalid)

    def __post_init__(self) -> None:
        self.x_coords = np.asarray(self.x_coords, dtype=np.float64)
        self.y_coords = np.asarray(self.y_coords, dtype=np.float64)
        self.z_matrix = np.asarray(self.z_matrix, dtype=np.float64)
        if self.z_matrix.shape != (len(self.y_coords), len(self.x_coords)):
            raise ValueError(
                f"Shape mismatch: z_matrix shape {self.z_matrix.shape} does not match "
                f"(len(y)={len(self.y_coords)}, len(x)={len(self.x_coords)})"
            )
        if self.mask is None:
            self.mask = np.ones_like(self.z_matrix, dtype=bool)
        else:
            self.mask = np.asarray(self.mask, dtype=bool)

    @property
    def shape(self) -> Tuple[int, int]:
        return self.z_matrix.shape

    @property
    def dx(self) -> float:
        if len(self.x_coords) < 2:
            return 0.0
        return float(np.mean(np.diff(self.x_coords)))

    @property
    def dy(self) -> float:
        if len(self.y_coords) < 2:
            return 0.0
        return float(np.mean(np.diff(self.y_coords)))

    def copy(self) -> TopographyGrid:
        return TopographyGrid(
            x_coords=self.x_coords.copy(),
            y_coords=self.y_coords.copy(),
            z_matrix=self.z_matrix.copy(),
            unit_xy=self.unit_xy,
            unit_z=self.unit_z,
            mask=self.mask.copy() if self.mask is not None else None,
        )


@dataclass(frozen=True)
class RoughnessParameters:
    """ISO 25178 / ISO 4287 compliant surface roughness parameters."""

    sa_mm: float  # Arithmetic mean height
    sq_mm: float  # Root mean square height
    sz_mm: float  # Maximum height (peak-to-valley)
    sp_mm: float  # Maximum peak height above mean
    sv_mm: float  # Maximum pit depth below mean
    ssk: float  # Skewness (degree of asymmetry)
    sku: float  # Kurtosis (peakedness / sharpness)
    valid_points: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LineProfile:
    """Represents a 1D cross-sectional profile extracted from topography."""

    x_points: np.ndarray
    y_points: np.ndarray
    distance_along_profile_mm: np.ndarray
    z_heights_mm: np.ndarray
    unit_xy: str = "mm"
    unit_z: str = "mm"

    def to_dict(self) -> dict[str, Any]:
        return {
            "num_points": len(self.distance_along_profile_mm),
            "total_length_mm": float(self.distance_along_profile_mm[-1]) if len(self.distance_along_profile_mm) > 0 else 0.0,
            "z_min_mm": float(np.min(self.z_heights_mm)) if len(self.z_heights_mm) > 0 else 0.0,
            "z_max_mm": float(np.max(self.z_heights_mm)) if len(self.z_heights_mm) > 0 else 0.0,
            "z_range_mm": float(np.ptp(self.z_heights_mm)) if len(self.z_heights_mm) > 0 else 0.0,
        }


@dataclass(frozen=True)
class ParticleFeature:
    """Quantitative metrics for a detected surface island or particle."""

    particle_id: int
    centroid_x_mm: float
    centroid_y_mm: float
    area_mm2: float
    equivalent_diameter_mm: float
    peak_height_mm: float
    mean_height_mm: float
    volume_mm3: float
    pixel_count: int


@dataclass(frozen=True)
class FeatureDetectionResult:
    """Aggregation of detected surface features."""

    particle_count: int
    threshold_z_mm: float
    particles: List[ParticleFeature]
    total_area_mm2: float
    total_volume_mm3: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "particle_count": self.particle_count,
            "threshold_z_mm": self.threshold_z_mm,
            "total_area_mm2": self.total_area_mm2,
            "total_volume_mm3": self.total_volume_mm3,
            "particles": [asdict(p) for p in self.particles],
        }


def level_plane(grid: TopographyGrid) -> TopographyGrid:
    """Performs first-order least-squares plane leveling (tilt correction).

    Fits Z = a*X + b*Y + c and subtracts the fitted plane from Z.
    """
    x_mesh, y_mesh = np.meshgrid(grid.x_coords, grid.y_coords)
    valid = grid.mask if grid.mask is not None else np.ones_like(grid.z_matrix, dtype=bool)

    x_val = x_mesh[valid]
    y_val = y_mesh[valid]
    z_val = grid.z_matrix[valid]

    if len(z_val) < 3:
        raise ValueError("Cannot level plane: fewer than 3 valid data points available.")

    # Design matrix [X, Y, 1]
    a_matrix = np.column_stack([x_val, y_val, np.ones_like(x_val)])
    coeff, _, _, _ = np.linalg.lstsq(a_matrix, z_val, rcond=None)
    a, b, c = coeff

    # Subtract plane across entire grid
    fitted_plane = a * x_mesh + b * y_mesh + c
    leveled_z = grid.z_matrix - fitted_plane

    result = grid.copy()
    result.z_matrix = leveled_z
    return result


def subtract_polynomial_background(grid: TopographyGrid, degree: int = 2) -> TopographyGrid:
    """Performs 2nd-order polynomial surface background subtraction.

    Fits Z = c0 + c1*X + c2*Y + c3*X^2 + c4*Y^2 + c5*X*Y and subtracts it.
    Eliminates scanner bow, thermal drift, and sample curvature.
    """
    if degree != 2:
        raise NotImplementedError("Currently only degree=2 polynomial background subtraction is supported.")

    x_mesh, y_mesh = np.meshgrid(grid.x_coords, grid.y_coords)
    valid = grid.mask if grid.mask is not None else np.ones_like(grid.z_matrix, dtype=bool)

    x_val = x_mesh[valid]
    y_val = y_mesh[valid]
    z_val = grid.z_matrix[valid]

    if len(z_val) < 6:
        raise ValueError("Cannot fit 2nd order polynomial: fewer than 6 valid data points.")

    a_matrix = np.column_stack([
        np.ones_like(x_val),
        x_val,
        y_val,
        x_val**2,
        y_val**2,
        x_val * y_val,
    ])
    coeff, _, _, _ = np.linalg.lstsq(a_matrix, z_val, rcond=None)

    full_design = np.column_stack([
        np.ones(x_mesh.size),
        x_mesh.ravel(),
        y_mesh.ravel(),
        (x_mesh**2).ravel(),
        (y_mesh**2).ravel(),
        (x_mesh * y_mesh).ravel(),
    ])
    fitted_background = full_design.dot(coeff).reshape(grid.shape)

    result = grid.copy()
    result.z_matrix = grid.z_matrix - fitted_background
    return result


def zero_reference(grid: TopographyGrid, method: str = "min") -> TopographyGrid:
    """Offsets height values so the minimum or mean height is 0.0."""
    valid = grid.mask if grid.mask is not None else np.ones_like(grid.z_matrix, dtype=bool)
    z_valid = grid.z_matrix[valid]

    if len(z_valid) == 0:
        return grid.copy()

    offset = float(np.min(z_valid)) if method == "min" else float(np.mean(z_valid))
    result = grid.copy()
    result.z_matrix = grid.z_matrix - offset
    return result


def apply_median_filter(grid: TopographyGrid, kernel_size: int = 3) -> TopographyGrid:
    """Applies a 2D median filter for despiking and artifact suppression."""
    if kernel_size < 1 or kernel_size % 2 == 0:
        raise ValueError("Kernel size must be an odd positive integer.")

    pad_width = kernel_size // 2
    padded = np.pad(grid.z_matrix, pad_width=pad_width, mode="reflect")

    # Vectorized sliding window median
    windows = np.lib.stride_tricks.sliding_window_view(padded, (kernel_size, kernel_size))
    filtered_z = np.median(windows, axis=(-2, -1))

    result = grid.copy()
    result.z_matrix = filtered_z
    return result


def apply_gaussian_filter(grid: TopographyGrid, sigma: float = 1.0) -> TopographyGrid:
    """Applies a 2D Gaussian smoothing filter."""
    if sigma <= 0:
        return grid.copy()

    radius = int(math.ceil(3.0 * sigma))
    size = 2 * radius + 1
    y, x = np.mgrid[-radius:radius+1, -radius:radius+1]
    kernel = np.exp(-(x**2 + y**2) / (2.0 * sigma**2))
    kernel /= np.sum(kernel)

    padded = np.pad(grid.z_matrix, pad_width=radius, mode="reflect")
    windows = np.lib.stride_tricks.sliding_window_view(padded, (size, size))
    filtered_z = np.sum(windows * kernel, axis=(-2, -1))

    result = grid.copy()
    result.z_matrix = filtered_z
    return result


def calculate_roughness(grid: TopographyGrid) -> RoughnessParameters:
    """Calculates ISO 25178 areal surface roughness metrics."""
    valid = grid.mask if grid.mask is not None else np.ones_like(grid.z_matrix, dtype=bool)
    z_valid = grid.z_matrix[valid]

    n = len(z_valid)
    if n < 2:
        return RoughnessParameters(
            sa_mm=0.0, sq_mm=0.0, sz_mm=0.0, sp_mm=0.0, sv_mm=0.0,
            ssk=0.0, sku=0.0, valid_points=n
        )

    mean_z = np.mean(z_valid)
    deviations = z_valid - mean_z

    sa = float(np.mean(np.abs(deviations)))
    sq = float(np.sqrt(np.mean(deviations**2)))
    sz = float(np.max(z_valid) - np.min(z_valid))
    sp = float(np.max(z_valid) - mean_z)
    sv = float(mean_z - np.min(z_valid))

    if sq > 1e-12:
        ssk = float(np.mean(deviations**3) / (sq**3))
        sku = float(np.mean(deviations**4) / (sq**4))
    else:
        ssk = 0.0
        sku = 3.0  # Gaussian baseline

    return RoughnessParameters(
        sa_mm=sa,
        sq_mm=sq,
        sz_mm=sz,
        sp_mm=sp,
        sv_mm=sv,
        ssk=ssk,
        sku=sku,
        valid_points=n,
    )


def extract_line_profile(
    grid: TopographyGrid,
    start_xy: Tuple[float, float],
    end_xy: Tuple[float, float],
    num_points: int = 100,
) -> LineProfile:
    """Extracts a cross-sectional profile along a line segment using bilinear interpolation."""
    if num_points < 2:
        raise ValueError("num_points must be at least 2.")

    x0, y0 = start_xy
    x1, y1 = end_xy

    x_line = np.linspace(x0, x1, num_points)
    y_line = np.linspace(y0, y1, num_points)

    dx_total = x1 - x0
    dy_total = y1 - y0
    dist_along = np.sqrt((x_line - x0)**2 + (y_line - y0)**2)

    # Convert coordinates to fractional indices in grid
    x_min, x_max = grid.x_coords[0], grid.x_coords[-1]
    y_min, y_max = grid.y_coords[0], grid.y_coords[-1]

    nx = len(grid.x_coords)
    ny = len(grid.y_coords)

    # Normalized indices
    xi = (x_line - x_min) / (x_max - x_min) * (nx - 1) if nx > 1 else np.zeros_like(x_line)
    yi = (y_line - y_min) / (y_max - y_min) * (ny - 1) if ny > 1 else np.zeros_like(y_line)

    xi = np.clip(xi, 0, nx - 1)
    yi = np.clip(yi, 0, ny - 1)

    x_floor = np.floor(xi).astype(int)
    y_floor = np.floor(yi).astype(int)
    x_ceil = np.clip(x_floor + 1, 0, nx - 1)
    y_ceil = np.clip(y_floor + 1, 0, ny - 1)

    wx = xi - x_floor
    wy = yi - y_floor

    # Bilinear interpolation
    q11 = grid.z_matrix[y_floor, x_floor]
    q21 = grid.z_matrix[y_floor, x_ceil]
    q12 = grid.z_matrix[y_ceil, x_floor]
    q22 = grid.z_matrix[y_ceil, x_ceil]

    z_interp = (
        q11 * (1 - wx) * (1 - wy)
        + q21 * wx * (1 - wy)
        + q12 * (1 - wx) * wy
        + q22 * wx * wy
    )

    return LineProfile(
        x_points=x_line,
        y_points=y_line,
        distance_along_profile_mm=dist_along,
        z_heights_mm=z_interp,
        unit_xy=grid.unit_xy,
        unit_z=grid.unit_z,
    )


def calculate_step_height(
    profile: LineProfile,
    lower_plateau_range: Tuple[float, float],
    upper_plateau_range: Tuple[float, float],
) -> dict[str, float]:
    """Calculates step height between two distance plateaus along a line profile."""
    d = profile.distance_along_profile_mm
    z = profile.z_heights_mm

    lower_mask = (d >= lower_plateau_range[0]) & (d <= lower_plateau_range[1])
    upper_mask = (d >= upper_plateau_range[0]) & (d <= upper_plateau_range[1])

    z_lower = z[lower_mask]
    z_upper = z[upper_mask]

    if len(z_lower) == 0 or len(z_upper) == 0:
        raise ValueError("Insufficient points within specified plateau ranges.")

    mean_lower = float(np.mean(z_lower))
    mean_upper = float(np.mean(z_upper))
    std_lower = float(np.std(z_lower, ddof=1)) if len(z_lower) > 1 else 0.0
    std_upper = float(np.std(z_upper, ddof=1)) if len(z_upper) > 1 else 0.0

    step_height = mean_upper - mean_lower
    standard_error = math.sqrt(
        (std_lower**2 / len(z_lower)) + (std_upper**2 / len(z_upper))
    )

    return {
        "step_height_mm": step_height,
        "standard_error_mm": standard_error,
        "lower_plateau_mean_mm": mean_lower,
        "lower_plateau_std_mm": std_lower,
        "lower_points": len(z_lower),
        "upper_plateau_mean_mm": mean_upper,
        "upper_plateau_std_mm": std_upper,
        "upper_points": len(z_upper),
    }


def detect_particles(
    grid: TopographyGrid,
    threshold_z_mm: Optional[float] = None,
    min_pixel_area: int = 3,
) -> FeatureDetectionResult:
    """Performs connected-component segmentation to detect surface particles/features.

    Uses an 8-connected flood-fill algorithm in pure vectorized/array Python without external dependencies.
    """
    if threshold_z_mm is None:
        # Default: Mean + 2 * Sq (Standard deviation above baseline)
        roughness = calculate_roughness(grid)
        threshold_z_mm = float(np.mean(grid.z_matrix)) + 2.0 * roughness.sq_mm

    binary_mask = (grid.z_matrix > threshold_z_mm)
    if grid.mask is not None:
        binary_mask &= grid.mask

    ny, nx = grid.shape
    labeled = np.zeros((ny, nx), dtype=int)
    current_label = 0

    # 8-connectivity offsets
    neighbors = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1),
    ]

    for r in range(ny):
        for c in range(nx):
            if binary_mask[r, c] and labeled[r, c] == 0:
                current_label += 1
                queue = [(r, c)]
                labeled[r, c] = current_label

                while queue:
                    curr_r, curr_c = queue.pop(0)
                    for dr, dc in neighbors:
                        nr, nc = curr_r + dr, curr_c + dc
                        if 0 <= nr < ny and 0 <= nc < nx:
                            if binary_mask[nr, nc] and labeled[nr, nc] == 0:
                                labeled[nr, nc] = current_label
                                queue.append((nr, nc))

    pixel_area_mm2 = abs(grid.dx * grid.dy) if (grid.dx != 0 and grid.dy != 0) else 1.0

    particles: List[ParticleFeature] = []
    total_area = 0.0
    total_volume = 0.0

    x_mesh, y_mesh = np.meshgrid(grid.x_coords, grid.y_coords)

    for label_id in range(1, current_label + 1):
        p_mask = (labeled == label_id)
        pixel_count = int(np.sum(p_mask))
        if pixel_count < min_pixel_area:
            continue

        p_x = x_mesh[p_mask]
        p_y = y_mesh[p_mask]
        p_z = grid.z_matrix[p_mask]

        centroid_x = float(np.mean(p_x))
        centroid_y = float(np.mean(p_y))
        area_mm2 = pixel_count * pixel_area_mm2
        equiv_diam_mm = 2.0 * math.sqrt(area_mm2 / math.pi)

        # Baseline reference for height is threshold_z_mm
        relative_z = p_z - threshold_z_mm
        peak_height_mm = float(np.max(relative_z))
        mean_height_mm = float(np.mean(relative_z))
        volume_mm3 = float(np.sum(relative_z) * pixel_area_mm2)

        particles.append(
            ParticleFeature(
                particle_id=len(particles) + 1,
                centroid_x_mm=centroid_x,
                centroid_y_mm=centroid_y,
                area_mm2=area_mm2,
                equivalent_diameter_mm=equiv_diam_mm,
                peak_height_mm=peak_height_mm,
                mean_height_mm=mean_height_mm,
                volume_mm3=volume_mm3,
                pixel_count=pixel_count,
            )
        )
        total_area += area_mm2
        total_volume += volume_mm3

    return FeatureDetectionResult(
        particle_count=len(particles),
        threshold_z_mm=float(threshold_z_mm),
        particles=particles,
        total_area_mm2=total_area,
        total_volume_mm3=total_volume,
    )


def render_topography_2d(
    grid: TopographyGrid,
    save_path: Path,
    title: str = "SPM 2D Topography Map",
    cmap: str = "viridis",
) -> Path:
    """Renders and saves a calibrated 2D false-color topography plot."""
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 7), dpi=300)
    extent = [grid.x_coords[0], grid.x_coords[-1], grid.y_coords[0], grid.y_coords[-1]]

    # Determine scaling unit for visualization (convert small mm to µm if useful)
    z_ptp = np.ptp(grid.z_matrix)
    if z_ptp < 0.05 and z_ptp > 0:  # < 50 µm
        display_z = grid.z_matrix * 1000.0
        z_label = "Height (µm)"
    else:
        display_z = grid.z_matrix
        z_label = f"Height ({grid.unit_z})"

    im = ax.imshow(
        display_z,
        origin="lower",
        extent=extent,
        cmap=cmap,
        aspect="equal",
        interpolation="bilinear",
    )
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(z_label, fontsize=11, fontweight="bold")

    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel(f"X ({grid.unit_xy})", fontsize=11)
    ax.set_ylabel(f"Y ({grid.unit_xy})", fontsize=11)
    ax.grid(True, linestyle="--", alpha=0.3)

    plt.tight_layout()
    fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)
    return save_path


def render_topography_3d(
    grid: TopographyGrid,
    save_path: Path,
    title: str = "SPM 3D Surface Topography",
    cmap: str = "viridis",
    elevation: int = 30,
    azimuth: int = -60,
) -> Path:
    """Renders and saves an interactive/publication 3D surface mesh plot."""
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(10, 8), dpi=300)
    ax = fig.add_subplot(111, projection="3d")

    x_mesh, y_mesh = np.meshgrid(grid.x_coords, grid.y_coords)
    z_ptp = np.ptp(grid.z_matrix)
    if z_ptp < 0.05 and z_ptp > 0:
        display_z = grid.z_matrix * 1000.0
        z_label = "Height (µm)"
    else:
        display_z = grid.z_matrix
        z_label = f"Height ({grid.unit_z})"

    surf = ax.plot_surface(
        x_mesh,
        y_mesh,
        display_z,
        cmap=cmap,
        linewidth=0.2,
        antialiased=True,
        rstride=1,
        cstride=1,
        edgecolor="none",
    )

    cbar = fig.colorbar(surf, ax=ax, shrink=0.55, aspect=12, pad=0.08)
    cbar.set_label(z_label, fontsize=11, fontweight="bold")

    ax.set_title(title, fontsize=13, fontweight="bold", pad=16)
    ax.set_xlabel(f"X ({grid.unit_xy})", fontsize=10, labelpad=8)
    ax.set_ylabel(f"Y ({grid.unit_xy})", fontsize=10, labelpad=8)
    ax.set_zlabel(z_label, fontsize=10, labelpad=8)
    ax.view_init(elev=elevation, azim=azimuth)

    plt.tight_layout()
    fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)
    return save_path


def render_profile_plot(
    profile: LineProfile,
    save_path: Path,
    title: str = "Extracted Line Profile",
) -> Path:
    """Renders and saves a 1D cross-sectional profile plot."""
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(9, 4.5), dpi=300)

    z_ptp = np.ptp(profile.z_heights_mm)
    if z_ptp < 0.05 and z_ptp > 0:
        display_z = profile.z_heights_mm * 1000.0
        z_label = "Height (µm)"
    else:
        display_z = profile.z_heights_mm
        z_label = f"Height ({profile.unit_z})"

    ax.plot(
        profile.distance_along_profile_mm,
        display_z,
        color="#1f77b4",
        lw=2.0,
        label="Surface Cross-section",
    )
    ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel(f"Distance Along Profile ({profile.unit_xy})", fontsize=10)
    ax.set_ylabel(z_label, fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="best", frameon=True)

    plt.tight_layout()
    fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)
    return save_path
