"""
Operational tools for day-to-day agent functionality.

These tools are used by the agent during normal operation to query
documents, analyze contracts, and perform legal assistance tasks.
"""

from .rag_query import rag_query
from .smart_query import smart_query, cross_corpus_query, detect_document_type

__all__ = [
    "rag_query",
    "smart_query",
    "cross_corpus_query",
    "detect_document_type",
]