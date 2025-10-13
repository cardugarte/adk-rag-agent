"""
RAG Tools package for interacting with Vertex AI RAG corpora.

This package now contains both administrative tools (for corpus management)
and operational tools (for day-to-day agent functionality).
"""

# Import from admin and operational subpackages
from .admin import *
from .operational import *
from .utils import (
    check_corpus_exists,
    get_corpus_resource_name,
    set_current_corpus,
)

# Make utils available at package level
__all__ = [
    "check_corpus_exists",
    "get_corpus_resource_name",
    "set_current_corpus",
]