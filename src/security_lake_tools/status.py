#!/usr/bin/env python3
"""
Show the current Security Lake setup status.

This module provides functions to query the Security Lake API and display
the current configuration including data lakes, log sources, subscribers,
and any exceptions.
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError, TokenRetrievalError
except ImportError:
    print("Error: boto3 is required. Install it with: pip install boto3")
    sys.exit(1)

if TYPE_CHECKING:
    from mypy_boto3_securitylake.type_defs import (
        DataLakeExceptionTypeDef,
        DataLakeResourceTypeDef,
        LogSourceTypeDef,
        SubscriberResourceTypeDef,
    )


def get_data_lakes(session: boto3.Session, region: str) -> "list[DataLakeResourceTypeDef] | None":
    """Get all data lakes in the account."""
    try:
        client = session.client("securitylake", region_name=region)
        response = client.list_data_lakes()
        return response.get("dataLakes", [])
    except ClientError as e:
        print(f"✗ Failed to list data lakes: {e.response['Error']['Message']}")
        return None
    except TokenRetrievalError:
        print("✗ AWS SSO token has expired")
        print("  Please refresh your SSO session:")
        print("  aws sso login --profile <your-profile>")
        return None


def get_data_lake_exceptions(
    session: boto3.Session, region: str
) -> "list[DataLakeExceptionTypeDef] | None":
    """Get all data lake exceptions."""
    try:
        client = session.client("securitylake", region_name=region)
        exceptions: list[DataLakeExceptionTypeDef] = []
        paginator = client.get_paginator("list_data_lake_exceptions")
        for page in paginator.paginate():
            exceptions.extend(page.get("exceptions", []))
        return exceptions
    except ClientError as e:
        print(f"✗ Failed to list data lake exceptions: {e.response['Error']['Message']}")
        return None
    except TokenRetrievalError:
        print("✗ AWS SSO token has expired")
        print("  Please refresh your SSO session:")
        print("  aws sso login --profile <your-profile>")
        return None


def get_log_sources(session: boto3.Session, region: str) -> "list[LogSourceTypeDef] | None":
    """Get all log sources."""
    try:
        client = session.client("securitylake", region_name=region)
        sources: list[LogSourceTypeDef] = []
        paginator = client.get_paginator("list_log_sources")
        for page in paginator.paginate():
            sources.extend(page.get("sources", []))
        return sources
    except ClientError as e:
        print(f"✗ Failed to list log sources: {e.response['Error']['Message']}")
        return None
    except TokenRetrievalError:
        print("✗ AWS SSO token has expired")
        print("  Please refresh your SSO session:")
        print("  aws sso login --profile <your-profile>")
        return None


def get_subscribers(
    session: boto3.Session, region: str
) -> "list[SubscriberResourceTypeDef] | None":
    """Get all subscribers."""
    try:
        client = session.client("securitylake", region_name=region)
        subscribers: list[SubscriberResourceTypeDef] = []
        paginator = client.get_paginator("list_subscribers")
        for page in paginator.paginate():
            subscribers.extend(page.get("subscribers", []))
        return subscribers
    except ClientError as e:
        print(f"✗ Failed to list subscribers: {e.response['Error']['Message']}")
        return None
    except TokenRetrievalError:
        print("✗ AWS SSO token has expired")
        print("  Please refresh your SSO session:")
        print("  aws sso login --profile <your-profile>")
        return None


def print_data_lakes(data_lakes: "list[DataLakeResourceTypeDef]") -> None:
    """Print data lake information."""
    print("Data Lakes")
    print("=" * 60)
    if not data_lakes:
        print("  No data lakes configured")
    else:
        for lake in data_lakes:
            print(f"  Region: {lake.get('region', 'N/A')}")
            print(f"  ARN: {lake.get('dataLakeArn', 'N/A')}")
            print(f"  S3 Bucket: {lake.get('s3BucketArn', 'N/A')}")
            if "encryptionConfiguration" in lake:
                enc = lake["encryptionConfiguration"]
                print(f"  Encryption KMS Key: {enc.get('kmsKeyId', 'default')}")
            if "lifecycleConfiguration" in lake:
                lifecycle = lake["lifecycleConfiguration"]
                if "expiration" in lifecycle:
                    print(f"  Expiration: {lifecycle['expiration'].get('days', 'N/A')} days")
                if "transitions" in lifecycle:
                    for t in lifecycle["transitions"]:
                        print(f"  Transition to {t.get('storageClass', 'N/A')}: {t.get('days', 'N/A')} days")
            if "replicationConfiguration" in lake:
                repl = lake["replicationConfiguration"]
                if repl.get("regions"):
                    print(f"  Replication Regions: {', '.join(repl['regions'])}")
                if repl.get("roleArn"):
                    print(f"  Replication Role: {repl['roleArn']}")
            status = lake.get("createStatus", "N/A")
            print(f"  Status: {status}")
            if lake.get("updateStatus"):
                update = lake["updateStatus"]
                print(f"  Update Status: {update.get('status', 'N/A')}")
                if update.get("exception"):
                    print(f"  Update Exception: {update['exception'].get('reason', 'N/A')}")
            print()
    print()


def print_exceptions(exceptions: "list[DataLakeExceptionTypeDef]") -> None:
    """Print data lake exceptions from the last 7 days."""
    print("Data Lake Exceptions (last 7 days)")
    print("=" * 60)
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    recent = [exc for exc in exceptions if exc.get("timestamp", cutoff) >= cutoff]
    if not recent:
        print("  No recent exceptions")
    else:
        for exc in recent:
            print(f"  Region: {exc.get('region', 'N/A')}")
            print(f"  Exception: {exc.get('exception', 'N/A')}")
            if exc.get("remediation"):
                print(f"  Remediation: {exc['remediation']}")
            if exc.get("timestamp"):
                print(f"  Timestamp: {exc['timestamp']}")
            print()
    print()


def print_log_sources(sources: "list[LogSourceTypeDef]") -> None:
    """Print log source information."""
    print("Log Sources")
    print("=" * 60)
    if not sources:
        print("  No log sources configured")
    else:
        for source in sources:
            account = source.get("account", "N/A")
            region = source.get("region", "N/A")
            print(f"  Account: {account}, Region: {region}")
            if "sources" in source:
                for src in source["sources"]:
                    if "awsLogSource" in src:
                        aws_src = src["awsLogSource"]
                        print(f"    AWS Source: {aws_src.get('sourceName', 'N/A')}")
                        print(f"      Version: {aws_src.get('sourceVersion', 'N/A')}")
                    if "customLogSource" in src:
                        custom_src = src["customLogSource"]
                        print(f"    Custom Source: {custom_src.get('sourceName', 'N/A')}")
                        print(f"      Version: {custom_src.get('sourceVersion', 'N/A')}")
                        if custom_src.get("provider"):
                            provider = custom_src["provider"]
                            print(f"      Location: {provider.get('location', 'N/A')}")
                            print(f"      Role ARN: {provider.get('roleArn', 'N/A')}")
                        if custom_src.get("attributes"):
                            attrs = custom_src["attributes"]
                            if attrs.get("databaseArn"):
                                # arn:aws:glue:region:account:database/name
                                db_name = attrs["databaseArn"].split("/")[-1]
                                print(f"      Glue Database: {db_name}")
                            if attrs.get("tableArn"):
                                # arn:aws:glue:region:account:table/db/name
                                table_name = attrs["tableArn"].split("/")[-1]
                                print(f"      Glue Table: {table_name}")
            print()
    print()


def print_subscribers(subscribers: "list[SubscriberResourceTypeDef]") -> None:
    """Print subscriber information."""
    print("Subscribers")
    print("=" * 60)
    if not subscribers:
        print("  No subscribers configured")
    else:
        for sub in subscribers:
            print(f"  Name: {sub.get('subscriberName', 'N/A')}")
            print(f"  ID: {sub.get('subscriberId', 'N/A')}")
            print(f"  ARN: {sub.get('subscriberArn', 'N/A')}")
            print(f"  Status: {sub.get('subscriberStatus', 'N/A')}")
            if sub.get("subscriberDescription"):
                print(f"  Description: {sub['subscriberDescription']}")
            if sub.get("subscriberIdentity"):
                identity = sub["subscriberIdentity"]
                print(f"  Principal: {identity.get('principal', 'N/A')}")
                print(f"  External ID: {identity.get('externalId', 'N/A')}")
            if sub.get("accessTypes"):
                print(f"  Access Types: {', '.join(sub['accessTypes'])}")
            if sub.get("sources"):
                print("  Sources:")
                for src in sub["sources"]:
                    if "awsLogSource" in src:
                        aws_src = src["awsLogSource"]
                        print(f"    - AWS: {aws_src.get('sourceName', 'N/A')}")
                    if "customLogSource" in src:
                        custom_src = src["customLogSource"]
                        print(f"    - Custom: {custom_src.get('sourceName', 'N/A')}")
            if sub.get("resourceShareArn"):
                print(f"  Resource Share: {sub['resourceShareArn']}")
            if sub.get("s3BucketArn"):
                print(f"  S3 Bucket: {sub['s3BucketArn']}")
            if sub.get("subscriberEndpoint"):
                print(f"  Endpoint: {sub['subscriberEndpoint']}")
            print()
    print()


def show_status(region: str, session: boto3.Session) -> int:
    """Show the Security Lake status."""
    print(f"\nSecurity Lake Status (Region: {region})\n")

    # Get all information
    data_lakes = get_data_lakes(session, region)
    if data_lakes is None:
        return 1

    exceptions = get_data_lake_exceptions(session, region)
    if exceptions is None:
        return 1

    sources = get_log_sources(session, region)
    if sources is None:
        return 1

    subscribers = get_subscribers(session, region)
    if subscribers is None:
        return 1

    # Print everything
    print_data_lakes(data_lakes)
    print_exceptions(exceptions)
    print_log_sources(sources)
    print_subscribers(subscribers)

    return 0


def main() -> int:
    """Main entry point for status command."""
    parser = argparse.ArgumentParser(
        description="Show the current Security Lake setup status",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--region", help="AWS region (default: from profile or AWS_DEFAULT_REGION)"
    )
    parser.add_argument("--profile", help="AWS profile to use")

    args = parser.parse_args()

    # Create boto3 session
    try:
        session = boto3.Session(profile_name=args.profile)
    except NoCredentialsError:
        print("✗ Error: No AWS credentials found")
        print("  Configure credentials using:")
        print("  • aws configure")
        print("  • Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)")
        print("  • IAM role (if running on EC2)")
        return 1

    # Determine region: CLI arg > session/profile > fallback
    region = args.region or session.region_name
    if not region:
        print("✗ Error: No AWS region specified")
        print("  Provide a region using one of:")
        print("  • --region flag")
        print("  • AWS_DEFAULT_REGION environment variable")
        print("  • region setting in your AWS profile")
        return 1

    return show_status(region, session)


if __name__ == "__main__":
    sys.exit(main())
