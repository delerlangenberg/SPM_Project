from datetime import datetime, timezone
from threading import Thread

import pytest

from core.application.modules.console_logger import ConsoleLogger, Severity


FIXED_TIME = datetime(2026, 7, 15, 12, 34, 56, 123000, tzinfo=timezone.utc)


def test_log_returns_structured_record_and_formats_timestamp() -> None:
    logger = ConsoleLogger(clock=lambda: FIXED_TIME)
    record = logger.log("Connected on COM6", Severity.EVENT, source="connection")

    assert record.sequence == 1
    assert record.severity is Severity.EVENT
    assert record.source == "connection"
    assert record.format(timestamps=False) == "Connected on COM6"
    assert record.format().endswith("Connected on COM6")


def test_filter_and_search_are_case_insensitive_by_default() -> None:
    logger = ConsoleLogger()
    logger.log("Calibration complete", "event", source="calibration")
    logger.log("Unsafe Z boundary", "warning", source="safety")
    logger.log("Connection failed", "error", source="connection")

    assert [item.message for item in logger.filter((Severity.WARNING, Severity.ERROR))] == [
        "Unsafe Z boundary",
        "Connection failed",
    ]
    assert [item.message for item in logger.search("CALIBRATION")] == ["Calibration complete"]
    assert [item.message for item in logger.search("safety")] == ["Unsafe Z boundary"]


def test_capacity_is_bounded_and_sequence_remains_monotonic_after_clear() -> None:
    logger = ConsoleLogger(capacity=2)
    logger.log("one")
    logger.log("two")
    logger.log("three")
    assert [item.sequence for item in logger.snapshot()] == [2, 3]

    logger.clear()
    assert logger.snapshot() == ()
    assert logger.log("four").sequence == 4


def test_subscriber_can_unsubscribe() -> None:
    logger = ConsoleLogger()
    received = []
    unsubscribe = logger.subscribe(received.append)
    logger.log("first")
    unsubscribe()
    logger.log("second")
    assert [item.message for item in received] == ["first"]


def test_concurrent_writers_do_not_lose_records_or_sequences() -> None:
    logger = ConsoleLogger(capacity=1000)
    workers = [Thread(target=lambda n=n: [logger.log(f"{n}:{i}") for i in range(50)]) for n in range(4)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()

    records = logger.snapshot()
    assert len(records) == 200
    assert [record.sequence for record in records] == list(range(1, 201))


@pytest.mark.parametrize("capacity", [0, -1])
def test_invalid_capacity_is_rejected(capacity: int) -> None:
    with pytest.raises(ValueError, match="capacity"):
        ConsoleLogger(capacity=capacity)


def test_empty_message_and_unknown_severity_are_rejected() -> None:
    logger = ConsoleLogger()
    with pytest.raises(ValueError, match="message"):
        logger.log("  ")
    with pytest.raises(ValueError):
        logger.log("message", "debug")
