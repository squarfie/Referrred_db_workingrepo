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


def backfill_age_display(apps, schema_editor):
    ReferredData = apps.get_model("home", "Referred_Data")
    records = []
    for record in ReferredData.objects.all().only(
        "pk",
        "Date_Birth",
        "Spec_Date",
        "Age",
        "Age_Display",
    ):
        display = format_display(record.Date_Birth, record.Spec_Date, record.Age)
        if record.Age_Display != display:
            record.Age_Display = display
            records.append(record)

    if records:
        ReferredData.objects.bulk_update(records, ["Age_Display"])


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0021_referred_data_age_display"),
    ]

    operations = [
        migrations.RunPython(backfill_age_display, migrations.RunPython.noop),
    ]
