"""
users/openapi.py

Configuración de OpenAPI 3.0 usando drf-spectacular.

Genera el schema completo de la API (JSON/YAML) accesible vía endpoint,
sin ninguna UI (Swagger UI / ReDoc).  Se consume desde herramientas
externas (Postman, Insomnia, CI pipelines, etc.).

Endpoint registrado:
    GET /api/schema/ → devuelve el documento OpenAPI 3.0 como JSON.
"""

from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.openapi import AutoSchema  # noqa: F401 — importado para disponibilidad


class CookieJWTScheme(OpenApiAuthenticationExtension):
    """
    Describe la autenticación por cookie HttpOnly para drf-spectacular.

    Permite que el schema OpenAPI refleje que los endpoints protegidos
    requieren un access_token enviado como cookie (no como header Bearer).
    """

    target_class = "users.infrastructure.cookie_authentication.CookieJWTAuthentication"
    name = "cookieAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "cookie",
            "name": "access_token",
            "description": (
                "JWT access token set as an HttpOnly cookie after login/register. "
                "Send it automatically via the browser or include the cookie header."
            ),
        }
