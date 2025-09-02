#!/usr/bin/env python3
"""Main CLI entry point for security-lake-tools."""

import argparse
import sys

from .create_source import main as create_source_main


def main() -> int:
    """Main CLI entry point with subcommands."""
    parser = argparse.ArgumentParser(
        description="AWS Security Lake management tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
        required=True,
    )

    # Create source subcommand
    create_parser = subparsers.add_parser(
        "create-source",
        help="Create a custom log source in Security Lake",
        description="Create a custom log source in Amazon Security Lake for OCSF event class",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 1001 --region us-east-1 --account-id 123456789012 \\
      --external-id my-external-id --glue-role-arn arn:aws:iam::123456789012:role/MyGlueRole
  %(prog)s 4003 --external-id my-external-id  # Uses auto-detected account ID
  %(prog)s --list  # List all available OCSF class UIDs
        """,
    )

    create_parser.add_argument(
        "class_uid", nargs="?", help="OCSF class UID (e.g., 1001 for File System Activity)"
    )

    create_parser.add_argument(
        "--region", default="us-east-1", help="AWS region (default: us-east-1)"
    )

    create_parser.add_argument(
        "--account-id", help="AWS account ID (default: auto-detected using boto3)"
    )

    create_parser.add_argument(
        "--external-id",
        required=False,
        help="External ID for trust relationship (required unless --list is used)",
    )

    create_parser.add_argument(
        "--glue-role-arn", help="ARN of the Glue service role (default: auto-generated)"
    )

    create_parser.add_argument("--profile", help="AWS profile to use")

    create_parser.add_argument(
        "--list", action="store_true", help="List all available OCSF class UIDs and exit"
    )

    create_parser.add_argument(
        "--skip-role-check", action="store_true", help="Skip verification that the Glue role exists"
    )

    create_parser.add_argument(
        "--no-create-role",
        action="store_true",
        help="Do not automatically create the Glue role if it doesn't exist",
    )

    args = parser.parse_args()

    if args.command == "create-source":
        # Pass the args directly to the create_source main function
        # We need to make it look like it came from the original parser
        sys.argv = ["security-lake-tools"]
        if args.class_uid:
            sys.argv.append(args.class_uid)
        if args.region != "us-east-1":
            sys.argv.extend(["--region", args.region])
        if args.account_id:
            sys.argv.extend(["--account-id", args.account_id])
        if args.external_id:
            sys.argv.extend(["--external-id", args.external_id])
        if args.glue_role_arn:
            sys.argv.extend(["--glue-role-arn", args.glue_role_arn])
        if args.profile:
            sys.argv.extend(["--profile", args.profile])
        if args.list:
            sys.argv.append("--list")
        if args.skip_role_check:
            sys.argv.append("--skip-role-check")
        if args.no_create_role:
            sys.argv.append("--no-create-role")

        return create_source_main()

    return 0


if __name__ == "__main__":
    sys.exit(main())
