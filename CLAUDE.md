# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Google Agent Development Kit (ADK) implementation of a RAG (Retrieval Augmented Generation) agent specialized in legal contract analysis using Google Cloud Vertex AI. The agent uses **ADK native OAuth2 authentication** for Google Workspace integration and can be deployed to Vertex AI Agent Engine.

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
gcloud services enable secretmanager.googleapis.com
```

### Environment Configuration

Create `.env` file in the `asistent/` directory with:

```env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=your-location
GOOGLE_GENAI_USE_VERTEXAI=TRUE
```

### Local Testing

```bash
# Test agent locally with interactive OAuth flow
python client/agent_client.py

# Test DocsToolset workflow (NEW)
python test_docs_workflow.py

# Test specific functionality
python create_test_doc.py
python test_drive_permissions.py
```

### Deployment

```bash
# Deploy to Vertex AI Agent Engine
python deploy_agent_engine.py

# Test deployed agent
python test_deployed_agent.py
```

### Secret Management

```bash
# Store OAuth credentials in Secret Manager
echo -n "YOUR_CLIENT_ID" | gcloud secrets create google-client-id --data-file=-
echo -n "YOUR_CLIENT_SECRET" | gcloud secrets create google-client-secret --data-file=-

# Store Drive folder configuration
echo -n "DRIVE_FOLDER_ID" | gcloud secrets create drive-root-folder-id --data-file=-

