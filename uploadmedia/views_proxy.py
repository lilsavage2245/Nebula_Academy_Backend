# uploadmedia/views_proxy.py
import os, re, tempfile
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
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

    # 1) Spill the incoming request body to a temp file (don’t trust Content-Length;
    #    read until EOF so we never under/over-read).
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False)
        src = request.META.get("wsgi.input")
        chunk = b""
        while True:
            chunk = src.read(1024 * 1024)
            if not chunk:
                break
            tmp.write(chunk)
        tmp.flush()
        size = os.path.getsize(tmp.name)
    except Exception as e:
        try:
            tmp.close(); os.unlink(tmp.name)
        except Exception:
            pass
        return JsonResponse({"detail": "proxy_buffer_failed", "message": str(e)}, status=502)

    # 2) Post the file to Cloudflare with a fixed Content-Length (no chunked)
    try:
        with open(tmp.name, "rb") as f:
            # Let requests derive Content-Length from the file descriptor.
            # Also explicitly set a simple Content-Type.
            upstream = requests.post(
                to,
                data=f,  # raw body, not multipart
                headers={
                    "Content-Type": "application/octet-stream",
                    # explicitly pin Content-Length to avoid chunked transfer
                    "Content-Length": str(size),
                    # disable 100-continue shenanigans on some proxies
                    "Expect": "",
                },
                timeout=None,
            )
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass

    # 3) Relay Cloudflare’s response verbatim to your client
    return HttpResponse(
        upstream.content,
        status=upstream.status_code,
        content_type=upstream.headers.get("Content-Type", "text/plain"),
    )
