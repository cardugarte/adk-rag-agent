# Arquitectura Completa del Sistema

## Estructura del Contenedor

### Cloud Run Container (4Gi RAM, 2 CPUs)

```
┌─────────────────────────────────────────────────────────────┐
│ Cloud Run Container                                         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ supervisord (PID 1)                                  │  │
│  │                                                       │  │
│  │  ┌────────────────────┐  ┌─────────────────────┐   │  │
│  │  │ Flask              │  │ ADK Web             │   │  │
│  │  │ Port: 8080 (public)│  │ Port: 8081 (interno)│   │  │
│  │  │                    │  │                     │   │  │
│  │  │ • OAuth Google     │  │ • UI Angular        │   │  │
│  │  │ • Sesiones cookies │  │ • Proxy a Agent     │   │  │
│  │  │ • Whitelist users  │  │ • WebSockets        │   │  │
│  │  │ • Proxy reverso    │  │                     │   │  │
│  │  └────────────────────┘  └─────────────────────┘   │  │
│  │         ↓                          ↓                 │  │
│  │    localhost:8080            localhost:8081          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                               ↓
        ┌──────────────────────────────────────┐
        │ Internet                             │
        │ https://rag-legal-agent-ui....run.app│
        └──────────────────────────────────────┘
                               ↓
                  ┌────────────────────────┐
                  │ Vertex AI Agent Engine │
                  │ ID: 1053512459316363264│
                  │                        │
                  │ • Gemini 2.5 Flash     │
                  │ • RAG Corpus           │
                  │ • Session Storage      │
                  └────────────────────────┘
```

## Componentes

### 1. Supervisord

**Rol:** Gestor de procesos

**Responsabilidades:**
- Iniciar Flask y ADK Web al arrancar el contenedor
- Mantener ambos procesos corriendo
- Reiniciar procesos si fallan
- Gestionar logs de ambos servicios

**Configuración:** `/etc/supervisor/conf.d/supervisord.conf`

```ini
[program:flask]
command=python main.py
port=8080

[program:adk-web]
command=adk web --port=8081 --session_service_uri=agentengine://...
startsecs=30
```

### 2. Flask (Puerto 8080)

**Rol:** Autenticación y proxy reverso

**Responsabilidades:**
- OAuth 2.0 con Google
- Validación de whitelist de usuarios
- Gestión de sesiones de autenticación (cookies)
- Proxy a ADK Web (puerto 8081)
- Middleware ProxyFix para HTTPS

**Stack:**
- Flask
- Authlib (OAuth)
- Werkzeug ProxyFix
- Requests (proxy HTTP)

**Rutas:**
- `/login-page` - Página de login
- `/login` - Inicia flujo OAuth
- `/authorize` - Callback de OAuth
- `/logout` - Cierra sesión
- `/<path>` - Proxy a ADK Web (requiere autenticación)

### 3. ADK Web (Puerto 8081)

**Rol:** Interfaz de chat con Agent Engine

**Responsabilidades:**
- UI Angular para chat
- Conexión WebSocket con Agent Engine
- Gestión de sesiones de chat
- Streaming de respuestas del agente

**Stack:**
- Google ADK
- Angular (frontend)
- Uvicorn (ASGI server)
- Vertex AI SDK

**Tiempo de inicio:** ~30-60 segundos (cold start)

## Flujo de una Request

### 1. Login Flow

```
Usuario abre URL
    ↓
Flask: GET /
    ↓
¿Tiene cookie válida?
    ↓ NO
Redirige a /login-page
    ↓
Usuario click "Login con Google"
    ↓
Flask: GET /login
    ↓
Redirige a Google OAuth
    ↓
Usuario se autentica en Google
    ↓
Google redirige a /authorize?code=...
    ↓
Flask: Intercambia code por token
    ↓
Obtiene email del usuario
    ↓
¿Email en whitelist?
    ↓ SÍ
Crea cookie firmada: session['user']
    ↓
Redirige a /
```

### 2. Chat Flow

