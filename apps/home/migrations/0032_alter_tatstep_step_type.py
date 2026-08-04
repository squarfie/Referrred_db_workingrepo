from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0031_remove_unique_bat_seq_per_batch'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tatstep',
            name='step_type',
            field=models.CharField(max_length=500),
        ),
    ]
