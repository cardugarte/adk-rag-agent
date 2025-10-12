"""
Tool for saving approved legal contracts to Google Drive as formatted Google Docs.

SECURITY:
- Uses TokenManager to retrieve user's OAuth tokens from Secret Manager
- Tokens are never exposed in session/cookies
- Supports automatic token refresh
"""

import logging
import os

from google.adk.tools.tool_context import ToolContext

from .google_workspace_utils import (
    create_formatted_document,
    ensure_user_folder,
    get_docs_service,
    get_drive_service,
    get_next_version_name,
    normalize_filename,
)
from .token_manager import TokenManager

logger = logging.getLogger(__name__)


def save_document_to_drive(
    document_title: str,
    document_content: str,
    document_type: str,
    tool_context: ToolContext,
) -> dict:
    """
    Save an approved legal contract to Google Drive as a formatted Google Doc.

    This tool creates a new Google Doc with rich formatting and saves it to the
    user's personal folder in Drive. If a document with the same name already exists,
    a new version is created automatically (e.g., -v2, -v3).

    Args:
        document_title (str): Descriptive title for the document
            Example: "Contrato Compra-Venta Juan Pérez"
        document_content (str): Full contract text to be saved
        document_type (str): Type/category of contract
            Examples: "compra-venta", "locacion", "poder", "certificacion"
        tool_context (ToolContext): Tool context to access user session state

    Returns:
        dict: Status and document information
            - status (str): "success" or "error"
            - message (str): Descriptive message
            - document_id (str): Google Docs document ID (on success)
            - document_url (str): Shareable link to document (on success)
            - version (str): Version name of created document (on success)
            - folder (str): User's folder name (on success)

    Example:
        result = save_document_to_drive(
            document_title="Contrato Compra-Venta Juan Pérez",
            document_content="CONTRATO DE COMPRA-VENTA\\n\\nPRIMERA: ...",
            document_type="compra-venta",
            tool_context=context
        )

        # Returns:
        # {
        #     "status": "success",
        #     "message": "Documento guardado exitosamente como 'contrato-compra-venta-juan-perez-v2'",
        #     "document_id": "1abc...",
        #     "document_url": "https://docs.google.com/document/d/1abc.../edit",
        #     "version": "contrato-compra-venta-juan-perez-v2",
        #     "folder": "carlos@xplorers.ar"
        # }
    """
    try:
        # Step 1: Get user email from tool context state
        # The user_email is injected into session.state by our custom query endpoint
        # in run_web.py, which ensures it's always available for authenticated users
        user_email = tool_context.state.get("user_email")

        if not user_email:
            logger.error("User email not found in tool context state")
            logger.error(f"Available state keys: {list(tool_context.state.keys())}")
            return {
                "status": "error",
                "message": "Usuario no autenticado. Por favor, recarga la página e intenta nuevamente.",
            }

        logger.info(f"Saving document for user: {user_email}")
        logger.info(f"Document title: {document_title}")
        logger.info(f"Document type: {document_type}")

        # Step 2: Initialize TokenManager to retrieve user's OAuth tokens
        # SECURITY: Tokens are retrieved from Secret Manager, not from session/cookies
        token_manager = TokenManager(os.environ.get('GOOGLE_CLOUD_PROJECT'))

        # Step 3: Ensure user folder exists (create if needed)
        user_folder_id = ensure_user_folder(user_email, token_manager)

        # Step 4: Generate normalized base filename
        base_name = normalize_filename(document_title)

        # Step 5: Get next version name (handles versioning automatically)
        versioned_name = get_next_version_name(user_folder_id, base_name, user_email, token_manager)

        # Step 6: Create formatted Google Doc
        doc_id, doc_url = create_formatted_document(
            title=versioned_name,
            content=document_content,
            folder_id=user_folder_id,
            user_email=user_email,
            token_manager=token_manager
        )

        # Step 7: Store document info in context state (for potential future reference)
        if "saved_documents" not in tool_context.state:
            tool_context.state["saved_documents"] = []

        tool_context.state["saved_documents"].append(
            {
                "document_id": doc_id,
                "document_title": versioned_name,
                "document_type": document_type,
                "document_url": doc_url,
            }
        )

        logger.info(f"Document saved successfully: {versioned_name}")

        return {
            "status": "success",
            "message": f"Documento guardado exitosamente como '{versioned_name}'",
            "document_id": doc_id,
            "document_url": doc_url,
            "version": versioned_name,
            "folder": user_email,
        }

    except Exception as e:
        error_msg = f"Error al guardar documento: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "document_title": document_title,
            "document_type": document_type,
        }
