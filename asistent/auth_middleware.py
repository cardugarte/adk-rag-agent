
import os
import time
from starlette.applications import Starlette
from starlette.responses import RedirectResponse, HTMLResponse
from starlette.routing import Route
from authlib.integrations.starlette_client import OAuth
from authlib.common.security import generate_token
from asistent.secrets import get_secret
from asistent.tools.token_manager import TokenManager

# --- HTML Templates ---
LOGIN_PAGE_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Acceso al Agente Legal RAG</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }

        .login-card {
            background: white;
            border-radius: 20px;
            padding: 60px 50px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 480px;
            width: 100%;
            text-align: center;
            animation: slideUp 0.5s ease-out;
        }

        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .logo {
            width: 80px;
            height: 80px;
            margin: 0 auto 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }

        .logo svg {
            width: 45px;
            height: 45px;
            fill: white;
        }

        h1 {
            color: #1a1a1a;
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 12px;
            line-height: 1.3;
        }

        .subtitle {
            color: #6b7280;
            font-size: 16px;
            margin-bottom: 40px;
            line-height: 1.5;
        }

        .google-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: white;
            color: #3c4043;
            border: 2px solid #dadce0;
            border-radius: 12px;
            padding: 16px 32px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            width: 100%;
            gap: 12px;
        }

        .google-btn:hover {
            background: #f8f9fa;
            border-color: #4285f4;
            box-shadow: 0 4px 12px rgba(66, 133, 244, 0.2);
            transform: translateY(-2px);
        }

        .google-btn:active {
            transform: translateY(0);
        }

        .google-icon {
            width: 24px;
            height: 24px;
        }

        .security-note {
            margin-top: 30px;
            padding-top: 30px;
            border-top: 1px solid #e5e7eb;
            color: #6b7280;
            font-size: 13px;
            line-height: 1.6;
        }

        .security-icon {
            display: inline-block;
            margin-right: 6px;
            color: #10b981;
        }

        @media (max-width: 600px) {
            .login-card {
                padding: 40px 30px;
            }

            h1 {
                font-size: 24px;
            }

            .subtitle {
                font-size: 14px;
            }
        }
    </style>
</head>
<body>
    <div class="login-card">
        <div class="logo">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5zm0 18c-4.41 0-8-3.59-8-8V8.41l8-4 8 4V12c0 4.41-3.59 8-8 8z"/>
                <path d="M10.5 13.5l-2.5-2.5-1.5 1.5 4 4 7-7-1.5-1.5z"/>
            </svg>
        </div>

        <h1>Agente Legal Inteligente</h1>
        <p class="subtitle">Sistema especializado en análisis y generación de contratos legales</p>

        <a href="/login" class="google-btn">
            <img class="google-icon" src="https://developers.google.com/identity/images/g-logo.png" alt="Google">
            <span>Continuar con Google</span>
        </a>

        <div class="security-note">
            <span class="security-icon">🔒</span>
            <strong>Acceso seguro y privado.</strong> Solo usuarios autorizados pueden acceder al sistema.
        </div>
    </div>
</body>
</html>
"""

UNAUTHORIZED_PAGE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Acceso Denegado</title>
    <style>
        body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f0f2f5; margin: 0; }
        .container { text-align: center; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        h1 { color: #d9534f; }
        p { color: #333; }
        a { color: #007bff; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Acceso Denegado</h1>
        <p>El usuario <strong>{email}</strong> no está autorizado para acceder a esta aplicación.</p>
        <p><a href="/logout">Intentar con otra cuenta</a></p>
    </div>
</body>
</html>
"""

# --- OAuth and Auth Logic ---
oauth = OAuth()
oauth.register(
    name='google',
    client_id=get_secret("google-client-id"),
    client_secret=get_secret("google-client-secret"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile '
                 'https://www.googleapis.com/auth/drive.file '
                 'https://www.googleapis.com/auth/documents'
    }
)

async def login(request):
    """
    Initiate OAuth2 login flow with PKCE and state parameter.

    SECURITY:
    - PKCE (code_verifier/code_challenge) prevents authorization code interception
    - State parameter prevents CSRF attacks
    """
    # Force HTTPS for Cloud Run (behind proxy)
    redirect_uri = request.url_for('authorize')
    # Replace http:// with https:// when behind a proxy
    redirect_uri = str(redirect_uri).replace('http://', 'https://')

    # Generate PKCE code verifier (48 bytes = secure random string)
    code_verifier = generate_token(48)
    request.session['code_verifier'] = code_verifier

    # Generate state parameter for CSRF protection (32 bytes)
    state = generate_token(32)
    request.session['oauth_state'] = state

    return await oauth.google.authorize_redirect(
        request,
        redirect_uri,
        code_challenge=code_verifier,
        code_challenge_method='S256',
        state=state
    )

