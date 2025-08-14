from django.core.management.base import BaseCommand
import smtplib

class Command(BaseCommand):
    help = "Test SMTP connectivity from this environment"

    def handle(self, *args, **options):
        host='sandbox.smtp.mailtrap.io'
        combos = [(2525, False, True), (587, False, True), (465, True, False)]
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
                self.stdout.write(self.style.SUCCESS(f"OK: connected on {port} (SSL={use_ssl}, TLS={use_tls})"))
                s.quit()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"FAIL on {port}: {e.__class__.__name__}: {e}"))
