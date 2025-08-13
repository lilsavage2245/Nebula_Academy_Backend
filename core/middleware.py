# core/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout

class InvalidateOnPasswordChangeMiddleware(MiddlewareMixin):
    """
    Force logout if the user's session was created before their last password change.
    """
    def process_request(self, request):
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            session_ts = request.session.get('password_changed_at')
            pw_ts = user.password_changed_at and user.password_changed_at.timestamp()
            if pw_ts and (session_ts is None or session_ts < pw_ts):
                logout(request)
            else:
                # store current pw timestamp in session
                request.session['password_changed_at'] = pw_ts