```
Usuario ya autenticado: GET /
    ↓
Flask: Valida cookie
    ↓ Cookie válida ✅
Proxy request a localhost:8081/
    ↓
ADK Web: Recibe request
    ↓
Identifica user_id del request
    ↓
Busca/crea session en Agent Engine
    ↓
Envía mensaje a Agent Engine
    ↓
Agent Engine:
  - Consulta RAG corpus
  - Genera respuesta con Gemini
  - Actualiza historial de sesión
    ↓
ADK Web: Recibe respuesta (streaming)
    ↓
Flask: Proxy respuesta al usuario
    ↓
Usuario ve respuesta en chat
```

## Gestión de Sesiones

### Sesiones de Autenticación (Flask)

**Tecnología:** Cookies firmadas con SECRET_KEY

**Datos almacenados:**
```python
session['user'] = {
    'email': 'carlos@xplorers.ar',
    'name': 'Carlos Dugarte',
    'picture': 'https://lh3.googleusercontent.com/...'
}
```

**Características:**
- ✅ Almacenadas en cookie del navegador
- ✅ Firmadas con SECRET_KEY (no falsificables)
- ✅ Independientes por usuario
- ✅ Persistentes entre reinicios de Cloud Run
- ✅ Funcionan con múltiples instancias de Cloud Run

**Seguridad:**
- SECRET_KEY en variable de entorno
- Cookie HttpOnly (no accesible desde JavaScript)
- Cookie Secure (solo HTTPS)
- CSRF protection con state token

### Sesiones de Chat (Agent Engine)

**Tecnología:** Vertex AI Agent Engine

**Creación de sesión:**
```python
session = await agent.async_create_session(
    user_id="carlos@xplorers.ar"
)
# Retorna: {'id': 'session-abc123...'}
```

**Envío de mensaje:**
```python
response = agent.async_stream_query(
    message="¿Qué contratos tengo?",
    user_id="carlos@xplorers.ar",
    session_id="session-abc123"
)
```

**Características:**
- ✅ Almacenadas en Vertex AI (no en el contenedor)
- ✅ Persistentes incluso si Cloud Run se reinicia
- ✅ Historial completo de conversación
- ✅ Independientes por user_id + session_id
- ✅ Múltiples sesiones por usuario

**Estructura de sesión:**
```json
{
  "id": "session-abc123",
  "user_id": "carlos@xplorers.ar",
  "created_at": "2025-10-10T17:54:00Z",
  "messages": [
    {
      "role": "user",
      "content": "¿Qué documentos tienes?",
      "timestamp": "2025-10-10T17:54:05Z"
    },
    {
      "role": "assistant",
      "content": "Tengo acceso a contratos, poderes...",
      "timestamp": "2025-10-10T17:54:08Z"
    }
  ],
  "context": {...}
}
```

## Escenarios Multi-Usuario

### Escenario 1: Múltiples usuarios simultáneos

```
Carlos (Chrome)
  Cookie: email=carlos@xplorers.ar
  → Flask valida ✅
  → Proxy a ADK Web
  → Agent Engine:
      user_id: "carlos@xplorers.ar"
      session_id: "session-carlos-1"
      historial: [msg1, msg2, msg3]

María (Firefox)
  Cookie: email=escribania@mastropasqua.ar
  → Flask valida ✅
  → Proxy a ADK Web
  → Agent Engine:
      user_id: "escribania@mastropasqua.ar"
      session_id: "session-maria-1"
      historial: [msg-a, msg-b, msg-c]
```

**Resultado:**
- ✅ Sesiones completamente aisladas
- ✅ Historiales independientes
- ✅ Sin cruce de información

### Escenario 2: Mismo usuario, múltiples pestañas

```
Carlos - Pestaña 1
  Cookie compartida (mismo navegador)
  → session_id: "session-carlos-1"
  → Historial: [msg1, msg2, msg3]

Carlos - Pestaña 2
  Cookie compartida (mismo navegador)
  → session_id: "session-carlos-1" (MISMA)
  → Historial: [msg1, msg2, msg3] (COMPARTIDO)
```

**Resultado:**
- ✅ Mismo historial en ambas pestañas
- ✅ Sincronización automática
- ✅ Coherencia de conversación

### Escenario 3: Cloud Run escala a múltiples instancias

