from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wgs_app", "0021_update_bactscout_fields"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="customwgspipelinerecord",
            name="matched_raw_data",
        ),
        migrations.AlterField(
            model_name="customwgspipelinerecord",
            name="match_source",
            field=models.CharField(
                blank=True,
                choices=[
                    ("final", "Final data"),
                    ("wgs_project", "WGS project"),
                    ("", "None"),
                ],
                default="",
                max_length=20,
            ),
        ),
    ]
