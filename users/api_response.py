"""
users/api_response.py

Utilidades para construir respuestas HTTP consistentes siguiendo JSON:API (jsonapi.org)
y las semánticas HTTP de RFC 7231 / RFC 9110.

Todas las respuestas del servicio pasan por estos helpers para garantizar
un envelope uniforme:

  Éxito (recurso individual):
    {
      "data": { "type": "users", "id": "...", "attributes": { ... } },
      "meta": { ... }
    }

  Éxito (colección):
    {
      "data": [ ... ],
      "meta": { "count": N, "timestamp": "..." }
    }

  Error:
    {
      "errors": [
        {
          "status": "404",
          "code": "user_not_found",
          "title": "Resource not found",
          "detail": "Usuario abc123 no encontrado",
          "source": { "pointer": "/data/attributes/id" }  // opcional
        }
      ]
    }
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

from rest_framework.response import Response
from rest_framework import status as http_status

# Thread-local storage para propagar request_id sin pasar request
# a cada función. El middleware lo setea al inicio de cada petición.
_local = threading.local()


def set_request_id(request_id: str) -> None:
    """Almacena el request_id en thread-local (llamado por el middleware)."""
    _local.request_id = request_id


def get_request_id() -> Optional[str]:
    """Obtiene el request_id del thread-local, o None si no está seteado."""
    return getattr(_local, "request_id", None)


# ---------------------------------------------------------------------------
# Helpers para construir bloques JSON:API
# ---------------------------------------------------------------------------

def _resource_object(
    resource_type: str,
    resource_id: str,
    attributes: Dict[str, Any],
    *,
    links: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Construye un *resource object* según JSON:API §5.2.

    Un resource object SIEMPRE tiene ``type`` e ``id`` en el nivel raíz;
    los demás campos van dentro de ``attributes``.
    """
    obj: Dict[str, Any] = {
        "type": resource_type,
        "id": str(resource_id),
        "attributes": attributes,
    }
    if links:
        obj["links"] = links
    return obj


