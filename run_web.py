"""
Modern ASGI-based ADK Web Server with OAuth authentication middleware.
Compatible with google-adk >= 1.15.1

ARCHITECTURE:
- OAuth authentication via AuthMiddleware (validates session cookies)
- Service Account with Application Default Credentials for Drive access
- No user_email injection needed - Service Account has direct access
"""
import os
import logging
import uvicorn
from google.adk.cli.fast_api import get_fast_api_app
from asistent.auth_middleware import AuthMiddleware
from starlette.middleware.sessions import SessionMiddleware
from asistent.secrets import get_secret

logger = logging.getLogger(__name__)


# Get the ADK FastAPI app
# This creates the complete ADK web server with all agents in the current directory
fastapi_app = get_fast_api_app(
    agents_dir=".",  # Current directory contains asistent package
    web=True,  # Enable web UI
    allow_origins=["*"],  # Allow CORS for development
    reload_agents=False,  # Don't reload agents in production
)

# Wrap the FastAPI app with authentication middleware
# Note: Middleware wrapping order matters!
# 1. SessionMiddleware (outermost) - manages cookies
# 2. AuthMiddleware - validates authentication
# 3. FastAPI app (innermost) - actual ADK application

# Determine if running in production (Cloud Run) or locally
is_production = os.environ.get("K_SERVICE") is not None  # K_SERVICE exists in Cloud Run

app = SessionMiddleware(
    AuthMiddleware(
        fastapi_app
    ),
    secret_key=get_secret("flask-secret-key"),
    max_age=3600,  # 1 hour session expiration (OAuth flow needs time)
    same_site="none" if is_production else "lax",  # "none" for Cloud Run OAuth, "lax" for local
    https_only=is_production,  # Only require HTTPS in production
    path="/"  # Ensure cookies are sent for all paths
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)