"""CLI sub-commands for runtime environment injection."""

from __future__ import annotations

import argparse
import subprocess
import sys

from envault.env_inject import inject_env


def cmd_inject(args: argparse.Namespace) -> None:
    """Inject decrypted vault variables into the current process environment,
    then optionally exec a command."""
    try:
        result = inject_env(
            args.vault,
            args.key,
            profile=args.profile,
            overwrite=args.overwrite,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not args.quiet:
        print(f"Injected {len(result.injected)} variable(s).", flush=True)
        if result.skipped:
            print(
                f"Skipped {len(result.skipped)} already-set variable(s) "
                "(use --overwrite to replace)."
            )

    if args.command:
        try:
            proc = subprocess.run(args.command, env=None)  # inherits os.environ
            sys.exit(proc.returncode)
        except FileNotFoundError:
            print(f"error: command not found: {args.command[0]}", file=sys.stderr)
            sys.exit(127)


def build_inject_subparsers(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "inject",
        help="Inject decrypted .env variables into the shell environment.",
    )
    p.add_argument("vault", help="Path to the .env.vault file.")
    p.add_argument("key", help="Encryption key (base-64 string).")
    p.add_argument(
        "--profile",
        default=None,
        metavar="NAME",
        help="Restrict injection to keys allowed for this profile.",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite variables that are already set in the environment.",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress informational output.",
    )
    p.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Optional command to run with the injected environment.",
    )
    p.set_defaults(func=cmd_inject)
