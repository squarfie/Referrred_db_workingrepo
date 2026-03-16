# ================================
# Standard Library
# ================================
import os
import re
import csv
from decimal import Decimal, InvalidOperation
from datetime import date, datetime
from collections import OrderedDict, defaultdict
from django.templatetags.static import static
# ================================
# Django Core
# ================================
from django.shortcuts import render, redirect, get_object_or_404
from django.http import (
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse,
    FileResponse,
)
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.template.loader import get_template
from django.utils import timezone
from django.utils.timezone import now
from django.utils.dateparse import parse_date
from django.db import IntegrityError, transaction
from django.db.models import (
    Q,
    Count,
    Prefetch,
    Case,
    When,
)
from django.core.paginator import Paginator
from django.views.decorators.http import require_GET, require_POST

# ================================
# Third-Party Libraries
# ================================

import openpyxl
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font as XLFont  # ✅ Safe alias (NO tkinter)

# PDF (ReportLab)
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

# Optional PDF (HTML to PDF)
from xhtml2pdf import pisa
from openpyxl.styles import Font

# ================================
# Project Imports
# ================================
from apps.home.views import link_callback
from apps.home.models import *
from apps.home.forms import *
from apps.wgs_app.models import *
from apps.wgs_app.forms import *

from .models import *
from .forms import *
from .models import ConcordanceReport
from .utils import get_filtered_antibiotics, apply_final_breakpoints
from django.db.models.functions import ExtractYear

# SHOW FINAL DATA TABLE
# @login_required(login_url="/login/")
# def show_final_table(request):
#     query = request.GET.get("q", "").strip()

#     # DEFAULT SORT FIELD MUST EXIST
#     sort_by = request.GET.get("sort", "f_Date_Modified")
#     order = request.GET.get("order", "desc")

#     # SAFETY: allow only valid sortable fields
#     allowed_sort_fields = {
#         "f_AccessionNo",
#         "f_First_Name",
#         "f_Last_Name",
#         "f_Batch_Code",
#         "f_SiteCode",
#         "f_Date_Modified",
#         "f_Spec_Date",
#     }

#     if sort_by not in allowed_sort_fields:
#         sort_by = "f_Date_Modified"

#     sort_field = f"-{sort_by}" if order == "desc" else sort_by

#     # BASE QUERYSET
#     records = (
#         Final_Data.objects
#         .select_related("f_Spec_Type", "f_Batch_id")  # FK optimization
#         .prefetch_related("final_entries")           # Antibiotics
#         .order_by(sort_field)
#     )

#     # SEARCH LOGIC (ALIGNED WITH Final_Data)
#     if query:
#         records = records.filter(
#             Q(f_AccessionNo__icontains=query) |
#             Q(f_First_Name__icontains=query) |
#             Q(f_Last_Name__icontains=query) |
#             Q(f_Patient_ID__icontains=query) |
#             Q(f_Batch_Code__icontains=query) |
#             Q(f_SiteCode__icontains=query) |
#             Q(f_Site_Name__icontains=query) |
#             Q(f_Site_Org__icontains=query) |
#             Q(f_Site_OrgName__icontains=query) |
#             Q(f_ars_OrgCode__icontains=query) |
#             Q(f_ars_OrgName__icontains=query) |
#             Q(f_Spec_Num__icontains=query) |
#             Q(f_Spec_Type__Specimen_code__icontains=query) |   # FK SAFE
#             Q(f_Spec_Type__Specimen_name__icontains=query)
#         ).distinct()

#     # PAGINATION
#     paginator = Paginator(records, 20)
#     page_number = request.GET.get("page")
#     page_obj = paginator.get_page(page_number)

#     return render(
#         request,
#         "home_final/tables_final.html",
#         {
#             "page_obj": page_obj,
#             "current_sort": sort_by,
#             "current_order": order,
#             "query": query,
#         }
#     )




