"""CLI command for read-only SPM hardware startup initialization."""

from core.system.hardware_startup_initializer import run_readonly_hardware_startup


def main() -> int:
    result = run_readonly_hardware_startup()

    print(f"timestamp={result.timestamp}")
    print(f"success={result.success}")
    print(f"port={result.port}")
    print(f"baudrate={result.baudrate}")

    for command_result in result.command_results:
        print("")
        print(f">>> {command_result.command}")
        print(f"success={command_result.success}")
        for line in command_result.response_lines:
            print(line)

    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
