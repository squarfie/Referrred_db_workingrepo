import re
import re
from collections import defaultdict

from django.db import transaction

from apps.home.models import Batch_Table
from apps.home_final.models import (
    ConcordanceDetail,
    ConcordanceReport,
    Final_AntibioticEntry,
    Final_Data,
)


MIXED_INDICATORS = ("mixed", "culture", "multiple", "various")
NONVIABLE_INDICATORS = ("not viable", "nonviable", "no growth")


def clean_str(value):
    if value is None:
        return ""
    return str(value).strip()


def normalize_result(value):
    result = clean_str(value).upper()
    if result in {"", "NA", "N/A", "NONE", "NULL", "ND"}:
        return None
    if result == "SDD":
        return "S"
    if result == "NS":
        return "R"
    return result


def normalize_ast_pair_code(value):
    """Group AST comparison keys by antibiotic and method, not disk potency."""
    code = clean_str(value).upper().replace(".", "_")
    if not code:
        return ""

    disk_match = re.match(r"^([A-Z0-9]+)_ND", code)
    if disk_match:
        return f"{disk_match.group(1)}_ND"

    mic_match = re.match(r"^([A-Z0-9]+)_NM", code)
    if mic_match:
        return f"{mic_match.group(1)}_NM"

    return code


def _contains_any(text, indicators):
    text = clean_str(text).lower()
    return any(indicator in text for indicator in indicators)


def _genus_name(organism_name):
    organism_name = clean_str(organism_name)
    return organism_name.split()[0].lower() if organism_name else ""


def _species_name(organism_name):
    organism_name = clean_str(organism_name)
    parts = organism_name.split()
    return " ".join(parts[1:]).lower() if len(parts) > 1 else ""


def classify_id_concordance(site_org, ars_pre, ars_org, ars_post=""):
    site = clean_str(site_org).lower()
    ars = clean_str(ars_org).lower()
    pre = clean_str(ars_pre).lower()
    post = clean_str(ars_post).lower()

    if _contains_any(" ".join([site, ars, pre, post]), MIXED_INDICATORS):
        return "M", "M"

    # "No ... recovered or isolated" is a discordant identification, not a non-viable isolate.
    if "no" in pre and ("recovered" in (pre + " " + post) or "isolated" in (pre + " " + post)):
        return "X", "X"

    if _contains_any(" ".join([ars, pre, post]), NONVIABLE_INDICATORS):
        return "N", "N"

    if not site or not ars:
        return None, None

    if site == ars:
        return "G", "S"

    site_genus = _genus_name(site)
    ars_genus = _genus_name(ars)
    site_species = _species_name(site)
    ars_species = _species_name(ars)

    genus_con = "G" if site_genus and ars_genus and site_genus == ars_genus else "X"

    if genus_con != "G":
        return "X", "X"

    if site_species and ars_species and (
        site_species == ars_species
        or site_species in ars_species
        or ars_species in site_species
    ):
        return "G", "S"

    return "G", "X"


def classify_ast_deviation(site_ris, ars_ris):
    site = normalize_result(site_ris)
    ars = normalize_result(ars_ris)

    if not site or not ars:
        return None, False

    if site == ars:
        return "S", False

    if site == "S" and ars == "R":
        return "A", True

    if site == "R" and ars == "S":
        return "B", True

    if "I" in {site, ars}:
        return "C", True

    return None, False


def get_site_ris(entry, antibiotic_code=""):
    pair_code = normalize_ast_pair_code(antibiotic_code)
    if pair_code.endswith("_ND"):
        return normalize_result(entry.ab_Disk_enRIS)
    if pair_code.endswith("_NM"):
        return normalize_result(entry.ab_MIC_enRIS)
    return normalize_result(entry.ab_Disk_enRIS) or normalize_result(entry.ab_MIC_enRIS)


def get_ars_ris(entry, antibiotic_code=""):
    pair_code = normalize_ast_pair_code(antibiotic_code)
    if pair_code.endswith("_ND"):
        return normalize_result(entry.ab_Retest_Disk_enRIS)
    if pair_code.endswith("_NM"):
        return normalize_result(entry.ab_Retest_MIC_enRIS)
    return normalize_result(entry.ab_Retest_Disk_enRIS) or normalize_result(entry.ab_Retest_MIC_enRIS)


def get_site_antibiotic_code(entry):
    return clean_str(entry.ab_Abx_code).upper()


def get_ars_antibiotic_code(entry):
    return clean_str(entry.ab_Retest_Abx_code).upper()


def build_ast_result_maps(isolate):
    site_results = {}
    ars_results = {}
    antibiotic_names = {}

    for entry in isolate.final_entries.all():
        site_code = get_site_antibiotic_code(entry)
        ars_code = get_ars_antibiotic_code(entry)
        site_pair_code = normalize_ast_pair_code(site_code)
        ars_pair_code = normalize_ast_pair_code(ars_code)

        site_ris = get_site_ris(entry, site_code)
        ars_ris = get_ars_ris(entry, ars_code)

        if site_pair_code and site_ris and site_pair_code not in site_results:
            site_results[site_pair_code] = site_ris
            antibiotic_names[site_pair_code] = entry.ab_Antibiotic or site_code

        if ars_pair_code and ars_ris and ars_pair_code not in ars_results:
            ars_results[ars_pair_code] = ars_ris
            antibiotic_names.setdefault(
                ars_pair_code,
                entry.ab_Retest_Antibiotic or ars_code,
            )

    return site_results, ars_results, antibiotic_names


