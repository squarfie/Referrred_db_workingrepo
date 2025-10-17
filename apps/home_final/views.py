from io import TextIOWrapper
import re
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
from collections import defaultdict
from django.db import transaction
from django.db.models import Count, Prefetch, Q


# Create your views here.
@login_required(login_url="/login/")
def edit_final_data(request, id):
    # --- Fetch antibiotics lists ---
    whonet_abx_data = BreakpointsTable.objects.filter(Show=True)
    whonet_retest_data = BreakpointsTable.objects.filter(Retest=True)

    # --- Get the isolate record ---
    isolates = get_object_or_404(Final_Data, pk=id)

    # Fetch all entries in one query
    all_entries = Final_AntibioticEntry.objects.filter(ab_idNum_f_referred=isolates)

    # Separate them based on the 'retest' condition
    existing_entries = all_entries.filter(ab_Abx_code__isnull=False)  # Regular entries
    retest_entries = all_entries.filter(ab_Retest_Abx_code__isnull=False)   # Retest entries

    # --- Handle GET request ---
    if request.method == "GET":
        form = Referred_Form(instance=isolates)
        return render(request, "home/Referred_form_final.html", {
            "form": form,
            "whonet_abx_data": whonet_abx_data,
            "whonet_retest_data": whonet_retest_data,
            "edit_mode": True,
            "isolates": isolates,
            "existing_entries": existing_entries,
            "retest_entries": retest_entries,

        })

    # --- Handle POST request ---
    elif request.method == "POST":
        form = Referred_Form(request.POST, instance=isolates)

        if form.is_valid():
            isolates = form.save(commit=False)
            isolates.save()

            
            # --- Handle main antibiotics ---
            for entry in whonet_abx_data:
                abx_code = (entry.Whonet_Abx or "").strip().upper()
                disk_value = request.POST.get(f"disk_{entry.id}") or ""
                disk_enris = (request.POST.get(f"disk_enris_{entry.id}") or "").strip()
                mic_value = request.POST.get(f"mic_{entry.id}") or ""
                mic_enris = (request.POST.get(f"mic_enris_{entry.id}") or "").strip()
                mic_operand = (request.POST.get(f"mic_operand_{entry.id}") or "").strip()
                alert_mic = f"alert_mic_{entry.id}" in request.POST

                try:
                    disk_value = int(disk_value) if disk_value.strip() else None
                except ValueError:
                    disk_value = None

                
                # Debugging: Print the values before saving
                print(f"Saving values for Antibiotic Entry {entry.id}:", {
                    'mic_operand': mic_operand,
                    'disk_value': disk_value,
                    'disk_enris': disk_enris,
                    'mic_value': mic_value,
                    'mic_enris': mic_enris,
                })

                # Get or update antibiotic entry
                antibiotic_entry, created = Final_AntibioticEntry.objects.update_or_create(
                    ab_idNum_f_referred=isolates,
                    ab_Abx_code=abx_code,
                    defaults={
                        "ab_AccessionNo": isolates.f_AccessionNo,
                        "ab_Antibiotic": entry.Antibiotic,
                        "ab_Abx": entry.Abx_code,
                        "ab_Disk_value": disk_value,
                        "ab_Disk_enRIS": disk_enris,
                        "ab_MIC_value": mic_value or None,
                        "ab_MIC_enRIS": mic_enris,
                        "ab_MIC_operand": mic_operand,
                        "ab_R_breakpoint": entry.R_val or None,
                        "ab_I_breakpoint": entry.I_val or None,
                        "ab_SDD_breakpoint": entry.SDD_val or None,
                        "ab_S_breakpoint": entry.S_val or None,
                        "ab_AlertMIC": alert_mic,
                        "ab_Alert_val": entry.Alert_val if alert_mic else '',
                    }
                )

                antibiotic_entry.ab_breakpoints_id.set([entry])

            # Separate loop for Retest Data
            for retest in whonet_retest_data:
                retest_abx_code = retest.Whonet_Abx

                # Fetch user input values for MIC and Disk
                if retest.Disk_Abx:
                    retest_disk_value = request.POST.get(f'retest_disk_{retest.id}')
                    retest_disk_enris = request.POST.get(f"retest_disk_enris_{retest.id}") or ""
                    retest_mic_value = ''
                    retest_mic_enris = ''
                    retest_mic_operand = ''
                    retest_alert_mic = False
                else:
                    retest_mic_value = request.POST.get(f'retest_mic_{retest.id}')
                    retest_mic_enris = request.POST.get(f"retest_mic_enris_{retest.id}") or ""
                    retest_mic_operand = request.POST.get(f'retest_mic_operand_{retest.id}')
                    retest_alert_mic = f'retest_alert_mic_{retest.id}' in request.POST
                    retest_disk_value = ''
                    retest_disk_enris = ''

                # Check and update retest mic_operand if needed
                retest_disk_enris = (retest_disk_enris or '').strip() # Ensure it's a string and strip whitespace
                retest_mic_enris = (retest_mic_enris or '').strip()
                retest_mic_operand = (retest_mic_operand or '').strip()
                
                # Convert `retest_disk_value` safely
                retest_disk_value = int(retest_disk_value) if retest_disk_value and retest_disk_value.strip().isdigit() else None

                # Debugging: Print the values before saving
                print(f"Saving values for Retest Entry {retest.id}:", {
                    'retest_mic_operand': retest_mic_operand,
                    'retest_disk_value': retest_disk_value,
                    'retest_disk_enris': retest_disk_enris,
                    'retest_mic_value': retest_mic_value,
                    'retest_mic_enris': retest_mic_enris,
                    'retest_alert_mic': retest_alert_mic,
                    'retest_alert_val': retest.Alert_val if retest_alert_mic else '',
                })

                # Get or update retest antibiotic entry
                retest_entry, created = Final_AntibioticEntry.objects.update_or_create(
                    ab_idNum_f_referred=isolates,
                    ab_Retest_Abx_code=retest_abx_code,
                    defaults={
                        "ab_Retest_DiskValue": retest_disk_value,
                        "ab_Retest_Disk_enRIS": retest_disk_enris,
                        "ab_Retest_MICValue": retest_mic_value or None,
                        "ab_Retest_MIC_enRIS": retest_mic_enris,
                        "ab_Retest_MIC_operand": retest_mic_operand,
                        "ab_Retest_Antibiotic": retest.Antibiotic,
                        "ab_Retest_Abx": retest.Abx_code,
                        "ab_Ret_R_breakpoint": retest.R_val or None,
                        "ab_Ret_S_breakpoint": retest.S_val or None,
                        "ab_Ret_SDD_breakpoint": retest.SDD_val or None,
                        "ab_Ret_I_breakpoint": retest.I_val or None,
                        "ab_Retest_AlertMIC": retest_alert_mic,
                        "ab_Retest_Alert_val": retest.Alert_val if retest_alert_mic else "",
                    }
                )

                retest_entry.ab_breakpoints_id.set([retest])

            messages.success(request, "Data saved successfully.")
            return redirect("show_data")
        else:
            messages.error(request, "Error: Saving unsuccessful")
            print(form.errors)

    # --- fallback GET render in case POST fails ---
    form = FinalReferred_Form(instance=isolates)
    existing_entries = Final_AntibioticEntry.objects.filter(ab_idNum_f_referred=isolates)
    return render(request, "home/Referred_form_final.html", {
        "form": form,
        "whonet_abx_data": whonet_abx_data,
        "whonet_retest_data": whonet_retest_data,
        "edit_mode": True,
        "isolates": isolates,
        "existing_entries": existing_entries,
        "retest_entries": retest_entries,

    })


