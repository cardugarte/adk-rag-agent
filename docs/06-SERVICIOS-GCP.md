# Servicios de Google Cloud Utilizados

## Vertex AI Agent Engine

**¿Qué es?**
Plataforma managed para ejecutar agentes de IA en producción.

**Uso en el proyecto:**
- Ejecuta el RAG Agent
- Gestiona sesiones de usuario
- Integración con Vertex AI RAG
- Escalamiento automático

**Configuración:**
- **Region**: `us-central1`
- **Model**: `gemini-2.5-flash`
- **Resource ID**: `1053512459316363264`

**Costos:**
- $0.03/hora de ejecución activa
- Tokens adicionales según uso de Gemini

**API:**
```
aiplatform.googleapis.com
```

**Console:**
https://console.cloud.google.com/vertex-ai/reasoning-engines?project=escribania-mastropasqua

---

## Cloud Run

**¿Qué es?**
Plataforma serverless para ejecutar containers HTTP.

**Uso en el proyecto:**
- Hostea la ADK Web UI
- Auto-scaling 0-10 instancias
- HTTPS automático
- Integración IAM

**Configuración:**
- **Service**: `rag-legal-agent-ui`
- **Region**: `us-central1`
- **Memory**: 2Gi
- **CPU**: 2
- **Port**: 8080
- **Timeout**: 3600s

**URL:**
```
https://rag-legal-agent-ui-997298514042.us-central1.run.app
```

**Costos:**
- $0.00002400/vCPU-second
- $0.00000250/GiB-second
- ~$0.10/hora activa

**API:**
```
run.googleapis.com
```

---

## Vertex AI RAG

**¿Qué es?**
Servicio managed para Retrieval Augmented Generation.

**Uso en el proyecto:**
- Almacena corpus de documentos
- Genera embeddings
- Búsqueda semántica

**Configuración:**
- **Embedding Model**: `text-embedding-005`
- **Chunk Size**: 512 tokens
- **Chunk Overlap**: 100 tokens
- **Top K**: 3 resultados

**Costos:**
- $0.025/1K tokens para embeddings
- Storage: $0.026/GB-mes

**API:**
```
aiplatform.googleapis.com
```

---

## Cloud Storage

**¿Qué es?**
Object storage para archivos y datos.

**Uso en el proyecto:**
- Staging bucket para deployments
- Almacenamiento de logs
- Artifact storage (opcional)

**Buckets:**
```
gs://cloud-ai-platform-23597a65-584b-4f31-af48-fc810cfe7cd0/
gs://escribania-mastropasqua_cloudbuild/
```

**Costos:**
- Regional storage: $0.020/GB-mes
- Operations: $0.05/10K ops

---

## Cloud Build

**¿Qué es?**
CI/CD managed para builds de containers.

**Uso en el proyecto:**
- Build de Docker images
- Deploy automatizado

**Configuración:**
```yaml
# cloudbuild.web.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/rag-legal-agent-ui', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/rag-legal-agent-ui']
```

**Costos:**
- Primeras 120 build-minutes/día: gratis
- Después: $0.003/build-minute

---

## Identity and Access Management (IAM)

**¿Qué es?**
Gestión de permisos y autenticación.

**Uso en el proyecto:**

### Service Accounts

```
997298514042-compute@developer.gserviceaccount.com
```

**Roles:**
- `roles/aiplatform.user`
- `roles/run.invoker`
- `roles/storage.objectViewer`

### Users

```yaml
roles/run.invoker:
  - user:carlos@xplorers.ar
  - user:escribania@mastropasqua.ar
  - user:escribaniamastropasqua@gmail.com
  - user:camib.milone@gmail.com
```

---

## Cloud Logging

**¿Qué es?**
Logging centralizado.

**Uso en el proyecto:**
- Logs de Cloud Run
- Logs de Agent Engine
- Error tracking

**Queries útiles:**

```bash
# Logs de Cloud Run
resource.type="cloud_run_revision"
AND resource.labels.service_name="rag-legal-agent-ui"

# Logs de Agent Engine
resource.type="aiplatform.googleapis.com/ReasoningEngine"
AND resource.labels.reasoning_engine_id="1053512459316363264"

# Solo errores
severity>=ERROR
```

**Costos:**
- Primeros 50GB/mes: gratis
- Después: $0.50/GB

---

## Cloud Monitoring

**¿Qué es?**
Métricas y alertas.

**Métricas disponibles:**

### Cloud Run
- Request count
- Request latency
- Instance count
- CPU utilization
- Memory utilization

### Agent Engine
- Query count
- Execution time
- Token usage
- Error rate

**Configuración de alertas:**

```bash
gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="High Error Rate" \
    --condition-display-name="Error rate > 10%" \
    --condition-threshold-value=0.1
```

---

## Resource Manager

**¿Qué es?**
Gestión de proyectos y organización.

**Configuración:**
- **Organization**: `travelsats.ar` (1054119104602)
- **Project ID**: `escribania-mastropasqua`
- **Project Number**: `997298514042`

**Organization Policies:**

```yaml
constraint: constraints/iam.allowedPolicyMemberDomains
listPolicy:
  allValues: ALLOW  # Permite Gmail y dominios externos
```

---

## Container Registry

**¿Qué es?**
Registry de Docker images.

**Images:**
```
gcr.io/escribania-mastropasqua/rag-legal-agent-ui:latest
```

**Costos:**
- Storage: $0.026/GB-mes
- Network egress: según uso

---

## APIs Habilitadas

```bash
aiplatform.googleapis.com              # Vertex AI
run.googleapis.com                     # Cloud Run
storage-api.googleapis.com             # Cloud Storage
cloudbuild.googleapis.com              # Cloud Build
logging.googleapis.com                 # Logging
monitoring.googleapis.com              # Monitoring
```

### Verificar APIs

```bash
gcloud services list --enabled --project=escribania-mastropasqua
```

### Habilitar API

```bash
gcloud services enable SERVICE_NAME.googleapis.com
```

---

## Quotas y Límites

### Cloud Run
- **Max instances**: 10 (configurable)
- **Max memory**: 32Gi
- **Max CPU**: 8
- **Max timeout**: 3600s

### Vertex AI
- **Max Agent Engines**: 100/project
- **Max tokens/request**: 32K (Gemini 2.5 Flash)
- **Requests/minute**: 300 (default)

### Aumentar Quotas

https://console.cloud.google.com/iam-admin/quotas?project=escribania-mastropasqua

---

## Regiones y Disponibilidad

**Region usada**: `us-central1`

**Ventajas:**
- Latencia baja a EE.UU.
- Disponibilidad de todos los servicios
- Costos competitivos

**Alternativas:**
- `us-east1` (Virginia)
- `southamerica-east1` (São Paulo) - Más cercano geográficamente

---

## Service Mesh (No implementado)

**Posible mejora futura:**
- Istio para service-to-service auth
- Traffic management
- Observability mejorada

---

## Arquitectura de Red

```
Internet
    ↓
Cloud Load Balancer (automático en Cloud Run)
    ↓
Cloud Run (VPC connector opcional)
    ↓
Vertex AI Agent Engine (private Google network)
    ↓
Vertex AI RAG (private Google network)
```

**Nota**: Todo el tráfico entre servicios de Google es interno, no sale a internet público.

---

## Referencias

- **Vertex AI Pricing**: https://cloud.google.com/vertex-ai/pricing
- **Cloud Run Pricing**: https://cloud.google.com/run/pricing
- **IAM Best Practices**: https://cloud.google.com/iam/docs/best-practices
- **ADK Documentation**: https://google.github.io/adk-docs
