#!/bin/bash

# OAuth Configuration Verification Script
# This script verifies that all OAuth configuration is correct for Cloud Run deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-escribania-mastropasqua}"
REGION="${GOOGLE_CLOUD_LOCATION:-us-central1}"
SERVICE_NAME="adk-default-service-name"

echo -e "${BLUE}=== OAuth Configuration Verification ===${NC}\n"

echo -e "${BLUE}Project:${NC} $PROJECT_ID"
echo -e "${BLUE}Region:${NC} $REGION"
echo -e "${BLUE}Service:${NC} $SERVICE_NAME\n"

# Function to print status
print_status() {
    local status=$1
    local message=$2

    if [ "$status" == "OK" ]; then
        echo -e "${GREEN}✓${NC} $message"
    elif [ "$status" == "WARN" ]; then
        echo -e "${YELLOW}⚠${NC} $message"
    else
        echo -e "${RED}✗${NC} $message"
    fi
}

# 1. Check if gcloud is configured
echo -e "${BLUE}[1/7] Checking gcloud configuration...${NC}"
if gcloud config get-value project &> /dev/null; then
    CURRENT_PROJECT=$(gcloud config get-value project)
    if [ "$CURRENT_PROJECT" == "$PROJECT_ID" ]; then
        print_status "OK" "gcloud configured for project: $CURRENT_PROJECT"
    else
        print_status "WARN" "Current project is $CURRENT_PROJECT, expected $PROJECT_ID"
        echo "      Run: gcloud config set project $PROJECT_ID"
    fi
else
    print_status "ERROR" "gcloud not configured"
    exit 1
fi
echo ""

# 2. Check if secrets exist
echo -e "${BLUE}[2/7] Checking Secret Manager secrets...${NC}"

REQUIRED_SECRETS=("google-client-id" "google-client-secret" "drive-root-folder-id")
ALL_SECRETS_EXIST=true

for secret in "${REQUIRED_SECRETS[@]}"; do
    if gcloud secrets describe "$secret" --project="$PROJECT_ID" &> /dev/null; then
        print_status "OK" "Secret exists: $secret"
    else
        print_status "ERROR" "Secret missing: $secret"
        ALL_SECRETS_EXIST=false
    fi
done

if [ "$ALL_SECRETS_EXIST" = false ]; then
    echo -e "\n${YELLOW}To create missing secrets, see: docs/OAUTH_CONFIGURATION.md${NC}"
fi
echo ""

# 3. Verify secret values (partial)
echo -e "${BLUE}[3/7] Verifying secret values...${NC}"

# Check google-client-id format
CLIENT_ID=$(gcloud secrets versions access latest --secret="google-client-id" --project="$PROJECT_ID" 2>/dev/null || echo "")
if [ -n "$CLIENT_ID" ]; then
    if [[ "$CLIENT_ID" =~ \.apps\.googleusercontent\.com$ ]]; then
        print_status "OK" "google-client-id format is valid"
        echo "      Client ID: ${CLIENT_ID:0:30}...${CLIENT_ID: -30}"
    else
        print_status "ERROR" "google-client-id format is invalid (should end with .apps.googleusercontent.com)"
    fi
else
    print_status "ERROR" "Cannot access google-client-id"
fi