async def authorize(request):
    """
    Handle OAuth2 callback and store tokens securely.

    SECURITY:
    - Verifies state parameter (CSRF protection)
    - Verifies PKCE code verifier
    - Stores tokens in Secret Manager (NOT in session/cookies)
    - Only stores user info in session
    """
    # SECURITY: Verify state parameter to prevent CSRF
    expected_state = request.session.pop('oauth_state', None)
    received_state = request.query_params.get('state')

    if not expected_state or expected_state != received_state:
        return HTMLResponse(
            "<h1>Error de Seguridad</h1>"
            "<p>El parámetro 'state' no coincide. Posible ataque CSRF detectado.</p>"
            "<p><a href='/login-page'>Volver a intentar</a></p>",
            status_code=403
        )

    # SECURITY: Retrieve PKCE code verifier
    code_verifier = request.session.pop('code_verifier', None)

    # Exchange authorization code for tokens
    token = await oauth.google.authorize_access_token(
        request,
        code_verifier=code_verifier
    )
    user_info = token.get('userinfo')

    if user_info:
        email = user_info.get('email')
        allowed_users_str = get_secret("allowed-users-list")
        allowed_users = [e.strip() for e in allowed_users_str.split(",")]

        if email not in allowed_users:
            return HTMLResponse(UNAUTHORIZED_PAGE_HTML.format(email=email), status_code=403)

        # SECURITY: Store ONLY user info in session (NO tokens)
        request.session['user'] = {
            'email': email,
            'name': user_info.get('name'),
            'picture': user_info.get('picture'),
            'session_start': int(time.time())  # For auditing
        }

        # SECURITY: Store tokens in Secret Manager (encrypted at-rest)
        try:
            token_manager = TokenManager(os.environ.get('GOOGLE_CLOUD_PROJECT'))
            expires_in = token.get('expires_in', 3600)
            expires_at = int(time.time()) + expires_in

            token_manager.store_user_tokens(
                user_email=email,
                access_token=token.get('access_token'),
                refresh_token=token.get('refresh_token'),
                expires_at=expires_at
            )
        except Exception as e:
            # Log error but don't fail the login
            # User can still use the app, Drive operations will fail gracefully
            import logging
            logging.error(f"Failed to store tokens for {email}: {str(e)}")

        return RedirectResponse(url='/')

    return HTMLResponse("Login failed", status_code=400)

async def logout(request):
    """
    Logout user and revoke tokens.

    SECURITY: Deletes tokens from Secret Manager to prevent reuse.
    """
    user = request.session.get('user')

    if user and 'email' in user:
        # SECURITY: Revoke tokens from Secret Manager
        try:
            token_manager = TokenManager(os.environ.get('GOOGLE_CLOUD_PROJECT'))
            token_manager.delete_user_tokens(user['email'])
        except Exception as e:
            import logging
            logging.error(f"Failed to delete tokens for {user['email']}: {str(e)}")

    request.session.pop('user', None)
    return RedirectResponse(url='/login-page')

async def login_page(request):
    return HTMLResponse(LOGIN_PAGE_HTML)

async def user_info(request):
    """Return current user info as JSON"""
    user = request.session.get('user')
    if user:
        return HTMLResponse(f"""
        <div style="position: fixed; top: 20px; right: 20px; background: white; padding: 12px 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); z-index: 10000; display: flex; align-items: center; gap: 12px; font-family: 'Inter', sans-serif;">
            <img src="{user.get('picture', '')}" alt="Avatar" style="width: 32px; height: 32px; border-radius: 50%;">
            <div style="display: flex; flex-direction: column; line-height: 1.3;">
                <span style="font-size: 13px; font-weight: 600; color: #1a1a1a;">{user.get('name', 'Usuario')}</span>
                <span style="font-size: 11px; color: #6b7280;">{user.get('email', '')}</span>
            </div>
            <a href="/logout" style="margin-left: 8px; padding: 6px 12px; background: #f3f4f6; border-radius: 6px; text-decoration: none; font-size: 12px; color: #374151; font-weight: 500; transition: all 0.2s;">Cerrar sesión</a>
        </div>
        """)
    return HTMLResponse("")

# --- Auth Middleware ---
class AuthMiddleware:
    def __init__(self, app):
        self.app = app
        self.auth_app = Starlette(routes=[
            Route('/login-page', endpoint=login_page),
            Route('/login', endpoint=login),
            Route('/authorize', endpoint=authorize),
            Route('/logout', endpoint=logout),
            Route('/user-info', endpoint=user_info),
        ])

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Handle auth routes separately
        path = scope['path']
        if path.startswith(('/login', '/logout', '/authorize', '/login-page', '/user-info')):
            await self.auth_app(scope, receive, send)
            return

        # Check session for all other routes
        if "user" not in scope['session']:
            response = RedirectResponse(url='/login-page', status_code=307)
            await response(scope, receive, send)
            return

        # Inject user email into scope state for ADK agent tools
        # This makes the user email available in tool_context.state
        user_info = scope['session']['user']
        user_email = user_info.get('email', '')

        # Store user email in scope's state so ADK can access it
        if 'state' not in scope:
            scope['state'] = {}
        scope['state']['user_email'] = user_email
        scope['state']['user_name'] = user_info.get('name', '')
        scope['state']['user_picture'] = user_info.get('picture', '')

        await self.app(scope, receive, send)
