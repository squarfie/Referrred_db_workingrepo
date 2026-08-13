from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wgs_app", "0018_rename_custom_wgs_pipeline_rec_acc_idx_custom_wgs__pipelin_a90caf_idx_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="mlst",
            old_name="name",
            new_name="file",
        ),
        migrations.RenameField(
            model_name="mlst",
            old_name="mlst",
            new_name="st",
        ),
        migrations.AddField(
            model_name="mlst",
            name="status",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="mlst",
            name="score",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="mlst",
            name="alleles",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.RemoveField(
            model_name="mlst",
            name="allele1",
        ),
        migrations.RemoveField(
            model_name="mlst",
            name="allele2",
        ),
        migrations.RemoveField(
            model_name="mlst",
            name="allele3",
        ),
        migrations.RemoveField(
            model_name="mlst",
            name="allele4",
        ),
        migrations.RemoveField(
            model_name="mlst",
            name="allele5",
        ),
        migrations.RemoveField(
            model_name="mlst",
            name="allele6",
        ),
        migrations.RemoveField(
            model_name="mlst",
            name="allele7",
        ),
    ]
