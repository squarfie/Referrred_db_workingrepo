from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0033_breakpointstable_org_code_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitedata",
            name="Site_Lab_Head_Credentials",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="sitedata",
            name="Site_Med_Ctr_Chief_Credentials",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="sitedata",
            name="Site_MedTech_Credentials",
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
