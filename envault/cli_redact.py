"""CLI commands for redacting sensitive values before display."""

import argparse
import sys

from envault.vault import unlock
from envault.redact import redact_env, format_redacted


def cmd_redact(args: argparse.Namespace) -> None:
    """Decrypt a vault and print it with sensitive values masked."""
    try:
        env = unlock(args.vault, args.key)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    extra = args.pattern or []
    custom = args.mask_key or []

    result = redact_env(env, extra_patterns=extra, custom_keys=custom)

    if args.show_masked:
        print(f"# Masked keys ({len(result.masked_keys)}): {', '.join(result.masked_keys)}")

    print(format_redacted(result))


def build_redact_subparsers(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "redact",
        help="Print decrypted env with sensitive values masked.",
    )
    p.add_argument("vault", help="Path to the encrypted vault file.")
    p.add_argument("--key", required=True, help="Encryption key.")
    p.add_argument(
        "--pattern",
        metavar="PATTERN",
        action="append",
        help="Extra substring pattern that marks a key as sensitive (repeatable).",
    )
    p.add_argument(
        "--mask-key",
        metavar="KEY",
        action="append",
        help="Explicitly mask this key regardless of its name (repeatable).",
    )
    p.add_argument(
        "--show-masked",
        action="store_true",
        help="Print a comment listing all masked key names.",
    )
    p.set_defaults(func=cmd_redact)
