"""
users/views.py

Capa de presentacion -- Controladores HTTP (thin controllers).

Cada vista/accion delega TODA la logica a los casos de uso y devuelve
respuestas en formato **JSON:API** (jsonapi.org) con codigos de estado
alineados a **RFC 7231 / RFC 9110**.

Las excepciones de dominio y DRF son capturadas por el exception handler
global (``users.exception_handler.jsonapi_exception_handler``), por lo que
los ``try/except`` en vistas se limitan a conversiones especificas de
HTTP-dominio que requieran cabeceras o logica extra (p.ej. Location, cookies).
"""

import logging
from typing import Any, Dict, cast

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.db import connection

from .application.use_cases import (
    RegisterUserCommand,
    LoginCommand,
    GetUsersByRoleCommand,
    DeactivateUserCommand,
    ChangeUserEmailCommand,
    RegisterUserUseCase,
    LoginUseCase,
    GetUsersByRoleUseCase,
    GetUserUseCase,
    ListUsersUseCase,
    DeactivateUserUseCase,
    ChangeUserEmailUseCase,
)
from .infrastructure.repository import DjangoUserRepository
from .infrastructure.event_publisher import RabbitMQEventPublisher
from .infrastructure.cookie_utils import set_auth_cookies, clear_auth_cookies
from .serializers import (
    RegisterUserSerializer,
    LoginSerializer,
    UpdateUserSerializer,
    DeactivateUserSerializer,
)
from .domain.exceptions import (
    UserAlreadyExists,
    InvalidEmail,
    InvalidUsername,
    InvalidUserData,
    UserNotFound,
    InvalidCredentials,
    InvalidRole,
)
from .api_response import (
    success_response,
    collection_response,
    no_content_response,
    not_found_error,
    conflict_error,
    validation_error,
    unauthorized_error,
    internal_error,
    user_resource,
    _error_object,
    _meta,
)

logger = logging.getLogger(__name__)


# ===========================================================================
# Health Check
# ===========================================================================

