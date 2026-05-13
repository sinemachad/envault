"""Notification hooks for envault events (e.g. lock, unlock, rotate)."""

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


def _get_notify_path(base_dir: str) -> Path:
    return Path(base_dir) / ".envault" / "notify.json"


def _load_notify(base_dir: str) -> Dict:
    path = _get_notify_path(base_dir)
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def _save_notify(base_dir: str, data: Dict) -> None:
    path = _get_notify_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


@dataclass
class NotifyEntry:
    event: str
    channel: str  # "stdout" | "command" | "file"
    target: str   # command string or file path; ignored for stdout
    extra: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "event": self.event,
            "channel": self.channel,
            "target": self.target,
            "extra": self.extra,
        }


def add_notify(base_dir: str, event: str, channel: str, target: str) -> NotifyEntry:
    """Register a notification for *event* via *channel* pointing at *target*."""
    if channel not in ("stdout", "command", "file"):
        raise ValueError(f"Unknown channel '{channel}'. Use stdout, command, or file.")
    data = _load_notify(base_dir)
    entries = data.get(event, [])
    entry = NotifyEntry(event=event, channel=channel, target=target)
    entries.append(entry.to_dict())
    data[event] = entries
    _save_notify(base_dir, data)
    return entry


def remove_notify(base_dir: str, event: str, channel: str, target: str) -> bool:
    """Remove a specific notification entry. Returns True if removed."""
    data = _load_notify(base_dir)
    entries = data.get(event, [])
    new_entries = [
        e for e in entries
        if not (e["channel"] == channel and e["target"] == target)
    ]
    removed = len(new_entries) < len(entries)
    data[event] = new_entries
    _save_notify(base_dir, data)
    return removed


def list_notify(base_dir: str, event: Optional[str] = None) -> Dict:
    """Return all notifications, optionally filtered by event."""
    data = _load_notify(base_dir)
    if event:
        return {event: data.get(event, [])}
    return data


def dispatch_notify(base_dir: str, event: str, message: str) -> List[str]:
    """Fire all registered notifications for *event*. Returns list of outcomes."""
    data = _load_notify(base_dir)
    entries = data.get(event, [])
    outcomes = []
    for entry in entries:
        channel = entry["channel"]
        target = entry["target"]
        if channel == "stdout":
            print(f"[envault notify] {event}: {message}")
            outcomes.append("stdout")
        elif channel == "command":
            try:
                subprocess.run(
                    target,
                    shell=True,
                    env={**os.environ, "ENVAULT_EVENT": event, "ENVAULT_MESSAGE": message},
                    check=True,
                )
                outcomes.append(f"command:ok:{target}")
            except subprocess.CalledProcessError as exc:
                outcomes.append(f"command:error:{exc.returncode}")
        elif channel == "file":
            try:
                path = Path(target)
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, "a") as fh:
                    fh.write(f"{event}: {message}\n")
                outcomes.append(f"file:ok:{target}")
            except OSError as exc:
                outcomes.append(f"file:error:{exc}")
    return outcomes
