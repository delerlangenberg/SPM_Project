from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import serial

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.system.hardware_initialized_profile import get_motion_controller_settings


DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_CSV_OUT = DATA_DIR / "phase9_xy_10x10_topography_skeleton.csv"
DEFAULT_PNG_OUT = DATA_DIR / "phase9_xy_10x10_topography_skeleton.png"
DEFAULT_RAW_LOG = DATA_DIR / "phase9_xy_10x10_topography_skeleton_raw_serial.txt"
DEFAULT_METADATA = DATA_DIR / "phase9_xy_10x10_topography_skeleton.metadata.json"

SAFE_CENTER_X = 125.0
SAFE_CENTER_Y = 105.0
SAFE_RETRACT_Z = 120.0
CONTACT_Z = 56.0


class ControllerTimeoutError(TimeoutError):
    def __init__(self, command: str, timeout_s: float, lines: list[str]):
        super().__init__(f"No ok received for {command!r} within {timeout_s:.1f}s")
        self.command = command
        self.timeout_s = timeout_s
        self.lines = list(lines)


@dataclass
class ScanPoint:
    point: int
    row: int
    col: int
    x: float
    y: float
    contact_z: float
    status: str
    method: str
    started_at: str
    completed_at: str
    position_response: str
    command_count: int


class RawSerialLogger:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.path.open("a", encoding="utf-8")

    def write(self, message: str) -> None:
        stamp = datetime.now().isoformat(timespec="milliseconds")
        self.handle.write(f"{stamp} {message}\n")
        self.handle.flush()

    def close(self) -> None:
        self.handle.close()


class RobustPrusaExecutor:
    def __init__(self, port: str, baudrate: int, raw_log: RawSerialLogger):
        self.port = port
        self.baudrate = int(baudrate)
        self.raw_log = raw_log
        self.serial = None
        self.command_count = 0

    def connect(self) -> None:
        self.raw_log.write(f"[OPEN] {self.port} @ {self.baudrate}")
        self.serial = serial.Serial(self.port, self.baudrate, timeout=0.5)
        time.sleep(2.0)
        self.drain_startup_lines(duration_s=1.5)

    def close(self) -> None:
        if self.serial is not None:
            self.raw_log.write("[CLOSE] serial port")
            self.serial.close()
            self.serial = None

    def drain_startup_lines(self, duration_s: float) -> None:
        assert self.serial is not None
        end = time.monotonic() + duration_s
        while time.monotonic() < end:
            raw = self.serial.readline()
            if raw:
                line = raw.decode(errors="replace").strip()
                if line:
                    print(line)
                    self.raw_log.write(f"<< {line}")

    def send(self, command: str, *, timeout_s: float, settle_s: float = 0.05) -> list[str]:
        assert self.serial is not None
        self.command_count += 1
        command = command.strip()
        print("")
        print(f">>> {command}")
        self.raw_log.write(f">> {command}")
        self.serial.write((command + "\n").encode("ascii", errors="replace"))
        self.serial.flush()
        if settle_s > 0:
            time.sleep(settle_s)
        return self.read_until_ok(command, timeout_s=timeout_s)

    def read_until_ok(self, command: str, *, timeout_s: float) -> list[str]:
        assert self.serial is not None
        lines: list[str] = []
        deadline = time.monotonic() + timeout_s
        last_activity = time.monotonic()

        while time.monotonic() < deadline:
            raw = self.serial.readline()
            if not raw:
                continue
            line = raw.decode(errors="replace").strip()
            if not line:
                continue
            last_activity = time.monotonic()
            print(line)
            self.raw_log.write(f"<< {line}")
            lines.append(line)

            lowered = line.lower()
            if lowered == "ok" or lowered.startswith("ok "):
                return lines
            if "busy:" in lowered:
                # Busy is normal during long MK4 motion. Keep waiting until the full deadline.
                continue

        self.raw_log.write(
            f"[TIMEOUT] command={command!r} timeout={timeout_s:.1f}s "
            f"lines={len(lines)} last_activity_age={time.monotonic() - last_activity:.1f}s"
        )
        raise ControllerTimeoutError(command, timeout_s, lines)

    def move_and_wait(self, command: str, *, move_timeout_s: float, wait_timeout_s: float) -> None:
        self.send(command, timeout_s=move_timeout_s)
        self.send("M400", timeout_s=wait_timeout_s)

    def read_position(self, *, timeout_s: float = 30.0) -> list[str]:
        return self.send("M114", timeout_s=timeout_s)


def build_points(size: int) -> list[tuple[int, int, float, float]]:
    if size < 1:
        raise ValueError("size must be at least 1")
    if size == 1:
        return [(1, 1, SAFE_CENTER_X, SAFE_CENTER_Y)]

    x_points = [105.0 + i * (40.0 / (size - 1)) for i in range(size)]
    y_points = [85.0 + i * (40.0 / (size - 1)) for i in range(size)]
    points: list[tuple[int, int, float, float]] = []
    for row_index, y in enumerate(y_points, start=1):
        ordered_x = x_points if row_index % 2 == 1 else list(reversed(x_points))
        for col_index, x in enumerate(ordered_x, start=1):
            points.append((row_index, col_index, round(x, 3), round(y, 3)))
    return points


