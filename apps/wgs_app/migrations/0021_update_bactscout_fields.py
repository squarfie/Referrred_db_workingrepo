from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("wgs_app", "0020_update_amrfinderplus_fields"),
    ]

    operations = [
        migrations.RenameField(
            model_name="bactscout",
            old_name="name",
            new_name="sample_id",
        ),
        migrations.RemoveField(
            model_name="bactscout",
            name="status",
        ),
        migrations.RemoveField(
            model_name="bactscout",
            name="completeness",
        ),
        migrations.RemoveField(
            model_name="bactscout",
            name="contamination",
        ),
        migrations.RemoveField(
            model_name="bactscout",
            name="completeness_model_used",
        ),
        migrations.RemoveField(
            model_name="bactscout",
            name="translation_table_used",
        ),
        migrations.RemoveField(
            model_name="bactscout",
            name="coding_density",
        ),
        migrations.RemoveField(
            model_name="bactscout",
            name="contig_n50",
        ),
        migrations.RemoveField(
            model_name="bactscout",
            name="average_gene_length",
        ),
        migrations.RemoveField(
            model_name="bactscout",
            name="genome_size",
        ),
        migrations.RemoveField(
            model_name="bactscout",
            name="checkm2_gc_content",
        ),
        migrations.RemoveField(
            model_name="bactscout",
            name="total_coding_sequences",
        ),
        migrations.RemoveField(
            model_name="bactscout",
            name="total_contigs",
        ),
        migrations.RemoveField(
            model_name="bactscout",
            name="max_contig_length",
        ),
        migrations.RemoveField(
            model_name="bactscout",
            name="additional_notes",
        ),
        migrations.RemoveField(
            model_name="bactscout",
            name="genome_size_expected_status",
        ),
    ]
