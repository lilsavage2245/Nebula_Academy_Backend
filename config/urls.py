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
from django.views.decorators.csrf import ensure_csrf_cookie

def api_root(_):
    return JsonResponse({
        "name": "Nebula Code Academy API (staging)",
        "version": "0.1.0",
        "health": "/health/",
        "docs": "/api/docs/",            # add later if you want
        "endpoints": {
            "programs": "/api/programs/",    # adjust to your real paths
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
    path("api/", api_root),  
    path("csrf/", csrf_ping),

]

