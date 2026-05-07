"""CLI sub-commands for vault change history."""

import argparse
import sys

from envault.history import record_change, read_history, clear_history, format_history


def cmd_history_show(args: argparse.Namespace) -> None:
    """Print the change history for a vault file."""
    entries = read_history(args.vault)
    if args.action:
        entries = [e for e in entries if e.get("action") == args.action]
    if args.limit and args.limit > 0:
        entries = entries[-args.limit:]
    print(format_history(entries))


def cmd_history_record(args: argparse.Namespace) -> None:
    """Manually record a change event (useful for scripting)."""
    try:
        entry = record_change(
            vault_path=args.vault,
            action=args.action,
            actor=getattr(args, "actor", None),
            note=getattr(args, "note", None),
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Recorded: {entry['action']} at {entry['timestamp']}")


def cmd_history_clear(args: argparse.Namespace) -> None:
    """Remove all history entries for a vault file."""
    count = clear_history(args.vault)
    print(f"Cleared {count} history entry/entries for {args.vault}")


def build_history_subparsers(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    # --- history show ---
    p_show = subparsers.add_parser("history-show", help="Show vault change history")
    p_show.add_argument("vault", help="Path to the vault file")
    p_show.add_argument("--action", help="Filter by action type (lock/unlock/rotate)")
    p_show.add_argument("--limit", type=int, default=0, help="Show only the last N entries")
    p_show.set_defaults(func=cmd_history_show)

    # --- history record ---
    p_rec = subparsers.add_parser("history-record", help="Manually record a change event")
    p_rec.add_argument("vault", help="Path to the vault file")
    p_rec.add_argument("action", help="Action label (e.g. lock, unlock, rotate)")
    p_rec.add_argument("--actor", help="Who performed the action")
    p_rec.add_argument("--note", help="Optional annotation")
    p_rec.set_defaults(func=cmd_history_record)

    # --- history clear ---
    p_clr = subparsers.add_parser("history-clear", help="Clear vault change history")
    p_clr.add_argument("vault", help="Path to the vault file")
    p_clr.set_defaults(func=cmd_history_clear)
