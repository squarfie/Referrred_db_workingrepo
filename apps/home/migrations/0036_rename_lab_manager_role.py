from django.db import migrations, models


OLD_ROLE = "Lab Manager"
NEW_ROLE = "Manager"


def replace_role_token(value, old_role=OLD_ROLE, new_role=NEW_ROLE):
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

    old_group = Group.objects.filter(name=OLD_ROLE).first()
    if old_group:
        old_group.name = NEW_ROLE
        old_group.save(update_fields=["name"])


def backwards(apps, schema_editor):
    Staff = apps.get_model("home", "arsStaff_Details")
    Group = apps.get_model("auth", "Group")

    for staff in Staff.objects.exclude(Staff_Role=""):
        updated_role = replace_role_token(staff.Staff_Role, NEW_ROLE, OLD_ROLE)
        if updated_role != staff.Staff_Role:
            staff.Staff_Role = updated_role
            staff.save(update_fields=["Staff_Role"])

    manager_group = Group.objects.filter(name=NEW_ROLE).first()
    if manager_group and not Group.objects.filter(name=OLD_ROLE).exists():
        manager_group.name = OLD_ROLE
        manager_group.save(update_fields=["name"])


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("home", "0035_rename_encoder_role_add_lab_encoder"),
    ]

    operations = [
        migrations.AlterField(
            model_name="arsstaff_details",
            name="Staff_Role",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", ""),
                    ("DMU Encoder", "DMU Encoder"),
                    ("LAB Encoder", "LAB Encoder"),
                    ("Verifier", "Verifier"),
                    ("Checker", "Checker"),
                    (NEW_ROLE, NEW_ROLE),
                    ("Admin", "Admin"),
                ],
                default="",
                max_length=150,
            ),
        ),
        migrations.RunPython(forwards, backwards),
    ]
