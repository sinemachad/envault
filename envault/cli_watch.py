"""CLI sub-commands for the watch feature."""

import argparse
import sys


def cmd_watch(args: argparse.Namespace) -> None:
    """Start watching a .env file and re-lock it on every save."""
    from envault.watch import watch_env, make_lock_callback

    env_path = args.env_file
    vault_path = args.vault_file
    key = args.key
    interval = args.interval

    if not key:
        print("error: --key is required", file=sys.stderr)
        sys.exit(1)

    callback = make_lock_callback(verbose=not args.quiet)

    if not args.quiet:
        print(
            f"[envault] watching {env_path} (interval={interval}s) "
            f"— press Ctrl+C to stop"
        )

    try:
        watch_env(
            env_path=env_path,
            vault_path=vault_path,
            key=key,
            on_lock=callback,
            poll_interval=interval,
        )
    except KeyboardInterrupt:
        if not args.quiet:
            print("\n[envault] watch stopped.")


def build_watch_subparsers(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "watch",
        help="Watch a .env file and re-lock it automatically on change.",
    )
    p.add_argument("env_file", help="Plaintext .env file to monitor.")
    p.add_argument("vault_file", help="Encrypted vault file to write on change.")
    p.add_argument("--key", required=True, help="Encryption key.")
    p.add_argument(
        "--interval",
        type=float,
        default=1.0,
        metavar="SECONDS",
        help="Poll interval in seconds (default: 1.0).",
    )
    p.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress informational output.",
    )
    p.set_defaults(func=cmd_watch)
