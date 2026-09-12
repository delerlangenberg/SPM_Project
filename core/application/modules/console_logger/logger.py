"""Thread-safe structured logger with no UI or hardware dependencies."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from threading import RLock
from typing import Callable, Iterable


class Severity(str, Enum):
    """Operator-facing log lanes."""

    CONSOLE = "console"
    EVENT = "event"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class LogRecord:
    """One immutable, ordered logger record."""

    sequence: int
    timestamp: datetime
    severity: Severity
    message: str
    source: str = "operator"

    def format(self, *, timestamps: bool = True) -> str:
        prefix = f"[{self.timestamp.astimezone().strftime('%H:%M:%S.%f')[:-3]}] " if timestamps else ""
        return f"{prefix}{self.message}"


Subscriber = Callable[[LogRecord], None]


class ConsoleLogger:
    """Bounded in-memory logger used through its stable public methods."""

    def __init__(self, *, capacity: int = 10_000, clock: Callable[[], datetime] | None = None) -> None:
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self._records: deque[LogRecord] = deque(maxlen=capacity)
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._sequence = 0
        self._subscribers: list[Subscriber] = []
        self._lock = RLock()

    def log(
        self,
        message: str,
        severity: Severity | str = Severity.CONSOLE,
        *,
        source: str = "operator",
    ) -> LogRecord:
        """Store one record and notify subscribers after releasing the lock."""
        clean_message = str(message).strip()
        if not clean_message:
            raise ValueError("message must not be empty")
        level = severity if isinstance(severity, Severity) else Severity(str(severity).lower())
        with self._lock:
            self._sequence += 1
            record = LogRecord(self._sequence, self._clock(), level, clean_message, str(source))
            self._records.append(record)
            subscribers = tuple(self._subscribers)
        for subscriber in subscribers:
            subscriber(record)
        return record

    def filter(
        self,
        severities: Severity | str | Iterable[Severity | str] | None = None,
        *,
        source: str | None = None,
    ) -> tuple[LogRecord, ...]:
        """Return an immutable snapshot matching severity and source."""
        levels = self._normalize_severities(severities)
        with self._lock:
            return tuple(
                record
                for record in self._records
                if (levels is None or record.severity in levels)
                and (source is None or record.source == source)
            )

    def search(
        self,
        query: str,
        severities: Severity | str | Iterable[Severity | str] | None = None,
        *,
        source: str | None = None,
        case_sensitive: bool = False,
    ) -> tuple[LogRecord, ...]:
        """Search message and source text within a filtered snapshot."""
        needle = str(query)
        if not needle:
            return self.filter(severities, source=source)
        if not case_sensitive:
            needle = needle.casefold()
        results = []
        for record in self.filter(severities, source=source):
            haystack = f"{record.message} {record.source}"
            if not case_sensitive:
                haystack = haystack.casefold()
            if needle in haystack:
                results.append(record)
        return tuple(results)

    def clear(self) -> None:
        with self._lock:
            self._records.clear()

    def subscribe(self, subscriber: Subscriber) -> Callable[[], None]:
        """Subscribe to future records and return an unsubscribe function."""
        with self._lock:
            if subscriber not in self._subscribers:
                self._subscribers.append(subscriber)

        def unsubscribe() -> None:
            with self._lock:
                if subscriber in self._subscribers:
                    self._subscribers.remove(subscriber)

        return unsubscribe

    def snapshot(self) -> tuple[LogRecord, ...]:
        return self.filter()

    @staticmethod
    def _normalize_severities(
        values: Severity | str | Iterable[Severity | str] | None,
    ) -> frozenset[Severity] | None:
        if values is None:
            return None
        if isinstance(values, (Severity, str)):
            values = (values,)
        return frozenset(value if isinstance(value, Severity) else Severity(str(value).lower()) for value in values)

