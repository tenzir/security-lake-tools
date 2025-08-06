#!/usr/bin/env python3
"""
Create a custom log source in Amazon Security Lake for a specific OCSF event class.

This script creates custom sources with explicit parameters, avoiding environment
variable dependencies for better reproducibility and clarity.
"""

import argparse
import json
import sys
import time

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError, TokenRetrievalError
except ImportError:
    print("Error: boto3 is required. Install it with: pip install boto3")
    sys.exit(1)


# Map OCSF class UIDs to event class names
OCSF_EVENT_CLASSES: dict[str, str] = {
    # System Activity
    "1001": "FILE_ACTIVITY",
    "1002": "KERNEL_EXTENSION",
    "1003": "KERNEL_ACTIVITY",
    "1004": "MEMORY_ACTIVITY",
    "1005": "MODULE_ACTIVITY",
    "1006": "SCHEDULED_JOB",
    "1007": "PROCESS_ACTIVITY",
    "1008": "EVENT_LOG",
    "1009": "SCRIPT_ACTIVITY",
    # Findings
    "2001": "SECURITY_FINDING",
    "2002": "VULNERABILITY_FINDING",
    "2003": "COMPLIANCE_FINDING",
    "2004": "DETECTION_FINDING",
    "2005": "INCIDENT_FINDING",
    "2006": "DATA_SECURITY_FINDING",
    "2007": "APPLICATION_SECURITY_FINDING",
    # Identity & Access Management
    "3001": "ACCOUNT_CHANGE",
    "3002": "AUTHENTICATION",
    "3003": "AUTHORIZE_SESSION",
    "3004": "ENTITY_MANAGEMENT",
    "3005": "USER_ACCESS",
    "3006": "GROUP_MANAGEMENT",
    # Network Activity
    "4001": "NETWORK_ACTIVITY",
    "4002": "HTTP_ACTIVITY",
    "4003": "DNS_ACTIVITY",
    "4004": "DHCP_ACTIVITY",
    "4005": "RDP_ACTIVITY",
    "4006": "SMB_ACTIVITY",
    "4007": "SSH_ACTIVITY",
    "4008": "FTP_ACTIVITY",
    "4009": "EMAIL_ACTIVITY",
    "4013": "NTP_ACTIVITY",
    "4014": "TUNNEL_ACTIVITY",
    # Discovery
    "5001": "DEVICE_INVENTORY",
    "5002": "DEVICE_CONFIG_STATE",
    "5003": "USER_INVENTORY",
    "5004": "OS_PATCH_STATE",
    # Application Activity
    "6001": "WEB_RESOURCES",
    "6002": "APPLICATION_LIFECYCLE",
    "6003": "API_ACTIVITY",
    "6005": "DATASTORE_ACTIVITY",
    "6006": "FILE_HOSTING",
    "6007": "SCAN_ACTIVITY",
    "6008": "APPLICATION_ERROR",
    # Remediation
    "7001": "REMEDIATION",
    "7002": "FILE_REMEDIATION",
    "7003": "PROCESS_REMEDIATION",
    # Windows Extension
    "201001": "REGISTRY_KEY_ACTIVITY",
    "201002": "REGISTRY_VALUE_ACTIVITY",
    "201003": "WINDOWS_RESOURCE_ACTIVITY",
    "201004": "WINDOWS_SERVICE_ACTIVITY",
}


def get_current_account_id(session: boto3.Session) -> str | None:
    """Get the current AWS account ID."""
    try:
        sts = session.client("sts")
        response = sts.get_caller_identity()
        return response["Account"]
    except (ClientError, NoCredentialsError):
        return None
    except TokenRetrievalError:
        print("✗ AWS SSO token has expired")
        print("  Please refresh your SSO session:")
        print("  aws sso login --profile <your-profile>")
        return None


def verify_glue_role(session: boto3.Session, role_arn: str) -> bool:
    """Verify that the Glue IAM role exists."""
    try:
        iam = session.client("iam")
        role_name = role_arn.split("/")[-1]
        iam.get_role(RoleName=role_name)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchEntity":
            return False
        # For other errors (e.g., access denied), assume role might exist
        return True
    except TokenRetrievalError:
        print("✗ AWS SSO token has expired")
        print("  Please refresh your SSO session:")
        print("  aws sso login --profile <your-profile>")
        raise


