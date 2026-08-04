from django.db import migrations, models


OLD_ENCODER = "Encoder"
DMU_ENCODER = "DMU Encoder"
LAB_ENCODER = "LAB Encoder"


def replace_role_token(value, old_role=OLD_ENCODER, new_role=DMU_ENCODER):
    parts = [
        part.strip()
        for part in str(value or "").replace(",", "|").replace(";", "|").split("|")
        if part.strip()
    ]
    updated = [new_role if part == old_role else part for part in parts]
    return "|".join(dict.fromkeys(updated))


def forwards(apps, schema_editor):
    Staff = apps.get_model("home", "arsStaff_Details")
    Group = apps.get_model("auth", "Group")

    for staff in Staff.objects.exclude(Staff_Role=""):
        updated_role = replace_role_token(staff.Staff_Role)
        if updated_role != staff.Staff_Role:
            staff.Staff_Role = updated_role
            staff.save(update_fields=["Staff_Role"])

    old_group = Group.objects.filter(name=OLD_ENCODER).first()
    if old_group:
        old_group.name = DMU_ENCODER
        old_group.save(update_fields=["name"])

    Group.objects.get_or_create(name=LAB_ENCODER)


def backwards(apps, schema_editor):
    Staff = apps.get_model("home", "arsStaff_Details")
    Group = apps.get_model("auth", "Group")

    for staff in Staff.objects.exclude(Staff_Role=""):
        updated_role = replace_role_token(staff.Staff_Role, DMU_ENCODER, OLD_ENCODER)
        if updated_role != staff.Staff_Role:
            staff.Staff_Role = updated_role
            staff.save(update_fields=["Staff_Role"])

    dmu_group = Group.objects.filter(name=DMU_ENCODER).first()
    if dmu_group and not Group.objects.filter(name=OLD_ENCODER).exists():
        dmu_group.name = OLD_ENCODER
        dmu_group.save(update_fields=["name"])


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("home", "0034_sitedata_credentials"),
    ]

    operations = [
        migrations.AlterField(
            model_name="arsstaff_details",
            name="Staff_Role",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", ""),
                    (DMU_ENCODER, DMU_ENCODER),
                    (LAB_ENCODER, LAB_ENCODER),
                    ("Verifier", "Verifier"),
                    ("Checker", "Checker"),
                    ("Lab Manager", "Lab Manager"),
                    ("Admin", "Admin"),
                ],
                default="",
                max_length=150,
            ),
        ),
        migrations.RunPython(forwards, backwards),
    ]
