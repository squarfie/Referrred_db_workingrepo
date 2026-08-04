from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("home", "0036_rename_lab_manager_role"),
        ("home_final", "0022_remove_unique_final_bat_seq_per_batch"),
        ("wgs_app", "0013_sampleinformation_dna_extraction_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomWGSPipeline",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150, unique=True)),
                ("slug", models.SlugField(max_length=170, unique=True)),
                ("description", models.TextField(blank=True)),
                ("sequencing_type", models.CharField(choices=[("short_read", "Short read"), ("long_read", "Long read"), ("hybrid", "Hybrid"), ("other", "Other")], default="short_read", max_length=20)),
                ("platform", models.CharField(choices=[("illumina", "Illumina"), ("nanopore", "Nanopore"), ("pacbio", "PacBio"), ("hybrid", "Hybrid"), ("other", "Other")], default="illumina", max_length=20)),
                ("category", models.CharField(blank=True, max_length=100)),
                ("sheet_name", models.CharField(blank=True, max_length=120)),
                ("accession_column", models.CharField(default="accession", max_length=120)),
                ("sample_name_column", models.CharField(blank=True, max_length=120)),
                ("date_column", models.CharField(blank=True, max_length=120)),
                ("show_in_upload_center", models.BooleanField(default=True)),
                ("show_in_overview", models.BooleanField(default=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="custom_wgs_pipelines", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "custom_wgs_pipeline", "ordering": ["sequencing_type", "name"]},
        ),
        migrations.CreateModel(
            name="CustomWGSPipelineUploadBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file_name", models.CharField(max_length=255)),
                ("sheet_name", models.CharField(blank=True, max_length=120)),
                ("row_count", models.PositiveIntegerField(default=0)),
                ("created_count", models.PositiveIntegerField(default=0)),
                ("updated_count", models.PositiveIntegerField(default=0)),
                ("skipped_count", models.PositiveIntegerField(default=0)),
                ("matched_count", models.PositiveIntegerField(default=0)),
                ("unmatched_count", models.PositiveIntegerField(default=0)),
                ("status", models.CharField(choices=[("completed", "Completed"), ("completed_with_warnings", "Completed with warnings"), ("failed", "Failed")], default="completed", max_length=30)),
                ("error_log", models.TextField(blank=True)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("pipeline", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="upload_batches", to="wgs_app.customwgspipeline")),
                ("uploaded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="custom_wgs_upload_batches", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "custom_wgs_pipeline_upload_batch", "ordering": ["-uploaded_at", "-id"]},
        ),
        migrations.CreateModel(
            name="CustomWGSPipelineField",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("field_key", models.SlugField(max_length=120)),
                ("display_label", models.CharField(max_length=150)),
                ("source_column", models.CharField(max_length=150)),
                ("column_aliases", models.TextField(blank=True)),
                ("data_type", models.CharField(choices=[("text", "Text"), ("integer", "Integer"), ("decimal", "Decimal"), ("date", "Date"), ("boolean", "Boolean")], default="text", max_length=20)),
                ("required", models.BooleanField(default=False)),
                ("default_value", models.CharField(blank=True, max_length=255)),
                ("show_in_table", models.BooleanField(default=True)),
                ("show_in_detail", models.BooleanField(default=True)),
                ("show_in_export", models.BooleanField(default=True)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("pipeline", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="fields", to="wgs_app.customwgspipeline")),
            ],
            options={"db_table": "custom_wgs_pipeline_field", "ordering": ["sort_order", "display_label"], "unique_together": {("pipeline", "field_key")}},
        ),
        migrations.CreateModel(
            name="CustomWGSPipelineRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("accession", models.CharField(db_index=True, max_length=255)),
                ("sample_name", models.CharField(blank=True, max_length=255)),
                ("match_status", models.CharField(choices=[("matched", "Matched"), ("unmatched", "Unmatched"), ("invalid", "Invalid")], db_index=True, default="unmatched", max_length=20)),
                ("match_source", models.CharField(blank=True, choices=[("final", "Final data"), ("raw", "Raw data"), ("wgs_project", "WGS project"), ("", "None")], default="", max_length=20)),
                ("values_json", models.JSONField(blank=True, default=dict)),
                ("raw_row_json", models.JSONField(blank=True, default=dict)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("matched_final_data", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="custom_wgs_records", to="home_final.final_data", to_field="f_AccessionNo")),
                ("matched_raw_data", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="custom_wgs_records", to="home.referred_data", to_field="AccessionNo")),
                ("pipeline", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="records", to="wgs_app.customwgspipeline")),
                ("upload_batch", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="records", to="wgs_app.customwgspipelineuploadbatch")),
                ("uploaded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="custom_wgs_records", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "custom_wgs_pipeline_record",
                "ordering": ["pipeline", "accession", "-uploaded_at"],
                "indexes": [
                    models.Index(fields=["pipeline", "accession"], name="custom_wgs_pipeline_rec_acc_idx"),
                    models.Index(fields=["pipeline", "match_status"], name="custom_wgs_pipeline_rec_match_idx"),
                ],
            },
        ),
    ]
