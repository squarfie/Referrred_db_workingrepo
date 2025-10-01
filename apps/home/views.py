# -*- encoding: utf-8 -*-
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
from apps.wgs_app.models import *
from .forms import *
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



def update_wgs_summaries_for_referred(referred_obj):
    """
    Updates WGS_Project summary booleans for a given Referred_Data object.
    Sets FastQ, Gambit, MLST summaries to True if the accession matches.
    """
    wgs_entries = WGS_Project.objects.filter(Ref_Accession=referred_obj)

    for wgs in wgs_entries:
        # FastQ summary
        wgs.WGS_FastqSummary = bool(wgs.WGS_FastQ_Acc) and wgs.WGS_FastQ_Acc.strip().upper() == referred_obj.AccessionNo.strip().upper()
        # Gambit summary
        wgs.WGS_GambitSummary = bool(wgs.WGS_Gambit_Acc) and wgs.WGS_Gambit_Acc.strip().upper() == referred_obj.AccessionNo.strip().upper()
        # MLST summary
        wgs.WGS_MlstSummary = bool(wgs.WGS_Mlst_Acc) and wgs.WGS_Mlst_Acc.strip().upper() == referred_obj.AccessionNo.strip().upper()
         # MLST summary
        wgs.WGS_Checkm2Summary = bool(wgs.WGS_Checkm2_Acc) and wgs.WGS_Checkm2_Acc.strip().upper() == referred_obj.AccessionNo.strip().upper()
        
        wgs.save()




@login_required(login_url="/login/")
def index(request):
    isolates = Referred_Data.objects.all().order_by('-Date_of_Entry')

    # Count per clinic
    site_count = Referred_Data.objects.values('SiteCode').distinct().count()

    # Count per city (assuming you have a 'Current_City' field)
    record_count = Referred_Data.objects.values('AccessionNo').distinct().count()

    # Count per sex
    male_count = Referred_Data.objects.filter(Sex='Male').count()
    female_count = Referred_Data.objects.filter(Sex='Female').count()

    # Count per age group
    age_0_18 = Referred_Data.objects.filter(Age__lte=18).count()
    age_19_35 = Referred_Data.objects.filter(Age__range=(19, 35)).count()
    age_36_60 = Referred_Data.objects.filter(Age__range=(36, 60)).count()
    age_60_plus = Referred_Data.objects.filter(Age__gte=61).count()

    # Include all context variables
    context = {
        'isolates': isolates,
        'site_count': site_count,
        'record_count': record_count,
        'male_count': male_count,
        'female_count': female_count,
        'age_0_18': age_0_18,
        'age_19_35': age_19_35,
        'age_36_60': age_36_60,
        'age_60_plus': age_60_plus,
    }

    return render(request, 'home/index.html', context)




@login_required(login_url="/login/")
def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:
        load_template = request.path.split('/')[-1]

        if load_template == 'admin':
            return HttpResponseRedirect(reverse('admin:index'))
        context['segment'] = load_template

        html_template = loader.get_template('home/' + load_template)
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:
        # Redirect to a different view or render a different template
        return redirect('home')  # Redirect to the home view or any other view

    except Exception as e:
        # Log the exception if needed
        print(f"Error: {e}")
        # Redirect to a different view or render a different template
        return redirect('home')  # Redirect to the home view or any other view


# @login_required(login_url="/login/")
# def batch_create_view(request):
#     """
#     Unified view for creating a batch, generating codes,
#     and saving ARSP staff details into Batch_Table and Referred_Data.
#     Updates existing accession numbers if needed.
#     """
#     if request.method == "POST":
#         form = BatchTable_form(request.POST)
#         if form.is_valid():
#             instance = form.save(commit=False)

#             # --- Extract values from javascript ---
#             site_code = instance.bat_SiteCode or ''  # string like "BGH"
#             referral_date_obj = instance.bat_Referral_Date
#             ref_no_raw = instance.bat_RefNo or ''
#             batch_no = instance.bat_BatchNo or ''
#             total_batch = instance.bat_Total_batch or ''
#             site_name = instance.bat_Site_NameGen or ''

#             if not referral_date_obj or not site_code or not ref_no_raw:
#                 messages.error(request, "Missing required fields.")
#                 return redirect("batch_create")

#             # --- Generate accession numbers and batch info ---
#             year_short = referral_date_obj.strftime('%y')
#             year_long = referral_date_obj.strftime('%m%d%Y')

#             if '-' in ref_no_raw:
#                 start_ref, end_ref = map(int, ref_no_raw.split('-'))
#             else:
#                 start_ref = end_ref = int(ref_no_raw)

#             accession_numbers = [] # List to hold generated accession numbers
#             for ref in range(start_ref, end_ref + 1):
#                 padded_ref = str(ref).zfill(4)
#                 accession_numbers.append(f"{year_short}ARS_{site_code}{padded_ref}")

#             batch_codegen = f"{site_code}_{year_long}_{batch_no}.{total_batch}_{ref_no_raw}"
#             auto_batch_name = batch_codegen


#             if not site_name and site_code:
#                 site_obj = SiteData.objects.filter(SiteCode=site_code).first()
#                 if site_obj:
#                     site_name = site_obj.SiteName

#             # --- Save Batch_Table ---
#             instance.bat_AccessionNo = ', '.join(accession_numbers)
#             instance.bat_Batch_Code = batch_codegen
#             instance.bat_Batch_Name = auto_batch_name
#             instance.bat_Site_Name = site_name
#             instance.save()

#             # --- Create or update Referred_Data entries ---
#             for acc_no in accession_numbers:
#                 Referred_Data.objects.update_or_create(
#                     AccessionNo=acc_no,
#                     defaults={
#                         "Batch_Code": batch_codegen,
#                         "Referral_Date": referral_date_obj,
#                         "RefNo": ref_no_raw,
#                         "BatchNo": batch_no,
#                         "Total_batch": total_batch,
#                         "SiteCode": site_code,
#                         "Site_Name": site_name,
#                         "Batch_Name": auto_batch_name,
#                         "arsp_Encoder": instance.bat_Encoder or '',
#                         "arsp_Enc_Lic": instance.bat_Enc_Lic or '',
#                         "arsp_Checker": instance.bat_Checker or '',
#                         "arsp_Chec_Lic": instance.bat_Chec_Lic or '',
#                         "arsp_Verifier": instance.bat_Verifier or '',
#                         "arsp_Ver_Lic": instance.bat_Ver_Lic or '',
#                         "arsp_LabManager": instance.bat_LabManager or '',
#                         "arsp_Lab_Lic": instance.bat_Lab_Lic or '',
#                         "arsp_Head": instance.bat_Head or '',
#                         "arsp_Head_Lic": instance.bat_Head_Lic or '',
#                     }
#                 )
#             total_records = Referred_Data.objects.filter(Batch_Code=batch_codegen).count()
#             messages.success(request, f"You have successfully created {total_records} record/s in this batch")
#             return redirect(f"{reverse('show_batches')}?batch_code={instance.bat_Batch_Code}")
#         else:
#             print(form.errors)
#             messages.error(request, "Invalid data. Please check the form.")
#     else:
#         form = BatchTable_form()

#     return render(request, 'home/Batchname_form.html', {'form': form})


@login_required(login_url="/login/")
def batch_create_view(request):
    """
    Creates or overwrites a batch:
    - If batch code exists, delete old Batch_Table + Referred_Data, then recreate.
    - If not, create new.
    Ensures no duplicates remain.
    """
    if request.method == "POST":
        form = BatchTable_form(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)

            # --- Extract values ---
            site_code = (instance.bat_SiteCode or "").strip()
            referral_date_obj = instance.bat_Referral_Date
            ref_no_raw = (instance.bat_RefNo or "").strip()
            batch_no = instance.bat_BatchNo or ""
            total_batch = instance.bat_Total_batch or ""
            site_name = instance.bat_Site_NameGen or ""

            # --- Validate required fields ---
            if not referral_date_obj or not site_code or not ref_no_raw:
                messages.error(request, "Missing required fields (Site Code, Referral Date, or Ref No).")
                return redirect("batch_create")

            # --- Generate accession numbers ---
            try:
                year_short = referral_date_obj.strftime("%y")
                year_long = referral_date_obj.strftime("%m%d%Y")

                if "-" in ref_no_raw:  # e.g. "100-105"
                    start_ref, end_ref = map(int, ref_no_raw.split("-"))
                else:
                    start_ref = end_ref = int(ref_no_raw)
            except ValueError:
                messages.error(request, "Invalid Ref No format. Use a number or range")
                return redirect("batch_create")

            accession_numbers = [
                f"{year_short}ARS_{site_code}{str(ref).zfill(4)}"
                for ref in range(start_ref, end_ref + 1)
            ]

            # --- Generate batch code + name ---
            batch_codegen = f"{site_code}_{year_long}_{batch_no}.{total_batch}_{ref_no_raw}"
            auto_batch_name = batch_codegen

            # --- Resolve site name ---
            if not site_name and site_code:
                site_obj = SiteData.objects.filter(SiteCode=site_code).first()
                if site_obj:
                    site_name = site_obj.SiteName

            # --- Delete old batch if exists (overwrite) ---
            old_batch = Batch_Table.objects.filter(bat_Batch_Code=batch_codegen).first()
            if old_batch:
                # If your Referred_Data model links to Batch_Table via ForeignKey 'Batch_id', use this:
                Referred_Data.objects.filter(Batch_id=old_batch).delete()  # Delete related isolates

                old_batch.delete()

            # --- Create new Batch_Table ---
            batch_obj = Batch_Table.objects.create(
                bat_Batch_Name=auto_batch_name,
                bat_AccessionNo=", ".join(accession_numbers),
                bat_Batch_Code=batch_codegen,
                bat_Site_Name=site_name,
                bat_SiteCode=site_code,
                bat_Referral_Date=referral_date_obj,
                bat_RefNo=ref_no_raw,
                bat_BatchNo=batch_no,
                bat_Total_batch=total_batch,
                bat_Encoder=instance.bat_Encoder or "",
                bat_Enc_Lic=instance.bat_Enc_Lic or "",
                bat_Checker=instance.bat_Checker or "",
                bat_Chec_Lic=instance.bat_Chec_Lic or "",
                bat_Verifier=instance.bat_Verifier or "",
                bat_Ver_Lic=instance.bat_Ver_Lic or "",
                bat_LabManager=instance.bat_LabManager or "",
                bat_Lab_Lic=instance.bat_Lab_Lic or "",
                bat_Head=instance.bat_Head or "",
                bat_Head_Lic=instance.bat_Head_Lic or "",
            )

            # --- Create or overwrite Referred_Data for each accession ---
            for acc_no in accession_numbers:
                with transaction.atomic():
                    Referred_Data.objects.update_or_create(
                        AccessionNo=acc_no,  # unique field
                        defaults={
                            "Batch_id": batch_obj,  # ForeignKey link
                            "Batch_Code": batch_codegen,
                            "Referral_Date": referral_date_obj,
                            "RefNo": ref_no_raw,
                            "BatchNo": batch_no,
                            "Total_batch": total_batch,
                            "SiteCode": site_code,
                            "Site_Name": site_name,
                            "Batch_Name": auto_batch_name,
                            "arsp_Encoder": batch_obj.bat_Encoder or "",
                            "arsp_Enc_Lic": batch_obj.bat_Enc_Lic or "",
                            "arsp_Checker": batch_obj.bat_Checker or "",
                            "arsp_Chec_Lic": batch_obj.bat_Chec_Lic or "",
                            "arsp_Verifier": batch_obj.bat_Verifier or "",
                            "arsp_Ver_Lic": batch_obj.bat_Ver_Lic or "",
                            "arsp_LabManager": batch_obj.bat_LabManager or "",
                            "arsp_Lab_Lic": batch_obj.bat_Lab_Lic or "",
                            "arsp_Head": batch_obj.bat_Head or "",
                            "arsp_Head_Lic": batch_obj.bat_Head_Lic or "",
                        }
                    )

            # --- Count only this batch ---
            total_records = Referred_Data.objects.filter(Batch_Code=batch_codegen).count()

            messages.success(
                request,
                f"Batch '{auto_batch_name}' saved successfully with {total_records} record(s)."
            )
            return redirect(f"{reverse('show_batches')}?batch_code={batch_obj.bat_Batch_Code}")

        else:
            messages.error(request, "Batch creation failed. Please check the form.")
    else:
        form = BatchTable_form()

    return render(request, "home/Batchname_form.html", {"form": form})


