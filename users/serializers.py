"""
users/serializers.py

📋 CAPA DE PRESENTACIÓN - Serialización

🎯 PROPÓSITO:
Transforma datos entre JSON (HTTP) y objetos Python.

📐 ESTRUCTURA:
- Un serializer por cada operación de API
- Valida INPUT desde el cliente
- Formatea OUTPUT hacia el cliente
- NO contiene lógica de negocio

✅ EJEMPLO de lo que DEBE ir aquí:
    from rest_framework import serializers

    class CreateUserSerializer(serializers.Serializer):
        '''Serializer para crear un usuario (INPUT)'''
        email = serializers.EmailField(required=True)
        username = serializers.CharField(min_length=3, max_length=50, required=True)
        password = serializers.CharField(min_length=8, write_only=True, required=True)

    class UserSerializer(serializers.Serializer):
        '''Serializer para representar un usuario (OUTPUT)'''
        id = serializers.CharField(read_only=True)
        email = serializers.EmailField()
        username = serializers.CharField()
        is_active = serializers.BooleanField()

        # NO incluimos password en el output por seguridad

    class DeactivateUserSerializer(serializers.Serializer):
        '''Serializer para desactivar un usuario'''
        reason = serializers.CharField(max_length=200, required=True)

💡 Los serializers son el "traductor" entre HTTP/JSON y tu aplicación.
   Hacen validaciones básicas, NO validaciones de negocio (esas van en el dominio).
"""

import re
from rest_framework import serializers


class RegisterUserSerializer(serializers.Serializer):
    """Serializer para registrar un nuevo usuario (INPUT).

    SEGURIDAD: No se acepta campo 'role'. Todo registro público
    crea usuarios con rol USER. El rol solo puede ser asignado
    por un administrador autenticado.

    Validaciones (RFC 9110 — semántica de la petición):
    - email: formato válido, longitud ≤ 255.
    - username: 3-50 caracteres alfanuméricos (y guiones/underscores).
    - password: ≥ 8 caracteres, al menos una mayúscula, una minúscula y un dígito.
    """
    email = serializers.EmailField(
        required=True,
        max_length=255,
        help_text="Dirección de correo electrónico válida (máx. 255 caracteres).",
        error_messages={
            "required": "The 'email' field is required.",
            "invalid": "Enter a valid email address.",
            "max_length": "Email must not exceed 255 characters.",
        },
    )
    username = serializers.CharField(
        min_length=3,
        max_length=50,
        required=True,
        help_text="Nombre de usuario (3-50 caracteres alfanuméricos, guiones o underscores).",
        error_messages={
            "required": "The 'username' field is required.",
            "min_length": "Username must be at least 3 characters long.",
            "max_length": "Username must not exceed 50 characters.",
            "blank": "Username must not be blank.",
        },
    )
    password = serializers.CharField(
        min_length=8,
        max_length=128,
        write_only=True,
        required=True,
        help_text="Contraseña (8-128 caracteres, al menos 1 mayúscula, 1 minúscula, 1 dígito).",
        error_messages={
            "required": "The 'password' field is required.",
            "min_length": "Password must be at least 8 characters long.",
            "max_length": "Password must not exceed 128 characters.",
            "blank": "Password must not be blank.",
        },
    )

    def validate_username(self, value: str) -> str:
        """Solo caracteres alfanuméricos, guiones y underscores."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", value):
            raise serializers.ValidationError(
                "Username can only contain letters, numbers, hyphens and underscores."
            )
        return value

    def validate_password(self, value: str) -> str:
        """Al menos una mayúscula, una minúscula y un dígito."""
        if not re.search(r"[A-Z]", value):
            raise serializers.ValidationError(
                "Password must contain at least one uppercase letter."
            )
        if not re.search(r"[a-z]", value):
            raise serializers.ValidationError(
                "Password must contain at least one lowercase letter."
            )
        if not re.search(r"\d", value):
            raise serializers.ValidationError(
                "Password must contain at least one digit."
            )
        return value


class LoginSerializer(serializers.Serializer):
    """Serializer para login de usuario (INPUT)."""
    email = serializers.EmailField(
        required=True,
        error_messages={
            "required": "The 'email' field is required.",
            "invalid": "Enter a valid email address.",
        },
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        error_messages={
            "required": "The 'password' field is required.",
            "blank": "Password must not be blank.",
        },
    )


class UserResponseSerializer(serializers.Serializer):
    """Serializer para representar un usuario (OUTPUT)."""
    id = serializers.CharField(read_only=True)
    email = serializers.EmailField()
    username = serializers.CharField()
    role = serializers.CharField()
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField(read_only=True)


class AuthUserSerializer(serializers.Serializer):
    """Serializer de usuario para respuestas de autenticación."""
    id = serializers.CharField(read_only=True)
    email = serializers.EmailField()
    username = serializers.CharField()
    role = serializers.CharField()
    is_active = serializers.BooleanField()


class AuthResponseSerializer(serializers.Serializer):
    """Serializer for login/register response.

    NOTE: Tokens are no longer included in the response body.
    They are set as HttpOnly cookies by the view layer.
    """
    user = AuthUserSerializer()


class UpdateUserSerializer(serializers.Serializer):
    """Serializer para actualizar el email de un usuario (PATCH /api/users/{id}/)."""
    email = serializers.EmailField(
        required=True,
        max_length=255,
        error_messages={
            "required": "The 'email' field is required.",
            "invalid": "Enter a valid email address.",
            "max_length": "Email must not exceed 255 characters.",
        },
    )


class DeactivateUserSerializer(serializers.Serializer):
    """Serializer para desactivar un usuario (POST /api/users/{id}/deactivate/)."""
    reason = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        default="",
        error_messages={
            "max_length": "Reason must not exceed 200 characters.",
        },
    )
