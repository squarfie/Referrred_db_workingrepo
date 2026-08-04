import re

from django.db import migrations


def accession_ref_sequence(accession):
    match = re.search(r"(\d+)(?!.*\d)", str(accession or "").strip())
    if not match:
        return None
    return int(match.group(1))


def backfill_bat_seq(apps, schema_editor):
    ReferredData = apps.get_model("home", "Referred_Data")
    rows = list(
        ReferredData.objects
        .exclude(AccessionNo__isnull=True)
        .exclude(AccessionNo="")
        .values("id", "Batch_id_id", "AccessionNo", "bat_seq")
    )

    targets = {}
    for row in rows:
        target = accession_ref_sequence(row["AccessionNo"])
        if target is not None:
            targets[row["id"]] = (row["Batch_id_id"], target)

    for row in rows:
        target_data = targets.get(row["id"])
        if target_data and row["bat_seq"] != target_data[1]:
            ReferredData.objects.filter(pk=row["id"]).update(bat_seq=None)

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
        ReferredData.objects.filter(pk=row["id"]).update(bat_seq=target)


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0024_referred_data_editable_phenotypes"),
    ]

    operations = [
        migrations.RunPython(backfill_bat_seq, migrations.RunPython.noop),
    ]