def calculate_isolate_concordance(isolate):
    genus_con, species_con = classify_id_concordance(
        isolate.f_Site_OrgName,
        isolate.f_ars_Pre,
        isolate.f_ars_OrgName,
        isolate.f_ars_Post,
    )

    site_results, ars_results, antibiotic_names = build_ast_result_maps(isolate)

    total_pairs = 0
    concordant_pairs = 0
    vmd = 0
    md = 0
    minor = 0
    details = []

    for antibiotic_code in sorted(set(site_results) & set(ars_results)):
        site_ris = site_results[antibiotic_code]
        ars_ris = ars_results[antibiotic_code]

        code, is_discordant = classify_ast_deviation(site_ris, ars_ris)
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

        details.append(
            ConcordanceDetail(
                accession_no=isolate.f_AccessionNo,
                isolate_id=isolate.id,
                organism=isolate.f_Site_OrgName or "",
                antibiotic=antibiotic_names.get(antibiotic_code, antibiotic_code),
                site_ris=site_ris,
                ars_ris=ars_ris,
                deviation_code=code,
                is_discordant=is_discordant,
                genus_con=genus_con,
                species_con=species_con,
            )
        )

    total_deviation = vmd + md + minor
    critical_deviation = vmd + md

    return {
        "genus_con": genus_con,
        "species_con": species_con,
        "genus_match": 1 if genus_con == "G" else 0,
        "species_match": 1 if species_con == "S" else 0,
        "mixed": 1 if genus_con == "M" else 0,
        "nonviable": 1 if genus_con == "N" else 0,
        "different_org": 1 if genus_con == "X" else 0,
        "total_pairs": total_pairs,
        "concordant_pairs": concordant_pairs,
        "vmd": vmd,
        "md": md,
        "minor": minor,
        "total_deviation": total_deviation,
        "critical_deviation": critical_deviation,
        "ast_concordance_rate": pct(concordant_pairs, total_pairs),
        "critical_deviation_rate": pct(critical_deviation, total_pairs),
        "total_deviation_rate": pct(total_deviation, total_pairs),
        "details": details,
    }


def pct(numerator, denominator):
    return round((numerator / denominator) * 100, 2) if denominator else 0


def build_id_stats(isolates):
    stats = {
        "total_isolates": 0,
        "genus_match": 0,
        "species_match": 0,
        "different_org": 0,
        "mixed_count": 0,
        "nonviable_count": 0,
        "discordant_rows": [],
    }

    for isolate in isolates:
        stats["total_isolates"] += 1
        result = calculate_isolate_concordance(isolate)

        stats["genus_match"] += result["genus_match"]
        stats["species_match"] += result["species_match"]
        stats["mixed_count"] += result["mixed"]
        stats["nonviable_count"] += result["nonviable"]
        stats["different_org"] += result["different_org"]

        if result["different_org"]:
            ars_identification = (
                isolate.f_ars_OrgName
                if _contains_any(
                    " ".join([
                        clean_str(isolate.f_ars_OrgName),
                        clean_str(isolate.f_ars_Pre),
                        clean_str(isolate.f_ars_Post),
                    ]),
                    NONVIABLE_INDICATORS,
                )
                else isolate.f_ars_Pre
            )
            stats["discordant_rows"].append({
                "refno": isolate.f_RefNo,
                "bat_seq": isolate.f_bat_seq if isolate.f_bat_seq is not None else "",
                "site_org": isolate.f_Site_OrgName,
                "ars_org": ars_identification,
            })

    viable_pure = (
        stats["total_isolates"]
        - stats["mixed_count"]
        - stats["nonviable_count"]
    )
    stats["viable_pure"] = max(viable_pure, 0)
    stats["genus_rate"] = pct(stats["genus_match"], stats["viable_pure"])
    stats["species_rate"] = pct(stats["species_match"], stats["viable_pure"])

    return stats


def _report_defaults_from_totals(totals, user=None):
    total_pairs = totals["total_pairs"]
    total_deviation = totals["vmd"] + totals["md"] + totals["minor"]
    critical_deviation = totals["vmd"] + totals["md"]

    return {
        "created_by": user,
        "total_isolates": totals["total_isolates"],
        "total_pairs": total_pairs,
        "concordant_pairs": totals["concordant_pairs"],
        "vmd": totals["vmd"],
        "md": totals["md"],
        "minor": totals["minor"],
        "total_deviation": total_deviation,
        "critical_deviation": critical_deviation,
        "ast_concordance_rate": pct(totals["concordant_pairs"], total_pairs),
        "critical_deviation_rate": pct(critical_deviation, total_pairs),
        "total_deviation_rate": pct(total_deviation, total_pairs),
        "genus_match": totals["genus_match"],
        "species_match": totals["species_match"],
        "genus_rate": pct(totals["genus_match"], totals["viable_pure"]),
        "species_rate": pct(totals["species_match"], totals["viable_pure"]),
    }


