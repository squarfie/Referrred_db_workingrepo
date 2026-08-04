from django.db import migrations, models


BUILTIN_PIPELINES = [
    ("sample_information", "Sample Information", True, False, 10),
    ("bactscout", "BactScout", True, True, 20),
    ("gtdbtk", "GTDB-Tk", True, False, 30),
    ("gambit", "Gambit", True, True, 40),
    ("mlst", "MLST", True, True, 50),
    ("checkm2", "CheckM2", True, True, 60),
    ("assembly", "Assembly Scan", True, True, 70),
    ("amrfinder", "AMRFinderPlus", True, True, 80),
]


def seed_builtin_pipeline_settings(apps, schema_editor):
    setting_model = apps.get_model("wgs_app", "BuiltinWGSPipelineSetting")
    for key, name, show_upload, show_overview, sort_order in BUILTIN_PIPELINES:
        setting_model.objects.update_or_create(
            pipeline_key=key,
            defaults={
                "display_name": name,
                "show_in_upload_center": show_upload,
                "show_in_overview": show_overview,
                "sort_order": sort_order,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("wgs_app", "0014_custom_wgs_pipeline"),
    ]

    operations = [
        migrations.CreateModel(
            name="BuiltinWGSPipelineSetting",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("pipeline_key", models.CharField(choices=[("sample_information", "Sample Information"), ("bactscout", "BactScout"), ("gtdbtk", "GTDB-Tk"), ("gambit", "Gambit"), ("mlst", "MLST"), ("checkm2", "CheckM2"), ("assembly", "Assembly Scan"), ("amrfinder", "AMRFinderPlus")], max_length=50, unique=True)),
                ("display_name", models.CharField(max_length=100)),
                ("show_in_upload_center", models.BooleanField(default=True)),
                ("show_in_overview", models.BooleanField(default=True)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "builtin_wgs_pipeline_setting",
                "ordering": ["sort_order", "display_name"],
            },
        ),
        migrations.RunPython(seed_builtin_pipeline_settings, migrations.RunPython.noop),
    ]
