from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0022_backfill_age_display"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sitedata",
            name="Site_Lab_Head_Contact",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name="sitedata",
            name="Site_Med_Ctr_Chief_Contact",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name="sitedata",
            name="Site_MedTech_Contact",
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
