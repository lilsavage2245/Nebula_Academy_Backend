# core/throttling.py
from rest_framework.throttling import SimpleRateThrottle

class PasswordResetRateThrottle(SimpleRateThrottle):
    scope = 'password_reset'

    def get_cache_key(self, request, view):
        # Throttle by email address to limit reset requests per user
        email = request.data.get('email', '').lower().strip()
        if not email:
            return None
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.normalize_ident(email)
        }

    def normalize_ident(self, ident):
        return ident.strip().lower()
