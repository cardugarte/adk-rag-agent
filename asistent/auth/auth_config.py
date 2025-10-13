"""
This module configures the authentication for Google API toolsets.
"""

import logging
from google.adk.tools.google_api_tool import CalendarToolset, DocsToolset, GmailToolset
from ..secrets import get_secret

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create instances of the toolsets
calendar_tool_set = CalendarToolset()
docs_tool_set = DocsToolset()
gmail_tool_set = GmailToolset()

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
    
    logger.info("Google API toolsets configured successfully.")
else:
    logger.warning("OAuth credentials not found in Secret Manager. Google API toolsets will not be available.")