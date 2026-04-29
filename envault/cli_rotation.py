"""CLI sub-commands for key rotation."""

import argparse
import sys

from .rotation import rotate_key
from .crypto import generate_key


def cmd_rotate(args: argparse.Namespace) -> None:
    """Handle the ``envault rotate`` sub-command."""
    old_key = args.old_key
    new_key = args.new_key  # may be None

    try:
        result_key = rotate_key(args.vault, old_key, new_key=new_key)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.print_key:
        print(result_key)
    else:
        print("Key rotated successfully.")
        print(f"New key: {result_key}")
        print(
            "Share this key with your team and update any CI/CD secrets.",
            file=sys.stderr,
        )


def build_rotation_subparsers(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register rotation sub-commands on *subparsers*."""
    rotate_parser = subparsers.add_parser(
        "rotate",
        help="Re-encrypt a vault with a new key.",
        description=(
            "Decrypts the vault using OLD_KEY and re-encrypts it with a "
            "freshly generated key (or NEW_KEY when supplied)."
        ),
    )
    rotate_parser.add_argument(
        "vault",
        metavar="VAULT",
        help="Path to the .env.vault file to rotate.",
    )
    rotate_parser.add_argument(
        "old_key",
        metavar="OLD_KEY",
        help="Current encryption key (base-64 encoded).",
    )
    rotate_parser.add_argument(
        "--new-key",
        dest="new_key",
        default=None,
        metavar="NEW_KEY",
        help="Explicit replacement key.  Auto-generated when omitted.",
    )
    rotate_parser.add_argument(
        "--print-key",
        action="store_true",
        default=False,
        help="Print only the new key (useful for scripting).",
    )
    rotate_parser.set_defaults(func=cmd_rotate)
