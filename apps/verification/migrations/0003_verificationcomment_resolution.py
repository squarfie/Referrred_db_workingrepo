import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("verification", "0002_lab_manager_head_workflow"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="verificationcomment",
            name="resolution_status",
            field=models.CharField(
                choices=[
                    ("open", "Open"),
                    ("handled", "Handled by Encoder/Checker"),
                    ("resolved", "Resolved by Verifier"),
                    ("rejected", "Rejected"),
                ],
                default="open",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="verificationcomment",
            name="resolution_note",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="verificationcomment",
            name="resolved_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="verificationcomment",
            name="resolved_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="resolved_verification_comments",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
