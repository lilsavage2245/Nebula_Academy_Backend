# people/migrations/0003_backfill_policy_versions.py
from django.db import migrations

def backfill(apps, schema_editor):
    from django.conf import settings
    policy = getattr(settings, "POLICY_VERSIONS", {"terms": "", "privacy": ""})
    OnboardingSurvey = apps.get_model("people", "OnboardingSurvey")
    (OnboardingSurvey.objects
        .filter(terms_version="")
        .update(terms_version=policy.get("terms", "")))
    (OnboardingSurvey.objects
        .filter(privacy_version="")
        .update(privacy_version=policy.get("privacy", "")))

class Migration(migrations.Migration):

    dependencies = [
        ("people", "0002_onboardingsurvey_accept_privacy_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
