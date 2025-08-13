"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import path, include
from django.http import JsonResponse

# DEBUG ONLY — remove after fixing
from django.http import HttpResponse
from django.contrib.auth import get_user_model, login

# --- DEBUG ONLY, remove after fixing ---
from django.http import HttpResponse
from django.db import connection

from django.http import HttpResponse
from django.conf import settings
from django.db import connection
import os

def env_check(request):
    db = settings.DATABASES["default"]
    lines = [
        f"DJANGO_SETTINGS_MODULE env = {os.getenv('DJANGO_SETTINGS_MODULE')}",
        f"settings module loaded = {getattr(settings, 'SETTINGS_MODULE', None)}",
        f"HAS DATABASE_URL env = {bool(os.getenv('DATABASE_URL'))}",
        f"DATABASES.default.ENGINE = {db.get('ENGINE')}",
        f"DATABASES.default.NAME = {db.get('NAME')}",
        f"DATABASES.default.HOST = {db.get('HOST')}",
        f'connection.vendor = {connection.vendor}',
    ]
    return HttpResponse("<br>".join(lines))


def db_check(request):
    s = connection.settings_dict
    host = s.get("HOST")
    name = s.get("NAME")
    user = s.get("USER")
    return HttpResponse(f"web DB -> host={host}, name={name}, user={user}")
# --------------------------------------


def whoami(request):
    u = request.user
    return HttpResponse(f"auth={u.is_authenticated}, user={getattr(u, 'email', getattr(u, 'username', 'anon'))}")

def force_login(request):
    U = get_user_model()
    u = U.objects.get(email="admin.staging@nebulacodeacademy.com")
    # ensure Django knows which backend to use
    u.backend = "django.contrib.auth.backends.ModelBackend"
    login(request, u)
    return HttpResponse("logged-in")

def health(_):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('api/program/', include('program.urls')),
    path('api/module/', include('module.urls')),
    path('api/news/', include('news.urls')),
    path('api/classes/', include('classes.urls')),
    path('api/worksheet/', include('worksheet.urls')),
    path('api/achievement/', include('achievement.urls')),
    path('api/dashboard/', include('dashboard.urls')), 
    path("api/engagement/", include("engagement.urls")),
    path("health/", health),
    path("whoami/", whoami),
    path("force-login/", force_login),
    path("db-check/", db_check),
    path("env-check/", env_check),

]

