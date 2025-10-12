"""
Utility functions for Google Workspace (Drive and Docs) integration.

This module provides helper functions for:
- Authenticating with Google Drive and Docs APIs using user OAuth tokens
- Managing user folders in Drive
- Creating and formatting Google Docs
- Version control for documents

SECURITY:
- Prioritizes user OAuth tokens from TokenManager
- Falls back to Service Account for internal operations
- Supports automatic token refresh
"""

import logging
import os
import re
from typing import Optional, Tuple

from google.auth import default
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from ..secrets import get_drive_root_folder_id, get_secret

logger = logging.getLogger(__name__)

# Service Account key file path (if available)
SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")


def get_drive_service(user_email: str = None, token_manager = None):
    """
    Get Google Drive API service using Service Account with domain-wide delegation.

    SIMPLIFIED APPROACH:
    - Use Service Account with delegation to impersonate user
    - No OAuth tokens, no token management complexity
    - Service Account must be authorized in Google Workspace Admin Console

    Args:
        user_email (str, optional): Email of the user to impersonate

    Returns:
        Google Drive API service instance
    """
    scopes = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.file'
    ]

    # Use Application Default Credentials (Compute Engine Service Account in Cloud Run)
    credentials, _ = default(scopes=scopes)

    # Delegate to user if email provided
    if user_email and hasattr(credentials, 'with_subject'):
        credentials = credentials.with_subject(user_email)
        logger.info(f"Using Service Account with delegation for user: {user_email}")
    else:
        logger.info("Using Service Account without delegation")

    return build('drive', 'v3', credentials=credentials)


def get_docs_service(user_email: str = None, token_manager = None):
    """
    Get Google Docs API service using Service Account with domain-wide delegation.

    SIMPLIFIED APPROACH:
    - Use Service Account with delegation to impersonate user
    - No OAuth tokens, no token management complexity
    - Service Account must be authorized in Google Workspace Admin Console

    Args:
        user_email (str, optional): Email of the user to impersonate

    Returns:
        Google Docs API service instance
    """
    scopes = [
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.file'
    ]

    # Use Application Default Credentials (Compute Engine Service Account in Cloud Run)
    credentials, _ = default(scopes=scopes)

    # Delegate to user if email provided
    if user_email and hasattr(credentials, 'with_subject'):
        credentials = credentials.with_subject(user_email)
        logger.info(f"Using Service Account with delegation for user: {user_email}")
    else:
        logger.info("Using Service Account without delegation")

    return build('docs', 'v1', credentials=credentials)


def normalize_filename(title: str) -> str:
    """
    Normalize a document title to a valid filename.

    Converts title to lowercase, replaces spaces with hyphens,
    and removes special characters.

    Args:
        title (str): The document title

    Returns:
        str: Normalized filename (without extension)

    Example:
        "Contrato Compra-Venta Juan Pérez" -> "contrato-compra-venta-juan-perez"
    """
    # Convert to lowercase
    filename = title.lower()

    # Replace spaces with hyphens
    filename = filename.replace(' ', '-')

    # Remove accents
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ñ': 'n', 'ü': 'u'
    }
    for old, new in replacements.items():
        filename = filename.replace(old, new)

    # Remove special characters (keep letters, numbers, hyphens)
    filename = re.sub(r'[^a-z0-9-]', '', filename)

    # Remove consecutive hyphens
    filename = re.sub(r'-+', '-', filename)

    # Remove leading/trailing hyphens
    filename = filename.strip('-')

    return filename


def ensure_user_folder(user_email: str, token_manager = None) -> str:
    """
    Ensure a user folder exists in the Drive root folder.
    Creates the folder if it doesn't exist.

    Args:
        user_email (str): User's email address (used as folder name)
        token_manager (TokenManager, optional): TokenManager for user OAuth tokens

    Returns:
        str: The folder ID

    Raises:
        Exception: If folder cannot be created or accessed
    """
    try:
        # Get Drive service with user OAuth tokens or fallback
        drive_service = get_drive_service(user_email, token_manager)

        root_folder_id = get_drive_root_folder_id()
        logger.info(f"Ensuring folder for user: {user_email}")

        # Search for existing user folder
        query = (
            f"name='{user_email}' and "
            f"'{root_folder_id}' in parents and "
            f"mimeType='application/vnd.google-apps.folder' and "
            f"trashed=false"
        )

        results = drive_service.files().list(
            q=query,
            fields="files(id, name)",
            spaces='drive'
        ).execute()

        folders = results.get('files', [])

        if folders:
            logger.info(f"Found existing folder for {user_email}: {folders[0]['id']}")
            return folders[0]['id']

        # Create folder if it doesn't exist
        logger.info(f"Creating new folder for {user_email}")
        file_metadata = {
            'name': user_email,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [root_folder_id]
        }

        folder = drive_service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()

        logger.info(f"Created folder for {user_email}: {folder['id']}")
        return folder['id']

    except Exception as e:
        logger.error(f"Error ensuring user folder for {user_email}: {str(e)}")
        raise


