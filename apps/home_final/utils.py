from django.db import models
from django.db.models import Q, Case, When
from apps.home.models import *


# ============================================================
# Antibiotic filtering based on breakpoint availability
# ============================================================
def get_filtered_antibiotics(breakpoint_year, resolved_org, *, retest=False):
    """
    Returns Antibiotic_List filtered by breakpoint availability.
    Matches organism-specific breakpoints first, then generic ones.
    """

    qs = Antibiotic_List.objects.all()


    if retest:
        qs = qs.filter(Retest=True)
    else:
        qs = qs.filter(Show=True)


    if not breakpoint_year:
        return qs.order_by("Antibiotic")


    bp_qs = BreakpointsTable.objects.filter(
        Year=breakpoint_year
    )

 
    if resolved_org:
        resolved_org = resolved_org.strip()

        if retest:
            # ARSRL / retest organism
            bp_qs = bp_qs.filter(
                Q(Org__iexact=resolved_org) |
                Q(Org__isnull=True) |
                Q(Org="")
            )
        else:
            # Sentinel organism
            bp_qs = bp_qs.filter(
                Q(Org__iexact=resolved_org) |
                Q(Org__isnull=True) |
                Q(Org="")
            )


    if not bp_qs.exists():
        return qs.order_by("Antibiotic")

    whonet_codes = (
        bp_qs
        .values_list("Whonet_Abx", flat=True)
        .distinct()
    )

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

    return (
        Organism_List.objects
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
        bp = (
            BreakpointsTable.objects
            .filter(
                Whonet_Abx=abx_code,
                Year=year,
                Test_Method="DISK"
            )
            .filter(
                Q(Org__iexact=resolved_org) |
                Q(Org="")
            )
            .order_by(
                Case(
                    When(Org__iexact=resolved_org, then=0),
                    When(Org="", then=1),
                    default=2
                )
            )
            .first()
        )

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
        bp = (
            BreakpointsTable.objects
            .filter(
                Whonet_Abx=abx_code,
                Year=year,
                Test_Method="MIC"
            )
            .filter(
                Q(Org__iexact=resolved_org) |
                Q(Org="")
            )
            .order_by(
                Case(
                    When(Org__iexact=resolved_org, then=0),
                    When(Org="", then=1),
                    default=2
                )
            )
            .first()
        )

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

