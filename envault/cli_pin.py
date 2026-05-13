"""CLI commands for vault key pinning."""

import argparse
import sys

from envault.pin import pin_key, read_pin, remove_pin, verify_pin


def cmd_pin_set(args: argparse.Namespace) -> None:
    """Pin a vault to the provided key."""
    try:
        record = pin_key(
            key=args.key,
            vault_path=args.vault,
            label=args.label,
            base_dir=args.base_dir,
        )
        print(f"Pinned vault '{record['vault']}' to key fingerprint {record['fingerprint']}")
        if record["label"]:
            print(f"  Label    : {record['label']}")
        print(f"  Pinned at: {record['pinned_at']}")
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_pin_show(args: argparse.Namespace) -> None:
    """Display the current pin record."""
    record = read_pin(base_dir=args.base_dir)
    if record is None:
        print("No pin set.")
        return
    print(f"Vault      : {record['vault']}")
    print(f"Fingerprint: {record['fingerprint']}")
    print(f"Label      : {record['label'] or '(none)'}")
    print(f"Pinned at  : {record['pinned_at']}")


def cmd_pin_verify(args: argparse.Namespace) -> None:
    """Verify that a key matches the stored pin."""
    ok = verify_pin(key=args.key, base_dir=args.base_dir)
    if ok:
        print("Key matches pinned fingerprint. ✓")
    else:
        print("Key does NOT match pinned fingerprint. ✗", file=sys.stderr)
        sys.exit(1)


def cmd_pin_remove(args: argparse.Namespace) -> None:
    """Remove the pin file."""
    removed = remove_pin(base_dir=args.base_dir)
    if removed:
        print("Pin removed.")
    else:
        print("No pin file found; nothing to remove.")


def build_pin_subparsers(subparsers) -> None:  # noqa: ANN001
    pin_parser = subparsers.add_parser("pin", help="Manage vault key pins")
    pin_sub = pin_parser.add_subparsers(dest="pin_cmd", required=True)

    # set
    p_set = pin_sub.add_parser("set", help="Pin vault to a key")
    p_set.add_argument("vault", help="Path to the vault file")
    p_set.add_argument("key", help="Encryption key to pin")
    p_set.add_argument("--label", default="", help="Optional human-readable label")
    p_set.add_argument("--base-dir", default=".", dest="base_dir")
    p_set.set_defaults(func=cmd_pin_set)

    # show
    p_show = pin_sub.add_parser("show", help="Show current pin")
    p_show.add_argument("--base-dir", default=".", dest="base_dir")
    p_show.set_defaults(func=cmd_pin_show)

    # verify
    p_verify = pin_sub.add_parser("verify", help="Verify a key against the pin")
    p_verify.add_argument("key", help="Key to verify")
    p_verify.add_argument("--base-dir", default=".", dest="base_dir")
    p_verify.set_defaults(func=cmd_pin_verify)

    # remove
    p_remove = pin_sub.add_parser("remove", help="Remove the pin")
    p_remove.add_argument("--base-dir", default=".", dest="base_dir")
    p_remove.set_defaults(func=cmd_pin_remove)
