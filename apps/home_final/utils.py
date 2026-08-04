import re

from django.db import models
from django.db.models import Q, Case, When
from django.apps import apps


class _LazyHomeModel:
    def __init__(self, model_name):
        self.model_name = model_name

    def _model(self):
        return apps.get_model("home", self.model_name)

    def __getattr__(self, attr):
        return getattr(self._model(), attr)


Antibiotic_List = _LazyHomeModel("Antibiotic_List")
BreakpointsTable = _LazyHomeModel("BreakpointsTable")
Organism_List = _LazyHomeModel("Organism_List")


# ============================================================
# Antibiotic filtering based on breakpoint availability
# ============================================================
def get_filtered_antibiotics(breakpoint_year, resolved_org, *, retest=False):
    """
    Returns Antibiotic_List filtered by breakpoint availability.
    Uses the nearest breakpoint year available for the selected organism.
    Falls back to all visible antibiotics if the organism has no breakpoints.
    """
    AntibioticList = apps.get_model("home", "Antibiotic_List")
    Breakpoints = apps.get_model("home", "BreakpointsTable")

    qs = AntibioticList.objects.all()

    if retest:
        qs = qs.filter(Retest=True)
    else:
        qs = qs.filter(Show=True)

    if not breakpoint_year:
        return qs.order_by("Antibiotic")

    bp_qs = Breakpoints.objects.filter(
        Q(Spec_code__isnull=True) |
        Q(Spec_code="")
    )
    if resolved_org:
        resolved_org = resolved_org.strip()
        bp_qs = bp_qs.filter(
            Q(Org__iexact=resolved_org) |
            Q(Org__isnull=True) |
            Q(Org="")
        )

    if not bp_qs.exists():
        return qs.order_by("Antibiotic")

    target_year = _year_as_int(breakpoint_year)
    years = []
    for year in bp_qs.values_list("Year", flat=True).distinct():
        year_int = _year_as_int(year)
        if year_int is not None:
            years.append(year_int)

    if not years:
        return qs.order_by("Antibiotic")

    if target_year is None:
        selected_year = max(years)
        bp_qs = bp_qs.filter(Year=str(selected_year))
    else:
        previous_or_current_years = [year for year in years if year <= target_year]
        if previous_or_current_years:
            bp_qs = bp_qs.filter(Year__in=[str(year) for year in previous_or_current_years])
        else:
            bp_qs = bp_qs.filter(Year=str(min(years)))

    latest_year_by_code = {}
    for code, year in bp_qs.values_list("Whonet_Abx", "Year"):
        code = (code or "").strip().upper()
        year_int = _year_as_int(year)
        if not code or year_int is None:
            continue
        if code not in latest_year_by_code or year_int > latest_year_by_code[code]:
            latest_year_by_code[code] = year_int

    whonet_codes = list(latest_year_by_code.keys())

    return (
        qs
        .filter(Whonet_Abx__in=whonet_codes)
        .order_by("Antibiotic")
    )


def _year_as_int(value):
    if hasattr(value, "year"):
        return value.year

    text = str(value or "").strip()
    if not text:
        return None

    try:
        return int(text)
    except (TypeError, ValueError):
        pass

    try:
        return int(float(text))
    except (TypeError, ValueError):
        pass

    match = re.search(r"\b(19|20)\d{2}\b", text)
    if match:
        return int(match.group(0))

    return None


# def get_breakpoint_panel_abx_codes(breakpoint_year, resolved_org):
#     """
#     Return distinct printable panel antibiotic codes from breakpoints.

#     Breakpoint uploads can contain a partial current-year panel plus older
#     panel rows.  For printing, choose the newest valid breakpoint for each
#     WHONET antibiotic code up to the isolate/specimen year, then collapse to
#     the short panel code used as the PDF column header.
#     """
#     bp_qs = BreakpointsTable.objects.filter(
#         Q(Spec_code__isnull=True) |
#         Q(Spec_code="")
#     )

#     resolved_org = (resolved_org or "").strip()
#     if resolved_org:
#         bp_qs = bp_qs.filter(
#             Q(Org__iexact=resolved_org) |
#             Q(Org__isnull=True) |
#             Q(Org="")
#         )
#     else:
#         bp_qs = bp_qs.filter(
#             Q(Org__isnull=True) |
#             Q(Org="")
#         )

#     target_year = _year_as_int(breakpoint_year)
#     best_by_whonet = {}

#     for bp in bp_qs:
#         whonet_code = (bp.Whonet_Abx or "").strip().upper()
#         panel_code = (bp.Abx_code or "").strip()
#         bp_year = _year_as_int(bp.Year)

