"""
Modern ASGI-based ADK Web Server with OAuth authentication middleware.
Compatible with google-adk >= 1.15.1

ARCHITECTURE:
- OAuth authentication via AuthMiddleware (validates session cookies)
- ADKStateInjectorMiddleware injects user_email into ADK session state
- Session state automatically includes user_email for tools
"""
import os
import logging
import json
from typing import Dict, Any, Optional, Callable
import uvicorn
from google.adk.cli.fast_api import get_fast_api_app
from asistent.auth_middleware import AuthMiddleware
from starlette.middleware.sessions import SessionMiddleware
from asistent.secrets import get_secret

logger = logging.getLogger(__name__)


class ADKStateInjectorMiddleware:
    """
    ASGI Middleware that injects authenticated user info into ADK requests.

    This middleware intercepts requests to ADK endpoints and modifies the
    request body to include user information in the session state initialization.

    This is the bridge between OAuth authentication (session cookies) and
    ADK's session management system.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        method = scope.get("method", "")

        # Only intercept POST requests to ADK query/run endpoints
        if method != "POST" or not ("/query" in path or "/run" in path):
            await self.app(scope, receive, send)
            return

        # Get authenticated user from session
        session = scope.get("session", {})
        user_info = session.get("user", {})
        user_email = user_info.get("email")

        if not user_email:
            # No authenticated user, let request proceed normally
            await self.app(scope, receive, send)
            return

        # Parse path to validate user_id
        try:
            path_parts = path.split("/")
            if "users" in path_parts:
                user_idx = path_parts.index("users") + 1
                requested_user_id = path_parts[user_idx]

                # SECURITY: Replace user_id in path with authenticated email
                path_parts[user_idx] = user_email
                scope["path"] = "/".join(path_parts)

                logger.info(f"ADK request user_id set to: {user_email}")

        except (ValueError, IndexError) as e:
            logger.warning(f"Could not parse user_id from path {path}: {e}")

        # Intercept and modify the request body
        original_receive = receive
        body_collected = []

        async def receive_wrapper():
            """Collect the request body."""
            message = await original_receive()
            if message["type"] == "http.request":
                body_collected.append(message.get("body", b""))
                if not message.get("more_body", False):
                    # All body received, modify it
                    try:
                        full_body = b"".join(body_collected)
                        if full_body:
                            body_data = json.loads(full_body.decode("utf-8"))

                            # Inject user info into state if not present
                            if "state" not in body_data:
                                body_data["state"] = {}

                            # Add user information
                            body_data["state"]["user_email"] = user_email
                            body_data["state"]["user_name"] = user_info.get("name", "")
                            body_data["state"]["user_picture"] = user_info.get("picture", "")

                            # Replace body
                            modified_body = json.dumps(body_data).encode("utf-8")
                            message["body"] = modified_body

                            logger.info(f"Injected user_email into ADK request state")

                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        logger.warning(f"Could not modify request body: {e}")

            return message

        # Continue with modified receive function
        await self.app(scope, receive_wrapper, send)


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
# 3. ADKStateInjectorMiddleware - injects user_email into ADK requests
# 4. FastAPI app (innermost) - actual ADK application

# Determine if running in production (Cloud Run) or locally
is_production = os.environ.get("K_SERVICE") is not None  # K_SERVICE exists in Cloud Run

app = SessionMiddleware(
    AuthMiddleware(
        ADKStateInjectorMiddleware(fastapi_app)  # NEW: Inject user state into ADK
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