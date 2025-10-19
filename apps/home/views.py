# -*- encoding: utf-8 -*-

from io import TextIOWrapper
import io
import json
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
from apps.home_final.models import *
from apps.wgs_app.models import *
from .forms import *
from apps.wgs_app.forms import *
from apps.home_final.forms import *
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


######## Updates WGS_Project summary booleans for a given Referred_Data object.
######  Sets FastQ, Gambit, MLST summaries to True if the accession matches.
def update_wgs_summaries_for_referred(referred_obj):

    wgs_entries = WGS_Project.objects.filter(Ref_Accession=referred_obj)

    for wgs in wgs_entries:
        # FastQ summary
        wgs.WGS_FastqSummary = bool(wgs.WGS_FastQ_Acc) and wgs.WGS_FastQ_Acc.strip().upper() == referred_obj.AccessionNo.strip().upper()
        # Gambit summary
        wgs.WGS_GambitSummary = bool(wgs.WGS_Gambit_Acc) and wgs.WGS_Gambit_Acc.strip().upper() == referred_obj.AccessionNo.strip().upper()
        # MLST summary
        wgs.WGS_MlstSummary = bool(wgs.WGS_Mlst_Acc) and wgs.WGS_Mlst_Acc.strip().upper() == referred_obj.AccessionNo.strip().upper()
         # Checkm2 summary
        wgs.WGS_Checkm2Summary = bool(wgs.WGS_Checkm2_Acc) and wgs.WGS_Checkm2_Acc.strip().upper() == referred_obj.AccessionNo.strip().upper()
         # Assembly Scan
        wgs.WGS_AssemblySummary = bool(wgs.WGS_Assembly_Acc) and wgs.WGS_Assembly_Acc.strip().upper() == referred_obj.AccessionNo.strip().upper()
         # Amr finder plus
        wgs.WGS_AmrfinderSummary = bool(wgs.WGS_Amrfinder_Acc) and wgs.WGS_Amrfinder_Acc.strip().upper() == referred_obj.AccessionNo.strip().upper()
        
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


# @login_required(login_url="/login/")
# def batch_create_view(request):
#     """
#     Creates or overwrites a batch:
#     - If batch code exists, overwrite it accesssion numbers will be overwritten as well but if an accession doesnt match any existing accessions then add it 
#     - If not, create new.
#     Ensures no duplicates remain.
#     """
#     if request.method == "POST":
#         form = BatchTable_form(request.POST)
#         if form.is_valid():
#             instance = form.save(commit=False)

#             # --- Extract values ---
#             site_code = (instance.bat_SiteCode or "").strip()
#             referral_date_obj = instance.bat_Referral_Date
#             ref_no_raw = (instance.bat_RefNo or "").strip()
#             batch_no = instance.bat_BatchNo or ""
#             total_batch = instance.bat_Total_batch or ""
#             site_name = instance.bat_Site_NameGen or ""

#             # --- Validate required fields ---
#             if not referral_date_obj or not site_code or not ref_no_raw:
#                 messages.error(request, "Missing required fields (Site Code, Referral Date, or Ref No).")
#                 return redirect("batch_create")

#             # --- Generate accession numbers ---
#             try:
#                 year_short = referral_date_obj.strftime("%y")
#                 year_long = referral_date_obj.strftime("%m%d%Y")

#                 if "-" in ref_no_raw:  # e.g. "100-105"
#                     start_ref, end_ref = map(int, ref_no_raw.split("-"))
#                 else:
#                     start_ref = end_ref = int(ref_no_raw)
#             except ValueError:
#                 messages.error(request, "Invalid Ref No format. Use a number or range")
#                 return redirect("batch_create")

#             accession_numbers = [
#                 f"{year_short}ARS_{site_code}{str(ref).zfill(4)}"
#                 for ref in range(start_ref, end_ref + 1)
#             ]

#             # --- Generate batch code + name ---
#             batch_codegen = f"{site_code}_{year_long}_{batch_no}.{total_batch}_{ref_no_raw}"
#             auto_batch_name = batch_codegen

#             # --- Resolve site name ---
#             if not site_name and site_code:
#                 site_obj = SiteData.objects.filter(SiteCode=site_code).first()
#                 if site_obj:
#                     site_name = site_obj.SiteName

#             # --- Delete old batch if exists (overwrite) ---
#             old_batch = Batch_Table.objects.filter(bat_Batch_Code=batch_codegen).first()
#             if old_batch:
#                 # If your Referred_Data model links to Batch_Table via ForeignKey 'Batch_id', use this:
#                 Referred_Data.objects.filter(Batch_id=old_batch).delete()  # Delete related isolates

#                 old_batch.delete()

#             # --- Create new Batch_Table ---
#             batch_obj = Batch_Table.objects.create(
#                 bat_Batch_Name=auto_batch_name,
#                 bat_AccessionNo=", ".join(accession_numbers),
#                 bat_Batch_Code=batch_codegen,
#                 bat_Site_Name=site_name,
#                 bat_SiteCode=site_code,
#                 bat_Referral_Date=referral_date_obj,
#                 bat_RefNo=ref_no_raw,
#                 bat_BatchNo=batch_no,
#                 bat_Total_batch=total_batch,
#                 bat_Encoder=instance.bat_Encoder or "",
#                 bat_Enc_Lic=instance.bat_Enc_Lic or "",
#                 bat_Checker=instance.bat_Checker or "",
#                 bat_Chec_Lic=instance.bat_Chec_Lic or "",
#                 bat_Verifier=instance.bat_Verifier or "",
#                 bat_Ver_Lic=instance.bat_Ver_Lic or "",
#                 bat_LabManager=instance.bat_LabManager or "",
#                 bat_Lab_Lic=instance.bat_Lab_Lic or "",
#                 bat_Head=instance.bat_Head or "",
#                 bat_Head_Lic=instance.bat_Head_Lic or "",
#             )

#             # --- Create or overwrite Referred_Data for each accession ---
#             for acc_no in accession_numbers:
#                 with transaction.atomic():
#                     Referred_Data.objects.update_or_create(
#                         AccessionNo=acc_no,  # unique field
#                         defaults={
#                             "Batch_id": batch_obj,  # ForeignKey link
#                             "Batch_Code": batch_codegen,
#                             "Referral_Date": referral_date_obj,
#                             "RefNo": ref_no_raw,
#                             "BatchNo": batch_no,
#                             "Total_batch": total_batch,
#                             "SiteCode": site_code,
#                             "Site_Name": site_name,
#                             "Batch_Name": auto_batch_name,
#                             "arsp_Encoder": batch_obj.bat_Encoder or "",
#                             "arsp_Enc_Lic": batch_obj.bat_Enc_Lic or "",
#                             "arsp_Checker": batch_obj.bat_Checker or "",
#                             "arsp_Chec_Lic": batch_obj.bat_Chec_Lic or "",
#                             "arsp_Verifier": batch_obj.bat_Verifier or "",
#                             "arsp_Ver_Lic": batch_obj.bat_Ver_Lic or "",
#                             "arsp_LabManager": batch_obj.bat_LabManager or "",
#                             "arsp_Lab_Lic": batch_obj.bat_Lab_Lic or "",
#                             "arsp_Head": batch_obj.bat_Head or "",
#                             "arsp_Head_Lic": batch_obj.bat_Head_Lic or "",
#                         }
#                     )

#             # --- Count only this batch ---
#             total_records = Referred_Data.objects.filter(Batch_Code=batch_codegen).count()