```
Container 1
  Flask + ADK Web
  SECRET_KEY: "abc123..." (env var)
  → Valida cookie de Carlos ✅
  → Proxy a Agent Engine

Container 2
  Flask + ADK Web
  SECRET_KEY: "abc123..." (MISMA env var)
  → Valida cookie de María ✅
  → Proxy a Agent Engine

Agent Engine (único, compartido)
  ├── Session Carlos: "session-carlos-1"
  └── Session María: "session-maria-1"
```

**Resultado:**
- ✅ Cookies válidas en cualquier instancia
- ✅ Sesiones centralizadas en Agent Engine
- ✅ Escalamiento transparente

## Persistencia y Durabilidad

### ¿Qué pasa si Cloud Run se reinicia?

| Componente | ¿Se pierde? | Impacto en usuario |
|------------|-------------|-------------------|
| Flask (proceso) | ✅ Sí | Ninguno (cookie en navegador) |
| ADK Web (proceso) | ✅ Sí | Reconexión automática |
| Cookie de autenticación | ❌ No | Usuario sigue logueado |
| Sesión de chat | ❌ No | Historial preservado |
| Historial de mensajes | ❌ No | Todo en Vertex AI |

### Almacenamiento del Historial

**Ubicación:** Vertex AI Agent Engine (managed storage)

**Retención:**
- Según políticas del proyecto de GCP
- Configurable en Agent Engine settings
- Default: Indefinido hasta eliminación manual

**Acceso:**
```python
# Obtener sesión existente
session = agent.get_session(
    user_id="carlos@xplorers.ar",
    session_id="session-abc123"
)

# Listar sesiones de un usuario
sessions = agent.list_sessions(
    user_id="carlos@xplorers.ar"
)
```

## Seguridad

### Autenticación

**OAuth 2.0 con Google:**
- Authorization Code Flow
- HTTPS obligatorio
- State token para prevenir CSRF
- Token validation con Google

**Whitelist de usuarios:**
```python
ALLOWED_USERS = [
    'carlos@xplorers.ar',
    'escribania@mastropasqua.ar',
    'escribaniamastropasqua@gmail.com',
    'camib.milone@gmail.com'
]
```

### Aislamiento de Sesiones

**Nivel Flask:**
- Cookies firmadas con SECRET_KEY
- HttpOnly cookies (anti-XSS)
- Secure cookies (solo HTTPS)
- SameSite cookies (anti-CSRF)

**Nivel Agent Engine:**
- Separación por user_id
- Session IDs únicos y aleatorios
- Sin acceso cross-user

**Validación:**
```python
@login_required
def proxy_adk(path=''):
    # Solo usuarios autenticados llegan aquí
    # session['user']['email'] validado previamente
    ...
```

### Network Security

**Flujo de tráfico:**
```
Internet (HTTPS)
    ↓
Cloud Load Balancer
    ↓
Cloud Run Container (puerto 8080)
    ↓
Flask (localhost:8080)
    ↓
ADK Web (localhost:8081) - NO EXPUESTO
    ↓
Vertex AI Agent Engine (private Google network)
```

**Puertos expuestos:**
- ✅ 8080: Público (Flask con OAuth)
- ❌ 8081: Interno (ADK Web no accesible desde internet)

## Variables de Entorno

### Variables Requeridas

```bash
# OAuth
GOOGLE_CLIENT_ID=...apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=...

# Flask
SECRET_KEY=<random-32-bytes-hex>

# GCP
GOOGLE_CLOUD_PROJECT=escribania-mastropasqua
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=TRUE

# Agent Engine
AGENT_ENGINE_ID=1053512459316363264

# Cloud Run
PORT=8080
```

### Configuración en Cloud Run

```bash
gcloud run services update rag-legal-agent-ui \
    --region=us-central1 \
    --update-env-vars="GOOGLE_CLIENT_ID=...,GOOGLE_CLIENT_SECRET=...,SECRET_KEY=..."
```

## Tiempos de Inicio

### Cold Start (primer acceso después de deploy o inactividad)

| Componente | Tiempo | Razón |
|------------|--------|-------|
| Container pull | ~10s | Descarga imagen Docker (4Gi) |
| Supervisord start | ~2s | Inicia gestor de procesos |
| Flask start | ~2s | Carga dependencias Python |
| ADK Web start | ~30-60s | Conecta a Vertex AI |
| **Total** | **~45-75s** | Primera vez |

