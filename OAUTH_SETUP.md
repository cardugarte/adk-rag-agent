# Configuración OAuth para Google Login

## Paso 1: Crear OAuth 2.0 Credentials

1. Ir a: https://console.cloud.google.com/apis/credentials?project=escribania-mastropasqua

2. Click en **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**

3. Si es la primera vez, configurar la pantalla de consentimiento:
   - Click en **"CONFIGURE CONSENT SCREEN"**
   - Seleccionar **"Internal"** (si usás Google Workspace) o **"External"**
   - Completar:
     - App name: `RAG Legal Agent`
     - User support email: Tu email
     - Developer contact: Tu email
   - Click **"SAVE AND CONTINUE"** hasta el final

4. Volver a crear OAuth client ID:
   - Application type: **Web application**
   - Name: `RAG Legal Agent Web UI`
   - Authorized JavaScript origins:
     ```
     https://rag-legal-agent-ui-997298514042.us-central1.run.app
     ```
   - Authorized redirect URIs:
     ```
     https://rag-legal-agent-ui-997298514042.us-central1.run.app/authorize
     ```
   - Click **"CREATE"**

5. Copiar el **Client ID** y **Client Secret** que aparecen

## Paso 2: Configurar Variables de Entorno en Cloud Run

```bash
gcloud run services update rag-legal-agent-ui \
    --region=us-central1 \
    --project=escribania-mastropasqua \
    --set-env-vars="GOOGLE_CLIENT_ID=TU_CLIENT_ID,GOOGLE_CLIENT_SECRET=TU_CLIENT_SECRET"
```

Reemplazar `TU_CLIENT_ID` y `TU_CLIENT_SECRET` con los valores del paso anterior.

## Paso 3: Deploy

Una vez configuradas las credenciales, ejecutar:

```bash
gcloud run deploy rag-legal-agent-ui \
    --source=. \
    --region=us-central1 \
    --project=escribania-mastropasqua \
    --port=8080 \
    --memory=2Gi \
    --cpu=2 \
    --timeout=3600
```

## Verificación

Acceder a: https://rag-legal-agent-ui-997298514042.us-central1.run.app

Deberías ver la página de login con el botón "Iniciar sesión con Google".