#         if not whonet_code or not panel_code or bp_year is None:
#             continue

#         if target_year is not None and bp_year > target_year:
#             continue

#         org_rank = 0 if resolved_org and (bp.Org or "").strip().lower() == resolved_org.lower() else 1
#         candidate_rank = (bp_year, -org_rank)
#         existing = best_by_whonet.get(whonet_code)

#         if existing is None or candidate_rank > existing["rank"]:
#             best_by_whonet[whonet_code] = {
#                 "rank": candidate_rank,
#                 "panel_code": panel_code,
#             }

#     if not best_by_whonet and target_year is not None:
#         # If all available breakpoints are newer than the specimen year, use
#         # the earliest available future year as a safe fallback.
#         future_years = [
#             _year_as_int(year)
#             for year in bp_qs.values_list("Year", flat=True).distinct()
#             if _year_as_int(year) is not None and _year_as_int(year) > target_year
#         ]
#         if future_years:
#             return get_breakpoint_panel_abx_codes(str(min(future_years)), resolved_org)

#     return {
#         item["panel_code"]
#         for item in best_by_whonet.values()
#         if item["panel_code"]
#     }





# fixed panel handling: do not filter by Spec_code, because the panel is organism-based, not specimen-based.  Show_Site and Show_Ars are still respected later in the PDF function through antibiotic_print_order(show_site=True/show_ars=True).

PANEL_ORG_KEY_FIELDS = (
    "Family_Code",
    "Genus_Group",
    "Genus_Code",
    "Species_Group",
    "Whonet_Org_Code",
)


def _normalize_panel_key(value):
    return str(value or "").strip()


def _organism_panel_keys(resolved_org):
    resolved_org = _normalize_panel_key(resolved_org)
    if not resolved_org:
        return []

    OrganismList = apps.get_model("home", "Organism_List")
    organism = (
        OrganismList.objects
        .filter(Q(Whonet_Org_Code__iexact=resolved_org) | Q(Replaced_by__iexact=resolved_org))
        .values(*PANEL_ORG_KEY_FIELDS)
        .first()
    )

    keys = []
    if organism:
        for field in PANEL_ORG_KEY_FIELDS:
            key = _normalize_panel_key(organism.get(field))
            if key and key.lower() not in {item.lower() for item in keys}:
                keys.append(key)

    if resolved_org and resolved_org.lower() not in {item.lower() for item in keys}:
        keys.append(resolved_org)

    return keys


def _panel_key_filter(panel_keys):
    query = Q()
    for key in panel_keys:
        query |= Q(Org__iexact=key)
    return query | Q(Org__isnull=True) | Q(Org="")


def get_breakpoint_panel_abx_codes(breakpoint_year, resolved_org):
    """
    Return distinct printable panel antibiotic codes from breakpoints.

    Panel selection is organism-based, not specimen-based.

    Important:
    - Do NOT filter by Spec_code.
    - Spec_code may exist in breakpoint rows, but it should not exclude the
      antibiotic from the printed organism panel.
    - Show_Site and Show_Ars are still respected later in the PDF function
      through antibiotic_print_order(show_site=True/show_ars=True).
    """

    # Do not filter Spec_code here.
    # We want the organism panel regardless of specimen type.
    Breakpoints = apps.get_model("home", "BreakpointsTable")
    bp_qs = Breakpoints.objects.all()

    resolved_org = (resolved_org or "").strip()
    panel_keys = _organism_panel_keys(resolved_org)
    panel_key_lookup = {key.lower(): index + 1 for index, key in enumerate(panel_keys)}

    if panel_keys:
        bp_qs = bp_qs.filter(_panel_key_filter(panel_keys))
    else:
        bp_qs = bp_qs.filter(
            Q(Org__isnull=True) |
            Q(Org="")
        )

    target_year = _year_as_int(breakpoint_year)
    best_by_whonet = {}

    for bp in bp_qs:
        whonet_code = (bp.Whonet_Abx or "").strip().upper()
        panel_code = (bp.Abx_code or "").strip()
        bp_year = _year_as_int(bp.Year)

        if not whonet_code or not panel_code or bp_year is None:
            continue

        # Do not use breakpoint rows newer than the isolate/specimen year.
        if target_year is not None and bp_year > target_year:
            continue

        org_key = (bp.Org or "").strip().lower()
        org_rank = panel_key_lookup.get(org_key, 0)

        candidate_rank = (bp_year, org_rank)
        existing = best_by_whonet.get(whonet_code)

        if existing is None or candidate_rank > existing["rank"]:
            best_by_whonet[whonet_code] = {
                "rank": candidate_rank,
                "panel_code": panel_code,
            }

    if not best_by_whonet and target_year is not None:
        # If all available breakpoints are newer than the specimen year,
        # use the earliest available future year as fallback.
        future_years = []
        for year in bp_qs.values_list("Year", flat=True).distinct():
            year_int = _year_as_int(year)
            if year_int is None:
                continue
            try:
                is_future_year = year_int > target_year
            except TypeError:
                continue
            if is_future_year:
                future_years.append(year_int)

        if future_years:
            return get_breakpoint_panel_abx_codes(str(min(future_years)), resolved_org)

    return {
        item["panel_code"]
        for item in best_by_whonet.values()
        if item["panel_code"]
    }



