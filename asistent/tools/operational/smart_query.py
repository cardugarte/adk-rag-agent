"""
Smart query tool for intelligent corpus selection and querying.

This tool automatically detects the appropriate corpus type based on the query
content and provides intelligent multi-corpus search capabilities.
"""

import logging
import re
from typing import Dict, List, Optional, Union

from google.adk.tools.tool_context import ToolContext
from vertexai import rag

from ...config import (
    CORPUS_CONFIGS,
    CORPUS_TYPE_KEYWORDS,
    CORPUS_TYPES,
    DEFAULT_DISTANCE_THRESHOLD,
    DEFAULT_TOP_K,
)
from ..utils import check_corpus_exists, get_corpus_resource_name
from .rag_query import rag_query

logger = logging.getLogger(__name__)


def smart_query(
    query: str,
    tool_context: ToolContext,
    document_type: Optional[str] = None,
) -> dict:
    """
    Intelligently query corpora by auto-detecting the appropriate corpus type.

    Args:
        query (str): The text query to search for
        document_type (Optional[str]): Force a specific document type. If None, auto-detect.
        tool_context (ToolContext): The tool context for state management

    Returns:
        dict: Query results with intelligence metadata
    """
    try:
        # Detect document type if not specified
        if document_type is None:
            detected_type = detect_document_type(query, tool_context)
            if detected_type["status"] == "success":
                document_type = detected_type["detected_type"]
            else:
                # If detection fails, try marco_legal as fallback
                document_type = "marco_legal"

        # Validate document type
        if document_type not in CORPUS_TYPES:
            return {
                "status": "error",
                "message": f"Invalid document type '{document_type}'. Must be one of: {', '.join(CORPUS_TYPES)}",
                "query": query,
                "document_type": document_type,
            }

        # Find appropriate corpus for the document type
        corpus_name = _find_corpus_for_type(document_type, tool_context)

        if not corpus_name:
            return {
                "status": "warning",
                "message": f"No corpus found for document type '{document_type}'. Please create one using corpus_manager.",
                "query": query,
                "document_type": document_type,
                "suggestion": f"Use create_specialized_corpus('{document_type}', 'default') to create a corpus for this type.",
            }

        # Perform the query using the intelligent selection
        result = rag_query(corpus_name, query, tool_context)

        # Add intelligence metadata
        result["intelligence"] = {
            "auto_detected_type": document_type,
            "corpus_used": corpus_name,
            "config_used": CORPUS_CONFIGS.get(document_type, {}),
        }

        return result

    except Exception as e:
        logger.error(f"Error in smart query: {str(e)}")
        return {
            "status": "error",
            "message": f"Error in smart query: {str(e)}",
            "query": query,
            "document_type": document_type,
        }


def cross_corpus_query(
    query: str,
    tool_context: ToolContext,
    corpus_types: Optional[List[str]] = None,
) -> dict:
    """
    Query multiple corpora and aggregate results.

    Args:
        query (str): The text query to search for
        corpus_types (Optional[List[str]]): List of corpus types to search. If None, use all available.
        tool_context (ToolContext): The tool context for state management

    Returns:
        dict: Aggregated results from multiple corpora
    """
    try:
        # If no corpus types specified, detect relevant ones
        if corpus_types is None:
            detection_result = detect_document_type(query, tool_context)
            if detection_result["status"] == "success":
                # Primary type + marco_legal for validation
                corpus_types = [detection_result["detected_type"], "marco_legal"]
            else:
                # Use all available types
                corpus_types = CORPUS_TYPES.copy()

        # Validate corpus types
        invalid_types = [ct for ct in corpus_types if ct not in CORPUS_TYPES]
        if invalid_types:
            return {
                "status": "error",
                "message": f"Invalid corpus types: {', '.join(invalid_types)}. Must be one of: {', '.join(CORPUS_TYPES)}",
                "query": query,
                "corpus_types": corpus_types,
            }

        results_by_type = {}
        total_results = 0
        successful_queries = 0

        for corpus_type in corpus_types:
            corpus_name = _find_corpus_for_type(corpus_type, tool_context)

            if not corpus_name:
                results_by_type[corpus_type] = {
                    "status": "warning",
                    "message": f"No corpus found for type '{corpus_type}'",
                    "results": [],
                    "results_count": 0,
                }
                continue

            # Query this corpus
            result = rag_query(corpus_name, query, tool_context)
            results_by_type[corpus_type] = result

            if result["status"] == "success":
                successful_queries += 1
                total_results += result.get("results_count", 0)

        return {
            "status": "success" if successful_queries > 0 else "warning",
            "message": f"Queried {len(corpus_types)} corpus types, {successful_queries} successful",
            "query": query,
            "corpus_types": corpus_types,
            "results_by_type": results_by_type,
            "total_results": total_results,
            "successful_queries": successful_queries,
        }

    except Exception as e:
        logger.error(f"Error in cross corpus query: {str(e)}")
        return {
            "status": "error",
            "message": f"Error in cross corpus query: {str(e)}",
            "query": query,
            "corpus_types": corpus_types,
        }


