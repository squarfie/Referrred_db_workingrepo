from io import TextIOWrapper
import re
from venv import logger
from django.shortcuts import render
import os
from django.conf import settings
from django.templatetags.static import static
from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404 
from django.template import loader
from django.db.models import Prefetch
from decimal import Decimal, InvalidOperation

from apps.home.views import link_callback
from .models import *
from .forms import *

from apps.home.models import *
from apps.wgs_app.models import *
from apps.home.forms import *
from apps.wgs_app.forms import *


from django.contrib import messages
# imports for generating pdf
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.templatetags.static import static
from reportlab.lib.units import cm
# for paginator
from django.core.paginator import Paginator
# for dropdown items
from django.contrib import messages
#to auto generate clinic_code, egasp id and clinic
from django.http import JsonResponse, FileResponse
#for importation 
import pandas as pd
from django.utils import timezone
from django.db.models import Q
from django.utils.timezone import now
import csv
from django.utils.dateparse import parse_date
from datetime import datetime
from django.db import IntegrityError
from collections import OrderedDict, defaultdict
from django.db import transaction
from django.db.models import Count, Prefetch, Q, Case, When
from .utils import get_filtered_antibiotics, apply_final_breakpoints
from django.views.decorators.http import require_GET, require_POST




# SHOW FINAL DATA TABLE
@login_required(login_url="/login/")
def show_final_table(request):
    query = request.GET.get("q", "").strip()

    # DEFAULT SORT FIELD MUST EXIST
    sort_by = request.GET.get("sort", "f_Date_Modified")
    order = request.GET.get("order", "desc")

    # SAFETY: allow only valid sortable fields
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

    # BASE QUERYSET
    records = (
        Final_Data.objects
        .select_related("f_Spec_Type", "f_Batch_id")  # FK optimization
        .prefetch_related("final_entries")           # Antibiotics
        .order_by(sort_field)
    )

    # SEARCH LOGIC (ALIGNED WITH Final_Data)
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
            Q(f_Spec_Type__Specimen_code__icontains=query) |   # FK SAFE
            Q(f_Spec_Type__Specimen_name__icontains=query)
        ).distinct()

    # PAGINATION
    paginator = Paginator(records, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "home_final/tables_final.html",
        {
            "page_obj": page_obj,
            "current_sort": sort_by,
            "current_order": order,
            "query": query,
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
                entry.ab_Org_Flag = bp_disk.Emerging_Org_Flag
                entry.ab_Abx_Flag = bp_disk.Emerging_Abx_Flag
                entry.ab_Abx_Phenotype = bp_disk.Emerging_Pheno_Flag
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
                entry.ab_Org_Flag = bp_mic.Emerging_Org_Flag
                entry.ab_Abx_Flag = bp_mic.Emerging_Abx_Flag
                entry.ab_Abx_Phenotype = bp_mic.Emerging_Pheno_Flag
                entry.ab_Ret_R_breakpoint = bp_mic.R_val
                entry.ab_Ret_I_breakpoint = bp_mic.I_val
                entry.ab_Ret_SDD_breakpoint = bp_mic.SDD_val
                entry.ab_Ret_S_breakpoint = bp_mic.S_val
                entry.ab_Retest_Alert_val = bp_mic.Alert_val if alert_mic else ""
                ret_bp_applied = True

        if not ret_bp_applied:
            entry.ab_Ret_Org = None
            entry.ab_Org_Flag = None
            entry.ab_Abx_Flag = None
            entry.ab_Abx_Phenotype = None
            entry.ab_Ret_R_breakpoint = None
            entry.ab_Ret_I_breakpoint = None
            entry.ab_Ret_SDD_breakpoint = None
            entry.ab_Ret_S_breakpoint = None
            entry.ab_Retest_Alert_val = ""

        entry.save()

    messages.success(request, "Final data saved successfully.")
    return redirect("show_final_table")



###### old version might break in some cases 
# @login_required
# @transaction.atomic
# def upload_final_combined_table(request):

#     if request.method == "POST" and request.FILES.get("FinalDataFile"):
#         try:
#             uploaded_file = request.FILES["FinalDataFile"]
#             file_name = uploaded_file.name.lower()

#             # --- Load file ---
#             if file_name.endswith(".csv"):
#                 df = pd.read_csv(uploaded_file)
#             elif file_name.endswith((".xlsx", ".xls")):
#                 df = pd.read_excel(uploaded_file)
#             else:
#                 messages.error(request, "Unsupported file format.")
#                 return redirect("upload_final_combined_table")

#             # 🔒 DO NOT NORMALIZE — already model-ready
#             df.columns = [str(c).strip() for c in df.columns]

#             rows = df.to_dict("records")
#             model_fields = {f.name for f in Final_Data._meta.fields}

#             created = updated = 0

#             def parse_date(val):
#                 if not val or str(val).lower() in ["nan", "nat", "none"]:
#                     return None
#                 dt = pd.to_datetime(val, errors="coerce")
#                 return None if pd.isna(dt) else dt.date()

#             for row in rows:
#                 accession = str(row.get("f_AccessionNo", "")).strip()
#                 if not accession:
#                     continue   #  THIS WAS SKIPPING EVERYTHING BEFORE

#                 # Parse date fields safely
#                 for d in ["f_Referral_Date", "f_Spec_Date", "f_Date_Birth", "f_Date_Admis"]:
#                     if d in row:
#                         row[d] = parse_date(row[d])

#                 # Keep ONLY Final_Data fields
#                 clean_row = {
#                     k: v for k, v in row.items()
#                     if k in model_fields
#                 }

#                 obj, is_created = Final_Data.objects.update_or_create(
#                     f_AccessionNo=accession,
#                     defaults=clean_row
#                 )

#                 created += int(is_created)
#                 updated += int(not is_created)

#             messages.success(
#                 request,
#                 f"Upload complete! {created} created, {updated} updated."
#             )
#             return redirect("show_final_data")

#         except Exception as e:
#             import traceback
#             traceback.print_exc()
#             messages.error(request, f"Upload failed: {e}")

#     return render(request, "wgs_app/Add_wgs.html")


## new version aligns with the new final data model
@login_required
@transaction.atomic
def upload_final_combined_table(request):

    if request.method == "POST" and request.FILES.get("FinalDataFile"):
        try:
            uploaded_file = request.FILES["FinalDataFile"]
            file_name = uploaded_file.name.lower()

            # ================= LOAD FILE =================
            if file_name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            elif file_name.endswith((".xlsx", ".xls")):
                df = pd.read_excel(uploaded_file)
            else:
                messages.error(request, "Unsupported file format.")
                return redirect("upload_final_combined_table")

            # ================= PREP DATA =================
            # DO NOT NORMALIZE FIELD NAMES — final table is already model-aligned
            df.columns = [str(c).strip() for c in df.columns]
            rows = df.to_dict("records")

            model_fields = {f.name for f in Final_Data._meta.fields}

            # Fields that MUST NOT be overwritten
            IMMUTABLE_FIELDS = {
                "f_Date_of_Entry",
                "f_Date_Modified",
            }

            # Integer fields that must be normalized
            INT_FIELDS = {
                "f_Age",
                "f_bat_seq",
            }

            created = 0
            updated = 0

            # ================= HELPERS =================
            def parse_date(val):
                if not val or str(val).lower() in {"nan", "nat", "none", ""}:
                    return None
                dt = pd.to_datetime(val, errors="coerce")
                return None if pd.isna(dt) else dt.date()

            # ================= PROCESS ROWS =================
            for row in rows:

                accession = str(row.get("f_AccessionNo", "")).strip()
                batch_code = str(row.get("f_Batch_Code", "")).strip()

                # FINAL table REQUIRES both keys
                if not accession or not batch_code:
                    continue

                # ---- parse date fields safely
                for d in (
                    "f_Referral_Date",
                    "f_Spec_Date",
                    "f_Date_Birth",
                    "f_Date_Admis",
                ):
                    if d in row:
                        row[d] = parse_date(row[d])

                # ---- keep ONLY Final_Data fields
                clean_row = {
                    k: v for k, v in row.items()
                    if k in model_fields and k not in IMMUTABLE_FIELDS
                }

                # ---- normalize integers
                for f in INT_FIELDS:
                    if f in clean_row and str(clean_row[f]).strip() == "":
                        clean_row[f] = None

                # ---- NEVER assign FK blindly from uploads
                clean_row.pop("f_Batch_id", None)

                # ================= UPSERT =================
                obj, is_created = Final_Data.objects.update_or_create(
                    f_AccessionNo=accession,
                    f_Batch_Code=batch_code,
                    defaults=clean_row
                )

                created += int(is_created)
                updated += int(not is_created)

            messages.success(
                request,
                f"Upload complete! {created} created, {updated} updated."
            )
            return redirect("show_final_data")

        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f"Upload failed: {e}")
            return redirect("upload_final_combined_table")

    # ================= GET REQUEST =================
    return render(request, "wgs_app/Add_wgs.html")




@login_required
def show_final_data(request):
    finaldata_summaries = Final_Data.objects.all().order_by("f_Referral_Date")  # optional ordering

    total_records = Final_Data.objects.count()
     # Paginate the queryset to display 20 records per page
    paginator = Paginator(finaldata_summaries, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Render the template with paginated data
    return render(
        request,
        "home_final/show_final_data.html",
        {"page_obj": page_obj,
         "total_records": total_records,
         },  # only send page_obj
    )




@login_required
def delete_final_data(request, pk):
    final_item = get_object_or_404(Final_Data, pk=pk)

    if request.method == "POST":
        final_item.delete()
        messages.success(
            request,
            f"Record {final_item.f_AccessionNo} deleted successfully!"
        )
        return redirect('show_final_table')

    messages.error(request, "Invalid request for deletion.")
    return redirect('show_final_table')


@login_required
def delete_all_final_data(request):
    Final_Data.objects.all().delete()
    messages.success(request, "Final Referred Isolates have been deleted successfully.")
    return redirect('show_final_table')  # Redirect to the table view




@login_required
def delete_finaldata_by_date(request):
    if request.method == "POST":
        upload_date_str = request.POST.get("f_Date_Modified")
        print(" Received upload_date_str:", upload_date_str)

        if not upload_date_str:
            messages.error(request, "Please select an upload date to delete.")
            return redirect("show_final_data")

        # Use Django’s date parser
        upload_date = parse_date(upload_date_str)

        if not upload_date:
            messages.error(request, f"Invalid date format: {upload_date_str}")
            return redirect("show_final_data")

        deleted_count, _ = Final_Data.objects.filter(Date_uploaded_fd=upload_date).delete()
        messages.success(request, f" Deleted {deleted_count} Final Isolates records uploaded on {upload_date}.")
        return redirect("show_final_table")

    messages.error(request, "Invalid request method.")
    return redirect("show_final_table")




#### Helpers for Antitbiocs upload and display
########### still not working the way I want

DISK_PATTERN = re.compile(r"^([A-Z0-9]+_ND[\d.]+)$")
MIC_PATTERN  = re.compile(r"^([A-Z0-9]+_NM)$")


def is_disk_column(col):
    return bool(DISK_PATTERN.match(col))


def is_mic_column(col):
    return bool(MIC_PATTERN.match(col))


def extract_whonet_abx(col):
    """
    Returns exact WHONET_ABX used in BreakpointsTable
    Examples:
        AMP_ND30 → AMP_ND30
        AMP_NM   → AMP_NM
    """
    return col.strip().upper()

def wide_to_long_antibiotics(df):
    """
    Converts raw uploaded Excel into LONG format.
    One row = one antibiotic test.
    """

    long_rows = []

    meta_cols = {"f_AccessionNo", "Year", "f_ars_OrgCode"}

    for _, row in df.iterrows():

        accession = str(row["f_AccessionNo"]).strip()
        year = str(row["Year"]).split(".")[0].strip()
        org  = str(row["f_ars_OrgCode"]).strip().lower()

        for col in df.columns:

            if col in meta_cols:
                continue
            if col.endswith("_RIS") or col.endswith("_OP"):
                continue

            raw_val = row[col]
            if pd.isna(raw_val) or str(raw_val).strip() == "":
                continue

            is_disk = is_disk_column(col)
            is_mic  = is_mic_column(col)

            if not (is_disk or is_mic):
                continue

            whonet_abx = extract_whonet_abx(col)

            # -------------------------
            # Parse value
            # -------------------------
            raw_str = str(raw_val).strip()
            operand = ""
            value = None

            try:
                if is_mic:
                    m = re.match(r"^(<=|>=|<|>)?\s*([\d.]+)$", raw_str)
                    if not m:
                        continue
                    operand = m.group(1) or ""
                    value = float(m.group(2))
                else:
                    value = int(float(raw_str))
            except Exception:
                continue

            ris = str(row.get(f"{col}_RIS", "")).strip().upper()

            long_rows.append({
                "AccessionNo": accession,
                "Year": year,
                "Org": org,
                "Whonet_Abx": whonet_abx,
                "Method": "DISK" if is_disk else "MIC",
                "Value": value,
                "Operand": operand,
                "RIS": ris,
            })

    return pd.DataFrame(long_rows)



def select_breakpoint(*, whonet_abx, org, year, is_disk):
    """
    Canonical breakpoint selector
    """

    if not whonet_abx or not year:
        return None

    test_method = "DISK" if is_disk else "MIC"

    qs = (
        BreakpointsTable.objects
        .filter(
            Whonet_Abx=whonet_abx,
            Year=str(year),
            Test_Method=test_method,
        )
        .filter(
            Q(Org__iexact=org) |
            Q(Org="")
        )
        .order_by(
            Case(
                When(Org__iexact=org, then=0),
                When(Org="", then=1),
                default=2,
            )
        )
    )

    return qs.first()

############# end of helpers
@login_required
@transaction.atomic
def upload_antibiotic_entries(request):

    if request.method != "POST" or "FinalAntibioticFile" not in request.FILES:
        messages.error(request, "No file uploaded.")
        return redirect("show_final_antibiotic")

    try:
        uploaded_file = request.FILES["FinalAntibioticFile"]

        # --------------------------------------------------
        # LOAD FILE
        # --------------------------------------------------
        if uploaded_file.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # --------------------------------------------------
        # REQUIRED COLUMNS
        # --------------------------------------------------
        required = {"f_AccessionNo", "Year", "f_ars_OrgCode"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # --------------------------------------------------
        # WIDE → LONG (THIS IS THE KEY FIX)
        # --------------------------------------------------
        long_df = wide_to_long_antibiotics(df)

        if long_df.empty:
            messages.warning(request, "No antibiotic data found in file.")
            return redirect("show_final_antibiotic")

        # --------------------------------------------------
        # PREFETCH Final_Data
        # --------------------------------------------------
        accessions = long_df["AccessionNo"].unique()

        ref_map = {
            r.f_AccessionNo: r
            for r in Final_Data.objects.filter(
                f_AccessionNo__in=accessions
            )
        }

        created = updated = 0

        # --------------------------------------------------
        # SAVE LONG FORMAT ROWS
        # --------------------------------------------------
        for _, row in long_df.iterrows():

            accession = row["AccessionNo"]
            ref = ref_map.get(accession)
            if not ref:
                continue

            is_disk = row["Method"] == "DISK"
            is_mic  = row["Method"] == "MIC"

            obj, created_flag = Final_AntibioticEntry.objects.update_or_create(
                ab_idNum_f_referred=ref,
                ab_Abx_code=row["Whonet_Abx"],
                defaults={
                    "ab_AccessionNo": accession,
                    "ab_Year": row["Year"],
                    "ab_Org": row["Org"],

                    # Identification (signal will fill these)
                    "ab_Antibiotic": None,
                    "ab_Abx": row["Whonet_Abx"].split("_")[0],

                    # Method
                    "ab_Ret_Disk_Abx": is_disk,

                    # DISK
                    "ab_Retest_DiskValue": row["Value"] if is_disk else None,
                    "ab_Retest_Disk_enRIS": row["RIS"] if is_disk else "",

                    # MIC
                    "ab_Retest_MICValue": row["Value"] if is_mic else None,
                    "ab_Retest_MIC_operand": row["Operand"] if is_mic else "",
                    "ab_Retest_MIC_enRIS": row["RIS"] if is_mic else "",
                }
            )

            created += int(created_flag)
            updated += int(not created_flag)

        messages.success(
            request,
            f"Processed {created + updated} antibiotic entries "
            f"({created} created, {updated} updated)."
        )

        return redirect("show_final_antibiotic")

    except Exception as e:
        import traceback
        traceback.print_exc()
        messages.error(request, f"Upload Error: {e}")
        return redirect("show_final_antibiotic")



# updated version
@login_required
def show_final_antibiotic(request):

    entries = (
        Final_AntibioticEntry.objects
        .select_related("ab_idNum_f_referred")
        .order_by("ab_idNum_f_referred__f_AccessionNo")
    )

    abx_data = {}
    abx_columns = set()

    for entry in entries:

        # Skip invalid entries
        if not entry.ab_Abx_code or not entry.ab_idNum_f_referred:
            continue

        acc = entry.ab_idNum_f_referred.f_AccessionNo
        abx_code = entry.ab_Abx_code.strip().upper()

        # Column naming (value / operand / RIS)
        col_value = abx_code
        col_op    = f"{abx_code}_OP"
        col_ris   = f"{abx_code}_RIS"

        abx_columns.update([col_value, col_op, col_ris])

        if acc not in abx_data:
            abx_data[acc] = {}

        # Determine MIC vs DISK based on actual data
        if entry.ab_MIC_value is not None:
            abx_data[acc][col_value] = entry.ab_MIC_value or ""
            abx_data[acc][col_op]    = entry.ab_MIC_operand or ""
            abx_data[acc][col_ris]   = entry.ab_MIC_enRIS or ""
        else:
            abx_data[acc][col_value] = entry.ab_Disk_value or ""
            abx_data[acc][col_op]    = ""
            abx_data[acc][col_ris]   = entry.ab_Disk_enRIS or ""

    # Sort antibiotic columns consistently
    abx_columns = sorted(abx_columns)

    # Pagination (per accession)
    paginated_list = list(abx_data.items())
    paginator = Paginator(paginated_list, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "home_final/show_final_antibiotic.html",
        {
            "page_obj": page_obj,
            "abx_data": dict(page_obj.object_list),
            "abx_codes": abx_columns,
            "total_records": len(abx_data),  # number of isolates
        }
    )




### updated version
@login_required
def delete_final_antibiotic(request, pk):

    target = get_object_or_404(Final_AntibioticEntry, pk=pk)
    acc = target.ab_idNum_f_referred.f_AccessionNo

    if request.method == "POST":
        Final_AntibioticEntry.objects.filter(
            ab_idNum_f_referred__f_AccessionNo=acc
        ).delete()

        messages.success(
            request,
            f"All final antibiotic records for accession {acc} deleted successfully!"
        )
        return redirect("show_final_antibiotic")

    messages.error(request, "Invalid request method.")
    return redirect("show_final_antibiotic")



@login_required
def delete_all_final_antibiotic(request):
    Final_AntibioticEntry.objects.all().delete()
    messages.success(request, "Final Referred Isolates have been deleted successfully.")
    return redirect('show_final_antibiotic')  # Redirect to the table view





#### updated version
@login_required
def delete_finalantibiotic_by_date(request):

    if request.method == "POST":
        upload_date_str = request.POST.get("upload_date")

        if not upload_date_str:
            messages.error(request, "Please select an upload date to delete.")
            return redirect("show_final_antibiotic")

        upload_date = parse_date(upload_date_str)

        if not upload_date:
            messages.error(request, f"Invalid date format: {upload_date_str}")
            return redirect("show_final_antibiotic")

        deleted_count, _ = Final_AntibioticEntry.objects.filter(
            ab_Date_uploaded_fd=upload_date
        ).delete()

        messages.success(
            request,
            f"Deleted {deleted_count} Final Antibiotic entries uploaded on {upload_date}."
        )
        return redirect("show_final_antibiotic")

    messages.error(request, "Invalid request method.")
    return redirect("show_final_antibiotic")


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
    MAX_ROWS = 2

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