# Store allowed users list (JSON array)
echo -n '["user1@example.com", "user2@example.com"]' | gcloud secrets create allowed-users --data-file=-
```

## Code Architecture

### Core Components

1. **Main Agent (`asistent/agent.py`)**
   - Uses Google ADK Agent framework
   - Configured with Gemini 2.5 Flash model
   - Specialized for legal contract analysis in Spanish (Argentina)
   - Implements both RAG and Google Workspace tools
   - Maintains internal consistency checking

2. **Package Initialization (`asistent/__init__.py`)**
   - Handles Vertex AI initialization at package load
   - Loads environment variables from `.env`
   - Imports and exposes the main agent

3. **Configuration (`asistent/config.py`)**
   - Centralized settings for RAG operations
   - Default values for chunk size, overlap, embedding model
   - Project and location configuration

4. **Authentication Module (`asistent/auth/`)**
   - **`auth_config.py`**: ADK-native OAuth2 configuration
   - Implements official ADK authentication pattern (6-step flow)
   - Manages Google Workspace API scopes (Drive, Docs)
   - Integrates with Secret Manager for credentials

5. **Secrets Management (`asistent/secrets.py`)**
   - Retrieves sensitive configuration from Google Cloud Secret Manager
   - Functions for OAuth credentials, Drive folder IDs, allowed users
   - Handles URL extraction and JSON parsing

6. **Tools Directory (`asistent/tools/`)**

   **RAG Tools** (no authentication required):
   - `rag_query.py`: Query documents in corpora
   - `list_corpora.py`: List available document corpora
   - `create_corpus.py`: Create new corpora
   - `add_data.py`: Add documents to corpora
   - `get_corpus_info.py`: Get detailed corpus information
   - `delete_document.py`: Delete specific documents
   - `delete_corpus.py`: Delete entire corpora

   **Google Workspace Tools** (OAuth2 required):
   - `save_document_to_drive.py`: Save contracts as Google Docs (legacy)
   - `list_user_documents.py`: List user's saved documents
   - `document_context_helper.py`: **NEW** Context preparation for DocsToolset
     - `prepare_document_context`: Prepares folder, filename, versioning
     - `finalize_document_in_drive`: Finalizes and organizes created documents

   **Google API Toolsets** (ADK built-in, OAuth2 required):
   - **DocsToolset**: Google's native Docs API toolset
     - Configured with OAuth credentials from Secret Manager
     - Provides multiple document operation tools
     - Used in 3-step workflow with context helpers

   **Shared Utilities**:
   - `utils.py`: Corpus name resolution, state management

### Authentication Architecture

The project uses **ADK native OAuth2 authentication** following the official 6-step pattern:

1. **Tool Configuration**: Tools declare OAuth2 requirements via `auth_config.py`
2. **Credential Request**: ADK detects when OAuth is needed
3. **User Authorization**: User completes OAuth flow in browser
4. **Token Exchange**: ADK automatically exchanges auth code for tokens
5. **Credential Caching**: Tokens stored in `tool_context.state` for reuse
6. **Auto Refresh**: ADK handles token refresh transparently

**Key Files**:
- `asistent/auth/auth_config.py`: OAuth2 scheme and credential configuration
- `client/agent_client.py`: Interactive OAuth flow for local testing
- `save_document_to_drive.py` & `list_user_documents.py`: Example tool implementations

**Authentication Flow**:
- RAG tools work without authentication (use Vertex AI service account)
- Workspace tools trigger OAuth when first accessed
- Credentials are shared across tools in the same session
- Session state persists credentials between tool calls

### Deployment Architecture

**Local Development**:
- `client/agent_client.py`: Interactive runner with OAuth support
- InMemorySessionService for session management
- Manual OAuth flow via console interaction

**Production (Agent Engine)**:
- `deploy_agent_engine.py`: Deployment script
- `test_deployed_agent.py`: Remote agent testing
- VertexAiSessionService (automatic session persistence)
- Auto-scaling and built-in monitoring

### State Management

- Uses ADK ToolContext for maintaining agent state
- Tracks "current corpus" for operations
- Caches corpus existence checks
- Stores OAuth credentials per session
- Manages resource name resolution

### Key Design Patterns

- All tools use the same utilities for corpus name resolution
- Full Vertex AI resource names are used internally but hidden from users
- Confirmation required for destructive operations (delete_document, delete_corpus)
- Error handling with appropriate user feedback
- OAuth credentials cached and shared between tools
- Automatic token refresh on 401/403 errors

## Dependencies

Main dependencies from `requirements.txt`:
- `google-adk>=1.16.0`: Google Agent Development Kit
- `google-cloud-aiplatform[adk,agent_engines]>=1.112.0`: Vertex AI integration
- `google-genai>=1.41.0`: Gemini model access
- `google-cloud-storage>=2.18.0`: GCS file handling
- `google-cloud-secret-manager>=2.22.0`: Secure configuration
- `google-api-python-client>=2.157.0`: Google Workspace APIs
- `python-dotenv>=1.0.0`: Environment variable management
- `authlib>=1.5.1`: OAuth2 implementation (ADK dependency)

## Important Technical Details

### Agent Instruction Pattern

The agent follows a specific workflow for document generation:
1. Gather requirements from user
2. Query templates using RAG
3. Generate initial draft
4. Iterate based on user feedback
5. Save to Drive only when explicitly approved

**Approval phrases recognized**:
- "Guardá este contrato"
- "Guardalo en Drive"
- "Creá el documento final"
- "Exportá este contrato"

### Document Versioning

Automatic version control for saved documents:
- Filenames auto-normalized: "Contrato Compra-Venta" → "contrato-compra-venta"
- Auto-increment on duplicates: `v2`, `v3`, etc.
- User always informed of final saved version name

### DocsToolset Workflow (NEW)

The agent now supports two approaches for saving documents:

**Option A: Legacy single-tool approach**
```python
save_document_to_drive(
    document_title="Contrato Compra-Venta Juan Pérez",
    document_content="...",
    document_type="compra-venta"
)
```

**Option B: DocsToolset 3-step workflow** (recommended for advanced use)
```python
# Step 1: Prepare context (folder, versioning)
context = prepare_document_context(
    document_title="Contrato Compra-Venta Juan Pérez",
    document_type="compra-venta"
)
# Returns: {"versioned_name": "contrato-compra-venta-juan-perez-v2", ...}

