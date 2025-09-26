# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Language and Communication Guidelines

**IMPORTANT - Language Rules:**

- **Communication with user**: Always respond in Spanish (from Argentina)
- **Code writing**: Always write code, comments, docstrings, variable names, and function names in English
- **Git commits**: Always write commit messages in English following conventional commit format
- **Documentation**: Write technical documentation in English, but explain it to the user in Spanish when asked

**Examples:**

- ✅ Code: `def create_specialized_corpus(corpus_type: str):`
- ✅ Commit: `feat: implement intelligent document detection`
- ✅ User communication: "He implementado la funcionalidad de detección automática..."
- ❌ Code in Spanish: `def crear_corpus_especializado(tipo_corpus: str):`
- ❌ Commit in Spanish: `feat: implementar detección inteligente`

## Project Overview

This is a Google Agent Development Kit (ADK) implementation of a RAG (Retrieval Augmented Generation) agent specialized in legal contract analysis using Google Cloud Vertex AI. The agent is designed to evolve into a comprehensive legal automation suite with:

- **Multi-corpus architecture** for specialized document types
- **Intelligent contract generation** with legal validation
- **Google Workspace integration** (Docs, Gmail, Calendar)
- **Automated communication workflows**
- **Advanced legal analysis** and compliance checking

### Vision

Transform from a basic RAG agent into a complete legal assistant capable of drafting contracts, detecting inconsistencies, managing document workflows, and automating client communications while ensuring compliance with Argentine legal standards.

### Current Status

**Phase 1 Foundation** - Multi-corpus architecture and smart analysis capabilities are in active development.

## Commands

### Development Environment Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Authentication Setup

```bash
# Initialize Google Cloud CLI
gcloud init

# Set up application default credentials
gcloud auth application-default login

# Enable required APIs
gcloud services enable aiplatform.googleapis.com
```

### Environment Configuration

Create `.env` file in the `asistent/` directory with:

```env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=your-location
```

## Code Architecture

### Multi-Corpus Architecture

The system is designed around **6 specialized corpus types** for optimal legal document processing:

1. **certificaciones** - Templates and examples of legal certifications
2. **compra_venta** - Real estate and personal property sale contracts
3. **locacion** - Urban and commercial lease agreements
4. **poderes** - Powers of attorney (general, special, revocations)
5. **reglamento_ph** - Condominium regulations and administration
6. **marco_legal** - Legal framework (Civil Code, laws, jurisprudence)

Each corpus has specialized configurations for chunk size, overlap, and embedding parameters optimized for its document type.

### Core Components

1. **Main Agent (`asistent/agent.py`)**
   - Uses Google ADK Agent framework
   - Configured with Gemini 2.5 Flash model
   - Specialized for legal contract analysis in Spanish (Argentina)
   - Maintains internal consistency checking

2. **Package Initialization (`asistent/__init__.py`)**
   - Handles Vertex AI initialization at package load
   - Loads environment variables from `.env`
   - Imports and exposes the main agent

3. **Configuration (`asistent/config.py`)**
   - Centralized settings for RAG operations
   - Default values for chunk size, overlap, embedding model
   - Multi-corpus specific configurations
   - Project and location configuration

4. **Current Tools Directory (`asistent/tools/`)**
   - `rag_query.py`: Query documents in corpora
   - `list_corpora.py`: List available document corpora
   - `create_corpus.py`: Create new corpora
   - `add_data.py`: Add documents to corpora
   - `get_corpus_info.py`: Get detailed corpus information
   - `delete_document.py`: Delete specific documents
   - `delete_corpus.py`: Delete entire corpora
   - `utils.py`: Shared utility functions for corpus management

### Planned Architecture Extensions

Future tools will be organized in specialized modules:

```text
asistent/tools/
├── analysis/
│   ├── template_analyzer.py
│   ├── consistency_checker.py
│   ├── document_comparator.py
│   └── risk_assessor.py
├── generation/
│   ├── contract_generator.py
│   ├── template_manager.py
│   └── clause_recommender.py
├── integrations/
│   ├── google_docs_creator.py
│   ├── gmail_sender.py
│   └── calendar_manager.py
├── validation/
│   ├── legal_compliance.py
│   ├── cross_corpus_query.py
│   └── corpus_manager.py
└── intelligence/
    ├── learning_engine.py
    └── analytics_reporter.py
```

### State Management

- Uses ADK ToolContext for maintaining agent state
- Tracks "current corpus" for operations
- Caches corpus existence checks
- Manages resource name resolution

### Key Design Patterns

