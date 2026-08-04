from django.db import migrations, models


CATEGORY_CHOICES = [
    ("quality_control", "Quality control"),
    ("genome_assembly", "Genome assembly"),
    ("species_identification", "Species identification"),
    ("serotyping", "Serotyping"),
    ("phylogrouping", "Phylogrouping"),
    ("sequence_typing", "Sequence typing"),
    ("amr_detection", "Antimicrobial resistance detection"),
    ("virulence_detection", "Virulence detection"),
    ("genome_annotation", "Genome annotation"),
    ("variant_calling", "Variant calling"),
    ("phylogenetics", "Phylogenetic analysis"),
    ("other", "Other"),
]


def normalize_category(value):
    text = str(value or "").strip()
    if not text:
        return ""

    key_lookup = {key.lower(): key for key, label in CATEGORY_CHOICES}
    label_lookup = {label.lower(): key for key, label in CATEGORY_CHOICES}
    normalized = text.lower().replace("-", "_").replace(" ", "_")

    if normalized in key_lookup:
        return key_lookup[normalized]
    if text.lower() in label_lookup:
        return label_lookup[text.lower()]
    return "other"


def copy_category_to_list(apps, schema_editor):
    pipeline_model = apps.get_model("wgs_app", "CustomWGSPipeline")
    for pipeline in pipeline_model.objects.all():
        category = normalize_category(getattr(pipeline, "category", ""))
        pipeline.category_values = [category] if category else []
        pipeline.save(update_fields=["category_values"])


def copy_list_to_category(apps, schema_editor):
    pipeline_model = apps.get_model("wgs_app", "CustomWGSPipeline")
    for pipeline in pipeline_model.objects.all():
        values = getattr(pipeline, "category_values", None) or []
        pipeline.category = values[0] if values else ""
        pipeline.save(update_fields=["category"])


class Migration(migrations.Migration):

    dependencies = [
        ("wgs_app", "0015_builtin_wgs_pipeline_setting"),
    ]

    operations = [
        migrations.AddField(
            model_name="customwgspipeline",
            name="category_values",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.RunPython(copy_category_to_list, copy_list_to_category),
        migrations.RemoveField(
            model_name="customwgspipeline",
            name="category",
        ),
        migrations.RenameField(
            model_name="customwgspipeline",
            old_name="category_values",
            new_name="category",
        ),
    ]
