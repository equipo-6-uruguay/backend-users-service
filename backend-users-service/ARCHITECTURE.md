# ARCHITECTURE.md — Contrato de API · users-service

> Microservicio de gestión y autenticación de usuarios.  
> Base URL: `http://localhost:8000/api`

---

## Tabla de contenidos
1. [Resumen de endpoints](#1-resumen-de-endpoints)
2. [Contrato detallado de cada endpoint](#2-contrato-detallado-de-cada-endpoint)
3. [Autenticación y sesión](#3-autenticación-y-sesión)
4. [Auditoría de verbos HTTP y códigos de estado](#4-auditoría-de-verbos-http-y-códigos-de-estado)
5. [Problemas encontrados](#5-problemas-encontrados)
6. [Endpoints sin uso y casos de uso sin endpoint](#6-endpoints-sin-uso-y-casos-de-uso-sin-endpoint)
7. [Endpoints faltantes recomendados](#7-endpoints-faltantes-recomendados)

---

## 1. Resumen de endpoints

| # | Método | Ruta | Acción | Auth requerida |
|---|--------|------|--------|----------------|
| 1 | `GET` | `/api/health/` | Estado del servicio | No |
| 2 | `POST` | `/api/auth/` | Registrar usuario | No |
| 3 | `POST` | `/api/auth/login/` | Iniciar sesión | No |
| 4 | `GET` | `/api/auth/me/` | Perfil del usuario autenticado | Sí |
| 5 | `POST` | `/api/auth/logout/` | Cerrar sesión | No (*) |
| 6 | `POST` | `/api/auth/refresh/` | Renovar token JWT | No |
| 7 | `GET` | `/api/auth/by-role/{role}/` | Listar usuarios por rol | Sí |

> (*) El endpoint de logout es público intencionalmente para permitir limpiar cookies aunque el token haya expirado.

---

## 2. Contrato detallado de cada endpoint

---

### 2.1 `GET /api/health/`

**Clase:** `HealthCheckView`  
**Propósito:** Verificar la disponibilidad del servicio y la conexión a la base de datos.  
**Autenticación:** No requerida

#### Request
```
GET /api/health/
```
Sin body.

#### Responses

**200 OK** — El servicio está operativo.
```json
{
  "service": "users-service",
  "status": "healthy",
  "database": "connected"
}
```

**503 Service Unavailable** — Error de conexión a la base de datos.
```json
{
  "service": "users-service",
  "status": "unhealthy",
  "database": "error: <mensaje de error>"
}
```

---

### 2.2 `POST /api/auth/` — Registrar usuario

**Clase:** `AuthViewSet.create()`  
**Propósito:** Crear una cuenta de usuario nueva. El rol siempre es `USER`; no puede ser asignado por el cliente.  
**Autenticación:** No requerida

#### Request body
```json
{
  "email": "usuario@ejemplo.com",
  "username": "miusuario",
  "password": "contraseña123"
}
```

| Campo | Tipo | Requerido | Reglas |
|-------|------|-----------|--------|
| `email` | string | Sí | Formato email válido |
| `username` | string | Sí | 3–50 caracteres |
| `password` | string | Sí | Mínimo 8 caracteres, write-only |

#### Responses

**201 Created** — Usuario creado exitosamente. Sets HttpOnly cookies `access_token` (30 min) y `refresh_token` (1 día).
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "usuario@ejemplo.com",
    "username": "miusuario",
    "role": "USER",
    "is_active": true
  }
}
```

**400 Bad Request** — Email duplicado o datos de dominio inválidos.
```json
{ "error": "Ya existe un usuario con el email: usuario@ejemplo.com" }
```

**500 Internal Server Error** — Error inesperado del servidor.
```json
{ "error": "Error inesperado: <detalle>" }
```

---

### 2.3 `POST /api/auth/login/`

**Clase:** `AuthViewSet.login()`  
**Propósito:** Autenticar un usuario con email y contraseña.  
**Autenticación:** No requerida

> ⚠️ Esta ruta **no** es generada por el router DRF; se registra manualmente en `users/urls.py` como `path('auth/login/', ...)`. El método `login` no lleva decorador `@action`.

#### Request body
```json
{
  "email": "usuario@ejemplo.com",
  "password": "contraseña123"
}
```

| Campo | Tipo | Requerido |
|-------|------|-----------|
| `email` | string | Sí |
| `password` | string | Sí |

#### Responses

**200 OK** — Autenticación exitosa. Sets cookies `access_token` y `refresh_token`.
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "usuario@ejemplo.com",
    "username": "miusuario",
    "role": "USER",
    "is_active": true
  }
}
```

**401 Unauthorized** — Credenciales inválidas o usuario inactivo.
```json
{ "error": "Credenciales inválidas" }
```

**500 Internal Server Error** — Error inesperado.
```json
{ "error": "Error inesperado: <detalle>" }
```

---

### 2.4 `GET /api/auth/me/`

**Clase:** `AuthViewSet.me()`  
**Propósito:** Obtener el perfil del usuario actualmente autenticado.  
**Autenticación:** Requerida (cookie `access_token`, vía `CookieJWTAuthentication`)

#### Request
```
GET /api/auth/me/
Cookie: access_token=<jwt>
```
Sin body.

#### Responses

**200 OK**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "usuario@ejemplo.com",
  "username": "miusuario",
  "role": "USER",
  "is_active": true
}
```

**401 Unauthorized** — DRF retorna automáticamente si el token es inválido o ausente.
```json
{ "detail": "Authentication credentials were not provided." }
```

---

### 2.5 `POST /api/auth/logout/`

**Clase:** `AuthViewSet.logout()`  
**Propósito:** Cerrar sesión eliminando las cookies de autenticación.  
**Autenticación:** No requerida (para permitir logout con tokens expirados)

#### Request
```
POST /api/auth/logout/
```
Sin body.

#### Responses

**200 OK** — Cookies limpiadas correctamente.
```json
{ "detail": "Sesión cerrada" }
```

---

### 2.6 `POST /api/auth/refresh/`

**Clase:** `CookieTokenRefreshView`  
**Propósito:** Renovar el `access_token` usando el `refresh_token` de la cookie HttpOnly.  
**Autenticación:** No requerida (lee cookie `refresh_token` directamente)

#### Request
```
POST /api/auth/refresh/
Cookie: refresh_token=<jwt>
```
Sin body.

#### Responses

**200 OK** — New cookies `access_token` y `refresh_token` emitidas.
```json
{ "detail": "Token renovado" }
```

**401 Unauthorized** — Token de refresco ausente, inválido o expirado. Cookies limpiadas.
```json
{ "error": "Refresh token no encontrado" }
```
```json
{ "error": "Refresh token inválido o expirado" }
```
```json
{ "error": "Error al renovar token" }
```

---

### 2.7 `GET /api/auth/by-role/{role}/`

**Clase:** `AuthViewSet.by_role()`  
**Propósito:** Obtener la lista de usuarios que tienen un rol específico.  
**Autenticación:** Requerida

#### Parámetros de ruta

| Parámetro | Valores válidos |
|-----------|----------------|
| `role` | `ADMIN`, `USER` (case-insensitive) |

#### Ejemplo
```
GET /api/auth/by-role/ADMIN/
```

#### Responses

**200 OK**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "admin@ejemplo.com",
    "username": "adminuser",
    "role": "ADMIN",
    "is_active": true
  }
]
```

> Si el rol no existe o la lista está vacía, responde `200 OK` con `[]`.

**500 Internal Server Error** — Error inesperado.
```json
{ "error": "Error inesperado: <detalle>" }
```

---

## 3. Autenticación y sesión

El servicio utiliza **JWT vía HttpOnly cookies**, nunca expone tokens en el body de respuesta.

| Cookie | Ruta activa | TTL | Descripción |
|--------|-------------|-----|-------------|
| `access_token` | `/` | 30 min | Token de acceso para endpoints protegidos |
| `refresh_token` | `/api/auth/` | 24 h | Token para renovar el `access_token` |

La autenticación personalizada `CookieJWTAuthentication` lee la cookie `access_token` en cada request protegido.

---

## 4. Auditoría de verbos HTTP y códigos de estado

### ✅ Usos correctos

| Endpoint | Verbo | Corrección | Código(s) de estado | Corrección |
|----------|-------|-----------|---------------------|-----------|
| `/api/health/` | `GET` | ✅ Operación de lectura, segura e idempotente | 200, 503 | ✅ |
| `/api/auth/` (register) | `POST` | ✅ Creación de recurso | 201, 400, 500 | ✅ |
| `/api/auth/login/` | `POST` | ✅ No idempotente, modifica estado de sesión | 200, 401, 500 | ✅ |
| `/api/auth/me/` | `GET` | ✅ Lectura segura | 200, 401* | ✅ |
| `/api/auth/logout/` | `POST` | ⚠️ Aceptable; `DELETE` sería más semántico | 200 | ⚠️ Ver nota |
| `/api/auth/refresh/` | `POST` | ✅ Crea un nuevo token (no idempotente) | 200, 401 | ✅ |
| `/api/auth/by-role/{role}/` | `GET` | ✅ Lectura filtrada, idempotente | 200, 500 | ⚠️ Ver nota |

> `*` El 401 del endpoint `/me/` es retornado automáticamente por DRF.

### ⚠️ Observaciones puntuales

#### `POST /api/auth/logout/` → debería retornar `204 No Content`
El logout no devuelve un recurso útil en el body (`{"detail": "Sesión cerrada"}`).  
REST recomienda **204 No Content** cuando la acción fue exitosa pero no hay contenido que retornar.  
**Estado actual:** 200 OK — funcionalmente aceptable pero semánticamente impreciso.

#### `GET /api/auth/by-role/{role}/` → rol inválido silencioso
Cuando se pasa un rol inexistente (e.g., `SUPERUSER`), el endpoint retorna **200 OK** con `[]` en lugar de **400 Bad Request**.  
Esto oculta errores del cliente y dificulta el debugging.

**Comportamiento actual:**
```json
GET /api/auth/by-role/SUPERUSER/  →  200 OK  →  []
```

**Comportamiento esperado:**
```json
GET /api/auth/by-role/SUPERUSER/  →  400 Bad Request  →  {"error": "Rol inválido: SUPERUSER. Valores permitidos: ADMIN, USER"}
```

---

## 5. Problemas encontrados

### P1 — Rutas duplicadas para `me` y `logout`

En `users/urls.py` existen rutas registradas **dos veces** para los mismos endpoints:

```python
# Ruta 1: generada automáticamente por el router a través del decorador @action
router.register(r'auth', AuthViewSet, basename='auth')
# → genera GET /api/auth/me/ y POST /api/auth/logout/

# Ruta 2: registradas explícitamente además del router
path('auth/me/',     AuthViewSet.as_view({'get': 'me'}),     name='auth-me'),
path('auth/logout/', AuthViewSet.as_view({'post': 'logout'}), name='auth-logout'),
```

Django resuelve usando la **primera coincidencia**, por lo que las rutas explícitas sobreescriben silenciosamente las del router. Esto es redundante y confuso.

**Solución recomendada:** Eliminar las tres rutas explícitas (`auth/login/`, `auth/me/`, `auth/logout/`) y decorar el método `login` con `@action` para que el router lo gestione:

```python
@action(detail=False, methods=['post'], url_path='login', permission_classes=[AllowAny])
def login(self, request):
    ...
```

---

### P2 — `AuthViewSet` expone rutas no implementadas (405 fantasmas)

El `DefaultRouter` para `AuthViewSet` genera automáticamente estas rutas que no están implementadas y devuelven `405 Method Not Allowed`:

| Ruta generada | Método | Resultado |
|---------------|--------|-----------|
| `GET /api/auth/` | list | 405 |
| `GET /api/auth/{id}/` | retrieve | 405 |
| `PUT /api/auth/{id}/` | update | 405 |
| `PATCH /api/auth/{id}/` | partial_update | 405 |
| `DELETE /api/auth/{id}/` | destroy | 405 |

**Solución recomendada:** Usar `SimpleRouter` en lugar de `DefaultRouter` para evitar la auto-documentación de rutas no disponibles, o cambiar a `APIView` individual si el ViewSet no va a tener más acciones.

---

### P3 — `by_role` no valida el rol y retorna 200 con lista vacía

Ver punto 4 (Auditoría de verbos), sección `⚠️ by-role`.

---

### P4 — `UserNotFound` como señal de credenciales inválidas en `LoginUseCase`
