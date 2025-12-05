# 🔐 security-lake-tools

`security-lake-tools` is a CLI utility for managing AWS Security Lake custom
sources with OCSF (Open Cybersecurity Schema Framework) support. It creates
custom log sources in Amazon Security Lake for specific OCSF event classes.

## ✨ Highlights

- 🚀 Create Security Lake custom sources for all OCSF event classes with a
  single command.
- 🔧 Automatic IAM role creation for AWS Glue crawlers with proper permissions.
- 📋 Built-in OCSF event class mapping—list available classes with `--list`.
- 🔍 Detailed error messages and troubleshooting guidance for common AWS issues.

## 📦 Installation

`security-lake-tools` ships on PyPI. Use
[`uvx`](https://docs.astral.sh/uv/concepts/tools/) to fetch and execute the
latest compatible version on demand:

```sh
uvx security-lake-tools --help
```

`uvx` downloads the newest release, runs it in an isolated environment, and
caches the result for snappy subsequent invocations.

## 🛠️ Usage

### Prerequisites

1. **AWS Credentials**: Configure via `aws configure`, SSO, environment
   variables, or IAM role.
2. **Security Lake**: Ensure Security Lake is enabled in your target region.
3. **IAM Permissions**: Create IAM roles/policies, Security Lake custom sources,
   and Glue crawlers.

### Create a Custom Source

```sh
uvx security-lake-tools create-source \
  --external-id your-external-id \
  --region us-east-1 \
  --account-id 123456789012 \
  --profile production \
  1001
```

### List OCSF Event Classes

```sh
uvx security-lake-tools create-source --list
```

### Command-Line Options

```
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

### IAM Role Management

By default, the tool auto-creates a Glue service role with proper trust
relationships and policies. Use `--glue-role-arn` to specify an existing role,
or `--no-create-role` to disable auto-creation.

## 🤝 Contributing

Want to contribute? We're all-in on agentic coding with [Claude
Code](https://claude.ai/code)! The repo comes pre-configured with our [custom
plugins](https://github.com/tenzir/claude-plugins)—just clone and start hacking.

## 📄 License

`security-lake-tools` is released under the Apache License, Version 2.0. Consult
[`LICENSE`](LICENSE) for the full text.
