"""CLI subcommands for audit log inspection."""

import argparse
import sys

from envault.audit import format_events, read_events


def cmd_audit(args: argparse.Namespace) -> None:
    """Display audit log events."""
    directory = getattr(args, "directory", ".")
    events = read_events(directory=directory)

    if not events:
        print("No audit log events found.")
        return

    if getattr(args, "json", False):
        import json
        print(json.dumps(events, indent=2))
        return

    limit = getattr(args, "limit", None)
    if limit and limit > 0:
        events = events[-limit:]

    output = format_events(events)
    print(output)


def cmd_audit_clear(args: argparse.Namespace) -> None:
    """Clear the audit log after confirmation."""
    from pathlib import Path
    from envault.audit import AUDIT_LOG_FILENAME

    directory = getattr(args, "directory", ".")
    log_path = Path(directory) / AUDIT_LOG_FILENAME

    if not log_path.exists():
        print("No audit log found.")
        return

    if not getattr(args, "yes", False):
        confirm = input("Clear audit log? [y/N] ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return

    log_path.unlink()
    print("Audit log cleared.")


def build_audit_subparsers(subparsers) -> None:
    """Register audit subcommands onto a subparsers action."""
    audit_parser = subparsers.add_parser("audit", help="View the audit log")
    audit_parser.add_argument(
        "--limit", "-n", type=int, default=0,
        help="Show only the last N events (0 = all)"
    )
    audit_parser.add_argument(
        "--json", action="store_true",
        help="Output events as JSON"
    )
    audit_parser.add_argument(
        "--directory", "-d", default=".",
        help="Directory containing the audit log (default: current directory)"
    )
    audit_parser.set_defaults(func=cmd_audit)

    clear_parser = subparsers.add_parser("audit-clear", help="Clear the audit log")
    clear_parser.add_argument(
        "--yes", "-y", action="store_true",
        help="Skip confirmation prompt"
    )
    clear_parser.add_argument(
        "--directory", "-d", default=".",
        help="Directory containing the audit log"
    )
    clear_parser.set_defaults(func=cmd_audit_clear)
