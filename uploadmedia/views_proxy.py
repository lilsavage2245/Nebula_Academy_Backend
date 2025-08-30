# uploadmedia/views_proxy.py
import os
import re
import tempfile
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
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

    # 1) Get content length from client (browser sets this)
    content_length = request.META.get("CONTENT_LENGTH")
    try:
        content_length_int = int(content_length) if content_length is not None else None
    except ValueError:
        content_length_int = None

    if not content_length_int or content_length_int <= 0:
        # Cloudflare rejects chunked uploads; we must provide Content-Length
        return JsonResponse({"detail": "Missing or invalid Content-Length"}, status=400)

    # 2) Spill request body to a temp file so we can pass a file object with a fixed length
    #    (Prevents DRF/Django from buffering in RAM and gives requests a seekable stream.)
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False)
        # copy from wsgi.input to tmp in chunks
        src = request.META.get("wsgi.input")
        remaining = content_length_int
        chunk_size = 1024 * 1024
        while remaining > 0:
            chunk = src.read(min(chunk_size, remaining))
            if not chunk:
                break
            tmp.write(chunk)
            remaining -= len(chunk)
        tmp.flush()
        tmp.seek(0)
    except Exception as e:
        try:
            tmp.close()
            os.unlink(tmp.name)
        except Exception:
            pass
        return JsonResponse({"detail": "proxy_buffer_failed", "message": str(e)}, status=502)

    # 3) Forward to Cloudflare with Content-Length and raw bytes
    try:
        with open(tmp.name, "rb") as f:
            upstream = requests.post(
                to,
                data=f,  # file-like with known length
                headers={
                    "Content-Type": "application/octet-stream",
                    "Content-Length": str(content_length_int),
                },
                timeout=None,  # large uploads
            )
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass

    return HttpResponse(
        upstream.content,
        status=upstream.status_code,
        content_type=upstream.headers.get("Content-Type", "text/plain"),
    )
