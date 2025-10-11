# Guía Rápida

## Comandos Esenciales

### Deploy Agente

```bash
python deploy.py
```

### Deploy Web UI

```bash
gcloud run deploy rag-legal-agent-ui \
    --source=. \
    --region=us-central1
```

### Agregar Usuario

```bash
gcloud run services add-iam-policy-binding rag-legal-agent-ui \
    --region=us-central1 \
    --member=user:email@domain.com \
    --role=roles/run.invoker
```

### Ver Logs Agente

```bash
gcloud logging read \
    "resource.type=aiplatform.googleapis.com/ReasoningEngine \
    AND resource.labels.reasoning_engine_id=1053512459316363264" \
    --limit=50
```

### Ver Logs Web UI

```bash
gcloud run logs read rag-legal-agent-ui --region=us-central1 --limit=50
```

### Test Local ADK Web

```bash
adk web --port=8080 --session_service_uri=agentengine://1053512459316363264 ./asistent
```

### Listar Usuarios Autorizados

```bash
gcloud run services get-iam-policy rag-legal-agent-ui --region=us-central1
```

### Remover Usuario

```bash
gcloud run services remove-iam-policy-binding rag-legal-agent-ui \
    --region=us-central1 \
    --member=user:email@domain.com \
    --role=roles/run.invoker
```

## URLs

- **Web UI**: https://rag-legal-agent-ui-997298514042.us-central1.run.app
- **Cloud Run Console**: https://console.cloud.google.com/run?project=escribania-mastropasqua
- **Agent Engine Console**: https://console.cloud.google.com/vertex-ai/reasoning-engines?project=escribania-mastropasqua

## Resource IDs

- **Project**: `escribania-mastropasqua`
- **Region**: `us-central1`
- **Agent Engine ID**: `1053512459316363264`
- **Cloud Run Service**: `rag-legal-agent-ui`
