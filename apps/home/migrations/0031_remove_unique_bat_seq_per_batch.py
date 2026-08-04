from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0030_remove_batch_table_bat_rev_lic_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="referred_data",
            name="unique_bat_seq_per_batch",
        ),
    ]