### Warm Start (container ya iniciado)

| Componente | Tiempo | Razón |
|------------|--------|-------|
| Request processing | ~100ms | Flask + ADK Web listos |
| Agent response | Variable | Depende de complejidad |
| **Total** | **~100ms + agent** | Requests subsiguientes |

### Optimización

**Min instances = 1:**
```bash
gcloud run services update rag-legal-agent-ui \
    --region=us-central1 \
    --min-instances=1
```

**Costo:** ~$15/mes adicional
**Beneficio:** Sin cold starts para usuarios

## Costos Mensuales Estimados

| Recurso | Configuración | Costo Base | Costo por Uso |
|---------|--------------|------------|---------------|
| Cloud Run | 4Gi RAM, 2 CPU | $0 (scale to zero) | $0.10/hora activa |
| Agent Engine | Gemini 2.5 Flash | $0 | $0.03/hora ejecución |
| Vertex AI RAG | Embeddings + storage | ~$5 | $0.025/1K tokens |
| Logging | Cloud Logging | Gratis (50GB) | $0.50/GB extra |
| Networking | Egress | Incluido | $0.12/GB |
| **Total Estimado** | - | **~$5-10/mes** | **+uso** |

**Con tráfico moderado (10 horas/día):**
- Cloud Run: $30/mes
- Agent Engine: $10/mes
- RAG: $5/mes
- **Total: ~$45-50/mes**

## Monitoreo

### Logs de Supervisord

```bash
gcloud run services logs read rag-legal-agent-ui \
    --region=us-central1 \
    --limit=50 | grep supervisor
```

### Logs de Flask

```bash
gcloud run services logs read rag-legal-agent-ui \
    --region=us-central1 \
    --limit=50 | grep flask
```

### Logs de ADK Web

```bash
gcloud run services logs read rag-legal-agent-ui \
    --region=us-central1 \
    --limit=50 | grep "adk\|ADK"
```

### Métricas de Cloud Run

```bash
gcloud monitoring time-series list \
    --filter='resource.type="cloud_run_revision"' \
    --project=escribania-mastropasqua
```

## Troubleshooting

### Usuario ve "Iniciando el Agente..." por más de 2 minutos

**Causa:** ADK Web no logra conectar a Agent Engine

**Solución:**
```bash
# Ver logs de ADK Web
gcloud run services logs read rag-legal-agent-ui \
    --region=us-central1 \
    --limit=100

# Reiniciar servicio
gcloud run services update rag-legal-agent-ui \
    --region=us-central1 \
    --clear-env-vars \
    --set-env-vars="$(cat env-vars.txt)"
```

### Error "redirect_uri_mismatch" en OAuth

**Causa:** URI mal configurado en Google Cloud Console

**Solución:**
```
1. Ir a: https://console.cloud.google.com/apis/credentials
2. Editar OAuth client
3. Verificar Authorized redirect URI:
   https://rag-legal-agent-ui-997298514042.us-central1.run.app/authorize
```

### Cookie de sesión no persiste

**Causa:** SECRET_KEY cambia entre reinicios

**Solución:**
```bash
# Verificar que SECRET_KEY esté en env vars
gcloud run services describe rag-legal-agent-ui \
    --region=us-central1 \
    --format="value(spec.template.spec.containers[0].env)"
```

### ADK Web no responde (503)

**Causa:** Proceso caído o no iniciado

**Solución:**
```bash
# Ver estado de supervisord
gcloud run services logs read rag-legal-agent-ui \
    --region=us-central1 \
    --limit=20 | grep "entered RUNNING"

# Si no hay "adk-web entered RUNNING", revisar errores:
gcloud run services logs read rag-legal-agent-ui \
    --region=us-central1 \
    --limit=100 | grep ERROR
```

## Referencias

- **Cloud Run**: https://cloud.google.com/run/docs
- **Vertex AI Agent Engine**: https://cloud.google.com/vertex-ai/docs/agent-engine
- **ADK Documentation**: https://google.github.io/adk-docs
- **Supervisord**: http://supervisord.org/
- **Flask OAuth**: https://docs.authlib.org/en/latest/client/flask.html
