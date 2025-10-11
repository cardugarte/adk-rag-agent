# Despliegue de ADK Web UI a Cloud Run

## Arquitectura

```
Cloud Run (Container)
  ├── FastAPI Server
  ├── ADK Web UI (Angular)
  └── Conexión a Agent Engine
```

## Dockerfile

`Dockerfile.web`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY asistent/ ./asistent/

ENV GOOGLE_CLOUD_PROJECT=escribania-mastropasqua
ENV GOOGLE_CLOUD_LOCATION=us-central1
ENV PORT=8080
ENV AGENT_ENGINE_ID=1053512459316363264
ENV GOOGLE_GENAI_USE_VERTEXAI=TRUE

EXPOSE 8080

CMD adk web \
    --host=0.0.0.0 \
    --port=${PORT} \
    --session_service_uri=agentengine://${AGENT_ENGINE_ID} \
    --no-reload \
    ./asistent
```

## Deploy

```bash
gcloud run deploy rag-legal-agent-ui \
    --source=. \
    --platform=managed \
    --region=us-central1 \
    --project=escribania-mastropasqua \
    --port=8080 \
    --memory=2Gi \
    --cpu=2 \
    --timeout=3600 \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=escribania-mastropasqua,GOOGLE_CLOUD_LOCATION=us-central1,GOOGLE_GENAI_USE_VERTEXAI=TRUE,AGENT_ENGINE_ID=1053512459316363264"
```

## Service URL

```
https://rag-legal-agent-ui-997298514042.us-central1.run.app
```

## Configuración IAM

### Permitir Dominios Externos

```yaml
# org-policy.yaml
constraint: constraints/iam.allowedPolicyMemberDomains
listPolicy:
  allValues: ALLOW
```

```bash
gcloud resource-manager org-policies set-policy org-policy.yaml \
    --project=escribania-mastropasqua
```

### Agregar Usuarios

```bash
gcloud run services add-iam-policy-binding rag-legal-agent-ui \
    --region=us-central1 \
    --project=escribania-mastropasqua \
    --member=user:email@domain.com \
    --role=roles/run.invoker
```

### Usuarios Actuales

```bash
gcloud run services get-iam-policy rag-legal-agent-ui \
    --region=us-central1 \
    --project=escribania-mastropasqua
```

**Output:**
```yaml
bindings:
- members:
  - user:camib.milone@gmail.com
  - user:carlos@xplorers.ar
  - user:escribania@mastropasqua.ar
  - user:escribaniamastropasqua@gmail.com
  role: roles/run.invoker
```

## ADK Web CLI

### Local

```bash
adk web \
    --host=0.0.0.0 \
    --port=8080 \
    --session_service_uri=agentengine://1053512459316363264 \
    ./asistent
```

### Opciones

| Flag | Descripción | Valor |
|------|-------------|-------|
| `--host` | Binding host | `0.0.0.0` |
| `--port` | Puerto | `8080` |
| `--session_service_uri` | Conexión a Agent Engine | `agentengine://{id}` |
| `--no-reload` | Deshabilitar auto-reload | Production |
| `--reload` | Habilitar auto-reload | Development |

## Actualización

```bash
# Rebuild y redeploy
gcloud run deploy rag-legal-agent-ui \
    --source=. \
    --region=us-central1 \
    --project=escribania-mastropasqua
```

## Monitoring

### Logs

```bash
gcloud run logs read rag-legal-agent-ui \
    --region=us-central1 \
    --limit=50
```

### Métricas

```bash
gcloud run services describe rag-legal-agent-ui \
    --region=us-central1 \
    --format="value(status.url,status.traffic)"
```

## Troubleshooting

### 403 Forbidden

Usuario no autorizado en IAM policy.

### 502 Bad Gateway

Container no inició correctamente. Ver logs.

### Timeout

Aumentar `--timeout`:
```bash
--timeout=3600  # 1 hora
```

## Costos

- **Cloud Run**: $0.10/hora de uso activo
- **Network egress**: $0.12/GB
- **Container Registry**: Storage de imagen

## Environment Variables

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `GOOGLE_CLOUD_PROJECT` | `escribania-mastropasqua` | Project ID |
| `GOOGLE_CLOUD_LOCATION` | `us-central1` | Región |
| `AGENT_ENGINE_ID` | `1053512459316363264` | ID del agente |
| `PORT` | `8080` | Puerto del servidor |
| `GOOGLE_GENAI_USE_VERTEXAI` | `TRUE` | Usar Vertex AI |

## Security

### HTTPS

Automático por Cloud Run.

### Autenticación

OAuth 2.0 vía Google Identity Platform.

### IAM

Rol `roles/run.invoker` requerido para acceso.

## CI/CD

### Cloud Build

`cloudbuild.web.yaml`:

```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/rag-legal-agent-ui:latest', '-f', 'Dockerfile.web', '.']

  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/rag-legal-agent-ui:latest']

images:
  - 'gcr.io/$PROJECT_ID/rag-legal-agent-ui:latest'
```

### Deploy Script

`deploy_web_ui.sh`:

```bash
#!/bin/bash
gcloud run deploy rag-legal-agent-ui \
    --source=. \
    --region=us-central1 \
    --project=escribania-mastropasqua \
    --port=8080 \
    --memory=2Gi \
    --cpu=2
```
