#!/bin/bash

# Deployment script for ADK Web UI to Cloud Run

set -e

# Configuration
PROJECT_ID="escribania-mastropasqua"
REGION="us-central1"
SERVICE_NAME="rag-legal-agent-ui"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Deploying ADK Web UI to Cloud Run..."
echo "   Project: ${PROJECT_ID}"
echo "   Region: ${REGION}"
echo "   Service: ${SERVICE_NAME}"
echo

# Build the container image
echo "📦 Building container image..."
gcloud builds submit \
    --config=cloudbuild.web.yaml \
    --project=${PROJECT_ID}

# Deploy to Cloud Run
echo "☁️  Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image=${IMAGE_NAME}:latest \
    --platform=managed \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --allow-unauthenticated \
    --port=8080 \
    --memory=2Gi \
    --cpu=2 \
    --timeout=3600 \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION}" \
    --service-account=997298514042-compute@developer.gserviceaccount.com

echo
echo "✅ Deployment complete!"
echo

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --platform=managed \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --format='value(status.url)')

echo "🌐 Service URL: ${SERVICE_URL}"
echo
echo "⚠️  IMPORTANT: The service is currently publicly accessible."
echo "   To enable Google authentication, run:"
echo "   ./configure_iap.sh"
echo
