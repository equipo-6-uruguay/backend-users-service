# Contrato API - Users Service

## 📋 Descripción

Microservicio de usuarios que gestiona registro, autenticación y administración de usuarios. Expone una API REST bajo el prefijo `/api/`.

---

## 🔐 Autenticación

El servicio utiliza **JWT (JSON Web Tokens)** almacenados en cookies HttpOnly:

| Cookie          | Descripción                              | Expiración  |
|-----------------|------------------------------------------|-------------|
| `access_token`  | Token de acceso para recursos protegidos | Corta (mins) |
| `refresh_token` | Token para renovar el access token       | Larga (días) |

Los endpoints protegidos requieren que la cookie `access_token` esté presente en la petición. Para renovar un token expirado se usa `POST /api/auth/refresh/`.

Los endpoints públicos (sin autenticación requerida) son: `POST /api/auth/`, `POST /api/auth/login/`, `POST /api/auth/logout/` y `POST /api/auth/refresh/`.

---

## 📡 Endpoints

### Health Check

#### `GET /api/health/`

Verifica el estado del servicio y la conectividad con la base de datos.

**Respuesta exitosa (200):**
```json
{
  "service": "users-service",
  "status": "healthy",
  "database": "connected"
}
```

**Respuesta con error de base de datos (503):**
```json
{
  "service": "users-service",
  "status": "unhealthy",
  "database": "error: <mensaje>"
}
```

---

### Autenticación

#### `POST /api/auth/` — Registro de usuario

Registra un nuevo usuario. Acceso público.

**Body:**
```json
{
  "email": "usuario@ejemplo.com",
  "username": "nombreusuario",
  "password": "contraseña123"
}
```

**Respuesta exitosa (201):**
```json
{
  "user": {
    "id": "uuid-del-usuario",
    "email": "usuario@ejemplo.com",
    "username": "nombreusuario",
    "role": "USER",
    "is_active": true
  }
}
```
Además establece las cookies `access_token` y `refresh_token`.

**Errores:**

| Código | Motivo |
|--------|--------|
| 400    | Email o usuario ya existe, datos inválidos |
| 500    | Error inesperado del servidor |

---

#### `POST /api/auth/login/` — Inicio de sesión

Autentica a un usuario existente. Acceso público.

**Body:**
```json
{
  "email": "usuario@ejemplo.com",
  "password": "contraseña123"
}
```

**Respuesta exitosa (200):**
```json
{
  "user": {
    "id": "uuid-del-usuario",
    "email": "usuario@ejemplo.com",
    "username": "nombreusuario",
    "role": "USER",
    "is_active": true
  }
}
```
Además establece las cookies `access_token` y `refresh_token`.

**Errores:**

| Código | Motivo |
|--------|--------|
| 401    | Credenciales inválidas |
| 500    | Error inesperado del servidor |

---

#### `POST /api/auth/logout/` — Cierre de sesión

Cierra la sesión limpiando las cookies de autenticación. Acceso público.

**Respuesta exitosa (200):**
```json
{
  "detail": "Sesión cerrada"
}
```

---

#### `GET /api/auth/me/` — Usuario actual 🔒

Devuelve los datos del usuario autenticado. Requiere `access_token`.

**Respuesta exitosa (200):**
```json
{
  "id": "uuid-del-usuario",
  "email": "usuario@ejemplo.com",
  "username": "nombreusuario",
  "role": "USER",
  "is_active": true
}
```

**Errores:**

| Código | Motivo |
|--------|--------|
| 401    | No autenticado |

---

#### `POST /api/auth/refresh/` — Renovar token

Renueva el `access_token` usando el `refresh_token` de la cookie. Acceso público.

**Respuesta exitosa (200):**
```json
{
  "detail": "Token renovado"
}
```
Además actualiza las cookies `access_token` y `refresh_token`.

**Errores:**

| Código | Motivo |
|--------|--------|
| 401    | `refresh_token` no encontrado, inválido o expirado |