def _meta(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Bloque ``meta`` común a todas las respuestas."""
    m: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "users-service",
    }
    request_id = get_request_id()
    if request_id:
        m["request_id"] = request_id
    if extra:
        m.update(extra)
    return m


def _error_object(
    *,
    status_code: int,
    code: str,
    title: str,
    detail: str,
    source: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Construye un *error object* según JSON:API §7."""
    err: Dict[str, Any] = {
        "status": str(status_code),
        "code": code,
        "title": title,
        "detail": detail,
    }
    if source:
        err["source"] = source
    return err


# ---------------------------------------------------------------------------
# Funciones de respuesta pública
# ---------------------------------------------------------------------------

def success_response(
    data: Dict[str, Any],
    *,
    status: int = http_status.HTTP_200_OK,
    headers: Optional[Dict[str, str]] = None,
    meta_extra: Optional[Dict[str, Any]] = None,
) -> Response:
    """
    Respuesta exitosa con un solo recurso.

    Args:
        data: Resource object ya formateado (con type/id/attributes).
        status: HTTP status code (200, 201, …).
        headers: Cabeceras adicionales (p.ej. Location).
        meta_extra: Campos adicionales para el bloque ``meta``.
    """
    body = {
        "data": data,
        "meta": _meta(meta_extra),
    }
    response = Response(body, status=status, content_type="application/vnd.api+json")
    if headers:
        for k, v in headers.items():
            response[k] = v
    return response


def collection_response(
    data: Sequence[Dict[str, Any]],
    *,
    status: int = http_status.HTTP_200_OK,
    meta_extra: Optional[Dict[str, Any]] = None,
) -> Response:
    """Respuesta exitosa con una colección de recursos."""
    extra = {"count": len(data)}
    if meta_extra:
        extra.update(meta_extra)
    body = {
        "data": list(data),
        "meta": _meta(extra),
    }
    return Response(body, status=status, content_type="application/vnd.api+json")


def error_response(
    errors: List[Dict[str, Any]],
    *,
    status: int = http_status.HTTP_400_BAD_REQUEST,
    headers: Optional[Dict[str, str]] = None,
) -> Response:
    """
    Respuesta de error siguiendo JSON:API §7.

    Args:
        errors: Lista de error objects.
        status: HTTP status code de la respuesta.
        headers: Cabeceras adicionales (p.ej. WWW-Authenticate).
    """
    body = {
        "errors": errors,
        "meta": _meta(),
    }
    response = Response(body, status=status, content_type="application/vnd.api+json")
    if headers:
        for k, v in headers.items():
            response[k] = v
    return response


def no_content_response() -> Response:
    """204 No Content — para DELETE exitoso (RFC 7231 §6.3.5)."""
    return Response(status=http_status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Shortcuts para errores frecuentes
# ---------------------------------------------------------------------------

def not_found_error(detail: str, *, code: str = "not_found") -> Response:
    """404 Not Found."""
    return error_response(
        [_error_object(
            status_code=404,
            code=code,
            title="Resource not found",
            detail=detail,
        )],
        status=http_status.HTTP_404_NOT_FOUND,
    )


def conflict_error(detail: str, *, code: str = "conflict") -> Response:
    """409 Conflict — recurso ya existe (RFC 9110 §15.5.10)."""
    return error_response(
        [_error_object(
            status_code=409,
            code=code,
            title="Conflict",
            detail=detail,
        )],
        status=http_status.HTTP_409_CONFLICT,
    )


def validation_error(
    detail: str,
    *,
    code: str = "validation_error",
    source: Optional[Dict[str, str]] = None,
) -> Response:
    """422 Unprocessable Entity — error de validación semántica (RFC 9110 §15.5.21)."""
    return error_response(
        [_error_object(
            status_code=422,
            code=code,
            title="Validation error",
            detail=detail,
            source=source,
        )],
        status=422,
    )


def unauthorized_error(
    detail: str = "Authentication credentials were not provided or are invalid.",
    *,
    code: str = "unauthorized",
) -> Response:
    """401 Unauthorized (RFC 9110 §15.5.2)."""
    return error_response(
        [_error_object(
            status_code=401,
            code=code,
            title="Unauthorized",
            detail=detail,
        )],
        status=http_status.HTTP_401_UNAUTHORIZED,
        headers={"WWW-Authenticate": "Bearer"},
    )


def forbidden_error(detail: str = "You do not have permission to perform this action.") -> Response:
    """403 Forbidden (RFC 9110 §15.5.4)."""
    return error_response(
        [_error_object(
            status_code=403,
            code="forbidden",
            title="Forbidden",
            detail=detail,
        )],
        status=http_status.HTTP_403_FORBIDDEN,
    )


def internal_error(detail: str = "An unexpected error occurred.") -> Response:
    """500 Internal Server Error."""
    return error_response(
        [_error_object(
            status_code=500,
            code="internal_error",
            title="Internal server error",
            detail=detail,
        )],
        status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


# ---------------------------------------------------------------------------
# Serializador de usuario a JSON:API resource object
# ---------------------------------------------------------------------------

def user_resource(user, *, request=None) -> Dict[str, Any]:
    """
    Convierte una entidad ``User`` de dominio a un JSON:API resource object.

    Centraliza la serialización para garantizar consistencia en todos los
    endpoints que devuelven usuarios.
    """
    role_value = getattr(user.role, "value", user.role) if hasattr(user, "role") else "USER"
    created = getattr(user, "created_at", None)
    if created and hasattr(created, "isoformat"):
        created = created.isoformat()

    attributes = {
        "email": user.email,
        "username": user.username,
        "role": role_value,
        "is_active": user.is_active,
    }
    if created:
        attributes["created_at"] = created

    links: Dict[str, str] = {}
    if request:
        links["self"] = f"/api/users/{user.id}/"

    return _resource_object("users", str(user.id), attributes, links=links)
