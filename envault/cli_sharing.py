"""CLI commands for bundle export/import (team sharing)."""

import argparse
import sys

from envault.sharing import export_bundle, import_bundle


def cmd_export(args: argparse.Namespace) -> None:
    """Handle the 'export' CLI command."""
    try:
        bundle_json = export_bundle(
            env_path=args.env_file,
            passphrase=args.passphrase,
            output_path=args.output,
        )
        if args.output:
            print(f"Bundle written to {args.output}")
        else:
            print(bundle_json)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_import(args: argparse.Namespace) -> None:
    """Handle the 'import' CLI command."""
    try:
        env_vars = import_bundle(
            bundle_path=args.bundle_file,
            passphrase=args.passphrase,
            output_path=args.output,
        )
        if args.output:
            print(f"Decrypted {len(env_vars)} variable(s) written to {args.output}")
        else:
            for key, value in env_vars.items():
                print(f"{key}={value}")
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception:
        print("Error: decryption failed — wrong passphrase or corrupt bundle.", file=sys.stderr)
        sys.exit(1)


def build_sharing_subparsers(subparsers: argparse._SubParsersAction) -> None:
    """Register 'export' and 'import' subcommands onto an existing subparser group."""
    # export
    p_export = subparsers.add_parser("export", help="Encrypt and export .env as a shareable bundle")
    p_export.add_argument("env_file", help="Path to the .env file to export")
    p_export.add_argument("passphrase", help="Shared passphrase for encryption")
    p_export.add_argument("-o", "--output", default=None, help="Output bundle file path")
    p_export.set_defaults(func=cmd_export)

    # import
    p_import = subparsers.add_parser("import", help="Decrypt and import a bundle into a .env file")
    p_import.add_argument("bundle_file", help="Path to the bundle JSON file")
    p_import.add_argument("passphrase", help="Shared passphrase for decryption")
    p_import.add_argument("-o", "--output", default=None, help="Output .env file path")
    p_import.set_defaults(func=cmd_import)
