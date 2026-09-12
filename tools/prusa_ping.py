import argparse

from core.motion.prusa_gcode_backend import PrusaGcodeBackend


def main() -> int:
    ap = argparse.ArgumentParser(description="Prusa MK4S safe ping (no motion).")
    ap.add_argument("--port", default=None, help="Serial port, e.g. /dev/ttyACM0 or COM5")
    ap.add_argument("--baud", type=int, default=115200, help="Baudrate (default 115200)")
    ap.add_argument(
        "--no-auto-detect",
        action="store_true",
        help="Disable serial auto-detection and require --port.",
    )
    args = ap.parse_args()

    backend = PrusaGcodeBackend(
        port=args.port,
        baudrate=args.baud,
        timeout=0.5,
        auto_detect_port=not args.no_auto_detect,
    )

    try:
        backend.connect()
        state = backend.get_state()
        print(f"Connected: {state.get('connected')} on {state.get('port')}")

        # Safe commands: no movement
        print(">> M115")
        for line in backend.send_gcode("M115", timeout=4.0):
            print(line)

        print("\n>> M114")
        for line in backend.send_gcode("M114", timeout=4.0):
            print(line)

        print("\nState:", backend.get_state())

        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        return 2
    finally:
        backend.disconnect()


if __name__ == "__main__":
    raise SystemExit(main())
