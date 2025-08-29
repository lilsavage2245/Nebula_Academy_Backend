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
# config/urls.py
from django.contrib import admin
from django.urls import path, include, re_path
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings
from django.conf.urls.static import static


def api_root(_):
    return JsonResponse({
        "name": "Nebula Code Academy API (staging)",
        "version": "0.1.0",
        "health": "/health/",
        "docs": "/api/docs/",  # add later if you want
        "endpoints": {
            "me": "/api/me/",
            "login (JWT)": "/api/token/",
            "refresh (JWT)": "/api/token/refresh/",
            "program": "/api/program/",
            "news": "/api/news/",
            "classes": "/api/classes/",
            "achievements": "/api/achievement/",
        }
    })

@ensure_csrf_cookie
def csrf_ping(_):
    return JsonResponse({"ok": True})

def health(_):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path("admin/", admin.site.urls),

    # Utilities / global endpoints
    path("health/", health),
    path("csrf/", csrf_ping),

    # Exact API root BEFORE the includes
    re_path(r"^api/$", api_root, name="api-root"),

    # App routers
    path("api/", include("core.urls")),          # contains /token/, /token/refresh/, /me/, etc.
    path("api/program/", include("program.urls")),
    path("api/module/", include("module.urls")),
    path("api/news/", include("news.urls")),
    path("api/classes/", include("classes.urls")),
    path("api/worksheet/", include("worksheet.urls")),
    path("api/achievement/", include("achievement.urls")),
    path("api/dashboard/", include("dashboard.urls")),
    path("api/engagement/", include("engagement.urls")),
    path("api/media/", include("uploadmedia.urls")),  # ← keep this prefix
]


if settings.DEBUG and settings.STORAGE_BACKEND == "local":
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)