@login_required(login_url="/login/")
def show_final_table(request):

    query = request.GET.get("q", "").strip()
    year = request.GET.get("year")

    sort_by = request.GET.get("sort", "f_Date_Modified")
    order = request.GET.get("order", "desc")

    allowed_sort_fields = {
        "f_AccessionNo",
        "f_First_Name",
        "f_Last_Name",
        "f_Batch_Code",
        "f_SiteCode",
        "f_Date_Modified",
        "f_Spec_Date",
    }

    if sort_by not in allowed_sort_fields:
        sort_by = "f_Date_Modified"

    sort_field = f"-{sort_by}" if order == "desc" else sort_by

    records = (
        Final_Data.objects
        .select_related("f_Spec_Type", "f_Batch_id")
        .prefetch_related("final_entries")
    )

    #  SEARCH
    if query:
        records = records.filter(
            Q(f_AccessionNo__icontains=query) |
            Q(f_First_Name__icontains=query) |
            Q(f_Last_Name__icontains=query) |
            Q(f_Patient_ID__icontains=query) |
            Q(f_Batch_Code__icontains=query) |
            Q(f_SiteCode__icontains=query) |
            Q(f_Site_Name__icontains=query) |
            Q(f_Site_Org__icontains=query) |
            Q(f_Site_OrgName__icontains=query) |
            Q(f_ars_OrgCode__icontains=query) |
            Q(f_ars_OrgName__icontains=query) |
            Q(f_Spec_Num__icontains=query) |
            Q(f_Spec_Type__Specimen_code__icontains=query) |
            Q(f_Spec_Type__Specimen_name__icontains=query)
        ).distinct()

    # YEAR FILTER
    if year and year.isdigit():
        records = records.filter(f_Referral_Date__year=int(year))

    records = records.order_by(sort_field)

    paginator = Paginator(records, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Available years
    available_years = (
        Final_Data.objects
        .annotate(year=ExtractYear("f_Referral_Date"))
        .values_list("year", flat=True)
        .distinct()
        .order_by("-year")
    )

    # Preserve GET parameters
    params = request.GET.copy()
    params.pop("sort", None)
    params.pop("order", None)
    preserved_params = params.urlencode()

    return render(
        request,
        "home_final/tables_final.html",
        {
            "page_obj": page_obj,
            "current_sort": sort_by,
            "current_order": order,
            "query": query,
            "year": year,
            "available_years": available_years,
            "preserved_params": preserved_params,
        }
    )




# # Create your views here.

# EDIT DATA - NEW VERSION
# @login_required(login_url="/login/")
# @transaction.atomic
# def edit_final_data(request, id):

#     isolate = get_object_or_404(Final_Data, pk=id)

#     request.session["current_final_isolate_id"] = isolate.id


#     classification, _ = Classification_Table.objects.get_or_create(
#         Class_AccessionNo=isolate.f_AccessionNo,
#         defaults={"Class_idNumReferred": isolate}
#     )


#     # =========================
#     # GET
#     # =========================
#     if request.method == "GET":

#         form = FinalReferred_Form(instance=isolate)

#         antibiotics_main = Antibiotic_List.objects.filter(Show=True).order_by("Antibiotic")
#         antibiotics_retest = Antibiotic_List.objects.filter(Retest=True).order_by("Antibiotic")

#         existing_entries = Final_AntibioticEntry.objects.filter(
#             ab_idNum_f_referred=isolate
#         )

#         retest_entries = existing_entries.exclude(
#             ab_Retest_Abx_code__isnull=True
#         )

#         return render(request, "home_final/edit_final.html", {
#             "form": form,
#             "isolates": isolate,
#             "antibiotics_main": antibiotics_main,
#             "antibiotics_retest": antibiotics_retest,
#             "existing_entries": existing_entries,
#             "retest_entries": retest_entries,
#             "classification": classification,
#             "edit_mode": True,
#         })

#     # =========================
#     # POST
#     # =========================


#     old_site_org = (isolate.f_Site_Org or "").strip()
#     old_ars_org  = (isolate.f_ars_OrgCode or "").strip()

#     form = FinalReferred_Form(request.POST, instance=isolate)
#     if not form.is_valid():
#         messages.error(request, "Error saving Final data.")
#         return redirect("edit_final_data", id=id)

#     # use instance, NOT form.save()
#     isolate = form.instance

#     # --- FORCE SAVE SITE ORG ---
#     site_org_obj = form.cleaned_data.get("f_Site_Org")
#     if site_org_obj:
#         isolate.f_Site_Org = site_org_obj.Whonet_Org_Code
#     else:
#         isolate.f_Site_Org = ""

#     # --- FORCE SAVE ARS ORG ---
#     ars_org_obj = form.cleaned_data.get("f_ars_OrgCode")
#     if ars_org_obj:
#         isolate.f_ars_OrgCode = ars_org_obj.Whonet_Org_Code
#     else:
#         isolate.f_ars_OrgCode = ""

#     # save ONCE
#     isolate.save()

#     classification.Class_Chk_Emerging    = "Class_Chk_Emerging" in request.POST
#     classification.Class_Chk_Satscan     = "Class_Chk_Satscan" in request.POST
#     classification.Class_Chk_Serotyping  = "Class_Chk_Serotyping" in request.POST
#     classification.Class_Chk_GHRU_all    = "Class_Chk_GHRU_all" in request.POST
#     classification.Class_Chk_GHRU_Neo    = "Class_Chk_GHRU_Neo" in request.POST
#     classification.Class_Chk_Tricycle    = "Class_Chk_Tricycle" in request.POST

#     classification.Class_AccessionNo = isolate.f_AccessionNo
#     classification.save()




#     # =========================
#     # Breakpoint year
#     # =========================
#     specimen_year = isolate.f_Spec_Date.year if isolate.f_Spec_Date else None

#     if specimen_year:
#         effective_year = (
#             BreakpointsTable.objects
#             .filter(Year__lte=str(specimen_year))
#             .order_by("-Year")
#             .values_list("Year", flat=True)
#             .first()
#         )
#     else:
#         effective_year = (
#             BreakpointsTable.objects
#             .order_by("-Year")
#             .values_list("Year", flat=True)
#             .first()
#         )

#     resolved_site_org = (isolate.f_Site_Org or "").strip()
#     resolved_ars_org  = (isolate.f_ars_OrgCode or "").strip()

#     # =========================
#     # ORG CHANGE CLEANUP
#     # =========================
#     if old_site_org != resolved_site_org:
#         Final_AntibioticEntry.objects.filter(
#             ab_idNum_f_referred=isolate,
#             ab_Abx_code__isnull=False
#         ).delete()

#     if old_ars_org != resolved_ars_org:
#         Final_AntibioticEntry.objects.filter(
#             ab_idNum_f_referred=isolate,
#             ab_Retest_Abx_code__isnull=False
#         ).delete()

#     # =========================
#     # MAIN ANTIBIOTICS
#     # =========================
#     for abx in Antibiotic_List.objects.filter(Show=True):

#         code = (abx.Whonet_Abx or "").strip().upper()

#         disk = request.POST.get(f"disk_{code}")
#         mic  = request.POST.get(f"mic_{code}")

#         disk = int(disk) if disk and disk.isdigit() else None
#         mic  = float(mic) if mic else None

#         if disk is None and mic is None:
#             continue

#         entry, _ = Final_AntibioticEntry.objects.update_or_create(
#             ab_idNum_f_referred=isolate,
#             ab_Abx_code=code,
#             defaults={
#                 "ab_AccessionNo": isolate.f_AccessionNo,
#                 "ab_Antibiotic": abx.Antibiotic,
#                 "ab_Abx": abx.Abx_code,
#                 "ab_Disk_value": disk,
#                 "ab_MIC_value": mic,
#                 "ab_Disk_enRIS": request.POST.get(f"disk_enris_{code}", ""),
#                 "ab_MIC_enRIS": request.POST.get(f"mic_enris_{code}", ""),
#                 "ab_MIC_operand": request.POST.get(f"mic_operand_{code}", ""),
#                 "ab_AlertMIC": f"alert_mic_{code}" in request.POST,
#             }
#         )

#         apply_final_breakpoints(
#             entry,
#             org_code=resolved_site_org,
#             year=effective_year,
#             is_retest=False
#         )

#     # =========================
#     # RETEST ANTIBIOTICS
#     # =========================
#     for abx in Antibiotic_List.objects.filter(Retest=True):

#         code = (abx.Whonet_Abx or "").strip().upper()

#         disk = request.POST.get(f"retest_disk_{code}")
#         mic  = request.POST.get(f"retest_mic_{code}")

#         disk = int(disk) if disk and disk.isdigit() else None
#         mic  = float(mic) if mic else None

#         if disk is None and mic is None:
#             continue

#         entry, _ = Final_AntibioticEntry.objects.update_or_create(
#             ab_idNum_f_referred=isolate,
#             ab_Retest_Abx_code=code,
#             defaults={
#                 "ab_AccessionNo": isolate.f_AccessionNo,
#                 "ab_Retest_Antibiotic": abx.Antibiotic,
#                 "ab_Retest_Abx": abx.Abx_code,
#                 "ab_Retest_DiskValue": disk,
#                 "ab_Retest_MICValue": mic,
#                 "ab_Retest_Disk_enRIS": request.POST.get(f"retest_disk_enris_{code}", ""),
#                 "ab_Retest_MIC_enRIS": request.POST.get(f"retest_mic_enris_{code}", ""),
#                 "ab_Retest_MIC_operand": request.POST.get(f"retest_mic_operand_{code}", ""),
#                 "ab_Retest_AlertMIC": f"retest_alert_mic_{code}" in request.POST,
#             }
#         )

#         apply_final_breakpoints(
#             entry,
#             org_code=resolved_ars_org,
#             year=effective_year,
#             is_retest=True
#         )

#     messages.success(request, "Final data saved successfully.")
#     return redirect("show_final_table")




@login_required(login_url="/login/")
@transaction.atomic
def edit_final_data(request, id):

    isolate = get_object_or_404(Final_Data, pk=id)

    request.session["current_final_isolate_id"] = isolate.id

    classification, _ = Classification_Table.objects.get_or_create(
        Class_idNumReferred=isolate,
        defaults={"Class_AccessionNo": isolate.f_AccessionNo}
    )

    # =========================
    # GET
    # =========================
    if request.method == "GET":

        form = FinalReferred_Form(instance=isolate)

        antibiotics_main = (
            Antibiotic_List.objects
            .filter(Show=True)
            .order_by("Antibiotic")
        )

        antibiotics_retest = (
            Antibiotic_List.objects
            .filter(Retest=True)
            .order_by("Antibiotic")
        )

        existing_entries = Final_AntibioticEntry.objects.filter(
            ab_idNum_f_referred=isolate
        )

        retest_entries = existing_entries.exclude(
            ab_Retest_Abx_code__isnull=True
        )

        return render(request, "home_final/edit_final.html", {
            "form": form,
            "isolates": isolate,
            "antibiotics_main": antibiotics_main,
            "antibiotics_retest": antibiotics_retest,
            "existing_entries": existing_entries,
            "retest_entries": retest_entries,
            "classification": classification,
            "edit_mode": True,
        })

    # =========================
    # POST
    # =========================

    old_site_org = (isolate.f_Site_Org or "").strip()
    old_ars_org  = (isolate.f_ars_OrgCode or "").strip()

    form = FinalReferred_Form(request.POST, instance=isolate)

    if not form.is_valid():
        messages.error(request, "Error saving Final data.")
        return redirect("edit_final_data", id=id)

    isolate = form.save()

    # =========================
    # SAVE CLASSIFICATION
    # =========================
    classification.Class_Chk_Emerging   = "Class_Chk_Emerging" in request.POST
    classification.Class_Chk_Satscan    = "Class_Chk_Satscan" in request.POST
    classification.Class_Chk_Serotyping = "Class_Chk_Serotyping" in request.POST
    classification.Class_Chk_GHRU_all   = "Class_Chk_GHRU_all" in request.POST
    classification.Class_Chk_GHRU_Neo   = "Class_Chk_GHRU_Neo" in request.POST
    classification.Class_Chk_Tricycle   = "Class_Chk_Tricycle" in request.POST
    classification.Class_AccessionNo    = isolate.f_AccessionNo
    classification.save()

    # =========================
    # BREAKPOINT YEAR
    # =========================
    specimen_year = isolate.f_Spec_Date.year if isolate.f_Spec_Date else None

    if specimen_year:
        effective_year = (
            BreakpointsTable.objects
            .filter(Year__lte=str(specimen_year))
            .order_by("-Year")
            .values_list("Year", flat=True)
            .first()
        )
    else:
        effective_year = (
            BreakpointsTable.objects
            .order_by("-Year")
            .values_list("Year", flat=True)
            .first()
        )

    new_site_org = (isolate.f_Site_Org or "").strip()
    new_ars_org  = (isolate.f_ars_OrgCode or "").strip()

    # =========================
    # DELETE IF ORGANISM CHANGED
    # =========================
    if old_site_org != new_site_org:
        Final_AntibioticEntry.objects.filter(
            ab_idNum_f_referred=isolate,
            ab_Abx_code__isnull=False
        ).delete()

    if old_ars_org != new_ars_org:
        Final_AntibioticEntry.objects.filter(
            ab_idNum_f_referred=isolate,
            ab_Retest_Abx_code__isnull=False
        ).delete()

    resolved_site_org = new_site_org
    resolved_ars_org  = new_ars_org

    # =========================
    # MAIN ANTIBIOTICS
    # =========================
    for abx in Antibiotic_List.objects.filter(Show=True):

        abx_code = (abx.Whonet_Abx or "").strip().upper()

        disk_value  = request.POST.get(f"disk_{abx_code}")
        mic_value   = request.POST.get(f"mic_{abx_code}")
        disk_enris  = request.POST.get(f"disk_enris_{abx_code}", "").strip()
        mic_enris   = request.POST.get(f"mic_enris_{abx_code}", "").strip()
        mic_operand = request.POST.get(f"mic_operand_{abx_code}", "").strip()
        alert_mic   = f"alert_mic_{abx_code}" in request.POST

        try:
            disk_value = int(disk_value) if disk_value else None
        except ValueError:
            disk_value = None

        try:
            mic_value = float(mic_value) if mic_value else None
        except ValueError:
            mic_value = None

        if disk_value is None and mic_value is None:
            Final_AntibioticEntry.objects.filter(
                ab_idNum_f_referred=isolate,
                ab_Abx_code=abx_code
            ).delete()
            continue

        entry, _ = Final_AntibioticEntry.objects.update_or_create(
            ab_idNum_f_referred=isolate,
            ab_Abx_code=abx_code,
            defaults={
                "ab_AccessionNo": isolate.f_AccessionNo,
                "ab_Antibiotic": abx.Antibiotic,
                "ab_Abx": abx.Abx_code,
                "ab_Disk_value": disk_value,
                "ab_Disk_enRIS": disk_enris,
                "ab_MIC_value": mic_value,
                "ab_MIC_enRIS": mic_enris,
                "ab_MIC_operand": mic_operand,
                "ab_AlertMIC": alert_mic,
            }
        )

        entry.ab_breakpoints_id.clear()
        bp_applied = False

        # DISK
        if disk_value is not None:
            bp_disk = BreakpointsTable.objects.filter(
                Antibiotic_list_id=abx_code,
                Year=effective_year,
                Test_Method="DISK",
                Org__in=[resolved_site_org, ""]
            ).order_by("-Org").first()

            if bp_disk:
                entry.ab_breakpoints_id.set([bp_disk])
                entry.ab_Site_Org = bp_disk.Org 
                entry.ab_R_breakpoint = bp_disk.R_val
                entry.ab_I_breakpoint = bp_disk.I_val
                entry.ab_SDD_breakpoint = bp_disk.SDD_val
                entry.ab_S_breakpoint = bp_disk.S_val
                bp_applied = True

        # MIC
        if mic_value is not None:
            bp_mic = BreakpointsTable.objects.filter(
                Antibiotic_list_id=abx_code,
                Year=effective_year,
                Test_Method="MIC",
                Org__in=[resolved_site_org, ""]
            ).order_by("-Org").first()

            if bp_mic:
                entry.ab_breakpoints_id.set([bp_mic])
                entry.ab_Site_Org = bp_mic.Org
                entry.ab_R_breakpoint = bp_mic.R_val
                entry.ab_I_breakpoint = bp_mic.I_val
                entry.ab_SDD_breakpoint = bp_mic.SDD_val
                entry.ab_S_breakpoint = bp_mic.S_val
                entry.ab_Alert_val = bp_mic.Alert_val if alert_mic else ""
                bp_applied = True

        if not bp_applied:
            entry.ab_Site_Org = None
            entry.ab_R_breakpoint = None
            entry.ab_I_breakpoint = None
            entry.ab_SDD_breakpoint = None
            entry.ab_S_breakpoint = None
            entry.ab_Alert_val = ""

        entry.save()

    # =========================
    # RETEST ANTIBIOTICS
    # =========================
    for abx in Antibiotic_List.objects.filter(Retest=True):

        abx_code = (abx.Whonet_Abx or "").strip().upper()

        disk_value  = request.POST.get(f"retest_disk_{abx_code}")
        mic_value   = request.POST.get(f"retest_mic_{abx_code}")
        disk_enris  = request.POST.get(f"retest_disk_enris_{abx_code}", "").strip()
        mic_enris   = request.POST.get(f"retest_mic_enris_{abx_code}", "").strip()
        mic_operand = request.POST.get(f"retest_mic_operand_{abx_code}", "").strip()
        alert_mic   = f"retest_alert_mic_{abx_code}" in request.POST

        try:
            disk_value = int(disk_value) if disk_value else None
        except ValueError:
            disk_value = None

        try:
            mic_value = float(mic_value) if mic_value else None
        except ValueError:
            mic_value = None

        if disk_value is None and mic_value is None:
            Final_AntibioticEntry.objects.filter(
                ab_idNum_f_referred=isolate,
                ab_Retest_Abx_code=abx_code
            ).delete()
            continue

        entry, _ = Final_AntibioticEntry.objects.update_or_create(
            ab_idNum_f_referred=isolate,
            ab_Retest_Abx_code=abx_code,
            defaults={
                "ab_AccessionNo": isolate.f_AccessionNo,
                "ab_Retest_Antibiotic": abx.Antibiotic,
                "ab_Retest_Abx": abx.Abx_code,
                "ab_Retest_DiskValue": disk_value,
                "ab_Retest_MICValue": mic_value,
                "ab_Retest_Disk_enRIS": disk_enris,
                "ab_Retest_MIC_enRIS": mic_enris,
                "ab_Retest_MIC_operand": mic_operand,
                "ab_Retest_AlertMIC": alert_mic,
            }
        )

        entry.ab_breakpoints_id.clear()
        ret_bp_applied = False

        if disk_value is not None:
            bp_disk = BreakpointsTable.objects.filter(
                Antibiotic_list_id=abx_code,
                Year=effective_year,
                Test_Method="DISK",
                Org__in=[resolved_ars_org, ""]
            ).order_by("-Org").first()

            if bp_disk:
                entry.ab_breakpoints_id.set([bp_disk])
                entry.ab_Ret_Org = bp_disk.Org
                entry.ab_Org_Flag = bool(bp_disk.Emerging_Org_Flag)
                entry.ab_Abx_Flag = bool(bp_disk.Emerging_Abx_Flag)
                entry.ab_Abx_Phenotype = bp_disk.Emerging_Pheno_Flag or ""
                entry.ab_Ret_R_breakpoint = bp_disk.R_val
                entry.ab_Ret_I_breakpoint = bp_disk.I_val
                entry.ab_Ret_SDD_breakpoint = bp_disk.SDD_val
                entry.ab_Ret_S_breakpoint = bp_disk.S_val
                ret_bp_applied = True

        if mic_value is not None:
            bp_mic = BreakpointsTable.objects.filter(
                Antibiotic_list_id=abx_code,
                Year=effective_year,
                Test_Method="MIC",
                Org__in=[resolved_ars_org, ""]
            ).order_by("-Org").first()

            if bp_mic:
                entry.ab_breakpoints_id.set([bp_mic])
                entry.ab_Ret_Org = bp_mic.Org
                entry.ab_Org_Flag = bool(bp_mic.Emerging_Org_Flag)
                entry.ab_Abx_Flag = bool(bp_mic.Emerging_Abx_Flag)
                entry.ab_Abx_Phenotype = bp_mic.Emerging_Pheno_Flag or ""
                entry.ab_Ret_R_breakpoint = bp_mic.R_val
                entry.ab_Ret_I_breakpoint = bp_mic.I_val
                entry.ab_Ret_SDD_breakpoint = bp_mic.SDD_val
                entry.ab_Ret_S_breakpoint = bp_mic.S_val
                entry.ab_Retest_Alert_val = bp_mic.Alert_val if alert_mic else ""
                ret_bp_applied = True

        if not ret_bp_applied:
            entry.ab_Ret_Org = None
            entry.ab_Org_Flag = False
            entry.ab_Abx_Flag = False
            entry.ab_Abx_Phenotype = ""
            entry.ab_Ret_R_breakpoint = None
            entry.ab_Ret_I_breakpoint = None
            entry.ab_Ret_SDD_breakpoint = None
            entry.ab_Ret_S_breakpoint = None
            entry.ab_Retest_Alert_val = ""

        entry.save()

    messages.success(request, "Final data saved successfully.")
    return redirect("show_final_table")









############## Lab Result



@transaction.atomic
def generate_final_batch_pdf(request, id):

    # fetch batch isolates
    batch = get_object_or_404(Batch_Table, pk=id)

    isolates = (
        Final_Data.objects
        .filter(f_Batch_id=batch)
        .order_by("f_bat_seq")
    )

    # paginate: 2 isolates per page
    def chunked(qs, size):
        for i in range(0, qs.count(), size):
            yield qs[i:i + size]

    isolate_pages = list(chunked(isolates, 2))

    # these are the constants
    MAX_COLS = 29
    MAX_ROWS = 3

    def chunk_list(items, size):
        for i in range(0, len(items), size):
            yield items[i:i + size]

    pages_data = []

    # whonet code map
    abx_map = dict(
        Antibiotic_List.objects
        .values_list("Whonet_Abx", "Abx_code")
    )

    # build pdf
    for page_isolates in isolate_pages:
        page_entries = []

        for isolate in page_isolates:

            site_org = isolate.f_Site_Org
            ars_org = isolate.f_ars_OrgCode

            # fetch the entries
            entries = Final_AntibioticEntry.objects.filter(
                ab_idNum_f_referred=isolate
            )

            # panels
            site_panel_abx = set(
                BreakpointsTable.objects
                .filter(Org=site_org)
                .values_list("Abx_code", flat=True)
                .distinct()
            )

            ars_panel_abx = set(
                BreakpointsTable.objects
                .filter(Org=ars_org)
                .values_list("Abx_code", flat=True)
                .distinct()
            )

            # extract printable antibiotics
            printable_abx_site = set(
                Antibiotic_List.objects
                .filter(Show_Site=True)
                .values_list("Abx_code", flat=True)
            )

            printable_abx_ars = set(
                Antibiotic_List.objects
                .filter(Show_Ars=True)
                .values_list("Abx_code", flat=True)
            )

            # find the encoded antiboitcs
            encoded_site_abx = set()
            encoded_ars_abx = set()

            for e in entries:
                if e.ab_Abx_code:
                    abx = abx_map.get(e.ab_Abx_code.strip().upper())
                    if abx:
                        encoded_site_abx.add(abx)

                if e.ab_Retest_Abx_code:
                    abx = abx_map.get(e.ab_Retest_Abx_code.strip().upper())
                    if abx:
                        encoded_ars_abx.add(abx)

            # create the panels 
            site_abx_codes = sorted(
                (site_panel_abx | encoded_site_abx) & printable_abx_site
            )

            ars_abx_codes = sorted(
                (ars_panel_abx | encoded_ars_abx) & printable_abx_ars
            )

            # group the antibiotics based on panels
            grouped_site = {
                abx: {"disk": None, "mic": None}
                for abx in site_abx_codes
            }

            grouped_ars = {
                abx: {"disk": None, "mic": None}
                for abx in ars_abx_codes
            }

           # assign the values into groups
            for e in entries:

                # -sentinel site-
                if e.ab_Abx_code:
                    abx = abx_map.get(e.ab_Abx_code.strip().upper())
                    if abx and abx in grouped_site:
                        # Prefer DISK if a disk value exists
                        if e.ab_Disk_value is not None:
                            grouped_site[abx]["disk"] = e

                        # Otherwise assign MIC only if MIC value exists
                        elif e.ab_MIC_value is not None:
                            grouped_site[abx]["mic"] = e


                # -arsrl / retest-
                if e.ab_Retest_Abx_code:
                    abx = abx_map.get(e.ab_Retest_Abx_code.strip().upper())
                    if abx and abx in grouped_ars:
                        if e.ab_Retest_DiskValue is not None:
                            grouped_ars[abx]["disk"] = e
                        elif e.ab_Retest_MICValue is not None:
                            grouped_ars[abx]["mic"] = e


            # a chunk for display
            grouped_rows = list(
                chunk_list(list(grouped_site.items()), MAX_COLS)
            )[:MAX_ROWS]

            grouped_ars_rows = list(
                chunk_list(list(grouped_ars.items()), MAX_COLS)
            )[:MAX_ROWS]

            page_entries.append({
                "isolate": isolate,
                "grouped_rows": grouped_rows,
                "grouped_ars_rows": grouped_ars_rows,
            })

        pages_data.append(page_entries)

    # render the pdf
    context = {
        "batch": batch,
        "pages": pages_data,
        "now": timezone.now(),
        "logo_path": static("assets/img/brand/arsplogo.jpg"),
    }

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'filename="Batch_Panel_Report.pdf"'

    template = get_template("home_final/Lab_result_panel_final.html")

    html = template.render(context)

    pisa.CreatePDF(
        html,
        dest=response,
        link_callback=link_callback
    )

    return response




############ filter antibiotics for panels


# used in breakopints dropdown for organism 
@require_GET
def get_organism_group(request):
    org_code = request.GET.get("org_code")

    if not org_code:
        return JsonResponse({"genus_group": ""})

    try:
        organism = Organism_List.objects.get(
            Whonet_Org_Code=org_code
        )
        return JsonResponse({
            "genus_group": organism.Genus_Group or ""
        })
    except Organism_List.DoesNotExist:
        return JsonResponse({"genus_group": ""})


## aut fill  abx code and tier

@login_required(login_url="/login/")
def get_antibiotic_name(request):
    whonet_code = request.GET.get("whonet")
    try:
        abx = Antibiotic_List.objects.get(Whonet_Abx=whonet_code)
        return JsonResponse({"name": abx.Antibiotic})
    except Antibiotic_List.DoesNotExist:
        return JsonResponse({"name": ""})

@require_GET
def get_antibiotic_details(request):
    whonet_abx = request.GET.get("whonet_abx", "").strip()
    
    # Use filter().first() to avoid DoesNotExist exceptions crashing the AJAX call
    abx = Antibiotic_List.objects.filter(Whonet_Abx=whonet_abx).first()
    
    if abx:
        return JsonResponse({
            "antibiotic": abx.Antibiotic,
            "abx_code": abx.Abx_code,
            "tier": abx.Tier,
        })
    
    return JsonResponse({"error": "Not found"}, status=404)


# @login_required(login_url="/login/")
# def ajax_filter_antibiotics(request):
#     if not request.user.is_authenticated:
#         return JsonResponse({"error": "Unauthorized"}, status=401)


#     isolate_id = request.GET.get("isolate_id")
#     org_code   = request.GET.get("org", "").strip().lower()
#     retest     = request.GET.get("retest") == "1"

#     isolate = get_object_or_404(Final_Data, pk=isolate_id)

#     # ================= DETERMINE BREAKPOINT YEAR =================
#     specimen_year = isolate.f_Spec_Date.year if isolate.f_Spec_Date else None

#     if specimen_year:
#         breakpoint_year = (
#             BreakpointsTable.objects
#             .filter(Year__lte=str(specimen_year))
#             .order_by("-Year")
#             .values_list("Year", flat=True)
#             .first()
#         )
#     else:
#         breakpoint_year = (
#             BreakpointsTable.objects
#             .order_by("-Year")
#             .values_list("Year", flat=True)
#             .first()
#         )

#     # If no breakpoints exist at all, return empty safely
#     if not breakpoint_year:
#         return JsonResponse({"antibiotics": []})

#     # ================= FILTER ANTIBIOTICS =================
#     antibiotics = get_filtered_antibiotics(
#         breakpoint_year,
#         org_code,     # ALWAYS organism code
#         retest=retest
#     )

#     # ================= FETCH EXISTING FINAL ENTRIES =================
#     entries = Final_AntibioticEntry.objects.filter(
#         ab_idNum_f_referred=isolate
#     )

#     # Map entries by WHONET code
#     entry_map = {}
#     for e in entries:
#         code = e.ab_Retest_Abx_code if retest else e.ab_Abx_code
#         if code:
#             entry_map[code.strip().upper()] = e

#     # ================= BUILD RESPONSE =================
#     payload = []

#     for abx in antibiotics:
#         code = (abx.Whonet_Abx or "").strip().upper()
#         entry = entry_map.get(code)

#         if retest:
#             payload.append({
#                 "whonet": code,
#                 "name": abx.Antibiotic,
#                 "is_disk": abx.Disk_Abx,

#                 # RETEST VALUES (FINAL)
#                 "disk": entry.ab_Retest_DiskValue if entry else "",
#                 "disk_enris": entry.ab_Retest_Disk_enRIS if entry else "",
#                 "mic": entry.ab_Retest_MICValue if entry else "",
#                 "mic_enris": entry.ab_Retest_MIC_enRIS if entry else "",
#                 "mic_operand": entry.ab_Retest_MIC_operand if entry else "",
#                 "alert_mic": entry.ab_Retest_AlertMIC if entry else False,
#             })
#         else:
#             payload.append({
#                 "whonet": code,
#                 "name": abx.Antibiotic,
#                 "is_disk": abx.Disk_Abx,

#                 # MAIN VALUES (FINAL)
#                 "disk": entry.ab_Disk_value if entry else "",
#                 "disk_enris": entry.ab_Disk_enRIS if entry else "",
#                 "mic": entry.ab_MIC_value if entry else "",
#                 "mic_enris": entry.ab_MIC_enRIS if entry else "",
#                 "mic_operand": entry.ab_MIC_operand if entry else "",
#                 "alert_mic": entry.ab_AlertMIC if entry else False,
#             })

#     return JsonResponse({"antibiotics": payload})





# @login_required(login_url="/login/")
# def ajax_filter_antibiotics(request):
#     if not request.user.is_authenticated:
#         return JsonResponse({"error": "Unauthorized"}, status=401)


#     isolate_id = request.GET.get("isolate_id")
#     org_code   = request.GET.get("org", "").strip().lower()
#     retest     = request.GET.get("retest") == "1"

#     isolate = get_object_or_404(Final_Data, pk=isolate_id)

#     # ================= DETERMINE BREAKPOINT YEAR =================
#     specimen_year = isolate.f_Spec_Date.year if isolate.f_Spec_Date else None

#     if specimen_year:
#         breakpoint_year = (
#             BreakpointsTable.objects
#             .filter(Year__lte=str(specimen_year))
#             .order_by("-Year")
#             .values_list("Year", flat=True)
#             .first()
#         )
#     else:
#         breakpoint_year = (
#             BreakpointsTable.objects
#             .order_by("-Year")
#             .values_list("Year", flat=True)
#             .first()
#         )

#     # If no breakpoints exist at all, return empty safely
#     if not breakpoint_year:
#         return JsonResponse({"antibiotics": []})

#     # ================= FILTER ANTIBIOTICS =================
#     antibiotics = get_filtered_antibiotics(
#         breakpoint_year,
#         org_code,     # ALWAYS organism code
#         retest=retest
#     )

#     # ================= FETCH EXISTING FINAL ENTRIES =================
#     entries = Final_AntibioticEntry.objects.filter(
#         ab_idNum_f_referred=isolate
#     )

#     # Map entries by WHONET code
#     entry_map = {}
#     for e in entries:
#         code = e.ab_Retest_Abx_code if retest else e.ab_Abx_code
#         if code:
#             entry_map[code.strip().upper()] = e

#     # ================= BUILD RESPONSE =================
#     payload = []

#     for abx in antibiotics:
#         code = (abx.Whonet_Abx or "").strip().upper()
#         entry = entry_map.get(code)

#         if retest:
#             payload.append({
#                 "whonet": code,
#                 "name": abx.Antibiotic,
#                 "is_disk": abx.Disk_Abx,

#                 # RETEST VALUES (FINAL)
#                 "disk": entry.ab_Retest_DiskValue if entry else "",
#                 "disk_enris": entry.ab_Retest_Disk_enRIS if entry else "",
#                 "mic": entry.ab_Retest_MICValue if entry else "",
#                 "mic_enris": entry.ab_Retest_MIC_enRIS if entry else "",
#                 "mic_operand": entry.ab_Retest_MIC_operand if entry else "",
#                 "alert_mic": entry.ab_Retest_AlertMIC if entry else False,
#             })
#         else:
#             payload.append({
#                 "whonet": code,
#                 "name": abx.Antibiotic,
#                 "is_disk": abx.Disk_Abx,

#                 # MAIN VALUES (FINAL)
#                 "disk": entry.ab_Disk_value if entry else "",
#                 "disk_enris": entry.ab_Disk_enRIS if entry else "",
#                 "mic": entry.ab_MIC_value if entry else "",
#                 "mic_enris": entry.ab_MIC_enRIS if entry else "",
#                 "mic_operand": entry.ab_MIC_operand if entry else "",
#                 "alert_mic": entry.ab_AlertMIC if entry else False,
#             })

#     return JsonResponse({"antibiotics": payload})




@login_required(login_url="/login/")
def ajax_filter_antibiotics(request):
    # 1. Get ID from GET parameters (passed by JS)
    isolate_id = request.GET.get("isolate_id")
    
    # 2. Fallback to session ONLY if GET is missing
    if not isolate_id:
        isolate_id = request.session.get("current_final_isolate_id")

    if not isolate_id:
        return JsonResponse({"error": "No Isolate ID provided"}, status=400)



    org_code   = request.GET.get("org", "").strip().lower()
    retest     = request.GET.get("retest") == "1"

    isolate = get_object_or_404(Final_Data, pk=isolate_id)

    # ================= DETERMINE BREAKPOINT YEAR =================
    specimen_year = isolate.f_Spec_Date.year if isolate.f_Spec_Date else None

    if specimen_year:
        breakpoint_year = (
            BreakpointsTable.objects
            .filter(Year__lte=str(specimen_year))
            .order_by("-Year")
            .values_list("Year", flat=True)
            .first()
        )
    else:
        breakpoint_year = (
            BreakpointsTable.objects
            .order_by("-Year")
            .values_list("Year", flat=True)
            .first()
        )

    # If no breakpoints exist at all, return empty safely
    if not breakpoint_year:
        return JsonResponse({"antibiotics": []})

    # ================= FILTER ANTIBIOTICS =================
    antibiotics = get_filtered_antibiotics(
        breakpoint_year,
        org_code,     # ALWAYS organism code
        retest=retest
    )

    # ================= FETCH EXISTING FINAL ENTRIES =================
    entries = Final_AntibioticEntry.objects.filter(
        ab_idNum_f_referred=isolate
    )

    # Map entries by WHONET code
    entry_map = {}
    for e in entries:
        code = e.ab_Retest_Abx_code if retest else e.ab_Abx_code
        if code:
            entry_map[code.strip().upper()] = e

    # ================= BUILD RESPONSE =================
    payload = []

    for abx in antibiotics:
        code = (abx.Whonet_Abx or "").strip().upper()
        entry = entry_map.get(code)

        if retest:
            payload.append({
                "whonet": code,
                "name": abx.Antibiotic,
                "is_disk": abx.Disk_Abx,

                # RETEST VALUES (FINAL)
                "disk": entry.ab_Retest_DiskValue if entry else "",
                "disk_enris": entry.ab_Retest_Disk_enRIS if entry else "",
                "mic": entry.ab_Retest_MICValue if entry else "",
                "mic_enris": entry.ab_Retest_MIC_enRIS if entry else "",
                "mic_operand": entry.ab_Retest_MIC_operand if entry else "",
                "alert_mic": entry.ab_Retest_AlertMIC if entry else False,
            })
        else:
            payload.append({
                "whonet": code,
                "name": abx.Antibiotic,
                "is_disk": abx.Disk_Abx,

                # MAIN VALUES (FINAL)
                "disk": entry.ab_Disk_value if entry else "",
                "disk_enris": entry.ab_Disk_enRIS if entry else "",
                "mic": entry.ab_MIC_value if entry else "",
                "mic_enris": entry.ab_MIC_enRIS if entry else "",
                "mic_operand": entry.ab_MIC_operand if entry else "",
                "alert_mic": entry.ab_AlertMIC if entry else False,
            })

    return JsonResponse({"antibiotics": payload})


# @login_required(login_url="/login/")
# def ajax_filter_antibiotics(request):
#     # 1. Get ID from GET parameters (passed by JS)
#     isolate_id = request.GET.get("isolate_id")
    
#     # 2. Fallback to session ONLY if GET is missing
#     if not isolate_id:
#         isolate_id = request.session.get("current_final_isolate_id")

#     if not isolate_id:
#         return JsonResponse({"error": "No Isolate ID provided"}, status=400)

#     # 3. Fetch the isolate safely
#     isolate = get_object_or_404(Final_Data, pk=isolate_id)

#     org_code = request.GET.get("org", "").strip().upper()
#     retest   = request.GET.get("retest") == "1"

#     # ================= DETERMINE BREAKPOINT YEAR =================
#     specimen_year = isolate.f_Spec_Date.year if isolate.f_Spec_Date else None

#     if specimen_year:
#         breakpoint_year = (
#             BreakpointsTable.objects
#             .filter(Year__lte=str(specimen_year))
#             .order_by("-Year")
#             .values_list("Year", flat=True)
#             .first()
#         )
#     else:
#         breakpoint_year = (
#             BreakpointsTable.objects
#             .order_by("-Year")
#             .values_list("Year", flat=True)
#             .first()
#         )

#     if not breakpoint_year:
#         return JsonResponse({"antibiotics": []})

#     # ================= FILTER ANTIBIOTICS =================
#     antibiotics = get_filtered_antibiotics(
#         breakpoint_year,
#         org_code,
#         retest=retest
#     )

#     # ================= FETCH EXISTING FINAL ENTRIES =================
#     entries = Final_AntibioticEntry.objects.filter(
#         ab_idNum_f_referred=isolate
#     )

#     entry_map = {}
#     for e in entries:
#         code = e.ab_Retest_Abx_code if retest else e.ab_Abx_code
#         if code:
#             entry_map[code.strip().upper()] = e

#     # ================= BUILD RESPONSE =================
#     payload = []

#     for abx in antibiotics:
#         code = (abx.Whonet_Abx or "").strip().upper()
#         entry = entry_map.get(code)

#         if retest:
#             payload.append({
#                 "whonet": code,
#                 "name": abx.Antibiotic,
#                 "is_disk": abx.Disk_Abx,

#                 "disk": entry.ab_Retest_DiskValue if entry else "",
#                 "disk_enris": entry.ab_Retest_Disk_enRIS if entry else "",
#                 "mic": entry.ab_Retest_MICValue if entry else "",
#                 "mic_enris": entry.ab_Retest_MIC_enRIS if entry else "",
#                 "mic_operand": entry.ab_Retest_MIC_operand if entry else "",
#                 "alert_mic": entry.ab_Retest_AlertMIC if entry else False,
#             })
#         else:
#             payload.append({
#                 "whonet": code,
#                 "name": abx.Antibiotic,
#                 "is_disk": abx.Disk_Abx,

#                 "disk": entry.ab_Disk_value if entry else "",
#                 "disk_enris": entry.ab_Disk_enRIS if entry else "",
#                 "mic": entry.ab_MIC_value if entry else "",
#                 "mic_enris": entry.ab_MIC_enRIS if entry else "",
#                 "mic_operand": entry.ab_MIC_operand if entry else "",
#                 "alert_mic": entry.ab_AlertMIC if entry else False,
#             })

#     return JsonResponse({"antibiotics": payload})






########## organism filtering
@login_required(login_url="/login/")
def get_organism_name(request):
    org_code = request.GET.get("org_code")
    field_key = request.GET.get("field_key")

    if not org_code or not field_key:
        return JsonResponse({"error": "Missing parameters"}, status=400)

    org = Organism_List.objects.filter(
        Whonet_Org_Code=org_code
    ).values().first()

    if not org:
        return JsonResponse({"error": "Organism not found"}, status=404)

    if field_key not in org:
        return JsonResponse({"error": "Invalid field_key"}, status=400)

    return JsonResponse({field_key: org[field_key]})




@login_required(login_url="/login/")
def download_combined_final_table(request):
    """
    Export FINAL DATA + FINAL ANTIBIOTIC ENTRIES into one wide CSV
    """

    final_data_entries = (
        Final_Data.objects
        .prefetch_related("final_entries")
        .all()
    )

    # --------------------------------------------------
    # Collect UNIQUE antibiotics (main + retest)
    # --------------------------------------------------
    unique_abx_codes = set()

    for abx, ret in (
        Final_AntibioticEntry.objects
        .values_list("ab_Abx_code", "ab_Retest_Abx_code")
        .distinct()
    ):
        if abx:
            unique_abx_codes.add(abx.upper())
        if ret:
            unique_abx_codes.add(ret.upper())

    sorted_antibiotics = sorted(unique_abx_codes)

    # --------------------------------------------------
    # HTTP CSV RESPONSE
    # --------------------------------------------------
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="final_combined_data.csv"'
    response.write("\ufeff")  # UTF-8 BOM

    writer = csv.writer(response)

    # --------------------------------------------------
    # STATIC FIELDS (Final_Data)
    # --------------------------------------------------
    static_fields = [
        "f_bat_seq",
        "f_Batch_id",
        "f_Hide",
        "f_Batch_Name",
        "f_Batch_Code",
        "f_Date_of_Entry",
        "f_Date_Modified",
        "f_RefNo",
        "f_BatchNo",
        "f_Total_batch",
        "f_AccessionNo",
        "f_AccessionNoGen",
        "f_SiteCode",
        "f_Site_Name",
        "f_Referral_Date",

        "f_Patient_ID",
        "f_First_Name",
        "f_Mid_Name",
        "f_Last_Name",
        "f_Date_Birth",
        "f_Age",
        "f_Emerging_Flag_Age",
        "f_Sex",
        "f_Date_Admis",
        "f_Nosocomial",
        "f_Diagnosis",
        "f_Diagnosis_ICD10",
        "f_Ward",
        "f_Ward_Type",
        "f_Service_Type",

        "f_Spec_Num",
        "f_Spec_Date",
        "f_Spec_Type",
        "f_Reason",
        "f_Growth",
        "f_Urine_ColCt",

        "f_ampC",
        "f_ESBL",
        "f_CARB",
        "f_MBL",
        "f_BL",
        "f_MR",
        "f_mecA",
        "f_ICR",
        "f_OtherResMech",

        "f_Site_Pre",
        "f_Site_Org",
        "f_Site_OrgName",
        "f_Site_Pos",
        "f_Comments",

        "f_ars_ampC",
        "f_ars_ESBL",
        "f_ars_CARB",
        "f_ars_ECIM",
        "f_ars_MCIM",
        "f_ars_EC_MCIM",
        "f_ars_MBL",
        "f_ars_BL",
        "f_ars_MR",
        "f_ars_mecA",
        "f_ars_ICR",
        "f_ars_Pre",
        "f_ars_Post",
        "f_ars_OrgCode",
        "f_ars_OrgName",
        "f_ars_ct_ctl",
        "f_ars_tz_tzl",
        "f_ars_cn_cni",
        "f_ars_ip_ipi",
        "f_ars_reco_Code",
        "f_ars_description",
        "f_ars_reco",

        "f_arsp_Encoder",
        "f_arsp_Enc_Lic",
        "f_arsp_Checker",
        "f_arsp_Chec_Lic",
        "f_arsp_Verifier",
        "f_arsp_Ver_Lic",
        "f_arsp_LabManager",
        "f_arsp_Lab_Lic",
        "f_arsp_Head",
        "f_arsp_Head_Lic",
        "f_Date_Accomplished_ARSP",

        "f_x_mrse",
        "f_x_mrsamrse",
        "f_x_entbac",
        "f_edta",
    ]

    # --------------------------------------------------
    # HEADER
    # --------------------------------------------------
    header = static_fields[:]

    for abx in sorted_antibiotics:
        header.extend([
            abx,
            f"{abx}_RIS",
            f"{abx}_RT",
            f"{abx}_RT_RIS",
        ])

    writer.writerow(header)

    # --------------------------------------------------
    # ROW DATA
    # --------------------------------------------------
    for final_obj in final_data_entries:

        row = [
            getattr(final_obj, field, "")
            for field in static_fields
        ]

        abx_data = {}

        for entry in final_obj.final_entries.all():

            # MAIN RESULT
            if entry.ab_Abx_code:
                code = entry.ab_Abx_code.upper()
                abx_data.setdefault(code, {})

                if entry.ab_Disk_value is not None or entry.ab_MIC_value is not None:
                    val = (
                        entry.ab_Disk_value
                        if entry.ab_Disk_value is not None
                        else f"{entry.ab_MIC_operand or ''}{entry.ab_MIC_value}"
                    )
                    ris = entry.ab_Disk_enRIS or entry.ab_MIC_enRIS

                    abx_data[code].update({
                        "VAL": val,
                        "RIS": ris,
                    })

            # RETEST RESULT
            if entry.ab_Retest_Abx_code:
                code = entry.ab_Retest_Abx_code.upper()
                abx_data.setdefault(code, {})

                if entry.ab_Retest_DiskValue is not None or entry.ab_Retest_MICValue is not None:
                    rt_val = (
                        entry.ab_Retest_DiskValue
                        if entry.ab_Retest_DiskValue is not None
                        else f"{entry.ab_Retest_MIC_operand or ''}{entry.ab_Retest_MICValue}"
                    )
                    rt_ris = entry.ab_Retest_Disk_enRIS or entry.ab_Retest_MIC_enRIS

                    abx_data[code].update({
                        "RT_VAL": rt_val,
                        "RT_RIS": rt_ris,
                    })

        # Expand antibiotic columns
        for abx in sorted_antibiotics:
            data = abx_data.get(abx, {})

            row.extend([
                data.get("VAL", ""),
                data.get("RIS", ""),
                data.get("RT_VAL", ""),
                data.get("RT_RIS", ""),
            ])

        writer.writerow(row)

    return response



@login_required(login_url="/login/")
def final_abxentry_view(request):
    """
    Displays ORDINARY (non-retest) antibiotic results
    from Final_AntibioticEntry grouped by accession number.
    """

    # Only FINAL antibiotic entries (exclude retest antibiotics)
    entries = (
        Final_AntibioticEntry.objects
        .filter(ab_Retest_Abx_code__isnull=True)
        .select_related("ab_idNum_f_referred")
    )

    abx_data = {}
    abx_codes = set()

    for entry in entries:
        final_obj = entry.ab_idNum_f_referred
        accession_no = final_obj.f_AccessionNo

        abx_code = entry.ab_Abx_code  # ordinary antibiotic only

        # Determine value (Disk preferred, else MIC)
        value = (
            entry.ab_Disk_value
            if entry.ab_Disk_value is not None
            else entry.ab_MIC_value
        )

        # RIS (prefer disk, else MIC)
        ris = (
            entry.ab_Disk_enRIS
            if entry.ab_Disk_enRIS
            else entry.ab_MIC_enRIS
        )

        operand = entry.ab_MIC_operand or None

        if accession_no not in abx_data:
            abx_data[accession_no] = {}

        if abx_code:
            abx_data[accession_no][abx_code] = {
                "value": value,
                "RIS": ris,
                "Operand": operand,
            }
            abx_codes.add(abx_code)

    context = {
        "abx_data": abx_data,
        "abx_codes": sorted(abx_codes),
    }

    return render(
        request,
        "home_final/AntibioticentryFinal.html",
        context
    )


@login_required(login_url="/login/")
def export_final_antibiotic_entries(request):
    """
    Export ALL Final_AntibioticEntry records to Excel
    aligned with Final_Data + Final_AntibioticEntry models.
    """

    objects = (
        Final_AntibioticEntry.objects
        .select_related("ab_idNum_f_referred")
        .all()
    )

    data = []

    for obj in objects:
        final = obj.ab_idNum_f_referred

        data.append({
            # ================= LINKED FINAL DATA =================
            "Final_AccessionNo": final.f_AccessionNo if final else None,
            "Final_Batch_Code": final.f_Batch_Code if final else None,
            "Final_Site_Name": final.f_Site_Name if final else None,
            "Final_Site_Org": final.f_Site_Org if final else None,
            "Final_ARS_Org": final.f_ars_OrgCode if final else None,

            ######### flag
            "Org_Flag": obj.ab_Org_Flag,
            "Abx_Flag": obj.ab_Abx_Flag,
            "Phenotype": obj.ab_Abx_Phenotype,


            # ================= ANTIBIOTIC META =================
            "Antibiotic": obj.ab_Antibiotic,
            "Abx_code": obj.ab_Abx_code,
            "Abx": obj.ab_Abx,
            "Disk_Abx": obj.ab_Disk_Abx,

            # ================= SENTINEL SITE RESULTS =================
            "Disk_value": obj.ab_Disk_value,
            "Disk_RIS": obj.ab_Disk_RIS,
            "Disk_enRIS": obj.ab_Disk_enRIS,

            "MIC_operand": obj.ab_MIC_operand,
            "MIC_value": obj.ab_MIC_value,
            "MIC_RIS": obj.ab_MIC_RIS,
            "MIC_enRIS": obj.ab_MIC_enRIS,

            "Alert_MIC": obj.ab_AlertMIC,
            "Alert_MIC_Value": obj.ab_Alert_val,

            # ================= BREAKPOINTS =================
            "R_breakpoint": obj.ab_R_breakpoint,
            "I_breakpoint": obj.ab_I_breakpoint,
            "SDD_breakpoint": obj.ab_SDD_breakpoint,
            "S_breakpoint": obj.ab_S_breakpoint,

            # ================= ARSRL / RETEST =================
            "Retest_Antibiotic": obj.ab_Retest_Antibiotic,
            "Retest_Abx_code": obj.ab_Retest_Abx_code,
            "Retest_Abx": obj.ab_Retest_Abx,

            "Retest_DiskValue": obj.ab_Retest_DiskValue,
            "Retest_Disk_RIS": obj.ab_Retest_Disk_RIS,
            "Retest_Disk_enRIS": obj.ab_Retest_Disk_enRIS,

            "Retest_MIC_operand": obj.ab_Retest_MIC_operand,
            "Retest_MICValue": obj.ab_Retest_MICValue,
            "Retest_MIC_RIS": obj.ab_Retest_MIC_RIS,
            "Retest_MIC_enRIS": obj.ab_Retest_MIC_enRIS,

            "Retest_Alert_MIC": obj.ab_Retest_AlertMIC,
            "Retest_Alert_Value": obj.ab_Retest_Alert_val,

            "Ret_R_breakpoint": obj.ab_Ret_R_breakpoint,
            "Ret_I_breakpoint": obj.ab_Ret_I_breakpoint,
            "Ret_SDD_breakpoint": obj.ab_Ret_SDD_breakpoint,
            "Ret_S_breakpoint": obj.ab_Ret_S_breakpoint,

            # ================= FLAGS =================
            "Org_Flag": obj.ab_Org_Flag,
            "Abx_Flag": obj.ab_Abx_Flag,
            "Phenotype_Flag": obj.ab_Abx_Phenotype,

            # ================= SYSTEM =================
            "Date_Uploaded": obj.ab_Date_uploaded_fd,
        })

    # ================= EXPORT =================
    df = pd.DataFrame(data)

    file_path = "Final_Antibiotic_Entries.xlsx"
    df.to_excel(file_path, index=False)

    return FileResponse(
        open(file_path, "rb"),
        as_attachment=True,
        filename="Final_Antibiotic_Entries.xlsx"
    )



######################### Autofill recommendatiaon



@require_GET
def get_recommendation_f_description(request):

    reco_code = request.GET.get("reco_code")

    if not reco_code:
        return JsonResponse({"description": ""})

    try:
        reco = Recommendation_items.objects.get(RecoCode=reco_code)
        return JsonResponse({"description": reco.Description})
    except Recommendation_items.DoesNotExist:
        return JsonResponse({"description": ""})



############### Emerging List


@login_required
def emerging_list_view(request):

    q = request.GET.get("q", "").strip()

    qs = Emerging_Table.fully_emerging()

    if q:
        qs = qs.filter(
            eme_Accession__icontains=q
        )

    qs = qs.order_by("-eme_spec_Date", "eme_Accession")

    paginator = Paginator(qs, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "projects/Emerging_List.html",
        {
            "page_obj": page_obj,
            "q": q,
        }
    )

########## for downloading


def is_blank(val):
    return val is None or val == ""


@login_required(login_url="/login/")
def download_emerging_list(request):


    emerging_qs = Emerging_Table.fully_emerging().select_related(
        "eme_primary_key"
    )

   #unique antibiotcs
    unique_abx_codes = set()

    abx_qs = Final_AntibioticEntry.objects.filter(
        ab_idNum_f_referred__in=emerging_qs.values_list(
            "eme_primary_key_id", flat=True
        )
    ).values_list("ab_Abx_code", "ab_Retest_Abx_code")

    for abx_code, rt_code in abx_qs:
        if abx_code:
            unique_abx_codes.add(abx_code)
        if rt_code:
            unique_abx_codes.add(rt_code)

    sorted_antibiotics = sorted(unique_abx_codes)


    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = (
        'attachment; filename="emerging_cases_wide.csv"'
    )
    response.write("\ufeff")  # UTF-8 BOM (Excel safe)

    writer = csv.writer(response)


    EXPORT_FIELDS = OrderedDict([
        ("eme_Site_Code",    "Site_Code"),
        ("eme_Accession",    "Accession_No"),
        ("eme_ReferralData", "Referral_Data"),
        ("eme_DateAdmis",    "Date_Admitted"),
        ("eme_Diagnosis",    "Diagnosis"),
        ("eme_Diag_ICD",     "Diagnosis_ICD"),
        ("eme_ars_Org",      "Organism"),

        ("eme_ars_Pre",      "ARS_Pre"),
        ("eme_ars_Post",     "ARS_Post"),

        ("eme_org_Grp",      "Organism_Group"),
        ("eme_org_Genus",    "Organism_Genus"),

        ("eme_spec_Num",     "Specimen_No"),
        ("eme_spec_Date",    "Specimen_Date"),
        ("eme_spec_Type",    "Specimen_Type"),
    ])


    header = list(EXPORT_FIELDS.values())

    #write headers
    for abx in sorted_antibiotics:
        header.extend([
            abx,
            f"{abx}_RIS",
            f"{abx}_RT",
            f"{abx}_RT_RIS",
        ])

    writer.writerow(header)

    #write rows
    for eme in emerging_qs:

        # ---- Static columns ----
        row = [
            getattr(eme, field, "")
            for field in EXPORT_FIELDS.keys()
        ]

        # ---- Antibiotic data ----
        abx_entries = Final_AntibioticEntry.objects.filter(
            ab_idNum_f_referred=eme.eme_primary_key
        )

        abx_data = {}

        for ab in abx_entries:

            ##3 initial result
            if ab.ab_Abx_code:
                code = ab.ab_Abx_code
                abx_data.setdefault(code, {})

                if not is_blank(ab.ab_Disk_value) or not is_blank(ab.ab_MIC_value):
                    val = (
                        ab.ab_Disk_value
                        if not is_blank(ab.ab_Disk_value)
                        else f"{ab.ab_MIC_operand or ''}{ab.ab_MIC_value}"
                    )
                    ris = ab.ab_Disk_enRIS or ab.ab_MIC_enRIS

                    abx_data[code].update({
                        "_Val": val,
                        "_RIS": ris,
                    })

            ## retest result
            if ab.ab_Retest_Abx_code:
                code = ab.ab_Retest_Abx_code
                abx_data.setdefault(code, {})

                if not is_blank(ab.ab_Retest_DiskValue) or not is_blank(ab.ab_Retest_MICValue):
                    rt_val = (
                        ab.ab_Retest_DiskValue
                        if not is_blank(ab.ab_Retest_DiskValue)
                        else f"{ab.ab_Retest_MIC_operand or ''}{ab.ab_Retest_MICValue}"
                    )
                    rt_ris = ab.ab_Retest_Disk_enRIS or ab.ab_Retest_MIC_enRIS

                    abx_data[code].update({
                        "RT_Val": rt_val,
                        "RT_RIS": rt_ris,
                    })

        #format into wide
        for abx in sorted_antibiotics:
            data = abx_data.get(abx, {})

            val = data.get("_Val", "")
            if isinstance(val, (int, float)):
                val = format(val, ".3f")

            rt_val = data.get("RT_Val", "")
            if isinstance(rt_val, (int, float)):
                rt_val = format(rt_val, ".3f")

            row.extend([
                val,
                data.get("_RIS", ""),
                rt_val,
                data.get("RT_RIS", ""),
            ])

        writer.writerow(row)

    return response


############# wgs overview


@login_required
def update_wgs_classification_inline(request, pk):
    if request.method == "POST":
        isolate = get_object_or_404(Final_Data, pk=pk)
        # update a few fields
        isolate.save()
        return JsonResponse({"status": "ok"})



# @login_required(login_url="/login/")
# def wgs_classification_view(request, pk):

#     isolate = get_object_or_404(Final_Data, pk=pk)

#     classification, created = Classification_Table.objects.get_or_create(
#         Class_idNumReferred=isolate,
#         defaults={
#             "Class_AccessionNo": isolate.f_AccessionNo,
#         }
#     )

#     if request.method == "POST":
#         form = FinalReferred_Form(request.POST, instance=isolate)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "WGS classification updated successfully.")
#             return redirect("wgs_classification_view", pk=pk)
#     else:
#         form = FinalReferred_Form(instance=isolate)

#     return render(
#         request,
#         "projects/wgs_review.html",
#         {
#             "form": form,
#             "isolates": isolate,
#         }
#     )


@login_required(login_url="/login/")
def wgs_classification_view(request, pk):
    isolate = get_object_or_404(Final_Data, pk=pk)

    wgs_project = (
        WGS_Project.objects
        .filter(Ref_Accession=isolate.f_AccessionNo)
        .first()
    )

    fastq = gambit = mlst = checkm2 = assembly = amrfinder = None

    if wgs_project:
        fastq = FastqSummary.objects.filter(
            FastQ_Accession=wgs_project.WGS_FastQ_Acc
        )

        gambit = Gambit.objects.filter(
            Gambit_Accession=wgs_project.WGS_Gambit_Acc
        )

        mlst = Mlst.objects.filter(
            Mlst_Accession=wgs_project.WGS_Mlst_Acc
        )

        checkm2 = Checkm2.objects.filter(
            Checkm2_Accession=wgs_project.WGS_Checkm2_Acc
        )

        assembly = AssemblyScan.objects.filter(
            Assembly_Accession=wgs_project.WGS_Assembly_Acc
        )

        amrfinder = Amrfinderplus.objects.filter(
            Amrfinder_Accession=wgs_project.WGS_Amrfinder_Acc
        )

    context = {
        "isolates": isolate,
        "wgs_project": wgs_project,

        # tool-specific datasets
        "fastq": fastq,
        "gambit": gambit,
        "mlst": mlst,
        "checkm2": checkm2,
        "assembly": assembly,
        "amrfinder": amrfinder,
    }

    return render(
        request,
        "projects/wgs_review.html",
        context
    )





########## CONCORDANCE ANALYSIS
# ================================
# RIS Extractors (PUT ABOVE VIEW)
# ================================

# =====================================================
# RIS HELPERS
# =====================================================

def get_site_ris(entry):
    if entry.ab_Disk_enRIS:
        return entry.ab_Disk_enRIS.strip().upper()
    if entry.ab_MIC_enRIS:
        return entry.ab_MIC_enRIS.strip().upper()
    return None


def get_ars_ris(entry):
    if entry.ab_Retest_Disk_enRIS:
        return entry.ab_Retest_Disk_enRIS.strip().upper()
    if entry.ab_Retest_MIC_enRIS:
        return entry.ab_Retest_MIC_enRIS.strip().upper()
    return None


########  CLASSIFY ID CONCORDANCE HELPER



def clean_str(val):
    """
    Safely convert any value to a lowercase string.
    Handles None, NaN, numbers, and Django model objects.
    """
    if val is None:
        return ""

    if pd.isna(val):
        return ""

    if hasattr(val, "Pre_Phenotypes"):
        return str(val.Pre_Phenotypes).strip().lower()

    return str(val).strip().lower()


def classify_id_concordance(site_org, ars_pre, ars_org):

    site = clean_str(site_org)
    ars = clean_str(ars_org)
    pre = clean_str(ars_pre)

    # Mixed Culture detection
    if "mixed culture of" in pre:
        return "M", "M"

    if ars == "not viable":
        return "N", "N"

    if site and ars and site == ars:
        return "G", "S"

    if site and ars and site != ars:
        return "X", "X"

    return None, None

# ==============================
# AST CONCORDANCE
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
        return "A", True

    if s == "R" and a == "S":
        return "B", True

    if "I" in {s, a}:
        return "C", True

    return None, False



@login_required(login_url="/login/")
def concordance_analysis_view(request):
    

    isolates = Final_Data.objects.prefetch_related("final_entries")

    total_isolates = isolates.count()

    # =============================
    # ORGANISM COUNTERS
    # =============================
    concordant_species = 0
    concordant_genus = 0
    different_org = 0
    mixed_count = 0
    not_viable_count = 0

    # =============================
    # AST COUNTERS
    # =============================
    total_pairs = 0
    concordant_pairs = 0
    vmd = 0
    md = 0
    minor = 0

    print("\n========== CONCORDANCE DEBUG START ==========\n")

    for isolate in isolates:

        print(f"\n--- Isolate {isolate.id} ({isolate.f_AccessionNo}) ---")

        # =============================
        # ORGANISM CONCORDANCE
        # =============================
        genus_con, species_con = classify_id_concordance(
            isolate.f_Site_OrgName,
            isolate.f_ars_Pre,
            isolate.f_ars_OrgName
        )

        if genus_con == "G":
            concordant_genus += 1

        if species_con == "S":
            concordant_species += 1

        if genus_con == "X":
            different_org += 1

        if genus_con == "M":
            mixed_count += 1

        if genus_con == "N":
            not_viable_count += 1

        print(
            f"Genus_Con={genus_con}, Species_Con={species_con}"
        )

        # =============================
        # AST CONCORDANCE
        # =============================
        entries = isolate.final_entries.all()

        site_results = {}
        ars_results = {}

        for entry in entries:

            antibiotic = entry.ab_Abx_code or entry.ab_Retest_Abx_code

            site_ris = get_site_ris(entry)
            ars_ris = get_ars_ris(entry)

            print(
                f"Entry {entry.id} | Abx={antibiotic} | "
                f"Site={site_ris} | ARS={ars_ris}"
            )

            if antibiotic and site_ris:
                site_results[antibiotic] = site_ris

            if antibiotic and ars_ris:
                ars_results[antibiotic] = ars_ris

        print("Site Results:", site_results)
        print("ARS Results:", ars_results)

        for antibiotic, site_ris in site_results.items():

            ars_ris = ars_results.get(antibiotic)

            if not ars_ris:
                print(f"Skipping {antibiotic} (no ARS match)")
                continue

            print(
                f"Comparing {antibiotic} → Site={site_ris} vs ARS={ars_ris}"
            )

            code, is_disc = classify_ast_deviation(site_ris, ars_ris)

            if not code:
                print("→ Skipped (invalid/ND)")
                continue

            total_pairs += 1

            if code == "S":
                concordant_pairs += 1
                print("→ Concordant")

            elif code == "A":
                vmd += 1
                print("→ Very Major")

            elif code == "B":
                md += 1
                print("→ Major")

            elif code == "C":
                minor += 1
                print("→ Minor")

    print("\n========== CONCORDANCE DEBUG END ==========\n")

    # =============================
    # RATE CALCULATIONS
    # =============================
    species_rate = round(
        (concordant_species / total_isolates) * 100, 2
    ) if total_isolates else 0

    genus_rate = round(
        (concordant_genus / total_isolates) * 100, 2
    ) if total_isolates else 0

    ast_concordance_rate = round(
        (concordant_pairs / total_pairs) * 100, 2
    ) if total_pairs else 0

    vmd_rate = round(
        (vmd / total_pairs) * 100, 2
    ) if total_pairs else 0

    md_rate = round(
        (md / total_pairs) * 100, 2
    ) if total_pairs else 0

    minor_rate = round(
        (minor / total_pairs) * 100, 2
    ) if total_pairs else 0

    context = {
        "total_isolates": total_isolates,

        # Organism
        "concordant_species": concordant_species,
        "species_rate": species_rate,

        "concordant_genus": concordant_genus,
        "genus_rate": genus_rate,

        "different_org": different_org,
        "mixed_count": mixed_count,
        "not_viable_count": not_viable_count,

        # AST
        "total_pairs": total_pairs,
        "concordant_pairs": concordant_pairs,
        "ast_concordance_rate": ast_concordance_rate,

        "vmd": vmd,
        "vmd_rate": vmd_rate,

        "md": md,
        "md_rate": md_rate,

        "minor": minor,
        "minor_rate": minor_rate,
        "isolates": isolates,

    }

    return render(
        request,
        "home_final/concordance_dashboard.html",
        context
    )




# this is per batch
@login_required(login_url="/login/")
@require_POST
@transaction.atomic
def concordance_generate_batch(request):

    batch_id = request.POST.get("batch_id")

    batch = get_object_or_404(Batch_Table, id=batch_id)

    isolates = (
        Final_Data.objects
        .filter(f_Batch_id=batch)
        .prefetch_related("final_entries")
    )

    total_isolates = isolates.count()

    total_pairs = 0
    concordant_pairs = 0
    vmd = 0
    md = 0
    minor = 0

    # =========================
    # GENUS / SPECIES COUNTERS
    # =========================
    genus_match = 0
    species_match = 0
    genus_discordant = 0
    mixed_count = 0
    not_viable_count = 0

    detail_objects = []

    for isolate in isolates:

        # ======================
        # ID CONCORDANCE
        # ======================
        genus_con, species_con = classify_id_concordance(
            isolate.f_Site_OrgName,
            isolate.f_ars_Pre,
            isolate.f_ars_OrgName
        )

        if genus_con == "G":
            genus_match += 1
        elif genus_con == "X":
            genus_discordant += 1
        elif genus_con == "M":
            mixed_count += 1
        elif genus_con == "N":
            not_viable_count += 1

        if species_con == "S":
            species_match += 1

        # ======================
        # AST COMPARISON
        # ======================
        site_results = {}
        ars_results = {}

        for entry in isolate.final_entries.all():

            site_ris = get_site_ris(entry)
            ars_ris = get_ars_ris(entry)

            if entry.ab_Abx_code and site_ris:
                site_results[entry.ab_Abx_code] = site_ris

            if entry.ab_Retest_Abx_code and ars_ris:
                ars_results[entry.ab_Retest_Abx_code] = ars_ris

        for antibiotic, site_ris in site_results.items():

            ars_ris = ars_results.get(antibiotic)
            if not ars_ris:
                continue

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

            detail_objects.append(
                ConcordanceDetail(
                    accession_no=isolate.f_AccessionNo,
                    isolate_id=isolate.id,
                    organism=isolate.f_Site_OrgName,
                    antibiotic=antibiotic,
                    site_ris=site_ris,
                    ars_ris=ars_ris,
                    deviation_code=code,
                    is_discordant=is_disc,
                    genus_con=genus_con,
                    species_con=species_con,
                )
            )

    viable = total_isolates - mixed_count - not_viable_count

    genus_rate = round((genus_match / viable) * 100, 2) if viable else 0
    species_rate = round((species_match / viable) * 100, 2) if viable else 0

    total_deviation = vmd + md + minor
    critical_deviation = vmd + md

    ast_concordance_rate = round(
        (concordant_pairs / total_pairs) * 100, 2
    ) if total_pairs else 0

    report, created = ConcordanceReport.objects.update_or_create(
        batch=batch,
        final_data=None,
        defaults={
            "created_by": request.user,
            "total_isolates": total_isolates,
            "total_pairs": total_pairs,
            "concordant_pairs": concordant_pairs,
            "vmd": vmd,
            "md": md,
            "minor": minor,
            "total_deviation": total_deviation,
            "critical_deviation": critical_deviation,
            "ast_concordance_rate": ast_concordance_rate,
            "genus_match": genus_match,
            "species_match": species_match,
            "genus_rate": genus_rate,
            "species_rate": species_rate,
        }
    )

    report.details.all().delete()

    for obj in detail_objects:
        obj.report = report

    ConcordanceDetail.objects.bulk_create(detail_objects)

    return redirect("concordance_batch_detail", report_id=report.id)





@login_required(login_url="/login/")
def concordance_batch_detail(request, report_id):

    report = get_object_or_404(
        ConcordanceReport.objects.select_related("batch", "created_by"),
        id=report_id,
        final_data__isnull=True
    )

    details = report.details.all().order_by("accession_no")

    context = {
        "report": report,
        "details": details,
        "is_batch_report": True,
    }

    return render(
        request,
        "home_final/concordance_batch_detail.html",
        context
    )



# this is per accession
@login_required(login_url="/login/")
@require_POST
@transaction.atomic
def concordance_generate_accession(request):

    isolate_id = request.POST.get("isolate_id")

    isolate = get_object_or_404(
        Final_Data.objects.prefetch_related("final_entries"),
        id=isolate_id
    )

    # ==========================
    # ORGANISM CONCORDANCE
    # ==========================
    genus_con, species_con = classify_id_concordance(
        isolate.f_Site_OrgName,
        isolate.f_ars_Pre,
        isolate.f_ars_OrgName
    )

    genus_match = 1 if genus_con == "G" else 0
    species_match = 1 if species_con == "S" else 0

    genus_rate = 100 if genus_con == "G" else 0
    species_rate = 100 if species_con == "S" else 0

    # ==========================
    # AST COMPARISON
    # ==========================
    total_pairs = 0
    concordant_pairs = 0
    vmd = 0
    md = 0
    minor = 0

    site_results = {}
    ars_results = {}
    detail_objects = []

    for entry in isolate.final_entries.all():

        site_ris = get_site_ris(entry)
        ars_ris = get_ars_ris(entry)

        if entry.ab_Abx_code and site_ris:
            site_results[entry.ab_Abx_code] = site_ris

        if entry.ab_Retest_Abx_code and ars_ris:
            ars_results[entry.ab_Retest_Abx_code] = ars_ris

    for antibiotic, site_ris in site_results.items():

        ars_ris = ars_results.get(antibiotic)
        if not ars_ris:
            continue

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

        detail_objects.append(
            ConcordanceDetail(
                accession_no=isolate.f_AccessionNo,
                isolate_id=isolate.id,
                organism=isolate.f_Site_OrgName,
                antibiotic=antibiotic,
                site_ris=site_ris,
                ars_ris=ars_ris,
                deviation_code=code,
                is_discordant=is_disc,
                genus_con=genus_con,
                species_con=species_con,
            )
        )

    total_deviation = vmd + md + minor
    critical_deviation = vmd + md

    ast_concordance_rate = round(
        (concordant_pairs / total_pairs) * 100, 2
    ) if total_pairs else 0

    report, created = ConcordanceReport.objects.update_or_create(
        final_data=isolate,
        defaults={
            "batch": isolate.f_Batch_id,
            "created_by": request.user,
            "total_isolates": 1,
            "total_pairs": total_pairs,
            "concordant_pairs": concordant_pairs,
            "vmd": vmd,
            "md": md,
            "minor": minor,
            "total_deviation": total_deviation,
            "critical_deviation": critical_deviation,
            "ast_concordance_rate": ast_concordance_rate,
            "genus_match": genus_match,
            "species_match": species_match,
            "genus_rate": genus_rate,
            "species_rate": species_rate,
        }
    )

    report.details.all().delete()

    for obj in detail_objects:
        obj.report = report

    ConcordanceDetail.objects.bulk_create(detail_objects)

    return redirect("concordance_accession_detail", report_id=report.id)



@login_required(login_url="/login/")
def concordance_accession_detail(request, report_id):

    report = get_object_or_404(
        ConcordanceReport.objects.select_related(
            "final_data", "batch", "created_by"
        ),
        id=report_id,
        final_data__isnull=False
    )

    details = report.details.all().order_by("antibiotic")

    context = {
        "report": report,
        "details": details,
        "isolate": report.final_data,
    }

    return render(
        request,
        "home_final/concordance_accession_detail.html",
        context
    )


### used when final data entry is updated to auto-regenerate snapshot for that accession
def regenerate_concordance_snapshot(isolate, user=None):
    """
    Auto-regenerates concordance snapshot using the unified engine.
    """

    from django.db import transaction

    genus_con, species_con = classify_id_concordance(
        isolate.f_Site_OrgName,
        isolate.f_ars_Pre,
        isolate.f_ars_OrgName
    )

    site_results = {}
    ars_results = {}

    for entry in isolate.final_entries.all():

        site_ris = get_site_ris(entry)
        ars_ris = get_ars_ris(entry)

        site_abx = entry.ab_Abx_code
        ars_abx = entry.ab_Retest_Abx_code

        if site_abx and site_ris:
            site_results[site_abx] = site_ris

        if ars_abx and ars_ris:
            ars_results[ars_abx] = ars_ris

    total_pairs = 0
    concordant_pairs = 0
    vmd = 0
    md = 0
    minor = 0

    detail_objects = []

    for antibiotic, site_ris in site_results.items():

        ars_ris = ars_results.get(antibiotic)
        if not ars_ris:
            continue

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

        detail_objects.append(
            ConcordanceDetail(
                accession_no=isolate.f_AccessionNo,
                isolate_id=isolate.id,
                organism=isolate.f_Site_OrgName,
                antibiotic=antibiotic,
                site_ris=site_ris,
                ars_ris=ars_ris,
                deviation_code=code,
                is_discordant=is_disc,
                genus_con=genus_con,
                species_con=species_con,
            )
        )

    total_deviation = vmd + md + minor
    critical_deviation = vmd + md

    ast_concordance_rate = round(
        (concordant_pairs / total_pairs) * 100, 2
    ) if total_pairs else 0

    critical_deviation_rate = round(
        (critical_deviation / total_pairs) * 100, 2
    ) if total_pairs else 0

    total_deviation_rate = round(
        (total_deviation / total_pairs) * 100, 2
    ) if total_pairs else 0

    with transaction.atomic():

        ConcordanceReport.objects.filter(
            batch=isolate.f_Batch_id,
            final_data__isnull=True
        ).delete()

        # Create fresh batch snapshot
        report = ConcordanceReport.objects.create(
            batch=isolate.f_Batch_id,
            created_by=user,
            total_isolates=1,
            total_pairs=total_pairs,
            concordant_pairs=concordant_pairs,
            vmd=vmd,
            md=md,
            minor=minor,
            total_deviation=total_deviation,
            critical_deviation=critical_deviation,
            ast_concordance_rate=ast_concordance_rate,
            critical_deviation_rate=critical_deviation_rate,
            total_deviation_rate=total_deviation_rate,
        )

        report.details.all().delete()

        for obj in detail_objects:
            obj.report = report

        ConcordanceDetail.objects.bulk_create(detail_objects)

    print("SNAPSHOT FULLY REGENERATED")


# =====================================================
# HISTORY VIEW
# =====================================================

@login_required(login_url="/login/")
def concordance_history_view(request):

    reports = (
        ConcordanceReport.objects
        .select_related("batch", "created_by")
        .order_by("-created_at")
    )

    return render(
        request,
        "home_final/concordance_history.html",
        {"reports": reports}
    )



@login_required(login_url="/login/")
def concordance_report_detail_view(request, report_id):

    report = get_object_or_404(
        ConcordanceReport.objects.select_related("batch", "created_by"),
        id=report_id
    )

    # Snapshot detail rows (AST comparison rows)
    details = report.details.all().order_by("isolate_id", "antibiotic")

    context = {
        "report": report,
        "details": details,
    }

    return render(
        request,
        "home_final/concordance_report_batch_detail.html",
        context
    )



@login_required(login_url="/login/")
def export_concordance_batch_excel(request, report_id):

    # 🔒 Ensure this is a BATCH report only
    report = get_object_or_404(
        ConcordanceReport.objects.select_related("batch"),
        id=report_id,
        final_data__isnull=True  # <--- IMPORTANT
    )

    batch = report.batch

    if not batch:
        return HttpResponse("Invalid batch report.", status=400)

    isolates = Final_Data.objects.filter(f_Batch_id=batch)

    total_isolates = isolates.count()

    site_name = isolates.first().f_Site_Name if isolates.exists() else ""
    referral_date = isolates.first().f_Referral_Date if isolates.exists() else ""

    ref_no = (
        isolates
        .exclude(f_RefNo__isnull=True)
        .exclude(f_RefNo__exact="")
        .values_list("f_RefNo", flat=True)
        .first()
    )

    accession_numbers = ref_no or ""

    # =====================================================
    # ORGANISM CONCORDANCE CALCULATION (LIVE)
    # =====================================================

    genus_match = 0
    species_match = 0
    different_org = 0
    mixed_count = 0
    nonviable_count = 0

    discordant_rows = []

    for isolate in isolates:

        site_org = (isolate.f_Site_OrgName or "").strip().lower()
        ars_org = (isolate.f_ars_OrgName or "").strip().lower()
        ars_pre = (isolate.f_ars_Pre or "").strip().lower()

        # Mixed Culture
        if ars_pre == "mixed culture":
            mixed_count += 1
            continue

        # Not Viable
        if ars_org == "not viable":
            nonviable_count += 1
            continue

        if site_org and ars_org:

            if site_org == ars_org:
                species_match += 1
                genus_match += 1

            elif site_org.split(" ")[0] == ars_org.split(" ")[0]:
                genus_match += 1

            else:
                different_org += 1
                discordant_rows.append([
                    isolate.f_RefNo,
                    isolate.f_Site_OrgName,
                    isolate.f_ars_OrgName
                ])

    viable_pure = total_isolates - mixed_count - nonviable_count

    genus_rate = round((genus_match / viable_pure) * 100, 2) if viable_pure else 0
    species_rate = round((species_match / viable_pure) * 100, 2) if viable_pure else 0

    # =====================================================
    # AST CALCULATIONS (FROM SNAPSHOT)
    # =====================================================

    total_pairs = report.total_pairs or 0
    concordant = report.concordant_pairs or 0
    vmd = report.vmd or 0
    md = report.md or 0
    minor = report.minor or 0

    total_deviation = vmd + md + minor

    concordance_rate = round((concordant / total_pairs) * 100, 2) if total_pairs else 0
    vmd_rate = round((vmd / total_pairs) * 100, 2) if total_pairs else 0
    total_deviation_rate = round((total_deviation / total_pairs) * 100, 2) if total_pairs else 0

    # =====================================================
    # WORKBOOK
    # =====================================================

    wb = Workbook()
    ws = wb.active
    ws.title = "Concordance Quality Report"

    # HEADER
    ws["A1"] = "Sentinel Site"
    ws["B1"] = site_name

    ws["A2"] = "Date of Referral"
    ws["B2"] = str(referral_date)

    ws["A3"] = "Accession Numbers"
    ws["B3"] = accession_numbers

    for row in range(1, 4):
        ws[f"A{row}"].font = Font(bold=True)

    # =====================================================
    # 1. QUALITY OF REFERRAL
    # =====================================================

    ws["A5"] = "1. QUALITY OF REFERRAL"
    ws["A5"].font = Font(bold=True)

    ws["A6"] = "1.1 Number of Isolates"
    ws["B6"] = total_isolates

    ws["A7"] = "1.2 Number of Nonviable Isolates"
    ws["B7"] = nonviable_count

    ws["A8"] = "1.3 Number of Mixed Cultures"
    ws["B8"] = mixed_count

    ws["A9"] = "1.4 Number of Viable and Pure Isolates"
    ws["B9"] = viable_pure

    # =====================================================
    # 2. ORGANISM IDENTIFICATION
    # =====================================================

    ws["A11"] = "2. ORGANISM IDENTIFICATION"
    ws["A11"].font = Font(bold=True)

    ws["A12"] = "2.1 Concordant ID Genus Level"
    ws["B12"] = ">= 96%"
    ws["C12"] = genus_match
    ws["D12"] = f"{genus_rate}%"

    ws["A13"] = "2.2 Concordant ID Species Level"
    ws["B13"] = ">= 90%"
    ws["C13"] = species_match
    ws["D13"] = f"{species_rate}%"

    ws["A14"] = "2.3 Different Identification"
    ws["C14"] = different_org

    # =====================================================
    # 3. AST RESULTS
    # =====================================================

    ws["A16"] = "3. AST RESULTS"
    ws["A16"].font = Font(bold=True)

    ws["A17"] = "3.1 Total Number of AST pairs analyzed"
    ws["C17"] = total_pairs

    ws["A18"] = "3.2 Concordant AST Results"
    ws["C18"] = concordant
    ws["D18"] = f"{concordance_rate}%"

    ws["A19"] = "A – Very Major Deviations"
    ws["C19"] = vmd
    ws["D19"] = f"{vmd_rate}%"

    ws["A20"] = "B – Major Deviations"
    ws["C20"] = md

    ws["A21"] = "C – Minor Deviations"
    ws["C21"] = minor

    ws["A22"] = "3.4 Critical Deviations (<=5%)"
    ws["C22"] = vmd

    ws["A23"] = "3.5 Total Deviations (<=8%)"
    ws["C23"] = total_deviation
    ws["D23"] = f"{total_deviation_rate}%"

    # Auto width
    for column in ws.columns:
        max_length = 0
        col_letter = column[0].column_letter
        for cell in column:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = max_length + 2

    filename = f"{batch.bat_Batch_Name}_Concordance.xlsx"

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    wb.save(response)
    return response






@login_required(login_url="/login/")
def export_concordance_accession_excel(request, report_id):

    # 🔒 Ensure this is an ACCESSION report only
    report = get_object_or_404(
        ConcordanceReport.objects.select_related("final_data"),
        id=report_id,
        final_data__isnull=False
    )

    isolate = report.final_data

    # =====================================================
    # ORGANISM CONCORDANCE (USING YOUR EXACT RULES)
    # =====================================================

    site_org = (isolate.f_Site_OrgName or "").strip().lower()
    ars_org = (isolate.f_ars_OrgName or "").strip().lower()
    ars_pre = (isolate.f_ars_Pre or "").strip().lower()

    if ars_pre == "mixed culture":
        genus_con = "M"
        species_con = "M"

    elif ars_org == "not viable":
        genus_con = "N"
        species_con = "N"

    elif site_org and ars_org and site_org == ars_org:
        genus_con = "G"
        species_con = "S"

    else:
        genus_con = "X"
        species_con = "X"

    # =====================================================
    # AST SNAPSHOT VALUES (FROM REPORT)
    # =====================================================

    total_pairs = report.total_pairs or 0
    concordant = report.concordant_pairs or 0
    vmd = report.vmd or 0
    md = report.md or 0
    minor = report.minor or 0

    total_deviation = vmd + md + minor

    concordance_rate = round((concordant / total_pairs) * 100, 2) if total_pairs else 0
    vmd_rate = round((vmd / total_pairs) * 100, 2) if total_pairs else 0
    total_deviation_rate = round((total_deviation / total_pairs) * 100, 2) if total_pairs else 0

    # =====================================================
    # WORKBOOK
    # =====================================================

    wb = Workbook()
    ws = wb.active
    ws.title = "Accession Concordance Report"

    # HEADER SECTION
    ws["A1"] = "Accession Number"
    ws["B1"] = isolate.f_AccessionNo

    ws["A1"] = "Sentinel Site"
    ws["B1"] = isolate.f_Site_Name

    ws["A3"] = "Date of Referral"
    ws["B3"] = str(isolate.f_Referral_Date)

    ws["A4"] = "Organism (Site)"
    ws["B4"] = isolate.f_Site_OrgName

    ws["A5"] = "Organism (ARSRL)"
    ws["B5"] = isolate.f_ars_OrgName

    for row in range(1, 6):
        ws[f"A{row}"].font = Font(bold=True)

    # =====================================================
    # 1. ORGANISM IDENTIFICATION
    # =====================================================

    ws["A7"] = "1. ORGANISM IDENTIFICATION"
    ws["A7"].font = Font(bold=True)

    ws["A8"] = "Genus Concordance"
    ws["B8"] = genus_con

    ws["A9"] = "Species Concordance"
    ws["B9"] = species_con

    # =====================================================
    # 2. AST RESULTS
    # =====================================================

    ws["A11"] = "2. AST RESULTS"
    ws["A11"].font = Font(bold=True)

    ws["A12"] = "Total AST pairs analyzed"
    ws["C12"] = total_pairs

    ws["A13"] = "Concordant Results"
    ws["C13"] = concordant
    ws["D13"] = f"{concordance_rate}%"

    ws["A14"] = "Very Major Deviations (A)"
    ws["C14"] = vmd
    ws["D14"] = f"{vmd_rate}%"

    ws["A15"] = "Major Deviations (B)"
    ws["C15"] = md

    ws["A16"] = "Minor Deviations (C)"
    ws["C16"] = minor

    ws["A17"] = "Total Deviations"
    ws["C17"] = total_deviation
    ws["D17"] = f"{total_deviation_rate}%"

    # =====================================================
    # DETAIL TABLE (FROM SNAPSHOT)
    # =====================================================

    ws["A19"] = "3. AST Detail Comparison"
    ws["A19"].font = Font(bold=True)

    headers = ["Antibiotic", "Site RIS", "ARS RIS", "Deviation"]

    for col_num, header in enumerate(headers, 1):
        ws.cell(row=20, column=col_num, value=header).font = Font(bold=True)

    row_index = 21

    for detail in report.details.all().order_by("antibiotic"):
        ws.cell(row=row_index, column=1, value=detail.antibiotic)
        ws.cell(row=row_index, column=2, value=detail.site_ris)
        ws.cell(row=row_index, column=3, value=detail.ars_ris)
        ws.cell(row=row_index, column=4, value=detail.deviation_code)
        row_index += 1

    # AUTO WIDTH
    for column in ws.columns:
        max_length = 0
        col_letter = column[0].column_letter
        for cell in column:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = max_length + 2

    filename = f"{isolate.f_AccessionNo}_Concordance.xlsx"

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    wb.save(response)
    return response






@login_required(login_url="/login/")
def export_concordance_report_pdf(request, report_id):

    report = get_object_or_404(
        ConcordanceReport.objects.select_related("batch"),
        id=report_id
    )

    batch = report.batch
    isolates = Final_Data.objects.filter(f_Batch_id=batch)

    total_isolates = isolates.count()

    site_name = isolates.first().f_Site_Name if isolates.exists() else ""
    referral_date = isolates.first().f_Referral_Date if isolates.exists() else ""
    refno = isolates.first().f_RefNo if isolates.exists() else ""

    # =====================================================
    # ORGANISM CONCORDANCE (LIVE CALCULATION)
    # =====================================================

    genus_match = 0
    species_match = 0
    different_org = 0
    mixed_count = 0
    nonviable_count = 0
    discordant_rows = []

    for isolate in isolates:

        site_org = (isolate.f_Site_OrgName or "").strip().lower()
        ars_org = (isolate.f_ars_OrgName or "").strip().lower()
        ars_pre = (isolate.f_ars_Pre or "").strip().lower()

        if "mixed culture" in ars_pre:
            mixed_count += 1
            continue

        if ars_org == "not viable":
            nonviable_count += 1
            continue

        if site_org and ars_org:

            if site_org == ars_org:
                species_match += 1
                genus_match += 1

            elif site_org.split(" ")[0] == ars_org.split(" ")[0]:
                genus_match += 1

            else:
                different_org += 1
                discordant_rows.append({
                    "refno": isolate.f_RefNo,
                    "site_org": isolate.f_Site_OrgName,
                    "ars_org": isolate.f_ars_OrgName
                })

    viable_pure = total_isolates - mixed_count - nonviable_count

    genus_rate = round((genus_match / viable_pure) * 100, 2) if viable_pure else 0
    species_rate = round((species_match / viable_pure) * 100, 2) if viable_pure else 0

    # =====================================================
    # AST CALCULATIONS (FROM SNAPSHOT)
    # =====================================================

    total_pairs = report.total_pairs or 0
    concordant = report.concordant_pairs or 0
    vmd = report.vmd or 0
    md = report.md or 0
    minor = report.minor or 0

    total_deviation = vmd + md + minor

    concordance_rate = round((concordant / total_pairs) * 100, 2) if total_pairs else 0
    vmd_rate = round((vmd / total_pairs) * 100, 2) if total_pairs else 0
    total_deviation_rate = round((total_deviation / total_pairs) * 100, 2) if total_pairs else 0

    # =====================================================
    # DISCORDANT ANTIBIOTIC SUMMARY
    # =====================================================

    details = report.details.all()

    from collections import defaultdict

    abx_summary = defaultdict(lambda: {
        "total": 0,
        "vmd": 0,
        "md": 0,
        "minor": 0
    })

    for row in details:
        if row.deviation_code != "Concordant":

            abx_summary[row.antibiotic]["total"] += 1

            if row.deviation_code == "Very Major":
                abx_summary[row.antibiotic]["vmd"] += 1
            elif row.deviation_code == "Major":
                abx_summary[row.antibiotic]["md"] += 1
            else:
                abx_summary[row.antibiotic]["minor"] += 1

    context = {
        "report": report,
        "site_name": site_name,
        "referral_date": referral_date,
        "refno": refno,
        "total_isolates": total_isolates,
        "mixed_count": mixed_count,
        "nonviable_count": nonviable_count,
        "viable_pure": viable_pure,
        "genus_match": genus_match,
        "species_match": species_match,
        "different_org": different_org,
        "genus_rate": genus_rate,
        "species_rate": species_rate,
        "discordant_rows": discordant_rows,
        "total_pairs": total_pairs,
        "concordant": concordant,
        "vmd": vmd,
        "md": md,
        "minor": minor,
        "concordance_rate": concordance_rate,
        "vmd_rate": vmd_rate,
        "total_deviation": total_deviation,
        "total_deviation_rate": total_deviation_rate,
        "abx_summary": dict(abx_summary),
        "now": datetime.now().strftime("%d %B %Y"),
    }

    template = get_template("home_final/concordance_report_pdf.html")
    html = template.render(context)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename=Batch_{report.batch.bat_Batch_Name}_Concordance.pdf'
    )

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse("PDF generation error", status=500)

    return response




