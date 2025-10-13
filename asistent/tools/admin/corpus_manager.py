"""
Corpus Manager for coordinated management of multiple specialized corpora.

This tool provides functionality to manage the 6 specialized corpus types:
- certificaciones: Legal certifications templates and examples
- compra_venta: Real estate and personal property sale contracts
- locacion: Urban and commercial lease agreements
- poderes: Powers of attorney (general, special, revocations)
- reglamento_ph: Condominium regulations and administration
- marco_legal: Legal framework (codes, laws, jurisprudence)
"""

import logging
from typing import Dict, List, Optional, Union

from google.adk.tools.tool_context import ToolContext
from vertexai import rag

from ...config import (
    CORPUS_CONFIGS,
    CORPUS_TYPES,
    DEFAULT_EMBEDDING_MODEL,
    LOCATION,
    PROJECT_ID,
)
from ..utils import check_corpus_exists, get_corpus_resource_name

logger = logging.getLogger(__name__)


def list_all_corpora(tool_context: ToolContext) -> dict:
    """
    List all available corpora grouped by corpus type.

    Args:
        tool_context (ToolContext): The tool context for state management

    Returns:
        dict: Status and corpora grouped by type
    """
    try:
        # Get all existing corpora
        corpora = rag.list_corpora()

        # Group corpora by type
        grouped_corpora = {corpus_type: [] for corpus_type in CORPUS_TYPES}
        unclassified_corpora = []

        for corpus in corpora:
            corpus_info = {
                "resource_name": corpus.name,
                "display_name": corpus.display_name,
                "create_time": str(corpus.create_time) if hasattr(corpus, "create_time") else "",
                "update_time": str(corpus.update_time) if hasattr(corpus, "update_time") else "",
            }

            # Determine corpus type based on display name
            corpus_type = _detect_corpus_type_from_name(corpus.display_name)
            if corpus_type:
                grouped_corpora[corpus_type].append(corpus_info)
            else:
                unclassified_corpora.append(corpus_info)

        # Update state with corpus existence info
        for corpus_type, corpus_list in grouped_corpora.items():
            for corpus in corpus_list:
                tool_context.state[f"corpus_exists_{corpus['display_name']}"] = True

        return {
            "status": "success",
            "message": f"Found corpora across {len(CORPUS_TYPES)} specialized types",
            "corpus_types": grouped_corpora,
            "unclassified": unclassified_corpora,
            "total_count": sum(len(corpus_list) for corpus_list in grouped_corpora.values()) + len(unclassified_corpora)
        }

    except Exception as e:
        logger.error(f"Error listing corpora by type: {str(e)}")
        return {
            "status": "error",
            "message": f"Error listing corpora by type: {str(e)}",
            "corpus_types": {},
            "unclassified": [],
            "total_count": 0
        }


def create_specialized_corpus(
    corpus_type: str,
    corpus_name: str,
    tool_context: ToolContext
) -> dict:
    """
    Create a new corpus with specialized configuration for the given type.

    Args:
        corpus_type (str): The type of corpus (must be one of CORPUS_TYPES)
        corpus_name (str): The name for the new corpus
        tool_context (ToolContext): The tool context for state management

    Returns:
        dict: Status information about the operation
    """
    # Validate corpus type
    if corpus_type not in CORPUS_TYPES:
        return {
            "status": "error",
            "message": f"Invalid corpus type '{corpus_type}'. Must be one of: {', '.join(CORPUS_TYPES)}",
            "corpus_name": corpus_name,
            "corpus_type": corpus_type,
            "corpus_created": False,
        }

    # Create full corpus name with type prefix
    full_corpus_name = f"{corpus_type}_{corpus_name}"

    # Check if corpus already exists
    if check_corpus_exists(full_corpus_name, tool_context):
        return {
            "status": "info",
            "message": f"Specialized corpus '{full_corpus_name}' already exists",
            "corpus_name": full_corpus_name,
            "corpus_type": corpus_type,
            "corpus_created": False,
        }

    try:
        # Get specialized configuration
        config = CORPUS_CONFIGS[corpus_type]

        # Configure embedding model with specialized settings
        embedding_model_config = rag.RagEmbeddingModelConfig(
            vertex_prediction_endpoint=rag.VertexPredictionEndpoint(
                publisher_model=config["embedding_model"]
            )
        )

        # Create the corpus with specialized configuration
        rag_corpus = rag.create_corpus(
            display_name=full_corpus_name,
            backend_config=rag.RagVectorDbConfig(
                rag_embedding_model_config=embedding_model_config,
                # Note: chunk_size and chunk_overlap are applied when adding documents
            ),
        )

        # Update state to track corpus existence and type
        tool_context.state[f"corpus_exists_{full_corpus_name}"] = True
        tool_context.state[f"corpus_type_{full_corpus_name}"] = corpus_type
        tool_context.state["current_corpus"] = full_corpus_name

        return {
            "status": "success",
            "message": f"Successfully created specialized corpus '{full_corpus_name}' of type '{corpus_type}'",
            "corpus_name": rag_corpus.name,
            "display_name": rag_corpus.display_name,
            "corpus_type": corpus_type,
            "corpus_created": True,
            "config_used": config,
        }

    except Exception as e:
        logger.error(f"Error creating specialized corpus: {str(e)}")
        return {
            "status": "error",
            "message": f"Error creating specialized corpus: {str(e)}",
            "corpus_name": full_corpus_name,
            "corpus_type": corpus_type,
            "corpus_created": False,
        }


