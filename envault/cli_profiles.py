"""CLI commands for managing envault profiles."""

import argparse
from envault.profiles import add_profile, remove_profile, get_profile, list_profiles


def cmd_profile_add(args: argparse.Namespace) -> None:
    """Register a new profile."""
    try:
        add_profile(args.name, args.vault_file)
        print(f"Profile '{args.name}' added -> {args.vault_file}")
    except ValueError as e:
        print(f"Error: {e}")
        raise SystemExit(1)


def cmd_profile_remove(args: argparse.Namespace) -> None:
    """Remove an existing profile."""
    try:
        remove_profile(args.name)
        print(f"Profile '{args.name}' removed.")
    except KeyError as e:
        print(f"Error: {e}")
        raise SystemExit(1)


def cmd_profile_show(args: argparse.Namespace) -> None:
    """Show details of a specific profile."""
    try:
        profile = get_profile(args.name)
        print(f"Profile : {args.name}")
        print(f"Vault   : {profile['vault_file']}")
    except KeyError as e:
        print(f"Error: {e}")
        raise SystemExit(1)


def cmd_profile_list(args: argparse.Namespace) -> None:
    """List all registered profiles."""
    names = list_profiles()
    if not names:
        print("No profiles registered.")
    else:
        print("Profiles:")
        for name in names:
            print(f"  - {name}")


def build_profile_subparsers(subparsers) -> None:
    """Attach profile sub-commands to an existing subparsers group."""
    profile_parser = subparsers.add_parser("profile", help="Manage named vault profiles")
    profile_sub = profile_parser.add_subparsers(dest="profile_cmd", required=True)

    # add
    p_add = profile_sub.add_parser("add", help="Register a new profile")
    p_add.add_argument("name", help="Profile name")
    p_add.add_argument("vault_file", help="Path to the associated vault file")
    p_add.set_defaults(func=cmd_profile_add)

    # remove
    p_rm = profile_sub.add_parser("remove", help="Remove a profile")
    p_rm.add_argument("name", help="Profile name")
    p_rm.set_defaults(func=cmd_profile_remove)

    # show
    p_show = profile_sub.add_parser("show", help="Show profile details")
    p_show.add_argument("name", help="Profile name")
    p_show.set_defaults(func=cmd_profile_show)

    # list
    p_list = profile_sub.add_parser("list", help="List all profiles")
    p_list.set_defaults(func=cmd_profile_list)
