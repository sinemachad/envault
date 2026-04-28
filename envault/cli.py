"""Command-line interface for envault."""

import sys
import argparse

from envault.crypto import generate_key
from envault.vault import lock, unlock, DEFAULT_ENV_FILE, DEFAULT_VAULT_FILE


def cmd_keygen(args: argparse.Namespace) -> int:
    """Generate and print a new encryption key."""
    key = generate_key()
    print(key)
    return 0


def cmd_lock(args: argparse.Namespace) -> int:
    """Encrypt .env file into a vault file."""
    try:
        vault_path = lock(
            key=args.key,
            env_path=args.env,
            vault_path=args.vault,
            password=args.password,
        )
        print(f"Locked: {args.env} -> {vault_path}")
        return 0
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Encryption failed: {exc}", file=sys.stderr)
        return 1


def cmd_unlock(args: argparse.Namespace) -> int:
    """Decrypt a vault file into a .env file."""
    try:
        data = unlock(
            key=args.key,
            vault_path=args.vault,
            env_path=args.env,
            password=args.password,
        )
        print(f"Unlocked: {args.vault} -> {args.env} ({len(data)} variables)")
        return 0
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Decryption failed: {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault",
        description="Lightweight secrets manager for .env files",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("keygen", help="Generate a new encryption key")

    lock_p = sub.add_parser("lock", help="Encrypt .env into vault")
    lock_p.add_argument("--key", required=True, help="Encryption key")
    lock_p.add_argument("--env", default=DEFAULT_ENV_FILE)
    lock_p.add_argument("--vault", default=DEFAULT_VAULT_FILE)
    lock_p.add_argument("--password", default=None)

    unlock_p = sub.add_parser("unlock", help="Decrypt vault into .env")
    unlock_p.add_argument("--key", required=True, help="Encryption key")
    unlock_p.add_argument("--vault", default=DEFAULT_VAULT_FILE)
    unlock_p.add_argument("--env", default=DEFAULT_ENV_FILE)
    unlock_p.add_argument("--password", default=None)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    dispatch = {"keygen": cmd_keygen, "lock": cmd_lock, "unlock": cmd_unlock}
    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