@login_required
@transaction.atomic
def upload_final_combined_table(request):
    form = WGSProjectForm()
    referred_form = FinalDataUploadForm()

    if request.method == "POST" and request.FILES.get("FinalDataFile"):
        try:
            uploaded_file = request.FILES["FinalDataFile"]
            file_name = uploaded_file.name.lower()

            ###### load file
            if file_name.endswith(".csv"):
                wrapper = TextIOWrapper(uploaded_file.file, encoding="utf-8-sig")
                df = pd.read_csv(wrapper)
            elif file_name.endswith((".xlsx", ".xls")):
                df = pd.read_excel(uploaded_file)
            else:
                messages.error(request, "Unsupported file format. Please upload CSV or Excel.")
                return redirect("upload_final_combined_table")

            # If file is transposed (samples as columns)
            if df.shape[0] < df.shape[1] and "accession_no" not in [c.lower() for c in df.columns]:
                df = df.transpose()
                df.columns = df.iloc[0].astype(str)
                df = df.iloc[1:].reset_index(drop=True)

            # Normalize headers
            original_columns = list(df.columns)
            df = df.rename(columns=lambda c: str(c).strip())
            rows = df.to_dict("records")

            # --- Setup & helpers ---
            site_codes = set(SiteData.objects.values_list("SiteCode", flat=True))
            model_fields = {f.name for f in Final_Data._meta.get_fields()}
            known_abx = set(BreakpointsTable.objects.values_list("Whonet_Abx", flat=True))

            created_ref = updated_ref = created_abx = updated_abx = 0

            FIELD_MAP = {
                "accession_no": "f_AccessionNo",
                "accessionno": "f_AccessionNo",
                "accession": "f_AccessionNo",
                "batch_code": "f_Batch_Code",
                "batch_name": "f_Batch_Name",
                "site_code": "f_SiteCode",
                "sitecode": "f_SiteCode",
                "batchno": "f_BatchNo",
                "total_batch": "f_Total_batch",
                "refno": "f_RefNo",
                "referral_date": "f_Referral_Date",
                "patient_id": "f_Patient_ID",
                "first_name": "f_First_Name",
                "mid_name": "f_Mid_Name",
                "last_name": "f_Last_Name",
                "date_birth": "f_Date_Birth",
                "age": "f_Age",
                "sex": "f_Sex",
                "date_admis": "f_Date_Admis",
                "nosocomial": "f_Nosocomial",
                "diagnosis": "f_Diagnosis",
                "diagnosis_icd10": "f_Diagnosis_ICD10",
                "ward": "f_Ward",
                "ward_type": "f_Ward_Type",
                "service_type": "f_Service_Type",
                "spec_num": "f_Spec_Num",
                "spec_date": "f_Spec_Date",
                "spec_type": "f_Spec_Type",
                "reason": "f_Reason",
                "growth": "f_Growth",
                "urine_colct": "f_Urine_ColCt",
                "comments": "f_Comments",
                "recommendation": "f_ars_reco",
            }

            def normalize_header(h):
                if h is None:
                    return ""
                key = re.sub(r"[\s\-_]+", "_", str(h).strip().lower())
                return FIELD_MAP.get(key, key)

            def parse_final_date(val):
                if val is None:
                    return None
                if isinstance(val, (pd.Timestamp, datetime)):
                    try:
                        return val.date()
                    except Exception:
                        return None
                s = str(val).strip()
                if s in ("", "nan", "NaT", "None", "none"):
                    return None
                try:
                    dt = pd.to_datetime(s, errors="coerce")
                    if pd.isna(dt):
                        return None
                    return dt.date()
                except Exception:
                    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y", "%b %d, %Y", "%B %d, %Y", "%m/%d/%Y", "%Y/%m/%d"):
                        try:
                            return datetime.strptime(s, fmt).date()
                        except Exception:
                            continue
                return None

            def parse_mic_value(value_str):
                if value_str is None:
                    return "", None
                s = str(value_str).strip()
                if s == "" or s.lower() in ("na", "nd", "nan", "n/a"):
                    return "", None
                m = re.match(r"^([<>≤≥=]+)?\s*([\d.]+)$", s)
                if m:
                    op = m.group(1) or ""
                    try:
                        val = float(m.group(2))
                    except Exception:
                        val = None
                    return op, val
                digit = re.search(r"([\d.]+)", s)
                if digit:
                    try:
                        return "", float(digit.group(1))
                    except Exception:
                        return "", None
                return "", None

            def extract_site_code_from_accession(acc):
                if not acc:
                    return ""
                s = str(acc)
                for code in site_codes:
                    if re.search(rf"\b{re.escape(code)}\b", s, flags=re.IGNORECASE):
                        return code
                return ""

            header_map = {normalize_header(orig): orig for orig in original_columns}

            # --- process rows ---
            for raw_row in rows:
                if not any([v is not None and str(v).strip() != "" for v in raw_row.values()]):
                    continue

                cleaned_row = {norm_key: raw_row.get(orig_col, "") for norm_key, orig_col in header_map.items()}

                accession = cleaned_row.get("f_AccessionNo") or cleaned_row.get("accession_no") or cleaned_row.get("accessionno") or cleaned_row.get("accession")
                if not accession or str(accession).strip() == "":
                    continue
                accession = str(accession).strip()

                site_code = extract_site_code_from_accession(accession)
                batch_name_val = cleaned_row.get("f_Batch_Name") or cleaned_row.get("batch_name") or ""
                batch_match = re.search(r"(\d+)\.(\d+)", str(batch_name_val)) if batch_name_val else None
                ref_range_match = re.search(r"(\d{4}-\d{4})", str(batch_name_val)) if batch_name_val else None
                batch_no = batch_match.group(1) if batch_match else ""
                total_batch = batch_match.group(2) if batch_match else ""
                ref_range = ref_range_match.group(1) if ref_range_match else ""

                date_fields_to_map = {
                    "f_Referral_Date": cleaned_row.get("f_Referral_Date") or cleaned_row.get("referral_date"),
                    "f_Spec_Date": cleaned_row.get("f_Spec_Date") or cleaned_row.get("spec_date"),
                    "f_Date_Birth": cleaned_row.get("f_Date_Birth") or cleaned_row.get("date_birth"),
                    "f_Date_Admis": cleaned_row.get("f_Date_Admis") or cleaned_row.get("date_admis"),
                }
                parsed_dates = {k: parse_final_date(v) for k, v in date_fields_to_map.items()}

                defaults = {}
                for norm_key, orig_col in header_map.items():
                    mapped_field = norm_key if norm_key.startswith("f_") else FIELD_MAP.get(norm_key)
                    if not mapped_field or mapped_field not in model_fields:
                        continue
                    val = cleaned_row.get(norm_key)
                    if mapped_field in parsed_dates:
                        defaults[mapped_field] = parsed_dates.get(mapped_field, None)
                    else:
                        defaults[mapped_field] = None if (val is None or (isinstance(val, float) and pd.isna(val))) else val

                defaults["f_SiteCode"] = site_code or defaults.get("f_SiteCode", "")
                defaults["f_BatchNo"] = batch_no or defaults.get("f_BatchNo", "")
                defaults["f_Total_batch"] = total_batch or defaults.get("f_Total_batch", "")
                if ref_range:
                    defaults["f_RefNo"] = ref_range

                # --- FIX: fill required fields with safe placeholders ---
                for req_field in ["f_Ward_Type", "f_Nosocomial", "f_Mid_Name"]:
                    if req_field not in defaults or defaults[req_field] in [None, "", "nan", "NaT"]:
                        defaults[req_field] = "Unknown"

                try:
                    ref_obj, created = Final_Data.objects.update_or_create(
                        f_AccessionNo=accession,
                        defaults=defaults
                    )
                except Exception as e:
                    print(f"[upload_final_combined_table] Failed saving accession {accession}: {e}")
                    continue

                if created:
                    created_ref += 1
                else:
                    updated_ref += 1

            messages.success(
                request,
                f"Upload complete! {created_ref} new Final_Data, {updated_ref} updated."
            )
            return redirect("show_final_data")

        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f"⚠️ Error: {e}")

    return render(request, "wgs_app/Add_wgs.html", {
        "referred_form": referred_form,
        "form": form,
    })




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
        "wgs_app/show_final_data.html",
        {"page_obj": page_obj,
         "total_records": total_records,
         },  # only send page_obj
    )



@login_required
def delete_final_data(request, pk):
    final_item = get_object_or_404(Final_Data, pk=pk)

    if request.method == "POST":
        final_item.delete()
        messages.success(request, f"Record {final_item.f_AccessionNo} deleted successfully!")
        return redirect('show_final_data')  # <-- Correct URL name

    messages.error(request, "Invalid request for deletion.")
    return redirect('show_final_data')  # <-- Correct URL name


@login_required
def delete_all_final_data(request):
    Final_Data.objects.all().delete()
    messages.success(request, "Final Referred Isolates have been deleted successfully.")
    return redirect('show_final_data')  # Redirect to the table view




@login_required
def delete_finaldata_by_date(request):
    if request.method == "POST":
        upload_date_str = request.POST.get("upload_date")
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
        return redirect("show_final_data")

    messages.error(request, "Invalid request method.")
    return redirect("show_final_data")