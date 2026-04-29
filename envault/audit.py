"""Audit log for envault operations."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

AUDIT_LOG_FILENAME = ".envault_audit.log"


def _get_log_path(directory: str = ".") -> Path:
    return Path(directory) / AUDIT_LOG_FILENAME


def record_event(action: str, target: str, directory: str = ".", extra: dict = None) -> dict:
    """Record an audit event and append it to the log file."""
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "target": target,
        "user": os.environ.get("USER") or os.environ.get("USERNAME") or "unknown",
    }
    if extra:
        event.update(extra)

    log_path = _get_log_path(directory)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

    return event


def read_events(directory: str = ".") -> list:
    """Read all audit events from the log file."""
    log_path = _get_log_path(directory)
    if not log_path.exists():
        return []

    events = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events


def format_events(events: list) -> str:
    """Format audit events for human-readable display."""
    if not events:
        return "No audit events found."

    lines = []
    for event in events:
        ts = event.get("timestamp", "unknown")
        action = event.get("action", "unknown")
        target = event.get("target", "unknown")
        user = event.get("user", "unknown")
        lines.append(f"[{ts}] {user} {action} {target}")
    return "\n".join(lines)