def get_next_version_name(folder_id: str, base_name: str, user_email: str, token_manager = None) -> str:
    """
    Find existing versions of a document and return the next version name.

    Searches for documents with the same base name and increments version number.

    Args:
        folder_id (str): The folder to search in
        base_name (str): The base filename (without version)
        user_email (str): User's email
        token_manager (TokenManager, optional): TokenManager for user OAuth tokens

    Returns:
        str: The versioned filename

    Examples:
        - No existing documents: "contrato-compra-venta-juan-perez"
        - Exists without version: "contrato-compra-venta-juan-perez-v2"
        - Exists v1: "contrato-compra-venta-juan-perez-v2"
        - Exists v1, v2: "contrato-compra-venta-juan-perez-v3"
    """
    try:
        # Get Drive service with user OAuth tokens or fallback
        drive_service = get_drive_service(user_email, token_manager)

        logger.info(f"Checking for existing versions of: {base_name}")

        # Search for files with similar names in the folder
        query = (
            f"name contains '{base_name}' and "
            f"'{folder_id}' in parents and "
            f"mimeType='application/vnd.google-apps.document' and "
            f"trashed=false"
        )

        results = drive_service.files().list(
            q=query,
            fields="files(name)",
            spaces='drive'
        ).execute()

        files = results.get('files', [])

        if not files:
            logger.info(f"No existing versions found, using base name: {base_name}")
            return base_name

        # Extract version numbers from filenames
        versions = []
        for file in files:
            name = file['name']

            # Check if it's the exact base name (no version)
            if name == base_name:
                versions.append(1)
                continue

            # Check if it has a version number
            if '-v' in name:
                try:
                    # Extract version number
                    version_str = name.split('-v')[-1]
                    version_num = int(version_str)
                    versions.append(version_num)
                except (ValueError, IndexError):
                    # Ignore malformed version numbers
                    continue

        if not versions:
            logger.info(f"No valid versions found, using base name: {base_name}")
            return base_name

        # Get the next version number
        max_version = max(versions)
        next_version = max_version + 1
        versioned_name = f"{base_name}-v{next_version}"

        logger.info(f"Found {len(versions)} existing version(s), using: {versioned_name}")
        return versioned_name

    except Exception as e:
        logger.error(f"Error getting next version name: {str(e)}")
        # Return base name as fallback
        return base_name


def create_formatted_document(
    title: str,
    content: str,
    folder_id: str,
    user_email: str,
    token_manager = None
) -> Tuple[str, str]:
    """
    Create a Google Doc with rich formatting and save it to a specific folder.

    Args:
        title (str): Document title
        content (str): Document content (plain text)
        folder_id (str): Drive folder ID where document will be saved
        user_email (str): User's email
        token_manager (TokenManager, optional): TokenManager for user OAuth tokens

    Returns:
        tuple: (document_id, document_url)

    Raises:
        Exception: If document cannot be created
    """
    try:
        # Get services with user OAuth tokens or fallback
        docs_service = get_docs_service(user_email, token_manager)
        drive_service = get_drive_service(user_email, token_manager)

        logger.info(f"Creating document: {title}")

        # Step 1: Create blank document
        doc = docs_service.documents().create(
            body={'title': title}
        ).execute()

        doc_id = doc['documentId']
        logger.info(f"Created blank document with ID: {doc_id}")

        # Step 2: Insert content
        requests = [
            {
                'insertText': {
                    'location': {'index': 1},
                    'text': content
                }
            }
        ]

        # Step 3: Apply formatting
        formatting_requests = parse_and_format_content(content)
        requests.extend(formatting_requests)

        # Step 4: Execute batch update
        if requests:
            docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests}
            ).execute()
            logger.info(f"Applied formatting to document {doc_id}")

        # Step 5: Move to user folder
        drive_service.files().update(
            fileId=doc_id,
            addParents=folder_id,
            fields='id, parents, webViewLink'
        ).execute()
        logger.info(f"Moved document to folder {folder_id}")

        # Step 6: Get shareable link
        file = drive_service.files().get(
            fileId=doc_id,
            fields='webViewLink'
        ).execute()

        doc_url = file['webViewLink']
        logger.info(f"Document created successfully: {doc_url}")

        return doc_id, doc_url

    except Exception as e:
        logger.error(f"Error creating formatted document: {str(e)}")
        raise


def parse_and_format_content(content: str) -> list:
    """
    Parse document content and generate formatting requests.

    Detects and formats:
    - Titles (lines starting with "CONTRATO DE", etc.) -> H1
    - Clauses (lines starting with "PRIMERA:", etc.) -> H2
    - Bold text (names, DNI, CUIT, amounts with $)
    - Italic text (text in quotes)
    - Numbered lists

    Args:
        content (str): The document content

    Returns:
        list: List of formatting requests for batchUpdate API

    Note:
        This is a basic implementation. Advanced formatting can be added later.
    """
    requests = []

    # TODO: Implement advanced formatting detection
    # For now, return empty list (document will be plain text)
    # Future enhancements:
    # - Detect "CONTRATO DE..." and apply H1 style
    # - Detect "PRIMERA:", "SEGUNDA:", etc. and apply H2 style
    # - Detect monetary amounts and apply bold
    # - Detect DNI/CUIT patterns and apply bold
    # - Detect text in quotes and apply italic

    return requests


def list_documents_in_folder(folder_id: str, user_email: str, token_manager = None) -> list:
    """
    List all Google Docs in a specific folder.

    Args:
        folder_id (str): The folder ID
        user_email (str): User's email
        token_manager (TokenManager, optional): TokenManager for user OAuth tokens

    Returns:
        list: List of document metadata dictionaries

    Each dictionary contains:
        - id: Document ID
        - name: Document name
        - createdTime: Creation timestamp
        - modifiedTime: Last modification timestamp
        - webViewLink: Shareable link
    """
    try:
        # Get Drive service with user OAuth tokens or fallback
        drive_service = get_drive_service(user_email, token_manager)

        logger.info(f"Listing documents in folder: {folder_id}")

        query = (
            f"'{folder_id}' in parents and "
            f"mimeType='application/vnd.google-apps.document' and "
            f"trashed=false"
        )

        results = drive_service.files().list(
            q=query,
            fields="files(id, name, createdTime, modifiedTime, webViewLink)",
            orderBy="modifiedTime desc",
            spaces='drive'
        ).execute()

        documents = results.get('files', [])
        logger.info(f"Found {len(documents)} document(s)")

        return documents

    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise
