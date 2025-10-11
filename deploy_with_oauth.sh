#!/bin/bash

set -e

PROJECT_ID="escribania-mastropasqua"
REGION="us-central1"
SERVICE_NAME="rag-legal-agent-ui"
SERVICE_URL="https://rag-legal-agent-ui-997298514042.us-central1.run.app"

echo "=========================================="
echo "Deploy RAG Legal Agent con OAuth"
echo "=========================================="
echo ""

# Check if OAuth credentials exist
echo "Verificando credenciales OAuth..."
CURRENT_CLIENT_ID=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format='value(spec.template.spec.containers[0].env[?name=="GOOGLE_CLIENT_ID"].value)' 2>/dev/null || echo "")

if [ -z "$CURRENT_CLIENT_ID" ]; then
    echo ""
    echo "⚠️  No se encontraron credenciales OAuth configuradas."
    echo ""
    echo "Por favor, seguí estos pasos:"
    echo ""
    echo "1. Abrí este link en tu navegador:"
    echo "   https://console.cloud.google.com/apis/credentials?project=$PROJECT_ID"
    echo ""
    echo "2. Click en '+ CREATE CREDENTIALS' → 'OAuth client ID'"
    echo ""
    echo "3. Si es necesario, configurá la pantalla de consentimiento primero"
    echo ""
    echo "4. Configurá:"
    echo "   - Application type: Web application"
    echo "   - Name: RAG Legal Agent Web UI"
    echo "   - Authorized redirect URIs: ${SERVICE_URL}/authorize"
    echo ""
    echo "5. Copiá el Client ID y Client Secret"
    echo ""
    read -p "Presioná Enter cuando hayas creado las credenciales..."
    echo ""
    read -p "Ingresá el GOOGLE_CLIENT_ID: " CLIENT_ID
    read -p "Ingresá el GOOGLE_CLIENT_SECRET: " CLIENT_SECRET
    echo ""
else
    echo "✓ Credenciales OAuth ya configuradas"
    read -p "¿Querés actualizar las credenciales? (y/n): " UPDATE_CREDS
    if [ "$UPDATE_CREDS" = "y" ]; then
        read -p "Ingresá el nuevo GOOGLE_CLIENT_ID: " CLIENT_ID
        read -p "Ingresá el nuevo GOOGLE_CLIENT_SECRET: " CLIENT_SECRET
        echo ""
    else
        CLIENT_ID=$CURRENT_CLIENT_ID
        CLIENT_SECRET="(usando existente)"
        echo "Usando credenciales existentes"
    fi
fi

# Deploy to Cloud Run
echo "Desplegando a Cloud Run..."
echo ""

if [ -n "$CLIENT_ID" ] && [ -n "$CLIENT_SECRET" ]; then
    gcloud run deploy $SERVICE_NAME \
        --source=. \
        --region=$REGION \
        --project=$PROJECT_ID \
        --port=8080 \
        --memory=2Gi \
        --cpu=2 \
        --timeout=3600 \
        --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=$REGION,GOOGLE_GENAI_USE_VERTEXAI=TRUE,AGENT_ENGINE_ID=1053512459316363264,GOOGLE_CLIENT_ID=$CLIENT_ID,GOOGLE_CLIENT_SECRET=$CLIENT_SECRET"
else
    gcloud run deploy $SERVICE_NAME \
        --source=. \
        --region=$REGION \
        --project=$PROJECT_ID \
        --port=8080 \
        --memory=2Gi \
        --cpu=2 \
        --timeout=3600
fi

echo ""
echo "=========================================="
echo "✓ Deploy completado"
echo "=========================================="
echo ""
echo "URL: $SERVICE_URL"
echo ""
echo "Usuarios autorizados:"
echo "  - carlos@xplorers.ar"
echo "  - escribania@mastropasqua.ar"
echo "  - escribaniamastropasqua@gmail.com"
echo "  - camib.milone@gmail.com"
echo ""
