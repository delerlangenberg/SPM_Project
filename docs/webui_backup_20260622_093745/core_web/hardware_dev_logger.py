from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import re
import secrets
from typing import Any


REDACTION_PATTERNS = [
    (re.compile(r"UUID:[0-9a-fA-F-]+"), "UUID:<redacted>"),
    (re.compile(r"SER=[A-Za-z0-9._:-]+"), "SER=<redacted>"),
]


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def hardware_log_dir() -> Path:
    path = project_root() / "docs" / "hardware_logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def redact(value: Any) -> str:
    text = str(value)
    for pattern, replacement in REDACTION_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def make_session_id(prefix: str = "HW") -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    token = secrets.token_hex(3).upper()
    return f"{prefix}_{stamp}_{token}"


class HardwareDevLogger:
    def __init__(self, phase: str, session_id: str | None = None) -> None:
        self.phase = phase
        self.session_id = session_id or make_session_id("SPM")
        self.lines: list[str] = []
        self.records: list[dict[str, Any]] = []

        base = hardware_log_dir() / f"{self.session_id}_{self.phase}"
        self.text_path = base.with_suffix(".txt")
        self.jsonl_path = base.with_suffix(".jsonl")

        self.emit(
            "INFO",
            "session_start",
            phase=self.phase,
            text_log=str(self.text_path),
            jsonl_log=str(self.jsonl_path),
        )

    def emit(self, level: str, event: str, **fields: Any) -> str:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        safe_fields = {str(k): redact(v) for k, v in fields.items()}

        parts = [
            f"[{now}]",
            f"[{level.upper()}]",
            f"[{event}]",
            f"session={self.session_id}",
        ]

        for key in sorted(safe_fields):
            value = safe_fields[key]
            if "\n" in value:
                value = value.replace("\n", "\\n")
            parts.append(f"{key}={value}")

        line = " ".join(parts)

        record = {
            "timestamp": now,
            "level": level.upper(),
            "event": event,
            "session": self.session_id,
            "phase": self.phase,
            **safe_fields,
        }

        self.lines.append(line)
        self.records.append(record)
        self.flush()
        return line

    def emit_raw(self, direction: str, text: str, **fields: Any) -> str:
        return self.emit("RAW", direction, text=redact(text), **fields)

    def flush(self) -> None:
        self.text_path.write_text("\n".join(self.lines) + "\n", encoding="utf-8")
        self.jsonl_path.write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in self.records),
            encoding="utf-8",
        )

    def summary_lines(self) -> list[str]:
        return list(self.lines)
