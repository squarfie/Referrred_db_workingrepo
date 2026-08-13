from django.db import migrations, models


def set_initial_signature_defaults(apps, schema_editor):
    Staff = apps.get_model("home", "arsStaff_Details")

    lab_manager = (
        Staff.objects
        .filter(Staff_Name__icontains="Olorosa")
        .order_by("Staff_Name")
        .first()
    )
    if lab_manager:
        Staff.objects.exclude(pk=lab_manager.pk).update(Is_Default_Lab_Manager=False)
        lab_manager.Is_Default_Lab_Manager = True
        lab_manager.save(update_fields=["Is_Default_Lab_Manager"])

    head = (
        Staff.objects
        .filter(Staff_Name__icontains="Sonia")
        .filter(Staff_Name__icontains="Sia")
        .order_by("Staff_Name")
        .first()
    )
    if head:
        Staff.objects.exclude(pk=head.pk).update(Is_Default_Head=False)
        head.Is_Default_Head = True
        head.save(update_fields=["Is_Default_Head"])


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0036_rename_lab_manager_role"),
    ]

    operations = [
        migrations.AddField(
            model_name="arsstaff_details",
            name="Is_Default_Lab_Manager",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="arsstaff_details",
            name="Is_Default_Head",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(set_initial_signature_defaults, migrations.RunPython.noop),
    ]
