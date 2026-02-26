# Plan de Pruebas y Gestión de Riesgos — Users Service API & Contenerización

---

## Contenido

| # | Sección | Pág. |
|---|---------|------|
| 1 | [Objetivo](#1-objetivo) | 1 |
| 2 | [Descripción del Plan de Pruebas](#2-descripción-del-plan-de-pruebas) | 1 |
| 3 | [Alcance de las Pruebas](#3-alcance-de-las-pruebas) | 2 |
| 3.1 | [Dentro del Alcance](#31-dentro-del-alcance) | 2 |
| 3.2 | [Fuera del Alcance](#32-fuera-del-alcance) | 4 |
| 4 | [Niveles de Prueba](#4-niveles-de-prueba) | 5 |
| 5 | [Estrategia de las Pruebas](#5-estrategia-de-las-pruebas) | 6 |
| 5.1 | [Estrategia de Ejecución](#51-estrategia-de-ejecución) | 6 |
| 5.2 | [Estrategia de Datos](#52-estrategia-de-datos) | 7 |
| 6 | [Pruebas de Integración y Contenerización](#6-pruebas-de-integración--endpoints-api-rest) | 7 |
| 7 | [Análisis de Riesgo — Matriz de Riesgos por Criterio de Aceptación](#7-análisis-de-riesgo--matriz-de-riesgos-por-criterio-de-aceptación) | 12 |
| 8 | [Gestión de Riesgos — ISO/IEC 25010:2023](#8-gestión-de-riesgos--isoiec-250102023) | 17 |
| 8.10 | [Riesgos de Proyecto](#810-riesgos-de-proyecto) | 25 |
| 9 | [Herramientas](#9-herramientas) | 26 |
| 10 | [Calendario de Pruebas (Cronograma)](#10-calendario-de-pruebas-cronograma) | 27 |
| 11 | [Prerequisitos](#11-prerequisitos) | 28 |
| 12 | [Acuerdos](#12-acuerdos) | 28 |
| 13 | [Equipo de Trabajo](#13-equipo-de-trabajo) | 29 |
| 14 | [Diseño de Casos de Pruebas](#14-diseño-de-casos-de-pruebas) | 30 |

---

## 1. Objetivo

Definir el plan de pruebas para la **API REST y la Contenerización del microservicio Users Service**, construido con Django + DDD + EDA. Este plan establece el alcance, niveles de prueba, estrategia, herramientas, cronograma y gestión de riesgos para asegurar la calidad del software según el estándar **ISO/IEC 25010:2023**.

El plan contempla pruebas de integración para todos los endpoints de la API REST, pruebas de contenerización con Docker, y análisis de riesgos mapeados a las ocho características de calidad del modelo de producto de software.

---

## 2. Descripción del Plan de Pruebas

El **Users Service** es un microservicio de gestión de usuarios que forma parte de un ecosistema distribuido. Proporciona funcionalidades de registro, autenticación, gestión de perfiles y administración de usuarios a través de una API REST. Está construido con **Django REST Framework** aplicando **Domain-Driven Design (DDD)** y **Event-Driven Architecture (EDA)** con publicación de eventos a **RabbitMQ**.

### Arquitectura del sistema bajo prueba

```
Presentación (views.py, serializers.py, urls.py)
      │
      ▼
Aplicación (use_cases.py) — Casos de uso / Comandos
      │
      ▼
Dominio (entities.py, events.py, factories.py, exceptions.py)
      │
      ▼
Infraestructura (repository.py, event_publisher.py, cookie_utils.py)
      │
      ▼
Persistencia: PostgreSQL / SQLite  │  Mensajería: RabbitMQ
```

### Endpoints bajo prueba

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|:-------------:|
| `GET` | `/api/health/` | Health check del servicio | No |
| `POST` | `/api/auth/` | Registro de usuario público | No |
| `POST` | `/api/auth/login/` | Autenticación de usuario | No |
| `GET` | `/api/auth/me/` | Perfil del usuario autenticado | Sí (JWT Cookie) |
| `POST` | `/api/auth/logout/` | Cierre de sesión | No |
| `GET` | `/api/auth/by-role/{role}/` | Consulta usuarios por rol | Sí (JWT Cookie) |
| `POST` | `/api/auth/refresh/` | Renovación de token JWT | No (Cookie refresh) |
| `GET` | `/api/users/` | Listar todos los usuarios | Sí (JWT Cookie) |
| `GET` | `/api/users/{id}/` | Obtener usuario por ID | Sí (JWT Cookie) |
| `PATCH` | `/api/users/{id}/` | Actualizar email del usuario | Sí (JWT Cookie) |
| `POST` | `/api/users/{id}/deactivate/` | Desactivar usuario | Sí (JWT Cookie) |
| `DELETE` | `/api/users/{id}/` | Eliminar usuario permanentemente | Sí (JWT Cookie) |

### Historias de Usuario cubiertas

| ID | Historia de Usuario | Prioridad |
|----|---------------------|:---------:|
| US-001 | Registro de usuario público | Alta |
| US-002 | Autenticación de usuario (Login) | Alta |
| US-003 | Obtener perfil del usuario autenticado | Media |
| US-004 | Logout de usuario | Media |
| US-005 | Consultar usuarios por rol | Media |
| US-006 | Health check del servicio | Alta |
| US-007 | Publicación de eventos de dominio | Alta |
| US-008 | Construcción de imagen Docker | Alta |
| US-009 | Ejecución del contenedor con variables de entorno | Alta |
| US-010 | Health check en Docker para orquestación | Alta |
| US-011 | Migración automática de base de datos en arranque | Alta |
| US-012 | Ejecución de tests en contenedor | Media |

---

## 3. Alcance de las Pruebas

### 3.1 Dentro del Alcance

#### 3.1.1 Pruebas de Integración — Endpoints de la API REST

Se verificará que cada endpoint de la API REST responda correctamente ante escenarios positivos y negativos, validando:

- Códigos de estado HTTP según la operación
- Estructura y contenido del cuerpo de respuesta (JSON)
- Establecimiento y limpieza de cookies JWT (`access_token`, `refresh_token`) como `HttpOnly`
- Validación de campos obligatorios y restricciones de serialización
- Propagación correcta de excepciones de dominio a respuestas HTTP
- Autenticación y autorización mediante cookies JWT

**Endpoints cubiertos:**

1. **US-001 — Registro de usuario (`POST /api/auth/`)**
   - Registro exitoso con datos válidos (email, username, password)
   - El usuario creado siempre tiene rol `USER` (el campo `role` no es aceptado en el registro)
   - Rechazo por email duplicado (HTTP 400)
   - Rechazo por password menor a 8 caracteres (HTTP 400)
   - Rechazo por username menor a 3 caracteres (HTTP 400)
   - Rechazo por email con formato inválido (HTTP 400)
   - Se establecen cookies JWT en la respuesta

2. **US-002 — Login de usuario (`POST /api/auth/login/`)**
   - Login exitoso con credenciales válidas (HTTP 200)
   - Verificación de datos del usuario en respuesta (`id`, `email`, `username`, `role`)
   - Login fallido con password incorrecto (HTTP 401)
   - Login fallido con email inexistente (HTTP 401)
   - Login rechazado para usuario inactivo (HTTP 401)
   - Se establecen cookies JWT en la respuesta exitosa

3. **US-003 — Perfil del usuario autenticado (`GET /api/auth/me/`)**
   - Obtención exitosa del perfil con JWT válido (HTTP 200)
   - Rechazo sin autenticación (HTTP 401)
   - Respuesta contiene `id`, `email`, `username`, `role`, `is_active`

4. **US-004 — Logout (`POST /api/auth/logout/`)**
   - Logout exitoso limpia cookies de autenticación (HTTP 200)
   - Logout sin autenticación es permitido (HTTP 200)

5. **US-005 — Consulta por rol (`GET /api/auth/by-role/{role}/`)**
   - Obtener usuarios con rol `ADMIN` (HTTP 200)
   - Obtener usuarios con rol `USER` (HTTP 200)
   - Rol inválido retorna error (HTTP 400)
   - Verificación de que todos los usuarios retornados tienen el rol solicitado

6. **US-006 — Health check (`GET /api/health/`)**
   - Servicio saludable con BD conectada (HTTP 200)
   - Verificación de campos `service`, `status`, `database`

7. **Renovación de token (`POST /api/auth/refresh/`)**
   - Renovación exitosa con refresh_token válido en cookie (HTTP 200)
   - Rechazo sin refresh_token (HTTP 401)
   - Rechazo con refresh_token expirado o inválido (HTTP 401)

8. **Listar usuarios (`GET /api/users/`)**
   - Listado exitoso con autenticación (HTTP 200)
   - Rechazo sin autenticación (HTTP 401)

9. **Obtener usuario por ID (`GET /api/users/{id}/`)**
   - Obtención exitosa de usuario existente (HTTP 200)
   - Usuario no encontrado (HTTP 404)
   - Rechazo sin autenticación (HTTP 401)

10. **Actualizar email (`PATCH /api/users/{id}/`)**
    - Actualización exitosa de email (HTTP 200)
    - Rechazo por email duplicado (HTTP 400)
    - Rechazo por email inválido (HTTP 400)
    - Usuario no encontrado (HTTP 404)

11. **Desactivar usuario (`POST /api/users/{id}/deactivate/`)**
    - Desactivación exitosa (HTTP 200)
    - Verificación de `is_active: false` en respuesta
    - Usuario no encontrado (HTTP 404)

12. **Eliminar usuario (`DELETE /api/users/{id}/`)**
    - Eliminación exitosa (HTTP 204)
    - Usuario no encontrado (HTTP 404)
    - Rechazo sin autenticación (HTTP 401)

#### 3.1.2 Pruebas Unitarias — Capa de Dominio

- Validaciones de la entidad `User` (email, username, reglas de negocio)
- Operación `deactivate()` con manejo de idempotencia (`UserAlreadyInactive`)
- Operación `change_email()` con validaciones
- Factory de creación de usuarios (`UserFactory`)
- Generación de eventos de dominio (`UserCreated`, `UserDeactivated`, `UserEmailChanged`)

#### 3.1.3 Pruebas de Casos de Uso (con mocks)

- `RegisterUserUseCase` — flujo completo con mocks de repositorio y event publisher
- `LoginUseCase` — autenticación con hash SHA-256
- `DeactivateUserUseCase` — desactivación con publicación de eventos
- `ChangeUserEmailUseCase` — cambio de email con validaciones de unicidad
- `GetUsersByRoleUseCase` — filtrado por rol con validación
- `ListUsersUseCase` / `GetUserUseCase` — consultas de lectura

#### 3.1.4 Pruebas de Contenerización — Docker

Se verificará que el servicio funcione correctamente dentro de un entorno contenerizado, validando:

- Construcción exitosa de la imagen Docker a partir del Dockerfile
- La imagen incluye todas las dependencias de `requirements.txt`
- Configuración del servicio mediante variables de entorno
- Health check funcional a nivel de Docker para orquestación
- Ejecución automática de migraciones de BD al iniciar el contenedor
- Ejecución de la suite de tests dentro del contenedor

**Historias de usuario cubiertas:**

1. **US-008 — Construcción de imagen Docker**
   - Build exitoso sin errores
   - Imagen basada en Python 3.12-slim
   - Archivos innecesarios excluidos por `.dockerignore`

2. **US-009 — Configuración por variables de entorno**
   - Arranque con configuración por defecto (puerto 8001, SQLite, DEBUG)
   - Conexión a PostgreSQL mediante `DATABASE_URL`
   - Configuración de `RABBITMQ_HOST`, `CORS_ALLOWED_ORIGINS`, `JWT_SECRET_KEY`

3. **US-010 — Health check en Docker**
   - HEALTHCHECK usa endpoint `/api/health/`
   - Contenedor marcado healthy/unhealthy según respuesta

4. **US-011 — Migraciones automáticas al arrancar**
   - Ejecución de `python manage.py migrate` antes de iniciar el servidor
   - Seed admin creado en primer arranque
   - Fallo de migración impide arranque

5. **US-012 — Tests en contenedor**
   - Tests de dominio pasan sin BD
   - Tests de integración pasan con BD de test
   - Tests de use cases pasan con mocks

### 3.2 Fuera del Alcance

Para cada historia de usuario, los siguientes puntos están fuera del alcance del presente plan de pruebas:

1. **US-001 — Registro de usuario público**
   - Verificación de fortaleza del password (solo se valida longitud mínima)
   - Envío de emails de confirmación de registro
   - Registro con proveedores OAuth externos (Google, GitHub, etc.)

2. **US-002 — Autenticación de usuario (Login)**
   - Login con campos diferentes al email (por ejemplo, username)
   - Implementación de doble factor de autenticación (2FA)
   - Mecanismo de bloqueo por intentos fallidos consecutivos

3. **US-003 — Perfil del usuario autenticado**
   - Actualización completa del perfil (nombre, avatar, preferencias)
   - Historial de sesiones del usuario

4. **US-004 — Logout**
   - Invalidación del token en blacklist del servidor
   - Logout desde todos los dispositivos simultáneamente

5. **US-005 — Consulta por rol**
   - Paginación de resultados
   - Filtrado combinado por múltiples criterios (rol + activo + fecha)

6. **General**
   - Pruebas de carga y estrés (rendimiento bajo alta concurrencia)
   - Pruebas de penetración (seguridad avanzada)
   - Pruebas de interfaz de usuario (el servicio es solo API)

7. **US-008 — Construcción de imagen Docker**
   - Optimización del tamaño de la imagen con multi-stage builds
   - Escaneo de vulnerabilidades de la imagen (Trivy, Snyk)
   - Publicación de la imagen en un registro de contenedores (Docker Hub, ECR)

8. **US-009 — Configuración por variables de entorno**
   - Gestión de secretos con herramientas externas (Vault, AWS Secrets Manager)
   - Validación de variables de entorno obligatorias al arranque

9. **US-010 — Health check en Docker**
   - Health checks de dependencias externas (RabbitMQ, servicios downstream)
   - Métricas de Prometheus / Grafana

10. **US-011 — Migraciones automáticas**
    - Rollback automático de migraciones fallidas
    - Migraciones zero-downtime con esquemas blue/green

11. **US-012 — Tests en contenedor**
    - Tests de rendimiento/carga dentro del contenedor
    - Tests de seguridad de la imagen (CIS benchmarks)

---

## 4. Niveles de Prueba

Se aplicarán los siguientes niveles de prueba, organizados de menor a mayor alcance:

### 4.1 Pruebas Unitarias (Unit Tests)

| Aspecto | Detalle |
|---------|---------|
| **Objetivo** | Verificar el comportamiento de componentes individuales en aislamiento |
| **Alcance** | Entidades de dominio, Value Objects, Factories, excepciones |
| **Dependencias** | Sin dependencias externas (sin BD, sin red) |
| **Herramienta** | `pytest` |
| **Ubicación** | `users/tests/test_domain.py` |

### 4.2 Pruebas de Componente / Casos de Uso (Component Tests)

| Aspecto | Detalle |
|---------|---------|
| **Objetivo** | Verificar la lógica de orquestación de los casos de uso |
| **Alcance** | Use Cases con dependencias mockeadas (repositorio, event publisher) |
| **Dependencias** | Mocks de `UserRepository` y `EventPublisher` |
| **Herramienta** | `pytest` + `unittest.mock` |
| **Ubicación** | `users/application/test_use_cases.py`, `users/tests/test_use_cases.py` |

### 4.3 Pruebas de Integración (Integration Tests)

| Aspecto | Detalle |
|---------|---------|
| **Objetivo** | Verificar el flujo completo HTTP → ViewSet → UseCase → Repository → DB |
| **Alcance** | Endpoints de la API REST con base de datos de test real |
| **Dependencias** | Django Test Client, base de datos SQLite de test, JWT |
| **Herramienta** | `pytest-django` + Django REST Framework `APIClient` |
| **Ubicación** | `users/tests/test_integration.py`, `users/tests/test_auth_cookies.py` |

### 4.4 Pruebas de Regresión

| Aspecto | Detalle |
|---------|---------|
| **Objetivo** | Asegurar que cambios nuevos no rompen funcionalidad existente |
| **Alcance** | Suite completa de tests automatizados |
| **Ejecución** | Automatizada en cada push (CI/CD) |
| **Herramienta** | `pytest` con `--tb=short` |

### 4.5 Pruebas de Contenerización (Containerization Tests)

| Aspecto | Detalle |
|---------|--------|
| **Objetivo** | Verificar que el servicio funciona correctamente dentro de un contenedor Docker |
| **Alcance** | Construcción de imagen, configuración por variables de entorno, health check, migraciones automáticas, ejecución de tests |
| **Dependencias** | Docker, Docker Compose, Dockerfile, docker-compose.yml |
| **Herramienta** | Docker CLI, Docker Compose, `curl` |
| **Ubicación** | Ejecución manual sobre contenedores Docker |

### Pirámide de Pruebas

```
         ╱  ╲
        ╱ E2E ╲           ← Fuera del alcance (no hay UI)
       ╱────────╲
      ╱Contenedor ╲       ← Contenerización Docker (US-008 a US-012)
     ╱──────────────╲
    ╱  Integración    ╲    ← Endpoints API REST (foco principal)
   ╱────────────────────╲
  ╱    Componente        ╲ ← Casos de uso con mocks
 ╱────────────────────────╲
╱       Unitarias          ╲← Dominio (entidades, factories, eventos)
╲──────────────────────────╱
```

---

## 5. Estrategia de las Pruebas

### 5.1 Estrategia de Ejecución

Las pruebas se ejecutarán en el siguiente orden:

1. **Smoke Test** — Se verificará que el servicio esté levantado y el endpoint `/api/health/` responda con status `200` y la base de datos esté conectada. Si el smoke test falla, no se procederá con los demás ciclos.

2. **Ciclo 1 — Pruebas funcionales y de integración** — Se ejecutarán los casos de prueba definidos para cada historia de usuario de acuerdo a los criterios de aceptación establecidos, priorizados por nivel de riesgo. Si se detectan defectos, se reportarán en el Bug Tracker para que el equipo de desarrollo los solucione.

3. **Ciclo 2 — Validación de correcciones** — Se verificarán las correcciones realizadas por el equipo de desarrollo para los defectos reportados en el Ciclo 1.

4. **Ciclo 3 — Regresión** — Se ejecutará un ciclo completo de regresión automatizada para asegurar que las correcciones no introdujeron nuevos defectos.

#### Orden de ejecución por historia de usuario (según priorización de riesgo)

De acuerdo con la identificación de riesgos en la sección 7, las pruebas se abordarán en el siguiente orden:

1. **US-010** — Health check en Docker — Riesgo promedio: **4.50**
2. **US-002** — Autenticación de usuario (Login) — Riesgo promedio: **5.00**
3. **US-001** — Registro de usuario público — Riesgo promedio: **4.14**
4. **US-007** — Publicación de eventos de dominio — Riesgo promedio: **4.00**
5. **US-009** — Configuración por variables de entorno — Riesgo promedio: **4.00**
6. **US-011** — Migraciones automáticas al arrancar — Riesgo promedio: **3.67**
7. **US-005** — Consultar usuarios por rol — Riesgo promedio: **3.33**
8. **US-003** — Obtener perfil del usuario autenticado — Riesgo promedio: **3.00**
9. **US-012** — Ejecución de tests en contenedor — Riesgo promedio: **2.67**
10. **US-006** — Health check del servicio — Riesgo promedio: **2.50**
11. **US-008** — Construcción de imagen Docker — Riesgo promedio: **2.33**
12. **US-004** — Logout de usuario — Riesgo promedio: **2.00**

### 5.2 Estrategia de Datos

- Los datos de prueba se crearán mediante fixtures de Django o directamente usando el `APIClient` de DRF.
- Para las pruebas de integración, cada test creará sus propios datos en una base de datos SQLite de test que se destruye al finalizar.
- Se utilizarán datos generados con la librería `Faker` para campos como email y username en pruebas parametrizadas.
- El usuario administrador seed (migración `0003_seed_admin`) estará disponible en todas las pruebas que lo requieran.
- Las contraseñas de prueba usarán el patrón `password123` (mínimo 8 caracteres) y se hashearán con SHA-256 internamente.

---

## 6. Pruebas de Integración — Endpoints API REST

### 6.1 US-006: Health Check (`GET /api/health/`)

| ID | Escenario | Método | Endpoint | Datos de Entrada | Resultado Esperado | Status |
|----|-----------|--------|----------|------------------|--------------------|--------|
| INT-HC-001 | Health check con BD conectada | `GET` | `/api/health/` | — | `{"service": "users-service", "status": "healthy", "database": "connected"}` | `200` |
| INT-HC-002 | Health check con BD desconectada | `GET` | `/api/health/` | — | `{"status": "unhealthy", "database": "error: ..."}` | `503` |

---

### 6.2 US-001: Registro de Usuario (`POST /api/auth/`)

| ID | Escenario | Método | Endpoint | Datos de Entrada | Resultado Esperado | Status |
|----|-----------|--------|----------|------------------|--------------------|--------|
| INT-REG-001 | Registro exitoso con datos válidos | `POST` | `/api/auth/` | `{"email": "nuevo@test.com", "username": "nuevo", "password": "password123"}` | Respuesta con `user.role = "USER"`, cookies JWT establecidas | `201` |
![alt text](image.png)
| INT-REG-002 | Registro rechaza email duplicado | `POST` | `/api/auth/` | Email ya existente | `{"error": "Ya existe un usuario con el email: ..."}` | `400` |
![alt text](image-1.png)
| INT-REG-003 | Registro rechaza password < 8 chars | `POST` | `/api/auth/` | `{"password": "short"}` | Error de validación | `400` |
![alt text](image-2.png)
| INT-REG-004 | Registro rechaza username < 3 chars | `POST` | `/api/auth/` | `{"username": "ab"}` | Error de validación | `400` |
![alt text](image-3.png)
| INT-REG-005 | Registro rechaza email inválido | `POST` | `/api/auth/` | `{"email": "no-es-email"}` | Error de validación | `400` |
![alt text](image-4.png)
| INT-REG-006 | Registro ignora campo role (seguridad) | `POST` | `/api/auth/` | `{"role": "ADMIN", ...datos válidos}` | `user.role = "USER"` (no ADMIN) | `201` |
![alt text](image-5.png)
| INT-REG-007 | Registro establece cookies HttpOnly | `POST` | `/api/auth/` | Datos válidos | Cookies `access_token` y `refresh_token` presentes, `HttpOnly=True` | `201` |
![alt text](image-6.png)
---

### 6.3 US-002: Login de Usuario (`POST /api/auth/login/`)

| ID | Escenario | Método | Endpoint | Datos de Entrada | Resultado Esperado | Status |
|----|-----------|--------|----------|------------------|--------------------|--------|
| INT-LOG-001 | Login exitoso con credenciales válidas | `POST` | `/api/auth/login/` | `{"email": "nuevo@test.com", "password": "password123"}` | Respuesta con `user.id`, `email`, `username`, `role` | `200` |
![alt text](image-7.png)
| INT-LOG-002 | Login establece cookies JWT | `POST` | `/api/auth/login/` | Credenciales válidas | Cookies `access_token`, `refresh_token` con `HttpOnly` | `200` |
![alt text](image-8.png)
| INT-LOG-003 | Login fallido con password incorrecto | `POST` | `/api/auth/login/` | `{"password": "wrongpass"}` | `{"error": "Credenciales inválidas"}` | `401` |
![alt text](image-9.png)
| INT-LOG-004 | Login fallido con email inexistente | `POST` | `/api/auth/login/` | `{"email": "noexiste@test.com"}` | `{"error": "Credenciales inválidas"}` | `401` |
![alt text](image-10.png)
| INT-LOG-005 | Login rechazado para usuario inactivo | `POST` | `/api/auth/login/` | Email de usuario desactivado | `{"error": "..."}` (usuario inactivo) | `401` |
![alt text](image-11.png)
| INT-LOG-006 | Login sin campo email (incompleto) | `POST` | `/api/auth/login/` | `{"password": "password123"}` | Error de validación serializer | `400` |
![alt text](image-12.png)
| INT-LOG-007 | Login sin campo password (incompleto) | `POST` | `/api/auth/login/` | `{"email": "user@test.com"}` | Error de validación serializer | `400` |
![alt text](image-13.png)

---

### 6.4 US-003: Perfil del Usuario Autenticado (`GET /api/auth/me/`)

| ID | Escenario | Método | Endpoint | Datos de Entrada | Resultado Esperado | Status |
|----|-----------|--------|----------|------------------|--------------------|--------|
| INT-ME-001 | Perfil exitoso con JWT válido | `GET` | `/api/auth/me/` | Cookie `access_token` válida | `{"id", "email", "username", "role", "is_active"}` | `200` |
![alt text](image-14.png)
| INT-ME-002 | Perfil rechazado sin autenticación | `GET` | `/api/auth/me/` | Sin cookies JWT | Error de autenticación | `401` |
![alt text](image-15.png)
| INT-ME-003 | Perfil rechazado con token expirado | `GET` | `/api/auth/me/` | Cookie `access_token` expirada | Error de autenticación | `401` |

---

### 6.5 US-004: Logout (`POST /api/auth/logout/`)

| ID | Escenario | Método | Endpoint | Datos de Entrada | Resultado Esperado | Status |
|----|-----------|--------|----------|------------------|--------------------|--------|
| INT-OUT-001 | Logout exitoso limpia cookies | `POST` | `/api/auth/logout/` | Usuario autenticado | `{"detail": "Sesión cerrada"}`, cookies eliminadas | `200` |
![alt text](image-16.png)
![alt text](image-17.png)
| INT-OUT-002 | Logout sin autenticación permitido | `POST` | `/api/auth/logout/` | Sin cookies | `{"detail": "Sesión cerrada"}` | `200` |
![alt text](image-18.png)

---

### 6.6 US-005: Consulta por Rol (`GET /api/auth/by-role/{role}/`)

| ID | Escenario | Método | Endpoint | Datos de Entrada | Resultado Esperado | Status |
|----|-----------|--------|----------|------------------|--------------------|--------|
| INT-ROL-001 | Usuarios con rol ADMIN | `GET` | `/api/auth/by-role/ADMIN/` | JWT válido | Lista donde todos tienen `role: "ADMIN"` | `200` |
![alt text](image-19.png)
| INT-ROL-002 | Usuarios con rol USER | `GET` | `/api/auth/by-role/USER/` | JWT válido | Lista donde todos tienen `role: "USER"` | `200` |
![alt text](image-20.png)
| INT-ROL-003 | Rol inválido retorna error | `GET` | `/api/auth/by-role/SUPERADMIN/` | JWT válido | `{"error": "Rol inválido: SUPERADMIN..."}` | `400` |
![alt text](image-21.png)
| INT-ROL-004 | Sin autenticación rechazado | `GET` | `/api/auth/by-role/USER/` | Sin JWT | Error de autenticación | `401` |
![alt text](image-22.png)

---

### 6.7 Renovación de Token (`POST /api/auth/refresh/`)

| ID | Escenario | Método | Endpoint | Datos de Entrada | Resultado Esperado | Status |
|----|-----------|--------|----------|------------------|--------------------|--------|
| INT-REF-001 | Refresh exitoso con cookie válida | `POST` | `/api/auth/refresh/` | Cookie `refresh_token` válida | `{"detail": "Token renovado"}`, nuevas cookies | `200` |
![alt text](image-23.png)
| INT-REF-002 | Refresh sin cookie refresh_token | `POST` | `/api/auth/refresh/` | Sin cookie | `{"error": "Refresh token no encontrado"}` | `401` |
![alt text](image-25.png)
| INT-REF-003 | Refresh con token inválido | `POST` | `/api/auth/refresh/` | Cookie `refresh_token` corrupta | `{"error": "Refresh token inválido o expirado"}` | `401` |
![alt text](image-24.png)

---

### 6.8 Listar Usuarios (`GET /api/users/`)

| ID | Escenario | Método | Endpoint | Datos de Entrada | Resultado Esperado | Status |
|----|-----------|--------|----------|------------------|--------------------|--------|
| INT-LST-001 | Listado exitoso con autenticación | `GET` | `/api/users/` | JWT válido | Array de usuarios con `id`, `email`, `username`, `role`, `is_active` | `200` |
| INT-LST-002 | Listado rechazado sin autenticación | `GET` | `/api/users/` | Sin JWT | Error de autenticación | `401` |

---

### 6.9 Obtener Usuario por ID (`GET /api/users/{id}/`)

| ID | Escenario | Método | Endpoint | Datos de Entrada | Resultado Esperado | Status |
|----|-----------|--------|----------|------------------|--------------------|--------|
| INT-GET-001 | Usuario encontrado | `GET` | `/api/users/{id}/` | ID existente, JWT válido | Datos del usuario | `200` |
| INT-GET-002 | Usuario no encontrado | `GET` | `/api/users/{id}/` | ID inexistente, JWT válido | `{"error": "Usuario {id} no encontrado"}` | `404` |
| INT-GET-003 | Sin autenticación rechazado | `GET` | `/api/users/{id}/` | Sin JWT | Error de autenticación | `401` |

---

### 6.10 Actualizar Email (`PATCH /api/users/{id}/`)

| ID | Escenario | Método | Endpoint | Datos de Entrada | Resultado Esperado | Status |
|----|-----------|--------|----------|------------------|--------------------|--------|
| INT-UPD-001 | Actualización exitosa de email | `PATCH` | `/api/users/{id}/` | `{"email": "nuevo@test.com"}`, JWT válido | Usuario con email actualizado | `200` |
| INT-UPD-002 | Email duplicado rechazado | `PATCH` | `/api/users/{id}/` | Email ya existente | Error de duplicado | `400` |
| INT-UPD-003 | Email inválido rechazado | `PATCH` | `/api/users/{id}/` | `{"email": "invalido"}` | Error de validación | `400` |
| INT-UPD-004 | Usuario no encontrado | `PATCH` | `/api/users/{uuid}/` | ID inexistente | `{"error": "Usuario {id} no encontrado"}` | `404` |

---

### 6.11 Desactivar Usuario (`POST /api/users/{id}/deactivate/`)

| ID | Escenario | Método | Endpoint | Datos de Entrada | Resultado Esperado | Status |
|----|-----------|--------|----------|------------------|--------------------|--------|
| INT-DEA-001 | Desactivación exitosa | `POST` | `/api/users/{id}/deactivate/` | `{"reason": "Motivo"}`, JWT válido | Usuario con `is_active: false` | `200` |
| INT-DEA-002 | Desactivación sin razón (opcional) | `POST` | `/api/users/{id}/deactivate/` | `{}`, JWT válido | Usuario con `is_active: false` | `200` |
| INT-DEA-003 | Usuario no encontrado | `POST` | `/api/users/{id}/deactivate/` | ID inexistente | `{"error": "Usuario {id} no encontrado"}` | `404` |

---

### 6.12 Eliminar Usuario (`DELETE /api/users/{id}/`)

| ID | Escenario | Método | Endpoint | Datos de Entrada | Resultado Esperado | Status |
|----|-----------|--------|----------|------------------|--------------------|--------|
| INT-DEL-001 | Eliminación exitosa | `DELETE` | `/api/users/{id}/` | JWT válido | Sin cuerpo | `204` |
| INT-DEL-002 | Usuario no encontrado | `DELETE` | `/api/users/{id}/` | ID inexistente | `{"error": "Usuario {id} no encontrado"}` | `404` |
| INT-DEL-003 | Sin autenticación rechazado | `DELETE` | `/api/users/{id}/` | Sin JWT | Error de autenticación | `401` |

---

## 6.13 US-008: Construcción de Imagen Docker

| ID | Escenario | Comando/Acción | Datos de Entrada | Resultado Esperado | Verificación |
|----|-----------|----------------|------------------|--------------------|--------------|
| CNT-BLD-001 | Build exitoso de la imagen | `docker build -t users-service .` | Dockerfile válido | Imagen construida sin errores, base Python 3.12-slim | `OK` |
| CNT-BLD-002 | Dependencias instaladas en la imagen | `docker run users-service pip list` | — | Todas las dependencias de `requirements.txt` presentes | `OK` |
| CNT-BLD-003 | Archivos innecesarios excluidos | `docker run users-service ls -la` | `.dockerignore` configurado | Sin directorio `venv` ni archivos `.git` en la imagen | `OK` |

---

### 6.14 US-009: Configuración por Variables de Entorno

| ID | Escenario | Comando/Acción | Datos de Entrada | Resultado Esperado | Verificación |
|----|-----------|----------------|------------------|--------------------|--------------|
| CNT-ENV-001 | Arranque con configuración por defecto | `docker run users-service` | Sin variables de entorno | Servicio inicia en puerto 8001, SQLite, DEBUG activo | `OK` |
| CNT-ENV-002 | PostgreSQL por variable de entorno | `docker run -e DATABASE_URL=postgres://... users-service` | `DATABASE_URL` | Conexión a PostgreSQL exitosa, migraciones aplicadas | `OK` |
| CNT-ENV-003 | RabbitMQ host configurable | `docker run -e RABBITMQ_HOST=rabbitmq users-service` | `RABBITMQ_HOST` | Event publisher se conecta al host especificado | `OK` |
| CNT-ENV-004 | CORS configurable | `docker run -e CORS_ALLOWED_ORIGINS=http://frontend:3000 users-service` | `CORS_ALLOWED_ORIGINS` | Servicio acepta requests desde origen configurado | `OK` |
| CNT-ENV-005 | JWT Secret Key configurable | `docker run -e JWT_SECRET_KEY=mi-clave-secreta users-service` | `JWT_SECRET_KEY` | Tokens firmados con la clave proporcionada | `OK` |

---

### 6.15 US-010: Health Check en Docker

| ID | Escenario | Comando/Acción | Datos de Entrada | Resultado Esperado | Verificación |
|----|-----------|----------------|------------------|--------------------|--------------|
| CNT-HCK-001 | Health check marca contenedor como healthy | `docker inspect --format='{{.State.Health.Status}}'` | BD accesible | `GET /api/health/` retorna `200`, contenedor marcado `healthy` | `OK` |
| CNT-HCK-002 | Health check marca contenedor como unhealthy | — | BD inaccesible | `GET /api/health/` retorna `503`, contenedor marcado `unhealthy` | `OK` |

---

### 6.16 US-011: Migraciones Automáticas al Arrancar

| ID | Escenario | Comando/Acción | Datos de Entrada | Resultado Esperado | Verificación |
|----|-----------|----------------|------------------|--------------------|--------------|
| CNT-MIG-001 | Primer arranque aplica migraciones | `docker run users-service` | BD vacía | `python manage.py migrate` ejecutado, migración `0003_seed_admin` crea usuario admin | `OK` |
| CNT-MIG-002 | Arranque posterior sin errores | `docker run users-service` | Migraciones ya aplicadas | Comando `migrate` no produce errores, servicio inicia normalmente | `OK` |
| CNT-MIG-003 | Fallo de migración impide arranque | `docker run users-service` | BD inaccesible | Proceso falla con exit code ≠ 0, servicio no inicia | `FAIL` |

---

### 6.17 US-012: Ejecución de Tests en Contenedor

| ID | Escenario | Comando/Acción | Datos de Entrada | Resultado Esperado | Verificación |
|----|-----------|----------------|------------------|--------------------|--------------|
| CNT-TST-001 | Tests de dominio pasan sin BD | `docker run users-service pytest users/tests/test_domain.py` | — | Todos los tests de dominio pasan, sin conexión a BD | `OK` |
| CNT-TST-002 | Tests de integración pasan | `docker run users-service pytest users/tests/test_integration.py` | BD de test SQLite | Django crea BD de test, todos los tests pasan | `OK` |
| CNT-TST-003 | Tests de use cases pasan | `docker run users-service pytest users/application/test_use_cases.py` | Mocks | Todos los tests de use cases pasan | `OK` |

---

## 7. Análisis de Riesgo — Matriz de Riesgos por Criterio de Aceptación

La probabilidad está definida en un rango de 1 a 3:
- **1** = Probabilidad baja
- **2** = Probabilidad media
- **3** = Probabilidad alta

El impacto está definido en un rango de 1 a 3:
- **1** = Impacto bajo
- **2** = Impacto medio
- **3** = Impacto alto

**Riesgo = Probabilidad × Impacto**

Tipo de ejecución: **Manual** o **Automatizada**.

---

### US-001: Registro de usuario público

| Criterio de Aceptación | Prob. | Imp. | Riesgo | Tipo |
|------------------------|:-----:|:----:|:------:|------|
| CA001: El endpoint `POST /api/auth/` permite registrar un usuario con email, username y password válidos, retornando status 201 con rol USER. | 1 | 3 | 3 | Automatizada |
| CA002: Al enviar un email ya registrado, el sistema retorna status 400 con mensaje de error indicando que el email ya existe. | 2 | 3 | 6 | Automatizada |
| CA003: Al enviar un password con menos de 8 caracteres, el sistema retorna status 400 con error de validación. | 1 | 2 | 2 | Automatizada |
| CA004: Al enviar un username con menos de 3 caracteres, el sistema retorna status 400 con error de validación. | 1 | 2 | 2 | Automatizada |
| CA005: Al enviar un email con formato inválido, el sistema retorna status 400 con error de validación. | 1 | 3 | 3 | Automatizada |
| CA006: Si se envía el campo `role: "ADMIN"` en el registro, el sistema lo ignora y crea el usuario con rol USER (seguridad). | 2 | 3 | 6 | Automatizada |
| CA007: La respuesta exitosa de registro establece cookies `access_token` y `refresh_token` como HttpOnly. | 2 | 3 | 6 | Automatizada |

**Promedio del riesgo: 4.00**

---

### US-002: Autenticación de usuario (Login)

| Criterio de Aceptación | Prob. | Imp. | Riesgo | Tipo |
|------------------------|:-----:|:----:|:------:|------|
| CA001: El endpoint `POST /api/auth/login/` autentica exitosamente con email y password válidos, retornando status 200 con datos del usuario. | 1 | 3 | 3 | Automatizada |
| CA002: La respuesta exitosa de login contiene `id`, `email`, `username`, `role` del usuario. | 1 | 2 | 2 | Automatizada |
| CA003: Al enviar credenciales inválidas (password incorrecto), el sistema retorna status 401 con mensaje "Credenciales inválidas". | 2 | 3 | 6 | Automatizada |
| CA004: Al enviar un email que no existe en el sistema, retorna status 401. | 2 | 3 | 6 | Automatizada |
| CA005: Al intentar login con un usuario desactivado, el sistema retorna status 401 indicando usuario inactivo. | 2 | 3 | 6 | Automatizada |
| CA006: La respuesta exitosa establece cookies JWT `access_token` y `refresh_token` como HttpOnly. | 2 | 3 | 6 | Automatizada |
| CA007: Sin campo email o password, el sistema retorna status 400 por validación del serializer. | 1 | 1 | 1 | Manual |

**Promedio del riesgo: 4.29**

---

### US-003: Obtener perfil del usuario autenticado

| Criterio de Aceptación | Prob. | Imp. | Riesgo | Tipo |
|------------------------|:-----:|:----:|:------:|------|
| CA001: El endpoint `GET /api/auth/me/` retorna los datos del usuario autenticado con status 200. | 1 | 2 | 2 | Automatizada |
| CA002: La respuesta contiene `id`, `email`, `username`, `role`, `is_active`. | 1 | 2 | 2 | Automatizada |
| CA003: Sin token JWT válido, el sistema retorna status 401. | 2 | 3 | 6 | Automatizada |
| CA004: Con token JWT expirado, el sistema retorna status 401. | 1 | 2 | 2 | Manual |

**Promedio del riesgo: 3.00**

---

### US-004: Logout de usuario

| Criterio de Aceptación | Prob. | Imp. | Riesgo | Tipo |
|------------------------|:-----:|:----:|:------:|------|
| CA001: El endpoint `POST /api/auth/logout/` retorna status 200 y limpia las cookies de autenticación. | 1 | 2 | 2 | Automatizada |
| CA002: El logout es accesible sin autenticación (permite limpiar cookies expiradas). | 1 | 2 | 2 | Manual |

**Promedio del riesgo: 2.00**

---

### US-005: Consultar usuarios por rol

| Criterio de Aceptación | Prob. | Imp. | Riesgo | Tipo |
|------------------------|:-----:|:----:|:------:|------|
| CA001: El endpoint `GET /api/auth/by-role/ADMIN/` retorna lista de usuarios con rol ADMIN y status 200. | 1 | 2 | 2 | Automatizada |
| CA002: El endpoint `GET /api/auth/by-role/USER/` retorna lista de usuarios con rol USER y status 200. | 1 | 2 | 2 | Automatizada |
| CA003: Al enviar un rol inválido (ej: `SUPERADMIN`), el sistema retorna status 400 con mensaje de error. | 2 | 3 | 6 | Automatizada |

**Promedio del riesgo: 3.33**

---

### US-006: Health check del servicio

| Criterio de Aceptación | Prob. | Imp. | Riesgo | Tipo |
|------------------------|:-----:|:----:|:------:|------|
| CA001: El endpoint `GET /api/health/` retorna status 200 con `"status": "healthy"` y `"database": "connected"` cuando la BD está accesible. | 1 | 3 | 3 | Automatizada |
| CA002: Cuando la base de datos no está accesible, retorna status 503 con `"status": "unhealthy"`. | 1 | 2 | 2 | Manual |

**Promedio del riesgo: 2.50**

---

### US-007: Publicación de eventos de dominio

| Criterio de Aceptación | Prob. | Imp. | Riesgo | Tipo |
|------------------------|:-----:|:----:|:------:|------|
| CA001: Al registrar un usuario exitosamente, se publica un evento `UserCreated` con routing key `user.created` conteniendo `user_id`, `email`, `username`. | 2 | 3 | 6 | Automatizada |
| CA002: Al desactivar un usuario activo, se publica un evento `UserDeactivated` con routing key `user.deactivated` conteniendo `user_id` y `reason`. | 2 | 3 | 6 | Automatizada |
| CA003: Si RabbitMQ no está disponible, la operación (registro/desactivación) se completa exitosamente y el error de publicación se registra en logs. | 1 | 2 | 2 | Manual |
| CA004: Al cambiar email de un usuario, se publica un evento `UserEmailChanged` con `old_email` y `new_email`. | 2 | 1 | 2 | Automatizada |

**Promedio del riesgo: 4.00**

---

### US-008: Construcción de imagen Docker

| Criterio de Aceptación | Prob. | Imp. | Riesgo | Tipo |
|------------------------|:-----:|:----:|:------:|------|
| CA001: La imagen se construye exitosamente con `docker build` usando Python 3.12-slim como base y sin errores. | 1 | 3 | 3 | Manual |
| CA002: Las dependencias de `requirements.txt` están instaladas correctamente en la imagen. | 1 | 3 | 3 | Manual |
| CA003: La imagen no contiene archivos innecesarios (`venv`, `.git`) gracias al `.dockerignore`. | 1 | 1 | 1 | Manual |

**Promedio del riesgo: 2.33**

---

### US-009: Configuración por variables de entorno

| Criterio de Aceptación | Prob. | Imp. | Riesgo | Tipo |
|------------------------|:-----:|:----:|:------:|------|
| CA001: El contenedor arranca con configuración por defecto (puerto 8001, SQLite, DEBUG activo) sin variables de entorno. | 1 | 2 | 2 | Manual |
| CA002: El contenedor se conecta a PostgreSQL cuando `DATABASE_URL` está configurado y las migraciones se aplican correctamente. | 2 | 3 | 6 | Manual |
| CA003: El event publisher se conecta al `RABBITMQ_HOST` especificado por variable de entorno. | 2 | 2 | 4 | Manual |
| CA004: El servicio acepta requests desde el origen configurado en `CORS_ALLOWED_ORIGINS`. | 1 | 2 | 2 | Manual |
| CA005: Los tokens JWT se firman con la clave proporcionada en `JWT_SECRET_KEY`. | 2 | 3 | 6 | Manual |

**Promedio del riesgo: 4.00**

---

### US-010: Health check en Docker para orquestación

| Criterio de Aceptación | Prob. | Imp. | Riesgo | Tipo |
|------------------------|:-----:|:----:|:------:|------|
| CA001: Docker HEALTHCHECK consulta `GET /api/health/` en puerto 8001 y marca el contenedor como healthy si recibe status 200. | 1 | 3 | 3 | Manual |
| CA002: El contenedor se marca como unhealthy si el health check recibe status 503 y el orquestador lo reinicia tras reintentos consecutivos. | 2 | 3 | 6 | Manual |

**Promedio del riesgo: 4.50**

---

### US-011: Migración automática de base de datos en arranque

| Criterio de Aceptación | Prob. | Imp. | Riesgo | Tipo |
|------------------------|:-----:|:----:|:------:|------|
| CA001: El primer arranque ejecuta `python manage.py migrate` antes de iniciar el servidor, aplicando todas las migraciones incluyendo `0003_seed_admin`. | 1 | 3 | 3 | Manual |
| CA002: Arranques posteriores no fallan con migraciones ya aplicadas y el servicio inicia normalmente. | 1 | 2 | 2 | Manual |
| CA003: Si la base de datos no está accesible, el proceso falla con código de salida distinto de 0 y el servicio no inicia. | 2 | 3 | 6 | Manual |

**Promedio del riesgo: 3.67**

---

### US-012: Ejecución de tests en contenedor

| Criterio de Aceptación | Prob. | Imp. | Riesgo | Tipo |
|------------------------|:-----:|:----:|:------:|------|
| CA001: Los tests de dominio pasan sin base de datos dentro del contenedor Docker. | 1 | 2 | 2 | Automatizada |
| CA002: Los tests de integración pasan con base de datos de test SQLite creada por Django. | 2 | 2 | 4 | Automatizada |
| CA003: Los tests de use cases pasan con mocks dentro del contenedor. | 1 | 2 | 2 | Automatizada |

**Promedio del riesgo: 2.67**

---

### Resumen de Priorización por Riesgo

| Prioridad | Historia de Usuario | Riesgo Promedio |
|:---------:|---------------------|:---------------:|
| 1 | US-010 — Health check en Docker | **4.50** |
| 2 | US-002 — Login de Usuario | **4.29** |
| 3 | US-001 — Registro de usuario | **4.00** |
| 4 | US-007 — Publicación de eventos | **4.00** |
| 5 | US-009 — Configuración por variables de entorno | **4.00** |
| 6 | US-011 — Migraciones automáticas al arrancar | **3.67** |
| 7 | US-005 — Consulta por rol | **3.33** |
| 8 | US-003 — Perfil autenticado | **3.00** |
| 9 | US-012 — Tests en contenedor | **2.67** |
| 10 | US-006 — Health check | **2.50** |
| 11 | US-008 — Construcción de imagen Docker | **2.33** |
| 12 | US-004 — Logout | **2.00** |

---

## 8. Gestión de Riesgos — ISO/IEC 25010:2023

Esta sección identifica, categoriza, evalúa y prioriza los riesgos del sistema basándose en el estándar **ISO/IEC 25010:2023** (Modelo de calidad de producto de software), que define ocho características de calidad:

1. Adecuación Funcional
2. Eficiencia de Desempeño
3. Compatibilidad
4. Usabilidad
5. Fiabilidad
6. Seguridad
7. Mantenibilidad
8. Portabilidad

Los riesgos se mapean a estas características para asegurar una cobertura exhaustiva y sistemática.

### Escala de evaluación

| Nivel | Probabilidad | Impacto |
|:-----:|:------------|:--------|
| **1** | Baja — Poco probable que ocurra | Bajo — Efecto mínimo en el sistema |
| **2** | Media — Puede ocurrir bajo ciertas condiciones | Medio — Afecta funcionalidad parcial |
| **3** | Alta — Es probable o ya se ha manifestado | Alto — Afecta funcionalidad crítica o seguridad |

**Severidad = Probabilidad × Impacto** (rango 1–9)

| Severidad | Clasificación | Acción |
|:---------:|:-------------|:-------|
| 1–2 | 🟢 Baja | Monitorear |
| 3–4 | 🟡 Media | Mitigar con pruebas regulares |
| 6 | 🟠 Alta | Mitigar con pruebas automatizadas y plan de acción |
| 9 | 🔴 Crítica | Acción inmediata, bloqueo de release |

---

### 8.1 Adecuación Funcional

> *Grado en que el producto proporciona funciones que satisfacen las necesidades declaradas e implícitas cuando se usa bajo condiciones especificadas.*

| ID | Riesgo | Subcaracterística | Prob. | Imp. | Sev. | Endpoint Afectado | Mitigación |
|----|--------|-------------------|:-----:|:----:|:----:|-------------------|------------|
| AF-001 | El registro no valida correctamente el formato de email, permitiendo emails inválidos en la BD | Completitud Funcional | 2 | 3 | 🟠 6 | `POST /api/auth/` | Pruebas automatizadas con emails inválidos (sin @, sin dominio, caracteres especiales). Validación en serializer + entidad de dominio. |
| AF-002 | El login permite acceso a usuarios desactivados, violando la regla de negocio de bloqueo | Corrección Funcional | 2 | 3 | 🟠 6 | `POST /api/auth/login/` | Test de integración: crear usuario → desactivar → intentar login. Validación en `LoginUseCase`. |
| AF-003 | El endpoint de desactivación no genera evento `UserDeactivated`, rompiendo la cadena EDA | Completitud Funcional | 2 | 3 | 🟠 6 | `POST /api/users/{id}/deactivate/` | Test con mock de `EventPublisher` para verificar publicación. Revisión de código en `DeactivateUserUseCase`. |
| AF-004 | El cambio de email no verifica unicidad contra otros usuarios, causando duplicados | Corrección Funcional | 2 | 3 | 🟠 6 | `PATCH /api/users/{id}/` | Test de integración: crear 2 usuarios, intentar cambiar email al de otro. Validación en `ChangeUserEmailUseCase`. |
| AF-005 | El filtrado por rol no retorna resultados completos o incluye usuarios de otros roles | Pertinencia Funcional | 1 | 2 | 🟢 2 | `GET /api/auth/by-role/{role}/` | Test: crear usuarios mixtos y verificar que el filtro retorna solo los del rol solicitado. |
| AF-006 | El health check reporta `healthy` cuando la BD está desconectada (falso positivo) | Corrección Funcional | 1 | 3 | 🟡 3 | `GET /api/health/` | Test de health check con BD desconectada (mock de `connection.ensure_connection()`). |
| AF-007 | La eliminación de un usuario no lo borra realmente de la BD (soft delete no implementado en destroy) | Completitud Funcional | 1 | 2 | 🟢 2 | `DELETE /api/users/{id}/` | Test: eliminar usuario, luego intentar obtenerlo con GET → debe retornar 404. |

---

### 8.2 Eficiencia de Desempeño

> *Desempeño relativo a la cantidad de recursos utilizados bajo condiciones determinadas.*

| ID | Riesgo | Subcaracterística | Prob. | Imp. | Sev. | Endpoint Afectado | Mitigación |
|----|--------|-------------------|:-----:|:----:|:----:|-------------------|------------|
| ED-001 | El endpoint de listar usuarios (`GET /api/users/`) no implementa paginación, retornando todos los registros y degradando rendimiento con volúmenes altos | Comportamiento Temporal | 2 | 2 | 🟡 4 | `GET /api/users/` | Monitorear tiempos de respuesta. Plan futuro: implementar paginación con `LimitOffsetPagination`. |
| ED-002 | Consultas a BD sin índices óptimos en campos de filtrado frecuente | Utilización de Recursos | 1 | 2 | 🟢 2 | Todos | Verificar que los índices definidos en `Meta.indexes` (`email`, `username`) se aplican. |
| ED-003 | La generación de tokens JWT en cada registro/login introduce latencia de hashing | Comportamiento Temporal | 1 | 1 | 🟢 1 | `POST /api/auth/`, `POST /api/auth/login/` | Monitorear. El overhead de JWT es aceptable para el volumen esperado. |
| ED-004 | La conexión a RabbitMQ en cada publicación de evento puede generar timeouts si el broker está lento | Comportamiento Temporal | 2 | 2 | 🟡 4 | `POST /api/auth/`, `POST /api/users/{id}/deactivate/` | Implementar timeout configurable. El `RabbitMQEventPublisher` ya maneja errores silenciosamente. |

---

### 8.3 Compatibilidad

> *Grado en que un producto puede intercambiar información con otros productos y/o realizar sus funciones requeridas mientras comparte el mismo entorno.*

| ID | Riesgo | Subcaracterística | Prob. | Imp. | Sev. | Endpoint Afectado | Mitigación |
|----|--------|-------------------|:-----:|:----:|:----:|-------------------|------------|
| CO-001 | Las cookies JWT HttpOnly no son compatibles con clientes que no soportan cookies (aplicaciones móviles nativas, herramientas CLI) | Interoperabilidad | 2 | 2 | 🟡 4 | Todos los endpoints autenticados | Documentar limitación. Considerar endpoint alternativo que retorne tokens en body para clientes no-browser. |
| CO-002 | Los eventos publicados a RabbitMQ tienen un formato no documentado, dificultando el consumo por otros microservicios | Interoperabilidad | 2 | 3 | 🟠 6 | Eventos `UserCreated`, `UserDeactivated` | Documentar schema de eventos en formato AsyncAPI. Tests de contrato para validar estructura. |
| CO-003 | Configuración de CORS no permite consumo desde dominios no configurados | Coexistencia | 1 | 2 | 🟢 2 | Todos | Verificar variable `CORS_ALLOWED_ORIGINS`. Test manual con frontend en diferente dominio. |

---

### 8.4 Usabilidad

> *Grado en que un producto puede ser utilizado por usuarios específicos para lograr objetivos específicos con eficacia, eficiencia y satisfacción.*

| ID | Riesgo | Subcaracterística | Prob. | Imp. | Sev. | Endpoint Afectado | Mitigación |
|----|--------|-------------------|:-----:|:----:|:----:|-------------------|------------|
| US-001 | Los mensajes de error no son suficientemente descriptivos para que el cliente de la API determine la causa del fallo | Reconocimiento de Adecuación | 2 | 2 | 🟡 4 | Todos | Revisar mensajes de error en excepciones de dominio. Verificar que incluyan campo afectado y razón. |
| US-002 | La API no retorna información de validaciones en formato estandarizado (ej: RFC 7807 Problem Details) | Operabilidad | 1 | 1 | 🟢 1 | Todos los endpoints con validación | Monitorear. DRF tiene su propio formato de errores de validación. |
| US-003 | La respuesta de registro no indica claramente que los tokens se establecen como cookies, confundiendo a desarrolladores frontend | Facilidad de Aprendizaje | 2 | 1 | 🟢 2 | `POST /api/auth/`, `POST /api/auth/login/` | Documentar en README y OpenAPI que los tokens se envían como cookies `HttpOnly`. |

---

### 8.5 Fiabilidad

> *Grado en que un sistema realiza funciones específicas bajo condiciones específicas durante un período de tiempo establecido.*

| ID | Riesgo | Subcaracterística | Prob. | Imp. | Sev. | Endpoint Afectado | Mitigación |
|----|--------|-------------------|:-----:|:----:|:----:|-------------------|------------|
| FI-001 | La caída de RabbitMQ causa que las operaciones de registro/desactivación fallen completamente | Tolerancia a Fallos | 1 | 3 | 🟡 3 | `POST /api/auth/`, `POST /api/users/{id}/deactivate/` | Verificar que `RabbitMQEventPublisher` tiene try/catch. Test: ejecutar operación sin RabbitMQ → debe completarse. |
| FI-002 | Una interrupción de red durante la persistencia de un usuario deja datos inconsistentes (sin rollback transaccional) | Recuperabilidad | 1 | 3 | 🟡 3 | `POST /api/auth/`, `PATCH /api/users/{id}/` | Verificar transaccionalidad Django (`@transaction.atomic`). Revisar que el repositorio maneja errores de BD. |
| FI-003 | El servicio no se recupera automáticamente después de una caída de la BD | Disponibilidad | 2 | 3 | 🟠 6 | Todos | Verificar health check para detección. Docker health check reinicia contenedor unhealthy. |
| FI-004 | Los tokens JWT no se invalidan del lado del servidor al desactivar un usuario, permitiendo acceso temporal | Madurez | 2 | 3 | 🟠 6 | `GET /api/auth/me/`, todos los protegidos | Documentar como limitación conocida. El token expira naturalmente. Considerar blacklist JWT. |

---

### 8.6 Seguridad

> *Grado en que un producto protege la información y los datos de manera que las personas u otros productos tengan el grado de acceso adecuado a su tipo y nivel de autorización.*

| ID | Riesgo | Subcaracterística | Prob. | Imp. | Sev. | Endpoint Afectado | Mitigación |
|----|--------|-------------------|:-----:|:----:|:----:|-------------------|------------|
| SE-001 | Un usuario puede escalar privilegios enviando `role: "ADMIN"` en el registro público | Confidencialidad | 1 | 3 | 🟡 3 | `POST /api/auth/` | Test INT-REG-006: verificar que el campo `role` es ignorado. `RegisterUserSerializer` no expone `role`. |
| SE-002 | Las contraseñas se almacenan con SHA-256 simple sin sal (salt), vulnerable a ataques de rainbow tables | Integridad | 2 | 3 | 🟠 6 | `POST /api/auth/`, `POST /api/auth/login/` | Evaluar migración a `bcrypt` o `argon2`. Documentar como riesgo de seguridad conocido. |
| SE-003 | Los endpoints protegidos no validan que el usuario accedido sea el propio (IDOR — Insecure Direct Object Reference) | Autenticidad | 2 | 3 | 🟠 6 | `PATCH /api/users/{id}/`, `DELETE /api/users/{id}/` | Test: autenticarse como usuario A, intentar modificar/eliminar usuario B. Implementar verificación de propiedad o rol ADMIN. |
| SE-004 | El endpoint `DELETE /api/users/{id}/` permite eliminación permanente sin confirmación adicional ni log de auditoría | No Repudio | 2 | 3 | 🟠 6 | `DELETE /api/users/{id}/` | Implementar log de auditoría. Considerar requerir header de confirmación. Test de integración. |
| SE-005 | El `JWT_SECRET_KEY` tiene un valor por defecto en settings.py, comprometiendo tokens en producción | Confidencialidad | 3 | 3 | 🔴 9 | Todos los endpoints autenticados | **ACCIÓN INMEDIATA**: Verificar que `SECRET_KEY` se configura por variable de entorno en producción. Bloquear deploy sin configuración. |
| SE-006 | Las cookies JWT no configuran correctamente `Secure`, `SameSite` y `Path`, exponiendo tokens | Confidencialidad | 2 | 3 | 🟠 6 | Todos | Verificar configuración en `set_auth_cookies()`. Test: inspeccionar atributos de cookies en respuesta. |
| SE-007 | No existe rate limiting para endpoints de login, permitiendo ataques de fuerza bruta | Resistencia | 3 | 3 | 🔴 9 | `POST /api/auth/login/` | **ACCIÓN INMEDIATA**: Implementar `django-ratelimit` o throttling de DRF. Prioridad máxima. |

---

### 8.7 Mantenibilidad

> *Grado de eficacia y eficiencia con que un producto puede ser modificado por los mantenedores previstos.*

| ID | Riesgo | Subcaracterística | Prob. | Imp. | Sev. | Componente Afectado | Mitigación |
|----|--------|-------------------|:-----:|:----:|:----:|---------------------|------------|
| MA-001 | La capa de presentación (views.py) contiene lógica que debería estar en casos de uso, dificultando testing | Modularidad | 1 | 2 | 🟢 2 | `users/views.py` | Revisión de código. Verificar que ViewSets sean thin controllers. Cobertura de tests de integración. |
| MA-002 | Las excepciones de dominio no cubren todos los flujos de error, causando HTTP 500 genéricos | Analizabilidad | 2 | 2 | 🟡 4 | Todos | Test: provocar errores inesperados y verificar que el catch-all retorna mensaje apropiado. Agregar excepciones faltantes. |
| MA-003 | No existe documentación de API (OpenAPI/Swagger), dificultando integración con otros equipos | Reutilización | 2 | 2 | 🟡 4 | API en general | Implementar `drf-spectacular` para generar documentación automática. |
| MA-004 | Los tests no cubren escenarios de concurrencia (dos registros simultáneos con mismo email) | Testabilidad | 2 | 2 | 🟡 4 | `POST /api/auth/` | Implementar unique constraint a nivel de BD. Test de concurrencia con threading. |

---

### 8.8 Portabilidad

> *Grado de eficacia y eficiencia con que un sistema puede ser transferido de un entorno a otro.*

| ID | Riesgo | Subcaracterística | Prob. | Imp. | Sev. | Componente Afectado | Mitigación |
|----|--------|-------------------|:-----:|:----:|:----:|---------------------|------------|
| PO-001 | El servicio funciona con SQLite en desarrollo pero PostgreSQL en producción, causando diferencias de comportamiento en queries | Adaptabilidad | 2 | 2 | 🟡 4 | Repositorio, migraciones | Ejecutar tests de integración también contra PostgreSQL (Docker). Evitar SQL raw en el repositorio. |
| PO-002 | El Dockerfile no usa multi-stage build ni usuario no-root, complicando despliegue en entornos con restricciones de seguridad | Facilidad de Instalación | 1 | 2 | 🟢 2 | `Dockerfile` | Evaluar multi-stage build. Agregar usuario no-root (`USER appuser`). |
| PO-003 | Las migraciones automáticas en el CMD del Dockerfile pueden fallar si la BD no está lista al arrancar | Facilidad de Instalación | 2 | 3 | 🟠 6 | `Dockerfile`, `docker-compose.yml` | Implementar `wait-for-it` o health check con `depends_on: condition: service_healthy`. |
| PO-004 | La configuración hardcodeada de puertos (8001) dificulta el despliegue en entornos con puertos dinámicos | Reemplazabilidad | 1 | 1 | 🟢 1 | `Dockerfile`, `docker-compose.yml` | Parametrizar con variable de entorno `PORT`. |
| PO-005 | No existe directiva HEALTHCHECK en el Dockerfile, impidiendo que Docker detecte contenedores degradados automáticamente | Facilidad de Instalación | 2 | 3 | 🟠 6 | `Dockerfile` | Agregar `HEALTHCHECK CMD curl -f http://localhost:8001/api/health/ || exit 1` al Dockerfile. Validar con `docker inspect`. |
| PO-006 | No existe entrypoint script para orquestar migraciones + inicio del servidor, requiriendo CMD compuesto propenso a errores | Adaptabilidad | 2 | 2 | 🟡 4 | `Dockerfile` | Crear `entrypoint.sh` que ejecute `migrate` y luego `gunicorn`. Pruebas de arranque en contenedor limpio. |

---

### 8.9 Resumen de Riesgos por Característica ISO/IEC 25010:2023

| Característica | Total Riesgos | 🔴 Críticos | 🟠 Altos | 🟡 Medios | 🟢 Bajos |
|---------------|:------------:|:-----------:|:--------:|:---------:|:--------:|
| **Adecuación Funcional** | 7 | 0 | 4 | 1 | 2 |
| **Eficiencia de Desempeño** | 4 | 0 | 0 | 2 | 2 |
| **Compatibilidad** | 3 | 0 | 1 | 1 | 1 |
| **Usabilidad** | 3 | 0 | 0 | 1 | 2 |
| **Fiabilidad** | 4 | 0 | 2 | 2 | 0 |
| **Seguridad** | 7 | 2 | 4 | 1 | 0 |
| **Mantenibilidad** | 4 | 0 | 0 | 3 | 1 |
| **Portabilidad** | 6 | 0 | 2 | 2 | 2 |
| **TOTAL** | **38** | **2** | **13** | **13** | **10** |

### Mapa de Calor — Riesgos por Severidad

```
Impacto →           Bajo (1)      Medio (2)      Alto (3)
                 ┌────────────┬────────────┬────────────┐
Prob. Alta (3)   │  🟡 3      │  🟠 6      │  🔴 9      │  SE-005, SE-007
                 ├────────────┼────────────┼────────────┤
Prob. Media (2)  │  🟢 2      │  🟡 4      │  🟠 6      │  AF-001..004, SE-002..006, PO-005
                 ├────────────┼────────────┼────────────┤
Prob. Baja (1)   │  🟢 1      │  🟢 2      │  🟡 3      │  SE-001, FI-001..002
                 └────────────┴────────────┴────────────┘
```

### Plan de Acción por Prioridad

#### 🔴 Riesgos Críticos (Severidad 9) — Acción Inmediata

| ID | Riesgo | Acción Requerida | Responsable | Deadline |
|----|--------|-----------------|-------------|----------|
| SE-005 | JWT_SECRET_KEY con valor por defecto | Verificar configuración por variable de entorno. Bloquear deploy sin config. | DevOps / Desarrollo | Sprint actual |
| SE-007 | Sin rate limiting en login | Implementar throttling (`django-ratelimit` o DRF throttle). | Desarrollo | Sprint actual |

#### 🟠 Riesgos Altos (Severidad 6) — Mitigación con pruebas automatizadas

| ID | Riesgo | Acción Requerida |
|----|--------|-----------------|
| AF-001 | Email inválido aceptado | Tests INT-REG-005 con variaciones de emails inválidos |
| AF-002 | Login con usuario inactivo | Test INT-LOG-005 automatizado |
| AF-003 | Evento no publicado en desactivación | Test con mock de EventPublisher |
| AF-004 | Email duplicado en cambio | Tests INT-UPD-002 |
| CO-002 | Formato de eventos no documentado | Schema de eventos + tests de contrato |
| FI-003 | Sin recuperación tras caída de BD | Test de health check y reinicio |
| FI-004 | JWT válido post-desactivación | Documentar limitación, evaluar blacklist |
| SE-002 | SHA-256 sin sal | Evaluar migración a bcrypt |
| SE-003 | IDOR en endpoints de usuario | Tests de acceso cruzado entre usuarios |
| SE-004 | DELETE sin auditoría | Implementar logging y tests |
| SE-006 | Cookies JWT sin Secure/SameSite | Verificar atributos en tests |
| PO-003 | Migraciones fallan sin BD lista | Implementar wait-for-it |
| PO-005 | Sin HEALTHCHECK en Dockerfile | Agregar directiva HEALTHCHECK al Dockerfile |
| PO-006 | Sin entrypoint script | Crear entrypoint.sh para orquestar arranque |

---

### 8.10 Riesgos de Proyecto

Los riesgos de proyecto están relacionados con la gestión y el control del proyecto. A diferencia de los riesgos de producto (secciones 8.1–8.8), estos riesgos afectan al **calendario**, el **presupuesto** o el **alcance** del proyecto, comprometiendo su capacidad para alcanzar los objetivos establecidos.

Se clasifican en cuatro categorías:

---

#### 8.10.1 Problemas de Organización

> *Riesgos derivados de la planificación, estimación, entrega y gestión de recursos del proyecto.*

| ID | Riesgo | Categoría | Prob. | Imp. | Sev. | Impacto en el Proyecto | Mitigación |
|----|--------|-----------|:-----:|:----:|:----:|------------------------|------------|
| RP-ORG-001 | Retraso en la entrega de los productos de trabajo (API endpoints, imagen Docker, tests) por dependencias no identificadas entre tareas | Entregas | 2 | 3 | 🟠 6 | Desplazamiento del cronograma del sprint de pruebas y del release del microservicio | Definir WBS (Work Breakdown Structure) con dependencias claras. Seguimiento diario en daily stand-up. Buffer de 20% en estimaciones. |
| RP-ORG-002 | Estimaciones inexactas del esfuerzo requerido para implementar la integración con RabbitMQ y la contenerización Docker | Estimaciones | 2 | 2 | 🟡 4 | Sobrecarga de trabajo en el sprint, posible recorte de alcance en pruebas no funcionales | Usar estimación por puntos de historia con Planning Poker. Comparar con velocidad de sprints anteriores. Revisar estimaciones al 50% del sprint. |
| RP-ORG-003 | Reducción de presupuesto que limite el acceso a entornos de prueba (instancia PostgreSQL, servidor RabbitMQ, infraestructura Docker) | Costes | 1 | 3 | 🟡 3 | Imposibilidad de ejecutar pruebas de integración en entorno productivo-like, reducción de la cobertura de pruebas | Usar servicios contenerizados locales (Docker Compose). Priorizar SQLite para pruebas unitarias. Evaluar servicios cloud con tier gratuito. |
| RP-ORG-004 | Falta de entrega oportuna de los requisitos actualizados de las historias de usuario US-008 a US-012 (contenerización) | Entregas | 2 | 2 | 🟡 4 | Bloqueo de la implementación de pruebas de contenerización, retrabajo en criterios de aceptación | Establecer deadline para la definición de requisitos antes del inicio del sprint. Acordar criterios de aceptación en sesión de refinamiento. |
| RP-ORG-005 | Ausencia de un entorno de staging dedicado para pruebas de integración pre-producción | Infraestructura | 2 | 3 | 🟠 6 | Defectos no detectados hasta producción, mayor costo de corrección post-release | Implementar entorno de staging con Docker Compose que replique la arquitectura de producción. Automatizar despliegue con CI/CD. |

---

#### 8.10.2 Problemas de Personal

> *Riesgos asociados a las competencias, disponibilidad y dinámica del equipo de desarrollo y pruebas.*

| ID | Riesgo | Categoría | Prob. | Imp. | Sev. | Impacto en el Proyecto | Mitigación |
|----|--------|-----------|:-----:|:----:|:----:|------------------------|------------|
| RP-PER-001 | Competencias insuficientes del equipo en Domain-Driven Design (DDD) y Event-Driven Architecture (EDA), afectando la calidad de pruebas de dominio | Competencias | 2 | 3 | 🟠 6 | Tests de dominio superficiales que no validan correctamente las invariantes de negocio ni los eventos publicados | Sesiones de capacitación en DDD/EDA. Pair programming para revisión de tests. Documentar patrones DDD del proyecto en ARCHITECTURE_DDD.md. |
| RP-PER-002 | Escasez de personal con experiencia en contenerización Docker y orquestación para validar US-008 a US-012 | Escasez | 2 | 2 | 🟡 4 | Pruebas de contenerización superficiales, configuraciones de Docker no validadas adecuadamente | Asignar un miembro con experiencia Docker como referente. Crear guía de pruebas Docker. Documentar procedimientos en TEST_ENDPOINTS.md. |
| RP-PER-003 | Conflictos entre los roles de desarrollo y QA cuando el mismo equipo implementa y prueba el código | Conflictos | 2 | 2 | 🟡 4 | Sesgo de confirmación en las pruebas, menor efectividad en la detección de defectos | Implementar revisión cruzada de tests. Asegurar que quien escribe el test no sea quien implementó la funcionalidad. Code review obligatorio. |
| RP-PER-004 | Problemas de comunicación entre el equipo de backend (Users Service) y los equipos consumidores de la API y de los eventos RabbitMQ | Comunicación | 2 | 3 | 🟠 6 | Contratos de API y esquemas de eventos desalineados, integración fallida con otros microservicios | Documentar contratos de API (OpenAPI) y esquemas de eventos (AsyncAPI). Reuniones de sincronización semanales con equipos consumidores. |
| RP-PER-005 | Baja de un miembro clave del equipo durante el sprint de pruebas por enfermedad o rotación | Escasez | 1 | 3 | 🟡 3 | Retraso en la ejecución de pruebas, pérdida de conocimiento técnico del proyecto | Documentar todo el conocimiento en el repositorio (README, ARCHITECTURE.md). Pair programming para transferencia de conocimiento. Al menos 2 personas deben conocer cada componente. |

---

#### 8.10.3 Problemas Técnicos

> *Riesgos relacionados con la complejidad técnica, el alcance del proyecto y las herramientas utilizadas.*

| ID | Riesgo | Categoría | Prob. | Imp. | Sev. | Impacto en el Proyecto | Mitigación |
|----|--------|-----------|:-----:|:----:|:----:|------------------------|------------|
| RP-TEC-001 | Corrupción del alcance (scope creep): adición de nuevos endpoints o funcionalidades no planificadas durante el sprint (ej. CRUD de roles, gestión de permisos) | Alcance | 3 | 3 | 🔴 9 | Desviación del cronograma, pruebas incompletas para funcionalidades nuevas y existentes, calidad reducida | **ACCIÓN INMEDIATA**: Definir y congelar el alcance antes del inicio del sprint. Todo cambio de alcance debe pasar por el proceso de gestión de cambios con evaluación de impacto. |
| RP-TEC-002 | Soporte deficiente de las herramientas de testing (pytest-django) para escenarios de prueba con cookies HttpOnly y autenticación por JWT en cookies | Herramientas | 2 | 2 | 🟡 4 | Pruebas de autenticación incompletas o con workarounds frágiles que no validan el comportamiento real | Desarrollar utilidades auxiliares de testing (`cookie_utils.py` de test). Documentar patrones de prueba con cookies en el proyecto. Evaluar `requests` como alternativa para tests E2E. |
| RP-TEC-003 | Incompatibilidad entre las versiones de dependencias (Django 5.x, DRF, PyJWT) que generen fallos intermitentes en testing | Herramientas | 1 | 2 | 🟢 2 | Falsos positivos/negativos en tests, tiempo perdido en troubleshooting de herramientas | Fijar versiones exactas en `requirements.txt`. Ejecutar `pip check` en CI. Usar entorno virtual dedicado para tests. |
| RP-TEC-004 | La arquitectura DDD introduce complejidad que dificulta la escritura de tests de integración por la cantidad de capas (dominio, aplicación, infraestructura, presentación) | Alcance | 2 | 2 | 🟡 4 | Pruebas que validan interacciones entre capas de forma incorrecta o incompleta, mayor tiempo de desarrollo de tests | Definir estrategia de testing por capa. Tests de dominio sin infraestructura, tests de uso de caso con mocks, tests de integración end-to-end. Seguir estructura existente en `users/tests/`. |
| RP-TEC-005 | Entorno Docker inconsistente entre máquinas de desarrollo (Windows, macOS, Linux), causando que tests pasen localmente pero fallen en CI/CD | Herramientas | 2 | 2 | 🟡 4 | Falsos positivos locales, pipeline CI/CD inestable, pérdida de confianza en los tests | Estandarizar entorno con Docker Compose para desarrollo. Documentar requisitos mínimos de Docker. Ejecutar tests siempre dentro del contenedor antes del merge. |

---

#### 8.10.4 Problemas con Proveedores

> *Riesgos asociados a dependencias de terceros, servicios externos y componentes proporcionados por proveedores.*

| ID | Riesgo | Categoría | Prob. | Imp. | Sev. | Impacto en el Proyecto | Mitigación |
|----|--------|-----------|:-----:|:----:|:----:|------------------------|------------|
| RP-PRO-001 | Fallo en la entrega por parte del equipo que mantiene el servicio de RabbitMQ compartido, impidiendo pruebas de integración de eventos | Entrega de terceros | 2 | 2 | 🟡 4 | Pruebas de eventos de dominio (US-007) bloqueadas, imposibilidad de validar flujo EDA completo | Mantener instancia local de RabbitMQ en Docker Compose. Usar mocks del `EventPublisher` como fallback para tests. No depender de infraestructura compartida para testing. |
| RP-PRO-002 | Indisponibilidad o cambios no comunicados en el servicio de PostgreSQL gestionado (ej. cloud provider), afectando pruebas de integración con BD relacional | Entrega de terceros | 1 | 3 | 🟡 3 | Pruebas de integración con BD real bloqueadas, retraso en validación de migraciones | Usar PostgreSQL local en Docker para pruebas. SQLite como fallback para tests de integración Django. Mantener scripts de migración versionados. |
| RP-PRO-003 | Quiebra o discontinuidad del proveedor de hosting/cloud donde se despliega el microservicio | Continuidad | 1 | 3 | 🟡 3 | Pérdida del entorno de despliegue, necesidad de migración de emergencia a otro proveedor | Diseño cloud-agnostic con Docker. No usar servicios propietarios del proveedor. Mantener IaC (Infrastructure as Code) para reproducir entorno en cualquier proveedor. |
| RP-PRO-004 | Cambios en la licencia o disponibilidad de librerías open source críticas (Django, DRF, PyJWT, pika) | Continuidad | 1 | 2 | 🟢 2 | Necesidad de migrar a librerías alternativas, retrabajo significativo en código y tests | Monitorear licenses de dependencias. Evaluar alternativas periódicamente. Fijar versiones en `requirements.txt` para aislar cambios inesperados. |
| RP-PRO-005 | El equipo que consume los eventos del Users Service no entrega los contratos de integración a tiempo, impidiendo tests de contrato | Entrega de terceros | 2 | 2 | 🟡 4 | Tests de interoperabilidad incompletos, riesgo de incompatibilidad en producción con servicios consumidores | Definir contratos de eventos proactivamente desde el productor (Users Service). Publicar esquemas en repositorio compartido. Implementar tests de contrato del lado del productor. |

---

#### 8.10.5 Resumen de Riesgos de Proyecto

| Categoría | Total Riesgos | 🔴 Críticos | 🟠 Altos | 🟡 Medios | 🟢 Bajos |
|-----------|:------------:|:-----------:|:--------:|:---------:|:--------:|
| **Problemas de Organización** | 5 | 0 | 2 | 3 | 0 |
| **Problemas de Personal** | 5 | 0 | 2 | 3 | 0 |
| **Problemas Técnicos** | 5 | 1 | 0 | 3 | 1 |
| **Problemas con Proveedores** | 5 | 0 | 0 | 4 | 1 |
| **TOTAL** | **20** | **1** | **4** | **13** | **2** |

#### Impacto de los Riesgos de Proyecto en los Objetivos

| Objetivo del Proyecto | Riesgos que lo Afectan | Nivel de Exposición |
|----------------------|------------------------|:-------------------:|
| **Calendario** — Entrega del microservicio en el sprint planificado | RP-ORG-001, RP-ORG-002, RP-ORG-004, RP-PER-002, RP-PER-005, RP-TEC-001 | 🟠 Alto |
| **Presupuesto** — Ejecución dentro del presupuesto asignado | RP-ORG-003, RP-PRO-003 | 🟡 Medio |
| **Alcance** — Cobertura completa de las 12 historias de usuario | RP-TEC-001, RP-TEC-004, RP-PER-001, RP-PER-003 | 🟠 Alto |
| **Calidad** — Cumplimiento de estándares ISO/IEC 25010:2023 | RP-PER-001, RP-PER-004, RP-TEC-002, RP-PRO-001, RP-PRO-005 | 🟠 Alto |

#### Plan de Acción — Riesgos de Proyecto Prioritarios

| Prioridad | ID | Riesgo | Acción Requerida | Responsable | Deadline |
|:---------:|----|--------|-----------------|-------------|----------|
| 🔴 1 | RP-TEC-001 | Corrupción del alcance (scope creep) | Congelar alcance. Proceso formal de gestión de cambios. | Scrum Master / PO | Inicio del sprint |
| 🟠 2 | RP-ORG-001 | Retrasos en entregas | WBS con dependencias, seguimiento diario, buffer 20% | Project Manager | Planificación |
| 🟠 3 | RP-ORG-005 | Sin entorno de staging | Implementar staging con Docker Compose | DevOps | Sprint 1 |
| 🟠 4 | RP-PER-001 | Falta de competencias DDD/EDA | Capacitación, pair programming, docs | Tech Lead | Semana 1 |
| 🟠 5 | RP-PER-004 | Comunicación entre equipos | Contratos API/eventos, sync semanales | Tech Lead | Continuo |

---

## 9. Herramientas

| Herramienta | Propósito | Versión |
|-------------|-----------|---------|
| **pytest** | Framework de pruebas unitarias y de integración | ≥ 7.0 |
| **pytest-django** | Plugin de pytest para integración con Django | ≥ 4.5 |
| **Django REST Framework APIClient** | Cliente HTTP para pruebas de integración de API | ≥ 3.14 |
| **unittest.mock** | Mocking de dependencias (repositorio, event publisher) | Stdlib Python |
| **Faker** | Generación de datos de prueba aleatorios | — |
| **Docker / Docker Compose** | Entorno de pruebas contenerizado (PostgreSQL, RabbitMQ) | — |
| **PostgreSQL 15** | Base de datos para pruebas de integración en entorno Docker | 15.x |
| **SQLite** | Base de datos para pruebas de integración locales (Django test) | Stdlib Python |
| **RabbitMQ** | Message broker para pruebas de eventos de dominio | 3.x |
| **Git** | Control de versiones y trazabilidad de cambios | — |
| **GitHub** | Repositorio de código y Bug Tracker (Issues) | — |
| **Postman / curl** | Pruebas manuales exploratorias de endpoints | — |

---

## 10. Calendario de Pruebas (Cronograma)

Se acordó con el equipo la ejecución de pruebas en sprints de 2 semanas, con entregas incrementales cada 2 días.

### Sprint de Pruebas

| Día | Actividad | Tipo | HU Cubiertas |
|:---:|-----------|------|:------------:|
| **1** | Configuración del entorno de pruebas. Smoke test (`/api/health/`). Preparación de datos de prueba. | Setup | US-006 |
| **2** | Pruebas unitarias de dominio (entidades, factories, excepciones). | Unitarias | Transversal |
| **3** | Pruebas de casos de uso con mocks (RegisterUser, Login). | Componente | US-001, US-002 |
| **4** | Pruebas de integración: Registro (`POST /api/auth/`). | Integración | US-001 |
| **5** | Pruebas de integración: Login (`POST /api/auth/login/`). | Integración | US-002 |
| **6** | Pruebas de integración: Perfil (`GET /api/auth/me/`), Logout (`POST /api/auth/logout/`), Refresh. | Integración | US-003, US-004 |
| **7** | Pruebas de integración: Consulta por rol, CRUD de usuarios. | Integración | US-005 |
| **8** | Pruebas de integración: Actualizar email, Desactivar, Eliminar usuario. | Integración | Transversal |
| **9** | Pruebas de eventos de dominio con mocks de RabbitMQ. | Componente | US-007 |
| **10** | Pruebas de contenerización: Build de imagen Docker, configuración por variables de entorno. | Contenerización | US-008, US-009 |
| **11** | Pruebas de contenerización: Health check Docker, migraciones automáticas, ejecución de tests en contenedor. | Contenerización | US-010, US-011, US-012 |
| **12** | Ciclo 2: Validación de correcciones de defectos reportados. | Correcciones | Todos |
| **13** | Ciclo de regresión automatizada completa. | Regresión | Todos |
| **14** | Reporte final de pruebas. Documentación de riesgos residuales. | Cierre | — |

### Hitos

| Hito | Fecha Relativa | Entregable |
|------|:-------------:|------------|
| Inicio de pruebas | Día 1 | Entorno configurado, smoke test OK |
| Fin de pruebas unitarias/componente | Día 3 | Reporte parcial con cobertura de dominio |
| Fin de Ciclo 1 (integración) | Día 9 | Reporte de defectos en Bug Tracker |
| Fin de pruebas de contenerización | Día 11 | Validación de Docker, env vars, health check, migraciones |
| Fin de Ciclo 2 (correcciones) | Día 12 | Defectos resueltos y validados |
| Fin de regresión | Día 13 | Suite verde al 100% |
| Cierre del plan de pruebas | Día 14 | Reporte final, riesgos residuales documentados |

---

## 11. Prerequisitos

- ✅ Acceso al repositorio de código en GitHub.
- ✅ Acceso a la plataforma Bug Tracker (GitHub Issues).
- ✅ Entorno de desarrollo local configurado con Python 3.12, Django 6.x, DRF.
- ✅ Docker y Docker Compose instalados para levantar PostgreSQL y RabbitMQ.
- ✅ Base de datos de test accesible (SQLite local o PostgreSQL en Docker).
- ✅ Endpoint de RabbitMQ disponible para pruebas de eventos (o mock configurado).
- ✅ Documentación actualizada del proyecto: `ARCHITECTURE_DDD.md`, `HistoriasUsuarios_API_Contenerizacion.md`, `TEST_ENDPOINTS.md`.
- ✅ Migración `0003_seed_admin` ejecutada (usuario admin seed disponible).
- ✅ Comunicación constante con el equipo de trabajo.

---

## 12. Acuerdos

- Cada defecto reportado se ingresará en el Bug Tracker (GitHub Issues) con etiqueta de severidad, y se notificará al equipo de desarrollo y al Product Owner.
- Los defectos críticos (🔴 Severidad 9) bloquean la release y deben resolverse antes de continuar con el siguiente ciclo.
- Los defectos altos (🟠 Severidad 6) deben resolverse dentro del sprint actual.
- Las pruebas automatizadas deben alcanzar una cobertura mínima del 80% en la capa de dominio y del 70% en la capa de integración.
- La suite de pruebas debe ejecutarse en CI/CD antes de cada merge a la rama principal.
- Los riesgos residuales se documentarán y comunicarán al Product Owner para decisión de aceptación.

---

## Otros Tipos de Pruebas Recomendadas

Se recomienda al equipo considerar las siguientes pruebas en futuras iteraciones:

- ▪ **Pruebas de Seguridad** — Penetration testing, OWASP API Security Top 10.
- ▪ **Pruebas de Carga** — Rendimiento bajo alta concurrencia con herramientas como `locust` o `k6`.
- ▪ **Pruebas de Contrato** — Validar esquema de eventos RabbitMQ con consumidores.
- ▪ **Pruebas de Regresión Visual** — Para el admin panel de Django (si aplica).
- ▪ **Pruebas de Migración** — Verificar migraciones de BD son reversibles.
- ▪ **Pruebas de Orquestación** — Validar despliegue multi-contenedor con Docker Compose y Kubernetes.

---

---

## 14. Diseño de Casos de Pruebas

Los siguientes casos de prueba están redactados en lenguaje **Gherkin** (Given/When/Then) y aplican técnicas de diseño de pruebas para maximizar la cobertura:

- **PE** — Partición de Equivalencia
- **VL** — Valores Límite
- **TD** — Tabla de Decisión

---

### 14.1 US-001 — Registro de Usuario (`POST /api/auth/`)

#### 14.1.1 Partición de Equivalencia — Campo `email`

| Clase | Tipo | Representante | Resultado esperado |
|-------|------|---------------|--------------------|
| CE-01 | Válida | `user@example.com` | Registro exitoso (201) |
| CE-02 | Inválida — sin `@` | `userexample.com` | Error (400) |
| CE-03 | Inválida — sin dominio | `user@` | Error (400) |
| CE-04 | Inválida — sin TLD | `user@example` | Error (400) |
| CE-05 | Inválida — vacío | `""` | Error (400) |
| CE-06 | Inválida — duplicado | email ya registrado | Error (400) |

```gherkin
Feature: Registro de usuario — Validación de email (Partición de Equivalencia)

  Scenario: CP-REG-001 — Registro exitoso con email válido (CE-01)
    Given no existe un usuario con email "newuser@example.com" en el sistema
    When envío una solicitud POST a "/api/auth/" con los datos:
      | email               | username  | password     |
      | newuser@example.com | newuser   | password123  |
    Then la respuesta tiene código de estado 201
    And la respuesta contiene un objeto "user" con el campo "email" igual a "newuser@example.com"
    And la respuesta establece cookies HttpOnly "access_token" y "refresh_token"

  Scenario: CP-REG-002 — Rechazo por email sin arroba (CE-02)
    Given no existe un usuario en el sistema
    When envío una solicitud POST a "/api/auth/" con los datos:
      | email             | username  | password     |
      | userexample.com   | testuser  | password123  |
    Then la respuesta tiene código de estado 400
    And la respuesta contiene un mensaje de error sobre el campo "email"

  Scenario: CP-REG-003 — Rechazo por email sin dominio (CE-03)
    Given no existe un usuario en el sistema
    When envío una solicitud POST a "/api/auth/" con los datos:
      | email   | username  | password     |
      | user@   | testuser  | password123  |
    Then la respuesta tiene código de estado 400
    And la respuesta contiene un mensaje de error sobre el campo "email"

  Scenario: CP-REG-004 — Rechazo por email sin TLD (CE-04)
    Given no existe un usuario en el sistema
    When envío una solicitud POST a "/api/auth/" con los datos:
      | email          | username  | password     |
      | user@example   | testuser  | password123  |
    Then la respuesta tiene código de estado 400
    And la respuesta contiene un mensaje de error sobre el campo "email"

  Scenario: CP-REG-005 — Rechazo por email vacío (CE-05)
    Given no existe un usuario en el sistema
    When envío una solicitud POST a "/api/auth/" con los datos:
      | email | username  | password     |
      |       | testuser  | password123  |
    Then la respuesta tiene código de estado 400
    And la respuesta contiene un mensaje de error sobre el campo "email"

  Scenario: CP-REG-006 — Rechazo por email duplicado (CE-06)
    Given existe un usuario registrado con email "existing@example.com"
    When envío una solicitud POST a "/api/auth/" con los datos:
      | email                | username   | password     |
      | existing@example.com | otheruser  | password123  |
    Then la respuesta tiene código de estado 400
    And la respuesta contiene un mensaje de error indicando que el email ya existe
```

#### 14.1.2 Valores Límite — Campo `username` (mín. 3 caracteres, máx. 50 caracteres)

| Valor límite | Longitud | Resultado esperado |
|--------------|:--------:|--------------------|
| `"ab"` | 2 | Error (400) — por debajo del mínimo |
| `"abc"` | 3 | Registro exitoso (201) — mínimo válido |
| `"abcd"` | 4 | Registro exitoso (201) — encima del mínimo |
| `"a" * 49` | 49 | Registro exitoso (201) — debajo del máximo |
| `"a" * 50` | 50 | Registro exitoso (201) — máximo válido |
| `"a" * 51` | 51 | Error (400) — por encima del máximo |

```gherkin
Feature: Registro de usuario — Validación de username (Valores Límite)

  Scenario: CP-REG-007 — Rechazo con username de 2 caracteres (debajo del mínimo)
    Given no existe un usuario en el sistema
    When envío una solicitud POST a "/api/auth/" con los datos:
      | email              | username | password     |
      | test1@example.com  | ab       | password123  |
    Then la respuesta tiene código de estado 400
    And la respuesta contiene un mensaje de error sobre el campo "username"

  Scenario: CP-REG-008 — Registro exitoso con username de 3 caracteres (mínimo válido)
    Given no existe un usuario con email "test2@example.com" en el sistema
    When envío una solicitud POST a "/api/auth/" con los datos:
      | email              | username | password     |
      | test2@example.com  | abc      | password123  |
    Then la respuesta tiene código de estado 201
    And la respuesta contiene un objeto "user" con el campo "username" igual a "abc"

  Scenario: CP-REG-009 — Registro exitoso con username de 4 caracteres (encima del mínimo)
    Given no existe un usuario con email "test3@example.com" en el sistema
    When envío una solicitud POST a "/api/auth/" con los datos:
      | email              | username | password     |
      | test3@example.com  | abcd     | password123  |
    Then la respuesta tiene código de estado 201
    And la respuesta contiene un objeto "user" con el campo "username" igual a "abcd"

  Scenario: CP-REG-010 — Registro exitoso con username de 49 caracteres (debajo del máximo)
    Given no existe un usuario con email "test4@example.com" en el sistema
    When envío una solicitud POST a "/api/auth/" con un username de 49 caracteres
    Then la respuesta tiene código de estado 201

  Scenario: CP-REG-011 — Registro exitoso con username de 50 caracteres (máximo válido)
    Given no existe un usuario con email "test5@example.com" en el sistema
    When envío una solicitud POST a "/api/auth/" con un username de 50 caracteres
    Then la respuesta tiene código de estado 201

  Scenario: CP-REG-012 — Rechazo con username de 51 caracteres (por encima del máximo)
    Given no existe un usuario en el sistema
    When envío una solicitud POST a "/api/auth/" con un username de 51 caracteres
    Then la respuesta tiene código de estado 400
    And la respuesta contiene un mensaje de error sobre el campo "username"
```

#### 14.1.3 Valores Límite — Campo `password` (mín. 8 caracteres)

| Valor límite | Longitud | Resultado esperado |
|--------------|:--------:|--------------------|
| `"1234567"` | 7 | Error (400) — por debajo del mínimo |
| `"12345678"` | 8 | Registro exitoso (201) — mínimo válido |
| `"123456789"` | 9 | Registro exitoso (201) — encima del mínimo |

```gherkin
Feature: Registro de usuario — Validación de password (Valores Límite)

  Scenario: CP-REG-013 — Rechazo con password de 7 caracteres (debajo del mínimo)
    Given no existe un usuario en el sistema
    When envío una solicitud POST a "/api/auth/" con los datos:
      | email              | username  | password |
      | test6@example.com  | testuser6 | 1234567  |
    Then la respuesta tiene código de estado 400
    And la respuesta contiene un mensaje de error sobre el campo "password"

  Scenario: CP-REG-014 — Registro exitoso con password de 8 caracteres (mínimo válido)
    Given no existe un usuario con email "test7@example.com" en el sistema
    When envío una solicitud POST a "/api/auth/" con los datos:
      | email              | username  | password |
      | test7@example.com  | testuser7 | 12345678 |
    Then la respuesta tiene código de estado 201

  Scenario: CP-REG-015 — Registro exitoso con password de 9 caracteres (encima del mínimo)
    Given no existe un usuario con email "test8@example.com" en el sistema
    When envío una solicitud POST a "/api/auth/" con los datos:
      | email              | username  | password  |
      | test8@example.com  | testuser8 | 123456789 |
    Then la respuesta tiene código de estado 201
```

#### 14.1.4 Tabla de Decisión — Registro de usuario

| # | email válido | email único | username ≥ 3 chars | password ≥ 8 chars | Resultado | HTTP |
|:-:|:------------:|:-----------:|:------------------:|:------------------:|-----------|:----:|
| 1 | ✅ | ✅ | ✅ | ✅ | Registro exitoso, cookies JWT establecidas, rol = USER | 201 |
| 2 | ❌ | — | ✅ | ✅ | Error: email inválido | 400 |
| 3 | ✅ | ❌ | ✅ | ✅ | Error: email ya existe | 400 |
| 4 | ✅ | ✅ | ❌ | ✅ | Error: username muy corto | 400 |
| 5 | ✅ | ✅ | ✅ | ❌ | Error: password muy corto | 400 |
| 6 | ❌ | — | ❌ | ❌ | Error: múltiples campos inválidos | 400 |
| 7 | ✅ | ✅ | ✅ | ✅ | Rol siempre es USER (campo role ignorado) | 201 |

```gherkin
Feature: Registro de usuario — Tabla de Decisión

  Scenario: CP-REG-016 — Regla 1: Todos los campos válidos y únicos
    Given no existe un usuario con email "valid@example.com" en el sistema
    When envío una solicitud POST a "/api/auth/" con los datos:
      | email             | username   | password     |
      | valid@example.com | validuser  | password123  |
    Then la respuesta tiene código de estado 201
    And la respuesta contiene un objeto "user" con el campo "role" igual a "USER"
    And la respuesta establece cookies HttpOnly "access_token" y "refresh_token"

  Scenario: CP-REG-017 — Regla 2: Email con formato inválido
    Given no existe un usuario en el sistema
    When envío una solicitud POST a "/api/auth/" con los datos:
      | email          | username   | password     |
      | not-an-email   | validuser  | password123  |
    Then la respuesta tiene código de estado 400

  Scenario: CP-REG-018 — Regla 3: Email duplicado con datos válidos
    Given existe un usuario registrado con email "dup@example.com"
    When envío una solicitud POST a "/api/auth/" con los datos:
      | email           | username  | password     |
      | dup@example.com | newuser2  | password123  |
    Then la respuesta tiene código de estado 400
    And la respuesta contiene un mensaje de error indicando que el email ya existe

  Scenario: CP-REG-019 — Regla 4: Username muy corto con demás campos válidos
    Given no existe un usuario en el sistema
    When envío una solicitud POST a "/api/auth/" con los datos:
      | email              | username | password     |
      | test9@example.com  | ab       | password123  |
    Then la respuesta tiene código de estado 400

  Scenario: CP-REG-020 — Regla 5: Password muy corto con demás campos válidos
    Given no existe un usuario en el sistema
    When envío una solicitud POST a "/api/auth/" con los datos:
      | email               | username   | password |
      | test10@example.com  | validuser  | short    |
    Then la respuesta tiene código de estado 400

  Scenario: CP-REG-021 — Regla 6: Múltiples campos inválidos simultáneamente
    Given no existe un usuario en el sistema
    When envío una solicitud POST a "/api/auth/" con los datos:
      | email      | username | password |
      | bad-email  | ab       | short    |
    Then la respuesta tiene código de estado 400

  Scenario: CP-REG-022 — Regla 7: Campo role enviado es ignorado, siempre asigna USER
    Given no existe un usuario con email "admin@try.com" en el sistema
    When envío una solicitud POST a "/api/auth/" con los datos:
      | email          | username  | password     | role  |
      | admin@try.com  | trynadmin | password123  | ADMIN |
    Then la respuesta tiene código de estado 201
    And la respuesta contiene un objeto "user" con el campo "role" igual a "USER"
```

---

### 14.2 US-002 — Autenticación de Usuario (`POST /api/auth/login/`)

#### 14.2.1 Partición de Equivalencia — Credenciales

| Clase | Tipo | Representante | Resultado esperado |
|-------|------|---------------|--------------------|
| CE-07 | Válida | email y password correctos, usuario activo | Login exitoso (200) |
| CE-08 | Inválida — password incorrecto | email correcto, password incorrecto | Error (401) |
| CE-09 | Inválida — email inexistente | email no registrado | Error (401) |
| CE-10 | Inválida — usuario inactivo | credenciales correctas, `is_active = false` | Error (401) |
| CE-11 | Inválida — campos vacíos | email y/o password vacíos | Error (400) |

```gherkin
Feature: Login de usuario — Validación de credenciales (Partición de Equivalencia)

  Scenario: CP-LOG-001 — Login exitoso con credenciales válidas (CE-07)
    Given existe un usuario activo con email "user@test.com" y password "password123"
    When envío una solicitud POST a "/api/auth/login/" con los datos:
      | email          | password     |
      | user@test.com  | password123  |
    Then la respuesta tiene código de estado 200
    And la respuesta contiene un objeto "user" con los campos "id", "email", "username", "role"
    And la respuesta establece cookies HttpOnly "access_token" y "refresh_token"

  Scenario: CP-LOG-002 — Rechazo por password incorrecto (CE-08)
    Given existe un usuario activo con email "user@test.com" y password "password123"
    When envío una solicitud POST a "/api/auth/login/" con los datos:
      | email          | password      |
      | user@test.com  | wrongpass123  |
    Then la respuesta tiene código de estado 401
    And la respuesta contiene un mensaje de error de credenciales inválidas

  Scenario: CP-LOG-003 — Rechazo por email inexistente (CE-09)
    Given no existe un usuario con email "noone@test.com" en el sistema
    When envío una solicitud POST a "/api/auth/login/" con los datos:
      | email           | password     |
      | noone@test.com  | password123  |
    Then la respuesta tiene código de estado 401
    And la respuesta contiene un mensaje de error de credenciales inválidas

  Scenario: CP-LOG-004 — Rechazo por usuario inactivo (CE-10)
    Given existe un usuario inactivo con email "inactive@test.com" y password "password123"
    When envío una solicitud POST a "/api/auth/login/" con los datos:
      | email              | password     |
      | inactive@test.com  | password123  |
    Then la respuesta tiene código de estado 401
    And la respuesta contiene un mensaje de error de credenciales inválidas

  Scenario: CP-LOG-005 — Rechazo por campos vacíos (CE-11)
    Given el sistema está disponible
    When envío una solicitud POST a "/api/auth/login/" con los datos:
      | email | password |
      |       |          |
    Then la respuesta tiene código de estado 400
```

#### 14.2.2 Tabla de Decisión — Login

| # | email existe | password correcto | usuario activo | Resultado | HTTP |
|:-:|:------------:|:-----------------:|:--------------:|-----------|:----:|
| 1 | ✅ | ✅ | ✅ | Login exitoso, cookies JWT establecidas | 200 |
| 2 | ✅ | ❌ | ✅ | Credenciales inválidas | 401 |
| 3 | ❌ | — | — | Credenciales inválidas | 401 |
| 4 | ✅ | ✅ | ❌ | Usuario inactivo | 401 |
| 5 | ✅ | ❌ | ❌ | Credenciales inválidas | 401 |

```gherkin
Feature: Login de usuario — Tabla de Decisión

  Scenario: CP-LOG-006 — Regla 1: Email existe, password correcto, usuario activo
    Given existe un usuario activo con email "active@test.com" y password "password123"
    When envío una solicitud POST a "/api/auth/login/" con los datos:
      | email            | password     |
      | active@test.com  | password123  |
    Then la respuesta tiene código de estado 200
    And la respuesta establece cookies HttpOnly "access_token" y "refresh_token"
    And la respuesta contiene un objeto "user" con los campos "id", "email", "username", "role"

  Scenario: CP-LOG-007 — Regla 2: Email existe, password incorrecto, usuario activo
    Given existe un usuario activo con email "active@test.com" y password "password123"
    When envío una solicitud POST a "/api/auth/login/" con los datos:
      | email            | password   |
      | active@test.com  | wrongpass  |
    Then la respuesta tiene código de estado 401

  Scenario: CP-LOG-008 — Regla 3: Email no existe
    Given no existe un usuario con email "ghost@test.com" en el sistema
    When envío una solicitud POST a "/api/auth/login/" con los datos:
      | email           | password     |
      | ghost@test.com  | password123  |
    Then la respuesta tiene código de estado 401

  Scenario: CP-LOG-009 — Regla 4: Email existe, password correcto, usuario inactivo
    Given existe un usuario inactivo con email "off@test.com" y password "password123"
    When envío una solicitud POST a "/api/auth/login/" con los datos:
      | email         | password     |
      | off@test.com  | password123  |
    Then la respuesta tiene código de estado 401

  Scenario: CP-LOG-010 — Regla 5: Email existe, password incorrecto, usuario inactivo
    Given existe un usuario inactivo con email "off@test.com" y password "password123"
    When envío una solicitud POST a "/api/auth/login/" con los datos:
      | email         | password  |
      | off@test.com  | wrong123  |
    Then la respuesta tiene código de estado 401
```

---

### 14.3 US-003 — Perfil del Usuario Autenticado (`GET /api/auth/me/`)

#### 14.3.1 Partición de Equivalencia — Autenticación

| Clase | Tipo | Representante | Resultado esperado |
|-------|------|---------------|--------------------|
| CE-12 | Válida | JWT válido en cookie | Perfil retornado (200) |
| CE-13 | Inválida — sin cookie | Sin cookie `access_token` | Error (401) |
| CE-14 | Inválida — JWT expirado | Token expirado en cookie | Error (401) |
| CE-15 | Inválida — JWT manipulado | Token alterado manualmente | Error (401) |

```gherkin
Feature: Perfil del usuario autenticado — Autenticación (Partición de Equivalencia)

  Scenario: CP-ME-001 — Obtención exitosa del perfil con JWT válido (CE-12)
    Given existe un usuario activo con email "me@test.com" y password "password123"
    And el usuario ha iniciado sesión y tiene una cookie "access_token" válida
    When envío una solicitud GET a "/api/auth/me/" con la cookie "access_token"
    Then la respuesta tiene código de estado 200
    And la respuesta contiene los campos "id", "email", "username", "role", "is_active"
    And el campo "email" es igual a "me@test.com"

  Scenario: CP-ME-002 — Rechazo sin cookie de autenticación (CE-13)
    Given el sistema está disponible
    When envío una solicitud GET a "/api/auth/me/" sin cookies de autenticación
    Then la respuesta tiene código de estado 401

  Scenario: CP-ME-003 — Rechazo con token JWT expirado (CE-14)
    Given existe un usuario activo con email "expired@test.com"
    And el usuario tiene una cookie "access_token" expirada
    When envío una solicitud GET a "/api/auth/me/" con la cookie "access_token" expirada
    Then la respuesta tiene código de estado 401

  Scenario: CP-ME-004 — Rechazo con token JWT manipulado (CE-15)
    Given el sistema está disponible
    When envío una solicitud GET a "/api/auth/me/" con una cookie "access_token" de valor "token.manipulado.invalido"
    Then la respuesta tiene código de estado 401
```

---

### 14.4 US-004 — Logout (`POST /api/auth/logout/`)

#### 14.4.1 Partición de Equivalencia — Sesión

| Clase | Tipo | Representante | Resultado esperado |
|-------|------|---------------|--------------------|
| CE-16 | Válida | Usuario autenticado | Logout exitoso, cookies limpiadas (200) |
| CE-17 | Válida — sin sesión | Sin autenticación | Logout permitido (200) |

```gherkin
Feature: Logout de usuario (Partición de Equivalencia)

  Scenario: CP-LOGOUT-001 — Logout exitoso con sesión activa (CE-16)
    Given existe un usuario activo con email "logout@test.com" y password "password123"
    And el usuario ha iniciado sesión y tiene cookies de autenticación
    When envío una solicitud POST a "/api/auth/logout/" con las cookies de autenticación
    Then la respuesta tiene código de estado 200
    And las cookies "access_token" y "refresh_token" son eliminadas de la respuesta

  Scenario: CP-LOGOUT-002 — Logout sin autenticación es permitido (CE-17)
    Given el sistema está disponible
    When envío una solicitud POST a "/api/auth/logout/" sin cookies de autenticación
    Then la respuesta tiene código de estado 200
```

---

### 14.5 US-005 — Consulta por Rol (`GET /api/auth/by-role/{role}/`)

#### 14.5.1 Partición de Equivalencia — Parámetro `role`

| Clase | Tipo | Representante | Resultado esperado |
|-------|------|---------------|--------------------|
| CE-18 | Válida | `ADMIN` | Lista de usuarios admin (200) |
| CE-19 | Válida | `USER` | Lista de usuarios regulares (200) |
| CE-20 | Inválida | `SUPERADMIN` | Error: rol inválido (400) |
| CE-21 | Inválida | `""` (vacío) | Error (400/404) |
| CE-22 | Inválida — sin auth | Cualquier rol, sin JWT | Error (401) |

```gherkin
Feature: Consulta de usuarios por rol (Partición de Equivalencia)

  Scenario: CP-ROLE-001 — Obtener usuarios con rol ADMIN (CE-18)
    Given existe al menos un usuario con rol "ADMIN" en el sistema
    And el usuario solicitante está autenticado con una cookie JWT válida
    When envío una solicitud GET a "/api/auth/by-role/ADMIN/" con la cookie de autenticación
    Then la respuesta tiene código de estado 200
    And la respuesta contiene una lista de usuarios
    And todos los usuarios de la lista tienen el campo "role" igual a "ADMIN"

  Scenario: CP-ROLE-002 — Obtener usuarios con rol USER (CE-19)
    Given existe al menos un usuario con rol "USER" en el sistema
    And el usuario solicitante está autenticado con una cookie JWT válida
    When envío una solicitud GET a "/api/auth/by-role/USER/" con la cookie de autenticación
    Then la respuesta tiene código de estado 200
    And la respuesta contiene una lista de usuarios
    And todos los usuarios de la lista tienen el campo "role" igual a "USER"

  Scenario: CP-ROLE-003 — Rechazo por rol inválido (CE-20)
    Given el usuario solicitante está autenticado con una cookie JWT válida
    When envío una solicitud GET a "/api/auth/by-role/SUPERADMIN/" con la cookie de autenticación
    Then la respuesta tiene código de estado 400
    And la respuesta contiene un mensaje de error indicando que el rol es inválido

  Scenario: CP-ROLE-004 — Sin autenticación (CE-22)
    Given el sistema está disponible
    When envío una solicitud GET a "/api/auth/by-role/USER/" sin cookies de autenticación
    Then la respuesta tiene código de estado 401
```

#### 14.5.2 Tabla de Decisión — Consulta por rol

| # | autenticado | rol válido | existen usuarios con ese rol | Resultado | HTTP |
|:-:|:-----------:|:----------:|:----------------------------:|-----------|:----:|
| 1 | ✅ | ✅ | ✅ | Lista con usuarios del rol solicitado | 200 |
| 2 | ✅ | ✅ | ❌ | Lista vacía | 200 |
| 3 | ✅ | ❌ | — | Error: rol inválido | 400 |
| 4 | ❌ | ✅ | — | Error: no autenticado | 401 |
| 5 | ❌ | ❌ | — | Error: no autenticado | 401 |

```gherkin
Feature: Consulta de usuarios por rol — Tabla de Decisión

  Scenario: CP-ROLE-005 — Regla 1: Autenticado, rol válido, existen usuarios
    Given existe un usuario con rol "USER" en el sistema
    And el usuario solicitante está autenticado con una cookie JWT válida
    When envío una solicitud GET a "/api/auth/by-role/USER/" con la cookie de autenticación
    Then la respuesta tiene código de estado 200
    And la respuesta contiene al menos 1 usuario en la lista

  Scenario: CP-ROLE-006 — Regla 2: Autenticado, rol válido, sin usuarios con ese rol
    Given no existen usuarios con rol "ADMIN" además del seed admin (si aplica)
    And el usuario solicitante está autenticado con una cookie JWT válida
    When envío una solicitud GET a "/api/auth/by-role/ADMIN/" con la cookie de autenticación
    Then la respuesta tiene código de estado 200
    And la respuesta contiene una lista de usuarios (puede ser vacía o solo el seed admin)

  Scenario: CP-ROLE-007 — Regla 3: Autenticado, rol inválido
    Given el usuario solicitante está autenticado con una cookie JWT válida
    When envío una solicitud GET a "/api/auth/by-role/MANAGER/" con la cookie de autenticación
    Then la respuesta tiene código de estado 400

  Scenario: CP-ROLE-008 — Regla 4: No autenticado, rol válido
    Given el sistema está disponible
    When envío una solicitud GET a "/api/auth/by-role/USER/" sin cookies de autenticación
    Then la respuesta tiene código de estado 401
```

---

### 14.6 US-006 — Health Check (`GET /api/health/`)

#### 14.6.1 Partición de Equivalencia — Estado del servicio

| Clase | Tipo | Representante | Resultado esperado |
|-------|------|---------------|--------------------|
| CE-23 | Válida | Servicio y BD saludables | Status healthy, database connected (200) |
| CE-24 | Inválida | BD no disponible | Status unhealthy (503) |

```gherkin
Feature: Health check del servicio (Partición de Equivalencia)

  Scenario: CP-HC-001 — Servicio saludable con BD conectada (CE-23)
    Given el servicio está corriendo y la base de datos está conectada
    When envío una solicitud GET a "/api/health/"
    Then la respuesta tiene código de estado 200
    And la respuesta contiene el campo "service" igual a "users-service"
    And la respuesta contiene el campo "status" igual a "healthy"
    And la respuesta contiene el campo "database" igual a "connected"

  Scenario: CP-HC-002 — Servicio con BD desconectada (CE-24)
    Given el servicio está corriendo pero la base de datos no está disponible
    When envío una solicitud GET a "/api/health/"
    Then la respuesta tiene código de estado 503
    And la respuesta contiene el campo "status" igual a "unhealthy"
```

---

### 14.7 Renovación de Token (`POST /api/auth/refresh/`)

#### 14.7.1 Partición de Equivalencia — Cookie `refresh_token`

| Clase | Tipo | Representante | Resultado esperado |
|-------|------|---------------|--------------------|
| CE-25 | Válida | `refresh_token` válido en cookie | Token renovado (200) |
| CE-26 | Inválida — sin cookie | Sin cookie `refresh_token` | Error (401) |
| CE-27 | Inválida — token expirado | `refresh_token` expirado | Error (401) |
| CE-28 | Inválida — token corrupto | Token aleatorio/manipulado | Error (401) |

```gherkin
Feature: Renovación de token JWT (Partición de Equivalencia)

  Scenario: CP-REF-001 — Renovación exitosa con refresh_token válido (CE-25)
    Given existe un usuario activo con email "refresh@test.com" y password "password123"
    And el usuario ha iniciado sesión y tiene una cookie "refresh_token" válida
    When envío una solicitud POST a "/api/auth/refresh/" con la cookie "refresh_token"
    Then la respuesta tiene código de estado 200
    And la respuesta establece una nueva cookie "access_token"

  Scenario: CP-REF-002 — Rechazo sin cookie refresh_token (CE-26)
    Given el sistema está disponible
    When envío una solicitud POST a "/api/auth/refresh/" sin cookies
    Then la respuesta tiene código de estado 401

  Scenario: CP-REF-003 — Rechazo con refresh_token expirado (CE-27)
    Given existe un usuario activo con email "expired@test.com"
    And el usuario tiene una cookie "refresh_token" expirada
    When envío una solicitud POST a "/api/auth/refresh/" con la cookie "refresh_token" expirada
    Then la respuesta tiene código de estado 401

  Scenario: CP-REF-004 — Rechazo con refresh_token manipulado (CE-28)
    Given el sistema está disponible
    When envío una solicitud POST a "/api/auth/refresh/" con una cookie "refresh_token" de valor "token.corrupto.xyz"
    Then la respuesta tiene código de estado 401
```

---

### 14.8 Listar Usuarios (`GET /api/users/`)

#### 14.8.1 Partición de Equivalencia — Autenticación y datos

| Clase | Tipo | Representante | Resultado esperado |
|-------|------|---------------|--------------------|
| CE-29 | Válida | Autenticado, existen usuarios | Lista de usuarios (200) |
| CE-30 | Inválida — sin auth | Sin cookie JWT | Error (401) |

```gherkin
Feature: Listar usuarios (Partición de Equivalencia)

  Scenario: CP-LIST-001 — Listado exitoso con autenticación (CE-29)
    Given existen usuarios registrados en el sistema
    And el usuario solicitante está autenticado con una cookie JWT válida
    When envío una solicitud GET a "/api/users/" con la cookie de autenticación
    Then la respuesta tiene código de estado 200
    And la respuesta contiene una lista de usuarios con los campos "id", "email", "username", "role", "is_active"

  Scenario: CP-LIST-002 — Rechazo sin autenticación (CE-30)
    Given el sistema está disponible
    When envío una solicitud GET a "/api/users/" sin cookies de autenticación
    Then la respuesta tiene código de estado 401
```

---

### 14.9 Obtener Usuario por ID (`GET /api/users/{id}/`)

#### 14.9.1 Partición de Equivalencia — Parámetro `id`

| Clase | Tipo | Representante | Resultado esperado |
|-------|------|---------------|--------------------|
| CE-31 | Válida | UUID existente | Usuario retornado (200) |
| CE-32 | Inválida — no existe | UUID válido pero inexistente | Error (404) |
| CE-33 | Inválida — formato | ID no UUID (ej. `"abc"`) | Error (404) |
| CE-34 | Inválida — sin auth | Cualquier ID, sin JWT | Error (401) |

```gherkin
Feature: Obtener usuario por ID (Partición de Equivalencia)

  Scenario: CP-GET-001 — Obtención exitosa de usuario existente (CE-31)
    Given existe un usuario con ID conocido en el sistema
    And el usuario solicitante está autenticado con una cookie JWT válida
    When envío una solicitud GET a "/api/users/{id}/" con el ID del usuario existente
    Then la respuesta tiene código de estado 200
    And la respuesta contiene los campos "id", "email", "username", "role", "is_active"

  Scenario: CP-GET-002 — Usuario no encontrado con UUID inexistente (CE-32)
    Given el usuario solicitante está autenticado con una cookie JWT válida
    When envío una solicitud GET a "/api/users/00000000-0000-0000-0000-000000000000/"
    Then la respuesta tiene código de estado 404

  Scenario: CP-GET-003 — ID con formato inválido (CE-33)
    Given el usuario solicitante está autenticado con una cookie JWT válida
    When envío una solicitud GET a "/api/users/not-a-uuid/"
    Then la respuesta tiene código de estado 404

  Scenario: CP-GET-004 — Sin autenticación (CE-34)
    Given existe un usuario con ID conocido en el sistema
    When envío una solicitud GET a "/api/users/{id}/" sin cookies de autenticación
    Then la respuesta tiene código de estado 401
```

---

### 14.10 Actualizar Email (`PATCH /api/users/{id}/`)

#### 14.10.1 Partición de Equivalencia — Campo `email` en actualización

| Clase | Tipo | Representante | Resultado esperado |
|-------|------|---------------|--------------------|
| CE-35 | Válida | Email nuevo válido y único | Actualización exitosa (200) |
| CE-36 | Inválida — duplicado | Email ya usado por otro usuario | Error (400) |
| CE-37 | Inválida — formato | Email sin formato válido | Error (400) |
| CE-38 | Inválida — usuario no existe | UUID inexistente | Error (404) |

```gherkin
Feature: Actualización de email de usuario (Partición de Equivalencia)

  Scenario: CP-UPD-001 — Actualización exitosa con email válido y único (CE-35)
    Given existe un usuario con ID conocido y email "old@test.com"
    And no existe otro usuario con email "new@test.com"
    And el usuario solicitante está autenticado con una cookie JWT válida
    When envío una solicitud PATCH a "/api/users/{id}/" con los datos:
      | email          |
      | new@test.com   |
    Then la respuesta tiene código de estado 200
    And la respuesta contiene el campo "email" igual a "new@test.com"

  Scenario: CP-UPD-002 — Rechazo por email duplicado (CE-36)
    Given existe un usuario con ID conocido y email "keep@test.com"
    And existe otro usuario con email "taken@test.com"
    And el usuario solicitante está autenticado con una cookie JWT válida
    When envío una solicitud PATCH a "/api/users/{id}/" con los datos:
      | email           |
      | taken@test.com  |
    Then la respuesta tiene código de estado 400
    And la respuesta contiene un mensaje de error indicando que el email ya existe

  Scenario: CP-UPD-003 — Rechazo por formato de email inválido (CE-37)
    Given existe un usuario con ID conocido
    And el usuario solicitante está autenticado con una cookie JWT válida
    When envío una solicitud PATCH a "/api/users/{id}/" con los datos:
      | email          |
      | invalid-email  |
    Then la respuesta tiene código de estado 400

  Scenario: CP-UPD-004 — Usuario no encontrado (CE-38)
    Given el usuario solicitante está autenticado con una cookie JWT válida
    When envío una solicitud PATCH a "/api/users/00000000-0000-0000-0000-000000000000/" con los datos:
      | email              |
      | email@example.com  |
    Then la respuesta tiene código de estado 404
```

#### 14.10.2 Tabla de Decisión — Actualizar email

| # | autenticado | usuario existe | email válido | email único | mismo email actual | Resultado | HTTP |
|:-:|:-----------:|:--------------:|:------------:|:-----------:|:------------------:|-----------|:----:|
| 1 | ✅ | ✅ | ✅ | ✅ | ❌ | Email actualizado, evento publicado | 200 |
| 2 | ✅ | ✅ | ✅ | ✅ | ✅ | Sin cambio (idempotente) | 200 |
| 3 | ✅ | ✅ | ✅ | ❌ | ❌ | Error: email ya existe | 400 |
| 4 | ✅ | ✅ | ❌ | — | — | Error: email inválido | 400 |
| 5 | ✅ | ❌ | ✅ | ✅ | — | Error: usuario no encontrado | 404 |
| 6 | ❌ | — | — | — | — | Error: no autenticado | 401 |

```gherkin
Feature: Actualización de email — Tabla de Decisión

  Scenario: CP-UPD-005 — Regla 1: Email nuevo válido y único, usuario existe
    Given existe un usuario con ID conocido y email "prev@test.com"
    And no existe otro usuario con email "next@test.com"
    And el usuario solicitante está autenticado con una cookie JWT válida
    When envío una solicitud PATCH a "/api/users/{id}/" con los datos:
      | email          |
      | next@test.com  |
    Then la respuesta tiene código de estado 200
    And la respuesta contiene el campo "email" igual a "next@test.com"

  Scenario: CP-UPD-006 — Regla 2: Mismo email actual (idempotente)
    Given existe un usuario con ID conocido y email "same@test.com"
    And el usuario solicitante está autenticado con una cookie JWT válida
    When envío una solicitud PATCH a "/api/users/{id}/" con los datos:
      | email          |
      | same@test.com  |
    Then la respuesta tiene código de estado 200
    And la respuesta contiene el campo "email" igual a "same@test.com"

  Scenario: CP-UPD-007 — Regla 3: Email ya en uso por otro usuario
    Given existe un usuario con ID conocido y email "mine@test.com"
    And existe otro usuario con email "yours@test.com"
    And el usuario solicitante está autenticado con una cookie JWT válida
    When envío una solicitud PATCH a "/api/users/{id}/" con los datos:
      | email           |
      | yours@test.com  |
    Then la respuesta tiene código de estado 400

  Scenario: CP-UPD-008 — Regla 4: Email con formato inválido
    Given existe un usuario con ID conocido
    And el usuario solicitante está autenticado con una cookie JWT válida
    When envío una solicitud PATCH a "/api/users/{id}/" con los datos:
      | email       |
      | not@valid   |
    Then la respuesta tiene código de estado 400

  Scenario: CP-UPD-009 — Regla 5: Usuario no existe
    Given el usuario solicitante está autenticado con una cookie JWT válida
    When envío una solicitud PATCH a "/api/users/99999999-9999-9999-9999-999999999999/" con los datos:
      | email              |
      | test@example.com   |
    Then la respuesta tiene código de estado 404

  Scenario: CP-UPD-010 — Regla 6: Sin autenticación
    Given existe un usuario con ID conocido
    When envío una solicitud PATCH a "/api/users/{id}/" sin cookies de autenticación con los datos:
      | email              |
      | test@example.com   |
    Then la respuesta tiene código de estado 401
```

---

### 14.11 Desactivar Usuario (`POST /api/users/{id}/deactivate/`)

#### 14.11.1 Partición de Equivalencia — Estado del usuario

| Clase | Tipo | Representante | Resultado esperado |
|-------|------|---------------|--------------------|
| CE-39 | Válida | Usuario activo existente | Desactivación exitosa (200) |
| CE-40 | Inválida — ya inactivo | Usuario ya desactivado | Error (400) |
| CE-41 | Inválida — no existe | UUID inexistente | Error (404) |
| CE-42 | Inválida — sin auth | Sin cookie JWT | Error (401) |

```gherkin
Feature: Desactivación de usuario (Partición de Equivalencia)

  Scenario: CP-DEAC-001 — Desactivación exitosa de usuario activo (CE-39)
    Given existe un usuario activo con ID conocido
    And el usuario solicitante está autenticado con una cookie JWT válida
    When envío una solicitud POST a "/api/users/{id}/deactivate/" con los datos:
      | reason                    |
      | Solicitud del usuario     |
    Then la respuesta tiene código de estado 200
    And la respuesta contiene el campo "is_active" igual a false

  Scenario: CP-DEAC-002 — Rechazo al desactivar usuario ya inactivo (CE-40)
    Given existe un usuario inactivo con ID conocido
    And el usuario solicitante está autenticado con una cookie JWT válida
    When envío una solicitud POST a "/api/users/{id}/deactivate/" con los datos:
      | reason             |
      | Intento duplicado  |
    Then la respuesta tiene código de estado 400
    And la respuesta contiene un mensaje de error indicando que el usuario ya está inactivo

  Scenario: CP-DEAC-003 — Usuario no encontrado (CE-41)
    Given el usuario solicitante está autenticado con una cookie JWT válida
    When envío una solicitud POST a "/api/users/00000000-0000-0000-0000-000000000000/deactivate/"
    Then la respuesta tiene código de estado 404

  Scenario: CP-DEAC-004 — Sin autenticación (CE-42)
    Given existe un usuario activo con ID conocido
    When envío una solicitud POST a "/api/users/{id}/deactivate/" sin cookies de autenticación
    Then la respuesta tiene código de estado 401
```

#### 14.11.2 Tabla de Decisión — Desactivar usuario

| # | autenticado | usuario existe | usuario activo | Resultado | HTTP |
|:-:|:-----------:|:--------------:|:--------------:|-----------|:----:|
| 1 | ✅ | ✅ | ✅ | Desactivado, evento `UserDeactivated` publicado | 200 |
| 2 | ✅ | ✅ | ❌ | Error: usuario ya inactivo | 400 |
| 3 | ✅ | ❌ | — | Error: usuario no encontrado | 404 |
| 4 | ❌ | — | — | Error: no autenticado | 401 |

```gherkin
Feature: Desactivación de usuario — Tabla de Decisión

  Scenario: CP-DEAC-005 — Regla 1: Autenticado, usuario existe y está activo
    Given existe un usuario activo con ID conocido
    And el usuario solicitante está autenticado con una cookie JWT válida
    When envío una solicitud POST a "/api/users/{id}/deactivate/" con los datos:
      | reason          |
      | Baja voluntaria |
    Then la respuesta tiene código de estado 200
    And la respuesta contiene el campo "is_active" igual a false

  Scenario: CP-DEAC-006 — Regla 2: Autenticado, usuario existe pero ya está inactivo
    Given existe un usuario inactivo con ID conocido
    And el usuario solicitante está autenticado con una cookie JWT válida
    When envío una solicitud POST a "/api/users/{id}/deactivate/"
    Then la respuesta tiene código de estado 400

  Scenario: CP-DEAC-007 — Regla 3: Autenticado, usuario no existe
    Given el usuario solicitante está autenticado con una cookie JWT válida
    When envío una solicitud POST a "/api/users/11111111-1111-1111-1111-111111111111/deactivate/"
    Then la respuesta tiene código de estado 404

  Scenario: CP-DEAC-008 — Regla 4: No autenticado
    Given existe un usuario activo con ID conocido
    When envío una solicitud POST a "/api/users/{id}/deactivate/" sin autenticación
    Then la respuesta tiene código de estado 401
```

---

### 14.12 Eliminar Usuario (`DELETE /api/users/{id}/`)

#### 14.12.1 Partición de Equivalencia — Eliminación

| Clase | Tipo | Representante | Resultado esperado |
|-------|------|---------------|--------------------|
| CE-43 | Válida | UUID existente, autenticado | Eliminación exitosa (204) |
| CE-44 | Inválida — no existe | UUID inexistente | Error (404) |
| CE-45 | Inválida — sin auth | Sin cookie JWT | Error (401) |

```gherkin
Feature: Eliminación de usuario (Partición de Equivalencia)

  Scenario: CP-DEL-001 — Eliminación exitosa de usuario existente (CE-43)
    Given existe un usuario con ID conocido en el sistema
    And el usuario solicitante está autenticado con una cookie JWT válida
    When envío una solicitud DELETE a "/api/users/{id}/" con la cookie de autenticación
    Then la respuesta tiene código de estado 204
    And el usuario ya no existe en el sistema

  Scenario: CP-DEL-002 — Usuario no encontrado (CE-44)
    Given el usuario solicitante está autenticado con una cookie JWT válida
    When envío una solicitud DELETE a "/api/users/00000000-0000-0000-0000-000000000000/"
    Then la respuesta tiene código de estado 404

  Scenario: CP-DEL-003 — Sin autenticación (CE-45)
    Given existe un usuario con ID conocido en el sistema
    When envío una solicitud DELETE a "/api/users/{id}/" sin cookies de autenticación
    Then la respuesta tiene código de estado 401
```

---

### 14.13 Entidad de Dominio — Validaciones de Negocio

#### 14.13.1 Valores Límite — Validación de email en entidad

| Valor límite | Tipo | Resultado esperado |
|--------------|------|--------------------|
| `""` | Vacío | `InvalidEmail` |
| `"   "` | Solo espacios | `InvalidEmail` |
| `"a@b.co"` | Mínimo válido | Entidad creada |
| `"user@domain.com"` | Email estándar | Entidad creada |

```gherkin
Feature: Entidad User — Validación de email (Valores Límite)

  Scenario: CP-DOM-001 — Rechazo con email vacío
    Given se intenta crear una entidad User
    When se proporciona un email vacío ""
    Then se lanza la excepción "InvalidEmail"

  Scenario: CP-DOM-002 — Rechazo con email de solo espacios
    Given se intenta crear una entidad User
    When se proporciona un email "   "
    Then se lanza la excepción "InvalidEmail"

  Scenario: CP-DOM-003 — Creación exitosa con email mínimo válido
    Given se intenta crear una entidad User
    When se proporciona un email "a@b.co" con username "testuser" y password_hash válido
    Then la entidad User se crea exitosamente

  Scenario: CP-DOM-004 — Creación exitosa con email estándar
    Given se intenta crear una entidad User
    When se proporciona un email "user@domain.com" con username "testuser" y password_hash válido
    Then la entidad User se crea exitosamente
```

#### 14.13.2 Valores Límite — Validación de username en entidad (mín. 3 caracteres)

| Valor límite | Longitud | Resultado esperado |
|--------------|:--------:|--------------------|
| `""` | 0 | `InvalidUsername` |
| `"ab"` | 2 | `InvalidUsername` |
| `"abc"` | 3 | Entidad creada |
| `"abcd"` | 4 | Entidad creada |

```gherkin
Feature: Entidad User — Validación de username (Valores Límite)

  Scenario: CP-DOM-005 — Rechazo con username vacío
    Given se intenta crear una entidad User
    When se proporciona un username vacío ""
    Then se lanza la excepción "InvalidUsername"

  Scenario: CP-DOM-006 — Rechazo con username de 2 caracteres
    Given se intenta crear una entidad User
    When se proporciona un username "ab"
    Then se lanza la excepción "InvalidUsername"

  Scenario: CP-DOM-007 — Creación exitosa con username de 3 caracteres (mínimo)
    Given se intenta crear una entidad User con email válido
    When se proporciona un username "abc"
    Then la entidad User se crea exitosamente

  Scenario: CP-DOM-008 — Creación exitosa con username de 4 caracteres
    Given se intenta crear una entidad User con email válido
    When se proporciona un username "abcd"
    Then la entidad User se crea exitosamente
```

#### 14.13.3 Tabla de Decisión — Método `deactivate()`

| # | `is_active` actual | Resultado | Evento generado |
|:-:|:------------------:|-----------|:---------------:|
| 1 | `true` | `is_active` → `false` | `UserDeactivated` ✅ |
| 2 | `false` | Excepción `UserAlreadyInactive` | Ninguno ❌ |

```gherkin
Feature: Entidad User — Método deactivate() (Tabla de Decisión)

  Scenario: CP-DOM-009 — Regla 1: Desactivar usuario activo
    Given existe una entidad User con "is_active" igual a true
    When se invoca el método "deactivate()" con razón "Baja voluntaria"
    Then el campo "is_active" cambia a false
    And se genera un evento de dominio "UserDeactivated" con la razón "Baja voluntaria"

  Scenario: CP-DOM-010 — Regla 2: Intentar desactivar usuario ya inactivo
    Given existe una entidad User con "is_active" igual a false
    When se invoca el método "deactivate()"
    Then se lanza la excepción "UserAlreadyInactive"
    And no se genera ningún evento de dominio
```

#### 14.13.4 Tabla de Decisión — Método `change_email()`

| # | email nuevo válido | email nuevo ≠ email actual | Resultado | Evento generado |
|:-:|:------------------:|:--------------------------:|-----------|:---------------:|
| 1 | ✅ | ✅ | Email actualizado | `UserEmailChanged` ✅ |
| 2 | ✅ | ❌ (mismo email) | Sin cambio (idempotente) | Ninguno ❌ |
| 3 | ❌ | — | Excepción `InvalidEmail` | Ninguno ❌ |

```gherkin
Feature: Entidad User — Método change_email() (Tabla de Decisión)

  Scenario: CP-DOM-011 — Regla 1: Cambio de email con valor nuevo y válido
    Given existe una entidad User con email "old@test.com"
    When se invoca "change_email('new@test.com')"
    Then el campo "email" cambia a "new@test.com"
    And se genera un evento de dominio "UserEmailChanged" con old_email "old@test.com" y new_email "new@test.com"

  Scenario: CP-DOM-012 — Regla 2: Cambio de email con el mismo valor actual (idempotente)
    Given existe una entidad User con email "same@test.com"
    When se invoca "change_email('same@test.com')"
    Then el campo "email" permanece igual a "same@test.com"
    And no se genera ningún evento de dominio

  Scenario: CP-DOM-013 — Regla 3: Cambio de email con formato inválido
    Given existe una entidad User con email "valid@test.com"
    When se invoca "change_email('not-valid')"
    Then se lanza la excepción "InvalidEmail"
    And no se genera ningún evento de dominio
```

---

### 14.14 Factory — Creación de Usuarios

#### 14.14.1 Valores Límite — Password en Factory (mín. 8 caracteres)

| Valor límite | Longitud | Resultado esperado |
|--------------|:--------:|--------------------|
| `""` | 0 | `InvalidUserData` |
| `"1234567"` | 7 | `InvalidUserData` |
| `"12345678"` | 8 | Usuario creado |
| `"123456789"` | 9 | Usuario creado |

```gherkin
Feature: UserFactory — Validación de password (Valores Límite)

  Scenario: CP-FAC-001 — Rechazo con password vacío
    Given se invoca UserFactory.create con email y username válidos
    When se proporciona un password vacío ""
    Then se lanza la excepción "InvalidUserData" con mensaje "El password debe tener al menos 8 caracteres"

  Scenario: CP-FAC-002 — Rechazo con password de 7 caracteres (debajo del mínimo)
    Given se invoca UserFactory.create con email y username válidos
    When se proporciona un password "1234567"
    Then se lanza la excepción "InvalidUserData" con mensaje "El password debe tener al menos 8 caracteres"

  Scenario: CP-FAC-003 — Creación exitosa con password de 8 caracteres (mínimo válido)
    Given se invoca UserFactory.create con email y username válidos
    When se proporciona un password "12345678"
    Then el usuario se crea exitosamente
    And el campo "password_hash" contiene el hash SHA-256 del password

  Scenario: CP-FAC-004 — Creación exitosa con password de 9 caracteres
    Given se invoca UserFactory.create con email y username válidos
    When se proporciona un password "123456789"
    Then el usuario se crea exitosamente
```

#### 14.14.2 Tabla de Decisión — UserFactory.create()

| # | email válido | username ≥ 3 | password ≥ 8 | role | Resultado |
|:-:|:------------:|:------------:|:------------:|:----:|-----------|
| 1 | ✅ | ✅ | ✅ | USER (default) | Usuario creado con rol USER |
| 2 | ✅ | ✅ | ✅ | ADMIN | Usuario creado con rol ADMIN |
| 3 | ❌ | ✅ | ✅ | — | `InvalidEmail` |
| 4 | ✅ | ❌ | ✅ | — | `InvalidUsername` |
| 5 | ✅ | ✅ | ❌ | — | `InvalidUserData` |
| 6 | ❌ | ❌ | ❌ | — | Primera validación falla (`InvalidEmail`) |

```gherkin
Feature: UserFactory — Tabla de Decisión

  Scenario: CP-FAC-005 — Regla 1: Todos los campos válidos, rol por defecto (USER)
    Given se invoca UserFactory.create
    When se proporcionan email "user@test.com", username "testuser", password "password123"
    Then el usuario se crea exitosamente con rol "USER"

  Scenario: CP-FAC-006 — Regla 2: Todos los campos válidos, rol explícito ADMIN
    Given se invoca UserFactory.create
    When se proporcionan email "admin@test.com", username "adminuser", password "password123" y role "ADMIN"
    Then el usuario se crea exitosamente con rol "ADMIN"

  Scenario: CP-FAC-007 — Regla 3: Email inválido
    Given se invoca UserFactory.create
    When se proporcionan email "invalid", username "testuser", password "password123"
    Then se lanza la excepción "InvalidEmail"

  Scenario: CP-FAC-008 — Regla 4: Username muy corto
    Given se invoca UserFactory.create
    When se proporcionan email "user@test.com", username "ab", password "password123"
    Then se lanza la excepción "InvalidUsername"

  Scenario: CP-FAC-009 — Regla 5: Password muy corto
    Given se invoca UserFactory.create
    When se proporcionan email "user@test.com", username "testuser", password "short"
    Then se lanza la excepción "InvalidUserData"

  Scenario: CP-FAC-010 — Regla 6: Todos los campos inválidos
    Given se invoca UserFactory.create
    When se proporcionan email "", username "ab", password "123"
    Then se lanza la excepción "InvalidEmail"
```

---

### 14.15 Resumen de Cobertura por Técnica de Diseño

| Técnica | Casos de Prueba | Funcionalidades Cubiertas |
|---------|:---------------:|---------------------------|
| **Partición de Equivalencia (PE)** | 45 clases (CE-01 a CE-45) | Registro, Login, Perfil, Logout, Rol, Health, Refresh, Listar, Obtener, Actualizar, Desactivar, Eliminar |
| **Valores Límite (VL)** | 19 escenarios | username (2,3,4,49,50,51 chars), password (7,8,9 chars), email (vacío, espacios, mínimo), password factory |
| **Tabla de Decisión (TD)** | 8 tablas, 37 reglas | Registro (7 reglas), Login (5), Rol (5), Actualizar email (6), Desactivar (4), deactivate() (2), change_email() (3), Factory (6) |

| Total de escenarios Gherkin | **88** |
|-----------------------------|:------:|

---

*Documento generado el 25 de febrero de 2026.*  
*Basado en el estándar ISO/IEC 25010:2023 — Modelo de calidad de producto de software.*
