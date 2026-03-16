from django.db import transaction
from apps.home.models import Batch_Table
from apps.home_final.models import (
    Final_Data,
    Final_AntibioticEntry,
    ConcordanceReport,
    ConcordanceDetail
)


# ==============================
# ID CONCORDANCE CLASSIFICATION
# ==============================
def classify_id_concordance(site_org, ars_pre, ars_org):

    site = (site_org or "").strip().lower()
    ars = (ars_org or "").strip().lower()
    pre = (ars_pre or "").strip().lower()

    # Mixed Culture rule
    if "mixed culture" in pre:
        return "M", "M"

    # Not Viable rule
    if ars == "not viable":
        return "N", "N"

    # Full concordance
    if site and ars and site == ars:
        return "G", "S"

    # Discordant
    return "X", "X"


# ==============================
# AST DEVIATION CLASSIFICATION
# ==============================
def classify_ast_deviation(site_ris, ars_ris):

    if not site_ris or not ars_ris:
        return None, False

    s = site_ris.strip().upper()
    a = ars_ris.strip().upper()

    # Normalize special values
    if s == "SDD":
        s = "S"
    if a == "SDD":
        a = "S"

    if s == "NS":
        s = "R"
    if a == "NS":
        a = "R"

    if s in ["ND", "NA"] or a in ["ND", "NA"]:
        return None, False

    if s == a:
        return "S", False

    if s == "S" and a == "R":
        return "A", True  # Very Major

    if s == "R" and a == "S":
        return "B", True  # Major

    if "I" in {s, a}:
        return "C", True  # Minor

    return None, False


# ==============================
# MAIN GENERATOR
# ==============================
@transaction.atomic
def generate_concordance_for_batch(batch_id, user):

    batch = Batch_Table.objects.get(id=batch_id)

    # Delete old report + details for this batch
    ConcordanceDetail.objects.filter(report__batch=batch).delete()
    ConcordanceReport.objects.filter(batch=batch).delete()

    # Create fresh batch-level report
    report = ConcordanceReport.objects.create(
        batch=batch,
        created_by=user
    )

    total_pairs = 0
    concordant_pairs = 0
    vmd = 0
    md = 0
    minor = 0

    isolates = Final_Data.objects.filter(f_Batch_id=batch)

    report.total_isolates = isolates.count()

    for isolate in isolates:

        # ---------- ID CONCORDANCE ----------
        genus_con, species_con = classify_id_concordance(
            isolate.f_Site_Org,
            isolate.f_ars_Pre,
            isolate.f_ars_OrgName
        )

        # ---------- AST LOOP ----------
        ab_entries = Final_AntibioticEntry.objects.filter(
            ab_idNum_f_referred=isolate
        )

        for entry in ab_entries:

            # Determine which RIS to use
            site_ris = entry.ab_Disk_enRIS or entry.ab_MIC_enRIS
            ars_ris = entry.ab_Retest_Disk_enRIS or entry.ab_Retest_MIC_enRIS

            code, is_disc = classify_ast_deviation(site_ris, ars_ris)

            if not code:
                continue

            total_pairs += 1

            if code == "S":
                concordant_pairs += 1
            elif code == "A":
                vmd += 1
            elif code == "B":
                md += 1
            elif code == "C":
                minor += 1

            ConcordanceDetail.objects.create(
                report=report,
                accession_no=isolate.f_AccessionNo,
                isolate_id=isolate.id,
                organism=isolate.f_Site_Org,
                antibiotic=entry.ab_Antibiotic,
                site_ris=site_ris,
                ars_ris=ars_ris,
                deviation_code=code,
                is_discordant=is_disc,
                genus_con=genus_con,
                species_con=species_con
            )

    # ---------- FINAL SUMMARY ----------
    report.total_pairs = total_pairs
    report.concordant_pairs = concordant_pairs
    report.vmd = vmd
    report.md = md
    report.minor = minor

    total_deviation = vmd + md + minor
    critical_deviation = vmd + md

    report.total_deviation = total_deviation
    report.critical_deviation = critical_deviation

    if total_pairs > 0:
        report.ast_concordance_rate = round(
            (concordant_pairs / total_pairs) * 100, 2
        )
        report.critical_deviation_rate = round(
            (critical_deviation / total_pairs) * 100, 2
        )
        report.total_deviation_rate = round(
            (total_deviation / total_pairs) * 100, 2
        )

    report.save()

    return report