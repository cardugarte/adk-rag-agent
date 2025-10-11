# Deployment de ADK Web UI con Autenticación Google

Esta guía te muestra cómo desplegar la interfaz web ADK para tu agente RAG Legal con autenticación de Google.

## 🎯 Qué vas a lograr

- ✅ Interfaz web completa de ADK accesible por URL pública
- ✅ Autenticación con Google (solo usuarios autorizados)
- ✅ Conexión directa con tu agente en Agent Engine
- ✅ Chat interactivo con historial de sesiones

## 📋 Prerequisitos

1. Agente ya desplegado en Agent Engine (✅ Ya lo tenés)
2. Google Cloud CLI configurado (✅ Ya lo tenés)
3. Permisos de administrador en el proyecto GCP

## 🚀 Paso 1: Desplegar la interfaz web

Ejecutá el script de deployment:

```bash
./deploy_web_ui.sh
```

Este script va a:
1. Construir una imagen Docker con ADK Web UI
2. Desplegarla en Cloud Run
3. Generar una URL pública

**Tiempo estimado:** 5-10 minutos

Al finalizar, verás algo como:

```
✅ Deployment complete!
🌐 Service URL: https://rag-legal-agent-ui-xxxxx-uc.a.run.app
```

⚠️ **IMPORTANTE:** En este punto, la URL es pública (cualquiera puede acceder). Seguí al Paso 2 para configurar autenticación.

## 🔐 Paso 2: Configurar autenticación con Google

Ejecutá el script de configuración de IAP:

```bash
./configure_iap.sh
```

Este script va a:
1. Requerir autenticación para acceder al servicio
2. Permitirte agregar usuarios autorizados (emails de Google)

Te va a pedir que ingreses los emails de los usuarios autorizados:

```
Email (or press Enter to finish): usuario1@gmail.com
   ✅ usuario1@gmail.com added

Email (or press Enter to finish): usuario2@gmail.com
   ✅ usuario2@gmail.com added

Email (or press Enter to finish): [Enter]
```

## 📝 Paso 3: Configurar OAuth Consent Screen (Primera vez)

Si es la primera vez que usás OAuth en el proyecto, necesitás configurar la pantalla de consentimiento:

1. Andá a: https://console.cloud.google.com/apis/credentials/consent?project=escribania-mastropasqua

2. Completá la información:
   - **App name:** RAG Legal Agent
   - **User support email:** Tu email
   - **Application home page:** La URL de Cloud Run
   - **Authorized domains:** `run.app`
   - **Developer contact information:** Tu email

3. Guardá y continuá

## 🎉 Paso 4: Usar la interfaz

1. Compartí la URL con los usuarios autorizados
2. Cuando accedan, van a ver la pantalla de login de Google
3. Después de autenticarse, van a ver la interfaz de ADK Web UI
4. Pueden empezar a chatear con el agente inmediatamente

## 🔧 Características de la interfaz

La interfaz ADK Web UI incluye:

- **Chat interactivo** con el agente
- **Historial de sesiones** persistente
- **Múltiples usuarios** simultáneos con sesiones aisladas
- **Eventos en tiempo real** mostrando el razonamiento del agente
- **Herramientas visibles** - podés ver qué herramientas usa el agente
- **Debug panel** para desarrolladores

## 🔄 Actualizar el agente

Si hacés cambios al agente y querés actualizarlo:

```bash
# 1. Re-desplegar el agente backend
python deploy.py

# 2. La interfaz se conecta automáticamente al nuevo agente
# No necesitás re-desplegar la interfaz web
```

## 👥 Administrar usuarios autorizados

### Agregar un nuevo usuario:

```bash
gcloud run services add-iam-policy-binding rag-legal-agent-ui \
    --region=us-central1 \
    --project=escribania-mastropasqua \
    --member="user:nuevo@gmail.com" \
    --role="roles/run.invoker"
```

### Remover un usuario:

```bash
gcloud run services remove-iam-policy-binding rag-legal-agent-ui \
    --region=us-central1 \
    --project=escribania-mastropasqua \
    --member="user:usuario@gmail.com" \
    --role="roles/run.invoker"
```

### Listar usuarios autorizados:

```bash
gcloud run services get-iam-policy rag-legal-agent-ui \
    --region=us-central1 \
    --project=escribania-mastropasqua
```

## 💰 Costos estimados

- **Cloud Run:** ~$0.05-0.10 por hora de uso activo
- **Agent Engine:** Según uso (consultas al agente)
- **Cloud Storage:** Almacenamiento de logs y datos

**Recomendación:** Configurá presupuestos y alertas en Google Cloud Console.

## 🐛 Troubleshooting

### Error: "Failed to authenticate"
- Verificá que el usuario esté en la lista de autorizados
- Revisá la configuración del OAuth consent screen

### Error: "Service not responding"
- Verificá los logs: `gcloud run logs read rag-legal-agent-ui --region=us-central1`
- Revisá que el Agent Engine esté activo

### La interfaz carga pero no responde
- Verificá el Agent Engine ID en el Dockerfile.web
- Revisá que tengas permisos en el proyecto

## 📞 Soporte

Para problemas con:
- **ADK Web UI:** https://github.com/google/adk-web/issues
- **Agent Engine:** https://cloud.google.com/vertex-ai/docs/agent-engine
- **Cloud Run:** https://cloud.google.com/run/docs

## 🔗 URLs útiles

- **Servicio Cloud Run:** https://console.cloud.google.com/run?project=escribania-mastropasqua
- **Agent Engine:** https://console.cloud.google.com/vertex-ai/reasoning-engines?project=escribania-mastropasqua
- **OAuth Config:** https://console.cloud.google.com/apis/credentials/consent?project=escribania-mastropasqua
