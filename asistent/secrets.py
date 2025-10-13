"""
Secret Manager integration for secure configuration management.

This module provides functions to retrieve secrets from Google Cloud Secret Manager
instead of using environment variables or .env files for sensitive data.
"""

import json
import logging
import os

from google.cloud import secretmanager

logger = logging.getLogger(__name__)

# Project ID from environment (one of the 3 allowed env vars)
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")


def get_secret(secret_id, version_id="latest"):
    """
    Get a secret from Google Secret Manager.

    Args:
        secret_id (str): The ID of the secret to retrieve
        version_id (str): The version of the secret (default: "latest")

    Returns:
        str: The secret value as a string, or None if error
    """
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set.")

    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

    try:
        response = client.access_secret_version(name=name)
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Error accessing secret {secret_id}: {e}")
        return None


def get_drive_root_folder_id() -> str:
    """
    Get the Google Drive root folder ID from Secret Manager.

    This is the ID of the folder where user subfolders will be created.
    Supports both full URLs and raw folder IDs.

    Returns:
        str: The Drive folder ID

    Example:
        Input: "https://drive.google.com/drive/folders/1_svAhVFlBqzc2f-_eNzOY9o8jbjO3OhX"
        Output: "1_svAhVFlBqzc2f-_eNzOY9o8jbjO3OhX"

        Input: "1_svAhVFlBqzc2f-_eNzOY9o8jbjO3OhX"
        Output: "1_svAhVFlBqzc2f-_eNzOY9o8jbjO3OhX"
    """
    folder_value = get_secret("drive-root-folder-id")

    if not folder_value:
        return None

    # If it's a URL, extract the folder ID
    if folder_value.startswith("http"):
        # Extract ID from URL like: https://drive.google.com/drive/folders/FOLDER_ID
        parts = folder_value.rstrip("/").split("/")
        return parts[-1]

    # Otherwise return as-is (already a folder ID)
    return folder_value


def get_allowed_users() -> list:
    """
    Get the list of allowed users from Secret Manager.

    Returns:
        list: List of allowed user email addresses
    """
    try:
        users_json = get_secret("allowed-users")
        if users_json:
            return json.loads(users_json)
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing allowed-users JSON: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Error getting allowed users: {str(e)}")
        return []


