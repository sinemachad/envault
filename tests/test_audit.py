"""Tests for envault.audit module."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from envault.audit import (
    AUDIT_LOG_FILENAME,
    format_events,
    read_events,
    record_event,
)


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


class TestRecordEvent:
    def test_returns_event_dict(self, tmp_dir):
        event = record_event("lock", ".env", directory=tmp_dir)
        assert isinstance(event, dict)

    def test_event_has_required_fields(self, tmp_dir):
        event = record_event("lock", ".env", directory=tmp_dir)
        assert "timestamp" in event
        assert event["action"] == "lock"
        assert event["target"] == ".env"
        assert "user" in event

    def test_event_written_to_log(self, tmp_dir):
        record_event("unlock", ".env.enc", directory=tmp_dir)
        log_path = Path(tmp_dir) / AUDIT_LOG_FILENAME
        assert log_path.exists()

    def test_extra_fields_included(self, tmp_dir):
        event = record_event("export", ".env", directory=tmp_dir, extra={"version": 2})
        assert event["version"] == 2

    def test_multiple_events_appended(self, tmp_dir):
        record_event("lock", ".env", directory=tmp_dir)
        record_event("unlock", ".env.enc", directory=tmp_dir)
        events = read_events(directory=tmp_dir)
        assert len(events) == 2


class TestReadEvents:
    def test_returns_empty_list_if_no_log(self, tmp_dir):
        events = read_events(directory=tmp_dir)
        assert events == []

    def test_returns_list_of_dicts(self, tmp_dir):
        record_event("lock", ".env", directory=tmp_dir)
        events = read_events(directory=tmp_dir)
        assert isinstance(events, list)
        assert all(isinstance(e, dict) for e in events)

    def test_skips_malformed_lines(self, tmp_dir):
        log_path = Path(tmp_dir) / AUDIT_LOG_FILENAME
        with open(log_path, "w") as f:
            f.write("not json\n")
            f.write(json.dumps({"action": "lock", "target": ".env", "timestamp": "t", "user": "u"}) + "\n")
        events = read_events(directory=tmp_dir)
        assert len(events) == 1


class TestFormatEvents:
    def test_empty_returns_message(self):
        result = format_events([])
        assert "No audit" in result

    def test_formats_event_fields(self):
        events = [{"timestamp": "2024-01-01T00:00:00+00:00", "action": "lock", "target": ".env", "user": "alice"}]
        result = format_events(events)
        assert "alice" in result
        assert "lock" in result
        assert ".env" in result
