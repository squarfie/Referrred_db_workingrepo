# apps/your_app/utils.py


from datetime import timedelta
from sqlalchemy import create_engine
import pandas as pd
from django.db import models
from django.db.models import Q
from django.apps import apps
from apps.home.models import *
from apps.home_final.utils import _year_as_int


#creating a connection to postgresql
# try:
#     # Create SQLAlchemy engine
#     engine = create_engine('postgresql+psycopg2://postgres:admin123@localhost:5432/test_db')

#     # SQL query to fetch data
#     breakpoints_query = "SELECT * FROM home_breakpointstable"
#     antibiotic_query = "SELECT * FROM home_antibioticentry"
#     # Use pandas to fetch data via SQLAlchemy engine
#     breakpoint_data = pd.read_sql_query(breakpoints_query, engine)
#     antibiotic_data = pd.read_sql_query(antibiotic_query, engine)


#     # Display the data
#     print(breakpoint_data)
#     print(antibiotic_data)


    


# except Exception as error:
#     print("Error while fetching data from PostgreSQL:", error)


# finally:
#     print("Execution completed")


# generate codes for handling generation of accession numbers
def generate_codes(site_code, referral_date_obj, ref_no_raw, batch_no, total_batch, site_name):
    """
    Generates accession numbers, batch code, and batch name.
    
    Handles multi-accession ranges like '0001-0002' and returns a list of dictionaries.
    """
    # Ensure referral date is valid
    if not referral_date_obj or not site_code or not ref_no_raw:
        return []

    # Parse the ref_no range
    ref_parts = ref_no_raw.split('-')
    if len(ref_parts) == 2 and ref_parts[0].isdigit() and ref_parts[1].isdigit():
        start_ref = int(ref_parts[0])
        end_ref = int(ref_parts[1])
        ref_numbers = range(start_ref, end_ref + 1)
    else:
        ref_numbers = [int(ref_parts[0])]  # single number

    year_short = referral_date_obj.strftime('%y')
    year_long = referral_date_obj.strftime('%m%d%Y')

    result_list = []

    for ref in ref_numbers:
        padded_ref = str(ref).zfill(4)
        accession_number = f"{year_short}ARS_{site_code}{padded_ref}"
        batch_codegen = f"{site_code}_{year_long}_{batch_no}.{total_batch}_{padded_ref}"
        auto_batch_name = batch_codegen  # identical format

        result_list.append({
            "accession_number": accession_number,
            "batch_codegen": batch_codegen,
            "auto_batch_name": auto_batch_name,
            "site_name": site_name,
        })

    return result_list




#### ADD THIS STARTING FROM HERE ###########


## working code (spec code filtering not added yet)
def get_filtered_antibiotics(breakpoint_year, resolved_org, *, retest=False):
    """
    Returns Antibiotic_List filtered by breakpoint availability.
    Uses the nearest breakpoint year available for the selected organism.
    Falls back to all visible antibiotics if the organism has no breakpoints.
    """
    Antibiotic_List = apps.get_model("home", "Antibiotic_List")
    BreakpointsTable = apps.get_model("home", "BreakpointsTable")

    qs = Antibiotic_List.objects.all()

    if retest:
        qs = qs.filter(Retest=True)
    else:
        qs = qs.filter(Show=True)

    if not breakpoint_year:
        return qs.order_by("Antibiotic")

    bp_qs = BreakpointsTable.objects.filter(
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

    def year_as_int(value):
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return None

    target_year = year_as_int(breakpoint_year)
    years = []
    for year in bp_qs.values_list("Year", flat=True).distinct():
        year_int = year_as_int(year)
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
        year_int = year_as_int(year)
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






def resolve_organism_name(org_code):
    """
    Converts 'sau' → 'Staphylococcus aureus'
    """
    if not org_code:
        return None

    Organism_List = apps.get_model("home", "Organism_List")

    org = (
        Organism_List.objects
        .filter(Whonet_Org_Code__iexact=org_code)
        .values_list("Organism", flat=True)
        .first()
    )

    return org




def working_days(start_date, end_date, step_owner=None):
    """
    Calculates working days between two dates.
    Excludes:
        - Saturdays
        - Sundays
        - Holidays in NonWorkingDay table
    If step_owner is provided (LAB / DMU),
    department-specific exclusions are applied.
    """

    if not start_date or not end_date:
        return None

    if end_date < start_date:
        return 0

    # 🔹 SAFE dynamic model loading (prevents circular import)
    NonWorkingDay = apps.get_model("home", "NonWorkingDay")

    holidays = NonWorkingDay.objects.filter(
        date__gte=start_date,
        date__lt=end_date
    )

    holiday_map = {
        h.date: h.applies_to
        for h in holidays
    }
    recurring_holidays = [
        (h.date.month, h.date.day, h.applies_to)
        for h in NonWorkingDay.objects.filter(is_recurring=True)
    ]

    day_count = 0
    current = start_date

    while current < end_date:

        # Skip weekends
        if current.weekday() >= 5:
            current += timedelta(days=1)
            continue

        # Skip holidays
        holiday_type = holiday_map.get(current)
        if not holiday_type:
            for month, day, applies_to in recurring_holidays:
                if current.month == month and current.day == day:
                    holiday_type = applies_to
                    break

        if holiday_type:
            if holiday_type == "ALL":
                current += timedelta(days=1)
                continue
            if step_owner and holiday_type == step_owner:
                current += timedelta(days=1)
                continue

        day_count += 1
        current += timedelta(days=1)

    return day_count



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

    Organism_List = apps.get_model("home", "Organism_List")
    organism = (
        Organism_List.objects
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
    bp_qs = BreakpointsTable.objects.all()

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
