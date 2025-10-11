"""
Modern ASGI-based ADK Web Server with OAuth authentication middleware.
Compatible with google-adk >= 1.15.1
"""
import os
import uvicorn
from google.adk.cli.fast_api import get_fast_api_app
from asistent.auth_middleware import AuthMiddleware
from starlette.middleware.sessions import SessionMiddleware
from asistent.secrets import get_secret

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
app = SessionMiddleware(
    AuthMiddleware(fastapi_app),
    secret_key=get_secret("flask-secret-key"),
    max_age=None,  # Session cookie - expires when browser closes
    same_site="lax",  # CSRF protection
    https_only=True  # Only send cookie over HTTPS (important for production)
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)