def write_partial_csv(path: Path, rows: list[ScanPoint]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(rows[0]).keys()) if rows else [
        "point",
        "row",
        "col",
        "x",
        "y",
        "contact_z",
        "status",
        "method",
        "started_at",
        "completed_at",
        "position_response",
        "command_count",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_metadata(path: Path, metadata: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)


def plot_partial(csv_path: Path, png_path: Path) -> None:
    rows: list[dict[str, str]] = []
    if csv_path.exists():
        with csv_path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))

    completed = [row for row in rows if row.get("status") == "complete"]
    if not completed:
        png_path.parent.mkdir(parents=True, exist_ok=True)
        plt.figure(figsize=(6, 4))
        plt.text(0.5, 0.5, "No completed points yet", ha="center", va="center")
        plt.axis("off")
        plt.savefig(png_path, dpi=160, bbox_inches="tight")
        plt.close()
        return

    xs = sorted({float(row["x"]) for row in completed})
    ys = sorted({float(row["y"]) for row in completed})
    z_by_xy = {(float(row["x"]), float(row["y"])): float(row["contact_z"]) for row in completed}
    z_grid = []
    for y in ys:
        z_grid.append([z_by_xy.get((x, y), float("nan")) for x in xs])

    png_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(7, 6))
    plt.imshow(
        z_grid,
        origin="lower",
        extent=[min(xs), max(xs), min(ys), max(ys)],
        aspect="auto",
    )
    plt.colorbar(label="Contact Z (mm)")
    plt.xlabel("X position (mm)")
    plt.ylabel("Y position (mm)")
    plt.title(f"Phase 9.6 Partial XY Topography ({len(completed)} points)")
    plt.savefig(png_path, dpi=200, bbox_inches="tight")
    plt.close()


def load_existing_rows(csv_path: Path) -> list[ScanPoint]:
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = []
        for row in csv.DictReader(handle):
            rows.append(
                ScanPoint(
                    point=int(row["point"]),
                    row=int(row["row"]),
                    col=int(row["col"]),
                    x=float(row["x"]),
                    y=float(row["y"]),
                    contact_z=float(row["contact_z"]),
                    status=row["status"],
                    method=row["method"],
                    started_at=row["started_at"],
                    completed_at=row["completed_at"],
                    position_response=row["position_response"],
                    command_count=int(row["command_count"]),
                )
            )
        return rows


def completed_point_numbers(rows: Iterable[ScanPoint]) -> set[int]:
    return {row.point for row in rows if row.status == "complete"}


def safe_return(executor: RobustPrusaExecutor | None, metadata: dict) -> None:
    if executor is None or executor.serial is None:
        metadata["safe_return_status"] = "not_started_no_serial_connection"
        return
    print("")
    print("SAFETY RETURN: retract Z, then return XY to foam center.")
    metadata["safe_return_started_at"] = datetime.now().isoformat(timespec="seconds")
    try:
        executor.move_and_wait(f"G1 Z{SAFE_RETRACT_Z:.2f} F600", move_timeout_s=90, wait_timeout_s=180)
        executor.move_and_wait(
            f"G1 X{SAFE_CENTER_X:.2f} Y{SAFE_CENTER_Y:.2f} F600",
            move_timeout_s=90,
            wait_timeout_s=180,
        )
        metadata["safe_return_status"] = "complete"
        metadata["safe_return_position_response"] = " | ".join(executor.read_position(timeout_s=45))
    except Exception as error:
        metadata["safe_return_status"] = "failed"
        metadata["safe_return_error"] = repr(error)
        print(f"SAFETY RETURN FAILED: {error}")
    finally:
        metadata["safe_return_finished_at"] = datetime.now().isoformat(timespec="seconds")