#             messages.success(
#                 request,
#                 f"Batch '{auto_batch_name}' saved successfully with {total_records} record(s)."
#             )
#             return redirect(f"{reverse('show_batches')}?batch_code={batch_obj.bat_Batch_Code}")

#         else:
#             messages.error(request, "Batch creation failed. Please check the form.")
#     else:
#         form = BatchTable_form()

#     return render(request, "home/Batchname_form.html", {"form": form})


@login_required(login_url="/login/")
def batch_create_view(request):
    """
    Creates or overwrites a batch:
    - Overwrites data only in Batch_Table (does NOT delete Referred_Data).
    - If batch already exists, asks for confirmation before overwriting.
    - Re-links existing Referred_Data isolates to the new batch.
    """

    if request.method == "POST":
        form = BatchTable_form(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)

            # --- Extract values ---
            site_code = (instance.bat_SiteCode or "").strip()
            referral_date_obj = instance.bat_Referral_Date
            ref_no_raw = (instance.bat_RefNo or "").strip()
            batch_no = (instance.bat_BatchNo or "").strip()
            total_batch = (instance.bat_Total_batch or "").strip()
            site_name = (instance.bat_Site_NameGen or "").strip()

            # --- Validate required fields ---
            if not (referral_date_obj and site_code and ref_no_raw):
                messages.error(request, "Missing required fields (Site Code, Referral Date, or Ref No).")
                return redirect("batch_create")

            # --- Generate accession numbers ---
            try:
                year_short = referral_date_obj.strftime("%y")
                year_long = referral_date_obj.strftime("%m%d%Y")

                if "-" in ref_no_raw:
                    start_ref, end_ref = map(int, ref_no_raw.split("-"))
                    if start_ref > end_ref:
                        start_ref, end_ref = end_ref, start_ref
                else:
                    start_ref = end_ref = int(ref_no_raw)
            except ValueError:
                messages.error(request, "Invalid Ref No format. Use a number or range (e.g., 1-5).")
                return redirect("batch_create")

            accession_numbers = [
                f"{year_short}ARS_{site_code}{str(ref).zfill(4)}"
                for ref in range(start_ref, end_ref + 1)
            ]

            # --- Generate batch code and name ---
            batch_codegen = f"{site_code}_{year_long}_{batch_no}.{total_batch}_{ref_no_raw}"
            auto_batch_name = batch_codegen

            # --- Resolve site name ---
            if not site_name and site_code:
                site_obj = SiteData.objects.filter(SiteCode=site_code).first()
                if site_obj:
                    site_name = site_obj.SiteName

            # --- Check if batch already exists ---
            existing_batch = Batch_Table.objects.filter(
                Q(bat_Batch_Code=batch_codegen)
                | Q(
                    bat_SiteCode=site_code,
                    bat_BatchNo=batch_no,
                    bat_Total_batch=total_batch,
                    bat_RefNo=ref_no_raw
                )
            ).first()

            # --- Step 1: Ask for confirmation before overwriting ---
            if existing_batch and "confirm_overwrite" not in request.POST:
                messages.warning(
                    request,
                    f"Batch '{existing_batch.bat_Batch_Name}' already exists. Confirm overwrite to replace it."
                )
                return render(request, "home/Batchname_form.html", {
                    "form": form,
                    "confirm_overwrite": True,
                    "existing_batch": existing_batch,
                })

            # --- Step 2: Safe overwrite logic (does NOT delete Referred_Data) ---
            with transaction.atomic():
                # Step 2.1: Find any Referred_Data records matching the new accession numbers
                existing_refs = Referred_Data.objects.filter(AccessionNo__in=accession_numbers)

                # Step 2.2: If those exist, delete their Batch_Table entries (if any)
                existing_batch_ids = existing_refs.values_list("Batch_id", flat=True).distinct()
                if existing_batch_ids:
                    Batch_Table.objects.filter(id__in=existing_batch_ids).delete()

                # Step 2.3: Also check for matching batch code (if already existing)
                existing_batch = Batch_Table.objects.filter(bat_Batch_Code=batch_codegen).first()
                if existing_batch:
                    existing_batch.delete()

                # Step 2.4: Now create a new batch cleanly
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
                    bat_Encoder=(instance.bat_Encoder or "").strip(),
                    bat_Enc_Lic=(instance.bat_Enc_Lic or "").strip(),
                    bat_Checker=(instance.bat_Checker or "").strip(),
                    bat_Chec_Lic=(instance.bat_Chec_Lic or "").strip(),
                    bat_Verifier=(instance.bat_Verifier or "").strip(),
                    bat_Ver_Lic=(instance.bat_Ver_Lic or "").strip(),
                    bat_LabManager=(instance.bat_LabManager or "").strip(),
                    bat_Lab_Lic=(instance.bat_Lab_Lic or "").strip(),
                    bat_Head=(instance.bat_Head or "").strip(),
                    bat_Head_Lic=(instance.bat_Head_Lic or "").strip(),
                )

                # Step 2.5: Re-link all existing isolates with the new batch
                Referred_Data.objects.filter(AccessionNo__in=accession_numbers).update(Batch_id=batch_obj)

                # Step 2.6: Create missing accessions (if new range includes more)
                for acc_no in accession_numbers:
                    Referred_Data.objects.update_or_create(
                        AccessionNo=acc_no,
                        defaults={
                            "Batch_id": batch_obj,
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

            # --- Count and success message ---
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
    # Prefetch isolates if your Batch_Table is linked via ForeignKey
    isolate_qs = Referred_Data.objects.only(
        "id", "AccessionNo", "SiteCode", "Patient_ID", "OrganismCode", "Batch_id"
    )

    batches = (
        Batch_Table.objects.all()
        .order_by("-bat_Referral_Date")
        .prefetch_related(
            Prefetch("Batch_isolates", queryset=isolate_qs, to_attr="prefetched_isolates")
        )
    )

    total_accessions_all = 0

    for batch in batches:
        # Start with isolates from Referred_Data
        if getattr(batch, "prefetched_isolates", None):
            isolates = batch.prefetched_isolates
        else:
            isolates = []

        # Fallback: use bat_AccessionNo if Referred_Data has no isolates
        if not isolates and batch.bat_AccessionNo:
            parsed_acc = [acc.strip() for acc in batch.bat_AccessionNo.split(",") if acc.strip()]
            # Create fake isolate-like objects for display
            isolates = [{"AccessionNo": acc, "SiteCode": batch.bat_Site_Name} for acc in parsed_acc]

        # Attach isolates to the batch object for template use
        batch.display_isolates = isolates
        batch.total_isolates = len(isolates)
        total_accessions_all += len(isolates)

    total_batches = len(batches)

    return render(
        request,
        "home/review_batches.html",
        {
            "batches": batches,
            "total_batches": total_batches,
            "total_accessions_all": total_accessions_all,
        },
    )


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


############## Raw data view

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


########### edit data view
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
    
    return render(request, 'home/SiteCodeForm.html', {'form': form, 'site_items': site_items, 'upload_form': SiteCode_uploadForm()})

@login_required(login_url="/login/")
def delete_dropdown(request, id):
    site_items = get_object_or_404(SiteData, pk=id)
    site_items.delete()
    return redirect('site_view')

def delete_all_dropdown(request):
    SiteData.objects.all().delete()
    messages.success(request, "All site codes were deleted successfully.")
    return redirect('site_view')

@login_required(login_url="/login/")
def site_view(request):
    site_items = SiteData.objects.all()  # Fetch all clinic data
    paginator = Paginator(site_items, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'home/SiteCodeView.html', {'page_obj': page_obj})

def upload_sitecode(request):
    if request.method == "POST":
        upload_form = SiteCode_uploadForm(request.POST, request.FILES)
        
        if upload_form.is_valid():
            uploaded_file = upload_form.save()
            file = uploaded_file.File_uploadSite  # Get the uploaded file
            
            print("Uploaded file:", file)  # Debugging statement

            try:
                # Load file into a DataFrame based on file type
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                elif file.name.endswith('.xlsx'):
                    df = pd.read_excel(file)
                else:
                    messages.error(request, 'Unsupported file format. Please upload a CSV or Excel file.')
                    return redirect('add_dropdown')

                print("DataFrame contents:\n", df.head())  # Debugging statement

                # Fill NaN values to avoid errors
                df.fillna("", inplace=True)

                # Loop through rows and save Site Codes
                for _, row in df.iterrows():
                    site_code = row.get('SiteCode', '').strip()
                    site_name = row.get('SiteName', '').strip()

                    if not site_code or not site_name:
                        continue  # Skip empty rows

                    # Create or update SiteData entry
                    SiteData.objects.update_or_create(
                        SiteCode=site_code,
                        defaults={'SiteName': site_name}
                    )

                messages.success(request, "File uploaded successfully and data added!")
                return redirect('site_view')

            except Exception as e:
                print("Error:", e)
                messages.error(request, f"Error processing file: {e}")
                return redirect('add_dropdown')
        else:
            messages.error(request, "Invalid form submission.")

    else:
        upload_form = SiteCode_uploadForm()

    return render(request, 'home/SiteCodeForm.html', {'upload_form': upload_form, 'form': SiteCode_Form()})

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




#download combined table
# def download_combined_table(request):
#     # Fetch all Egasp_Data entries
#     referred_data_entries = Referred_Data.objects.all()

#     # Fetch all unique antibiotic codes (both initial and retest), excluding None values
#     unique_antibiotics_raw = (
#         AntibioticEntry.objects
#         .values_list('ab_Abx_code', 'ab_Retest_Abx_code').distinct()
#     )

#     # Flatten and clean the list (avoid duplicates)
#     antibiotic_set = set()
#     for abx_code, retest_code in unique_antibiotics_raw:
#         if abx_code:
#             antibiotic_set.add(abx_code)
#         if retest_code:
#             antibiotic_set.add(retest_code)

#     # Sort the antibiotics alphabetically
#     sorted_antibiotics = sorted(antibiotic_set)

#     # Create the HTTP response for CSV download
#     response = HttpResponse(content_type='text/csv')
#     response['Content-Disposition'] = 'attachment; filename="combined_table.csv"'

#     # Create a CSV writer
#     writer = csv.writer(response)

#     # Write the header row
#     header = [
#             "Batch_id", "Hide", "Copy_data", "Batch_Name", "Batch_Code", "Date_of_Entry", "RefNo", "BatchNo", "Total_batch",
#             "AccessionNo", "AccessionNoGen", "Default_Year", "SiteCode", "Site_Name", "Referral_Date", "Patient_ID",
#             "First_Name", "Mid_Name", "Last_Name", "Date_Birth", "Age", "Age_Verification", "Sex", "Date_Admis", "Nosocomial",
#             "Diagnosis", "Diagnosis_ICD10", "Ward", "Service_Type", "Spec_Num", "Spec_Date", "Spec_Type", "Reason", "Growth",
#             "Urine_ColCt", "ampC", "ESBL", "CARB", "MBL", "BL", "MR", "mecA", "ICR", "OtherResMech", "Site_Pre", "Site_Org",
#             "Site_Pos", "OrganismCode", "Comments", "ars_ampC", "ars_ESBL", "ars_CARB", "ars_ECIM", "ars_MCIM", "ars_EC_MCIM",
#             "ars_MBL", "ars_BL", "ars_MR", "ars_mecA", "ars_ICR", "ars_Pre", "ars_Post", "ars_OrgCode", "ars_OrgName",
#             "ars_ct_ctl", "ars_tz_tzl", "ars_cn_cni", "ars_ip_ipi", "ars_reco_Code", "ars_reco", "SiteName", "Status",
#             "Month_Date", "Day_Date", "Year_Date", "RefDate", "Start_AccNo", "End_AccNo", "No_Isolates", "BatchNumber",
#             "TotalBatchNumber", "Concordance_Check", "Concordance_by", "Concordance_by_Initials", "abx_code"
#         ]

#     # Add antibiotic-related headers
#     for abx in sorted_antibiotics:
#         is_disk_abx = BreakpointsTable.objects.filter(Whonet_Abx=abx, Disk_Abx=True).exists()
#         if not is_disk_abx:  # Add _Op fields only for MIC antibiotics
#             header.append(f'{abx}_Op')
#         header.append(f'{abx}_Val')
#         header.append(f'{abx}_RIS')
#         if not is_disk_abx:  # Add RT_Op fields only for MIC antibiotics
#             header.append(f'{abx}_RT_Op')
#         header.append(f'{abx}_RT_Val')
#         header.append(f'{abx}_RT_RIS')

#     writer.writerow(header)

#     # Now write each data row
#     for referred_entry in referred_data_entries:
#         row = [
#             # Batch details
#             referred_entry.Batch_id, referred_entry.Hide, referred_entry.Copy_data,
#             referred_entry.Batch_Name, referred_entry.Batch_Code, referred_entry.Date_of_Entry,
#             referred_entry.RefNo, referred_entry.BatchNo, referred_entry.Total_batch,

#             # Accession and site info
#             referred_entry.AccessionNo, referred_entry.AccessionNoGen, referred_entry.Default_Year,
#             referred_entry.SiteCode, referred_entry.Site_Name, referred_entry.Referral_Date,

#             # Patient info
#             referred_entry.Patient_ID, referred_entry.First_Name, referred_entry.Mid_Name,
#             referred_entry.Last_Name, referred_entry.Date_Birth, referred_entry.Age,
#             referred_entry.Age_Verification, referred_entry.Sex,

#             # Hospital and diagnosis info
#             referred_entry.Date_Admis, referred_entry.Nosocomial, referred_entry.Diagnosis,
#             referred_entry.Diagnosis_ICD10, referred_entry.Ward, referred_entry.Service_Type,

#             # Specimen details
#             referred_entry.Spec_Num, referred_entry.Spec_Date, referred_entry.Spec_Type,
#             referred_entry.Reason, referred_entry.Growth, referred_entry.Urine_ColCt,

#             # Resistance mechanisms
#             referred_entry.ampC, referred_entry.ESBL, referred_entry.CARB, referred_entry.MBL,
#             referred_entry.BL, referred_entry.MR, referred_entry.mecA, referred_entry.ICR,
#             referred_entry.OtherResMech,

#             # Site and organism info
#             referred_entry.Site_Pre, referred_entry.Site_Org, referred_entry.Site_Pos,
#             referred_entry.OrganismCode, referred_entry.Comments,

#             # ARS results
#             referred_entry.ars_ampC, referred_entry.ars_ESBL, referred_entry.ars_CARB,
#             referred_entry.ars_ECIM, referred_entry.ars_MCIM, referred_entry.ars_EC_MCIM,
#             referred_entry.ars_MBL, referred_entry.ars_BL, referred_entry.ars_MR,
#             referred_entry.ars_mecA, referred_entry.ars_ICR, referred_entry.ars_Pre,
#             referred_entry.ars_Post, referred_entry.ars_OrgCode, referred_entry.ars_OrgName,
#             referred_entry.ars_ct_ctl, referred_entry.ars_tz_tzl, referred_entry.ars_cn_cni,
#             referred_entry.ars_ip_ipi, referred_entry.ars_reco_Code, referred_entry.ars_reco,

#             # Reporting and meta info
#             referred_entry.SiteName, referred_entry.Status, referred_entry.Month_Date,
#             referred_entry.Day_Date, referred_entry.Year_Date, referred_entry.RefDate,
#             referred_entry.Start_AccNo, referred_entry.End_AccNo, referred_entry.No_Isolates,
#             referred_entry.BatchNumber, referred_entry.TotalBatchNumber,

#             # Concordance and antibiotic info
#             referred_entry.Concordance_Check, referred_entry.Concordance_by,
#             referred_entry.Concordance_by_Initials, referred_entry.abx_code,
#         ]

#         # Fetch related antibiotics for this Egasp entry, sorted
#         antibiotics = AntibioticEntry.objects.filter(ab_idNum_referred=referred_entry).order_by('ab_Abx_code')

#         # Create a mapping for quick lookup
#         abx_data = {}
#         for antibiotic in antibiotics:
#             if antibiotic.ab_Abx_code:
#                 abx_data[antibiotic.ab_Abx_code] = {
#                     '_Val': antibiotic.ab_Disk_value or antibiotic.ab_MIC_value,
#                     '_RIS': antibiotic.ab_Disk_RIS or antibiotic.ab_MIC_RIS,
#                     '_Op': antibiotic.ab_MIC_operand or '',
#                 }
#             if antibiotic.ab_Retest_Abx_code:
#                 abx_data[antibiotic.ab_Retest_Abx_code] = {
#                     'RT_Val': antibiotic.ab_Retest_DiskValue or antibiotic.ab_Retest_MICValue,
#                     'RT_RIS': antibiotic.ab_Retest_Disk_RIS or antibiotic.ab_Retest_MIC_RIS,
#                     'RT_Op': antibiotic.ab_Retest_MIC_operand or '',
#                 }

#         # Now add antibiotic fields in the sorted order
#         for abx in sorted_antibiotics:
#             is_disk_abx = BreakpointsTable.objects.filter(Whonet_Abx=abx, Disk_Abx=True).exists()
#             if abx in abx_data:
#                 if not is_disk_abx:  # Add _Op field only for MIC antibiotics
#                     row.append(abx_data[abx].get('_Op', ''))
#                 row.append(abx_data[abx].get('_Val', ''))
#                 row.append(abx_data[abx].get('_RIS', ''))
#                 if not is_disk_abx:  # Add RT_Op field only for MIC antibiotics
#                     row.append(abx_data[abx].get('RT_Op', ''))
#                 row.append(abx_data[abx].get('RT_Val', ''))
#                 row.append(abx_data[abx].get('RT_RIS', ''))
#             else:
#                 # If no data for this antibiotic, add empty columns
#                 if not is_disk_abx:
#                     row.append('')  # Empty _Op field
#                 row.extend(['', ''])  # Empty _Val and _RIS fields
#                 if not is_disk_abx:
#                     row.append('')  # Empty RT_Op field
#                 row.extend(['', ''])  # Empty RT_Val and RT_RIS fields

#         writer.writerow(row)

#     return response


def is_blank(value):
    return value in [None, '', 0]

@login_required(login_url="/login/")
def download_combined_table(request):
    referred_data_entries = Referred_Data.objects.all()

    # Collect unique antibiotics from both abx and retest
    unique_abx_codes = set()
    for abx_code, rt_code in AntibioticEntry.objects.values_list('ab_Abx_code', 'ab_Retest_Abx_code').distinct():
        if abx_code:
            unique_abx_codes.add(abx_code)
        if rt_code:
            unique_abx_codes.add(rt_code)

    sorted_antibiotics = sorted(unique_abx_codes)

    # Pre-check which antibiotics are disk types
    disk_abx_lookup = {
        abx: BreakpointsTable.objects.filter(Whonet_Abx=abx, Disk_Abx=True).exists()
        for abx in sorted_antibiotics
    }

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="combined_table.csv"'
    response.write('\ufeff')  # UTF-8 BOM
    writer = csv.writer(response)


    # Static fields (as you defined)
    static_fields = [
        "Batch_id", "Hide", "Copy_data", "Batch_Name", "Batch_Code", "Date_of_Entry", "RefNo", "BatchNo", "Total_batch",
            "AccessionNo", "AccessionNoGen", "Default_Year", "SiteCode", "Site_Name", "Referral_Date", "Patient_ID",
            "First_Name", "Mid_Name", "Last_Name", "Date_Birth", "Age", "Age_Verification", "Sex", "Date_Admis", "Nosocomial",
            "Diagnosis", "Diagnosis_ICD10", "Ward", "Service_Type", "Spec_Num", "Spec_Date", "Spec_Type", "Reason", "Growth",
            "Urine_ColCt", "ampC", "ESBL", "CARB", "MBL", "BL", "MR", "mecA", "ICR", "OtherResMech", "Site_Pre", "Site_Org",
            "Site_Pos", "OrganismCode", "Comments", "ars_ampC", "ars_ESBL", "ars_CARB", "ars_ECIM", "ars_MCIM", "ars_EC_MCIM",
            "ars_MBL", "ars_BL", "ars_MR", "ars_mecA", "ars_ICR", "ars_Pre", "ars_Post", "ars_OrgCode", "ars_OrgName",
            "ars_ct_ctl", "ars_tz_tzl", "ars_cn_cni", "ars_ip_ipi", "ars_reco_Code", "ars_reco", "SiteName", "Status",
            "Month_Date", "Day_Date", "Year_Date", "RefDate", "Start_AccNo", "End_AccNo", "No_Isolates", "BatchNumber",
            "TotalBatchNumber", "Concordance_Check", "Concordance_by", "Concordance_by_Initials", "abx_code"
    ]

    header = static_fields[:]
    for abx in sorted_antibiotics:
        header.append(f'{abx}')
        header.append(f'{abx}_RIS')
        header.append(f'{abx}_RT')
        header.append(f'{abx}_RT_RIS')

    writer.writerow(header)

    for referred in referred_data_entries:
        row = [getattr(referred, field, '') for field in static_fields]
        abx_entries = AntibioticEntry.objects.filter(ab_idNum_referred=referred)
        abx_data = {}

        for ab in abx_entries:
            # Initial result
            if ab.ab_Abx_code:
                code = ab.ab_Abx_code
                if code not in abx_data:
                    abx_data[code] = {}
                if not is_blank(ab.ab_MIC_value) or not is_blank(ab.ab_Disk_value):
                    val = ab.ab_Disk_value if not is_blank(ab.ab_Disk_value) else f"{ab.ab_MIC_operand or ''}{ab.ab_MIC_value}"
                    ris = ab.ab_Disk_RIS or ab.ab_MIC_RIS
                    abx_data[code].update({
                        '_Val': val,
                        '_RIS': ris,
                    })

            # Retest result
            if ab.ab_Retest_Abx_code:
                code = ab.ab_Retest_Abx_code
                if code not in abx_data:
                    abx_data[code] = {}
                if not is_blank(ab.ab_Retest_MICValue) or not is_blank(ab.ab_Retest_DiskValue):
                    rt_val = ab.ab_Retest_DiskValue if not is_blank(ab.ab_Retest_DiskValue) else f"{ab.ab_Retest_MIC_operand or ''}{ab.ab_Retest_MICValue}"
                    rt_ris = ab.ab_Retest_Disk_RIS or ab.ab_Retest_MIC_RIS
                    abx_data[code].update({
                        'RT_Val': rt_val,
                        'RT_RIS': rt_ris,
                    })

        # Populate row with antibiotic data
        for abx in sorted_antibiotics:
            data = abx_data.get(abx, {})
            val = data.get('_Val', '')
            if isinstance(val, (int, float)):
                val = format(val, '.3f')
            rt_val = data.get('RT_Val', '')
            if isinstance(rt_val, (int, float)):
                rt_val = format(rt_val, '.3f')
            row.extend([val, data.get('_RIS', ''), rt_val, data.get('RT_RIS', '')])

        writer.writerow(row)

    return response




def read_uploaded_file(uploaded_file):
    filename = uploaded_file.name.lower()
    if filename.endswith('.csv'):
        return pd.read_csv(uploaded_file)
    elif filename.endswith(('.xls', '.xlsx')):
        return pd.read_excel(uploaded_file)
    else:
        raise ValueError("Unsupported file format. Please upload a CSV or Excel file.")



#for uploading data in tables referred data and antibiotics entries
# def upload_combined_table(request):
#     form = WGSProjectForm()
#     referred_upload = ReferredData_upload()


#     if request.method == "POST" and request.FILES.get("ReferredDataFile"):
#         referred_upload = ReferredUploadForm(request.POST, request.FILES)
#         if referred_upload.is_valid():
#             try:
#                 upload = referred_upload.save()
#                 df = read_uploaded_file(upload.ReferredDataFile)
#                 df.columns = df.columns.str.strip().str.replace(".", "", regex=False)
#             except Exception as e:
#                 messages.error(request, f"Error processing FASTQ file: {e}")
#                 return render(request, "home/Tables.html", {
#                     "form": form,
#                     "fastq_form": referred_upload,
#                 })

#     # if request.method == 'POST':
#     #     upload_form = ReferredUploadForm(request.POST, request.FILES)
        
#     #     if upload_form.is_valid():  # Changed from 'form' to 'upload_form'
#     #         uploaded_file = request.FILES['ReferredDataFile']
#     #         csv_file = TextIOWrapper(uploaded_file.file, encoding='utf-8')
#     #         reader = csv.DictReader(csv_file)

#             # for row in reader:
#             #     accession_no = row.get('AccessionNo', '').strip()
#             #     if not accession_no:
#             #         continue  # Skip rows without accession number

#             for row in df:
#                 accession_no = row.get('AccessionNo', '').strip()
#                 if not accession_no:
#                     continue  # Skip rows without accession number
                
#                 # Helper function to parse dates
#                 def parse_date_field(date_str):
#                     if not date_str or date_str.strip() == '':
#                         return None
#                     return parse_date(date_str.strip())
                
#                 # Helper function to parse integers
#                 def parse_int_field(int_str):
#                     if not int_str or int_str.strip() == '':
#                         return None
#                     try:
#                         return int(int_str.strip())
#                     except ValueError:
#                         return None
                
#                 # Helper function to parse booleans
#                 def parse_bool_field(bool_str):
#                     if not bool_str or bool_str.strip() == '':
#                         return False
#                     return bool_str.strip().lower() in ['true', '1', 'yes']

#                 # Get or create Batch_Table instance if needed
#                 batch_id = None
#                 batch_id_str = row.get('Batch_id', '').strip()
#                 if batch_id_str:
#                     try:
#                         batch_id = Batch_Table.objects.get(id=int(batch_id_str))
#                     except (Batch_Table.DoesNotExist, ValueError):
#                         batch_id = None

#                 # Create or update the Referred Data Record
#                 referred_data, created = Referred_Data.objects.update_or_create(
#                     AccessionNo=accession_no,
#                     defaults={
#                         'Batch_id': batch_id,
#                         'Hide': parse_bool_field(row.get('Hide')),
#                         'Copy_data': parse_bool_field(row.get('Copy_data')),
#                         'Batch_Name': row.get('Batch_Name', '').strip(),
#                         'Batch_Code': row.get('Batch_Code', '').strip(),
#                         'RefNo': row.get('RefNo', '').strip(),
#                         'BatchNo': row.get('BatchNo', '').strip(),
#                         'Total_batch': row.get('Total_batch', '').strip(),
#                         'AccessionNoGen': row.get('AccessionNoGen', '').strip(),
#                         'Default_Year': parse_date_field(row.get('Default_Year')),
#                         'SiteCode': row.get('SiteCode', '').strip(),
#                         'Site_Name': row.get('Site_Name', '').strip(),
#                         'Referral_Date': parse_date_field(row.get('Referral_Date')),
#                         'Patient_ID': row.get('Patient_ID', '').strip(),
#                         'First_Name': row.get('First_Name', '').strip(),
#                         'Mid_Name': row.get('Mid_Name', '').strip(),
#                         'Last_Name': row.get('Last_Name', '').strip(),
#                         'Date_Birth': parse_date_field(row.get('Date_Birth')),
#                         'Age': row.get('Age', '').strip(),
#                         'Age_Verification': row.get('Age_Verification', '').strip(),
#                         'Sex': row.get('Sex', '').strip(),
#                         'Date_Admis': parse_date_field(row.get('Date_Admis')),
#                         'Nosocomial': row.get('Nosocomial', 'n/a'),
#                         'Diagnosis': row.get('Diagnosis', '').strip(),
#                         'Diagnosis_ICD10': row.get('Diagnosis_ICD10', '').strip(),
#                         'Ward': row.get('Ward', '').strip(),
#                         'Service_Type': row.get('Service_Type', 'n/a'),
#                         'Spec_Num': row.get('Spec_Num', '').strip(),
#                         'Spec_Date': parse_date_field(row.get('Spec_Date')),
#                         'Spec_Type': row.get('Spec_Type', '').strip(),
#                         'Reason': row.get('Reason', 'n/a'),
#                         'Growth': row.get('Growth', '').strip(),
#                         'Urine_ColCt': row.get('Urine_ColCt', '').strip(),
#                         'ampC': row.get('ampC', 'n/a'),
#                         'ESBL': row.get('ESBL', 'n/a'),
#                         'CARB': row.get('CARB', 'n/a'),
#                         'MBL': row.get('MBL', 'n/a'),
#                         'BL': row.get('BL', 'n/a'),
#                         'MR': row.get('MR', 'n/a'),
#                         'mecA': row.get('mecA', 'n/a'),
#                         'ICR': row.get('ICR', 'n/a'),
#                         'OtherResMech': row.get('OtherResMech', '').strip(),
#                         'Site_Pre': row.get('Site_Pre', '').strip(),
#                         'Site_Org': row.get('Site_Org', '').strip(),
#                         'Site_Pos': row.get('Site_Pos', '').strip(),
#                         'OrganismCode': row.get('OrganismCode', '').strip(),
#                         'Comments': row.get('Comments', '').strip(),
#                         'ars_ampC': row.get('ars_ampC', 'n/a'),
#                         'ars_ESBL': row.get('ars_ESBL', 'n/a'),
#                         'ars_CARB': row.get('ars_CARB', 'n/a'),
#                         'ars_ECIM': row.get('ars_ECIM', 'n/a'),
#                         'ars_MCIM': row.get('ars_MCIM', 'n/a'),
#                         'ars_EC_MCIM': row.get('ars_EC_MCIM', 'n/a'),
#                         'ars_MBL': row.get('ars_MBL', 'n/a'),
#                         'ars_BL': row.get('ars_BL', 'n/a'),
#                         'ars_MR': row.get('ars_MR', 'n/a'),
#                         'ars_mecA': row.get('ars_mecA', 'n/a'),
#                         'ars_ICR': row.get('ars_ICR', 'n/a'),
#                         'ars_Pre': row.get('ars_Pre', '').strip(),
#                         'ars_Post': row.get('ars_Post', '').strip(),
#                         'ars_OrgCode': row.get('ars_OrgCode', '').strip(),
#                         'ars_OrgName': row.get('ars_OrgName', '').strip(),
#                         'ars_ct_ctl': row.get('ars_ct_ctl', '').strip(),
#                         'ars_tz_tzl': row.get('ars_tz_tzl', '').strip(),
#                         'ars_cn_cni': row.get('ars_cn_cni', '').strip(),
#                         'ars_ip_ipi': row.get('ars_ip_ipi', '').strip(),
#                         'ars_reco_Code': row.get('ars_reco_Code', '').strip(),
#                         'ars_reco': row.get('ars_reco', '').strip(),
#                         'SiteName': row.get('SiteName', '').strip(),
#                         'Status': row.get('Status', 'n/a'),
#                         'Month_Date': parse_date_field(row.get('Month_Date')),
#                         'Day_Date': parse_date_field(row.get('Day_Date')),
#                         'Year_Date': parse_date_field(row.get('Year_Date')),
#                         'RefDate': parse_date_field(row.get('RefDate')),
#                         'Start_AccNo': parse_int_field(row.get('Start_AccNo')),
#                         'End_AccNo': parse_int_field(row.get('End_AccNo')),
#                         'No_Isolates': parse_int_field(row.get('No_Isolates')),
#                         'BatchNumber': parse_int_field(row.get('BatchNumber')),
#                         'TotalBatchNumber': parse_int_field(row.get('TotalBatchNumber')),
#                         'Concordance_Check': row.get('Concordance_Check', '').strip(),
#                         'Concordance_by': row.get('Concordance_by', '').strip(),
#                         'Concordance_by_Initials': row.get('Concordance_by_Initials', '').strip(),
#                         'abx_code': row.get('abx_code', '').strip(),
#                         'arsp_Encoder': row.get('arsp_Encoder', '').strip(),
#                         'arsp_Enc_Lic': row.get('arsp_Enc_Lic', '').strip(),
#                         'arsp_Checker': row.get('arsp_Checker', '').strip(),
#                         'arsp_Chec_Lic': row.get('arsp_Chec_Lic', '').strip(),
#                         'arsp_Verifier': row.get('arsp_Verifier', '').strip(),
#                         'arsp_Ver_Lic': row.get('arsp_Ver_Lic', '').strip(),
#                         'arsp_LabManager': row.get('arsp_LabManager', '').strip(),
#                         'arsp_Lab_Lic': row.get('arsp_Lab_Lic', '').strip(),
#                         'arsp_Head': row.get('arsp_Head', '').strip(),
#                         'arsp_Head_Lic': row.get('arsp_Head_Lic', '').strip(),
#                         'Date_Accomplished_ARSP': parse_date_field(row.get('Date_Accomplished_ARSP')),
#                     }
#                 )

#                 # Clear previous antibiotics for this entry
#                 AntibioticEntry.objects.filter(ab_idNum_referred=referred_data).delete()

#                 # Loop over antibiotics in the row
#                 for field in row:
#                     if field.endswith('_Val'):
#                         abx_code = field.replace('_Val', '')
#                         val = row.get(f'{abx_code}_Val', '').strip()
#                         ris = row.get(f'{abx_code}_RIS', '').strip()
#                         operand = row.get(f'{abx_code}_Op', '').strip()

#                         rt_val = row.get(f'{abx_code}_RT_Val', '').strip()
#                         rt_ris = row.get(f'{abx_code}_RT_RIS', '').strip()
#                         rt_operand = row.get(f'{abx_code}_RT_Op', '').strip()

#                         if not val and not rt_val:
#                             continue  # Skip if no values at all

#                         is_disk_abx = BreakpointsTable.objects.filter(
#                             Whonet_Abx=abx_code, Disk_Abx=True
#                         ).exists()

#                         abx_entry = AntibioticEntry(
#                             ab_idNum_referred=referred_data,
#                             ab_AccessionNo=accession_no,
#                             ab_Abx_code=abx_code,
#                         )

#                         if is_disk_abx:
#                             abx_entry.ab_Disk_value = int(val) if val else None
#                             abx_entry.ab_Disk_RIS = ris if ris else ''
#                             abx_entry.ab_Retest_DiskValue = int(rt_val) if rt_val else None
#                             abx_entry.ab_Retest_Disk_RIS = rt_ris if rt_ris else ''
#                         else:
#                             abx_entry.ab_MIC_value = float(val) if val else None
#                             abx_entry.ab_MIC_RIS = ris if ris else ''
#                             abx_entry.ab_MIC_operand = operand if operand else ''
#                             abx_entry.ab_Retest_MICValue = float(rt_val) if rt_val else None
#                             abx_entry.ab_Retest_MIC_RIS = rt_ris if rt_ris else ''
#                             abx_entry.ab_Retest_MIC_operand = rt_operand if rt_operand else ''

#                         abx_entry.save()

#                         # Link antibiotic to matching breakpoints
#                         bp_matches = BreakpointsTable.objects.filter(Whonet_Abx=abx_code)
#                         if bp_matches.exists():
#                             abx_entry.ab_breakpoints_id.set(bp_matches)

#             messages.success(request, "CSV uploaded and data imported successfully.")
#             return redirect('show_data')
#         else:
#             messages.error(request, 'Form validation failed. Please check your file.')
#     else:
#         upload_form = ReferredUploadForm()

#     return render(request, 'tables.html', {'upload_form': upload_form})


@login_required(login_url="/login/")
def copy_data_to_final(request, id):
    """
    Copies all data from Referred_Data and its AntibioticEntries
    into Final_Data and Final_AntibioticEntry.
    """
    try:
        isolates = get_object_or_404(Referred_Data, pk=id)
        all_entries = AntibioticEntry.objects.filter(ab_idNum_f_referred=isolates)

        with transaction.atomic():
            # --- Create or Update Final_Data ---
            final_obj, created = Final_Data.objects.update_or_create(
                f_AccessionNo=isolates.AccessionNo,
                defaults={
                    # Batch info
                    "f_Batch_Code": getattr(isolates, "Batch_Code", ""),
                    "f_Batch_Name": getattr(isolates, "Batch_Name", ""),
                    "f_RefNo": getattr(isolates, "RefNo", None),
                    "f_BatchNo": getattr(isolates, "BatchNo", ""),
                    "f_Total_batch": getattr(isolates, "Total_batch", ""),
                    "f_SiteCode": getattr(isolates, "Site_Code", ""),
                    "f_Site_Name": getattr(isolates, "Site_Name", ""),
                    "f_Referral_Date": getattr(isolates, "Referral_Date", None),

                    # Patient Info
                    "f_Patient_ID": getattr(isolates, "Patient_ID", ""),
                    "f_First_Name": getattr(isolates, "First_Name", ""),
                    "f_Mid_Name": getattr(isolates, "Mid_Name", ""),
                    "f_Last_Name": getattr(isolates, "Last_Name", ""),
                    "f_Date_Birth": getattr(isolates, "Date_Birth", None),
                    "f_Age": getattr(isolates, "Age", ""),
                    "f_Sex": getattr(isolates, "Sex", ""),
                    "f_Date_Admis": getattr(isolates, "Date_Admis", None),
                    "f_Diagnosis": getattr(isolates, "Diagnosis", ""),
                    "f_Diagnosis_ICD10": getattr(isolates, "Diagnosis_ICD10", ""),
                    "f_Ward": getattr(isolates, "Ward", ""),
                    "f_Ward_Type": getattr(isolates, "Ward_Type", ""),
                    "f_Service_Type": getattr(isolates, "Service_Type", "n/a"),

                    # Specimen
                    "f_Spec_Num": getattr(isolates, "Spec_Num", ""),
                    "f_Spec_Date": getattr(isolates, "Spec_Date", None),
                    "f_Spec_Type": getattr(isolates, "Spec_Type", ""),
                    "f_Growth": getattr(isolates, "Growth", ""),
                    "f_Urine_ColCt": getattr(isolates, "Urine_ColCt", ""),

                    # Organism
                    "f_Site_Pre": getattr(isolates, "Site_Pre", ""),
                    "f_Site_Org": getattr(isolates, "Site_Org", ""),
                    "f_Site_Pos": getattr(isolates, "Site_Pos", ""),
                    "f_OrganismCode": getattr(isolates, "OrganismCode", ""),
                    "f_Comments": getattr(isolates, "Comments", ""),
                },
            )

            # --- Clear existing entries in Final_AntibioticEntry ---
            Final_AntibioticEntry.objects.filter(ab_idNum_f_referred=final_obj).delete()

            # --- Copy each AntibioticEntry record ---
            for entry in all_entries:
                final_entry = Final_AntibioticEntry.objects.create(
                    ab_idNum_f_referred=final_obj,
                    ab_AccessionNo=entry.ab_AccessionNo,
                    ab_RefNo=getattr(isolates, "RefNo", ""),
                    ab_Antibiotic=entry.ab_Antibiotic,
                    ab_Abx_code=entry.ab_Abx_code,
                    ab_Abx=entry.ab_Abx,
                    ab_Disk_value=entry.ab_Disk_value,
                    ab_Disk_RIS=entry.ab_Disk_RIS,
                    ab_Disk_enRIS=entry.ab_Disk_enRIS,
                    ab_MIC_operand=entry.ab_MIC_operand,
                    ab_MIC_value=entry.ab_MIC_value,
                    ab_MIC_RIS=entry.ab_MIC_RIS,
                    ab_MIC_enRIS=entry.ab_MIC_enRIS,
                    ab_R_breakpoint=entry.ab_R_breakpoint,
                    ab_I_breakpoint=entry.ab_I_breakpoint,
                    ab_SDD_breakpoint=entry.ab_SDD_breakpoint,
                    ab_S_breakpoint=entry.ab_S_breakpoint,
                    ab_Retest_Antibiotic=entry.ab_Retest_Antibiotic,
                    ab_Retest_Abx_code=entry.ab_Retest_Abx_code,
                    ab_Retest_Abx=entry.ab_Retest_Abx,
                    ab_Retest_DiskValue=entry.ab_Retest_DiskValue,
                    ab_Retest_Disk_RIS=entry.ab_Retest_Disk_RIS,
                    ab_Retest_Disk_enRIS=entry.ab_Retest_Disk_enRIS,
                    ab_Retest_MIC_operand=entry.ab_Retest_MIC_operand,
                    ab_Retest_MICValue=entry.ab_Retest_MICValue,
                    ab_Retest_MIC_RIS=entry.ab_Retest_MIC_RIS,
                    ab_Retest_MIC_enRIS=entry.ab_Retest_MIC_enRIS,
                    ab_Ret_R_breakpoint=entry.ab_Ret_R_breakpoint,
                    ab_Ret_I_breakpoint=entry.ab_Ret_I_breakpoint,
                    ab_Ret_SDD_breakpoint=entry.ab_Ret_SDD_breakpoint,
                    ab_Ret_S_breakpoint=entry.ab_Ret_S_breakpoint,
                )

                # Copy M2M breakpoints
                final_entry.ab_breakpoints_id.set(entry.ab_breakpoints_id.all())

            messages.success(
                request,
                f"Data successfully copied to Final_Data (Accession: {isolates.AccessionNo})."
            )

        return redirect("show_data")

    except Exception as e:
        import traceback
        traceback.print_exc()
        messages.error(request, f"⚠️ Error copying data: {e}")
        return redirect("show_data")
    



    
#### uploading referred data
@login_required
@transaction.atomic
def upload_combined_table(request):
    """
    Upload referred data (Referred_Data + AntibioticEntry) 
    using user-defined field mappings from FieldMapping.
    """
    form = WGSProjectForm()
    referred_form = ReferredUploadForm()

    if request.method == "POST" and request.FILES.get("ReferredDataFile"):
        try:
            uploaded_file = request.FILES["ReferredDataFile"]
            file_name = uploaded_file.name.lower()

            # --- Load file ---
            if file_name.endswith(".csv"):
                file = TextIOWrapper(uploaded_file.file, encoding="utf-8-sig")
                df = pd.read_csv(file)
            elif file_name.endswith((".xlsx", ".xls")):
                df = pd.read_excel(uploaded_file)
            else:
                messages.error(request, "Unsupported file format. Please upload CSV, XLSX, or XLS.")
                return render(request, "wgs_app/Add_wgs.html", {
                    "referred_form": referred_form,
                    "form": form,
                })

            # --- Apply user-defined mappings ---
            user_mappings = dict(
                FieldMapping.objects.filter(user=request.user)
                .values_list("raw_field", "mapped_field")
            )
            if user_mappings:
                df.rename(columns=user_mappings, inplace=True)
                print(f"[UPLOAD] Applied {len(user_mappings)} user field mappings.")
            else:
                messages.warning(request, "⚠️ No saved field mappings found. Using raw headers.")

            # --- Normalize headers (fallback cleanup) ---
            def normalize_header(header):
                key = str(header).strip().lower().replace("_", " ").replace("-", " ")
                return re.sub(r"\s+", " ", key).strip().title()

            df.columns = [normalize_header(c) for c in df.columns]

            # --- Prepare data ---
            rows = df.to_dict("records")
            site_codes = set(SiteData.objects.values_list("SiteCode", flat=True))
            model_fields = [f.name for f in Referred_Data._meta.get_fields()]
            known_abx = set(BreakpointsTable.objects.values_list("Whonet_Abx", flat=True))

            created_ref, updated_ref, created_abx, updated_abx = 0, 0, 0, 0

            # --- Helper Functions ---
            def parse_mic_value(value_str):
                """Extract operator and numeric MIC value (e.g. '<=0.5' → ('<=', 0.5))"""
                if not value_str or pd.isna(value_str):
                    return "", None
                value_str = str(value_str).strip()
                match = re.match(r"^([<>=≤≥]+)?\s*([\d.]+)$", value_str)
                if match:
                    return match.group(1) or "", float(match.group(2))
                try:
                    return "", float(value_str)
                except ValueError:
                    return "", None

            def extract_site_code(accession_no):
                """Extract 3-letter site code from accession number (if exists)."""
                for code in site_codes:
                    if re.search(rf"{code}", str(accession_no), re.IGNORECASE):
                        return code
                return ""

            def parse_batch_info(batch_name):
                """
                Parse batch-related details from a batch name like:
                '1.1 GMH_09122019_1.1_0001-0009'
                """
                if not batch_name or pd.isna(batch_name):
                    return {"BatchNo": "", "TotalBatch": "", "RefNo": ""}
                batch_name = str(batch_name)
                batch_match = re.search(r"(\d+)\.(\d+)", batch_name)
                range_match = re.search(r"_(\d{4}-\d{4})", batch_name)
                return {
                    "BatchNo": batch_match.group(1) if batch_match else "",
                    "TotalBatch": batch_match.group(2) if batch_match else "",
                    "RefNo": range_match.group(1) if range_match else "",
                }

            # --- Process each row ---
            for row in rows:
                cleaned_row = {k: ("" if pd.isna(v) else v) for k, v in row.items()}

                accession = cleaned_row.get("AccessionNo") or cleaned_row.get("ID_Number")
                if not accession:
                    continue

                # Extract site and batch info
                site_code = extract_site_code(accession)
                batch_name = cleaned_row.get("Batch_Name", "")
                batch_info = parse_batch_info(batch_name)

                cleaned_row.update({
                    "Site_Code": site_code,
                    "BatchNo": batch_info["BatchNo"],
                    "Total_Batch": batch_info["TotalBatch"],
                    "RefNo": batch_info["RefNo"],
                })

                # Keep only model fields
                valid_fields = {k: v for k, v in cleaned_row.items() if k in model_fields}

                # --- Create or update Referred_Data record ---
                ref_obj, ref_created = Referred_Data.objects.update_or_create(
                    AccessionNo=str(accession).strip(),
                    defaults=valid_fields,
                )
                created_ref += int(ref_created)
                updated_ref += int(not ref_created)

                # --- Antibiotic Entries ---
                for abx in known_abx:
                    abx_val = str(cleaned_row.get(abx, "")).strip()
                    abx_ris = str(cleaned_row.get(f"{abx}_RIS", "")).strip()
                    abx_rt_val = str(cleaned_row.get(f"{abx}_RT", "")).strip()
                    abx_rt_ris = str(cleaned_row.get(f"{abx}_RT_RIS", "")).strip()

                    if not any([abx_val, abx_ris, abx_rt_val, abx_rt_ris]):
                        continue

                    mic_op, mic_val = parse_mic_value(abx_val)
                    ret_op, ret_val = parse_mic_value(abx_rt_val)

                    ab_entry, ab_created = AntibioticEntry.objects.update_or_create(
                        ab_idNum_referred=ref_obj,
                        ab_Abx_code=abx,
                        defaults={
                            "ab_MIC_operand": mic_op,
                            "ab_MIC_value": mic_val,
                            "ab_MIC_RIS": abx_ris,
                            "ab_Retest_MIC_operand": ret_op,
                            "ab_Retest_MICValue": ret_val,
                            "ab_Retest_MIC_RIS": abx_rt_ris,
                        },
                    )
                    created_abx += int(ab_created)
                    updated_abx += int(not ab_created)

            # --- Success message ---
            messages.success(
                request,
                f"✅ Upload complete! "
                f"{created_ref} new Referred_Data, {updated_ref} updated; "
                f"{created_abx} new AntibioticEntry, {updated_abx} updated."
            )
            return redirect("show_data")

        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f"⚠️ Error processing file: {e}")

    # --- Default render (GET request) ---
    return render(request, "wgs_app/Add_wgs.html", {
        "referred_form": referred_form,
        "form": form,
        "fastq_form": FastqUploadForm(),
        "gambit_form": GambitUploadForm(),
        "mlst_form": MlstUploadForm(),
        "checkm2_form": Checkm2UploadForm(),
        "assembly_form": AssemblyUploadForm(),
        "amrfinder_form": AmrUploadForm(),
    })







@login_required
def field_mapper_tool(request):
    """
    STEP 1: Upload a raw file and preview headers for mapping.
    """
    if request.method == "POST" and request.FILES.get("raw_file"):
        uploaded_file = request.FILES["raw_file"]

        # --- Read file to extract headers ---
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file, nrows=1)
            else:
                df = pd.read_excel(uploaded_file, nrows=1)
        except Exception as e:
            messages.error(request, f"Error reading file: {e}")
            return redirect("field_mapper_tool")

        raw_headers = df.columns.tolist()

        # --- Save file temporarily to session ---
        # Create temp directory if it doesn't exist
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_uploads')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Generate unique filename
        temp_filename = f"{request.user.id}_{uploaded_file.name}"
        temp_filepath = os.path.join(temp_dir, temp_filename)
        
        # Save file
        with open(temp_filepath, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        # Store path in session
        request.session['temp_file_path'] = temp_filepath
        request.session['temp_file_name'] = uploaded_file.name

        # --- Get model field lists ---
        final_fields = [f.name for f in Final_Data._meta.fields if f.name != "id"]
        abx_fields = list(
            BreakpointsTable.objects.filter(Show=True)
            .values_list("Whonet_Abx", flat=True)
            .distinct()
        )

        # --- Load saved mappings ---
        saved_mappings = FieldMapping.objects.filter(user=request.user)
        saved_dict = {m.raw_field: m.mapped_field for m in saved_mappings}

        context = {
            "raw_headers": raw_headers,
            "final_fields": final_fields,
            "abx_fields": abx_fields,
            "saved_mappings": saved_dict,
            "file_name": uploaded_file.name,
        }

        return render(request, "home/map_fields.html", context)

    # --- GET request (upload step) ---
    return render(request, "home/upload_raw.html")


@login_required
def generate_mapped_excel(request):
    """
    STEP 2: Apply user mappings and generate the mapped Excel file.
    """
    if request.method == "POST":
        try:
            # Get mapping from POST data
            mapping_json = request.POST.get("mapping", "{}")
            mapping = json.loads(mapping_json)

            # Get file from session
            temp_file_path = request.session.get('temp_file_path')
            temp_file_name = request.session.get('temp_file_name', 'output.xlsx')

            if not temp_file_path or not os.path.exists(temp_file_path):
                messages.error(request, "File not found. Please upload the file again.")
                return redirect("field_mapper_tool")

            # Read the file
            try:
                if temp_file_name.endswith(".csv"):
                    df = pd.read_csv(temp_file_path)
                else:
                    df = pd.read_excel(temp_file_path)
            except Exception as e:
                messages.error(request, f"Error reading file: {e}")
                return redirect("field_mapper_tool")

            # Save mappings to database
            for raw_field, mapped_field in mapping.items():
                if mapped_field:
                    FieldMapping.objects.update_or_create(
                        user=request.user,
                        raw_field=raw_field,
                        defaults={"mapped_field": mapped_field},
                    )

            # Apply mappings
            mapped_cols = {r: m for r, m in mapping.items() if m}

            if not mapped_cols:
                # Export raw file if no mapping
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="Raw_Data")
                output.seek(0)
                
                # Clean up temp file
                cleanup_temp_file(temp_file_path, request)
                
                response = HttpResponse(
                    output.getvalue(),
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                response["Content-Disposition"] = 'attachment; filename="Raw_Data.xlsx"'
                return response

            # Rename columns and export
            df.rename(columns=mapped_cols, inplace=True)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Mapped_Data")
            output.seek(0)

            # Clean up temp file
            cleanup_temp_file(temp_file_path, request)

            response = HttpResponse(
                output.getvalue(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            # Generate output filename
            base_name = os.path.splitext(temp_file_name)[0]
            response["Content-Disposition"] = f'attachment; filename="{base_name}_Mapped.xlsx"'
            
            messages.success(request, "Mapped file generated successfully!")
            return response

        except Exception as e:
            print(f"[ERROR] generate_mapped_excel: {e}")
            messages.error(request, f"Error generating mapped file: {e}")
            return redirect("field_mapper_tool")

    return redirect("field_mapper_tool")


@login_required
def clear_mappings(request):
    """
    Clear all saved field mappings for the current user.
    """
    if request.method == "POST":
        FieldMapping.objects.filter(user=request.user).delete()
        messages.success(request, "Your saved field mappings were cleared.")
    return redirect("field_mapper_tool")


def cleanup_temp_file(file_path, request):
    """
    Helper function to delete temporary file and clear session.
    """
    if file_path and os.path.exists(file_path):
            os.remove(file_path)