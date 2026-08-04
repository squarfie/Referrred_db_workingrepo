import re

from django.db import migrations


def accession_ref_sequence(accession):
    match = re.search(r"(\d+)(?!.*\d)", str(accession or "").strip())
    if not match:
        return None
    return int(match.group(1))


def backfill_f_bat_seq(apps, schema_editor):
    FinalData = apps.get_model("home_final", "Final_Data")
    rows = list(
        FinalData.objects
        .exclude(f_AccessionNo__isnull=True)
        .exclude(f_AccessionNo="")
        .values("id", "f_Batch_id_id", "f_AccessionNo", "f_bat_seq")
    )

    targets = {}
    for row in rows:
        target = accession_ref_sequence(row["f_AccessionNo"])
        if target is not None:
            targets[row["id"]] = (row["f_Batch_id_id"], target)

    for row in rows:
        target_data = targets.get(row["id"])
        if target_data and row["f_bat_seq"] != target_data[1]:
            FinalData.objects.filter(pk=row["id"]).update(f_bat_seq=None)

    used = set()
    for row in rows:
        target_data = targets.get(row["id"])
        if not target_data:
            continue
        batch_id, target = target_data
        key = (batch_id, target)
        if key in used:
            continue
        used.add(key)
        FinalData.objects.filter(pk=row["id"]).update(f_bat_seq=target)


class Migration(migrations.Migration):

    dependencies = [
        ("home_final", "0016_final_data_editable_phenotypes"),
    ]

    operations = [
        migrations.RunPython(backfill_f_bat_seq, migrations.RunPython.noop),
    ]