class HealthCheckView(APIView):
    """
    GET /api/health/

    Health check -- indica si el servicio y sus dependencias estan operativos.

    Responses:
        200: Servicio healthy.
        503: Servicio unhealthy (p.ej. base de datos inaccesible).
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        """Verifica estado del servicio y conectividad con la base de datos."""
        health: Dict[str, Any] = {
            "status": "healthy",
            "service": "users-service",
            "checks": {
                "database": "connected",
            },
        }

        try:
            connection.ensure_connection()
        except Exception as e:
            health["status"] = "unhealthy"
            health["checks"]["database"] = f"error: {e}"
            return Response(
                {"data": health, "meta": _meta()},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                content_type="application/vnd.api+json",
            )

        return Response(
            {"data": health, "meta": _meta()},
            status=status.HTTP_200_OK,
            content_type="application/vnd.api+json",
        )


# ===========================================================================
# Auth ViewSet
# ===========================================================================

class AuthViewSet(viewsets.ViewSet):
    """
    Autenticacion de usuarios.

    Endpoints:
        POST   /api/auth/           -- Registrar nuevo usuario (201 Created).
        POST   /api/auth/login/     -- Autenticar usuario (200 OK + cookies).
        POST   /api/auth/logout/    -- Cerrar sesion (200 OK, limpia cookies).
        GET    /api/auth/me/        -- Datos del usuario autenticado (200 OK).
        GET    /api/auth/by-role/{role}/ -- Usuarios filtrados por rol (200 OK).
    """

    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repository = DjangoUserRepository()
        self.event_publisher = RabbitMQEventPublisher()

    def get_permissions(self):
        """Permite acceso publico a register, login y logout."""
        if self.action in ("create", "login", "logout"):
            return [AllowAny()]
        return super().get_permissions()

    # -- POST /api/auth/  ->  Register ------------------------------------
    def create(self, request):
        """
        Registrar un nuevo usuario.

        Request body (application/json):
            { "email": "...", "username": "...", "password": "..." }

        Success 201 Created:
            JSON:API resource object + HttpOnly auth cookies.

        Errors:
            409 Conflict -- email ya registrado.
            422 Unprocessable Entity -- datos invalidos.
        """
        serializer = RegisterUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = cast(Dict[str, Any], serializer.validated_data)

        command = RegisterUserCommand(
            email=data["email"],
            username=data["username"],
            password=data["password"],
        )
        use_case = RegisterUserUseCase(
            repository=self.repository,
            event_publisher=self.event_publisher,
        )

        # Excepciones de dominio (UserAlreadyExists, InvalidEmail, etc.)
        # se propagan al exception handler global.
        auth_result = use_case.execute(command)
        user = auth_result["user"]
        tokens = auth_result["tokens"]

        resource = user_resource(user, request=request)
        response = success_response(
            resource,
            status=status.HTTP_201_CREATED,
            headers={"Location": f"/api/users/{user.id}/"},
        )
        return set_auth_cookies(response, tokens["access"], tokens["refresh"])

    # -- POST /api/auth/login/ --------------------------------------------
    @action(detail=False, methods=["post"], url_path="login")
    def login(self, request):
        """
        Autenticar un usuario existente.

        Request body:
            { "email": "...", "password": "..." }

        Success 200 OK:
            JSON:API resource object + HttpOnly auth cookies.

        Errors:
            401 Unauthorized -- credenciales invalidas / usuario inactivo.
            422 Unprocessable Entity -- datos de entrada invalidos.
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = cast(Dict[str, Any], serializer.validated_data)

        command = LoginCommand(email=data["email"], password=data["password"])
        use_case = LoginUseCase(repository=self.repository)

        auth_result = use_case.execute(command)
        user = auth_result["user"]
        tokens = auth_result["tokens"]

        resource = user_resource(user, request=request)
        response = success_response(resource, status=status.HTTP_200_OK)
        return set_auth_cookies(response, tokens["access"], tokens["refresh"])

    # -- GET /api/auth/me/ ------------------------------------------------
    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        """
        Datos del usuario autenticado.

        Success 200 OK:
            JSON:API resource object con datos del usuario actual.

        Errors:
            401 Unauthorized -- no autenticado.
        """
        user = request.user
        resource = user_resource(user, request=request)
        return success_response(resource, status=status.HTTP_200_OK)

    # -- POST /api/auth/logout/ -------------------------------------------
    @action(detail=False, methods=["post"], url_path="logout")
    def logout(self, request):
        """
        Cerrar sesion limpiando cookies de autenticacion.

        Success 200 OK:
            Confirmacion de cierre de sesion.
        """
        response = Response(
            {
                "data": None,
                "meta": {
                    **_meta(),
                    "message": "Session closed successfully.",
                },
            },
            status=status.HTTP_200_OK,
            content_type="application/vnd.api+json",
        )
        return clear_auth_cookies(response)

    # -- GET /api/auth/by-role/{role}/ ------------------------------------
    @action(detail=False, methods=["get"], url_path=r"by-role/(?P<role>[^/.]+)")
    def by_role(self, request, role=None):
        """
        Obtener usuarios filtrados por rol.

        Path parameters:
            role -- "ADMIN" o "USER".

        Success 200 OK:
            JSON:API collection de usuarios.

        Errors:
            422 Unprocessable Entity -- rol invalido.
        """
        command = GetUsersByRoleCommand(role=role)
        use_case = GetUsersByRoleUseCase(repository=self.repository)
        users = use_case.execute(command)

        resources = [user_resource(u, request=request) for u in users]
        return collection_response(resources, status=status.HTTP_200_OK)


# ===========================================================================
# Cookie Token Refresh
# ===========================================================================

