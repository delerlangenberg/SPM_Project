"""SPM adaptive safety advisor.

Advisory only:
- classifies faults
- ranks safe recovery actions
- learns from operator-verified outcomes
- detects dangerous state combinations

This module intentionally has no serial, G-code, motion or hardware API.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ADVISORY_ONLY = True
EXECUTION_ALLOWED = False
HARDWARE_ACCESS = False

DEFAULT_HISTORY = Path("data/ml_safety/safety_learning_history.jsonl")


RECOVERY_CATALOG = {
    "communication_timeout": [
        (
            "retry_readonly",
            "Repeat only the read-only M115/M105/M119/M114 handshake.",
            0.90,
        ),
        (
            "explicit_port",
            "Select the verified MK4S serial device explicitly and retry read-only communication.",
            0.86,
        ),
        (
            "inspect_usb",
            "Inspect USB power/data path and confirm no competing serial client is active.",
            0.80,
        ),
    ],

    "serial_busy": [
        (
            "close_serial_clients",
            "Close competing serial applications while keeping motion locked.",
            0.92,
        ),
        (
            "reopen_readonly",
            "Reopen only the verified read-only MK4S session.",
            0.86,
        ),
    ],

    "probe_feedback": [
        (
            "repeat_probe_read",
            "Keep Z motion blocked and read Arduino probe feedback twice.",
            0.97,
        ),
        (
            "inspect_probe",
            "Inspect CR-Touch/D3 wiring and trigger state before any Z approach.",
            0.93,
        ),
    ],

    "position_mismatch": [
        (
            "repeat_m114",
            "Keep motion locked and repeat M114 before trusting XYZ position.",
            0.97,
        ),
        (
            "compare_counts",
            "Compare MK4S step counts with converted millimetre coordinates.",
            0.92,
        ),
        (
            "inspect_calibration",
            "Compare current position evidence with the saved calibration record.",
            0.89,
        ),
    ],

    "endstop_state": [
        (
            "repeat_m119",
            "Keep motion locked and repeat M119 before using endstop state.",
            0.97,
        ),
        (
            "inspect_parser",
            "Inspect software parsing of the MK4S endstop response.",
            0.88,
        ),
    ],

    "calibration": [
        (
            "review_reference",
            "Review position, endstops and calibration reference before repeating calibration.",
            0.97,
        ),
        (
            "readonly_preflight",
            "Repeat M114 and M119 before authorizing calibration motion.",
            0.94,
        ),
    ],

    "connection_missing": [
        (
            "refresh_ports",
            "Refresh serial devices and verify MK4S VID/PID before reconnecting.",
            0.94,
        ),
        (
            "inspect_power_usb",
            "Verify printer power and USB data connection without enabling motion.",
            0.88,
        ),
    ],

    "unknown": [
        (
            "collect_evidence",
            "Keep motion locked and collect read-only evidence before choosing a correction.",
            0.98,
        ),
        (
            "operator_review",
            "Require operator review because the condition is not reliably classified.",
            0.96,
        ),
    ],
}


def classify_error(message: str) -> str:
    text = str(message or "").casefold()

    if any(x in text for x in (
        "busy", "permission", "access is denied", "in use"
    )):
        return "serial_busy"

    if any(x in text for x in (
        "timeout", "timed out", "no response", "incomplete response"
    )):
        return "communication_timeout"

    if any(x in text for x in (
        "probe", "cr-touch", "crtouch", "d3",
        "deflection", "trigger_latched"
    )):
        return "probe_feedback"

    if "endstop" in text or "m119" in text:
        return "endstop_state"

    if any(x in text for x in (
        "calibration", "homing", "g28", "home position"
    )):
        return "calibration"

    if any(x in text for x in (
        "position", "m114", "coordinate", "count x:"
    )):
        return "position_mismatch"

    if any(x in text for x in (
        "not found", "no prusa", "device missing", "disconnected"
    )):
        return "connection_missing"

    return "unknown"


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            name = str(key)

            if any(secret in name.casefold() for secret in (
                "password", "token", "secret",
                "apikey", "api_key", "credential"
            )):
                out[name] = "<redacted>"
            else:
                out[name] = _redact(item)

        return out

    if isinstance(value, (list, tuple)):
        return [_redact(item) for item in value]

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    return str(value)


class SafetyLearningAdvisor:
    def __init__(self, history_path: str | Path = DEFAULT_HISTORY):
        self.history_path = Path(history_path)
        self.records: list[dict[str, Any]] = []
        self.history_ok = True
        self.history_error = ""

        self._load()


    def _load(self) -> None:
        if not self.history_path.exists():
            return

        try:
            for line in self.history_path.read_text(
                encoding="utf-8"
            ).splitlines():

                if not line.strip():
                    continue

                record = json.loads(line)

                if record.get("operator_verified") is not True:
                    continue

                self.records.append(record)

        except (OSError, json.JSONDecodeError, TypeError) as exc:
            self.records = []
            self.history_ok = False
            self.history_error = str(exc)


    def _stats(
        self,
        error_type: str,
        recommendation_id: str,
    ) -> tuple[int, int]:

        success = 0
        failure = 0

        for record in self.records:
            if record.get("error_type") != error_type:
                continue

            if record.get("recommendation_id") != recommendation_id:
                continue

            if record.get("success") is True:
                success += 1
            elif record.get("success") is False:
                failure += 1

        return success, failure


    def record_outcome(
        self,
        *,
        error_type: str,
        recommendation_id: str,
        success: bool,
        operator_verified: bool,
        context: dict[str, Any] | None = None,
        note: str = "",
    ) -> dict[str, Any]:

        if operator_verified is not True:
            raise PermissionError(
                "Learning requires explicit operator verification."
            )

        if error_type not in RECOVERY_CATALOG:
            raise ValueError(f"Unknown error type: {error_type}")

        valid_ids = {
            entry[0]
            for entry in RECOVERY_CATALOG[error_type]
        }

        if recommendation_id not in valid_ids:
            raise ValueError(
                f"Unknown recommendation: {recommendation_id}"
            )

        if not self.history_ok:
            raise RuntimeError(
                "History is invalid; learning is disabled."
            )

        record = {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(timespec="milliseconds"),

            "error_type": error_type,
            "recommendation_id": recommendation_id,
            "success": bool(success),
            "operator_verified": True,
            "context": _redact(context or {}),
            "note": str(note),
        }

        self.history_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.history_path.open(
            "a",
            encoding="utf-8",
        ) as handle:
            handle.write(
                json.dumps(record, sort_keys=True) + "\n"
            )

        self.records.append(record)

        return record


    def _safety_flags(
        self,
        context: dict[str, Any],
    ) -> list[str]:

        flags = []

        connected = context.get("connected")

        authorization = str(
            context.get(
                "authorization_state",
                context.get("motion_authorization", "LOCKED"),
            )
        ).upper()

        if (
            connected is False
            and authorization in {"STANDBY", "OPERATIONAL"}
        ):
            flags.append(
                "motion_authorization_without_connection"
            )

        if (
            authorization == "OPERATIONAL"
            and context.get("calibration_valid") is False
        ):
            flags.append(
                "operational_without_valid_calibration"
            )

        probe = str(
            context.get("probe_state", "")
        ).casefold()

        action = str(
            context.get("requested_action", "")
        ).casefold()

        if (
            any(x in probe for x in (
                "trigger", "contact", "latched"
            ))
            and any(x in action for x in (
                "approach", "z down", "z_down", "calibrat"
            ))
        ):
            flags.append(
                "probe_triggered_before_requested_motion"
            )

        if (
            str(context.get("safety_state", "")).upper() == "E_STOP"
            or context.get("emergency_stop") is True
        ):
            flags.append("emergency_stop_active")

        return flags


    def recommend(
        self,
        *,
        error: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        error_type = classify_error(error)
        context = _redact(context or {})

        ranked = []

        for rec_id, text, prior in RECOVERY_CATALOG[error_type]:
            successes, failures = self._stats(
                error_type,
                rec_id,
            )

            count = successes + failures

            learned_rate = (
                (successes + 1) / (count + 2)
            )

            evidence_weight = (
                count / (count + 5.0)
                if count
                else 0.0
            )

            adjustment = (
                0.20
                * ((learned_rate - 0.5) * 2.0)
                * evidence_weight
            )

            score = max(
                0.0,
                min(1.0, prior + adjustment),
            )

            ranked.append({
                "recommendation_id": rec_id,
                "text": text,
                "score": round(score, 4),
                "verified_successes": successes,
                "verified_failures": failures,
                "evidence_count": count,
                "learned_success_rate": round(
                    learned_rate, 4
                ),
            })

        ranked.sort(
            key=lambda item: (
                item["score"],
                item["evidence_count"],
            ),
            reverse=True,
        )

        top_count = (
            ranked[0]["evidence_count"]
            if ranked
            else 0
        )

        if not self.history_ok:
            confidence = "invalid-history"
        elif top_count < 3:
            confidence = "insufficient"
        elif top_count < 8:
            confidence = "limited"
        else:
            confidence = "established"

        flags = self._safety_flags(context)

        return {
            "advisory_only": ADVISORY_ONLY,
            "execution_allowed": EXECUTION_ALLOWED,
            "hardware_access": HARDWARE_ACCESS,

            "error_type": error_type,
            "recommendations": ranked,
            "top_recommendation": ranked[0] if ranked else None,

            "confidence": confidence,
            "safety_flags": flags,

            "requires_operator_review": bool(
                flags
                or error_type == "unknown"
                or confidence != "established"
            ),

            "learning_records": len(self.records),
            "history_ok": self.history_ok,
            "history_error": self.history_error,
        }