def get_corpus_by_type(corpus_type: str, tool_context: ToolContext) -> dict:
    """
    Get all corpora of a specific type.

    Args:
        corpus_type (str): The type of corpus to search for
        tool_context (ToolContext): The tool context for state management

    Returns:
        dict: Status and list of corpora of the specified type
    """
    # Validate corpus type
    if corpus_type not in CORPUS_TYPES:
        return {
            "status": "error",
            "message": f"Invalid corpus type '{corpus_type}'. Must be one of: {', '.join(CORPUS_TYPES)}",
            "corpus_type": corpus_type,
            "corpora": [],
        }

    try:
        # Get all corpora and filter by type
        corpora = rag.list_corpora()
        type_corpora = []

        for corpus in corpora:
            # Check if corpus name indicates this type
            if _detect_corpus_type_from_name(corpus.display_name) == corpus_type:
                corpus_info = {
                    "resource_name": corpus.name,
                    "display_name": corpus.display_name,
                    "create_time": str(corpus.create_time) if hasattr(corpus, "create_time") else "",
                    "update_time": str(corpus.update_time) if hasattr(corpus, "update_time") else "",
                }
                type_corpora.append(corpus_info)

                # Update state
                tool_context.state[f"corpus_exists_{corpus.display_name}"] = True
                tool_context.state[f"corpus_type_{corpus.display_name}"] = corpus_type

        if not type_corpora:
            return {
                "status": "warning",
                "message": f"No corpora found of type '{corpus_type}'",
                "corpus_type": corpus_type,
                "corpora": [],
                "config": CORPUS_CONFIGS[corpus_type],
            }

        return {
            "status": "success",
            "message": f"Found {len(type_corpora)} corpora of type '{corpus_type}'",
            "corpus_type": corpus_type,
            "corpora": type_corpora,
            "config": CORPUS_CONFIGS[corpus_type],
        }

    except Exception as e:
        logger.error(f"Error getting corpora by type: {str(e)}")
        return {
            "status": "error",
            "message": f"Error getting corpora by type: {str(e)}",
            "corpus_type": corpus_type,
            "corpora": [],
        }


def initialize_corpus_types(tool_context: ToolContext) -> dict:
    """
    Initialize default corpora for all corpus types.
    Creates one corpus per type with default naming.

    Args:
        tool_context (ToolContext): The tool context for state management

    Returns:
        dict: Status of initialization process
    """
    results = []
    created_count = 0

    for corpus_type in CORPUS_TYPES:
        default_name = f"default"
        result = create_specialized_corpus(corpus_type, default_name, tool_context)

        if result["corpus_created"]:
            created_count += 1

        results.append({
            "corpus_type": corpus_type,
            "result": result,
        })

    return {
        "status": "success" if created_count > 0 else "info",
        "message": f"Initialization complete. Created {created_count} new corpora out of {len(CORPUS_TYPES)} types.",
        "created_count": created_count,
        "total_types": len(CORPUS_TYPES),
        "results": results,
    }


def _detect_corpus_type_from_name(corpus_name: str) -> Optional[str]:
    """
    Detect corpus type from corpus name.

    Args:
        corpus_name (str): The corpus display name

    Returns:
        Optional[str]: The detected corpus type, or None if not detectable
    """
    corpus_name_lower = corpus_name.lower()

    # Check if name starts with any corpus type
    for corpus_type in CORPUS_TYPES:
        if corpus_name_lower.startswith(f"{corpus_type}_"):
            return corpus_type

    # Check if name contains corpus type keywords
    for corpus_type in CORPUS_TYPES:
        if corpus_type in corpus_name_lower:
            return corpus_type

    return None