---

#### `GET /api/auth/by-role/{role}/` — Usuarios por rol 🔒

Devuelve todos los usuarios con el rol especificado. Requiere `access_token`.

**Parámetros de ruta:**

| Parámetro | Valores válidos |
|-----------|-----------------|
| `role`    | `ADMIN`, `USER` |

**Respuesta exitosa (200):**
```json
[
  {
    "id": "uuid-del-usuario",
    "email": "usuario@ejemplo.com",
    "username": "nombreusuario",
    "role": "USER",
    "is_active": true
  }
]
```

**Errores:**

| Código | Motivo |
|--------|--------|
| 400    | Rol inválido |
| 401    | No autenticado |
| 500    | Error inesperado del servidor |

---

### Gestión de Usuarios

Todos los endpoints de esta sección requieren `access_token` (🔒).

#### `GET /api/users/` — Listar usuarios 🔒

Devuelve todos los usuarios del sistema.

**Respuesta exitosa (200):**
```json
[
  {
    "id": "uuid-del-usuario",
    "email": "usuario@ejemplo.com",
    "username": "nombreusuario",
    "role": "USER",
    "is_active": true
  }
]
```

---

#### `GET /api/users/{id}/` — Obtener usuario por ID 🔒

**Respuesta exitosa (200):**
```json
{
  "id": "uuid-del-usuario",
  "email": "usuario@ejemplo.com",
  "username": "nombreusuario",
  "role": "USER",
  "is_active": true
}
```

**Errores:**

| Código | Motivo |
|--------|--------|
| 404    | Usuario no encontrado |

---

#### `PATCH /api/users/{id}/` — Actualizar email 🔒

Actualiza el email del usuario.

**Body:**
```json
{
  "email": "nuevo@ejemplo.com"
}
```

**Respuesta exitosa (200):**
```json
{
  "id": "uuid-del-usuario",
  "email": "nuevo@ejemplo.com",
  "username": "nombreusuario",
  "role": "USER",
  "is_active": true
}
```

**Errores:**

| Código | Motivo |
|--------|--------|
| 400    | Email inválido o ya en uso |
| 404    | Usuario no encontrado |

---

#### `POST /api/users/{id}/deactivate/` — Desactivar usuario 🔒

Desactiva un usuario impidiendo su acceso al sistema.

**Body (opcional):**
```json
{
  "reason": "Motivo de desactivación"
}
```

**Respuesta exitosa (200):**
```json
{
  "id": "uuid-del-usuario",
  "email": "usuario@ejemplo.com",
  "username": "nombreusuario",
  "role": "USER",
  "is_active": false
}
```

**Errores:**

| Código | Motivo |
|--------|--------|
| 404    | Usuario no encontrado |

---

#### `DELETE /api/users/{id}/` — Eliminar usuario 🔒

Elimina un usuario permanentemente.

**Respuesta exitosa (204):** Sin cuerpo.

**Errores:**

| Código | Motivo |
|--------|--------|
| 404    | Usuario no encontrado |

---

## 👤 Roles de Usuario

| Rol     | Descripción          |
|---------|----------------------|
| `USER`  | Usuario estándar (por defecto al registrarse) |
| `ADMIN` | Administrador del sistema |

---

## ⚠️ Problemas Conocidos

- **Hashing de contraseñas**: actualmente se utiliza SHA-256. En producción se debe reemplazar por bcrypt u otro algoritmo de hashing seguro con salt.
- **Autorización no implementada**: todos los endpoints protegidos solo verifican autenticación (token válido), pero no comprueban si el usuario tiene permisos suficientes para realizar la operación (p. ej., solo un ADMIN debería poder listar o eliminar usuarios).
- **Sin paginación**: los endpoints `GET /api/users/` y `GET /api/auth/by-role/{role}/` devuelven la lista completa sin paginación, lo que puede ser un problema con grandes volúmenes de datos.
