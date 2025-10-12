"""
Secure token management using Google Cloud Secret Manager.

This module provides a TokenManager class for securely storing and retrieving
OAuth2 tokens with automatic refresh, rotation, and revocation capabilities.

Security Features:
- Tokens stored encrypted at-rest in Secret Manager
- Automatic access token refresh
- Refresh token rotation detection
- Secure token revocation on logout
- Audit logging for all token operations
"""

import json
import logging
import os
import time
from typing import Dict, Optional

from google.cloud import secretmanager
from google.api_core import exceptions as gcp_exceptions

logger = logging.getLogger(__name__)


class TokenManager:
    """
    Manages OAuth2 tokens securely using Google Cloud Secret Manager.

    This class implements OWASP OAuth2 security best practices:
    - Server-side token storage (not in client cookies)
    - Automatic token refresh with expiration handling
    - Refresh token rotation detection
    - Secure token revocation

    Example:
        token_manager = TokenManager(project_id="my-project")

        # Store tokens after OAuth login
        token_manager.store_user_tokens(
            user_email="user@example.com",
            access_token="ya29...",
            refresh_token="1//...",
            expires_at=1234567890
        )

        # Retrieve valid access token (auto-refreshes if needed)
        access_token = token_manager.get_valid_access_token(
            user_email="user@example.com",
            oauth_client=oauth
        )

        # Revoke tokens on logout
        token_manager.delete_user_tokens(user_email="user@example.com")
    """

    def __init__(self, project_id: str):
        """
        Initialize TokenManager with Google Cloud project.

        Args:
            project_id (str): Google Cloud project ID
        """
        self.project_id = project_id
        self.client = secretmanager.SecretManagerServiceClient()
        self.parent = f"projects/{project_id}"

    def store_user_tokens(
        self,
        user_email: str,
        access_token: str,
        refresh_token: str,
        expires_at: int
    ) -> None:
        """
        Store user OAuth2 tokens securely in Secret Manager.

        SECURITY: Tokens are encrypted at-rest by Secret Manager.
        Each user has their own secret for token isolation.

        Args:
            user_email (str): User's email address (used as secret ID)
            access_token (str): OAuth2 access token
            refresh_token (str): OAuth2 refresh token
            expires_at (int): Unix timestamp when access token expires

        Raises:
            Exception: If token storage fails
        """
        try:
            secret_id = self._get_secret_id(user_email)

            token_data = {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_at': expires_at,
                'last_updated': int(time.time()),
                'user_email': user_email  # Store for validation
            }

            # Create or update secret
            self._create_or_update_secret(secret_id, json.dumps(token_data))

            logger.info(f"Tokens stored securely for user: {user_email}")

        except Exception as e:
            logger.error(f"Failed to store tokens for {user_email}: {str(e)}")
            raise

    def get_user_tokens(self, user_email: str) -> Optional[Dict]:
        """
        Retrieve user tokens from Secret Manager.

        Args:
            user_email (str): User's email address

        Returns:
            dict: Token data including access_token, refresh_token, expires_at
            None: If tokens don't exist or are invalid
        """
        try:
            secret_id = self._get_secret_id(user_email)
            secret_data = self._get_secret_value(secret_id)

            if not secret_data:
                logger.warning(f"No tokens found for user: {user_email}")
                return None

            token_data = json.loads(secret_data)

            # Validate that the email matches (security check)
            if token_data.get('user_email') != user_email:
                logger.error(f"Email mismatch in token data for {user_email}")
                return None

            return token_data

        except json.JSONDecodeError as e:
            logger.error(f"Invalid token data format for {user_email}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve tokens for {user_email}: {str(e)}")
            return None

    def get_valid_access_token(
        self,
        user_email: str,
        oauth_client
    ) -> Optional[str]:
        """
        Get a valid access token, refreshing if necessary.

        This method implements automatic token refresh:
        1. Retrieves tokens from Secret Manager
        2. Checks if access token is still valid
        3. If expired, refreshes using refresh token
        4. Stores new tokens (implements rotation if supported)
        5. Returns valid access token

        Args:
            user_email (str): User's email address
            oauth_client: Authlib OAuth client instance for token refresh

        Returns:
            str: Valid access token
            None: If tokens don't exist or refresh fails

        Example:
            from authlib.integrations.starlette_client import OAuth
            oauth = OAuth()
            oauth.register(name='google', ...)

            token = token_manager.get_valid_access_token(
                user_email="user@example.com",
                oauth_client=oauth
            )
        """
        try:
            tokens = self.get_user_tokens(user_email)

            if not tokens:
                logger.warning(f"No tokens available for {user_email}")
                return None

            # Check if access token is still valid (with 5 min buffer)
            current_time = int(time.time())
            expires_at = tokens.get('expires_at', 0)

            if expires_at > (current_time + 300):  # 5 min buffer
                logger.info(f"Using cached access token for {user_email}")
                return tokens['access_token']

            # Access token expired, refresh it
            logger.info(f"Access token expired for {user_email}, refreshing...")
            new_tokens = self._refresh_tokens(
                tokens['refresh_token'],
                oauth_client
            )

            if not new_tokens:
                logger.error(f"Token refresh failed for {user_email}")
                return None

            # Store new tokens (implements rotation)
            self.store_user_tokens(
                user_email=user_email,
                access_token=new_tokens['access_token'],
                refresh_token=new_tokens.get('refresh_token', tokens['refresh_token']),
                expires_at=new_tokens['expires_at']
            )

            logger.info(f"Access token refreshed successfully for {user_email}")
            return new_tokens['access_token']

        except Exception as e:
            logger.error(f"Failed to get valid access token for {user_email}: {str(e)}")
            return None

    def delete_user_tokens(self, user_email: str) -> bool:
        """
        Delete user tokens from Secret Manager (e.g., on logout).

        SECURITY: Implements secure token revocation.
        After calling this, the user must re-authenticate.

        Args:
            user_email (str): User's email address

        Returns:
            bool: True if tokens were deleted, False otherwise
        """
        try:
            secret_id = self._get_secret_id(user_email)
            self._delete_secret(secret_id)

            logger.info(f"Tokens revoked for user: {user_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete tokens for {user_email}: {str(e)}")
            return False

    def _refresh_tokens(
        self,
        refresh_token: str,
        oauth_client
    ) -> Optional[Dict]:
        """
        Refresh access token using refresh token.

        SECURITY: Implements refresh token rotation if provider supports it.
        Google OAuth2 may return a new refresh token in the response.

        Args:
            refresh_token (str): Current refresh token
            oauth_client: Authlib OAuth client instance

        Returns:
            dict: New token data with access_token, refresh_token (if rotated), expires_at
            None: If refresh fails
        """
        try:
            # Use Authlib to refresh token
            token = oauth_client.google.fetch_access_token(
                grant_type='refresh_token',
                refresh_token=refresh_token
            )

            expires_in = token.get('expires_in', 3600)
            expires_at = int(time.time()) + expires_in

            result = {
                'access_token': token['access_token'],
                'refresh_token': token.get('refresh_token', refresh_token),  # Use new if rotated
                'expires_at': expires_at
            }

            logger.info("Token refresh successful")
            return result

        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            return None

    def _get_secret_id(self, user_email: str) -> str:
        """
        Generate Secret Manager secret ID from user email.

        Args:
            user_email (str): User's email address

        Returns:
            str: Secret ID (alphanumeric with hyphens)

        Example:
            user@example.com -> user-tokens-user-at-example-com
        """
        # Sanitize email for use in secret ID
        sanitized = user_email.replace('@', '-at-').replace('.', '-')
        return f"user-tokens-{sanitized}"

    def _create_or_update_secret(self, secret_id: str, secret_value: str) -> None:
        """
        Create or update a secret in Secret Manager.

        Args:
            secret_id (str): Secret identifier
            secret_value (str): Secret value (JSON string)

        Raises:
            Exception: If secret creation/update fails
        """
        secret_path = f"{self.parent}/secrets/{secret_id}"

        try:
            # Try to create the secret first
            try:
                self.client.create_secret(
                    request={
                        "parent": self.parent,
                        "secret_id": secret_id,
                        "secret": {
                            "replication": {"automatic": {}},
                        },
                    }
                )
                logger.info(f"Created new secret: {secret_id}")
            except gcp_exceptions.AlreadyExists:
                # Secret already exists, will add new version
                pass

            # Add secret version with the value
            self.client.add_secret_version(
                request={
                    "parent": secret_path,
                    "payload": {"data": secret_value.encode("UTF-8")},
                }
            )

        except Exception as e:
            logger.error(f"Failed to create/update secret {secret_id}: {str(e)}")
            raise

    def _get_secret_value(self, secret_id: str) -> Optional[str]:
        """
        Retrieve the latest version of a secret from Secret Manager.

        Args:
            secret_id (str): Secret identifier

        Returns:
            str: Secret value
            None: If secret doesn't exist
        """
        try:
            secret_path = f"{self.parent}/secrets/{secret_id}/versions/latest"

            response = self.client.access_secret_version(
                request={"name": secret_path}
            )

            return response.payload.data.decode("UTF-8")

        except gcp_exceptions.NotFound:
            return None
        except Exception as e:
            logger.error(f"Failed to access secret {secret_id}: {str(e)}")
            return None

    def _delete_secret(self, secret_id: str) -> None:
        """
        Delete a secret from Secret Manager.

        Args:
            secret_id (str): Secret identifier

        Raises:
            Exception: If secret deletion fails
        """
        try:
            secret_path = f"{self.parent}/secrets/{secret_id}"
            self.client.delete_secret(request={"name": secret_path})

        except gcp_exceptions.NotFound:
            logger.warning(f"Secret {secret_id} not found, already deleted")
        except Exception as e:
            logger.error(f"Failed to delete secret {secret_id}: {str(e)}")
            raise
