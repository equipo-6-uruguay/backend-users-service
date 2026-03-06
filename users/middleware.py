"""
users/middleware.py

Middleware de la API para cumplimiento de RFC 7231 / RFC 9110.

Responsabilidades:
- Content negotiation: valida Accept y Content-Type.
- Inyección de cabeceras estándar (X-Request-ID, Cache-Control, Vary).
- Seguridad: X-Content-Type-Options, etc.
"""

from __future__ import annotations

import uuid
import logging
from typing import Callable

from django.http import HttpRequest, HttpResponse, JsonResponse

from .api_response import set_request_id

logger = logging.getLogger(__name__)

# Rutas que NO requieren content negotiation (health check, admin, etc.)
_EXEMPT_PREFIXES = ("/admin/", "/static/")


class APIHeadersMiddleware:
    """
    Middleware que inyecta cabeceras HTTP estándar en todas las respuestas
    de la API, según RFC 7231 §7 y mejores prácticas de seguridad.

    Cabeceras añadidas:
    - X-Request-ID: identificador único para trazabilidad.
    - X-Content-Type-Options: nosniff (seguridad).
    - Cache-Control: no-store para endpoints API (datos sensibles).
    - Vary: Accept, Authorization (content negotiation correcta).
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Generar o propagar X-Request-ID para trazabilidad
        request_id = request.META.get("HTTP_X_REQUEST_ID") or str(uuid.uuid4())
        request.META["HTTP_X_REQUEST_ID"] = request_id

        # Almacenar en thread-local para que _meta() lo incluya en el body
        set_request_id(request_id)

        response: HttpResponse = self.get_response(request)

        # ── Cabeceras en TODAS las respuestas ──────────────────────────
        response["X-Request-ID"] = request_id
        response["X-Content-Type-Options"] = "nosniff"

        # ── Cabeceras solo para rutas /api/ ────────────────────────────
        if request.path.startswith("/api/"):
            # Datos de API no deben cachearse (contienen info de usuario)
            if not response.has_header("Cache-Control"):
                response["Cache-Control"] = "no-store, no-cache, must-revalidate"

            # Vary indica a proxies que la respuesta depende de estos headers
            response["Vary"] = "Accept, Authorization, Cookie"

        return response


class ContentNegotiationMiddleware:
    """
    Middleware que valida Content-Type en requests con body (POST, PUT, PATCH)
    y el header Accept, según RFC 7231 §5.3.

    - Si el cliente envía un body con Content-Type no soportado → 415.
    - Si el cliente pide un Accept que no podemos servir → 406.

    Solo se aplica a rutas bajo /api/.
    """

    SUPPORTED_CONTENT_TYPES = {
        "application/json",
        "application/vnd.api+json",
    }

    # Content types that browsers / test clients send by default
    # for form submissions or empty POST bodies — never reject these.
    _PASSTHROUGH_CONTENT_TYPES = {
        "application/x-www-form-urlencoded",
        "multipart/form-data",
    }

    SUPPORTED_ACCEPT = {
        "application/json",
        "application/vnd.api+json",
        "*/*",
    }

    METHODS_WITH_BODY = {"POST", "PUT", "PATCH"}

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        path = request.path

        # Solo interceptar rutas de API
        if not path.startswith("/api/"):
            return self.get_response(request)

        # Excluir rutas exentas
        for prefix in _EXEMPT_PREFIXES:
            if path.startswith(prefix):
                return self.get_response(request)

        # ── Validar Content-Type en métodos con body (RFC 9110 §8.3) ──
        if request.method in self.METHODS_WITH_BODY:
            content_type = request.content_type or ""
            # Ignorar parámetros (charset, boundary, etc.)
            base_ct = content_type.split(";")[0].strip().lower()

            # Skip validation when there's no meaningful body content
            # (e.g. logout, action endpoints with empty POST)
            content_length = int(request.META.get("CONTENT_LENGTH") or 0)
            if (
                base_ct
                and base_ct not in self.SUPPORTED_CONTENT_TYPES
                and base_ct not in self._PASSTHROUGH_CONTENT_TYPES
                and content_length > 0
            ):
                return JsonResponse(
                    {
                        "errors": [
                            {
                                "status": "415",
                                "code": "unsupported_media_type",
                                "title": "Unsupported Media Type",
                                "detail": (
                                    f"Content-Type '{content_type}' is not supported. "
                                    f"Use 'application/json' or 'application/vnd.api+json'."
                                ),
                            }
                        ],
                        "meta": {
                            "request_id": request.META.get("HTTP_X_REQUEST_ID", ""),
                        },
                    },
                    status=415,
                    content_type="application/vnd.api+json",
                )

        # ── Validar Accept (RFC 9110 §12.5.1) ────────────────────────
        accept_header = request.META.get("HTTP_ACCEPT", "*/*")
        # Parsear los media-types del Accept (simplificado)
        accepted = {
            a.split(";")[0].strip().lower()
            for a in accept_header.split(",")
        }

        # Si el cliente es explícito y no acepta JSON, rechazar
        if accepted and not accepted.intersection(self.SUPPORTED_ACCEPT):
            return JsonResponse(
                {
                    "errors": [
                        {
                            "status": "406",
                            "code": "not_acceptable",
                            "title": "Not Acceptable",
                            "detail": (
                                f"This API only serves 'application/json' and "
                                f"'application/vnd.api+json'. "
                                f"Received Accept: '{accept_header}'."
                            ),
                        }
                    ],
                    "meta": {
                        "request_id": request.META.get("HTTP_X_REQUEST_ID", ""),
                    },
                },
                status=406,
                content_type="application/vnd.api+json",
            )

        return self.get_response(request)
