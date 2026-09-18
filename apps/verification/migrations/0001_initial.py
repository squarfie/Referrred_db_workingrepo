# Generated for verifier workflow.

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("home", "0043_nonworkingday_is_recurring"),
        ("home_final", "0027_concordanceoptions_is_active"),
    ]

    operations = [
        migrations.CreateModel(
            name="VerificationCase",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("for_verification", "For Verification"),
                            ("withdrawn_by_checker", "Withdrawn by Checker"),
                            ("returned_to_encoder", "Returned to Encoder"),
                            ("returned_to_checker", "Returned to Checker"),
                            ("approved_by_verifier", "Approved by Verifier"),
                            ("signed_by_head", "Signed by ARSRL Head"),
                            ("released", "Released"),
                        ],
                        default="draft",
                        max_length=40,
                    ),
                ),
                ("note", models.TextField(blank=True, default="")),
                ("sent_to_verifier_at", models.DateTimeField(blank=True, null=True)),
                ("withdrawn_at", models.DateTimeField(blank=True, null=True)),
                ("verifier_decision_at", models.DateTimeField(blank=True, null=True)),
                ("signed_by_head_at", models.DateTimeField(blank=True, null=True)),
                ("qr_token", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("qr_generated_at", models.DateTimeField(blank=True, null=True)),
                ("released_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "assigned_checker",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assigned_checker_cases",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "assigned_verifier",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assigned_verifier_cases",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_verification_cases",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "final_accession",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="verification_cases",
                        to="home_final.final_data",
                    ),
                ),
                (
                    "final_batch",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="verification_cases",
                        to="home.batch_table",
                    ),
                ),
                (
                    "sent_by_checker",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="sent_verification_cases",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "signed_by_head",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="head_signed_verification_cases",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "verifier_decision_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="decided_verification_cases",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "withdrawn_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="withdrawn_verification_cases",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-updated_at", "-created_at"),
            },
        ),
        migrations.CreateModel(
            name="VerificationComment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("field_name", models.CharField(blank=True, default="", max_length=150)),
                ("field_label", models.CharField(blank=True, default="", max_length=150)),
                ("field_value_snapshot", models.TextField(blank=True, default="")),
                ("comment", models.TextField()),
                (
                    "decision",
                    models.CharField(
                        choices=[
                            ("note", "Note"),
                            ("approved", "Approved"),
                            ("needs_correction", "Needs Correction"),
                            ("returned", "Returned"),
                            ("resolved", "Resolved"),
                        ],
                        default="note",
                        max_length=30,
                    ),
                ),
                ("is_resolved", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="verification_comments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "final_accession_ref_sequence",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="verifier_comments",
                        to="home_final.final_data",
                    ),
                ),
                (
                    "verification_case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comments",
                        to="verification.verificationcase",
                    ),
                ),
            ],
            options={
                "verbose_name": "Verifier Comment",
                "verbose_name_plural": "Verifier Comments",
                "ordering": ("-created_at",),
            },
        ),
        migrations.AddConstraint(
            model_name="verificationcase",
            constraint=models.UniqueConstraint(
                condition=models.Q(final_accession__isnull=True, final_batch__isnull=False),
                fields=("final_batch",),
                name="one_batch_verification_case",
            ),
        ),
        migrations.AddConstraint(
            model_name="verificationcase",
            constraint=models.UniqueConstraint(
                condition=models.Q(final_accession__isnull=False, final_batch__isnull=True),
                fields=("final_accession",),
                name="one_accession_verification_case",
            ),
        ),
    ]