def create_glue_role(session: boto3.Session, role_name: str, account_id: str) -> str | None:
    """Create the Glue service role for Security Lake."""
    try:
        iam = session.client("iam")

        # Create trust policy for Glue
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "glue.amazonaws.com"},
                    "Action": "sts:AssumeRole",
                }
            ],
        }

        # Create the role
        print(f"→ Creating IAM role: {role_name}")
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Glue service role for Amazon Security Lake custom sources",
        )
        role_arn = response["Role"]["Arn"]
        print(f"✔︎ Created role: {role_arn}")

        # Attach AWS managed policy for Glue
        print("→ Attaching AWSGlueServiceRole policy...")
        iam.attach_role_policy(
            RoleName=role_name, PolicyArn="arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
        )
        print("✔︎ Attached AWSGlueServiceRole policy")

        # Also attach Lake Formation permissions
        print("→ Attaching Lake Formation permissions...")
        lakeformation_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["lakeformation:GetDataAccess", "lakeformation:GrantPermissions"],
                    "Resource": "*",
                }
            ],
        }

        lf_policy_name = f"SecurityLakeLakeFormationAccess-{role_name}"
        try:
            lf_policy_response = iam.create_policy(
                PolicyName=lf_policy_name,
                PolicyDocument=json.dumps(lakeformation_policy),
                Description="Lake Formation access for Security Lake Glue crawlers",
            )
            lf_policy_arn = lf_policy_response["Policy"]["Arn"]
            iam.attach_role_policy(RoleName=role_name, PolicyArn=lf_policy_arn)
            print("✔︎ Attached Lake Formation permissions")
        except ClientError as e:
            if e.response["Error"]["Code"] == "EntityAlreadyExists":
                # Policy already exists, try to attach it
                lf_policy_arn = f"arn:aws:iam::{account_id}:policy/{lf_policy_name}"
                try:
                    iam.attach_role_policy(RoleName=role_name, PolicyArn=lf_policy_arn)
                    print("✔︎ Attached existing Lake Formation policy")
                except ClientError:
                    print("⚠ Could not attach Lake Formation policy")

        # Create and attach S3 policy for Security Lake buckets
        print("→ Creating S3 access policy for Security Lake...")
        s3_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["s3:GetObject", "s3:ListBucket", "s3:PutObject", "s3:DeleteObject"],
                    "Resource": [
                        "arn:aws:s3:::aws-security-data-lake-*",
                        "arn:aws:s3:::aws-security-data-lake-*/*",
                    ],
                }
            ],
        }

        policy_name = f"SecurityLakeGlueS3Access-{role_name}"

        try:
            policy_response = iam.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(s3_policy),
                Description="S3 access for Security Lake Glue crawlers",
            )
            policy_arn = policy_response["Policy"]["Arn"]
            print(f"✔︎ Created S3 access policy: {policy_name}")

            # Attach the S3 policy to the role
            iam.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
            print("✔︎ Attached S3 access policy")

        except ClientError as e:
            if e.response["Error"]["Code"] == "EntityAlreadyExists":
                # Policy already exists, try to attach it
                policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"
                print(f"ℹ S3 policy already exists, attaching: {policy_name}")
                try:
                    iam.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
                    print("✔︎ Attached existing S3 access policy")
                except ClientError:
                    print("⚠ Could not attach S3 policy, continuing anyway")
            else:
                print(f"⚠ Could not create S3 policy: {e.response['Error']['Message']}")

        print(f"\n✔︎ Glue role ready: {role_arn}")

        # Wait a moment for role propagation
        print("ℹ Waiting for role propagation...")
        time.sleep(5)

        return role_arn

    except ClientError as e:
        print(f"✗ Failed to create role: {e.response['Error']['Message']}")
        return None


