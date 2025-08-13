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

]

