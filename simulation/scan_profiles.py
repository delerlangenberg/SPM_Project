# simulation/scan_profiles.py

import numpy as np


def bumps_profile(x, y, scale=1.0):
    return 0.5 * scale * np.sin(2 * np.pi * x) * np.cos(2 * np.pi * y)


def wave_profile(x, y, scale=1.0):
    return scale * np.sin(2 * np.pi * x)


def lines_profile(x, y, scale=1.0):
    return 0.3 * scale * np.sin(4 * np.pi * x)


def grid_profile(x, y, scale=1.0):
    return scale * (np.mod(x * 5, 1.0) + np.mod(y * 5, 1.0)) * 0.2


def gaussian_bumps(x, y, centers, sigma=0.1, amplitude=1.0):
    """
    Superposition of Gaussian bumps at specified (x, y) centers.
    """
    z = np.zeros_like(x)
    for cx, cy in centers:
        z += amplitude * np.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2 * sigma ** 2))
    return z


def random_noise(x, y, scale=0.1):
    """
    Return a small random height fluctuation over the surface.
    """
    rng = np.random.default_rng(seed=42)
    return scale * rng.normal(size=x.shape)


def load_real_profile(path):
    """
    Load topography data from a real dataset (CSV, image, etc.).
    """
    try:
        return np.loadtxt(path, delimiter=',')
    except Exception:
        return np.zeros((100, 100))  # fallback


def generate_custom_surface(width, height, resolution, mode='bumps', **kwargs):
    """
    Central method to generate a topography matrix using profile functions.
    """
    x = np.linspace(0, width, resolution)
    y = np.linspace(0, height, resolution)
    X, Y = np.meshgrid(x, y)

    if mode == 'bumps':
        Z = bumps_profile(X / width, Y / height)
    elif mode == 'wave':
        Z = wave_profile(X / width, Y / height)
    elif mode == 'lines':
        Z = lines_profile(X / width, Y / height)
    elif mode == 'grid':
        Z = grid_profile(X / width, Y / height)
    elif mode == 'gaussian':
        centers = kwargs.get('centers', [(0.5, 0.5)])
        Z = gaussian_bumps(X / width, Y / height, centers)
    elif mode == 'real':
        Z = load_real_profile(kwargs.get('path', ''))
    elif mode == 'noisy':
        Z = bumps_profile(X / width, Y / height) + random_noise(X, Y)
    else:
        Z = np.zeros_like(X)

    return Z
