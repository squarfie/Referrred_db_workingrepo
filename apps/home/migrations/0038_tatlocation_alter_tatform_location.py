from django.db import migrations, models


DEFAULT_TAT_LOCATIONS = [
    ("Medical Specialist II", 1),
    ("LAB", 2),
    ("DMU", 3),
    ("Executive Secretary", 4),
    ("Medical Specialist IV", 5),
    ("Laboratory Manager", 6),
    ("n/a", 99),
]


def seed_tat_locations(apps, schema_editor):
    TATLocation = apps.get_model("home", "TATLocation")
    for name, order in DEFAULT_TAT_LOCATIONS:
        TATLocation.objects.update_or_create(
            name=name,
            defaults={
                "order": order,
                "is_active": True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0037_staff_signature_defaults"),
    ]

    operations = [
        migrations.CreateModel(
            name="TATLocation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "db_table": "TATLocation",
                "ordering": ["order", "name"],
            },
        ),
        migrations.AlterField(
            model_name="tatform",
            name="tat_Batch_Location",
            field=models.CharField(default="n/a", max_length=100),
        ),
        migrations.RunPython(seed_tat_locations, migrations.RunPython.noop),
    ]
