import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("verification", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="verificationcase",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Draft"),
                    ("for_verification", "For Verification"),
                    ("withdrawn_by_checker", "Withdrawn by Checker"),
                    ("returned_to_encoder", "Returned to Encoder"),
                    ("returned_to_checker", "Returned to Checker"),
                    ("approved_by_verifier", "Approved by Verifier"),
                    ("for_lab_manager", "For Lab Manager"),
                    ("returned_to_verifier", "Returned to Verifier"),
                    ("approved_by_lab_manager", "Approved by Lab Manager"),
                    ("for_head", "For ARSRL Head"),
                    ("disapproved_by_lab_manager", "Disapproved by Lab Manager"),
                    ("disapproved_by_head", "Disapproved by ARSRL Head"),
                    ("signed_by_head", "Signed by ARSRL Head"),
                    ("released", "Released"),
                ],
                default="draft",
                max_length=40,
            ),
        ),
        migrations.AddField(
            model_name="verificationcase",
            name="assigned_lab_manager",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assigned_lab_manager_cases",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="verificationcase",
            name="assigned_head",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assigned_head_cases",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="verificationcase",
            name="sent_to_lab_manager_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="verificationcase",
            name="sent_to_lab_manager_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="sent_lab_manager_verification_cases",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="verificationcase",
            name="lab_manager_decision_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="verificationcase",
            name="lab_manager_decision_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="lab_manager_decided_verification_cases",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="verificationcase",
            name="sent_to_head_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="verificationcase",
            name="sent_to_head_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="sent_head_verification_cases",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="verificationcase",
            name="head_decision_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="verificationcase",
            name="head_decision_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="head_decided_verification_cases",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
