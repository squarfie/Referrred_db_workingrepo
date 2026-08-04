from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wgs_app", "0016_custom_pipeline_multi_category"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customwgspipeline",
            name="platform",
            field=models.CharField(default="Illumina", max_length=100),
        ),
    ]
