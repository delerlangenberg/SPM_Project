from dataclasses import asdict
import argparse
import time
import csv

from core.motion.prusa_gcode_backend import PrusaGcodeBackend
from core.z_control.z_driver_simulated import SimulatedZDriver
from core.education.safe_raster import generate_grid_from_scan_area, make_raster_row
from core.education.synthetic_signal import synthetic_surface_signal
from core.education.config_loader import (
    load_config,
    get_prusa_backend_kwargs,
    get_safe_feedrates,
    get_safe_raster_config,
)
from core.education.scan_profile import (
    MotionLimits,
    ScanProfile,
    validate_scan_profile,
)


def build_motion_limits(config: dict) -> MotionLimits:
    motion_limits = config["motion_limits"]

    return MotionLimits(
        x_min=motion_limits["x"][0],
        x_max=motion_limits["x"][1],
        y_min=motion_limits["y"][0],
        y_max=motion_limits["y"][1],
        z_min=motion_limits["z"][0],
        z_max=motion_limits["z"][1],
    )


def build_scan_profile(config: dict, args: argparse.Namespace) -> ScanProfile:
    scan_area = config["scan_area"]
    safe_feedrates = get_safe_feedrates(config)

    return ScanProfile(
        x_min=args.x_min if args.x_min is not None else scan_area["x_min"],
        x_max=args.x_max if args.x_max is not None else scan_area["x_max"],
        y_min=args.y_min if args.y_min is not None else scan_area["y_min"],
        y_max=args.y_max if args.y_max is not None else scan_area["y_max"],
        z=args.z if args.z is not None else scan_area["z"],
        x_resolution=args.x_resolution if args.x_resolution is not None else scan_area["x_resolution"],
        y_resolution=args.y_resolution if args.y_resolution is not None else scan_area["y_resolution"],
        feedrate_xy=safe_feedrates["xy"],
        feedrate_z=safe_feedrates["z"],
        mode=args.mode,
    )


def scan_area_from_profile(profile: ScanProfile) -> dict:
    return {
        "x_min": profile.x_min,
        "x_max": profile.x_max,
        "y_min": profile.y_min,
        "y_max": profile.y_max,
        "z": profile.z,
        "x_resolution": profile.x_resolution,
        "y_resolution": profile.y_resolution,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run validated configured raster scan"
    )

    parser.add_argument("--mode", default="SIMULATED_SURFACE")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output-file")

    parser.add_argument("--x-min", type=float)
    parser.add_argument("--x-max", type=float)
    parser.add_argument("--y-min", type=float)
    parser.add_argument("--y-max", type=float)
    parser.add_argument("--z", type=float)
    parser.add_argument("--x-resolution", type=int)
    parser.add_argument("--y-resolution", type=int)

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    config = load_config()
    backend_kwargs = get_prusa_backend_kwargs(config)
    raster_config = get_safe_raster_config(config)

    profile = build_scan_profile(config, args)
    limits = build_motion_limits(config)

    try:
        validate_scan_profile(profile, limits)
    except ValueError as error:
        print("Validation: FAIL")
        print(f"Reason: {error}")
        raise SystemExit(1)

    active_scan_area = scan_area_from_profile(profile)
    output_file = args.output_file if args.output_file is not None else raster_config["output_file"]

    print("Validated configured raster scan")
    print("Validation: PASS")
    print(f"Scan profile: {profile}")
    print(f"Output file: {output_file}")

    if args.dry_run:
        print("Dry run only. No hardware movement.")
        return

    motion = PrusaGcodeBackend(**backend_kwargs)
    z_driver = SimulatedZDriver()
    data = []

    try:
        motion.connect()
        print("Connected:", motion.get_state())

        print(f"Moving to safe scan height Z{profile.z}...")
        motion.move_to(z=profile.z, feedrate=profile.feedrate_z)

        print("Starting educational raster scan...")

        for x, y in generate_grid_from_scan_area(active_scan_area):
            print(f"Point X{x} Y{y}")
            motion.move_to(x=x, y=y, feedrate=profile.feedrate_xy)

            z_driver.move_to(synthetic_surface_signal(x, y))
            z_value = z_driver.get_position()

            state = motion.get_state()
            row = make_raster_row(x, y, state, z_value)
            data.append(asdict(row))

            print(asdict(row))
            time.sleep(0.3)

        with open(output_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

        print("Saved:", output_file)

    finally:
        motion.disconnect()
        z_driver.close()
        print("Disconnected")


if __name__ == "__main__":
    main()
