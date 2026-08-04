from django.db import migrations, models
from django.db.models import F


def backfill_editable_phenotypes(apps, schema_editor):
    FinalData = apps.get_model("home_final", "Final_Data")
    FinalData.objects.update(
        f_Site_Pre_ed=F("f_Site_Pre"),
        f_Site_Pos_ed=F("f_Site_Pos"),
        f_ars_Pre_ed=F("f_ars_Pre"),
        f_ars_Post_ed=F("f_ars_Post"),
    )


class Migration(migrations.Migration):

    dependencies = [
        ("home_final", "0015_backfill_f_age_display"),
    ]

    operations = [
        migrations.AddField(
            model_name="final_data",
            name="f_Site_Pre_ed",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="final_data",
            name="f_Site_Pos_ed",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="final_data",
            name="f_ars_Pre_ed",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="final_data",
            name="f_ars_Post_ed",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.RunPython(backfill_editable_phenotypes, migrations.RunPython.noop),
    ]