def summarize_isolates(isolates):
    totals = defaultdict(int)
    detail_objects = []

    isolate_list = list(isolates)
    totals["total_isolates"] = len(isolate_list)

    for isolate in isolate_list:
        result = calculate_isolate_concordance(isolate)

        totals["genus_match"] += result["genus_match"]
        totals["species_match"] += result["species_match"]
        totals["mixed_count"] += result["mixed"]
        totals["nonviable_count"] += result["nonviable"]
        totals["different_org"] += result["different_org"]
        totals["total_pairs"] += result["total_pairs"]
        totals["concordant_pairs"] += result["concordant_pairs"]
        totals["vmd"] += result["vmd"]
        totals["md"] += result["md"]
        totals["minor"] += result["minor"]
        detail_objects.extend(result["details"])

    totals["viable_pure"] = max(
        totals["total_isolates"] - totals["mixed_count"] - totals["nonviable_count"],
        0,
    )

    return totals, detail_objects


@transaction.atomic
def generate_concordance_for_batch(batch_id, user=None):
    batch = Batch_Table.objects.get(id=batch_id)
    isolates = (
        Final_Data.objects
        .filter(f_Batch_id=batch)
        .prefetch_related("final_entries")
    )
    totals, detail_objects = summarize_isolates(isolates)
    defaults = _report_defaults_from_totals(totals, user)

    report, _ = ConcordanceReport.objects.update_or_create(
        batch=batch,
        final_data=None,
        defaults=defaults,
    )

    report.details.all().delete()
    for obj in detail_objects:
        obj.report = report
    ConcordanceDetail.objects.bulk_create(detail_objects)

    return report


@transaction.atomic
def generate_concordance_for_isolate(isolate, user=None):
    isolate = (
        Final_Data.objects
        .filter(pk=isolate.pk)
        .prefetch_related("final_entries")
        .first()
    )
    if not isolate:
        return None

    result = calculate_isolate_concordance(isolate)
    totals = defaultdict(int)
    totals.update({
        "total_isolates": 1,
        "genus_match": result["genus_match"],
        "species_match": result["species_match"],
        "mixed_count": result["mixed"],
        "nonviable_count": result["nonviable"],
        "total_pairs": result["total_pairs"],
        "concordant_pairs": result["concordant_pairs"],
        "vmd": result["vmd"],
        "md": result["md"],
        "minor": result["minor"],
    })
    totals["viable_pure"] = max(1 - result["mixed"] - result["nonviable"], 0)

    defaults = _report_defaults_from_totals(totals, user)
    defaults["batch"] = isolate.f_Batch_id

    report, _ = ConcordanceReport.objects.update_or_create(
        final_data=isolate,
        defaults=defaults,
    )

    report.details.all().delete()
    for obj in result["details"]:
        obj.report = report
    ConcordanceDetail.objects.bulk_create(result["details"])

    return report


def collect_concordance_dashboard(year=None):
    isolates = Final_Data.objects.prefetch_related("final_entries")
    if year not in (None, "", "all"):
        isolates = isolates.filter(f_Referral_Date__year=year)
    totals, _ = summarize_isolates(isolates)

    return {
        "total_isolates": totals["total_isolates"],
        "concordant_species": totals["species_match"],
        "species_rate": pct(totals["species_match"], totals["viable_pure"]),
        "concordant_genus": totals["genus_match"],
        "genus_rate": pct(totals["genus_match"], totals["viable_pure"]),
        "different_org": totals["different_org"],
        "mixed_count": totals["mixed_count"],
        "not_viable_count": totals["nonviable_count"],
        "total_pairs": totals["total_pairs"],
        "concordant_pairs": totals["concordant_pairs"],
        "ast_concordance_rate": pct(totals["concordant_pairs"], totals["total_pairs"]),
        "vmd": totals["vmd"],
        "vmd_rate": pct(totals["vmd"], totals["total_pairs"]),
        "md": totals["md"],
        "md_rate": pct(totals["md"], totals["total_pairs"]),
        "minor": totals["minor"],
        "minor_rate": pct(totals["minor"], totals["total_pairs"]),
        "isolates": isolates,
    }


def calculate_antibiotic_summary(details):
    summary = defaultdict(lambda: {"total": 0, "vmd": 0, "md": 0, "minor": 0})

    for detail in details:
        code = (detail.deviation_code or "").upper()
        if code not in {"A", "B", "C"}:
            continue

        summary[detail.antibiotic]["total"] += 1
        if code == "A":
            summary[detail.antibiotic]["vmd"] += 1
        elif code == "B":
            summary[detail.antibiotic]["md"] += 1
        elif code == "C":
            summary[detail.antibiotic]["minor"] += 1

    return dict(summary)
