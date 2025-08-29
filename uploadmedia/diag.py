# uploadmedia/diag.py
import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response

class CloudflareDiag(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        token = settings.CF_STREAM_TOKEN
        acct  = settings.CF_ACCOUNT_ID
        ok_token = bool(token and len(token) > 20)
        ok_acct  = bool(acct and len(acct) > 10)

        # Try token verify
        ver = {}
        try:
            r = requests.get(
                "https://api.cloudflare.com/client/v4/user/tokens/verify",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )
            ver = r.json()
        except Exception as e:
            ver = {"error": str(e)}

        # Try /stream list (simple read)
        stream = {}
        try:
            r2 = requests.get(
                f"https://api.cloudflare.com/client/v4/accounts/{acct}/stream",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )
            stream = r2.json()
        except Exception as e:
            stream = {"error": str(e)}

        return Response({
            "has_CF_STREAM_TOKEN": ok_token,
            "has_CF_ACCOUNT_ID": ok_acct,
            "verify": ver,
            "stream_list": stream,
        })
