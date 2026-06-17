"""CLI for Phase 9.7 read-only hardware information exchange.

Default mode is dry-run planning. Use --real to open the confirmed serial port
and send read-only commands only.
"""

from __future__ import annotations

import argparse

from core.system.hardware_information_exchange import (
    READONLY_HARDWARE_ACTIONS,
    append_information_exchange_log,
    action_commands,
    run_real_information_exchange,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Educational SPM read-only hardware information CLI")
    parser.add_argument(
        "action",
        choices=["ALL", *READONLY_HARDWARE_ACTIONS.keys()],
        help="Read-only hardware action to run",
    )
    parser.add_argument("--real", action="store_true", help="Open serial port and run read-only hardware command.")
    parser.add_argument("--port", default=None, help="Override configured serial port.")
    parser.add_argument("--baudrate", type=int, default=None, help="Override configured baudrate.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    planned = action_commands(args.action)

    if not args.real:
        print("DRY RUN ONLY. No serial port opened and no hardware command sent.")
        for action, command in planned:
            print(f"plan: {action} -> {command}")
        return 0

    results = run_real_information_exchange(args.action, port=args.port, baudrate=args.baudrate)
    log_path = append_information_exchange_log(results)
    for result in results:
        print(f"\n>>> {result.action} ({result.command}) success={result.success}")
        for line in result.response_lines:
            print(line)
    print(f"\nlog={log_path}")
    return 0 if all(result.success for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