class CookieTokenRefreshView(APIView):
    """
    POST /api/auth/refresh/

    Renueva el access token leyendo el refresh_token de la cookie HttpOnly.

    Success 200 OK:
        Nuevas cookies con tokens renovados.

    Errors:
        401 Unauthorized -- refresh token ausente, invalido o expirado.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            return unauthorized_error(
                detail="Refresh token not found in cookies.",
                code="refresh_token_missing",
            )

        try:
            refresh = RefreshToken(refresh_token)
            new_access = str(refresh.access_token)
            new_refresh = str(refresh)

            response = Response(
                {
                    "data": None,
                    "meta": {
                        **_meta(),
                        "message": "Token refreshed successfully.",
                    },
                },
                status=status.HTTP_200_OK,
                content_type="application/vnd.api+json",
            )
            return set_auth_cookies(response, new_access, new_refresh)

        except TokenError:
            resp = unauthorized_error(
                detail="Refresh token is invalid or expired.",
                code="refresh_token_invalid",
            )
            return clear_auth_cookies(resp)

        except Exception as e:
            logger.error("Unexpected error during token refresh: %s", e, exc_info=True)
            resp = unauthorized_error(
                detail="Could not refresh token.",
                code="refresh_error",
            )
            return clear_auth_cookies(resp)


# ===========================================================================
# User ViewSet (CRUD)
# ===========================================================================

class UserViewSet(viewsets.ViewSet):
    """
    Gestion de usuarios (requiere autenticacion).

    Endpoints:
        GET    /api/users/                   -- Listar usuarios (200).
        GET    /api/users/{id}/              -- Obtener usuario (200 | 404).
        PATCH  /api/users/{id}/              -- Actualizar email (200 | 404 | 409 | 422).
        POST   /api/users/{id}/deactivate/   -- Desactivar usuario (200 | 404 | 409).
        DELETE /api/users/{id}/              -- Eliminar usuario (204 | 404).
    """

    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repository = DjangoUserRepository()
        self.event_publisher = RabbitMQEventPublisher()

    # -- GET /api/users/ --------------------------------------------------
    def list(self, request):
        """
        Listar todos los usuarios del sistema.

        Success 200 OK:
            JSON:API collection con meta.count.
        """
        use_case = ListUsersUseCase(repository=self.repository)
        users = use_case.execute()
        resources = [user_resource(u, request=request) for u in users]
        return collection_response(resources, status=status.HTTP_200_OK)

    # -- GET /api/users/{id}/ ---------------------------------------------
    def retrieve(self, request, pk=None):
        """
        Obtener un usuario por ID.

        Success 200 OK:
            JSON:API resource object.

        Errors:
            404 Not Found -- usuario no existe.
        """
        use_case = GetUserUseCase(repository=self.repository)
        user = use_case.execute(user_id=pk)  # UserNotFound -> handler global
        resource = user_resource(user, request=request)
        return success_response(resource, status=status.HTTP_200_OK)

    # -- PATCH /api/users/{id}/ -------------------------------------------
    def partial_update(self, request, pk=None):
        """
        Actualizar el email del usuario.

        Request body:
            { "email": "new@example.com" }

        Success 200 OK:
            JSON:API resource object actualizado.

        Errors:
            404 Not Found -- usuario no existe.
            409 Conflict -- email ya en uso.
            422 Unprocessable Entity -- email invalido.
        """
        serializer = UpdateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        command = ChangeUserEmailCommand(
            user_id=pk,
            new_email=serializer.validated_data["email"],
        )
        use_case = ChangeUserEmailUseCase(
            repository=self.repository,
            event_publisher=self.event_publisher,
        )
        user = use_case.execute(command)
        resource = user_resource(user, request=request)
        return success_response(resource, status=status.HTTP_200_OK)

    # -- POST /api/users/{id}/deactivate/ ---------------------------------
    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate(self, request, pk=None):
        """
        Desactivar un usuario (impide su acceso al sistema).

        Request body (opcional):
            { "reason": "Motivo de la desactivacion" }

        Success 200 OK:
            JSON:API resource object con is_active=false.

        Errors:
            404 Not Found -- usuario no existe.
            409 Conflict -- usuario ya inactivo.
        """
        serializer = DeactivateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        command = DeactivateUserCommand(
            user_id=pk,
            reason=serializer.validated_data.get("reason") or None,
        )
        use_case = DeactivateUserUseCase(
            repository=self.repository,
            event_publisher=self.event_publisher,
        )
        user = use_case.execute(command)
        resource = user_resource(user, request=request)
        return success_response(resource, status=status.HTTP_200_OK)

    # -- DELETE /api/users/{id}/ ------------------------------------------
    def destroy(self, request, pk=None):
        """
        Eliminar un usuario permanentemente.

        Success 204 No Content (RFC 7231 6.3.5):
            Sin cuerpo de respuesta.

        Errors:
            404 Not Found -- usuario no existe.
        """
        user = self.repository.find_by_id(pk)
        if not user:
            raise UserNotFound(pk)
        self.repository.delete(pk)
        return no_content_response()