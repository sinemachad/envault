"""CLI commands for searching vault files."""

import argparse
import sys

from envault.search import format_search_results, search_multiple_vaults, search_vault


def cmd_search(args: argparse.Namespace) -> None:
    """Search one or more vault files for keys matching a pattern."""
    vault_paths = args.vault if isinstance(args.vault, list) else [args.vault]
    mask = not args.reveal

    try:
        if len(vault_paths) == 1:
            result = search_vault(
                vault_paths[0],
                key=args.key,
                pattern=args.pattern,
                mask_values=mask,
            )
            results = [result]
        else:
            results = search_multiple_vaults(
                vault_paths,
                key=args.key,
                pattern=args.pattern,
                mask_values=mask,
            )

        total_matches = sum(len(r.matches) for r in results)
        if total_matches == 0:
            print("No matching keys found.")
            sys.exit(0)

        print(format_search_results(results))
        print(f"{total_matches} match(es) found.")

    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Search failed: {exc}", file=sys.stderr)
        sys.exit(1)


def build_search_subparsers(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'search' subcommand."""
    parser = subparsers.add_parser(
        "search",
        help="Search for keys inside one or more vault files.",
    )
    parser.add_argument(
        "vault",
        nargs="+",
        help="Path(s) to vault file(s) to search.",
    )
    parser.add_argument(
        "--key",
        required=True,
        help="Encryption key used to unlock the vault(s).",
    )
    parser.add_argument(
        "--pattern",
        default=None,
        help="Regex pattern to filter keys (case-insensitive).",
    )
    parser.add_argument(
        "--reveal",
        action="store_true",
        default=False,
        help="Show plaintext values instead of masking them.",
    )
    parser.set_defaults(func=cmd_search)