def antibiotic_print_order(*, show_site=False, show_ars=False):
    """
    Return short ABX codes in Antibiotic-name order.

    PDF tables display the compact Abx_code header (AMC, AMK, etc.), but the
    laboratory-facing order should follow the full Antibiotic name.
    """
    AntibioticList = apps.get_model("home", "Antibiotic_List")

    qs = AntibioticList.objects.exclude(Abx_code__exact="")
    if show_site:
        qs = qs.filter(Show_Site=True)
    if show_ars:
        qs = qs.filter(Show_Ars=True)

    rows = qs.values("Abx_code", "Antibiotic")
    ordered_rows = sorted(
        rows,
        key=lambda row: (
            (row["Antibiotic"] or "").strip().lower(),
            (row["Abx_code"] or "").strip().upper(),
        ),
    )

    ordered_codes = []
    seen = set()
    for row in ordered_rows:
        code = (row["Abx_code"] or "").strip()
        if code and code.upper() not in seen:
            ordered_codes.append(code)
            seen.add(code.upper())

    return ordered_codes


def sort_abx_codes_by_antibiotic(abx_codes):
    """
    Sort any extra/fallback ABX codes by Antibiotic name when known.
    Unknown codes are placed after known codes and sorted by code.
    """
    requested = [(code or "").strip() for code in abx_codes if (code or "").strip()]
    if not requested:
        return []

    requested_upper = {code.upper() for code in requested}
    name_by_code = {}
    AntibioticList = apps.get_model("home", "Antibiotic_List")
    for row in AntibioticList.objects.filter(Abx_code__in=requested).values("Abx_code", "Antibiotic"):
        code = (row["Abx_code"] or "").strip().upper()
        if code and code not in name_by_code:
            name_by_code[code] = (row["Antibiotic"] or "").strip()

    return sorted(
        requested,
        key=lambda code: (
            0 if code.upper() in name_by_code else 1,
            name_by_code.get(code.upper(), "").lower(),
            code.upper(),
        ),
    )


def resolve_breakpoint(abx_code, specimen_year=None, org_code="", test_method=""):
    """
    Finds the best breakpoint for one antibiotic/organism/method.

    Priority:
    1. Exact specimen year
    2. Latest previous year
    3. Earliest later year
    4. Latest year if specimen year is missing

    For the selected year, organism-specific rows beat generic rows.
    """
    abx_code = (abx_code or "").strip().upper()
    org_code = (org_code or "").strip()
    test_method = (test_method or "").strip().upper()

    if not abx_code or not test_method:
        return None

    candidates = list(
        apps.get_model("home", "BreakpointsTable").objects
        .filter(
            Q(Antibiotic_list_id=abx_code) | Q(Whonet_Abx__iexact=abx_code),
            Test_Method__iexact=test_method,
        )
        .filter(
            Q(Org__iexact=org_code) |
            Q(Org__isnull=True) |
            Q(Org="")
        )
    )

    if not candidates:
        return None

    target_year = _year_as_int(specimen_year)
    by_year = {}

    for bp in candidates:
        bp_year = _year_as_int(bp.Year)
        if bp_year is None:
            continue
        by_year.setdefault(bp_year, []).append(bp)

    if not by_year:
        return None

    if target_year is None:
        selected_year = max(by_year)
    elif target_year in by_year:
        selected_year = target_year
    else:
        previous_years = [year for year in by_year if year <= target_year]
        if previous_years:
            selected_year = max(previous_years)
        else:
            selected_year = min(by_year)

    return sorted(
        by_year[selected_year],
        key=lambda bp: (
            0 if (bp.Org or "").strip().lower() == org_code.lower() else 1,
            0 if not (bp.Spec_code or "").strip() else 1,
        ),
    )[0]