- All tools use the same utilities for corpus name resolution
- Full Vertex AI resource names are used internally but hidden from users
- Confirmation required for destructive operations (delete_document, delete_corpus)
- Error handling with appropriate user feedback

## Dependencies

### Current Dependencies

Main dependencies from `requirements.txt`:

- `google-adk`: Google Agent Development Kit
- `google-generativeai`: Gemini model access
- `google-cloud-aiplatform`: Vertex AI integration
- `google-cloud-storage`: GCS file handling
- `google-genai`: Additional Google AI utilities
- `python-dotenv`: Environment variable management
- `git-python`: Git integration

### Planned Additional Dependencies

For the full roadmap implementation:

**Google Workspace Integration:**

- `google-api-python-client`: Google APIs client
- `google-auth-oauthlib`: OAuth authentication
- `google-auth-httplib2`: HTTP transport for Google APIs

**Document Processing & Templates:**

- `python-docx`: Word document manipulation
- `jinja2`: Template engine for contract generation
- `pdfplumber`: PDF text extraction

**Data Processing & Analysis:**

- `pandas`: Data analysis and manipulation
- `scikit-learn`: Machine learning utilities
- `spacy`: Natural language processing
- `regex`: Advanced pattern matching

**Argentine-specific Validations:**

- `validate-docbr`: Document validation utilities
- Custom validators for CUIT/DNI/addresses

## Project Commands

### GitHub Project Management

```bash
# View project status
gh project view 10 --owner cardugarte

# Add issue to project
gh project item-add 10 --owner cardugarte --url <issue-url>
```

### Development Workflow

```bash
# Start working on an issue
gh issue develop <issue-number> --repo cardugarte/adk-rag-agent

# Run tests for specific corpus
python -m pytest tests/corpus/test_<corpus_type>.py

# Run full test suite
python -m pytest tests/
```

### Multi-Corpus Operations

```bash
# Initialize all corpus types
python -c "from asistent.tools.corpus_manager import initialize_all_corpus; initialize_all_corpus()"

# Test cross-corpus functionality
python scripts/test_cross_corpus.py
```

## Authentication Requirements

- Google Cloud account with billing enabled
- Vertex AI API enabled in the project
- Application Default Credentials configured
- Appropriate IAM permissions for Vertex AI resources

## Development Roadmap & GitHub Project

### GitHub Project

**URL**: <https://github.com/users/cardugarte/projects/10>
**Title**: Agente Legal Inteligente - RAG Development

The project contains 8 detailed issues organized across 5 epics with clear dependencies and acceptance criteria.

### Development Phases

#### Phase 1: Foundation - Multi-Corpus & Analysis (High Priority)

- **Issue #1**: Corpus Manager - Foundation for multi-corpus architecture
- **Issue #4**: Template Analyzer - Automatic contract type detection
- **Issue #5**: Enhanced Consistency Checker - Argentine legal validations

#### Phase 2: Smart Generation & Validation (High Priority)

- **Issue #2**: Cross-Corpus Query System - Intelligent multi-corpus searches
- **Issue #3**: Legal Compliance Checker - Automated legal validation
- **Issue #8**: Smart Contract Generator - Automated contract generation

#### Phase 3: Workspace Integration (Medium Priority)

- **Issue #6**: Google Docs Auto-Creator - Document generation integration

#### Phase 4: Communication Automation (Medium Priority)

- **Issue #7**: Email Automation System - Automated client communications

### Implementation Order

1. **Corpus Manager** (Foundation - enables all other features)
2. **Template Analyzer** (Can be developed in parallel with #1)
3. **Cross-Corpus Query System** (Depends on Corpus Manager)
4. **Enhanced Consistency Checker** (Depends on Template Analyzer)
5. **Legal Compliance Checker** (Depends on #1, #2)
6. **Smart Contract Generator** (Depends on #1-#5)

### Issue Labels Organization

- **Epics**: `epic:multi-corpus`, `epic:smart-analysis`, `epic:workspace-integration`, `epic:communication`, `epic:advanced-ai`
- **Corpus Types**: `corpus:certificaciones`, `corpus:compra-venta`, `corpus:locacion`, `corpus:poderes`, `corpus:reglamento-ph`, `corpus:marco-legal`
- **Priority**: `priority:high`, `priority:medium`, `priority:low`
- **Type**: `type:foundation`, `type:feature`

### Key Dependencies

- All corpus-related features depend on Issue #1 (Corpus Manager)
- Advanced analysis features depend on Template Analyzer
- Integration features require foundation to be complete
- Each issue has detailed acceptance criteria and story point estimates
- does not include co-authorship mentions or third-party advertising (e.g., Claude Code).
