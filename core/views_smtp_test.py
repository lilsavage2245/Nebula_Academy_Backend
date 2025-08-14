import smtplib
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(["GET"])
def smtp_test(request):
    host = "sandbox.smtp.mailtrap.io"
    combos = [
        (2525, False, True),
        (587, False, True),
        (465, True, False),
    ]
    results = []
    for port, use_ssl, use_tls in combos:
        try:
            if use_ssl:
                s = smtplib.SMTP_SSL(host, port, timeout=8)
            else:
                s = smtplib.SMTP(host, port, timeout=8)
                if use_tls:
                    s.ehlo()
                    s.starttls()
            s.ehlo()
            results.append({
                "port": port,
                "use_ssl": use_ssl,
                "use_tls": use_tls,
                "status": "OK"
            })
            s.quit()
        except Exception as e:
            results.append({
                "port": port,
                "use_ssl": use_ssl,
                "use_tls": use_tls,
                "status": f"FAIL - {e.__class__.__name__}: {e}"
            })
    return Response(results)
