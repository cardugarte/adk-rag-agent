"""
Configuration settings for the RAG Agent.

These settings are used by the various RAG tools.
Vertex AI initialization is performed in the package's __init__.py
"""

import os

from dotenv import load_dotenv

# Load environment variables (this is redundant if __init__.py is imported first,
# but included for safety when importing config directly)
load_dotenv()

# Vertex AI settings
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION")

# RAG settings
DEFAULT_CHUNK_SIZE = 512
DEFAULT_CHUNK_OVERLAP = 100
DEFAULT_TOP_K = 3
DEFAULT_DISTANCE_THRESHOLD = 0.5
DEFAULT_EMBEDDING_MODEL = "publishers/google/models/text-embedding-005"
DEFAULT_EMBEDDING_REQUESTS_PER_MIN = 1000

# Multi-corpus configuration
CORPUS_TYPES = [
    "certificaciones",
    "compra_venta",
    "locacion",
    "poderes",
    "reglamento_ph",
    "marco_legal"
]

# Specialized configurations per corpus type
CORPUS_CONFIGS = {
    "certificaciones": {
        "chunk_size": 256,
        "chunk_overlap": 50,
        "description": "Templates y ejemplos de certificaciones legales",
        "embedding_model": DEFAULT_EMBEDDING_MODEL
    },
    "compra_venta": {
        "chunk_size": 512,
        "chunk_overlap": 100,
        "description": "Contratos inmobiliarios y de bienes muebles",
        "embedding_model": DEFAULT_EMBEDDING_MODEL
    },
    "locacion": {
        "chunk_size": 512,
        "chunk_overlap": 100,
        "description": "Contratos de locaciones urbanas y comerciales",
        "embedding_model": DEFAULT_EMBEDDING_MODEL
    },
    "poderes": {
        "chunk_size": 384,
        "chunk_overlap": 75,
        "description": "Poderes generales, especiales y revocatorias",
        "embedding_model": DEFAULT_EMBEDDING_MODEL
    },
    "reglamento_ph": {
        "chunk_size": 512,
        "chunk_overlap": 100,
        "description": "Reglamentos de copropiedad y administración",
        "embedding_model": DEFAULT_EMBEDDING_MODEL
    },
    "marco_legal": {
        "chunk_size": 1024,
        "chunk_overlap": 200,
        "description": "Base jurídica: códigos, leyes, jurisprudencia",
        "embedding_model": DEFAULT_EMBEDDING_MODEL
    }
}

# Document type detection keywords
CORPUS_TYPE_KEYWORDS = {
    "certificaciones": [
        "certifico", "certificación", "certificado", "fe de vida",
        "domicilio", "soltería", "nacimiento", "defunción"
    ],
    "compra_venta": [
        "compraventa", "venta", "compra", "vendedor", "comprador",
        "precio", "inmueble", "bien mueble", "transferencia"
    ],
    "locacion": [
        "locación", "alquiler", "arrendamiento", "locador", "locatario",
        "canon", "depósito", "garantía", "plazo"
    ],
    "poderes": [
        "poder", "apoderado", "mandante", "representación", "facultades",
        "revocatoria", "sustitución", "mandato"
    ],
    "reglamento_ph": [
        "consorcio", "propiedad horizontal", "administrador", "expensas",
        "reglamento", "unidad funcional", "partes comunes"
    ],
    "marco_legal": [
        "código civil", "ley", "artículo", "jurisprudencia", "decreto",
        "constitución", "normativa", "legal", "derecho"
    ]
}
