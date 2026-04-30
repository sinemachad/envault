"""CLI commands for vault file tagging."""
import argparse
from envault.tags import add_tag, remove_tag, list_tags, find_by_tag


def cmd_tag_add(args: argparse.Namespace) -> None:
    """Add a tag to a vault file."""
    try:
        result = add_tag(args.vault_file, args.tag)
        print(f"Tagged '{args.vault_file}' with '{args.tag}'")
        print("Tags: " + ", ".join(result["tags"]))
    except Exception as e:
        print(f"Error: {e}")
        raise SystemExit(1)


def cmd_tag_remove(args: argparse.Namespace) -> None:
    """Remove a tag from a vault file."""
    try:
        result = remove_tag(args.vault_file, args.tag)
        print(f"Removed tag '{args.tag}' from '{args.vault_file}'")
        remaining = result["tags"]
        if remaining:
            print("Remaining tags: " + ", ".join(remaining))
        else:
            print("No tags remaining.")
    except ValueError as e:
        print(f"Error: {e}")
        raise SystemExit(1)


def cmd_tag_list(args: argparse.Namespace) -> None:
    """List all tags for a vault file."""
    tags = list_tags(args.vault_file)
    if tags:
        print(f"Tags for '{args.vault_file}':")
        for tag in tags:
            print(f"  - {tag}")
    else:
        print(f"No tags found for '{args.vault_file}'.")


def cmd_tag_find(args: argparse.Namespace) -> None:
    """Find all vault files with a given tag."""
    files = find_by_tag(args.tag)
    if files:
        print(f"Vault files tagged '{args.tag}':")
        for vf in files:
            print(f"  - {vf}")
    else:
        print(f"No vault files found with tag '{args.tag}'.")


def build_tag_subparsers(subparsers) -> None:
    tag_parser = subparsers.add_parser("tag", help="Manage vault file tags")
    tag_sub = tag_parser.add_subparsers(dest="tag_command", required=True)

    p_add = tag_sub.add_parser("add", help="Add a tag to a vault file")
    p_add.add_argument("vault_file", help="Path to the vault file")
    p_add.add_argument("tag", help="Tag to add")
    p_add.set_defaults(func=cmd_tag_add)

    p_remove = tag_sub.add_parser("remove", help="Remove a tag from a vault file")
    p_remove.add_argument("vault_file", help="Path to the vault file")
    p_remove.add_argument("tag", help="Tag to remove")
    p_remove.set_defaults(func=cmd_tag_remove)

    p_list = tag_sub.add_parser("list", help="List tags for a vault file")
    p_list.add_argument("vault_file", help="Path to the vault file")
    p_list.set_defaults(func=cmd_tag_list)

    p_find = tag_sub.add_parser("find", help="Find vault files by tag")
    p_find.add_argument("tag", help="Tag to search for")
    p_find.set_defaults(func=cmd_tag_find)
