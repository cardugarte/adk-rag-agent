# Administración del Sistema

## Gestión de Usuarios

### Agregar Usuario

```bash
gcloud run services add-iam-policy-binding rag-legal-agent-ui \
    --region=us-central1 \
    --project=escribania-mastropasqua \
    --member=user:nuevo@email.com \
    --role=roles/run.invoker
```

### Remover Usuario

```bash
gcloud run services remove-iam-policy-binding rag-legal-agent-ui \
    --region=us-central1 \
    --project=escribania-mastropasqua \
    --member=user:usuario@email.com \
    --role=roles/run.invoker
```

### Listar Usuarios

```bash
gcloud run services get-iam-policy rag-legal-agent-ui \
    --region=us-central1 \
    --project=escribania-mastropasqua
```

## Actualización del Agente

### 1. Modificar código

```bash
# Editar archivos en asistent/
vim asistent/agent.py
vim asistent/tools/nueva_tool.py
```

### 2. Re-deploy

```bash
python deploy.py
```

**Nota**: Se crea un nuevo Agent Engine. Actualizar `AGENT_ENGINE_ID` en Dockerfile.web.

### 3. Actualizar Web UI

```bash
# Editar Dockerfile.web con nuevo ID
gcloud run deploy rag-legal-agent-ui --source=. --region=us-central1
```

## Actualización de la Web UI

### Cambiar configuración

```bash
gcloud run services update rag-legal-agent-ui \
    --region=us-central1 \
    --set-env-vars="AGENT_ENGINE_ID=nuevo_id"
```

### Cambiar recursos

```bash
gcloud run services update rag-legal-agent-ui \
    --region=us-central1 \
    --memory=4Gi \
    --cpu=4
```

### Cambiar timeout

```bash
gcloud run services update rag-legal-agent-ui \
    --region=us-central1 \
    --timeout=7200
```

## Monitoreo

### Métricas Cloud Run

```bash
gcloud monitoring time-series list \
    --filter='resource.type="cloud_run_revision" AND resource.labels.service_name="rag-legal-agent-ui"' \
    --project=escribania-mastropasqua
```

### Logs en Tiempo Real

```bash
gcloud run logs tail rag-legal-agent-ui --region=us-central1
```

### Errores Recientes

```bash
gcloud logging read "resource.type=cloud_run_revision \
    AND resource.labels.service_name=rag-legal-agent-ui \
    AND severity>=ERROR" \
    --limit=20 \
    --project=escribania-mastropasqua
```

## Backup y Restore

### Backup Código

```bash
git add .
git commit -m "backup: estado actual"
git push
```

### Export IAM Policy

```bash
gcloud run services get-iam-policy rag-legal-agent-ui \
    --region=us-central1 \
    --format=json > iam-policy-backup.json
```

### Restore IAM Policy

```bash
gcloud run services set-iam-policy rag-legal-agent-ui \
    iam-policy-backup.json \
    --region=us-central1
```

## Rollback

### Listar Revisiones

```bash
gcloud run revisions list --service=rag-legal-agent-ui --region=us-central1
```

### Rollback a Revisión Anterior

```bash
gcloud run services update-traffic rag-legal-agent-ui \
    --region=us-central1 \
    --to-revisions=rag-legal-agent-ui-00001=100
```

## Gestión de Costos

### Ver Facturación

```bash
gcloud billing accounts list
gcloud billing projects describe escribania-mastropasqua
```

### Budget Alert

```bash
gcloud billing budgets create \
    --billing-account=BILLING_ACCOUNT_ID \
    --display-name="RAG Agent Budget" \
    --budget-amount=100USD \
    --threshold-rule=percent=50 \
    --threshold-rule=percent=90
```

### Costos Estimados Mensuales

| Servicio | Costo Base | Costo por Uso |
|----------|------------|---------------|
| Cloud Run | $0 (sin tráfico) | ~$0.10/hora activa |
| Agent Engine | $0 (sin queries) | ~$0.03/hora ejecución |
| Gemini 2.5 Flash | $0 | $0.15/1M tokens in |
| Storage (logs) | ~$5/mes | $0.026/GB |
| **Total Estimado** | **$5-10/mes** | **+uso** |

## Scaling

### Auto-scaling Configurado

```yaml
minInstances: 0  # Scale to zero
maxInstances: 10 # Máximo 10 instancias
```

### Cambiar Límites

```bash
gcloud run services update rag-legal-agent-ui \
    --region=us-central1 \
    --min-instances=1 \
    --max-instances=20
```

## Seguridad

### Rotar Service Account Key

```bash
gcloud iam service-accounts keys create new-key.json \
    --iam-account=997298514042-compute@developer.gserviceaccount.com
```

### Auditar Accesos

```bash
gcloud logging read \
    "protoPayload.methodName=google.cloud.run.v2.Services.GetService \
    AND resource.labels.service_name=rag-legal-agent-ui" \
    --limit=100
```

### Configurar VPC Connector (Opcional)

```bash
gcloud compute networks vpc-access connectors create rag-connector \
    --region=us-central1 \
    --range=10.8.0.0/28

gcloud run services update rag-legal-agent-ui \
    --region=us-central1 \
    --vpc-connector=rag-connector
```

## Troubleshooting

### Service Not Responding

1. Ver logs:
```bash
gcloud run logs tail rag-legal-agent-ui --region=us-central1
```

2. Ver estado:
```bash
gcloud run services describe rag-legal-agent-ui --region=us-central1
```

3. Restart:
```bash
gcloud run services update rag-legal-agent-ui \
    --region=us-central1 \
    --clear-env-vars \
    --set-env-vars="$(cat env-vars.txt)"
```

### High Latency

```bash
# Aumentar CPU
gcloud run services update rag-legal-agent-ui --region=us-central1 --cpu=4

# Aumentar memoria
gcloud run services update rag-legal-agent-ui --region=us-central1 --memory=4Gi

# Keep warm (evitar cold starts)
gcloud run services update rag-legal-agent-ui --region=us-central1 --min-instances=1
```

### Agent Engine Errors

```bash
# Ver logs específicos
gcloud logging read \
    "resource.labels.reasoning_engine_id=1053512459316363264 \
    AND severity>=ERROR" \
    --limit=50
```

## Maintenance

### Schedule Downtime

```bash
# Stop traffic
gcloud run services update-traffic rag-legal-agent-ui \
    --region=us-central1 \
    --to-revisions=NONE

# Realizar mantenimiento

# Restore traffic
gcloud run services update-traffic rag-legal-agent-ui \
    --region=us-central1 \
    --to-latest
```

### Health Checks

```bash
# Endpoint de health
curl https://rag-legal-agent-ui-997298514042.us-central1.run.app/health

# Automated monitoring
gcloud monitoring uptime-check-configs create rag-ui-health \
    --display-name="RAG UI Health Check" \
    --http-check --path="/health"
```

## Disaster Recovery

### Eliminar y Recrear Servicio

```bash
# 1. Backup IAM policy
gcloud run services get-iam-policy rag-legal-agent-ui \
    --region=us-central1 > iam-backup.json

# 2. Delete service
gcloud run services delete rag-legal-agent-ui --region=us-central1

# 3. Redeploy
gcloud run deploy rag-legal-agent-ui --source=. --region=us-central1

# 4. Restore IAM
gcloud run services set-iam-policy rag-legal-agent-ui \
    iam-backup.json --region=us-central1
```
