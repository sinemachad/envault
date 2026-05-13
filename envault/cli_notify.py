"""CLI commands for managing envault notifications."""

import argparse
import sys

from envault.notify import add_notify, dispatch_notify, list_notify, remove_notify


def cmd_notify_add(args: argparse.Namespace) -> None:
    """Register a notification channel for an event."""
    try:
        entry = add_notify(
            base_dir=args.dir,
            event=args.event,
            channel=args.channel,
            target=args.target or "",
        )
        print(f"Notification added: [{entry.event}] via {entry.channel} -> {entry.target or '(stdout)'}")
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_notify_remove(args: argparse.Namespace) -> None:
    """Remove a registered notification."""
    removed = remove_notify(
        base_dir=args.dir,
        event=args.event,
        channel=args.channel,
        target=args.target or "",
    )
    if removed:
        print(f"Notification removed for event '{args.event}'.")
    else:
        print(f"No matching notification found for event '{args.event}'.")


def cmd_notify_list(args: argparse.Namespace) -> None:
    """List all registered notifications."""
    event = getattr(args, "event", None)
    data = list_notify(base_dir=args.dir, event=event)
    if not any(data.values()):
        print("No notifications registered.")
        return
    for ev, entries in data.items():
        for entry in entries:
            target_str = entry["target"] or "(stdout)"
            print(f"  [{ev}] {entry['channel']} -> {target_str}")


def cmd_notify_dispatch(args: argparse.Namespace) -> None:
    """Manually fire notifications for an event (useful for testing)."""
    outcomes = dispatch_notify(
        base_dir=args.dir,
        event=args.event,
        message=args.message,
    )
    if not outcomes:
        print(f"No notifications configured for event '{args.event}'.")
    else:
        for outcome in outcomes:
            print(f"  dispatched: {outcome}")


def build_notify_subparsers(sub: argparse._SubParsersAction) -> None:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--dir", default=".", help="Project base directory")

    p_add = sub.add_parser("notify-add", parents=[common], help="Register a notification")
    p_add.add_argument("event", help="Event name (e.g. lock, unlock, rotate)")
    p_add.add_argument("channel", choices=["stdout", "command", "file"], help="Notification channel")
    p_add.add_argument("target", nargs="?", default="", help="Command or file path (omit for stdout)")
    p_add.set_defaults(func=cmd_notify_add)

    p_rm = sub.add_parser("notify-remove", parents=[common], help="Remove a notification")
    p_rm.add_argument("event", help="Event name")
    p_rm.add_argument("channel", choices=["stdout", "command", "file"])
    p_rm.add_argument("target", nargs="?", default="")
    p_rm.set_defaults(func=cmd_notify_remove)

    p_list = sub.add_parser("notify-list", parents=[common], help="List notifications")
    p_list.add_argument("event", nargs="?", default=None, help="Filter by event")
    p_list.set_defaults(func=cmd_notify_list)

    p_disp = sub.add_parser("notify-dispatch", parents=[common], help="Fire notifications for an event")
    p_disp.add_argument("event", help="Event name")
    p_disp.add_argument("message", help="Message payload")
    p_disp.set_defaults(func=cmd_notify_dispatch)
