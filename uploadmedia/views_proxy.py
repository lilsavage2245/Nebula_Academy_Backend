# uploadmedia/views_proxy.py  (new file)
import re
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
import requests

CF_UPLOAD_HOST = "upload.cloudflarestream.com"
CF_UPLOAD_RE = re.compile(rf"^https://{CF_UPLOAD_HOST}/[A-Za-z0-9]+$")

@csrf_exempt
def proxy_direct_upload(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    to = request.GET.get("to")
    if not to or not CF_UPLOAD_RE.match(to):
        return JsonResponse({"detail": "Invalid or missing 'to' upload URL"}, status=400)

    # IMPORTANT: stream the body without loading it all in memory
    input_stream = request.META.get("wsgi.input")
    if not input_stream:
        return JsonResponse({"detail": "No input stream"}, status=400)

    def gen():
        while True:
            chunk = input_stream.read(1024 * 1024)  # 1 MiB
            if not chunk:
                break
            yield chunk

    try:
        upstream = requests.post(
            to,
            data=gen(),                                 # generator = chunked transfer
            headers={"Content-Type": "application/octet-stream"},
            timeout=None,                                # allow large uploads
        )
    except Exception as e:
        return JsonResponse({"detail": "proxy_failed", "message": str(e)}, status=502)

    return HttpResponse(
        upstream.content,
        status=upstream.status_code,
        content_type=upstream.headers.get("Content-Type", "text/plain"),
    )