# Step 2: Create document with DocsToolset
doc = DocsToolset.create_document(
    title=context["versioned_name"],
    content="..."
)
# Returns: {"document_id": "1abc123..."}

# Step 3: Finalize (move to folder, get link)
result = finalize_document_in_drive(
    document_id=doc["document_id"]
)
# Returns: {"document_url": "https://docs.google.com/...", ...}
```

**Benefits of DocsToolset workflow**:
- Separation of concerns (business logic vs. document operations)
- Access to all DocsToolset capabilities (formatting, batch operations, etc.)
- Future-proof as DocsToolset is maintained by Google
- More flexible for complex document operations

### Resource Name Resolution

The `utils.py` module handles three corpus name formats:
1. Full resource name: `projects/{id}/locations/{loc}/ragCorpora/{name}`
2. Display name: User-friendly name (resolved via API lookup)
3. Short ID: Just the corpus identifier (constructed into full name)

### OAuth2 Credential Flow

Tools requiring authentication follow this pattern:
```python
# 1. Import auth config
from asistent.auth.auth_config import get_google_oauth_auth_scheme, get_google_oauth_credential

# 2. Decorate tool with auth
@agent_tool(
    auth_config=AuthConfig(
        auth_scheme=get_google_oauth_auth_scheme(),
        auth_credential=get_google_oauth_credential()
    )
)
def my_tool(...):
    # 3. Get credentials from context
    creds = tool_context.state.get('google_workspace_credentials')

    # 4. Build service
    service = build('drive', 'v3', credentials=creds)
```

### Secret Manager Integration

All sensitive configuration stored in Secret Manager:
- `google-client-id`: OAuth2 client ID
- `google-client-secret`: OAuth2 client secret
- `drive-root-folder-id`: Root folder for user documents
- `allowed-users`: JSON array of authorized email addresses

Access via `asistent/secrets.py` functions:
- `get_secret(secret_id)`: Generic secret retrieval
- `get_drive_root_folder_id()`: Drive folder with URL parsing
- `get_allowed_users()`: User list with JSON parsing

## Authentication Requirements

- Google Cloud account with billing enabled
- Vertex AI API enabled in the project
- Secret Manager API enabled
- OAuth2 client credentials configured in Cloud Console
- Application Default Credentials configured locally
- Appropriate IAM permissions:
  - `aiplatform.reasoningEngines.create` (for deployment)
  - `secretmanager.versions.access` (for secrets)
  - `storage.buckets.get` (for staging bucket)

## Deployment Checklist

Before deploying to Agent Engine:

1. **OAuth Configuration**:
   - Create OAuth 2.0 client in Cloud Console
   - Add authorized redirect URIs
   - Store credentials in Secret Manager

2. **Environment Setup**:
   - Update `deploy_agent_engine.py` with project details
   - Ensure staging bucket exists and is accessible
   - Verify all required secrets exist in Secret Manager

3. **Testing**:
   - Test locally first: `python client/agent_client.py`
   - Verify RAG tools work without auth
   - Verify Workspace tools trigger OAuth correctly
   - Confirm credential caching and reuse

4. **Deployment**:
   - Run `python deploy_agent_engine.py`
   - Wait 5-10 minutes for deployment
   - Test with `python test_deployed_agent.py`
   - Monitor logs and traces in Cloud Console

## References

- [ADK Documentation](https://google.github.io/adk-docs/)
- [ADK Authentication Guide](https://google.github.io/adk-docs/tools/authentication/)
- [Agent Engine Overview](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview)
- [Vertex AI RAG Documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/rag-overview)
- Project-specific docs in `docs/` directory:
  - `AUTH_REFACTOR_SUMMARY.md`: Technical auth refactoring details
  - `DEPLOYMENT_GUIDE.md`: Complete deployment walkthrough
