from django.db import migrations, models
from django.db.models import F


def backfill_editable_phenotypes(apps, schema_editor):
    ReferredData = apps.get_model("home", "Referred_Data")
    ReferredData.objects.update(
        Site_Pre_ed=F("Site_Pre"),
        Site_Pos_ed=F("Site_Pos"),
        ars_Pre_ed=F("ars_Pre"),
        ars_Post_ed=F("ars_Post"),
    )


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0023_alter_sitedata_contact_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="referred_data",
            name="Site_Pre_ed",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="referred_data",
            name="Site_Pos_ed",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="referred_data",
            name="ars_Pre_ed",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="referred_data",
            name="ars_Post_ed",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.RunPython(backfill_editable_phenotypes, migrations.RunPython.noop),
    ]
