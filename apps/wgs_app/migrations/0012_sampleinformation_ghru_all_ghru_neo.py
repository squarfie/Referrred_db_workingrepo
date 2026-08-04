# Generated manually for WGS sample information programme flags.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wgs_app", "0011_alter_bactscout_species_abundance_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="sampleinformation",
            name="ghru_all",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="sampleinformation",
            name="ghru_neo",
            field=models.BooleanField(default=False),
        ),
    ]
