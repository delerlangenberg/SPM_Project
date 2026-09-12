# Module 5: Console Logger

Last updated: 2026-07-15

## Responsibility

`ConsoleLogger` provides bounded, thread-safe, structured application logging. It has no PyQt, hardware, connection, or scan dependencies. UI code consumes immutable snapshots or subscribes through the public callback interface.

## Public interface

- `ConsoleLogger(capacity=10000, clock=None)` creates a logger.
- `log(message, severity="console", source="operator")` stores and publishes a record.
- `filter(severities=None, source=None)` returns a filtered immutable snapshot.
- `search(query, severities=None, source=None, case_sensitive=False)` searches records.
- `snapshot()` returns all retained records.
- `clear()` removes retained records without resetting sequence numbers.
- `subscribe(callback)` registers a callback and returns an unsubscribe function.
- `Severity` defines `console`, `event`, `warning`, and `error` lanes.
- `LogRecord.format(timestamps=True)` produces display text.

Subscriber callbacks run synchronously after the logger lock is released. UI subscribers must marshal updates onto their UI thread.

## Configuration

The module consumes no environment variables or configuration files. `capacity` controls the in-memory record limit; the oldest record is discarded when that limit is exceeded.

## Dependencies

Python standard library only.

## Error handling

- Empty messages raise `ValueError`.
- Unknown severity values raise `ValueError` through `Severity` validation.
- Invalid capacities raise `ValueError`.
- Subscriber exceptions are deliberately propagated to the caller so integration failures remain visible.

## Isolated tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q core\application\modules\console_logger\tests.py
```

