from datetime import timedelta

from django.db import migrations


def format_display(birth_date, specimen_date, age):
    if age in ("", " ", None):
        return ""
    if not birth_date or not specimen_date or specimen_date < birth_date:
        return str(age)

    years = specimen_date.year - birth_date.year
    months = specimen_date.month - birth_date.month
    days = specimen_date.day - birth_date.day

    if days < 0:
        days += (specimen_date.replace(day=1) - timedelta(days=1)).day
        months -= 1

    if months < 0:
        months += 12
        years -= 1

    if years > 0:
        return str(age)

    parts = []
    if months > 0:
        parts.append(f"{months}m")
    if days > 0 or not parts:
        parts.append(f"{days}d")
    return "".join(parts)


def backfill_f_age_display(apps, schema_editor):
    FinalData = apps.get_model("home_final", "Final_Data")
    records = []
    for record in FinalData.objects.all().only(
        "pk",
        "f_Date_Birth",
        "f_Spec_Date",
        "f_Age",
        "f_Age_Display",
    ):
        display = format_display(record.f_Date_Birth, record.f_Spec_Date, record.f_Age)
        if record.f_Age_Display != display:
            record.f_Age_Display = display
            records.append(record)

    if records:
        FinalData.objects.bulk_update(records, ["f_Age_Display"])


class Migration(migrations.Migration):

    dependencies = [
        ("home_final", "0014_final_data_f_age_display"),
    ]

    operations = [
        migrations.RunPython(backfill_f_age_display, migrations.RunPython.noop),
    ]
