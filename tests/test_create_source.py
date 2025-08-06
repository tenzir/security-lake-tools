"""Tests for the create_source module."""

from unittest.mock import Mock, patch

from botocore.exceptions import ClientError

from security_lake_tools.create_source import (
    OCSF_EVENT_CLASSES,
    create_custom_source,
    create_glue_role,
    verify_glue_role,
)


class TestOCSFEventClasses:
    """Test OCSF event class mappings."""

    def test_event_classes_exist(self):
        """Test that OCSF event classes are defined."""
        assert len(OCSF_EVENT_CLASSES) > 0

    def test_specific_event_classes(self):
        """Test specific known event classes."""
        assert OCSF_EVENT_CLASSES["1001"] == "FILE_ACTIVITY"
        assert OCSF_EVENT_CLASSES["2001"] == "SECURITY_FINDING"
        assert OCSF_EVENT_CLASSES["3001"] == "ACCOUNT_CHANGE"
        assert OCSF_EVENT_CLASSES["4001"] == "NETWORK_ACTIVITY"


class TestVerifyGlueRole:
    """Test Glue role verification."""

    @patch("security_lake_tools.create_source.boto3.Session")
    def test_role_exists(self, mock_session):
        """Test when role exists."""
        mock_iam = Mock()
        mock_iam.get_role.return_value = {"Role": {"RoleName": "test-role"}}
        mock_session.return_value.client.return_value = mock_iam

        session = mock_session()
        result = verify_glue_role(session, "arn:aws:iam::123456789012:role/test-role")

        assert result is True
        mock_iam.get_role.assert_called_once_with(RoleName="test-role")

    @patch("security_lake_tools.create_source.boto3.Session")
    def test_role_not_exists(self, mock_session):
        """Test when role doesn't exist."""
        mock_iam = Mock()
        mock_iam.get_role.side_effect = ClientError({"Error": {"Code": "NoSuchEntity"}}, "GetRole")
        mock_session.return_value.client.return_value = mock_iam

        session = mock_session()
        result = verify_glue_role(session, "arn:aws:iam::123456789012:role/test-role")

        assert result is False


class TestCreateGlueRole:
    """Test Glue role creation."""

    @patch("security_lake_tools.create_source.boto3.Session")
    def test_successful_creation(self, mock_session):
        """Test successful role creation."""
        mock_iam = Mock()
        mock_iam.create_role.return_value = {
            "Role": {"Arn": "arn:aws:iam::123456789012:role/test-role"}
        }
        mock_iam.create_policy.return_value = {
            "Policy": {"Arn": "arn:aws:iam::123456789012:policy/test-policy"}
        }
        mock_session.return_value.client.return_value = mock_iam

        session = mock_session()
        result = create_glue_role(session, "test-role", "123456789012")

        assert result == "arn:aws:iam::123456789012:role/test-role"
        assert mock_iam.create_role.called
        assert mock_iam.attach_role_policy.called


class TestCreateCustomSource:
    """Test custom source creation."""

    @patch("security_lake_tools.create_source.boto3.Session")
    def test_invalid_class_uid(self, mock_session):
        """Test with invalid OCSF class UID."""
        session = mock_session()
        result = create_custom_source(
            "9999",  # Invalid UID
            "us-east-1",
            "123456789012",
            "test-external-id",
            "arn:aws:iam::123456789012:role/test-role",
            session,
        )

        assert result is False

    @patch("security_lake_tools.create_source.boto3.Session")
    def test_successful_creation(self, mock_session):
        """Test successful source creation."""
        mock_client = Mock()
        mock_client.create_custom_log_source.return_value = {
            "source": {
                "sourceName": "tnz-ocsf-1001",
                "provider": {
                    "roleArn": "arn:aws:iam::123456789012:role/Provider",
                    "location": "s3://bucket/path/",
                },
            }
        }
        mock_session.return_value.client.return_value = mock_client

        session = mock_session()
        result = create_custom_source(
            "1001",
            "us-east-1",
            "123456789012",
            "test-external-id",
            "arn:aws:iam::123456789012:role/test-role",
            session,
        )

        assert result is True
        assert mock_client.create_custom_log_source.called
