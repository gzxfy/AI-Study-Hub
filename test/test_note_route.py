from datetime import datetime, timedelta, timezone

from backend.routes.note_route import serialize_timestamp


def test_serialize_timestamp_treats_naive_datetime_as_utc():
    timestamp = datetime(2026, 11, 23, 16, 30)

    assert serialize_timestamp(timestamp) == "2026-11-23T16:30:00Z"


def test_serialize_timestamp_converts_offset_to_utc():
    timestamp = datetime(2026, 11, 23, 10, 30, tzinfo=timezone(timedelta(hours=-6)))

    assert serialize_timestamp(timestamp) == "2026-11-23T16:30:00Z"
