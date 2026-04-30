"""CLI commands for vault snapshot management."""

import argparse
import sys
import time
from datetime import datetime

from envault.snapshots import save_snapshot, restore_snapshot, list_snapshots, delete_snapshot


def cmd_snapshot_save(args: argparse.Namespace) -> None:
    """Save a named snapshot of the current vault."""
    try:
        entry = save_snapshot(
            name=args.name,
            vault_path=args.vault,
            key=args.key,
        )
        ts = datetime.fromtimestamp(entry["created_at"]).strftime("%Y-%m-%d %H:%M:%S")
        print(f"Snapshot '{entry['name']}' saved at {ts}")
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error saving snapshot: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_snapshot_restore(args: argparse.Namespace) -> None:
    """Restore a named snapshot to the vault path."""
    try:
        restore_snapshot(
            name=args.name,
            vault_path=args.vault,
            key=args.key,
        )
        print(f"Snapshot '{args.name}' restored to {args.vault}")
    except KeyError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_snapshot_list(args: argparse.Namespace) -> None:
    """List all saved snapshots."""
    entries = list_snapshots()
    if not entries:
        print("No snapshots found.")
        return
    print(f"{'NAME':<20} {'VAULT PATH':<35} {'CREATED AT'}")
    print("-" * 70)
    for entry in entries:
        ts = datetime.fromtimestamp(entry["created_at"]).strftime("%Y-%m-%d %H:%M:%S")
        print(f"{entry['name']:<20} {entry['vault_path']:<35} {ts}")


def cmd_snapshot_delete(args: argparse.Namespace) -> None:
    """Delete a named snapshot."""
    try:
        delete_snapshot(args.name)
        print(f"Snapshot '{args.name}' deleted.")
    except KeyError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def build_snapshot_subparsers(subparsers) -> None:
    snap_parser = subparsers.add_parser("snapshot", help="Manage vault snapshots")
    snap_sub = snap_parser.add_subparsers(dest="snapshot_cmd", required=True)

    # save
    p_save = snap_sub.add_parser("save", help="Save a snapshot")
    p_save.add_argument("name", help="Snapshot name")
    p_save.add_argument("--vault", required=True, help="Path to vault file")
    p_save.add_argument("--key", required=True, help="Encryption key")
    p_save.set_defaults(func=cmd_snapshot_save)

    # restore
    p_restore = snap_sub.add_parser("restore", help="Restore a snapshot")
    p_restore.add_argument("name", help="Snapshot name")
    p_restore.add_argument("--vault", required=True, help="Target vault file path")
    p_restore.add_argument("--key", required=True, help="Encryption key")
    p_restore.set_defaults(func=cmd_snapshot_restore)

    # list
    p_list = snap_sub.add_parser("list", help="List all snapshots")
    p_list.set_defaults(func=cmd_snapshot_list)

    # delete
    p_delete = snap_sub.add_parser("delete", help="Delete a snapshot")
    p_delete.add_argument("name", help="Snapshot name")
    p_delete.set_defaults(func=cmd_snapshot_delete)