# Check google-client-secret exists and is not empty
CLIENT_SECRET=$(gcloud secrets versions access latest --secret="google-client-secret" --project="$PROJECT_ID" 2>/dev/null || echo "")
if [ -n "$CLIENT_SECRET" ] && [ ${#CLIENT_SECRET} -gt 10 ]; then
    print_status "OK" "google-client-secret exists and is not empty"
else
    print_status "ERROR" "google-client-secret is missing or empty"
fi

# Check drive-root-folder-id
DRIVE_FOLDER=$(gcloud secrets versions access latest --secret="drive-root-folder-id" --project="$PROJECT_ID" 2>/dev/null || echo "")
if [ -n "$DRIVE_FOLDER" ]; then
    print_status "OK" "drive-root-folder-id exists"
    echo "      Folder ID: $DRIVE_FOLDER"
else
    print_status "ERROR" "drive-root-folder-id is missing or empty"
fi
echo ""

# 4. Check if Cloud Run service exists
echo -e "${BLUE}[4/7] Checking Cloud Run service...${NC}"

if gcloud run services describe "$SERVICE_NAME" --region="$REGION" --project="$PROJECT_ID" &> /dev/null; then
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)")
    print_status "OK" "Cloud Run service exists"
    echo "      Service URL: $SERVICE_URL"

    # Check if service is publicly accessible
    ALLOW_UNAUTH=$(gcloud run services get-iam-policy "$SERVICE_NAME" --region="$REGION" --project="$PROJECT_ID" --format="value(bindings.members)" 2>/dev/null | grep -c "allUsers" || echo "0")
    if [ "$ALLOW_UNAUTH" -gt 0 ]; then
        print_status "OK" "Service allows unauthenticated access"
    else
        print_status "WARN" "Service requires authentication"
        echo "      Run: gcloud run services add-iam-policy-binding $SERVICE_NAME --region=$REGION --member='allUsers' --role='roles/run.invoker' --project=$PROJECT_ID"
    fi
else
    print_status "WARN" "Cloud Run service not found (not deployed yet?)"
    SERVICE_URL="https://$SERVICE_NAME-PROJECT_NUMBER.$REGION.run.app"
    echo "      Expected URL pattern: $SERVICE_URL"
fi
echo ""

# 5. Check required APIs
echo -e "${BLUE}[5/7] Checking enabled APIs...${NC}"

REQUIRED_APIS=(
    "run.googleapis.com"
    "secretmanager.googleapis.com"
    "drive.googleapis.com"
    "docs.googleapis.com"
    "aiplatform.googleapis.com"
)

for api in "${REQUIRED_APIS[@]}"; do
    if gcloud services list --enabled --project="$PROJECT_ID" --format="value(config.name)" 2>/dev/null | grep -q "^$api$"; then
        print_status "OK" "API enabled: $api"
    else
        print_status "WARN" "API not enabled: $api"
        echo "      Run: gcloud services enable $api --project=$PROJECT_ID"
    fi
done
echo ""

# 6. Check OAuth redirect URIs (manual verification required)
echo -e "${BLUE}[6/7] OAuth Redirect URI Configuration${NC}"
echo -e "${YELLOW}⚠${NC} Manual verification required in Google Cloud Console"
echo ""
echo "Visit: https://console.cloud.google.com/apis/credentials?project=$PROJECT_ID"
echo ""
if [ -n "$SERVICE_URL" ]; then
    echo "Verify these redirect URIs are configured:"
    echo "  1. $SERVICE_URL/oauth2callback"
    echo "  2. $SERVICE_URL/auth/callback"
    echo "  3. http://localhost:8000/oauth2callback (for local dev)"
    echo "  4. http://localhost:8000/auth/callback (for local dev)"
else
    echo "Deploy the service first to get the Service URL, then configure redirect URIs"
fi
echo ""

# 7. Service Account Permissions
echo -e "${BLUE}[7/7] Checking Service Account permissions...${NC}"

if gcloud run services describe "$SERVICE_NAME" --region="$REGION" --project="$PROJECT_ID" &> /dev/null; then
    SERVICE_ACCOUNT=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --project="$PROJECT_ID" --format="value(spec.template.spec.serviceAccountName)")

    if [ -n "$SERVICE_ACCOUNT" ]; then
        print_status "OK" "Service Account: $SERVICE_ACCOUNT"

        # Check if SA has Secret Manager access
        echo "      Checking Secret Manager access..."
        for secret in "${REQUIRED_SECRETS[@]}"; do
            if gcloud secrets get-iam-policy "$secret" --project="$PROJECT_ID" --format="value(bindings.members)" 2>/dev/null | grep -q "$SERVICE_ACCOUNT"; then
                print_status "OK" "  Has access to: $secret"
            else
                print_status "WARN" "  Missing access to: $secret"
                echo "        Run: gcloud secrets add-iam-policy-binding $secret --member='serviceAccount:$SERVICE_ACCOUNT' --role='roles/secretmanager.secretAccessor' --project=$PROJECT_ID"
            fi
        done
    else
        print_status "WARN" "Using default service account"
    fi
else
    print_status "WARN" "Service not deployed yet, cannot check service account"
fi
echo ""

# Summary
echo -e "${BLUE}=== Summary ===${NC}\n"

if [ -n "$SERVICE_URL" ]; then
    echo -e "${GREEN}Next Steps:${NC}"
    echo "1. Verify OAuth redirect URIs in Google Cloud Console"
    echo "2. Test the OAuth flow by accessing: $SERVICE_URL"
    echo "3. Try saving a document to trigger OAuth"
    echo ""
    echo -e "${BLUE}View logs:${NC}"
    echo "gcloud run services logs read $SERVICE_NAME --region=$REGION --project=$PROJECT_ID --limit=50"
else
    echo -e "${YELLOW}Deploy the service first:${NC}"
    echo "adk deploy cloud_run --project=$PROJECT_ID --region=$REGION --with_ui asistent/"
fi

echo ""
echo -e "${BLUE}Full documentation:${NC} docs/OAUTH_CONFIGURATION.md"
