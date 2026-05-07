"""CLI subcommand: envault compare — compare two encrypted vault files."""

from __future__ import annotations

import argparse
import sys

from envault.compare import compare_vaults, format_compare


def cmd_compare(args: argparse.Namespace) -> None:
    try:
        result = compare_vaults(
            left_path=args.left,
            right_path=args.right,
            key=args.key,
            left_key=getattr(args, "left_key", None),
            right_key=getattr(args, "right_key", None),
            mask_values=not args.show_values,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(format_compare(result))

    if args.exit_code and result.has_differences():
        sys.exit(1)


def build_compare_subparsers(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "compare",
        help="Compare two encrypted vault files side-by-side.",
    )
    p.add_argument("left", help="Path to the first (left) vault file.")
    p.add_argument("right", help="Path to the second (right) vault file.")
    p.add_argument("--key", required=True, help="Shared decryption key for both vaults.")
    p.add_argument("--left-key", dest="left_key", default=None, help="Override key for left vault.")
    p.add_argument("--right-key", dest="right_key", default=None, help="Override key for right vault.")
    p.add_argument(
        "--show-values",
        action="store_true",
        default=False,
        help="Display actual values for changed keys (default: masked).",
    )
    p.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 1 if differences are found.",
    )
    p.set_defaults(func=cmd_compare)
