# Despliegue del Agente Backend a Agent Engine

## Prerequisitos

- Python 3.12
- Google Cloud CLI autenticado
- Proyecto: `escribania-mastropasqua`
- APIs habilitadas: `aiplatform.googleapis.com`

## Configuración Inicial

### 1. Dependencias

```bash
pip install google-cloud-aiplatform[adk,agent_engines]
```

### 2. Variables de Entorno

`.env`:
```bash
GOOGLE_CLOUD_PROJECT=escribania-mastropasqua
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=TRUE
```

### 3. Autenticación

```bash
gcloud auth application-default login
gcloud config set project escribania-mastropasqua
```

## Estructura del Agente

```python
# asistent/agent.py
from google.adk.agents import Agent

root_agent = Agent(
    name="RagAgent",
    model="gemini-2.5-flash",
    description="Vertex AI RAG Agent",
    tools=[
        rag_query,
        list_corpora,
        create_corpus,
        add_data,
        get_corpus_info,
        delete_corpus,
        delete_document,
    ],
    instruction="..."  # Instrucciones en español
)
```

## Deploy Script

`deploy.py`:

```python
import vertexai
from vertexai import agent_engines

# Init
vertexai.init(
    project="escribania-mastropasqua",
    location="us-central1",
    staging_bucket="gs://cloud-ai-platform-23597a65-584b-4f31-af48-fc810cfe7cd0"
)

# Import agent
from asistent.agent import root_agent

# Wrap en AdkApp
app = agent_engines.AdkApp(
    agent=root_agent,
    enable_tracing=True
)

# Deploy
remote_app = agent_engines.create(
    agent_engine=app,
    requirements=[
        "google-cloud-aiplatform[adk,agent_engines]",
        "google-generativeai",
        "python-dotenv",
        "google-cloud-storage",
        "google-genai"
    ],
    extra_packages=["./asistent"],
    display_name="RAG Legal Agent"
)
```

## Deployment

```bash
python deploy.py
```

**Output:**
```
AgentEngine created
Resource name: projects/997298514042/locations/us-central1/reasoningEngines/1053512459316363264
```

## Verificación

```python
from vertexai import agent_engines

agent = agent_engines.get(
    "projects/997298514042/locations/us-central1/reasoningEngines/1053512459316363264"
)

# Crear sesión
session = await agent.async_create_session(user_id="test")

# Test query
response = agent.async_stream_query(
    message="¿Qué puedes hacer?",
    user_id="test",
    session_id=session['id']
)
```

## Configuración RAG

`asistent/config.py`:

```python
DEFAULT_CHUNK_SIZE = 512
DEFAULT_CHUNK_OVERLAP = 100
DEFAULT_TOP_K = 3
DEFAULT_DISTANCE_THRESHOLD = 0.5
DEFAULT_EMBEDDING_MODEL = "publishers/google/models/text-embedding-005"
```

## Herramientas Implementadas

| Tool | Descripción | Parámetros |
|------|-------------|------------|
| `rag_query` | Consulta documentos | `corpus_name`, `query` |
| `list_corpora` | Lista corpus | - |
| `create_corpus` | Crea corpus | `corpus_name` |
| `add_data` | Agrega docs | `corpus_name`, `paths` |
| `get_corpus_info` | Info de corpus | `corpus_name` |
| `delete_document` | Elimina doc | `corpus_name`, `document_id`, `confirm` |
| `delete_corpus` | Elimina corpus | `corpus_name`, `confirm` |

## Actualizar Agente

1. Modificar código en `asistent/`
2. Re-ejecutar `python deploy.py`
3. Nuevo resource name generado

## Costos

- **Agent Engine**: $0.03/hora de ejecución
- **Gemini 2.5 Flash**: $0.15/1M tokens input, $0.60/1M output
- **Embeddings**: $0.025/1M tokens

## Troubleshooting

### Error: Module not found

```bash
# Agregar al extra_packages
extra_packages=["./asistent", "./otro_modulo"]
```

### Error: Staging bucket required

```python
vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket="gs://bucket-name"  # Requerido
)
```

### Ver logs

```bash
gcloud logging read \
    "resource.type=aiplatform.googleapis.com/ReasoningEngine \
    AND resource.labels.reasoning_engine_id=1053512459316363264" \
    --limit=50
```

## Resource Names

**Formato:**
```
projects/{project}/locations/{location}/reasoningEngines/{id}
```

**Ejemplo:**
```
projects/997298514042/locations/us-central1/reasoningEngines/1053512459316363264
```

## CLI Commands

```bash
# Listar agent engines
gcloud ai reasoning-engines list --region=us-central1

# Eliminar agent engine
gcloud ai reasoning-engines delete 1053512459316363264 --region=us-central1
```
