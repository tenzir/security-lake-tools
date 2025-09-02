# Security Lake Tools

[![CI](https://github.com/tenzir/security-lake-tools/actions/workflows/test.yml/badge.svg)](https://github.com/tenzir/security-lake-tools/actions/workflows/test.yml)
[![PyPI version](https://img.shields.io/pypi/v/security-lake-tools.svg)](https://pypi.org/project/security-lake-tools/)
[![Python versions](https://img.shields.io/pypi/pyversions/security-lake-tools.svg)](https://pypi.org/project/security-lake-tools/)
[![License](https://img.shields.io/pypi/l/security-lake-tools.svg)](https://github.com/tenzir/security-lake-tools/blob/main/LICENSE)

Tools for managing AWS Security Lake custom sources with OCSF (Open Cybersecurity Schema Framework) support.

## Features

- ✨ Create Security Lake custom sources for all OCSF event classes
- 🔧 Automatic IAM role creation for AWS Glue crawlers
- 📋 Built-in OCSF event class mapping
- 🔍 Detailed error messages and troubleshooting guidance
- 🚀 Simple command-line interface

## Installation

The easiest way to use this tool is with [uvx](https://github.com/astral-sh/uv),
which runs the tool in an isolated environment:

```sh
uvx security-lake-tools --help
```

Alternatively, install it with:

```bash
uv pip install security-lake-tools
```

## Quick Start

### Create a custom source

```sh
uvx security-lake-tools create-source \
  --external-id your-external-id \
  --region us-east-1 \
  --account-id 123456789012 \
  --profile production \
  1001
```

### List available OCSF event classes

```bash
uvx security-lake-tools create-source --list

# Or if installed
security-lake-tools create-source --list
```

## Detailed Usage

### Prerequisites

1. **AWS Credentials**: Configure AWS credentials using one of:
   - `aws configure` (for access keys)
   - `aws configure sso` (for SSO authentication)
   - Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
   - IAM role (if running on EC2)

2. **Security Lake**: Ensure Security Lake is enabled in your target region

3. **IAM Permissions**: You need permissions to:
   - Create IAM roles and policies
   - Create Security Lake custom sources
   - Create and manage Glue crawlers

### Command-Line Options

```bash
security-lake-tools create-source [OPTIONS] CLASS_UID

Arguments:
  CLASS_UID          OCSF class UID (e.g., 1001 for File System Activity)

Options:
  --region           AWS region (default: us-east-1)
  --account-id       AWS account ID (default: auto-detected)
  --external-id      External ID for trust relationship (required)
  --glue-role-arn    ARN of existing Glue service role
  --profile          AWS profile to use
  --no-create-role   Don't auto-create Glue role if missing
  --skip-role-check  Skip Glue role verification
  --list             List all available OCSF class UIDs
  --help             Show help message
```

### OCSF Event Classes

The tool supports all standard OCSF event classes that are accepted by Security
Lake.

> [!NOTE]
> AWS Security Lake does not support the OCSF Base Event (class_uid 0). While
> Base Event exists in the OCSF specification as an abstract parent class,
> Security Lake only accepts concrete event types.

#### System Activity (1xxx)

- 1001: File System Activity
- 1002: Kernel Extension Activity
- 1003: Kernel Activity
- 1004: Memory Activity
- 1005: Module Activity
- 1006: Scheduled Job Activity
- 1007: Process Activity
- 1008: Event Log Activity
- 1009: Script Activity

#### Findings (2xxx)

- 2001: Security Finding
- 2002: Vulnerability Finding
- 2003: Compliance Finding
- 2004: Detection Finding
- 2005: Incident Finding
- 2006: Data Security Finding
- 2007: Application Security Posture Finding

[See full list with `--list` option]

### IAM Role Management

By default, the tool automatically creates a Glue service role with:

- Trust relationship with `glue.amazonaws.com`
- AWS managed policy `AWSGlueServiceRole`
- Custom S3 policy for Security Lake buckets
- Lake Formation permissions

To use an existing role:

```bash
security-lake-tools create-source 1001 \
  --external-id your-external-id \
  --glue-role-arn arn:aws:iam::123456789012:role/MyExistingGlueRole
```

To prevent automatic role creation:

```bash
security-lake-tools create-source 1001 \
  --external-id your-external-id \
  --no-create-role
```

## What Gets Created

For each custom source, Security Lake creates:

1. **Provider Role**: `AmazonSecurityLake-Provider-{source-name}-{region}`
   - Allows the specified account to write logs to Security Lake

2. **S3 Location**: `s3://aws-security-data-lake-{region}-{id}/ext/{source-name}/`
   - Where your OCSF-formatted logs should be written

3. **Glue Resources**:
   - Crawler: Discovers and catalogs your data
   - Database: Stores metadata
   - Table: Defines the schema

## Troubleshooting

### Common Issues

1. **"The Glue role does not exist"**
   - Let the tool create it automatically (default behavior)
   - Or create manually with proper permissions
   - Or specify existing role with `--glue-role-arn`

2. **"Source already exists"**
   - Delete the existing source first
   - Or use a different class UID

3. **"Security Lake not enabled"**
   - Enable Security Lake in the AWS Console
   - Ensure you're using the correct region

4. **"Invalid principal" error**
   - Ensure the account ID is correct
   - Check that the external ID matches your configuration

### Debug Mode

For more detailed output, set the `AWS_DEBUG` environment variable:

```bash
AWS_DEBUG=1 security-lake-tools create-source 1001 --external-id test
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/security-lake-tools
cd security-lake-tools

# Install with development dependencies using uv
uv pip install -e ".[dev]"
```

### Running Tests

```bash
# Run tests
uv run pytest

# With coverage
uv run pytest --cov=security_lake_tools
```

### Code Quality

```bash
# Format code
uv run black src tests

# Lint
uv run ruff check src tests

# Type checking
uv run mypy src
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- AWS Security Lake team for the service
- OCSF community for the schema framework
- Contributors and users of this tool
