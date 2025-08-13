# core/utils/urls.py
from django.conf import settings

def build_full_url(request, path: str) -> str:
    """
    Builds a full absolute URL using the current request or settings fallback.

    Args:
        request: The HTTP request (can be None for tasks or testing).
        path: The relative path to append (e.g., /reset-password/?token=abc)

    Returns:
        A fully qualified URL like https://domain.com/path
    """
    domain = getattr(settings, "SITE_DOMAIN", None)
    if not domain and request:
        domain = request.get_host()
    if not domain:
        domain = "localhost:8000"  # fallback

    scheme = "https" if not settings.DEBUG else "http"
    return f"{scheme}://{domain}{path}"