def run_scan(args: argparse.Namespace) -> int:
    settings = get_motion_controller_settings()
    csv_out = Path(args.csv_out)
    png_out = Path(args.png_out)
    raw_log_path = Path(args.raw_log)
    metadata_path = Path(args.metadata)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    points = build_points(args.size)
    rows = load_existing_rows(csv_out) if args.resume else []
    done = completed_point_numbers(rows)
    metadata = {
        "phase": "9.6",
        "script": str(Path(__file__).relative_to(PROJECT_ROOT)),
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "execute": bool(args.execute),
        "size": args.size,
        "total_points": len(points),
        "csv_out": str(csv_out),
        "png_out": str(png_out),
        "raw_log": str(raw_log_path),
        "controller": settings,
        "safe_center": {"x": SAFE_CENTER_X, "y": SAFE_CENTER_Y},
        "safe_retract_z": SAFE_RETRACT_Z,
        "contact_z": CONTACT_Z,
        "status": "running",
        "error": None,
    }
    write_metadata(metadata_path, metadata)

    if not args.execute:
        print("DRY RUN ONLY. No serial port opened and no hardware moved.")
        print("Planned points:")
        for index, (row_index, col_index, x, y) in enumerate(points, start=1):
            print(f"{index:03d}: row={row_index} col={col_index} X={x:.3f} Y={y:.3f} Z={CONTACT_Z:.3f}")
        metadata["status"] = "dry_run_plan_complete"
        metadata["finished_at"] = datetime.now().isoformat(timespec="seconds")
        write_partial_csv(csv_out, rows)
        plot_partial(csv_out, png_out)
        write_metadata(metadata_path, metadata)
        return 0

    raw_logger = RawSerialLogger(raw_log_path)
    executor: RobustPrusaExecutor | None = None
    exit_code = 0

    try:
        executor = RobustPrusaExecutor(settings["port"], int(settings["baudrate"]), raw_logger)
        executor.connect()
        executor.send("M114", timeout_s=45)
        executor.send("M17", timeout_s=45)
        executor.send("G90", timeout_s=45)
        executor.move_and_wait(f"G1 Z{SAFE_RETRACT_Z:.2f} F600", move_timeout_s=90, wait_timeout_s=180)

        for point_number, (row_index, col_index, x, y) in enumerate(points, start=1):
            if point_number in done:
                print(f"Skipping completed point {point_number}/{len(points)}")
                continue

            started_at = datetime.now().isoformat(timespec="seconds")
            print("")
            print(f"=== POINT {point_number}/{len(points)} row={row_index} col={col_index} X={x:.2f} Y={y:.2f} ===")

            executor.move_and_wait(
                f"G1 X{x:.2f} Y{y:.2f} F600",
                move_timeout_s=90,
                wait_timeout_s=180,
            )
            executor.read_position(timeout_s=45)

            executor.move_and_wait(
                f"G1 Z{CONTACT_Z:.2f} F60",
                move_timeout_s=180,
                wait_timeout_s=240,
            )
            position_lines = executor.read_position(timeout_s=60)

            rows.append(
                ScanPoint(
                    point=point_number,
                    row=row_index,
                    col=col_index,
                    x=x,
                    y=y,
                    contact_z=CONTACT_Z,
                    status="complete",
                    method="phase9_6_fixed_known_foam_contact_z_robust_partial_save",
                    started_at=started_at,
                    completed_at=datetime.now().isoformat(timespec="seconds"),
                    position_response=" | ".join(position_lines),
                    command_count=executor.command_count,
                )
            )
            write_partial_csv(csv_out, rows)
            plot_partial(csv_out, png_out)
            write_metadata(metadata_path, {**metadata, "status": "running", "completed_points": len(completed_point_numbers(rows))})

            executor.move_and_wait(f"G1 Z{SAFE_RETRACT_Z:.2f} F600", move_timeout_s=90, wait_timeout_s=180)

        metadata["status"] = "complete"

    except KeyboardInterrupt as error:
        exit_code = 130
        metadata["status"] = "interrupted"
        metadata["error"] = repr(error)
        print("Interrupted by operator.")
    except Exception as error:
        exit_code = 1
        metadata["status"] = "failed"
        metadata["error"] = repr(error)
        if isinstance(error, ControllerTimeoutError):
            metadata["timeout_command"] = error.command
            metadata["timeout_s"] = error.timeout_s
            metadata["timeout_lines"] = error.lines[-40:]
        print(f"ERROR: {error}")
    finally:
        safe_return(executor, metadata)
        metadata["finished_at"] = datetime.now().isoformat(timespec="seconds")
        metadata["completed_points"] = len(completed_point_numbers(rows))
        write_partial_csv(csv_out, rows)
        plot_partial(csv_out, png_out)
        write_metadata(metadata_path, metadata)
        if executor is not None:
            executor.close()
        raw_logger.close()

    print("")
    print(f"Saved partial CSV: {csv_out}")
    print(f"Saved partial PNG: {png_out}")
    print(f"Saved metadata: {metadata_path}")
    print(f"Saved raw serial log: {raw_log_path}")
    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Phase 9.6 robust XY topography skeleton with partial saves and safe return."
    )
    parser.add_argument("--execute", action="store_true", help="Open serial port and move hardware. Omit for dry-run plan.")
    parser.add_argument("--resume", action="store_true", help="Skip completed points already present in CSV.")
    parser.add_argument("--size", type=int, default=10, help="Grid size. Use 2 or 3 for supervised shakedown before 10.")
    parser.add_argument("--csv-out", default=str(DEFAULT_CSV_OUT))
    parser.add_argument("--png-out", default=str(DEFAULT_PNG_OUT))
    parser.add_argument("--raw-log", default=str(DEFAULT_RAW_LOG))
    parser.add_argument("--metadata", default=str(DEFAULT_METADATA))
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_scan(args)


if __name__ == "__main__":
    raise SystemExit(main())
