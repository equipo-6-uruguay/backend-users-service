"""
users/exception_handler.py

Global exception handler para Django REST Framework.

Centraliza la conversión de TODAS las excepciones (dominio, DRF, Django)
a respuestas JSON:API consistentes según RFC 7231 / RFC 9110.

Se registra en settings.py como:
    REST_FRAMEWORK = {
        'EXCEPTION_HANDLER': 'users.exception_handler.jsonapi_exception_handler',
    }
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status as http_status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    MethodNotAllowed,
    NotAuthenticated,
    NotFound,
    ParseError,
    PermissionDenied as DRFPermissionDenied,
    Throttled,
    UnsupportedMediaType,
    ValidationError as DRFValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_default_handler

from .api_response import _error_object, _meta
from .domain.exceptions import (
    DomainException,
    InvalidCredentials,
    InvalidEmail,
    InvalidRole,
    InvalidUserData,
    InvalidUsername,
    UserAlreadyExists,
    UserAlreadyInactive,
    UserNotFound,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mapeo de excepciones de dominio → (HTTP status, code, title)
# ---------------------------------------------------------------------------
_DOMAIN_MAP: Dict[type, tuple[int, str, str]] = {
    UserNotFound: (404, "user_not_found", "Resource not found"),
    UserAlreadyExists: (409, "user_already_exists", "Conflict"),
    UserAlreadyInactive: (409, "user_already_inactive", "Conflict"),
    InvalidEmail: (422, "invalid_email", "Validation error"),
    InvalidUsername: (422, "invalid_username", "Validation error"),
    InvalidUserData: (422, "invalid_user_data", "Validation error"),
    InvalidCredentials: (401, "invalid_credentials", "Unauthorized"),
    InvalidRole: (422, "invalid_role", "Validation error"),
}


def _build_response(errors: List[Dict[str, Any]], status_code: int) -> Response:
    """Construye la Response con envelope JSON:API."""
    body = {
        "errors": errors,
        "meta": _meta(),
    }
    return Response(body, status=status_code, content_type="application/vnd.api+json")


def _flatten_drf_validation(detail: Any, prefix: str = "") -> List[Dict[str, Any]]:
    """
    Convierte el detail de DRFValidationError (dict, list, str) en una lista
    de error objects JSON:API con ``source.pointer``.
    """
    errors: List[Dict[str, Any]] = []

    if isinstance(detail, dict):
        for field_name, messages in detail.items():
            pointer = f"/data/attributes/{field_name}" if field_name != "non_field_errors" else "/data"
            if isinstance(messages, list):
                for msg in messages:
                    errors.append(_error_object(
                        status_code=422,
                        code="validation_error",
                        title="Validation error",
                        detail=str(msg),
                        source={"pointer": pointer},
                    ))
            else:
                errors.append(_error_object(
                    status_code=422,
                    code="validation_error",
                    title="Validation error",
                    detail=str(messages),
                    source={"pointer": pointer},
                ))
    elif isinstance(detail, list):
        for msg in detail:
            if isinstance(msg, dict):
                errors.extend(_flatten_drf_validation(msg, prefix))
            else:
                errors.append(_error_object(
                    status_code=422,
                    code="validation_error",
                    title="Validation error",
                    detail=str(msg),
                ))
    else:
        errors.append(_error_object(
            status_code=422,
            code="validation_error",
            title="Validation error",
            detail=str(detail),
        ))

    return errors


def jsonapi_exception_handler(exc: Exception, context: Any) -> Optional[Response]:
    """
    Exception handler global registrado en DRF.

    Orden de resolución:
      1. Excepciones de dominio → mapeo explícito.
      2. DRF ValidationError → 422 con source pointers.
      3. Otras excepciones de DRF → mapeo automático.
      4. Django Http404 / PermissionDenied → mapeo.
      5. Cualquier otra excepción no controlada → 500.
    """

    # ── 1. Excepciones de dominio ──────────────────────────────────────
    if isinstance(exc, DomainException):
        status_code, code, title = _DOMAIN_MAP.get(
            type(exc), (400, "domain_error", "Domain error")
        )
        errors = [_error_object(
            status_code=status_code,
            code=code,
            title=title,
            detail=str(exc),
        )]
        if isinstance(exc, InvalidCredentials):
            resp = _build_response(errors, status_code)
            resp["WWW-Authenticate"] = "Bearer"
            return resp
        return _build_response(errors, status_code)

    # ── 2. DRF ValidationError → 422 ──────────────────────────────────
    if isinstance(exc, DRFValidationError):
        errors = _flatten_drf_validation(exc.detail)
        return _build_response(errors, 422)

    # ── 3. Otras DRF exceptions ────────────────────────────────────────
    if isinstance(exc, NotAuthenticated):
        errors = [_error_object(
            status_code=401, code="not_authenticated",
            title="Unauthorized",
            detail=str(exc.detail),
        )]
        resp = _build_response(errors, 401)
        resp["WWW-Authenticate"] = "Bearer"
        return resp

    if isinstance(exc, AuthenticationFailed):
        errors = [_error_object(
            status_code=401, code="authentication_failed",
            title="Unauthorized",
            detail=str(exc.detail),
        )]
        resp = _build_response(errors, 401)
        resp["WWW-Authenticate"] = "Bearer"
        return resp

    if isinstance(exc, (DRFPermissionDenied, PermissionDenied)):
        errors = [_error_object(
            status_code=403, code="forbidden",
            title="Forbidden",
            detail=str(getattr(exc, 'detail', str(exc))),
        )]
        return _build_response(errors, 403)

    if isinstance(exc, (NotFound, Http404)):
        detail_msg = str(getattr(exc, 'detail', "Resource not found"))
        errors = [_error_object(
            status_code=404, code="not_found",
            title="Resource not found",
            detail=detail_msg,
        )]
        return _build_response(errors, 404)

    if isinstance(exc, MethodNotAllowed):
        errors = [_error_object(
            status_code=405, code="method_not_allowed",
            title="Method not allowed",
            detail=str(exc.detail),
        )]
        resp = _build_response(errors, 405)
        if hasattr(exc, 'detail'):
            allowed = getattr(context.get('view', None), 'allowed_methods', [])
            if allowed:
                resp["Allow"] = ", ".join(allowed)
        return resp

    if isinstance(exc, UnsupportedMediaType):
        errors = [_error_object(
            status_code=415, code="unsupported_media_type",
            title="Unsupported media type",
            detail=str(exc.detail),
        )]
        return _build_response(errors, 415)

    if isinstance(exc, Throttled):
        errors = [_error_object(
            status_code=429, code="throttled",
            title="Too many requests",
            detail=f"Request was throttled. Expected available in {exc.wait} seconds.",
        )]
        resp = _build_response(errors, 429)
        if exc.wait:
            resp["Retry-After"] = str(int(exc.wait))
        return resp

    if isinstance(exc, ParseError):
        errors = [_error_object(
            status_code=400, code="parse_error",
            title="Bad request",
            detail=str(exc.detail),
        )]
        return _build_response(errors, 400)

    if isinstance(exc, APIException):
        errors = [_error_object(
            status_code=exc.status_code,
            code=exc.default_code if hasattr(exc, 'default_code') else "error",
            title=exc.default_detail if hasattr(exc, 'default_detail') else "Error",
            detail=str(exc.detail),
        )]
        return _build_response(errors, exc.status_code)

    # ── 4. Django ValidationError ──────────────────────────────────────
    if isinstance(exc, DjangoValidationError):
        errors = []
        if hasattr(exc, 'message_dict'):
            for field_name, messages in exc.message_dict.items():
                for msg in messages:
                    errors.append(_error_object(
                        status_code=422,
                        code="validation_error",
                        title="Validation error",
                        detail=str(msg),
                        source={"pointer": f"/data/attributes/{field_name}"},
                    ))
        else:
            for msg in exc.messages:
                errors.append(_error_object(
                    status_code=422,
                    code="validation_error",
                    title="Validation error",
                    detail=str(msg),
                ))
        return _build_response(errors, 422)

    # ── 5. Fallback: cualquier excepción no controlada → 500 ──────────
    logger.exception("Unhandled exception in API view: %s", exc)
    errors = [_error_object(
        status_code=500,
        code="internal_error",
        title="Internal server error",
        detail="An unexpected error occurred. Please try again later.",
    )]
    return _build_response(errors, 500)
