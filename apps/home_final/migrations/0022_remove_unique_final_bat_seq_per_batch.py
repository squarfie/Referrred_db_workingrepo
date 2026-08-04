from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("home_final", "0021_remove_final_data_f_arsp_rev_lic_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="final_data",
            name="unique_final_bat_seq_per_batch",
        ),
    ]