# @login_required(login_url="/login/")
# def show_batches(request):
#     """
#     Show isolates that belong to a specific batch (filtered by Batch_Code).
#     Falls back to showing all isolates if no Batch_Code is provided.
#     """
#     batch_code = request.GET.get('batch_code', None)  # lowercase for consistency

#     isolates = Referred_Data.objects.prefetch_related('antibiotic_entries')

#     if batch_code:
#         isolates = isolates.filter(Batch_Code=batch_code)

#     isolates = isolates.order_by('-Date_of_Entry')

#     # Paginate the queryset to display 20 records per page
#     paginator = Paginator(isolates, 20)
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)

#     return render(request, 'home/Batch_isolates.html', {
#         'page_obj': page_obj,
#         'batch_code': batch_code,
#     })



@login_required(login_url="/login/")
def show_batches(request):
    """
    Show isolates that belong to the last generated batch by default,
    or filter by batch_code if provided in GET.
    """
    batch_code = request.GET.get('batch_code')

    if not batch_code:
        # Get the last generated batch code from the database
        last_batch = Referred_Data.objects.order_by('-Date_of_Entry').first()
        batch_code = last_batch.Batch_Code if last_batch else None

    isolates = Referred_Data.objects.prefetch_related('antibiotic_entries')
 
    if batch_code:
        isolates = isolates.filter(Batch_Code=batch_code)

    isolates = isolates.order_by('-Date_of_Entry')

    # Paginate the queryset to display 20 records per page
    paginator = Paginator(isolates, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Fetch batch object for header buttons
    batch = Batch_Table.objects.filter(bat_Batch_Code=batch_code).first() if batch_code else None
    
    return render(request, 'home/Batch_isolates.html', {
        'page_obj': page_obj,
        'batch_code': batch_code,
        'batch': batch,
    })


# @login_required(login_url="/login/")
# def review_batches(request):
#     from django.db.models import Count, Prefetch
#     batches = (
#         Batch_Table.objects.all()
#         .order_by("-bat_Referral_Date")
#         .annotate(total_isolates=Count("Batch_isolates"))
#         .prefetch_related(
#             Prefetch(
#                 "Batch_isolates",
#                 queryset=Referred_Data.objects.only("AccessionNo", "SiteCode", "Patient_ID", "OrganismCode")
#             )
#         )
#     )
#     return render(request, "home/review_batches.html", {"batches": batches})





@login_required(login_url="/login/")
def review_batches(request):
    # Only include Referred_Data with non-empty OrganismCode and correct batch link
    isolate_qs = Referred_Data.objects.filter(
        OrganismCode__isnull=False
    ).exclude(OrganismCode="").only("id", "AccessionNo", "SiteCode", "Patient_ID", "OrganismCode", "Batch_id")

    # Annotate using the correct related_name for the ForeignKey from Referred_Data to Batch_Table
    # Make sure your Referred_Data model's ForeignKey to Batch_Table uses related_name="Batch_isolates"
    batches = (
        Batch_Table.objects.all()
        .order_by("-bat_Referral_Date")
        .annotate(
            total_isolates=Count(
                "Batch_isolates",
                filter=Q(Batch_isolates__OrganismCode__isnull=False) & ~Q(Batch_isolates__OrganismCode=""),
                distinct=True,
            )
        )
        .prefetch_related(
            Prefetch("Batch_isolates", queryset=isolate_qs, to_attr="prefetched_isolates")
        )
    )

    return render(request, "home/review_batches.html", {"batches": list(batches)})


@login_required(login_url="/login/")
def clean_batch(request, batch_id):
    """
    Deletes a batch and all related Referred_Data records.
    """
    batch = get_object_or_404(Batch_Table, pk=batch_id)
    
    # Delete related isolates manually
    Referred_Data.objects.filter(Batch_Code=batch.bat_Batch_Code).delete()
    
    # Delete the batch itself
    batch.delete()
    
    messages.success(request, f"Batch '{batch.bat_Batch_Name}' and all related isolates have been deleted.")
    
    return redirect('review_batches')



# @login_required(login_url="/login/")
# def delete_batch(request, batch_id):
#     batch = get_object_or_404(Batch_Table, pk=batch_id)
#     batch.delete()  # cascades to delete all Referred_Data because of on_delete=models.CASCADE
#     return redirect('show_batches')  # better: go back to the batches page


@login_required(login_url="/login/")
def delete_batch(request, batch_id):
    """
    Deletes a batch and all related Referred_Data records.
    """
    batch = get_object_or_404(Batch_Table, pk=batch_id)
    
    # Delete related isolates manually
    Referred_Data.objects.filter(Batch_Code=batch.bat_Batch_Code).delete()
    
    # Delete the batch itself
    batch.delete()
    
    messages.success(request, f"Batch '{batch.bat_Batch_Name}' and all related isolates have been deleted.")
    
    return redirect('show_batches')


# @login_required(login_url="/login/")
# def raw_data(request, isolate_id):
#     # --- Fetch antibiotics lists ---
#     whonet_abx_data = BreakpointsTable.objects.filter(Show=True)
#     whonet_retest_data = BreakpointsTable.objects.filter(Retest=True)

#     # --- Get the isolate record ---
#     raw_instance = get_object_or_404(Referred_Data, id=isolate_id)

#     # --- Handle GET request ---
#     if request.method == "GET":
#         form = Referred_Form(instance=raw_instance)


#         return render(request, "home/Referred_form.html", {
#             "form": form,
#             "whonet_abx_data": whonet_abx_data,
#             "whonet_retest_data": whonet_retest_data,
#             "edit_mode": True,
#             "raw_instance": raw_instance,
#         })

#     # --- Handle POST request ---
#     elif request.method == "POST":
#         form = Referred_Form(request.POST, instance=raw_instance)

#         if form.is_valid() :
#             raw_instance = form.save(commit=False)
#             raw_instance.save()

#             # --- Clear old AntibioticEntry if editing ---
#             AntibioticEntry.objects.filter(ab_idNum_referred=raw_instance).delete()

#             # --- Handle main antibiotics ---
#             for entry in whonet_abx_data:
#                 abx_code = entry.Whonet_Abx
#                 if entry.Disk_Abx:
#                     disk_value = request.POST.get(f"disk_{entry.id}")
#                     disk_enris = request.POST.get(f"disk_enris_{entry.id}") or ""
#                     mic_value, mic_operand, alert_mic, mic_enris = "", "", False, ""
#                 else:
#                     mic_value = request.POST.get(f"mic_{entry.id}")
#                     mic_enris = request.POST.get(f"mic_enris_{entry.id}") or ""
#                     mic_operand = request.POST.get(f"mic_operand_{entry.id}") or ""
#                     alert_mic = f"alert_mic_{entry.id}" in request.POST
#                     disk_value = ""
#                     disk_enris = ""
                
#                 # Check and update mic_operand if needed
#                 disk_enris = (disk_enris or '').strip() # Ensure it's a string and strip whitespace
#                 mic_enris = (mic_enris or '').strip()
#                 mic_operand = (mic_operand or '').strip()

#                 # Convert `disk_value` safely # Convert to int if valid, else None
#                 disk_value = int(disk_value) if disk_value and disk_value.strip().isdigit() else None 

#                 # Debugging: Print the values before saving
#                 print(f"Saving values for Antibiotic Entry {entry.id}:", {
#                     'mic_operand': mic_operand,
#                     'disk_value': disk_value,
#                     'disk_enris': disk_enris,
#                     'mic_value': mic_value,
#                     'mic_enris': mic_enris,
#                 })

#                 antibiotic_entry = AntibioticEntry.objects.create(
#                     ab_idNum_referred=raw_instance,
#                     ab_AccessionNo=raw_instance.AccessionNo,
#                     ab_Antibiotic=entry.Antibiotic,
#                     ab_Abx=entry.Abx_code,
#                     ab_Abx_code=abx_code,
#                     ab_Disk_value=int(disk_value) if disk_value and disk_value.strip().isdigit() else None,
#                     ab_Disk_enRIS=disk_enris,
#                     ab_MIC_value=mic_value or None,
#                     ab_MIC_enRIS=mic_enris,
#                     ab_MIC_operand=mic_operand,
#                     ab_R_breakpoint=entry.R_val or None,
#                     ab_I_breakpoint=entry.I_val or None,
#                     ab_SDD_breakpoint=entry.SDD_val or None,
#                     ab_S_breakpoint=entry.S_val or None,
#                     ab_AlertMIC=alert_mic,
#                     ab_Alert_val=entry.Alert_val if alert_mic else "",
#                 )
#                 antibiotic_entry.ab_breakpoints_id.set([entry])

#             # --- Handle retest antibiotics ---
#             for retest in whonet_retest_data:
#                 retest_abx_code = retest.Whonet_Abx
#                 if retest.Disk_Abx:
#                     retest_disk_value = request.POST.get(f"retest_disk_{retest.id}")
#                     retest_disk_enris = request.POST.get(f"retest_disk_enris_{retest.id}") or ""
#                     retest_mic_value, retest_mic_operand, retest_alert_mic, retest_mic_enris = "", "", False, ""    
#                 else:
#                     retest_mic_value = request.POST.get(f"retest_mic_{retest.id}")
#                     retest_mic_operand = request.POST.get(f"retest_mic_operand_{retest.id}") or ""
#                     retest_mic_enris = request.POST.get(f"retest_mic_enris_{retest.id}") or ""
#                     retest_alert_mic = f"retest_alert_mic_{retest.id}" in request.POST
#                     retest_disk_value = ""
#                     retest_disk_enris = ""

                
#                 # Check and update retest mic_operand if needed
#                 retest_disk_enris = (retest_disk_enris or '').strip() # Ensure it's a string and strip whitespace
#                 retest_mic_enris = (retest_mic_enris or '').strip()
#                 retest_mic_operand = (retest_mic_operand or '').strip()
                
#                 # Convert `retest_disk_value` safely
#                 retest_disk_value = int(retest_disk_value) if retest_disk_value and retest_disk_value.strip().isdigit() else None

#                 # Debugging: Print the values before saving
#                 print(f"Saving values for Retest Entry {retest.id}:", {
#                     'retest_mic_operand': retest_mic_operand,
#                     'retest_disk_value': retest_disk_value,
#                     'retest_disk_enris': retest_disk_enris,
#                     'retest_mic_value': retest_mic_value,
#                     'retest_mic_enris': retest_mic_enris,
#                     'retest_alert_mic': retest_alert_mic,
#                     'retest_alert_val': retest.Alert_val if retest_alert_mic else '',
#                 })

#                 if retest_disk_value or retest_mic_value:
#                     retest_entry = AntibioticEntry.objects.create(
#                         ab_idNum_referred=raw_instance,
#                         ab_Retest_Abx_code=retest_abx_code,
#                         ab_Retest_DiskValue=int(retest_disk_value) if retest_disk_value and retest_disk_value.strip().isdigit() else None,
#                         ab_Retest_Disk_enRIS=retest_disk_enris,
#                         ab_Retest_MICValue=retest_mic_value or None,
#                         ab_Retest_MIC_enRIS=retest_mic_enris,
#                         ab_Retest_MIC_operand=retest_mic_operand,
#                         ab_Retest_Antibiotic=retest.Antibiotic,
#                         ab_Retest_Abx=retest.Abx_code,
#                         ab_Ret_R_breakpoint=retest.R_val or None,
#                         ab_Ret_I_breakpoint=retest.I_val or None,
#                         ab_Ret_SDD_breakpoint=retest.SDD_val or None,
#                         ab_Ret_S_breakpoint=retest.S_val or None,
#                         ab_Retest_AlertMIC=retest_alert_mic,
#                         ab_Retest_Alert_val=retest.Alert_val if retest_alert_mic else "",
#                     )
#                     retest_entry.ab_breakpoints_id.set([retest])

#             messages.success(request, "Data saved successfully.")
#             return redirect("show_data")
#         else:
#             messages.error(request, "Error: Saving unsuccessful")
#             print(form.errors)

#     # --- fallback GET render in case POST fails ---
#     form = Referred_Form(instance=raw_instance)

#     return render(request, "home/Referred_form.html", {
#         "form": form,
#         "whonet_abx_data": whonet_abx_data,
#         "whonet_retest_data": whonet_retest_data,
#         "edit_mode": True,
#         "raw_instance": raw_instance,

#     })


# @login_required(login_url="/login/")
# def raw_data(request, id):
#     # --- Fetch antibiotics lists ---
#     whonet_abx_data = BreakpointsTable.objects.filter(Show=True)
#     whonet_retest_data = BreakpointsTable.objects.filter(Retest=True)

#     # --- Get the isolate record ---
#     isolates = get_object_or_404(Referred_Data, pk=id)

#     # Fetch all entries in one query
#     all_entries = AntibioticEntry.objects.filter(ab_idNum_referred=isolates)

#     # Separate them based on the 'retest' condition
#     existing_entries = all_entries.filter(ab_Abx_code__isnull=False)  # Regular entries
#     retest_entries = all_entries.filter(ab_Retest_Abx_code__isnull=False)   # Retest entries

#     # --- Handle GET request ---
#     if request.method == "GET":
#         form = Referred_Form(instance=isolates)
#         return render(request, "home/Referred_form.html", {
#             "form": form,
#             "whonet_abx_data": whonet_abx_data,
#             "whonet_retest_data": whonet_retest_data,
#             "edit_mode": True,
#             "isolates": isolates,
#             "existing_entries": existing_entries,
#             "retest_entries": retest_entries,

#         })

#     # --- Handle POST request ---
#     elif request.method == "POST":
#         form = Referred_Form(request.POST, instance=isolates)

#         if form.is_valid():
#             isolates = form.save(commit=False)
#             isolates.save()

#             # --- Handle main antibiotics ---
#             for entry in whonet_abx_data:
#                 abx_code = (entry.Whonet_Abx or "").strip().upper()
#                 disk_value = request.POST.get(f"disk_{entry.id}") or ""
#                 disk_enris = (request.POST.get(f"disk_enris_{entry.id}") or "").strip()
#                 mic_value = request.POST.get(f"mic_{entry.id}") or ""
#                 mic_enris = (request.POST.get(f"mic_enris_{entry.id}") or "").strip()
#                 mic_operand = (request.POST.get(f"mic_operand_{entry.id}") or "").strip()
#                 alert_mic = f"alert_mic_{entry.id}" in request.POST

#                 try:
#                     disk_value = int(disk_value) if disk_value.strip() else None
#                 except ValueError:
#                     disk_value = None

                
#                 # Debugging: Print the values before saving
#                 print(f"Saving values for Antibiotic Entry {entry.id}:", {
#                     'mic_operand': mic_operand,
#                     'disk_value': disk_value,
#                     'disk_enris': disk_enris,
#                     'mic_value': mic_value,
#                     'mic_enris': mic_enris,
#                 })

#                 # Get or update antibiotic entry
#                 antibiotic_entry, created = AntibioticEntry.objects.update_or_create(
#                     ab_idNum_referred=isolates,
#                     ab_Abx_code=abx_code,
#                     defaults={
#                         "ab_AccessionNo": isolates.AccessionNo,
#                         "ab_Antibiotic": entry.Antibiotic,
#                         "ab_Abx": entry.Abx_code,
#                         "ab_Disk_value": disk_value,
#                         "ab_Disk_enRIS": disk_enris,
#                         "ab_MIC_value": mic_value or None,
#                         "ab_MIC_enRIS": mic_enris,
#                         "ab_MIC_operand": mic_operand,
#                         "ab_R_breakpoint": entry.R_val or None,
#                         "ab_I_breakpoint": entry.I_val or None,
#                         "ab_SDD_breakpoint": entry.SDD_val or None,
#                         "ab_S_breakpoint": entry.S_val or None,
#                         "ab_AlertMIC": alert_mic,
#                         "ab_Alert_val": entry.Alert_val if alert_mic else '',
#                     }
#                 )

#                 antibiotic_entry.ab_breakpoints_id.set([entry])

#             # Separate loop for Retest Data
#             for retest in whonet_retest_data:
#                 retest_abx_code = retest.Whonet_Abx

#                 # Fetch user input values for MIC and Disk
#                 if retest.Disk_Abx:
#                     retest_disk_value = request.POST.get(f'retest_disk_{retest.id}')
#                     retest_disk_enris = request.POST.get(f"retest_disk_enris_{retest.id}") 
#                     retest_mic_value = ''
#                     retest_mic_enris = ''
#                     retest_mic_operand = ''
#                     retest_alert_mic = False
#                 else:
#                     retest_mic_value = request.POST.get(f'retest_mic_{retest.id}')
#                     retest_mic_enris = request.POST.get(f"retest_mic_enris_{retest.id}") 
#                     retest_mic_operand = request.POST.get(f'retest_mic_operand_{retest.id}')
#                     retest_alert_mic = f'retest_alert_mic_{retest.id}' in request.POST
#                     retest_disk_value = ''
#                     retest_disk_enris = ''

#                 # Check and update retest mic_operand if needed
#                 retest_disk_enris = (retest_disk_enris or '').strip() # Ensure it's a string and strip whitespace
#                 retest_mic_enris = (retest_mic_enris or '').strip()
#                 retest_mic_operand = (retest_mic_operand or '').strip()
                
#                 # Convert `retest_disk_value` safely
#                 retest_disk_value = int(retest_disk_value) if retest_disk_value and retest_disk_value.strip().isdigit() else None

#                 # Debugging: Print the values before saving
#                 print(f"Saving values for Retest Entry {retest.id}:", {
#                     'retest_mic_operand': retest_mic_operand,
#                     'retest_disk_value': retest_disk_value,
#                     'retest_disk_enris': retest_disk_enris,
#                     'retest_mic_value': retest_mic_value,
#                     'retest_mic_enris': retest_mic_enris,
#                     'retest_alert_mic': retest_alert_mic,
#                     'retest_alert_val': retest.Alert_val if retest_alert_mic else '',
#                 })

#                 # Get or update retest antibiotic entry
#                 retest_entry, created = AntibioticEntry.objects.update_or_create(
#                     ab_idNum_referred=isolates,
#                     ab_Retest_Abx_code=retest_abx_code,
#                     defaults={
#                         "ab_Retest_DiskValue": retest_disk_value,
#                         "ab_Retest_Disk_enRIS": retest_disk_enris,
#                         "ab_Retest_MICValue": retest_mic_value or None,
#                         "ab_Retest_MIC_enRIS": retest_mic_enris,
#                         "ab_Retest_MIC_operand": retest_mic_operand,
#                         "ab_Retest_Antibiotic": retest.Antibiotic,
#                         "ab_Retest_Abx": retest.Abx_code,
#                         "ab_Ret_R_breakpoint": retest.R_val or None,
#                         "ab_Ret_S_breakpoint": retest.S_val or None,
#                         "ab_Ret_SDD_breakpoint": retest.SDD_val or None,
#                         "ab_Ret_I_breakpoint": retest.I_val or None,
#                         "ab_Retest_AlertMIC": retest_alert_mic,
#                         "ab_Retest_Alert_val": retest.Alert_val if retest_alert_mic else '',
#                     }
#                 )

#                 retest_entry.ab_breakpoints_id.set([retest])

#             messages.success(request, "Data saved successfully.")
#             return redirect("show_data")
#         else:
#             messages.error(request, "Error: Saving unsuccessful")
#             print(form.errors)

#     # --- fallback GET render in case POST fails ---
#     form = Referred_Form(instance=isolates)
#     existing_entries = AntibioticEntry.objects.filter(ab_idNum_referred=isolates)
#     return render(request, "home/Referred_form.html", {
#         "form": form,
#         "whonet_abx_data": whonet_abx_data,
#         "whonet_retest_data": whonet_retest_data,
#         "edit_mode": True,
#         "isolates": isolates,
#         "existing_entries": existing_entries,
#         "retest_entries": retest_entries,

#     })




# @login_required(login_url="/login/")
# def raw_data(request, id):
#     # --- Fetch antibiotics lists ---
#     whonet_abx_data = BreakpointsTable.objects.filter(Show=True)
#     whonet_retest_data = BreakpointsTable.objects.filter(Retest=True)

#     # --- Get the isolate record ---
#     isolates = get_object_or_404(Referred_Data, pk=id)

#     # Fetch all entries in one query
#     all_entries = AntibioticEntry.objects.filter(ab_idNum_referred=isolates)

#     # Separate them based on the 'retest' condition
#     existing_entries = all_entries.filter(ab_Abx_code__isnull=False)  # Regular entries
#     retest_entries = all_entries.filter(ab_Retest_Abx_code__isnull=False)   # Retest entries

#     # --- Handle GET request ---
#     if request.method == "GET":
#         form = Referred_Form(instance=isolates)
#         return render(request, "home/Referred_form.html", {
#             "form": form,
#             "whonet_abx_data": whonet_abx_data,
#             "whonet_retest_data": whonet_retest_data,
#             "edit_mode": True,
#             "isolates": isolates,
#             "existing_entries": existing_entries,
#             "retest_entries": retest_entries,

#         })

#     # --- Handle POST request ---
#     elif request.method == "POST":
#         form = Referred_Form(request.POST, instance=isolates)

#         if form.is_valid():
#             isolates = form.save(commit=False)
#             isolates.save()

#             # --- Handle main antibiotics ---
#             for entry in whonet_abx_data:
#                 abx_code = (entry.Whonet_Abx or "").strip().upper()
#                 disk_value = request.POST.get(f"disk_{entry.id}") or ""
#                 disk_enris = (request.POST.get(f"disk_enris_{entry.id}") or "").strip()
#                 mic_value = request.POST.get(f"mic_{entry.id}") or ""
#                 mic_enris = (request.POST.get(f"mic_enris_{entry.id}") or "").strip()
#                 mic_operand = (request.POST.get(f"mic_operand_{entry.id}") or "").strip()
#                 alert_mic = f"alert_mic_{entry.id}" in request.POST

#                 try:
#                     disk_value = int(disk_value) if disk_value.strip() else None
#                 except ValueError:
#                     disk_value = None

                
#                 # Debugging: Print the values before saving
#                 print(f"Saving values for Antibiotic Entry {entry.id}:", {
#                     'mic_operand': mic_operand,
#                     'disk_value': disk_value,
#                     'disk_enris': disk_enris,
#                     'mic_value': mic_value,
#                     'mic_enris': mic_enris,
#                 })

#                 # Get or update antibiotic entry
#                 antibiotic_entry, created = AntibioticEntry.objects.update_or_create(
#                     ab_idNum_referred=isolates,
#                     ab_Abx_code=abx_code,
#                     defaults={
#                         "ab_AccessionNo": isolates.AccessionNo,
#                         "ab_Antibiotic": entry.Antibiotic,
#                         "ab_Abx": entry.Abx_code,
#                         "ab_Disk_value": disk_value,
#                         "ab_Disk_enRIS": disk_enris,
#                         "ab_MIC_value": mic_value or None,
#                         "ab_MIC_enRIS": mic_enris,
#                         "ab_MIC_operand": mic_operand,
#                         "ab_R_breakpoint": entry.R_val or None,
#                         "ab_I_breakpoint": entry.I_val or None,
#                         "ab_SDD_breakpoint": entry.SDD_val or None,
#                         "ab_S_breakpoint": entry.S_val or None,
#                         "ab_AlertMIC": alert_mic,
#                         "ab_Alert_val": entry.Alert_val if alert_mic else '',
#                     }
#                 )

#                 antibiotic_entry.ab_breakpoints_id.set([entry])

#             # Separate loop for Retest Data
#             for retest in whonet_retest_data:
#                 retest_abx_code = retest.Whonet_Abx

#                 # Fetch user input values for MIC and Disk
#                 if retest.Disk_Abx:
#                     retest_disk_value = request.POST.get(f'retest_disk_{retest.id}')
#                     retest_disk_enris = request.POST.get(f"retest_disk_enris_{retest.id}") or ""
#                     retest_mic_value = ''
#                     retest_mic_enris = ''
#                     retest_mic_operand = ''
#                     retest_alert_mic = False
#                 else:
#                     retest_mic_value = request.POST.get(f'retest_mic_{retest.id}')
#                     retest_mic_enris = request.POST.get(f"retest_mic_enris_{retest.id}") or ""
#                     retest_mic_operand = request.POST.get(f'retest_mic_operand_{retest.id}')
#                     retest_alert_mic = f'retest_alert_mic_{retest.id}' in request.POST
#                     retest_disk_value = ''
#                     retest_disk_enris = ''

#                 # Check and update retest mic_operand if needed
#                 retest_disk_enris = (retest_disk_enris or '').strip() # Ensure it's a string and strip whitespace
#                 retest_mic_enris = (retest_mic_enris or '').strip()
#                 retest_mic_operand = (retest_mic_operand or '').strip()
                
#                 # Convert `retest_disk_value` safely
#                 retest_disk_value = int(retest_disk_value) if retest_disk_value and retest_disk_value.strip().isdigit() else None

#                 # Debugging: Print the values before saving
#                 print(f"Saving values for Retest Entry {retest.id}:", {
#                     'retest_mic_operand': retest_mic_operand,
#                     'retest_disk_value': retest_disk_value,
#                     'retest_disk_enris': retest_disk_enris,
#                     'retest_mic_value': retest_mic_value,
#                     'retest_mic_enris': retest_mic_enris,
#                     'retest_alert_mic': retest_alert_mic,
#                     'retest_alert_val': retest.Alert_val if retest_alert_mic else '',
#                 })

#                 # Get or update retest antibiotic entry
#                 retest_entry, created = AntibioticEntry.objects.update_or_create(
#                     ab_idNum_referred=isolates,
#                     ab_Retest_Abx_code=retest_abx_code,
#                     defaults={
#                         "ab_Retest_DiskValue": retest_disk_value,
#                         "ab_Retest_Disk_enRIS": retest_disk_enris,
#                         "ab_Retest_MICValue": retest_mic_value or None,
#                         "ab_Retest_MIC_enRIS": retest_mic_enris,
#                         "ab_Retest_MIC_operand": retest_mic_operand,
#                         "ab_Retest_Antibiotic": retest.Antibiotic,
#                         "ab_Retest_Abx": retest.Abx_code,
#                         "ab_Ret_R_breakpoint": retest.R_val or None,
#                         "ab_Ret_S_breakpoint": retest.S_val or None,
#                         "ab_Ret_SDD_breakpoint": retest.SDD_val or None,
#                         "ab_Ret_I_breakpoint": retest.I_val or None,
#                         "ab_Retest_AlertMIC": retest_alert_mic,
#                         "ab_Retest_Alert_val": retest.Alert_val if retest_alert_mic else "",
#                     }
#                 )

#                 retest_entry.ab_breakpoints_id.set([retest])

#             messages.success(request, "Data saved successfully.")
#             return redirect("show_data")
#         else:
#             messages.error(request, "Error: Saving unsuccessful")
#             print(form.errors)

#     # --- fallback GET render in case POST fails ---
#     form = Referred_Form(instance=isolates)
#     existing_entries = AntibioticEntry.objects.filter(ab_idNum_referred=isolates)
#     return render(request, "home/Referred_form.html", {
#         "form": form,
#         "whonet_abx_data": whonet_abx_data,
#         "whonet_retest_data": whonet_retest_data,
#         "edit_mode": True,
#         "isolates": isolates,
#         "existing_entries": existing_entries,
#         "retest_entries": retest_entries,

#     })





@login_required(login_url="/login/")
def raw_data(request, id):
    # --- Fetch antibiotics lists ---
    whonet_abx_data = BreakpointsTable.objects.filter(Show=True)
    whonet_retest_data = BreakpointsTable.objects.filter(Retest=True)

    # --- Get the isolate record ---
    isolates = get_object_or_404(Referred_Data, pk=id)

    # Fetch all entries in one query
    all_entries = AntibioticEntry.objects.filter(ab_idNum_referred=isolates)

    # Separate them based on the 'retest' condition
    existing_entries = all_entries.filter(ab_Abx_code__isnull=False)  # Regular entries
    retest_entries = all_entries.filter(ab_Retest_Abx_code__isnull=False)   # Retest entries

    # --- Handle GET request ---
    if request.method == "GET":
        form = Referred_Form(instance=isolates)
        return render(request, "home/Referred_form.html", {
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
                antibiotic_entry, created = AntibioticEntry.objects.update_or_create(
                    ab_idNum_referred=isolates,
                    ab_Abx_code=abx_code,
                    defaults={
                        "ab_AccessionNo": isolates.AccessionNo,
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
                retest_entry, created = AntibioticEntry.objects.update_or_create(
                    ab_idNum_referred=isolates,
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
    form = Referred_Form(instance=isolates)
    existing_entries = AntibioticEntry.objects.filter(ab_idNum_referred=isolates)
    return render(request, "home/Referred_form.html", {
        "form": form,
        "whonet_abx_data": whonet_abx_data,
        "whonet_retest_data": whonet_retest_data,
        "edit_mode": True,
        "isolates": isolates,
        "existing_entries": existing_entries,
        "retest_entries": retest_entries,

    })



#Retrieve all data
@login_required(login_url="/login/")
def show_data(request):
    sort_by = request.GET.get('sort', 'Date_of_Entry')  # Default sort field
    order = request.GET.get('order', 'desc')  # Default sort order

    sort_field = f"-{sort_by}" if order == 'desc' else sort_by

    isolates = Referred_Data.objects.prefetch_related(
        'antibiotic_entries'
    ).order_by(sort_field)

    paginator = Paginator(isolates, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'current_sort': sort_by,
        'current_order': order,
    }

    return render(request, 'home/tables.html', context)



# @login_required(login_url="/login/")
# def edit_data(request, id):
#     # Fetch the Referred_Data instance to edit
#     isolates = get_object_or_404(Referred_Data, pk=id)

#     # Fetch related data for antibiotics
  
#     whonet_abx_data = BreakpointsTable.objects.filter(Show=True)
#     whonet_retest_data = BreakpointsTable.objects.filter(Retest=True)

#     if request.method == 'POST':
#         # Print received data for debugging
#         print("POST Data:", request.POST)

#         form = Referred_Form(request.POST, instance=isolates)
#         if form.is_valid():
#             isolates = form.save(commit=False)

#             # Update or Create Antibiotic Entries (whonet_abx_data)
#             for entry in whonet_abx_data:
#                 abx_code = entry.Whonet_Abx

#                 # Fetch user input values for MIC and Disk
#                 if entry.Disk_Abx:
#                     disk_value = request.POST.get(f'disk_{entry.id}')
#                     disk_enris = request.POST.get(f'disk_enris_{entry.id}') 
#                     mic_value = ''
#                     mic_enris = ''
#                     mic_operand = ''
#                     alert_mic = False  
#                 else:
#                     mic_value = request.POST.get(f'mic_{entry.id}')
#                     mic_enris = request.POST.get(f'mic_enris_{entry.id}') 
#                     mic_operand = request.POST.get(f'mic_operand_{entry.id}')
#                     alert_mic = f'alert_mic_{entry.id}' in request.POST
#                     disk_value = ''
#                     disk_enris = ''
                
#                 # Check and update mic_operand if needed
#                 disk_enris = (disk_enris or '').strip() # Ensure it's a string and strip whitespace
#                 mic_enris = (mic_enris or '').strip()
#                 mic_operand = (mic_operand or '').strip()

#                 # Convert `disk_value` safely # Convert to int if valid, else None
#                 disk_value = int(disk_value) if disk_value and disk_value.strip().isdigit() else None 

#                 # Debugging: Print the values before saving
#                 print(f"Saving values for Antibiotic Entry {entry.id}:", {
#                     'mic_operand': mic_operand,
#                     'disk_value': disk_value,
#                     'disk_enris': disk_enris,
#                     'mic_value': mic_value,
#                     'mic_enris': mic_enris,
#                 })

#                 # Get or update antibiotic entry
#                 antibiotic_entry, created = AntibioticEntry.objects.update_or_create(
#                     ab_idNum_referred=isolates,
#                     ab_Abx_code=abx_code,
#                     defaults={
#                         "ab_AccessionNo": isolates.AccessionNo,
#                         "ab_Antibiotic": entry.Antibiotic,
#                         "ab_Abx": entry.Abx_code,
#                         "ab_Disk_value": disk_value,
#                         "ab_Disk_enRIS": disk_enris,
#                         "ab_MIC_value": mic_value or None,
#                         "ab_MIC_enRIS": mic_enris,
#                         "ab_MIC_operand": mic_operand,
#                         "ab_R_breakpoint": entry.R_val or None,
#                         "ab_I_breakpoint": entry.I_val or None,
#                         "ab_SDD_breakpoint": entry.SDD_val or None,
#                         "ab_S_breakpoint": entry.S_val or None,
#                         "ab_AlertMIC": alert_mic,
#                         "ab_Alert_val": entry.Alert_val if alert_mic else '',
#                     }
#                 )

#                 antibiotic_entry.ab_breakpoints_id.set([entry.pk])

#             # Separate loop for Retest Data
#             for retest in whonet_retest_data:
#                 retest_abx_code = retest.Whonet_Abx

#                 # Fetch user input values for MIC and Disk
#                 if retest.Disk_Abx:
#                     retest_disk_value = request.POST.get(f'retest_disk_{retest.id}')
#                     retest_disk_enris = request.POST.get(f"retest_disk_enris_{retest.id}") or ""
#                     retest_mic_value, retest_mic_operand, retest_alert_mic, retest_mic_enris = "", "", False, ""    
#                 else:
#                     retest_mic_value = request.POST.get(f'retest_mic_{retest.id}')
#                     retest_mic_operand = request.POST.get(f"retest_mic_operand_{retest.id}") or ""
#                     retest_mic_enris = request.POST.get(f"retest_mic_enris_{retest.id}") or ""
#                     retest_alert_mic = f"retest_alert_mic_{retest.id}" in request.POST
#                     retest_disk_value = ""
#                     retest_disk_enris = ""

                
#                 # Check and update retest mic_operand if needed
#                 retest_disk_enris = (retest_disk_enris or '').strip() # Ensure it's a string and strip whitespace
#                 retest_mic_enris = (retest_mic_enris or '').strip()
#                 retest_mic_operand = (retest_mic_operand or '').strip()
                
#                 # Convert `retest_disk_value` safely
#                 retest_disk_value = int(retest_disk_value) if retest_disk_value and retest_disk_value.strip().isdigit() else None

#                 # Debugging: Print the values before saving
#                 print(f"Saving values for Retest Entry {retest.id}:", {
#                     'retest_mic_operand': retest_mic_operand,
#                     'retest_disk_value': retest_disk_value,
#                     'retest_disk_enris': retest_disk_enris,
#                     'retest_mic_value': retest_mic_value,
#                     'retest_mic_enris': retest_mic_enris,
#                     'retest_alert_mic': retest_alert_mic,
#                     'retest_alert_val': retest.Alert_val if retest_alert_mic else '',
#                 })

#                 # Get or update retest antibiotic entry
#                 retest_entry, created = AntibioticEntry.objects.update_or_create(
#                     ab_idNum_referred=isolates,
#                     ab_Retest_Abx_code=retest_abx_code,
#                     defaults={
#                         "ab_Retest_DiskValue": retest_disk_value,
#                         "ab_Retest_Disk_enRIS": retest_disk_enris,
#                         "ab_Retest_MICValue": retest_mic_value or None,
#                         "ab_Retest_MIC_enRIS": retest_mic_enris,
#                         "ab_Retest_MIC_operand": retest_mic_operand,
#                         "ab_Retest_Antibiotic": retest.Antibiotic,
#                         "ab_Retest_Abx": retest.Abx_code,
#                         "ab_Ret_R_breakpoint": retest.R_val or None,
#                         "ab_Ret_S_breakpoint": retest.S_val or None,
#                         "ab_Ret_SDD_breakpoint": retest.SDD_val or None,
#                         "ab_Ret_I_breakpoint": retest.I_val or None,
#                         "ab_Retest_AlertMIC": retest_alert_mic,
#                         "ab_Retest_Alert_val": retest.Alert_val if retest_alert_mic else "",
#                     }
#                 )

#                 retest_entry.ab_breakpoints_id.set([retest])

#             messages.success(request, "Data saved successfully.")
#             return redirect("show_data")
#         else:
#             messages.error(request, "Error: Saving unsuccessful")
#             print(form.errors)

#     # --- fallback GET render in case POST fails ---
#     form = Referred_Form(instance=isolates)
#     existing_entries = AntibioticEntry.objects.filter(ab_idNum_referred=isolates)
#     return render(request, "home/Referred_form.html", {
#         "form": form,
#         "whonet_abx_data": whonet_abx_data,
#         "whonet_retest_data": whonet_retest_data,
#         "edit_mode": True,
#         "isolates": isolates,
#         "existing_entries": existing_entries,
#         "retest_entries": retest_entries,

#     })



# @login_required(login_url="/login/")
# def edit_data(request, id):
#     # Fetch the Referred_Data instance to edit
#     isolates = get_object_or_404(Referred_Data, pk=id)

#     # Fetch related data for antibiotics
  
#     whonet_abx_data = BreakpointsTable.objects.filter(Show=True)
#     whonet_retest_data = BreakpointsTable.objects.filter(Retest=True)

#     if request.method == 'POST':
#         # Print received data for debugging
#         print("POST Data:", request.POST)

#         form = Referred_Form(request.POST, instance=isolates)
#         if form.is_valid():
#             isolates = form.save(commit=False)

#             # Update or Create Antibiotic Entries (whonet_abx_data)
#             for entry in whonet_abx_data:
#                 abx_code = entry.Whonet_Abx

#                 # Fetch user input values for MIC and Disk
#                 if entry.Disk_Abx:
#                     disk_value = request.POST.get(f'disk_{entry.id}')
#                     disk_enris = request.POST.get(f'disk_enris_{entry.id}') 
#                     mic_value = ''
#                     mic_enris = ''
#                     mic_operand = ''
#                     alert_mic = False  
#                 else:
#                     mic_value = request.POST.get(f'mic_{entry.id}')
#                     mic_enris = request.POST.get(f'mic_enris_{entry.id}') 
#                     mic_operand = request.POST.get(f'mic_operand_{entry.id}')
#                     alert_mic = f'alert_mic_{entry.id}' in request.POST
#                     disk_value = ''
#                     disk_enris = ''
                
#                 # Check and update mic_operand if needed
#                 disk_enris = (disk_enris or '').strip() # Ensure it's a string and strip whitespace
#                 mic_enris = (mic_enris or '').strip()
#                 mic_operand = (mic_operand or '').strip()

#                 # Convert `disk_value` safely # Convert to int if valid, else None
#                 disk_value = int(disk_value) if disk_value and disk_value.strip().isdigit() else None 

#                 # Debugging: Print the values before saving
#                 print(f"Saving values for Antibiotic Entry {entry.id}:", {
#                     'mic_operand': mic_operand,
#                     'disk_value': disk_value,
#                     'disk_enris': disk_enris,
#                     'mic_value': mic_value,
#                     'mic_enris': mic_enris,
#                 })

#                 # Get or update antibiotic entry
#                 antibiotic_entry, created = AntibioticEntry.objects.update_or_create(
#                     ab_idNum_referred=isolates,
#                     ab_Abx_code=abx_code,
#                     defaults={
#                         "ab_AccessionNo": isolates.AccessionNo,
#                         "ab_Antibiotic": entry.Antibiotic,
#                         "ab_Abx": entry.Abx_code,
#                         "ab_Disk_value": disk_value,
#                         "ab_Disk_enRIS": disk_enris,
#                         "ab_MIC_value": mic_value or None,
#                         "ab_MIC_enRIS": mic_enris,
#                         "ab_MIC_operand": mic_operand,
#                         "ab_R_breakpoint": entry.R_val or None,
#                         "ab_I_breakpoint": entry.I_val or None,
#                         "ab_SDD_breakpoint": entry.SDD_val or None,
#                         "ab_S_breakpoint": entry.S_val or None,
#                         "ab_AlertMIC": alert_mic,
#                         "ab_Alert_val": entry.Alert_val if alert_mic else '',
#                     }
#                 )

#                 antibiotic_entry.ab_breakpoints_id.set([entry.pk])

#             # Separate loop for Retest Data
#             for retest in whonet_retest_data:
#                 retest_abx_code = retest.Whonet_Abx

#                 # Fetch user input values for MIC and Disk
#                 if retest.Disk_Abx:
#                     retest_disk_value = request.POST.get(f'retest_disk_{retest.id}')
#                     retest_disk_enris = request.POST.get(f"retest_disk_enris_{retest.id}") or ""
#                     retest_mic_value = ''
#                     retest_mic_enris = ''
#                     retest_mic_operand = ''
#                     retest_alert_mic = False
#                 else:
#                     retest_mic_value = request.POST.get(f'retest_mic_{retest.id}')
#                     retest_mic_enris = request.POST.get(f"retest_mic_enris_{retest.id}") or ""
#                     retest_mic_operand = request.POST.get(f'retest_mic_operand_{retest.id}')
#                     retest_alert_mic = f'retest_alert_mic_{retest.id}' in request.POST
#                     retest_disk_value = ''
#                     retest_disk_enris = ''

#                 # Check and update retest mic_operand if needed
#                 retest_disk_enris = (retest_disk_enris or '').strip() # Ensure it's a string and strip whitespace
#                 retest_mic_enris = (retest_mic_enris or '').strip()
#                 retest_mic_operand = (retest_mic_operand or '').strip()

#                 # Convert `retest_disk_value` safely
#                 retest_disk_value = int(retest_disk_value) if retest_disk_value and retest_disk_value.strip().isdigit() else None

#                 # Debugging: Print the values before saving
#                 print(f"Saving values for Retest Entry {retest.id}:", {
#                     'retest_mic_operand': retest_mic_operand,
#                     'retest_disk_value': retest_disk_value,
#                     'retest_disk_enris': retest_disk_enris,
#                     'retest_mic_value': retest_mic_value,
#                     'retest_mic_enris': retest_mic_enris,
#                     'retest_alert_mic': retest_alert_mic,
#                     'retest_alert_val': retest.Alert_val if retest_alert_mic else '',
#                 })

#                 # Get or update retest antibiotic entry
#                 retest_entry, created = AntibioticEntry.objects.update_or_create(
#                     ab_idNum_referred=isolates,
#                     ab_Retest_Abx_code=retest_abx_code,
#                     defaults={
#                         "ab_Retest_DiskValue": retest_disk_value,
#                         "ab_Retest_Disk_enRIS": retest_disk_enris,
#                         "ab_Retest_MICValue": retest_mic_value or None,
#                         "ab_Retest_MIC_enRIS": retest_mic_enris,
#                         "ab_Retest_MIC_operand": retest_mic_operand,
#                         "ab_Retest_Antibiotic": retest.Antibiotic,
#                         "ab_Retest_Abx": retest.Abx_code,
#                         "ab_Ret_R_breakpoint": retest.R_val or None,
#                         "ab_Ret_S_breakpoint": retest.S_val or None,
#                         "ab_Ret_SDD_breakpoint": retest.SDD_val or None,
#                         "ab_Ret_I_breakpoint": retest.I_val or None,
#                         "ab_Retest_AlertMIC": retest_alert_mic,
#                         "ab_Retest_Alert_val": retest.Alert_val if retest_alert_mic else "",
#                     }
#                 )

#                 retest_entry.ab_breakpoints_id.set([retest])

#             messages.success(request, "Data saved successfully.")
#             return redirect("show_data")
#         else:
#             messages.error(request, "Error: Saving unsuccessful")
#             print(form.errors)

#     # --- fallback GET render in case POST fails ---
#     form = Referred_Form(instance=isolates)
#     existing_entries = AntibioticEntry.objects.filter(ab_idNum_referred=isolates)
#     return render(request, "home/Referred_form.html", {
#         "form": form,
#         "whonet_abx_data": whonet_abx_data,
#         "whonet_retest_data": whonet_retest_data,
#         "edit_mode": True,
#         "isolates": isolates,
#         "existing_entries": existing_entries,
#         "retest_entries": retest_entries,

#     })


# @login_required(login_url="/login/")
# def edit_data(request, id):
#     # Fetch the Referred_Data instance to edit
#     isolates = get_object_or_404(Referred_Data, pk=id)

#     # Fetch related data for antibiotics
  
#     whonet_abx_data = BreakpointsTable.objects.filter(Show=True)
#     whonet_retest_data = BreakpointsTable.objects.filter(Retest=True)

#     if request.method == 'POST':
#         # Print received data for debugging
#         print("POST Data:", request.POST)

#         form = Referred_Form(request.POST, instance=isolates)
#         if form.is_valid():
#             isolates = form.save(commit=False)

#             # Update or Create Antibiotic Entries (whonet_abx_data)
#             for entry in whonet_abx_data:
#                 abx_code = entry.Whonet_Abx

#                 # Fetch user input values for MIC and Disk
#                 if entry.Disk_Abx:
#                     disk_value = request.POST.get(f'disk_{entry.id}')
#                     disk_enris = request.POST.get(f'disk_enris_{entry.id}') 
#                     mic_value = ''
#                     mic_enris = ''
#                     mic_operand = ''
#                     alert_mic = False  
#                 else:
#                     mic_value = request.POST.get(f'mic_{entry.id}')
#                     mic_enris = request.POST.get(f'mic_enris_{entry.id}') 
#                     mic_operand = request.POST.get(f'mic_operand_{entry.id}')
#                     alert_mic = f'alert_mic_{entry.id}' in request.POST
#                     disk_value = ''
#                     disk_enris = ''
                
#                 # Check and update mic_operand if needed
#                 disk_enris = (disk_enris or '').strip() # Ensure it's a string and strip whitespace
#                 mic_enris = (mic_enris or '').strip()
#                 mic_operand = (mic_operand or '').strip()

#                 # Convert `disk_value` safely # Convert to int if valid, else None
#                 disk_value = int(disk_value) if disk_value and disk_value.strip().isdigit() else None 

#                 # Debugging: Print the values before saving
#                 print(f"Saving values for Antibiotic Entry {entry.id}:", {
#                     'mic_operand': mic_operand,
#                     'disk_value': disk_value,
#                     'disk_enris': disk_enris,
#                     'mic_value': mic_value,
#                     'mic_enris': mic_enris,
#                 })

#                 # Get or update antibiotic entry
#                 antibiotic_entry, created = AntibioticEntry.objects.update_or_create(
#                     ab_idNum_referred=isolates,
#                     ab_Abx_code=abx_code,
#                     defaults={
#                         "ab_AccessionNo": isolates.AccessionNo,
#                         "ab_Antibiotic": entry.Antibiotic,
#                         "ab_Abx": entry.Abx_code,
#                         "ab_Disk_value": disk_value,
#                         "ab_Disk_enRIS": disk_enris,
#                         "ab_MIC_value": mic_value or None,
#                         "ab_MIC_enRIS": mic_enris,
#                         "ab_MIC_operand": mic_operand,
#                         "ab_R_breakpoint": entry.R_val or None,
#                         "ab_I_breakpoint": entry.I_val or None,
#                         "ab_SDD_breakpoint": entry.SDD_val or None,
#                         "ab_S_breakpoint": entry.S_val or None,
#                         "ab_AlertMIC": alert_mic,
#                         "ab_Alert_val": entry.Alert_val if alert_mic else '',
#                     }
#                 )

#                 antibiotic_entry.ab_breakpoints_id.set([entry.pk])

#             # Separate loop for Retest Data
#             for retest in whonet_retest_data:
#                 retest_abx_code = retest.Whonet_Abx

#                 # Fetch user input values for MIC and Disk
#                 if retest.Disk_Abx:
#                     retest_disk_value = request.POST.get(f'retest_disk_{retest.id}')
#                     retest_disk_enris = request.POST.get(f"retest_disk_enris_{retest.id}") or ""
#                     retest_mic_value = ''
#                     retest_mic_enris = ''
#                     retest_mic_operand = ''
#                     retest_alert_mic = False
#                 else:
#                     retest_mic_value = request.POST.get(f'retest_mic_{retest.id}')
#                     retest_mic_enris = request.POST.get(f"retest_mic_enris_{retest.id}") or ""
#                     retest_mic_operand = request.POST.get(f'retest_mic_operand_{retest.id}')
#                     retest_alert_mic = f'retest_alert_mic_{retest.id}' in request.POST
#                     retest_disk_value = ''
#                     retest_disk_enris = ''

#                 # Check and update retest mic_operand if needed
#                 retest_disk_enris = (retest_disk_enris or '').strip() # Ensure it's a string and strip whitespace
#                 retest_mic_enris = (retest_mic_enris or '').strip()
#                 retest_mic_operand = (retest_mic_operand or '').strip()

#                 # Convert `retest_disk_value` safely
#                 retest_disk_value = int(retest_disk_value) if retest_disk_value and retest_disk_value.strip().isdigit() else None

#                 # Debugging: Print the values before saving
#                 print(f"Saving values for Retest Entry {retest.id}:", {
#                     'retest_mic_operand': retest_mic_operand,
#                     'retest_disk_value': retest_disk_value,
#                     'retest_disk_enris': retest_disk_enris,
#                     'retest_mic_value': retest_mic_value,
#                     'retest_mic_enris': retest_mic_enris,
#                     'retest_alert_mic': retest_alert_mic,
#                     'retest_alert_val': retest.Alert_val if retest_alert_mic else '',
#                 })

#                 # Get or update retest antibiotic entry
#                 retest_entry, created = AntibioticEntry.objects.update_or_create(
#                     ab_idNum_referred=isolates,
#                     ab_Retest_Abx_code=retest_abx_code,
#                     defaults={
#                         "ab_Retest_DiskValue": retest_disk_value,
#                         "ab_Retest_Disk_enRIS": retest_disk_enris,
#                         "ab_Retest_MICValue": retest_mic_value or None,
#                         "ab_Retest_MIC_enRIS": retest_mic_enris,
#                         "ab_Retest_MIC_operand": retest_mic_operand,
#                         "ab_Retest_Antibiotic": retest.Antibiotic,
#                         "ab_Retest_Abx": retest.Abx_code,
#                         "ab_Ret_R_breakpoint": retest.R_val or None,
#                         "ab_Ret_S_breakpoint": retest.S_val or None,
#                         "ab_Ret_SDD_breakpoint": retest.SDD_val or None,
#                         "ab_Ret_I_breakpoint": retest.I_val or None,
#                         "ab_Retest_AlertMIC": retest_alert_mic,
#                         "ab_Retest_Alert_val": retest.Alert_val if retest_alert_mic else "",
#                     }
#                 )

#                 retest_entry.ab_breakpoints_id.set([retest])

#             messages.success(request, "Data saved successfully.")
#             return redirect("show_data")
#         else:
#             messages.error(request, "Error: Saving unsuccessful")
#             print(form.errors)

#     # --- fallback GET render in case POST fails ---
#     form = Referred_Form(instance=isolates)
#     existing_entries = AntibioticEntry.objects.filter(ab_idNum_referred=isolates)
#     return render(request, "home/Referred_form.html", {
#         "form": form,
#         "whonet_abx_data": whonet_abx_data,
#         "whonet_retest_data": whonet_retest_data,
#         "edit_mode": True,
#         "isolates": isolates,
#         "existing_entries": existing_entries,
#         "retest_entries": retest_entries,

#     })


@login_required(login_url="/login/")
def edit_data(request, id):
    # --- Fetch antibiotics lists ---
    whonet_abx_data = BreakpointsTable.objects.filter(Show=True)
    whonet_retest_data = BreakpointsTable.objects.filter(Retest=True)

    # --- Get the isolate record ---
    isolates = get_object_or_404(Referred_Data, pk=id)

    # Fetch all entries in one query
    all_entries = AntibioticEntry.objects.filter(ab_idNum_referred=isolates)

    # Separate them based on the 'retest' condition
    existing_entries = all_entries.filter(ab_Abx_code__isnull=False)  # Regular entries
    retest_entries = all_entries.filter(ab_Retest_Abx_code__isnull=False)   # Retest entries

    # --- Handle GET request ---
    if request.method == "GET":
        form = Referred_Form(instance=isolates)
        return render(request, "home/Referred_form.html", {
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
                antibiotic_entry, created = AntibioticEntry.objects.update_or_create(
                    ab_idNum_referred=isolates,
                    ab_Abx_code=abx_code,
                    defaults={
                        "ab_AccessionNo": isolates.AccessionNo,
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
                retest_entry, created = AntibioticEntry.objects.update_or_create(
                    ab_idNum_referred=isolates,
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
    form = Referred_Form(instance=isolates)
    existing_entries = AntibioticEntry.objects.filter(ab_idNum_referred=isolates)
    return render(request, "home/Referred_form.html", {
        "form": form,
        "whonet_abx_data": whonet_abx_data,
        "whonet_retest_data": whonet_retest_data,
        "edit_mode": True,
        "isolates": isolates,
        "existing_entries": existing_entries,
        "retest_entries": retest_entries,

    })


#Deleting Data
@login_required(login_url="/login/")
def delete_data(request, id):
    isolate = get_object_or_404(Referred_Data, pk=id)

    isolate.delete()
    return redirect('show_data')




def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access images and static files.
    """
    sUrl = settings.STATIC_URL      # Typically /static/
    sRoot = settings.STATIC_ROOT    # Path to static folder
    mUrl = settings.MEDIA_URL       # Typically /media/
    mRoot = settings.MEDIA_ROOT     # Path to media folder

    if uri.startswith(mUrl):
        path = os.path.join(mRoot, uri.replace(mUrl, ""))
    elif uri.startswith(sUrl):
        path = os.path.join(sRoot, uri.replace(sUrl, ""))
    else:
        return uri  # Absolute URL (http://...)

    if not os.path.isfile(path):
        raise Exception('File not found: %s' % path)

    return path


@login_required(login_url="/login/")
def generate_pdf(request, id):
    # Get the record from the database using the provided ID
    isolate = get_object_or_404(Referred_Data, pk=id)
    
    # Fetch related antibiotic entries
    antibiotic_entries = AntibioticEntry.objects.filter(ab_idNumber_egasp=isolate)

    # Debugging: Print antibiotic entries to verify data
    print("Antibiotic Entries Count:", antibiotic_entries.count())
    for entry in antibiotic_entries:
        print("Antibiotic Entry:", entry.ab_Abx_code, entry.ab_Disk_value, entry.ab_MIC_value, entry.ab_Retest_MICValue)

    # Use the static URL for the logo
    logo_path = static("assets/img/brand/arsplogo.jpg")

    # Debugging: Check if the logo file exists
    absolute_logo_path = os.path.join(settings.STATIC_ROOT, "assets/img/brand/arsplogo.jpg").replace("\\", "/").strip()
    if not os.path.exists(absolute_logo_path):
        print(f"Logo file not found at: {absolute_logo_path}")
        logo_path = ""  # Set to None if the file does not exist

    context = {
        'isolate': isolate,
        'antibiotic_entries': antibiotic_entries,
        'now': timezone.now(),  # Add current time to context
        'logo_path': logo_path,  # Use the static URL
    }
    
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    
    # Name the PDF for download or preview
    response['Content-Disposition'] = 'filename="Lab_Result_Report.pdf"'
    
    # Find the template and render it
    template_path = 'home/Lab_result.html'
    template = get_template(template_path)
    html = template.render(context)

    # Debugging: Print rendered HTML to verify template rendering
    print("Rendered HTML:", html[:500])  # Print the first 500 characters of the rendered HTML

    # Generate PDF using Pisa
    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)

    # Check for errors during PDF generation
    if pisa_status.err:
        print("Pisa Error:", pisa_status.err)
        return HttpResponse(f'Error in generating PDF: {html}')
    
    return response



@login_required(login_url="/login/")
# generate gram stain
def generate_gs(request, id):
    # Get the record from the database using the provided ID
    try:
        isolate = Referred_Data.objects.get(pk=id)
    except Referred_Data.DoesNotExist:
        return HttpResponse("Error: Data not found.", status=404)
    
    # Context data to pass to the template
    context = {
        'isolate': isolate,
        'now': timezone.now(),  # Current timestamp
    }

    # Create a Django response object with PDF content type
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="Gram_Stain_Report.pdf"'

    # Load and render the template
    template_path = 'home/GS_result.html'  # Adjust if needed
    template = get_template(template_path)
    html = template.render(context)

    # Generate PDF using Pisa
    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)

    # Check for errors
    if pisa_status.err:
        return HttpResponse(f'Error generating PDF: {html}')

    return response




@login_required(login_url="/login/")
# for Quick search
def search(request):
   query = request.GET.get('q')
   items = Referred_Data.objects.filter(AccessionNo__icontains=query)
   return render (request, 'home/search_results.html',{'items': items, 'query':query})


###################### done  edited start #################

@login_required(login_url="/login/")
# FOR DROPDOWN ITEMS (Site Code)  
def add_dropdown(request):
    if request.method == "POST":
        form = SiteCode_Form(request.POST)  
        if form.is_valid():           
            form.save()  
            messages.success(request, 'Added Successfully')
            return redirect('add_dropdown')  # Redirect after successful POST
            
            
        else:
            messages.error(request, 'Error / Adding Unsuccessful')
            print(form.errors)
    else:
        form = SiteCode_Form()  # Show an empty form for GET request

    # Fetch clinic data from the database for dropdown options
    site_items = SiteData.objects.all()
    
    return render(request, 'home/SiteCodeForm.html', {'form': form, 'site_items': site_items})

@login_required(login_url="/login/")
def delete_dropdown(request, id):
    site_items = get_object_or_404(SiteData, pk=id)
    site_items.delete()
    return redirect('site_view')

@login_required(login_url="/login/")
def site_view(request):
    site_items = SiteData.objects.all()  # Fetch all clinic data
    return render(request, 'home/SiteCodeView.html', {'site_items': site_items})

################## done edited finish  ##########################





@login_required(login_url="/login/")
# auto generate clinic_code based on javascript
def get_clinic_code(request):
    site_code = request.GET.get('site_code')
    site_name = SiteData.objects.filter(SiteCode=site_code).values_list('SiteName', flat=True).first()
    return JsonResponse({'site_name': site_name})


@login_required(login_url="/login/")
def add_breakpoints(request, pk=None):
    breakpoint = None  # Initialize breakpoint to avoid UnboundLocalError
    upload_form = Breakpoint_uploadForm()

    if pk:  # Editing an existing breakpoint
        breakpoint = get_object_or_404(BreakpointsTable, pk=pk)
        form = BreakpointsForm(request.POST or None, instance=breakpoint)
        editing = True
    else:  # Adding a new breakpoint
        form = BreakpointsForm(request.POST or None)
        editing = False

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Update Successful")
            return redirect('breakpoints_view')  # Redirect to avoid form resubmission

    return render(request, 'home/Breakpoints.html', {
        'form': form,
        'editing': editing,  # Pass editing flag to template
        'breakpoint': breakpoint,  # Pass breakpoint even if None
        'upload_form': upload_form,
    })

@login_required(login_url="/login/")
#View existing breakpoints
def breakpoints_view(request):
    breakpoints = BreakpointsTable.objects.all().order_by('-Date_Modified')
    paginator = Paginator(breakpoints, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'home/BreakpointsView.html',{ 'breakpoints':breakpoints,  'page_obj': page_obj})

@login_required(login_url="/login/")
#Delete breakpoints
def breakpoints_del(request, id):
    breakpoints = get_object_or_404(BreakpointsTable, pk=id)
    breakpoints.delete()
    return redirect('breakpoints_view')

@login_required(login_url="/login/")
# for uploading and replacing existing breakpoints data
def upload_breakpoints(request):
    if request.method == "POST":
        upload_form = Breakpoint_uploadForm(request.POST, request.FILES)
        if upload_form.is_valid():
            # Save the uploaded file instance
            uploaded_file = upload_form.save()
            file = uploaded_file.File_uploadBP  # Get the actual file field
            print("Uploaded file:", file)  # Debugging statement
            try:
                # Load file into a DataFrame using file's temporary path
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)  # For CSV files
                    
                elif file.name.endswith('.xlsx'):
                    df = pd.read_excel(file)  # For Excel files

                else:
                    messages.error(request, messages.INFO, 'Unsupported file format. Please upload a CSV or Excel file.')
                    return redirect('upload_breakpoints')

                # Check the DataFrame for debugging
                print(df)
                
                # Check the DataFrame for debugging
                print("DataFrame contents:\n", df.head())  # Print the first few rows

                # Check column and Replace NaN values with empty strings to avoid validation errors
                df.fillna(value={col: "" for col in df.columns}, inplace=True)


                 # Use this to Clear existing records with matching Whonet_Abx values
                whonet_abx_values = df['Whonet_Abx'].unique()
                BreakpointsTable.objects.filter(Whonet_Abx__in=whonet_abx_values).delete()


                # Insert rows into BreakpointsTable
                for _, row in df.iterrows():
                    # Parse Date_Modified if it's present and valid
                    date_modified = None
                    if row.get('Date_Modified'):
                        date_modified = pd.to_datetime(row['Date_Modified'], errors='coerce')
                        if pd.isna(date_modified):
                            date_modified = None

                    # Create a new instance of BreakpointsTable
                    BreakpointsTable.objects.create(
                        Show=bool(row.get('Show', False)),
                        Retest=bool(row.get('Retest', False)),
                        Disk_Abx=bool(row.get('Disk_Abx', False)),
                        Guidelines=row.get('Guidelines', ''),
                        Tier=row.get('Tier', ''),
                        Test_Method=row.get('Test_Method', ''),
                        Potency=row.get('Potency', ''),
                        Abx_code=row.get('Abx_code', ''),
                        Antibiotic=row.get('Antibiotic', ''),
                        Alert_val=row.get('Alert_val',''),
                        Whonet_Abx=row.get('Whonet_Abx', ''),
                        R_val=row.get('R_val', ''),
                        I_val=row.get('I_val', ''),
                        SDD_val=row.get('SDD_val', ''),
                        S_val=row.get('S_val', ''),
                        Date_Modified=date_modified,
                    )
                
                messages.success(request, messages.INFO, 'File uploaded and data added successfully to the database!')
                return redirect('breakpoints_view')

            except Exception as e:
                print("Error during processing:", e)  # Debug statement
                messages.error(request, f"Error processing file: {e}")
                return redirect('add_breakpoints')
        else:
            messages.error(request, messages.INFO, "Form is not valid.")

    else:
        upload_form = Breakpoint_uploadForm()

    return render(request, 'home/Breakpoints.html', {'upload_form': upload_form})

@login_required(login_url="/login/")
#for exporting into excel
def export_breakpoints(request):
    objects = BreakpointsTable.objects.all()
    data = []

    for obj in objects:
        data.append({
            "Show": obj.Show,
            "Retest": obj.Retest,
            "Disk_Abx": obj.Disk_Abx,
            "Guidelines": obj.Guidelines,
            "Tier": obj.Tier,
            "Test_Method": obj.Test_Method,
            "Potency": obj.Potency,
            "Abx_code": obj.Abx_code,
            "Antibiotic": obj.Antibiotic,
            "Alert_val": obj.Alert_val,
            "Whonet_Abx": obj.Whonet_Abx,
            "R_val": obj.R_val,
            "I_val": obj.I_val,
            "SDD_val": obj.SDD_val,
            "S_val": obj.S_val,
            "Date_Modified": obj.Date_Modified,
        })
    
    # Define file path
    file_path = "Breakpoints_egasp.xlsx"

    # Convert data to DataFrame and save as Excel
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False)

    # Return the file as a response
    return FileResponse(open(file_path, "rb"), as_attachment=True, filename="Breakpoints_egasp.xlsx")

@login_required(login_url="/login/")
def delete_all_breakpoints(request):
    BreakpointsTable.objects.all().delete()
    messages.success(request, "All records have been deleted successfully.")
    return redirect('breakpoints_view')  # Redirect to the table view


@login_required(login_url="/login/")
def abxentry_view(request):
    entries = AntibioticEntry.objects.filter(ab_Retest_Abx_code__isnull=True)
    abx_data = {}
    abx_codes = set()

    for entry in entries:
        accession_no = entry.ab_AccessionNo
        abx_code = entry.ab_Abx_code  # Only ordinary antibiotic (excluding retest antibiotics)

        # Get all values and interpretations for ordinary antibiotics
        value = entry.ab_Disk_value or entry.ab_MIC_value
        RIS = entry.ab_Disk_RIS or entry.ab_MIC_RIS
        Operand = entry.ab_MIC_operand or None

        if accession_no not in abx_data:
            abx_data[accession_no] = {}

        # Store only **ordinary** antibiotic values
        if abx_code:  
            abx_data[accession_no][abx_code] = {'value': value, 'RIS': RIS, 'Operand': Operand}
            abx_codes.add(abx_code)  # Add only ordinary antibiotics

    context = {
        'abx_data': abx_data,
        'abx_codes': sorted(abx_codes),  # Sorted list of ordinary antibiotics
    }
    
    return render(request, 'home/AntibioticentryView.html', context)




@login_required(login_url="/login/")
# View to display all specimen types
def specimen_list(request):
    specimen_items = SpecimenTypeModel.objects.all()
    return render(request, 'home/SpecimenView.html', {'specimen_items': specimen_items})

@login_required(login_url="/login/")
# View to add or edit a specimen type
def add_specimen(request):
    if request.method == 'POST':
        form = SpecimenTypeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('add_specimen')  # Redirect after saving
    else:
        form = SpecimenTypeForm()  # Empty form for new specimen
    
    return render(request, 'home/Specimentype.html', {'form': form})

@login_required(login_url="/login/")
# Edit an existing specimen
def edit_specimen(request, pk):
    specimen = get_object_or_404(SpecimenTypeModel, pk=pk)

    if request.method == 'POST':
        form = SpecimenTypeForm(request.POST, instance=specimen)  # Pre-fill with existing data
        if form.is_valid():
            form.save()
            return redirect('specimen_list')  # Redirect after saving
    else:
        form = SpecimenTypeForm(instance=specimen)  # Load existing data
    
    return render(request, 'home/SpecimenEdit.html', {'form': form, 'specimen': specimen})


@login_required(login_url="/login/")
# View to delete a specimen type
def delete_specimen(request, pk):
    specimen = get_object_or_404(SpecimenTypeModel, pk=pk)
    specimen.delete()
    return redirect('specimen_list')




@login_required(login_url="/login/")
def export_Antibioticentry(request):
    objects = AntibioticEntry.objects.all()
    data = []

    for obj in objects:
        data.append({
            "ab_idNumber_egasp": obj.ab_idNum_referred.AccessionNo if obj.ab_idNum_referred else None,
            "Accession_No": obj.ab_AccessionNo,
            "Antibiotic": obj.ab_Antibiotic,
            "Abx_code": obj.ab_Abx_code,
            "Abx": obj.ab_Abx,
            "Disk_value": obj.ab_Disk_value,
            "Disk_RIS": obj.ab_Disk_RIS,
            "MIC_operand": obj.ab_MIC_operand,
            "MIC_value": obj.ab_MIC_value,
            "MIC_RIS": obj.ab_MIC_RIS,
            "Retest_Antibiotic": obj.ab_Retest_Antibiotic,
            "Retest_Abx_code": obj.ab_Retest_Abx_code,
            "Retest_Abx": obj.ab_Retest_Abx,
            "Retest_DiskValue": obj.ab_Retest_DiskValue,
            "Retest_Disk_RIS": obj.ab_Retest_Disk_RIS,
            "Ret_MIC_Operand": obj.ab_Retest_MIC_operand,
            "Retest_MICValue": obj.ab_Retest_MICValue,
            "Retest_MIC_RIS": obj.ab_Retest_MIC_RIS,
        })
    
    # Define file path
    file_path = "AntibioticEntry_referred.xlsx"

    # Convert data to DataFrame and save as Excel
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False)

    # Return the file as a response
    return FileResponse(open(file_path, "rb"), as_attachment=True, filename="AntibioticEntry_referred.xlsx")


@login_required(login_url="/login/")
#Address Book
#Contact Form not working
def add_contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)  
        if form.is_valid():           
            form.save()  
            messages.success(request, 'Added Successfully')
            return redirect('add_contact')  # Redirect after successful POST
            
            
        else:
            messages.error(request, 'Error / Adding Unsuccessful')
            print(form.errors)
    else:
        form = ContactForm()  # Show an empty form for GET request

    # Fetch clinic data from the database for dropdown options
    contacts = arsStaff_Details.objects.all()
    
    return render(request, 'home/Contact_Form.html', {'form': form, 'contacts': contacts})


@login_required(login_url="/login/")
def delete_contact(request, id):
    contact_items = get_object_or_404(arsStaff_Details, pk=id)
    contact_items.delete()
    return redirect('contact_view')


@login_required(login_url="/login/")
def contact_view(request):
    contact_items = arsStaff_Details.objects.all()  # Fetch all contact data
    return render(request, 'home/Contact_View.html', {'contact_items': contact_items})


@login_required(login_url="/login/")
def get_ars_staff_details(request):
    ars_staff_name = request.GET.get('ars_staff_id')
    license_field = request.GET.get('license_field')  # NEW: dynamic field key

    ars_staff_details = arsStaff_Details.objects.filter(
        Staff_Name=ars_staff_name
    ).values('Staff_License').first()

    if ars_staff_details:
        return JsonResponse({
            license_field: str(ars_staff_details['Staff_License'])  # dynamic key
        })
    else:
        return JsonResponse({'error': 'Staff not found'}, status=404)

    

@login_required(login_url="/login/")
#for province and city fields
def upload_locations(request):
    if request.method == "POST":
        upload_form = LocationUploadForm(request.POST, request.FILES)
        
        if upload_form.is_valid():
            uploaded_file = upload_form.save()
            file = uploaded_file.file  # Get the uploaded file
            
            print("Uploaded file:", file)  # Debugging statement

            try:
                # Load file into a DataFrame based on file type
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                elif file.name.endswith('.xlsx'):
                    df = pd.read_excel(file)
                else:
                    messages.error(request, 'Unsupported file format. Please upload a CSV or Excel file.')
                    return redirect('upload_locations')

                print("DataFrame contents:\n", df.head())  # Debugging statement

                # Fill NaN values to avoid errors
                df.fillna("", inplace=True)

                # Loop through rows and save Provinces and Cities
                for _, row in df.iterrows():
                    provincename = row.get('Province', '').strip()
                    cityname = row.get('City', '').strip()

                    if not provincename or not cityname:
                        continue  # Skip empty rows

                    # Get or create province
                    province, _ = Province.objects.get_or_create(provincename=provincename)

                    # Get or create city linked to the province
                    City.objects.get_or_create(cityname=cityname, province=province)

                messages.success(request, "File uploaded successfully and data added!")
                return redirect('add_location')

            except Exception as e:
                print("Error:", e)
                messages.error(request, f"Error processing file: {e}")
                return redirect('upload_locations')
        else:
            messages.error(request, "Invalid form submission.")

    else:
        upload_form = LocationUploadForm()

    return render(request, 'home/Add_location.html', {'upload_form': upload_form})


@login_required(login_url="/login/")
def add_location(request, id=None):
    provinces = Province.objects.all()  # Renamed 'province' to 'provinces' for clarity
    upload_form = LocationUploadForm()  
    if request.method == "POST":
        form = CityForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Location added successfully!")
            return redirect("add_location")  # Use the correct URL name
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CityForm()

    return render(request, "home/Add_location.html", {"form": form, "provinces": provinces, "upload_form": upload_form})



def TAT_process(request, id=None):
    process = TATprocess.objects.all()  # Renamed 'province' to 'provinces' for clarity
    upload_form = TATUploadForm()  
    if request.method == "POST":
        form = TAT_form(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Location added successfully!")
            return redirect("TAT_process")  # Use the correct URL name
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = TAT_form()

    return render(request, "home/Add_TAT.html", {"form": form, "process": process, "upload_form": upload_form})







@login_required(login_url="/login/")
def view_locations(request):
    # Fetch all provinces, sorted by province name
    provinces = Province.objects.prefetch_related(
        Prefetch('cities', queryset=City.objects.order_by('cityname'))  # Sort cities by city name
    ).order_by('provincename')  # Sort provinces by province name

    return render(request, 'home/view_locations.html', {'provinces': provinces})


@login_required(login_url="/login/")
def delete_cities(request):
    City.objects.all().delete()
    Province.objects.all().delete()
    messages.success(request, "All records have been deleted successfully.")
    return redirect('view_locations')  # Redirect to the table view

@login_required(login_url="/login/")
def delete_city(request, id):
    city_items = get_object_or_404(City, pk=id)
    city_items.delete()
    return redirect('view_locations')

@login_required(login_url="/login/")
#download combined table
def download_combined_table(request):
    # Fetch all Egasp_Data entries
    referred_data_entries = Referred_Data.objects.all()

    # Fetch all unique antibiotic codes (both initial and retest), excluding None values
    unique_antibiotics_raw = (
        AntibioticEntry.objects
        .values_list('ab_Abx_code', 'ab_Edit_Abx_code')
        .distinct()
    )

    # Flatten and clean the list (avoid duplicates)
    antibiotic_set = set()
    for abx_code, retest_code in unique_antibiotics_raw:
        if abx_code:
            antibiotic_set.add(abx_code)
        if retest_code:
            antibiotic_set.add(retest_code)

    # Sort the antibiotics alphabetically
    sorted_antibiotics = sorted(antibiotic_set)

    # Create the HTTP response for CSV download
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="combined_table.csv"'

    # Create a CSV writer
    writer = csv.writer(response)

    # Write the header row
    header = [
       "Hide", "Copy_data", "Batch_Name", "Batch_Code", "Date_of_Entry", "RefNo", 
        "BatchNo", "Total_batch", "AccessionNo", "AccessionNoGen", "Default_Year", 
        "SiteCode", "Site_Name", "Site_NameGen", "Referral_Date", "Patient_ID", 
        "First_Name", "Mid_Name", "Last_Name", "Date_Birth", "Age", "Age_Verification", 
        "Sex", "Date_Admis", "Nosocomial", "Diagnosis", "Diagnosis_ICD10", "Ward", 
        "Service_Type", "Spec_Num", "Spec_Date", "Spec_Type", "Reason", "Growth", 
        "Urine_ColCt", "ampC", "ESBL", "CARB", "MBL", "BL", "MR", "mecA", "ICR", 
        "OtherResMech", "Site_Pre", "Site_Org", "Site_Pos", "OrganismCode", "Comments", 
        "ars_ampC", "ars_ESBL", "ars_CARB", "ars_ECIM", "ars_MCIM", "ars_EC_MCIM", 
        "ars_MBL", "ars_BL", "ars_MR", "ars_mecA", "ars_ICR", "ars_Pre", "ars_Post", 
        "ars_OrgCode", "ars_OrgName", "ars_ct_ctl", "ars_tz_tzl", "ars_cn_cni", 
        "ars_ip_ipi", "ars_reco_Code", "ars_reco", "SiteName", "Status", "Month_Date", 
        "Day_Date", "Year_Date", "RefDate", "Start_AccNo", "End_AccNo", "No_Isolates", 
        "BatchNumber", "TotalBatchNumber", "Encoded_by", "Encoded_by_Initials", "Edited_by", 
        "Edited_by_Initials", "Checked_by", "Checked_by_Initials", "Verified_by_Senior", 
        "Verified_by_Senior_Initials", "Verified_by_LabManager", "Verified_by_LabManager_Initials", 
        "Noted_by", "Noted_by_Initials", "Concordance_Check", "Concordance_by", "Concordance_by_Initials", 
        "abx_code", "Laboratory_Staff", "Date_Accomplished_ARSP", "ars_notes", "ars_contact", 
        "ars_email", "arsp_Encoder", "arsp_Enc_Lic", "arsp_Checker", "arsp_Chec_Lic", 
        "arsp_Verifier", "arsp_Ver_Lic", "arsp_LabManager", "arsp_Lab_Lic", "arsp_Head", "arsp_Head_Lic"
]
    # Add antibiotic-related headers
    for abx in sorted_antibiotics:
        is_disk_abx = BreakpointsTable.objects.filter(Whonet_Abx=abx, Disk_Abx=True).exists()
        if not is_disk_abx:  # Add _Op fields only for MIC antibiotics
            header.append(f'{abx}_Op')
        header.append(f'{abx}_Val')
        header.append(f'{abx}_RIS')
        if not is_disk_abx:  # Add RT_Op fields only for MIC antibiotics
            header.append(f'{abx}_RT_Op')
        header.append(f'{abx}_RT_Val')
        header.append(f'{abx}_RT_RIS')

    writer.writerow(header)

    # Now write each data row
    for egasp_entry in referred_data_entries:
        row = [
            egasp_entry.Date_of_Entry,egasp_entry.ID_Number,egasp_entry.Egasp_Id,egasp_entry.PTIDCode,egasp_entry.Laboratory,egasp_entry.Clinic,egasp_entry.Consult_Date,egasp_entry.Consult_Type,egasp_entry.Client_Type,egasp_entry.Uic_Ptid,egasp_entry.Clinic_Code,egasp_entry.ClinicCodeGen,egasp_entry.First_Name,egasp_entry.Middle_Name,egasp_entry.Last_Name,egasp_entry.Suffix,egasp_entry.Birthdate,egasp_entry.Age,egasp_entry.Sex,egasp_entry.Gender_Identity,egasp_entry.Gender_Identity_Other,egasp_entry.Occupation,egasp_entry.Civil_Status,egasp_entry.Civil_Status_Other,egasp_entry.Current_Province,egasp_entry.Current_City,egasp_entry.Current_Country,egasp_entry.Permanent_Province,egasp_entry.Permanent_City,egasp_entry.Permanent_Country,egasp_entry.Nationality,egasp_entry.Nationality_Other,egasp_entry.Travel_History,egasp_entry.Travel_History_Specify,egasp_entry.Client_Group,egasp_entry.Client_Group_Other,egasp_entry.History_Of_Sex_Partner,egasp_entry.Nationality_Sex_Partner,egasp_entry.Date_of_Last_Sex,egasp_entry.Nationality_Sex_Partner_Other,egasp_entry.Number_Of_Sex_Partners,egasp_entry.Relationship_to_Partners,egasp_entry.SB_Urethral,egasp_entry.SB_Vaginal,egasp_entry.SB_Anal_Insertive,egasp_entry.SB_Anal_Receptive,egasp_entry.SB_Oral_Insertive,egasp_entry.SB_Oral_Receptive,egasp_entry.Sharing_of_Sex_Toys,egasp_entry.SB_Others,egasp_entry.Sti_None,egasp_entry.Sti_Hiv,egasp_entry.Sti_Hepatitis_B,egasp_entry.Sti_Hepatitis_C,egasp_entry.Sti_NGI,egasp_entry.Sti_Syphilis,egasp_entry.Sti_Chlamydia,egasp_entry.Sti_Anogenital_Warts,egasp_entry.Sti_Genital_Ulcer,egasp_entry.Sti_Herpes,egasp_entry.Sti_Other,egasp_entry.Illicit_Drug_Use,egasp_entry.Illicit_Drug_Specify,egasp_entry.Abx_Use_Prescribed,egasp_entry.Abx_Use_Prescribed_Specify,egasp_entry.Abx_Use_Self_Medicated,egasp_entry.Abx_Use_Self_Medicated_Specify,egasp_entry.Abx_Use_None,egasp_entry.Abx_Use_Other,egasp_entry.Abx_Use_Other_Specify,egasp_entry.Route_Oral,egasp_entry.Route_Injectable_IV,egasp_entry.Route_Dermal,egasp_entry.Route_Suppository,egasp_entry.Route_Other,egasp_entry.Symp_With_Discharge,egasp_entry.Symp_No,egasp_entry.Symp_Discharge_Urethra,egasp_entry.Symp_Discharge_Vagina,egasp_entry.Symp_Discharge_Anus,egasp_entry.Symp_Discharge_Oropharyngeal,egasp_entry.Symp_Pain_Lower_Abdomen,egasp_entry.Symp_Tender_Testicles,egasp_entry.Symp_Painful_Urination,egasp_entry.Symp_Painful_Intercourse,egasp_entry.Symp_Rectal_Pain,egasp_entry.Symp_Other,egasp_entry.Outcome_Of_Follow_Up_Visit,egasp_entry.Prev_Test_Pos,egasp_entry.Prev_Test_Pos_Date,egasp_entry.Result_Test_Cure_Initial,egasp_entry.Result_Test_Cure_Followup,egasp_entry.NoTOC_Other_Test,egasp_entry.NoTOC_DatePerformed,egasp_entry.NoTOC_Result_of_Test,egasp_entry.Patient_Compliance_Antibiotics,egasp_entry.OtherDrugs_Specify,egasp_entry.OtherDrugs_Dosage,egasp_entry.OtherDrugs_Route,egasp_entry.OtherDrugs_Duration,egasp_entry.Gonorrhea_Treatment,egasp_entry.Treatment_Outcome,egasp_entry.Primary_Antibiotic,egasp_entry.Primary_Abx_Other,egasp_entry.Secondary_Antibiotic,egasp_entry.Secondary_Abx_Other,egasp_entry.Notes,egasp_entry.Clinic_Staff,egasp_entry.Requesting_Physician,egasp_entry.Telephone_Number,egasp_entry.Email_Address,egasp_entry.Date_Accomplished_Clinic,egasp_entry.Date_Requested_Clinic,egasp_entry.Date_Specimen_Collection,egasp_entry.Specimen_Code,egasp_entry.Specimen_Type,egasp_entry.Specimen_Quality,egasp_entry.Date_Of_Gram_Stain,egasp_entry.Diagnosis_At_This_Visit,egasp_entry.Gram_Neg_Intracellular,egasp_entry.Gram_Neg_Extracellular,egasp_entry.Gs_Presence_Of_Pus_Cells,egasp_entry.Presence_GN_Intracellular,egasp_entry.Presence_GN_Extracellular,egasp_entry.GS_Pus_Cells,egasp_entry.Epithelial_Cells,egasp_entry.GS_Date_Released,egasp_entry.GS_Others,egasp_entry.GS_Negative,egasp_entry.Date_Received_in_lab,egasp_entry.Positive_Culture_Date,egasp_entry.Culture_Result,egasp_entry.Species_Identification,egasp_entry.Other_species_ID,egasp_entry.Specimen_Quality_Cs,egasp_entry.Susceptibility_Testing_Date,egasp_entry.Retested_Mic,egasp_entry.Confirmation_Ast_Date,egasp_entry.Beta_Lactamase,egasp_entry.PPng,egasp_entry.TRng,egasp_entry.Date_Released,egasp_entry.For_possible_WGS,egasp_entry.Date_stocked,egasp_entry.Location,egasp_entry.abx_code,egasp_entry.Laboratory_Staff,egasp_entry.Date_Accomplished_ARSP,egasp_entry.ars_notes,egasp_entry.ars_contact,egasp_entry.ars_email,
        ]

        # Fetch related antibiotics for this Egasp entry, sorted
        antibiotics = AntibioticEntry.objects.filter(ab_idNumber_egasp=egasp_entry).order_by('ab_Abx_code')

        # Create a mapping for quick lookup
        abx_data = {}
        for antibiotic in antibiotics:
            if antibiotic.ab_Abx_code:
                abx_data[antibiotic.ab_Abx_code] = {
                    '_Val': antibiotic.ab_Disk_value or antibiotic.ab_MIC_value,
                    '_RIS': antibiotic.ab_Disk_RIS or antibiotic.ab_MIC_RIS,
                    '_Op': antibiotic.ab_MIC_operand or '',
                }
            if antibiotic.ab_Retest_Abx_code:
                abx_data[antibiotic.ab_Retest_Abx_code] = {
                    'RT_Val': antibiotic.ab_Retest_DiskValue or antibiotic.ab_Retest_MICValue,
                    'RT_RIS': antibiotic.ab_Retest_Disk_RIS or antibiotic.ab_Retest_MIC_RIS,
                    'RT_Op': antibiotic.ab_Retest_MIC_operand or '',
                }

        # Now add antibiotic fields in the sorted order
        for abx in sorted_antibiotics:
            is_disk_abx = BreakpointsTable.objects.filter(Whonet_Abx=abx, Disk_Abx=True).exists()
            if abx in abx_data:
                if not is_disk_abx:  # Add _Op field only for MIC antibiotics
                    row.append(abx_data[abx].get('_Op', ''))
                row.append(abx_data[abx].get('_Val', ''))
                row.append(abx_data[abx].get('_RIS', ''))
                if not is_disk_abx:  # Add RT_Op field only for MIC antibiotics
                    row.append(abx_data[abx].get('RT_Op', ''))
                row.append(abx_data[abx].get('RT_Val', ''))
                row.append(abx_data[abx].get('RT_RIS', ''))
            else:
                # If no data for this antibiotic, add empty columns
                if not is_disk_abx:
                    row.append('')  # Empty _Op field
                row.extend(['', ''])  # Empty _Val and _RIS fields
                if not is_disk_abx:
                    row.append('')  # Empty RT_Op field
                row.extend(['', ''])  # Empty RT_Val and RT_RIS fields

        writer.writerow(row)

    return response

