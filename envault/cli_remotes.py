"""CLI commands for managing remote backends."""

import sys
from envault.remotes import add_remote, remove_remote, get_remote, list_remotes


def cmd_remote_add(args):
    """Register a new named remote."""
    try:
        entry = add_remote(args.name, args.url)
        print(f"Remote '{entry['name']}' added: {entry['url']}")
    except (ValueError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_remote_remove(args):
    """Remove a registered remote by name."""
    try:
        remove_remote(args.name)
        print(f"Remote '{args.name}' removed.")
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_remote_show(args):
    """Show details for a single remote."""
    try:
        entry = get_remote(args.name)
        print(f"name : {entry['name']}")
        print(f"url  : {entry['url']}")
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_remote_list(args):
    """List all registered remotes."""
    remotes = list_remotes()
    if not remotes:
        print("No remotes configured.")
        return
    for r in remotes:
        print(f"  {r['name']:20s}  {r['url']}")


def build_remote_subparsers(subparsers):
    remote_parser = subparsers.add_parser("remote", help="Manage remote backends")
    remote_sub = remote_parser.add_subparsers(dest="remote_cmd", required=True)

    p_add = remote_sub.add_parser("add", help="Register a remote")
    p_add.add_argument("name", help="Unique name for the remote")
    p_add.add_argument("url", help="URL of the remote (https://, s3://, file://)")
    p_add.set_defaults(func=cmd_remote_add)

    p_remove = remote_sub.add_parser("remove", help="Remove a remote")
    p_remove.add_argument("name", help="Name of the remote to remove")
    p_remove.set_defaults(func=cmd_remote_remove)

    p_show = remote_sub.add_parser("show", help="Show a remote's details")
    p_show.add_argument("name", help="Name of the remote")
    p_show.set_defaults(func=cmd_remote_show)

    p_list = remote_sub.add_parser("list", help="List all remotes")
    p_list.set_defaults(func=cmd_remote_list)

    return remote_parser
