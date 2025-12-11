# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Project Overview

Security Lake Tools is a CLI utility for managing AWS Security Lake custom
sources with OCSF (Open Cybersecurity Schema Framework) support. It creates
custom log sources in Amazon Security Lake for specific OCSF event classes.

## Architecture

The package follows a simple structure:

- `src/security_lake_tools/cli.py` - Main CLI entry point with subcommand routing via argparse. Currently only has `create-source` subcommand.
- `src/security_lake_tools/create_source.py` - Core implementation containing:
  - `OCSF_EVENT_CLASSES` dict mapping class UIDs to event class names
  - `create_custom_source()` - Creates Security Lake custom sources via boto3
  - `create_glue_role()` - Automatically creates IAM Glue service role with required policies
  - `verify_glue_role()` - Checks if a Glue role exists

The CLI uses subcommand pattern via argparse subparsers. The `cli.py` reconstructs `sys.argv` to pass arguments to `create_source.main()`.

## Key Behaviors

- Auto-detects AWS account ID via STS `get_caller_identity` if not provided
- Auto-creates Glue IAM role if it doesn't exist (unless `--no-create-role`)
- Source names follow pattern: `tnz-ocsf-{class_uid}`
- Handles AWS SSO token expiration with specific guidance