def make_cached_breakpoint_resolver():
    cache = {}

    def cached_resolve_breakpoint(
        abx_code,
        specimen_year=None,
        org_code="",
        test_method="",
    ):
        key = (
            (abx_code or "").strip().upper(),
            _year_as_int(specimen_year),
            (org_code or "").strip().lower(),
            (test_method or "").strip().upper(),
        )
        if key not in cache:
            cache[key] = resolve_breakpoint(
                abx_code,
                specimen_year,
                org_code,
                test_method,
            )
        return cache[key]

    return cached_resolve_breakpoint



def resolve_organism_name(org_code):
    """
    Converts 'sau' → 'Staphylococcus aureus'
    """
    if not org_code:
        return None

    OrganismList = apps.get_model("home", "Organism_List")
    return (
        OrganismList.objects
        .filter(Whonet_Org_Code__iexact=org_code)
        .values_list("Organism", flat=True)
        .first()
    )


# ============================================================
# Apply breakpoints to Final_AntibioticEntry
# ============================================================
def apply_final_breakpoints(entry, *, org_code, year, is_retest=False):
    """
    Applies DISK/MIC breakpoints to a Final_AntibioticEntry.
    """

    abx_code = (
        entry.ab_Retest_Abx_code if is_retest
        else entry.ab_Abx_code
    )

    if not abx_code or not year:
        return

    resolved_org = (org_code or "").strip()

    entry.ab_breakpoints_id.clear()
    applied = False

    # ============================
    # DISK
    # ============================
    disk_value = (
        entry.ab_Retest_DiskValue if is_retest
        else entry.ab_Disk_value
    )

    if disk_value is not None:
        bp = resolve_breakpoint(abx_code, year, resolved_org, "DISK")

        if bp:
            entry.ab_breakpoints_id.set([bp])

            if is_retest:
                entry.ab_Ret_Org = bp.Org
                entry.ab_Ret_R_breakpoint = bp.R_val
                entry.ab_Ret_I_breakpoint = bp.I_val
                entry.ab_Ret_SDD_breakpoint = bp.SDD_val
                entry.ab_Ret_S_breakpoint = bp.S_val
            else:
                entry.ab_Site_Org = bp.Org
                entry.ab_R_breakpoint = bp.R_val
                entry.ab_I_breakpoint = bp.I_val
                entry.ab_SDD_breakpoint = bp.SDD_val
                entry.ab_S_breakpoint = bp.S_val

            applied = True

    # ============================
    # MIC (OVERRIDES DISK)
    # ============================
    mic_value = (
        entry.ab_Retest_MICValue if is_retest
        else entry.ab_MIC_value
    )

    if mic_value is not None:
        bp = resolve_breakpoint(abx_code, year, resolved_org, "MIC")

        if bp:
            entry.ab_breakpoints_id.set([bp])

            if is_retest:
                entry.ab_Ret_Org = bp.Org
                entry.ab_Ret_R_breakpoint = bp.R_val
                entry.ab_Ret_I_breakpoint = bp.I_val
                entry.ab_Ret_SDD_breakpoint = bp.SDD_val
                entry.ab_Ret_S_breakpoint = bp.S_val
                entry.ab_Retest_Alert_val = (
                    bp.Alert_val if entry.ab_Retest_AlertMIC else ""
                )
            else:
                entry.ab_Site_Org = bp.Org
                entry.ab_R_breakpoint = bp.R_val
                entry.ab_I_breakpoint = bp.I_val
                entry.ab_SDD_breakpoint = bp.SDD_val
                entry.ab_S_breakpoint = bp.S_val
                entry.ab_Alert_val = (
                    bp.Alert_val if entry.ab_AlertMIC else ""
                )

            applied = True

    # ============================
    # CLEANUP IF NOTHING APPLIED
    # ============================
    if not applied:
        if is_retest:
            entry.ab_Ret_Org = None
            entry.ab_Ret_R_breakpoint = None
            entry.ab_Ret_I_breakpoint = None
            entry.ab_Ret_SDD_breakpoint = None
            entry.ab_Ret_S_breakpoint = None
            entry.ab_Retest_Alert_val = ""
        else:
            entry.ab_Site_Org = None
            entry.ab_R_breakpoint = None
            entry.ab_I_breakpoint = None
            entry.ab_SDD_breakpoint = None
            entry.ab_S_breakpoint = None
            entry.ab_Alert_val = ""

    entry.save()
