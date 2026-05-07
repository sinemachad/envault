"""CLI subcommands for the export feature."""

import argparse
import sys

from envault.vault import unlock
from envault.export import export_env, SUPPORTED_FORMATS


def cmd_export(args: argparse.Namespace) -> None:
    """Handle `envault export` subcommand."""
    try:
        env = unlock(args.vault, args.key)
    except Exception as exc:
        print(f"error: could not decrypt vault — {exc}", file=sys.stderr)
        sys.exit(1)

    keys = args.keys if args.keys else None

    try:
        result = export_env(env, fmt=args.format, keys=keys)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        try:
            with open(args.output, "w") as fh:
                fh.write(result.content)
            if not args.quiet:
                print(f"Exported {result.count} variable(s) to {args.output} [{args.format}]")
        except OSError as exc:
            print(f"error: could not write file — {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        print(result.content)


def build_export_subparsers(sub: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = sub.add_parser("export", help="Export decrypted env variables to a file or stdout")
    p.add_argument("vault", help="Path to the encrypted vault file")
    p.add_argument("--key", required=True, help="Decryption key")
    p.add_argument(
        "--format", "-f",
        choices=SUPPORTED_FORMATS,
        default="dotenv",
        help="Output format (default: dotenv)",
    )
    p.add_argument(
        "--output", "-o",
        default=None,
        help="Write output to this file instead of stdout",
    )
    p.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        default=None,
        help="Only export these specific keys",
    )
    p.add_argument("--quiet", "-q", action="store_true", help="Suppress informational output")
    p.set_defaults(func=cmd_export)
