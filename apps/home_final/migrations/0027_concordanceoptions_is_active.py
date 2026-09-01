from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home_final", "0026_alter_concordanceoptions_report_nullable"),
    ]

    operations = [
        migrations.AddField(
            model_name="concordanceoptions",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
    ]
