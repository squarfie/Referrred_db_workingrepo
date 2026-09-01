from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("home_final", "0025_concordanceoptions_applied_org_grp"),
    ]

    operations = [
        migrations.AlterField(
            model_name="concordanceoptions",
            name="report",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="options",
                to="home_final.concordancereport",
            ),
        ),
    ]