def detect_document_type(text: str, tool_context: ToolContext) -> dict:
    """
    Detect the document type based on text content using keyword analysis.

    Args:
        text (str): Text to analyze for document type detection
        tool_context (ToolContext): The tool context for state management

    Returns:
        dict: Detection result with confidence scores
    """
    try:
        if not text or not isinstance(text, str):
            return {
                "status": "error",
                "message": "Invalid text input for document type detection",
                "text": text,
            }

        text_lower = text.lower()
        type_scores = {}

        # Calculate scores for each corpus type based on keyword matches
        for corpus_type, keywords in CORPUS_TYPE_KEYWORDS.items():
            score = 0
            matched_keywords = []

            for keyword in keywords:
                keyword_lower = keyword.lower()
                # Count occurrences of this keyword
                matches = len(re.findall(re.escape(keyword_lower), text_lower))
                if matches > 0:
                    score += matches
                    matched_keywords.append(keyword)

            if score > 0:
                type_scores[corpus_type] = {
                    "score": score,
                    "matched_keywords": matched_keywords,
                    "config": CORPUS_CONFIGS[corpus_type],
                }

        # If no matches found
        if not type_scores:
            return {
                "status": "warning",
                "message": "Could not detect document type from text content",
                "text": text[:100] + "..." if len(text) > 100 else text,
                "detected_type": "marco_legal",  # Default fallback
                "confidence": 0.0,
                "all_scores": {},
            }

        # Find the type with highest score
        best_type = max(type_scores.keys(), key=lambda t: type_scores[t]["score"])
        best_score = type_scores[best_type]["score"]

        # Calculate confidence (basic scoring)
        total_score = sum(data["score"] for data in type_scores.values())
        confidence = best_score / total_score if total_score > 0 else 0.0

        return {
            "status": "success",
            "message": f"Detected document type '{best_type}' with {confidence:.1%} confidence",
            "text": text[:100] + "..." if len(text) > 100 else text,
            "detected_type": best_type,
            "confidence": confidence,
            "matched_keywords": type_scores[best_type]["matched_keywords"],
            "all_scores": type_scores,
        }

    except Exception as e:
        logger.error(f"Error in document type detection: {str(e)}")
        return {
            "status": "error",
            "message": f"Error in document type detection: {str(e)}",
            "text": text,
        }


def _find_corpus_for_type(corpus_type: str, tool_context: ToolContext) -> Optional[str]:
    """
    Find the first available corpus for the given type.

    Args:
        corpus_type (str): The corpus type to search for
        tool_context (ToolContext): The tool context for state management

    Returns:
        Optional[str]: The corpus name if found, None otherwise
    """
    try:
        # Get all corpora and find one that matches the type
        corpora = rag.list_corpora()

        for corpus in corpora:
            # Check if this corpus matches the desired type
            corpus_name = corpus.display_name
            detected_type = _detect_corpus_type_from_name(corpus_name)

            if detected_type == corpus_type:
                # Update state
                tool_context.state[f"corpus_exists_{corpus_name}"] = True
                tool_context.state[f"corpus_type_{corpus_name}"] = corpus_type
                return corpus_name

        return None

    except Exception as e:
        logger.warning(f"Error finding corpus for type {corpus_type}: {str(e)}")
        return None


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