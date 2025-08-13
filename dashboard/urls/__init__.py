from django.urls import include, path

urlpatterns = [
    path('free/', include('dashboard.urls.free')),
]
