import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.education.config_loader import (
    load_config,
    get_safe_feedrates,
    get_safe_raster_config,
)
from core.education.scan_profile import (
    MotionLimits,
    ScanProfile,
    validate_scan_profile,
)


def build_scan_profile_from_config(config: dict, mode: str) -> ScanProfile:
    scan_area = config["scan_area"]
    safe_feedrates = get_safe_feedrates(config)

    return ScanProfile(
        x_min=scan_area["x_min"],
        x_max=scan_area["x_max"],
        y_min=scan_area["y_min"],
        y_max=scan_area["y_max"],
        z=scan_area["z"],
        x_resolution=scan_area["x_resolution"],
        y_resolution=scan_area["y_resolution"],
        feedrate_xy=safe_feedrates["xy"],
        feedrate_z=safe_feedrates["z"],
        mode=mode,
    )


def apply_cli_overrides(profile: ScanProfile, args: argparse.Namespace) -> ScanProfile:
    return ScanProfile(
        x_min=args.x_min if args.x_min is not None else profile.x_min,
        x_max=args.x_max if args.x_max is not None else profile.x_max,
        y_min=args.y_min if args.y_min is not None else profile.y_min,
        y_max=args.y_max if args.y_max is not None else profile.y_max,
        z=args.z if args.z is not None else profile.z,
        x_resolution=args.x_resolution if args.x_resolution is not None else profile.x_resolution,
        y_resolution=args.y_resolution if args.y_resolution is not None else profile.y_resolution,
        feedrate_xy=args.feedrate_xy if getattr(args, "feedrate_xy", None) is not None else profile.feedrate_xy,
        feedrate_z=args.feedrate_z if getattr(args, "feedrate_z", None) is not None else profile.feedrate_z,
        mode=profile.mode,
    )


def build_motion_limits_from_config(config: dict) -> MotionLimits:
    motion_limits = config["motion_limits"]

    return MotionLimits(
        x_min=motion_limits["x"][0],
        x_max=motion_limits["x"][1],
        y_min=motion_limits["y"][0],
        y_max=motion_limits["y"][1],
        z_min=motion_limits["z"][0],
        z_max=motion_limits["z"][1],
    )


def build_hardware_command(
    profile: ScanProfile,
    output_file: str | None = None,
    dry_run: bool = False,
) -> list[str]:
    command = [
        sys.executable,
        "tools/run_configured_raster_scan.py",
        "--mode",
        profile.mode,
        "--x-min",
        str(profile.x_min),
        "--x-max",
        str(profile.x_max),
        "--y-min",
        str(profile.y_min),
        "--y-max",
        str(profile.y_max),
        "--z",
        str(profile.z),
        "--x-resolution",
        str(profile.x_resolution),
        "--y-resolution",
        str(profile.y_resolution),
        "--feedrate-xy",
        str(profile.feedrate_xy),
        "--feedrate-z",
        str(profile.feedrate_z),
    ]

    if dry_run:
        command.insert(2, "--dry-run")

    if output_file is not None:
        command.extend(["--output-file", output_file])

    return command


def run_verified_hardware_raster(profile: ScanProfile, output_file: str | None = None) -> int:
    result = subprocess.run(
        build_hardware_command(profile, output_file),
        check=False,
    )
    return result.returncode


def run_verified_software_raster(profile: ScanProfile, output_file: str | None = None) -> int:
    result = subprocess.run(
        build_hardware_command(profile, output_file, dry_run=True),
        check=False,
    )
    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SPM educational scan launcher"
    )

    parser.add_argument("--mode", default="SIMULATED_SURFACE")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute-hardware", action="store_true")
    parser.add_argument("--output-file")

    parser.add_argument("--x-min", type=float)
    parser.add_argument("--x-max", type=float)
    parser.add_argument("--y-min", type=float)
    parser.add_argument("--y-max", type=float)
    parser.add_argument("--z", type=float)
    parser.add_argument("--x-resolution", type=int)
    parser.add_argument("--y-resolution", type=int)
    parser.add_argument("--feedrate-xy", type=float)
    parser.add_argument("--feedrate-z", type=float)

    args = parser.parse_args()

    config = load_config()
    profile = build_scan_profile_from_config(config, args.mode)
    profile = apply_cli_overrides(profile, args)
    limits = build_motion_limits_from_config(config)

    try:
        validate_scan_profile(profile, limits)
    except ValueError as error:
        print("Validation: FAIL")
        print(f"Reason: {error}")
        raise SystemExit(1)

    raster_config = get_safe_raster_config(config)
    output_file = args.output_file if args.output_file is not None else raster_config["output_file"]

    print("SPM CLI scan launcher")
    print("Validation: PASS")
    print(f"Mode: {profile.mode}")
    print(f"Scan profile: {profile}")
    print(f"Output file: {output_file}")

    if args.dry_run:
        print("Dry run requested. No hardware movement.")
        print("Generating verified synthetic raster output...")
        exit_code = run_verified_software_raster(profile, output_file)

        if exit_code != 0:
            raise SystemExit(exit_code)

        print("Dry-run synthetic raster complete.")
        return

    if args.execute_hardware:
        print("Hardware execution requested.")
        print("Running verified configured raster scan with CLI profile...")
        exit_code = run_verified_hardware_raster(profile, output_file)

        if exit_code != 0:
            raise SystemExit(exit_code)

        print("Hardware raster scan complete.")
        return

    print("No hardware execution requested.")
    print("Use --dry-run for validation only.")
    print("Use --execute-hardware only when the printer area is clear.")


if __name__ == "__main__":
    main()
