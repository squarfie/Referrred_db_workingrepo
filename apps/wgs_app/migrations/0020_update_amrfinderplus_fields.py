from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wgs_app", "0019_update_mlst_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="amrfinderplus",
            name="amrfinder_id",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="amrfinderplus",
            name="hierarchy_node",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
