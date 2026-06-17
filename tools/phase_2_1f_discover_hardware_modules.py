from __future__ import annotations

from pathlib import Path
from datetime import datetime


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT = PROJECT_ROOT / "docs" / "PHASE_2_1F_HARDWARE_DRY_RUN_DISCOVERY.md"

SEARCH_EXTENSIONS = {".py", ".ps1", ".md", ".txt", ".json", ".yaml", ".yml"}
SKIP_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "backups",
    "htmlcov",
}

KEYWORD_GROUPS = {
    "mk4s_prusa": ["MK4S", "Prusa", "prusa"],
    "serial": ["serial", "COM", "baud", "pyserial"],
    "gcode_readonly": ["M115", "M119", "M105", "M114"],
    "gcode_motion": ["G0", "G1", "G28", "M17", "M18", "M84"],
    "dry_run_simulation": ["dry_run", "dry-run", "simulation", "simulated", "stub"],
    "z_control": ["z_approach", "approach", "retract", "z_driver", "Z"],
    "scan": ["scan", "raster", "topography", "line"],
    "web_api": ["api", "operator_console", "system_control"],
}


def should_scan(path: Path) -> bool:
    if any(part in SKIP_PARTS for part in path.parts):
        return False
    return path.suffix.lower() in SEARCH_EXTENSIONS


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="ignore")
    except Exception:
        return ""


def matching_lines(text: str, keywords: list[str], limit: int = 12) -> list[str]:
    lines = []
    for idx, line in enumerate(text.splitlines(), start=1):
        if any(keyword in line for keyword in keywords):
            cleaned = line.strip()
            if cleaned:
                lines.append(f"L{idx}: {cleaned[:180]}")
        if len(lines) >= limit:
            break
    return lines


def main() -> None:
    files = [p for p in PROJECT_ROOT.rglob("*") if p.is_file() and should_scan(p)]

    sections: dict[str, list[tuple[Path, list[str]]]] = {
        key: [] for key in KEYWORD_GROUPS
    }

    for file_path in files:
        text = read_text(file_path)
        if not text:
            continue

        for group, keywords in KEYWORD_GROUPS.items():
            hits = matching_lines(text, keywords)
            if hits:
                sections[group].append((file_path, hits))

    lines: list[str] = []
    lines.append("# Phase 2.1F Hardware Dry-Run Discovery Report")
    lines.append("")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## Safety")
    lines.append("")
    lines.append("This discovery phase does not connect to serial hardware.")
    lines.append("It does not send G-code.")
    lines.append("It does not move the printer.")
    lines.append("")
    lines.append("## Purpose")
    lines.append("")
    lines.append("Find existing safe MK4S / Prusa / serial / dry-run modules so Phase 2.1 can connect the web GUI to proven project code instead of inventing a second hardware stack.")
    lines.append("")
    lines.append("## Summary counts")
    lines.append("")
    for group, entries in sections.items():
        lines.append(f"- {group}: {len(entries)} files")
    lines.append("")

    for group, entries in sections.items():
        lines.append(f"## {group}")
        lines.append("")
        if not entries:
            lines.append("No direct matches found.")
            lines.append("")
            continue

        for path, hits in entries[:30]:
            rel = path.relative_to(PROJECT_ROOT)
            lines.append(f"### `{rel}`")
            lines.append("")
            for hit in hits:
                lines.append(f"- {hit}")
            lines.append("")

    lines.append("## Recommended next integration target")
    lines.append("")
    lines.append("Use this report to choose the safest existing module for:")
    lines.append("")
    lines.append("1. read-only printer status,")
    lines.append("2. dry-run startup plan,")
    lines.append("3. explicit hardware lockout,")
    lines.append("4. later real read-only serial status,")
    lines.append("5. only after that: controlled motion through safety gates.")
    lines.append("")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"report_written: {REPORT}")


if __name__ == "__main__":
    main()
