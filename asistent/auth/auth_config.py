"""
This module configures the authentication for Google API toolsets.
"""

import logging
from google.adk.tools.google_api_tool import CalendarToolset, DocsToolset, GmailToolset, GoogleApiToolset
from ..secrets import get_secret

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom DriveToolset implementation
class DriveToolset(GoogleApiToolset):
    """
    Custom toolset for Google Drive API v3.
    Provides access to Drive operations like files.copy.
    """
    def __init__(
        self,
        client_id: str = None,
        client_secret: str = None,
        tool_filter: list = None,
        service_account = None,
        tool_name_prefix: str = None,
    ):
        super().__init__(
            "drive",
            "v3",
            client_id,
            client_secret,
            tool_filter,
            service_account,
            tool_name_prefix,
        )

# Define desired tools for each toolset
GMAIL_TOOLS = [
    "gmail_users_messages_send",
    "gmail_users_drafts_create",
    "gmail_users_drafts_send",
]

DOCS_TOOLS = [
    "docs_documents_create",
    "docs_documents_get",
    "docs_documents_batch_update",
]

CALENDAR_TOOLS = [
    "calendar_events_insert",
    "calendar_events_list",
    "calendar_events_get",
    "calendar_events_patch",
    "calendar_events_delete",
]

DRIVE_TOOLS = [
    "drive_files_copy",
    "drive_files_get",
]

# Create instances of the toolsets with tool_filter parameter
calendar_tool_set = CalendarToolset(tool_filter=CALENDAR_TOOLS)
docs_tool_set = DocsToolset(tool_filter=DOCS_TOOLS)
gmail_tool_set = GmailToolset(tool_filter=GMAIL_TOOLS)
drive_tool_set = DriveToolset(tool_filter=DRIVE_TOOLS)

# Get OAuth credentials from Secret Manager
CLIENT_ID = get_secret("google-client-id")
CLIENT_SECRET = get_secret("google-client-secret")

if CLIENT_ID and CLIENT_SECRET:
    logger.info("Configuring Google API toolsets...")

    # Configure Calendar toolset
    calendar_tool_set.configure_auth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )

    # Configure Docs toolset
    docs_tool_set.configure_auth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )

    # Configure Gmail toolset
    gmail_tool_set.configure_auth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )

    # Configure Drive toolset
    drive_tool_set.configure_auth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )

    logger.info("Google API toolsets configured successfully.")
else:
    logger.warning("OAuth credentials not found in Secret Manager. Google API toolsets will not be available.")