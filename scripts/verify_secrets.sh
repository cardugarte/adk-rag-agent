#!/bin/bash

# Verification script for Secret Manager configuration
# Run this before deployment to ensure all secrets are properly configured

set -e

PROJECT_ID="escribania-mastropasqua"
REQUIRED_SECRETS=("flask-secret-key" "google-client-id" "google-client-secret" "allowed-users-list")

echo "🔍 Verifying Secret Manager configuration for project: $PROJECT_ID"
echo ""

# Check if Secret Manager API is enabled
echo "✓ Checking if Secret Manager API is enabled..."
if gcloud services list --enabled --project=$PROJECT_ID --filter="name:secretmanager.googleapis.com" --format="value(name)" | grep -q secretmanager; then
    echo "  ✅ Secret Manager API is enabled"
else
    echo "  ❌ Secret Manager API is NOT enabled"
    exit 1
fi

echo ""

# Check if all required secrets exist
echo "✓ Checking if all required secrets exist..."
for secret in "${REQUIRED_SECRETS[@]}"; do
    if gcloud secrets describe $secret --project=$PROJECT_ID &>/dev/null; then
        echo "  ✅ Secret '$secret' exists"
    else
        echo "  ❌ Secret '$secret' does NOT exist"
        exit 1
    fi
done

echo ""

# Check if secrets have active versions
echo "✓ Checking if secrets have active versions..."
for secret in "${REQUIRED_SECRETS[@]}"; do
    version_state=$(gcloud secrets versions list $secret --project=$PROJECT_ID --limit=1 --format="value(state)")
    if [ "$version_state" = "enabled" ]; then
        echo "  ✅ Secret '$secret' has an active version"
    else
        echo "  ❌ Secret '$secret' does NOT have an active version"
        exit 1
    fi
done

echo ""

# Check service account permissions
echo "✓ Checking service account permissions..."
# Default compute service account used by Cloud Run
SERVICE_ACCOUNT="997298514042-compute@developer.gserviceaccount.com"

if gcloud projects get-iam-policy $PROJECT_ID --flatten="bindings[].members" --format="table(bindings.role)" --filter="bindings.members:serviceAccount:$SERVICE_ACCOUNT AND bindings.role:roles/secretmanager.secretAccessor" | grep -q secretmanager.secretAccessor; then
    echo "  ✅ Service account '$SERVICE_ACCOUNT' has secretAccessor role"
else
    echo "  ❌ Service account '$SERVICE_ACCOUNT' does NOT have secretAccessor role"
    exit 1
fi

echo ""

# Test reading secrets (optional - only checks if you have access)
echo "✓ Testing secret access (checking if you can read secrets)..."
for secret in "${REQUIRED_SECRETS[@]}"; do
    if gcloud secrets versions access latest --secret=$secret --project=$PROJECT_ID &>/dev/null; then
        # Get length without revealing the value
        secret_length=$(gcloud secrets versions access latest --secret=$secret --project=$PROJECT_ID | wc -c)
        echo "  ✅ Can access '$secret' (length: $secret_length bytes)"
    else
        echo "  ❌ Cannot access '$secret'"
        exit 1
    fi
done

echo ""
echo "✅ All verifications passed! You're ready to deploy."
echo ""
echo "📝 Next steps:"
echo "   1. Update your application code to read from Secret Manager"
echo "   2. Deploy to Cloud Run with the verified service account"
echo "   3. Test the OAuth flow in the deployed environment"
