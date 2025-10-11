# Documentación del Proyecto RAG Legal Agent

Bienvenido a la documentación completa del Agente Legal con RAG (Retrieval Augmented Generation).

## 📚 Índice de Documentación

### Para Empezar

- **[Guía Rápida](04-GUIA-RAPIDA.md)** - Cómo usar el sistema rápidamente

### Arquitectura y Conceptos

- **[Arquitectura del Sistema](01-ARQUITECTURA.md)** - Entendiendo cómo funciona todo
- **[Arquitectura Completa](07-ARQUITECTURA-COMPLETA.md)** - Estructura detallada con supervisord, sesiones, multi-usuario
- **[Servicios de Google Cloud](06-SERVICIOS-GCP.md)** - Qué servicios usamos y por qué

### Deployment

- **[Despliegue del Agente Backend](02-DESPLIEGUE-AGENTE.md)** - Cómo se desplegó el agente en Agent Engine
- **[Despliegue de la Interfaz Web](03-DESPLIEGUE-WEB-UI.md)** - Cómo se desplegó la UI en Cloud Run

### Administración

- **[Administración del Sistema](05-ADMINISTRACION.md)** - Gestión de usuarios, actualizaciones, monitoreo

## 🎯 ¿Qué es este proyecto?

Este proyecto implementa un **agente conversacional especializado en análisis de contratos legales** usando:

- **RAG (Retrieval Augmented Generation)**: El agente busca información en documentos antes de responder
- **Gemini 2.5 Flash**: Modelo de IA de Google para generación de respuestas
- **Vertex AI Agent Engine**: Infraestructura serverless de Google para ejecutar agentes
- **ADK (Agent Development Kit)**: Framework de Google para desarrollar agentes
- **Cloud Run**: Servicio serverless para hospedar la interfaz web

## 🏗️ Arquitectura General

```
┌─────────────────┐
│   Usuarios      │
│  (navegador)    │
└────────┬────────┘
         │ HTTPS
         ↓
┌─────────────────────────────────┐
│   Cloud Run                     │
│   (ADK Web UI)                  │
│   Puerto: 8080                  │
└────────┬────────────────────────┘
         │ API Interna
         ↓
┌─────────────────────────────────┐
│   Vertex AI Agent Engine        │
│   (RAG Agent Backend)           │
│   - Gemini 2.5 Flash           │
│   - RAG Tools (7 herramientas) │
│   - Estado de sesiones         │
└────────┬────────────────────────┘
         │
         ↓
┌─────────────────────────────────┐
│   Vertex AI RAG                 │
│   (Corpus de documentos)        │
│   - Embeddings                  │
│   - Búsqueda semántica         │
└─────────────────────────────────┘
```

## 🔑 Conceptos Clave

### ¿Qué es RAG?

**RAG** (Retrieval Augmented Generation) es una técnica donde el agente:

1. **Busca** información relevante en documentos (Retrieval)
2. **Genera** una respuesta usando esa información (Generation)

**Ventaja**: El agente responde con información actualizada de tus documentos, no solo con su conocimiento pre-entrenado.

### ¿Qué es Agent Engine?

**Agent Engine** es la infraestructura de Google que:
- Ejecuta tu agente en la nube (serverless)
- Escala automáticamente según la demanda
- Mantiene el estado de las conversaciones
- Gestiona la autenticación y seguridad

### ¿Qué es ADK?

**ADK** (Agent Development Kit) es el framework de Google para:
- Desarrollar agentes con herramientas (tools)
- Conectar múltiples agentes entre sí
- Desplegar agentes fácilmente
- Proveer una interfaz web para testing

## 📂 Estructura del Proyecto

```
adk-rag-agent/
├── asistent/                    # Código del agente
│   ├── agent.py                # Definición del agente principal
│   ├── config.py               # Configuración (chunk size, embeddings, etc)
│   ├── __init__.py             # Inicialización de Vertex AI
│   └── tools/                  # Herramientas del agente
│       ├── rag_query.py        # Consultar documentos
│       ├── list_corpora.py     # Listar corpus disponibles
│       ├── create_corpus.py    # Crear nuevos corpus
│       ├── add_data.py         # Agregar documentos
│       ├── get_corpus_info.py  # Info de corpus
│       ├── delete_document.py  # Eliminar documentos
│       ├── delete_corpus.py    # Eliminar corpus
│       └── utils.py            # Utilidades compartidas
│
├── docs/                        # Documentación (estás aquí)
│
├── deploy.py                    # Script para desplegar el agente
├── Dockerfile.web              # Container para la UI web
├── cloudbuild.web.yaml         # Configuración de build
├── requirements.txt            # Dependencias Python
├── .env                        # Variables de entorno (local)
│
└── CLAUDE.md                   # Instrucciones para Claude Code
```

## 🚀 URLs Importantes

### Producción

- **Interfaz Web**: https://rag-legal-agent-ui-997298514042.us-central1.run.app
- **Agent Engine**: projects/997298514042/locations/us-central1/reasoningEngines/1053512459316363264

### Consolas de Administración

- **Cloud Run**: https://console.cloud.google.com/run?project=escribania-mastropasqua
- **Agent Engine**: https://console.cloud.google.com/vertex-ai/reasoning-engines?project=escribania-mastropasqua
- **IAM y Seguridad**: https://console.cloud.google.com/iam-admin?project=escribania-mastropasqua

## 💡 Próximos Pasos

1. Lee la **[Arquitectura](01-ARQUITECTURA.md)** para entender cómo funciona todo
2. Revisa los **[Servicios de GCP](06-SERVICIOS-GCP.md)** para entender qué estás usando
3. Consulta la **[Guía de Administración](05-ADMINISTRACION.md)** para aprender a gestionar el sistema

## 🆘 Soporte

- **Issues del proyecto ADK**: https://github.com/google/adk-python/issues
- **Documentación oficial ADK**: https://google.github.io/adk-docs
- **Vertex AI docs**: https://cloud.google.com/vertex-ai/docs

---

**Última actualización**: 2025-10-10
