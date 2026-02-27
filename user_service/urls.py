"""
URL configuration for user_service project.

La configuración de URLs del proyecto incluye:
- /admin/: Interfaz de administración de Django
- /api/: Rutas de la API REST de la aplicación users

Para microservicios, todas las rutas de API deben estar bajo /api/
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # OpenAPI 3.0 schema (JSON) — sin UI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # API de la aplicación users
    # Las rutas de users se configuran en users/urls.py
    path('api/', include('users.urls')),  # incluye las rutas /api/auth/, /api/health/
]
