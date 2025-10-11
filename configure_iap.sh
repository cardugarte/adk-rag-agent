#!/bin/bash

# Script to configure Identity-Aware Proxy (IAP) for Google Authentication

set -e

PROJECT_ID="escribania-mastropasqua"
REGION="us-central1"
SERVICE_NAME="rag-legal-agent-ui"

echo "🔐 Configurando Identity-Aware Proxy (IAP)..."
echo "   Project: ${PROJECT_ID}"
echo "   Service: ${SERVICE_NAME}"
echo

# Step 1: Update Cloud Run to require authentication
echo "📝 Step 1: Requiring authentication for Cloud Run service..."
gcloud run services update ${SERVICE_NAME} \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --no-allow-unauthenticated

echo "✅ Service now requires authentication"
echo

# Step 2: Create IAP Brand (OAuth consent screen)
echo "📝 Step 2: Configure OAuth consent screen..."
echo "⚠️  You need to manually configure the OAuth consent screen in the Google Cloud Console:"
echo "   1. Go to: https://console.cloud.google.com/apis/credentials/consent?project=${PROJECT_ID}"
echo "   2. Configure the consent screen if not already done"
echo "   3. Add authorized domains"
echo

# Step 3: Add IAM bindings for authorized users
echo "📝 Step 3: Add authorized users..."
echo "Enter the email addresses of users who should have access (one per line, empty line to finish):"
echo

while true; do
    read -p "Email (or press Enter to finish): " USER_EMAIL
    if [ -z "$USER_EMAIL" ]; then
        break
    fi

    echo "   Adding ${USER_EMAIL}..."
    gcloud run services add-iam-policy-binding ${SERVICE_NAME} \
        --region=${REGION} \
        --project=${PROJECT_ID} \
        --member="user:${USER_EMAIL}" \
        --role="roles/run.invoker"

    echo "   ✅ ${USER_EMAIL} added"
done

echo
echo "✅ IAP Configuration complete!"
echo

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --platform=managed \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --format='value(status.url)')

echo "🌐 Service URL: ${SERVICE_URL}"
echo
echo "📋 Users with access need to:"
echo "   1. Visit: ${SERVICE_URL}"
echo "   2. Sign in with their Google account"
echo "   3. They will see the ADK Web UI interface"
echo