def create_custom_source(
    class_uid: str,
    region: str,
    account_id: str,
    external_id: str,
    glue_role_arn: str,
    session: boto3.Session,
) -> bool:
    """Create a Security Lake custom source."""

    if class_uid not in OCSF_EVENT_CLASSES:
        print(f"✗ Error: Unknown OCSF class UID: {class_uid}")
        print(f"ℹ Valid class UIDs: {', '.join(sorted(OCSF_EVENT_CLASSES.keys()))}")
        return False

    event_class = OCSF_EVENT_CLASSES[class_uid]
    source_name = f"tnz-ocsf-{class_uid}"

    print(f"→ Creating custom source: {source_name} for event class: {event_class}")
    print(f"  Region: {region}")
    print(f"  Account ID: {account_id}")
    print(f"  Glue Role: {glue_role_arn}")
    print(f"  External ID: {external_id}")
    print()
    provider_role = f"AmazonSecurityLake-Provider-{source_name}-{region}"
    print(f"ℹ Note: Security Lake will create the provider role: {provider_role}")
    print()

    try:
        # Create Security Lake client
        security_lake = session.client("securitylake", region_name=region)

        # Create the custom log source
        response = security_lake.create_custom_log_source(
            sourceName=source_name,
            eventClasses=[event_class],
            configuration={
                "crawlerConfiguration": {"roleArn": glue_role_arn},
                "providerIdentity": {"principal": account_id, "externalId": external_id},
            },
        )

        print("✔︎ Successfully created custom source:", source_name)

        # Display the created source details
        if "source" in response:
            source = response["source"]
            print("\nCreated source details:")
            print(f"  Source name: {source.get('sourceName', 'N/A')}")
            print(f"  Source version: {source.get('sourceVersion', 'N/A')}")

            if "provider" in source:
                provider = source["provider"]
                print(f"  Provider role: {provider.get('roleArn', 'N/A')}")
                print(f"  S3 location: {provider.get('location', 'N/A')}")

            if "attributes" in source:
                attributes = source["attributes"]
                if "crawlerArn" in attributes:
                    print(f"  Crawler ARN: {attributes['crawlerArn']}")
                if "databaseArn" in attributes:
                    print(f"  Database ARN: {attributes['databaseArn']}")
                if "tableArn" in attributes:
                    print(f"  Table ARN: {attributes['tableArn']}")

        return True

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]

        print(f"✗ Failed to create custom source: {source_name}")
        print(f"  Error ({error_code}): {error_message}")

        # Provide specific guidance based on error
        print("\nℹ Possible solutions:")

        if error_code == "ResourceAlreadyExistsException":
            print("  • Source already exists with this name")
            print("  • Delete the existing source or use a different name")
        elif error_code == "AccessDeniedException":
            print("  • Check IAM permissions for securitylake:CreateCustomLogSource")
            print("  • Ensure you have permissions to pass the Glue role")
        elif error_code == "ResourceNotFoundException":
            print("  • Security Lake may not be enabled in this region")
            print("  • The specified Glue role may not exist")
        elif error_code == "ValidationException":
            print("  • Check that the Glue role ARN is valid")
            print("  • Ensure the external ID meets requirements")
        elif error_code == "BadRequestException" and "role" in error_message.lower():
            print(f"  • The Glue role does not exist: {glue_role_arn}")
            print("  • Create the role first with appropriate permissions:")
            print("    - Trust relationship with glue.amazonaws.com")
            print("    - AWSGlueServiceRole managed policy")
            print("    - S3 access to Security Lake buckets")
            print("  • Or specify an existing role with --glue-role-arn")
        else:
            print("  • Check AWS credentials and permissions")
            print(f"  • Ensure Security Lake is enabled in region: {region}")

        return False

    except NoCredentialsError:
        print("✗ Error: No AWS credentials found")
        print("  Configure credentials using:")
        print("  • aws configure")
        print("  • Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)")
        print("  • IAM role (if running on EC2)")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(
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

    parser.add_argument(
        "class_uid", nargs="?", help="OCSF class UID (e.g., 1001 for File System Activity)"
    )

    parser.add_argument("--region", default="us-east-1", help="AWS region (default: us-east-1)")

    parser.add_argument("--account-id", help="AWS account ID (default: auto-detected using boto3)")

    parser.add_argument(
        "--external-id",
        required=False,
        help="External ID for trust relationship (required unless --list is used)",
    )

    parser.add_argument(
        "--glue-role-arn", help="ARN of the Glue service role (default: auto-generated)"
    )

    parser.add_argument("--profile", help="AWS profile to use")

    parser.add_argument(
        "--list", action="store_true", help="List all available OCSF class UIDs and exit"
    )

    parser.add_argument(
        "--skip-role-check", action="store_true", help="Skip verification that the Glue role exists"
    )

    parser.add_argument(
        "--no-create-role",
        action="store_true",
        help="Do not automatically create the Glue role if it doesn't exist",
    )

    args = parser.parse_args()

    # Handle --list option
    if args.list:
        print("Available OCSF class UIDs:\n")
        categories = [
            (
                "System Activity",
                ["1001", "1002", "1003", "1004", "1005", "1006", "1007", "1008", "1009"],
            ),
            ("Findings", ["2001", "2002", "2003", "2004", "2005", "2006", "2007"]),
            ("Identity & Access Management", ["3001", "3002", "3003", "3004", "3005", "3006"]),
            (
                "Network Activity",
                [
                    "4001",
                    "4002",
                    "4003",
                    "4004",
                    "4005",
                    "4006",
                    "4007",
                    "4008",
                    "4009",
                    "4013",
                    "4014",
                ],
            ),
            ("Discovery", ["5001", "5002", "5003", "5004"]),
            ("Application Activity", ["6001", "6002", "6003", "6005", "6006", "6007", "6008"]),
            ("Remediation", ["7001", "7002", "7003"]),
            ("Windows Extension", ["201001", "201002", "201003", "201004"]),
        ]

        for category, uids in categories:
            print(f"{category}:")
            for uid in uids:
                print(f"  {uid}: {OCSF_EVENT_CLASSES[uid]}")
            print()

        return 0

    # Validate required arguments
    if not args.class_uid:
        parser.error("class_uid is required unless --list is used")

    if not args.external_id:
        parser.error("--external-id is required")

    # Create boto3 session
    session_kwargs = {}
    if args.profile:
        session_kwargs["profile_name"] = args.profile

    session = boto3.Session(**session_kwargs)

    # Auto-detect account ID if not provided
    account_id = args.account_id
    if not account_id:
        account_id = get_current_account_id(session)
        if not account_id:
            print("✗ Error: Could not auto-detect AWS account ID")
            print("  Please provide --account-id or configure AWS credentials")
            return 1
        print(f"ℹ Auto-detected account ID: {account_id}")

    # Default Glue role ARN if not provided
    glue_role_arn = args.glue_role_arn
    if not glue_role_arn:
        glue_role_arn = f"arn:aws:iam::{account_id}:role/AWSGlueServiceRole-SecurityLake"

    # Verify the Glue role exists (unless skipped)
    if not args.skip_role_check:
        print(f"ℹ Checking Glue role: {glue_role_arn}")
        if not verify_glue_role(session, glue_role_arn):
            role_name = glue_role_arn.split("/")[-1]

            if args.no_create_role:
                print(f"✗ Error: The Glue role does not exist: {glue_role_arn}")
                print("\nTo create the role, you need:")
                print("  1. An IAM role with trust relationship for glue.amazonaws.com")
                print("  2. The AWSGlueServiceRole managed policy attached")
                print("  3. A policy for S3 access to Security Lake buckets")
                print("\nAlternatively:")
                print("  • Remove --no-create-role to create it automatically")
                print("  • Specify an existing role with --glue-role-arn")
                print("  • Skip this check with --skip-role-check")
                return 1
            else:
                print("ℹ Glue role does not exist, creating it automatically...")
                created_role_arn = create_glue_role(session, role_name, account_id)
                if not created_role_arn:
                    print("\n✗ Failed to create Glue role")
                    print("  You may need additional IAM permissions to create roles")
                    print("  Try specifying an existing role with --glue-role-arn")
                    return 1
                glue_role_arn = created_role_arn
                print()  # Add spacing after role creation
        else:
            print("✔︎ Glue role verified\n")

    # Create the custom source
    success = create_custom_source(
        args.class_uid, args.region, account_id, args.external_id, glue_role_arn, session
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
