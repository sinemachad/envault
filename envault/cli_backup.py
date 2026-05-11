"""CLI sub-commands for vault backup management."""

import sys

from envault.backup import create_backup, delete_backup, list_backups, restore_backup


def cmd_backup_create(args):
    try:
        entry = create_backup(
            vault_path=args.vault,
            base_dir=args.base_dir,
            label=getattr(args, "label", None),
        )
        print(f"Backup created: {entry['id']}")
        if entry["label"]:
            print(f"  Label    : {entry['label']}")
        print(f"  Timestamp: {entry['timestamp']}")
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_backup_list(args):
    entries = list_backups(base_dir=args.base_dir)
    if not entries:
        print("No backups found.")
        return
    for e in entries:
        label = f"  [{e['label']}]" if e["label"] else ""
        print(f"{e['id']}{label}  {e['timestamp']}")


def cmd_backup_restore(args):
    try:
        entry = restore_backup(
            backup_id=args.backup_id,
            dest_path=args.vault,
            base_dir=args.base_dir,
        )
        print(f"Restored backup '{entry['id']}' -> {args.vault}")
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_backup_delete(args):
    try:
        entry = delete_backup(backup_id=args.backup_id, base_dir=args.base_dir)
        print(f"Deleted backup: {entry['id']}")
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def build_backup_subparsers(subparsers):
    backup_parser = subparsers.add_parser("backup", help="Manage vault backups")
    backup_sub = backup_parser.add_subparsers(dest="backup_cmd")

    p_create = backup_sub.add_parser("create", help="Create a backup of the vault")
    p_create.add_argument("vault", help="Path to the .env.vault file")
    p_create.add_argument("--label", default="", help="Optional human-readable label")
    p_create.add_argument("--base-dir", default=".", dest="base_dir")
    p_create.set_defaults(func=cmd_backup_create)

    p_list = backup_sub.add_parser("list", help="List all backups")
    p_list.add_argument("--base-dir", default=".", dest="base_dir")
    p_list.set_defaults(func=cmd_backup_list)

    p_restore = backup_sub.add_parser("restore", help="Restore a backup")
    p_restore.add_argument("backup_id", help="ID of the backup to restore")
    p_restore.add_argument("vault", help="Destination path for the restored vault")
    p_restore.add_argument("--base-dir", default=".", dest="base_dir")
    p_restore.set_defaults(func=cmd_backup_restore)

    p_delete = backup_sub.add_parser("delete", help="Delete a backup")
    p_delete.add_argument("backup_id", help="ID of the backup to delete")
    p_delete.add_argument("--base-dir", default=".", dest="base_dir")
    p_delete.set_defaults(func=cmd_backup_delete)

    return backup_parser
