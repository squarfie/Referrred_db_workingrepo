# -*- encoding: utf-8 -*-

from io import TextIOWrapper
import io
import json
import os
import re
from django.conf import settings
from django.templatetags.static import static
from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404 
from django.template import loader
from django.db.models import Prefetch

from apps.home_final.utils import apply_final_breakpoints, get_filtered_antibiotics, resolve_organism_name
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
from django.db.models import Q, F, Case, When
from django.utils.timezone import now
import csv
from django.utils.dateparse import parse_date
from datetime import datetime
from django.db import IntegrityError
from collections import OrderedDict, defaultdict
from django.db import transaction
from django.db.models import Count, Prefetch, Q
from django.template.loader import render_to_string
from django.db.models import Max
from itertools import islice
from django.views.decorators.http import require_GET, require_POST



@login_required(login_url="/login/")
# auto generate clinic_code based on javascript
def get_clinic_code(request):
    site_code = request.GET.get('site_code')
    site_name = SiteData.objects.filter(SiteCode=site_code).values_list('SiteName', flat=True).first()
    return JsonResponse({'site_name': site_name})



@login_required
def settings_page(request):

    context = {
        "antibiotic_form": AntibioticsForm(),
        "org_form": OrganismForm(),
        "breakpoint_form": BreakpointsForm(),
        "site_form": SiteCode_Form(),
        "specimen_form": SpecimenTypeForm(),
        "contact_form":ContactForm(),
        "emerging_form":Emerge_Pheno_Form(),
        "abx_upload_form": Antibiotics_uploadForm(),
        'bp_upload_form': Breakpoint_uploadForm(),
        "site_upload_form": SiteCode_uploadForm(),
        "org_upload_form": Organism_uploadForm(),
        "eme_upload_form": Emerging_Crit_upload(),
        "specimen_upload": SpecimenUploadForm(),
        "pheno_pre_form": Phenotype_Pre_Form(),
        "phenotype_pre_upload": Pheno_pre_upForm(),
        "pheno_post_form": Phenotype_Post_Form(),
        "phenotype_post_upload": Pheno_post_upForm(),
        "reco_desc_form": Recco_item_Form(),
        "reco_desc_upload": Reco_item_upForm(),

        
        "editing": False,  # default state
    }

    return render(request, "home/Settings.html", context)



@login_required(login_url="/login/")
def index(request):
    isolates = Final_Data.objects.all().order_by('-f_Date_of_Entry')
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





#activate bat_seq
@login_required(login_url="/login/")
def batch_create_view(request):
    """
    Creates or overwrites a batch:
    - Overwrites Batch_Table safely
    - Re-links Referred_Data
    - Assigns clean auto sequence (bat_seq) per batch
    """

    if request.method == "POST":
        form = BatchTable_form(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)

            # extract values
            site_code = (instance.bat_SiteCode or "").strip()
            referral_date = instance.bat_Referral_Date
            ref_no_raw = (instance.bat_RefNo or "").strip()
            batch_no = (instance.bat_BatchNo or "").strip()
            total_batch = (instance.bat_Total_batch or "").strip()
            site_name = (instance.bat_Site_NameGen or "").strip()

            if not (site_code and referral_date and ref_no_raw):
                messages.error(request, "Missing required fields.")
                return redirect("batch_create")

            # generate accession numbers
            try:
                year_short = referral_date.strftime("%y")
                year_long = referral_date.strftime("%m%d%Y")

                if "-" in ref_no_raw:
                    start_ref, end_ref = map(int, ref_no_raw.split("-"))
                    if start_ref > end_ref:
                        start_ref, end_ref = end_ref, start_ref
                else:
                    start_ref = end_ref = int(ref_no_raw)

            except ValueError:
                messages.error(request, "Invalid Ref No format.")
                return redirect("batch_create")

            accession_numbers = [
                f"{year_short}ARS_{site_code}{str(ref).zfill(4)}"
                for ref in range(start_ref, end_ref + 1)
            ]

           # generate batch code and name
            batch_codegen = f"{site_code}_{year_long}_{batch_no}.{total_batch}_{ref_no_raw}"
            auto_batch_name = batch_codegen

            if not site_name:
                site_obj = SiteData.objects.filter(SiteCode=site_code).first()
                if site_obj:
                    site_name = site_obj.SiteName

          # check if batch exists then overwrite
            existing_batch = Batch_Table.objects.filter(
                bat_Batch_Code=batch_codegen
            ).first()

            if existing_batch and "confirm_overwrite" not in request.POST:
                messages.warning(
                    request,
                    f"Batch '{existing_batch.bat_Batch_Name}' already exists."
                )
                return render(request, "home/Batchname_form.html", {
                    "form": form,
                    "confirm_overwrite": True,
                    "existing_batch": existing_batch,
                })

           # start atomic transaction
            with transaction.atomic():

                # Delete old batch safely
                if existing_batch:
                    existing_batch.delete()

                # Create new batch
                batch_obj = Batch_Table.objects.create(
                    bat_Batch_Name=auto_batch_name,
                    bat_AccessionNo=", ".join(accession_numbers),
                    bat_Batch_Code=batch_codegen,
                    bat_Site_Name=site_name,
                    bat_SiteCode=site_code,
                    bat_Referral_Date=referral_date,
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

                # Ensure all accession numbers exist in Referred_Data
                for acc in accession_numbers:
                    Referred_Data.objects.get_or_create(
                        AccessionNo=acc
                    )


              
                # fetch isolates to update
                isolates = (
                    Referred_Data.objects
                    .filter(AccessionNo__in=accession_numbers)
                    .order_by("AccessionNo")  
                )

             # assign bat_seq and update fields
                seq = 1

                for iso in isolates:
                    iso.bat_seq = seq
                    iso.Batch_id_id = batch_obj.id   # ForeignKey link
                    iso.Batch_Code = batch_codegen
                    iso.Referral_Date = referral_date
                    iso.RefNo = ref_no_raw
                    iso.BatchNo = batch_no
                    iso.Total_batch = total_batch
                    iso.SiteCode = site_code
                    iso.Site_Name = site_name
                    iso.Batch_Name = auto_batch_name

                    # ---- ARSRL PERSONNEL FIELDS ----
                    iso.arsp_Encoder = batch_obj.bat_Encoder or ""
                    iso.arsp_Enc_Lic = batch_obj.bat_Enc_Lic or ""
                    iso.arsp_Checker = batch_obj.bat_Checker or ""
                    iso.arsp_Chec_Lic = batch_obj.bat_Chec_Lic or ""
                    iso.arsp_Verifier = batch_obj.bat_Verifier or ""
                    iso.arsp_Ver_Lic = batch_obj.bat_Ver_Lic or ""
                    iso.arsp_LabManager = batch_obj.bat_LabManager or ""
                    iso.arsp_Lab_Lic = batch_obj.bat_Lab_Lic or ""
                    iso.arsp_Head = batch_obj.bat_Head or ""
                    iso.arsp_Head_Lic = batch_obj.bat_Head_Lic or ""

                    iso.save(update_fields=[
                        "bat_seq",
                        "Batch_id_id",
                        "Batch_Code",
                        "Referral_Date",
                        "RefNo",
                        "BatchNo",
                        "Total_batch",
                        "SiteCode",
                        "Site_Name",
                        "Batch_Name",
                        "arsp_Encoder",
                        "arsp_Enc_Lic",
                        "arsp_Checker",
                        "arsp_Chec_Lic",
                        "arsp_Verifier",
                        "arsp_Ver_Lic",
                        "arsp_LabManager",
                        "arsp_Lab_Lic",
                        "arsp_Head",
                        "arsp_Head_Lic",
                    ])

                    seq += 1

           
            messages.success(
                request,
                f"Batch '{auto_batch_name}' saved with {len(accession_numbers)} isolates."
            )

            return redirect(
                f"{reverse('show_batches')}?batch_code={batch_obj.bat_Batch_Code}"
            )

        else:
            messages.error(request, "Batch creation failed.")
    else:
        form = BatchTable_form()

    return render(request, "home/Batchname_form.html", {
    "form": form,
    "editing": False,
})




## edit the batch
@login_required(login_url="/login/")
@transaction.atomic
def batch_edit_view(request, pk):

    batch = get_object_or_404(Batch_Table, pk=pk)

    if request.method == "POST":
        form = BatchEditForm(request.POST, instance=batch)

        if form.is_valid():
            batch = form.save()

            isolates = (
                Referred_Data.objects
                .filter(Batch_id=batch)
                .order_by("AccessionNo")
            )

            for seq, iso in enumerate(isolates, start=1):
                iso.bat_seq = seq

                # ONLY PERSONNEL FIELDS
                iso.arsp_Encoder     = batch.bat_Encoder or ""
                iso.arsp_Enc_Lic     = batch.bat_Enc_Lic or ""
                iso.arsp_Checker     = batch.bat_Checker or ""
                iso.arsp_Chec_Lic    = batch.bat_Chec_Lic or ""
                iso.arsp_Verifier    = batch.bat_Verifier or ""
                iso.arsp_Ver_Lic     = batch.bat_Ver_Lic or ""
                iso.arsp_LabManager  = batch.bat_LabManager or ""
                iso.arsp_Lab_Lic     = batch.bat_Lab_Lic or ""
                iso.arsp_Head        = batch.bat_Head or ""
                iso.arsp_Head_Lic    = batch.bat_Head_Lic or ""
                iso.Date_Accomplished_ARSP = batch.bat_Date_Accomplished

                iso.save(update_fields=[
                    "bat_seq",
                    "arsp_Encoder",
                    "arsp_Enc_Lic",
                    "arsp_Checker",
                    "arsp_Chec_Lic",
                    "arsp_Verifier",
                    "arsp_Ver_Lic",
                    "arsp_LabManager",
                    "arsp_Lab_Lic",
                    "arsp_Head",
                    "arsp_Head_Lic",
                    "Date_Accomplished_ARSP",
                ])

                # final data
                try:
                    final_iso = Final_Data.objects.get(
                        f_AccessionNo=iso.AccessionNo
                    )

                    final_iso.f_arsp_Encoder     = batch.bat_Encoder or ""
                    final_iso.f_arsp_Enc_Lic     = batch.bat_Enc_Lic or ""
                    final_iso.f_arsp_Checker     = batch.bat_Checker or ""
                    final_iso.f_arsp_Chec_Lic    = batch.bat_Chec_Lic or ""
                    final_iso.f_arsp_Verifier    = batch.bat_Verifier or ""
                    final_iso.f_arsp_Ver_Lic     = batch.bat_Ver_Lic or ""
                    final_iso.f_arsp_LabManager  = batch.bat_LabManager or ""
                    final_iso.f_arsp_Lab_Lic     = batch.bat_Lab_Lic or ""
                    final_iso.f_arsp_Head        = batch.bat_Head or ""
                    final_iso.f_arsp_Head_Lic    = batch.bat_Head_Lic or ""
                    final_iso.f_Date_Accomplished_ARSP = batch.bat_Date_Accomplished

                    final_iso.save(update_fields=[
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
                    ])

                except Final_Data.DoesNotExist:
                    # Final record may not exist yet — SAFE TO IGNORE
                    pass

            messages.success(request, "Batch and signatories updated successfully.")
            return redirect("show_data")

    else:
        form = BatchEditForm(instance=batch)

    return render(
        request,
        "home/Batchname_author.html",
        {
            "form": form,
            "editing": True,
            "batch": batch,
        }
    )




@login_required(login_url="/login/")
def show_batches(request):
    batch_code = request.GET.get("batch_code")

    if not batch_code:
        last_batch = Batch_Table.objects.order_by("-id").first()
        batch_code = last_batch.bat_Batch_Code if last_batch else None

    isolates = (
        Referred_Data.objects
        .filter(Batch_Code=batch_code)
        .exclude(bat_seq__isnull=True)   
        .order_by("bat_seq")             
        .prefetch_related("antibiotic_entries")
    )

    paginator = Paginator(isolates, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    batch = Batch_Table.objects.filter(bat_Batch_Code=batch_code).first()

    return render(request, "home/Batch_isolates.html", {
        "page_obj": page_obj,
        "batch_code": batch_code,
        "batch": batch,
    })
# @login_required(login_url="/login/")
# def review_batches(request):

#     isolate_qs = (
#         Referred_Data.objects
#         .only(
#             "id",
#             "AccessionNo",
#             "SiteCode",
#             "Patient_ID",
#             "Site_Org",
#             "Spec_Type",
#             "Batch_id",
#         )
#         .exclude(
#             Q(Site_Org__isnull=False) & ~Q(Site_Org="")
#             |
#             Q(Spec_Type__isnull=False)
#         )
#     )

#     batches = (
#         Batch_Table.objects.all()
#         .order_by("-bat_Referral_Date")
#         .prefetch_related(
#             Prefetch(
#                 "Batch_isolates",
#                 queryset=isolate_qs,
#                 to_attr="prefetched_isolates",
#             )
#         )
#     )

#     total_accessions_all = 0

#     #  PRELOAD Final_Data batch IDs
#     final_batch_ids = set(
#         Final_Data.objects
#         .values_list("f_Batch_id", flat=True)
#         .distinct()
#     )

#     for batch in batches:
#         isolates = getattr(batch, "prefetched_isolates", [])
#         batch.display_isolates = isolates
#         batch.total_isolates = len(isolates)
#         total_accessions_all += len(isolates)

#         #  THIS IS THE KEY FLAG
#         batch.is_copied_to_final = batch.id in final_batch_ids

#     return render(
#         request,
#         "home/review_batches.html",
#         {
#             "batches": batches,
#             "total_batches": batches.count(),
#             "total_accessions_all": total_accessions_all,
#         },
#     )




@login_required(login_url="/login/")
def review_batches(request):

    q = request.GET.get("q", "").strip()

    isolate_qs = (
        Referred_Data.objects
        .only(
            "id",
            "AccessionNo",
            "Batch_id",
        )
        .exclude(
            Q(Site_Org__isnull=False) & ~Q(Site_Org="")
            |
            Q(Spec_Type__isnull=False)
        )
    )

    # Accession-only filter
    if q:
        isolate_qs = isolate_qs.filter(
            AccessionNo__icontains=q
        )

    batches = Batch_Table.objects.all().order_by("-bat_Referral_Date")

    #  Batch name filter
    if q:
        batches = batches.filter(
            bat_Batch_Code__icontains=q
        )

    batches = batches.prefetch_related(
        Prefetch(
            "Batch_isolates",
            queryset=isolate_qs,
            to_attr="prefetched_isolates",
        )
    )

    total_accessions_all = 0

    final_batch_ids = set(
        Final_Data.objects.values_list("f_Batch_id", flat=True).distinct()
    )

    for batch in batches:
        isolates = getattr(batch, "prefetched_isolates", [])
        batch.display_isolates = isolates
        batch.total_isolates = len(isolates)
        total_accessions_all += len(isolates)
        batch.is_copied_to_final = batch.id in final_batch_ids

    return render(
        request,
        "home/review_batches.html",
        {
            "batches": batches,
            "total_batches": batches.count(),
            "total_accessions_all": total_accessions_all,
            "q": q,
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




@login_required(login_url="/login/")
@transaction.atomic
def delete_batch(request, batch_id):
    """
    Deletes a batch and all related Referred_Data and Final_Data records.
    """

    batch = get_object_or_404(Batch_Table, pk=batch_id)

    Referred_Data.objects.filter(
        Batch_Code=batch.bat_Batch_Code
    ).delete()

    Final_Data.objects.filter(
        f_Batch_Code=batch.bat_Batch_Code
    ).delete()

    batch.delete()

    messages.success(
        request,
        f"Batch '{batch.bat_Batch_Name}' and all related records have been deleted."
    )

    return redirect("show_batches")



@login_required(login_url="/login/")
@transaction.atomic
def delete_record_in_batch(request, id):

    isolate = get_object_or_404(Referred_Data, pk=id)

    accession_no = isolate.AccessionNo

    Final_Data.objects.filter(
        f_AccessionNo=accession_no
    ).delete()

    isolate.delete()

    messages.success(
        request,
        f"Isolate '{accession_no}' and related final record have been deleted."
    )

    return redirect("show_batches")


############# filtering of antibiotics via ajax 
@login_required(login_url="/login/")
def get_antibiotic_name(request):
    whonet_code = request.GET.get("whonet")
    try:
        abx = Antibiotic_List.objects.get(Whonet_Abx=whonet_code)
        return JsonResponse({"name": abx.Antibiotic})
    except Antibiotic_List.DoesNotExist:
        return JsonResponse({"name": ""})



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


@login_required
def ajax_filter_antibiotics(request):
    isolate_id = request.GET.get("isolate_id")
    org_code   = request.GET.get("org", "").strip().lower()
    retest     = request.GET.get("retest") == "1"

    isolate = get_object_or_404(Referred_Data, pk=isolate_id)

   # determine breakpoint year
    specimen_year = isolate.Spec_Date.year if isolate.Spec_Date else None

    if specimen_year:
        breakpoint_year = (
            BreakpointsTable.objects
            .filter(Year__lte=specimen_year)
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


    
    # filter antibiotics
    antibiotics = get_filtered_antibiotics(
        breakpoint_year,
        org_code,     # ✅ ALWAYS CODE (matches raw_data + edit_data)
        retest=retest
    )

    # fetch existing entries
    entries = AntibioticEntry.objects.filter(
        ab_idNum_referred=isolate
    )

    # Map entries by Whonet code
    entry_map = {}
    for e in entries:
        code = e.ab_Retest_Abx_code if retest else e.ab_Abx_code
        if code:
            entry_map[code.upper()] = e

    # build payload JSON
    payload = []

    for abx in antibiotics:
        code = (abx.Whonet_Abx or "").strip().upper()
        entry = entry_map.get(code)

        if retest:
            payload.append({
                "whonet": code,
                "name": abx.Antibiotic,
                "is_disk": abx.Disk_Abx,

                # RETEST VALUES
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

                # MAIN VALUES
                "disk": entry.ab_Disk_value if entry else "",
                "disk_enris": entry.ab_Disk_enRIS if entry else "",
                "mic": entry.ab_MIC_value if entry else "",
                "mic_enris": entry.ab_MIC_enRIS if entry else "",
                "mic_operand": entry.ab_MIC_operand if entry else "",
                "alert_mic": entry.ab_AlertMIC if entry else False,
            })

    return JsonResponse({"antibiotics": payload})





################ Raw data view (final version with dynamic breakpoints)

# new version with auto filter antibiotics + breakpoint assignment
# aligns with new edit data view

@login_required(login_url="/login/")
@transaction.atomic
def raw_data(request, id):

   # Fetch the isolate
    isolates = get_object_or_404(Referred_Data, pk=id)

   # get the display form
    if request.method == "GET":

        form = Referred_Form(instance=isolates)

        antibiotics_main = Antibiotic_List.objects.filter(Show=True).order_by("Antibiotic")
        antibiotics_retest = Antibiotic_List.objects.filter(Retest=True).order_by("Antibiotic")

        existing_entries = AntibioticEntry.objects.filter(
            ab_idNum_referred=isolates
        )

        return render(request, "home/Referred_form.html", {
            "form": form,
            "isolates": isolates,
            "antibiotics_main": antibiotics_main,
            "antibiotics_retest": antibiotics_retest,
            "existing_entries": existing_entries,
            "retest_entries": existing_entries,
            "edit_mode": True,
        })

    # save form first before processing antibiotics
    form = Referred_Form(request.POST, instance=isolates)


    if not form.is_valid():
        messages.error(request, "Error saving data.")
        return redirect(request.path)

    isolates = form.save()

    form = Referred_Form(request.POST, instance=isolates)



    # determine effective breakpoint year
    specimen_year = isolates.Spec_Date.year if isolates.Spec_Date else None

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

    # resolve organism codes (do not lowercase)
    resolved_site_org = (isolates.Site_Org or "").strip()
    resolved_ars_org  = (isolates.ars_OrgCode or "").strip()

  ## FOR MAIN ANIBIOTICS
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

        # Save ONLY if something was entered
        if disk_value is None and mic_value is None:
            continue

        entry, _ = AntibioticEntry.objects.update_or_create(
            ab_idNum_referred=isolates,
            ab_Abx_code=abx_code,
            defaults={
                "ab_AccessionNo": isolates.AccessionNo,
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

        # ALWAYS reset breakpoints before re-applying
        entry.ab_breakpoints_id.clear()

        bp_applied = False

       # apply the disk breakpoints if existing
        if disk_value is not None:
            bp_disk = (
                BreakpointsTable.objects
                .filter(
                    Antibiotic_list_id=abx_code,
                    Year=effective_year,
                    Test_Method="DISK"
                )
                .filter(
                    Q(Org__iexact=resolved_site_org) |
                    Q(Org='')
                )
                .order_by(
                    Case(
                        When(Org__iexact=resolved_site_org, then=0),
                        When(Org='', then=1),
                        default=2,
                    )
                )
                .first()
            )

            if bp_disk:
                entry.ab_breakpoints_id.add(bp_disk)  # for disk
                entry.ab_Site_Org = bp_disk.Org

                entry.ab_R_breakpoint   = bp_disk.R_val
                entry.ab_I_breakpoint   = bp_disk.I_val
                entry.ab_SDD_breakpoint = bp_disk.SDD_val
                entry.ab_S_breakpoint   = bp_disk.S_val
                bp_applied = True

        # apply the mic breakpoints if existing
        if mic_value is not None:
            bp_mic = (
                BreakpointsTable.objects
                .filter(
                    Antibiotic_list_id=abx_code,
                    Year=effective_year,
                    Test_Method="MIC"
                )
                .filter(
                    Q(Org__iexact=resolved_site_org) |
                    Q(Org='')
                )
                .order_by(
                    Case(
                        When(Org__iexact=resolved_site_org, then=0),
                        When(Org='', then=1),
                        default=2,
                    )
                )
                .first()
            )

            if bp_mic:
                entry.ab_breakpoints_id.add(bp_mic)  # for mic
                entry.ab_Site_Org = bp_mic.Org
                entry.ab_R_breakpoint   = bp_mic.R_val
                entry.ab_I_breakpoint   = bp_mic.I_val
                entry.ab_SDD_breakpoint = bp_mic.SDD_val
                entry.ab_S_breakpoint   = bp_mic.S_val
                entry.ab_Alert_val = bp_mic.Alert_val if alert_mic else ""
                bp_applied = True
            
        if not bp_applied:
            entry.ab_Site_Org = None
            entry.ab_R_breakpoint = None
            entry.ab_I_breakpoint = None
            entry.ab_SDD_breakpoint = None
            entry.ab_S_breakpoint = None
            entry.ab_Alert_val = ""

        entry.save(update_fields=[
            "ab_AccessionNo",
            "ab_Site_Org",
            "ab_Disk_value",
            "ab_Disk_enRIS",
            "ab_MIC_value",
            "ab_MIC_enRIS",
            "ab_MIC_operand",
            "ab_AlertMIC",
            "ab_Alert_val",
            "ab_R_breakpoint",
            "ab_I_breakpoint",
            "ab_SDD_breakpoint",
            "ab_S_breakpoint",
        ])


    ## FOR RETEST ANTIBIOITCS
    for abx in Antibiotic_List.objects.filter(Retest=True):
        abx_code = (abx.Whonet_Abx or "").strip().upper()
        disk_value  = request.POST.get(f"retest_disk_{abx_code}")
        disk_enris  = request.POST.get(f"retest_disk_enris_{abx_code}", "").strip()
        mic_value   = request.POST.get(f"retest_mic_{abx_code}")
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

        entry, _ = AntibioticEntry.objects.update_or_create(
            ab_idNum_referred=isolates,
            ab_Retest_Abx_code=abx_code,
            defaults={
                "ab_Retest_Antibiotic": abx.Antibiotic,
                "ab_Retest_Abx": abx.Abx_code,
                "ab_Retest_DiskValue": disk_value,
                "ab_Retest_Disk_enRIS": disk_enris,
                "ab_Retest_MICValue": mic_value,
                "ab_Retest_MIC_enRIS": mic_enris,
                "ab_Retest_MIC_operand": mic_operand,
                "ab_Retest_AlertMIC": alert_mic,
            }
        )

        # ALWAYS reset breakpoints before re-applying
        entry.ab_breakpoints_id.clear()

        ret_bp_applied = False
        # apply disk breakpoints for retest antibiotics if existing
        if disk_value is not None:
            bp_disk = (
                BreakpointsTable.objects
                .filter(
                    Antibiotic_list_id=abx_code,
                    Year=effective_year,
                    Test_Method="DISK"
                )
                .filter(
                    Q(Org__iexact=resolved_ars_org) |
                    Q(Org='')
                )
                .order_by(
                    Case(
                        When(Org__iexact=resolved_ars_org, then=0),
                        When(Org='', then=1),
                        default=2,
                    )
                )
                .first()
            )

            if bp_disk:
                entry.ab_breakpoints_id.add(bp_disk)  # for disk
                entry.ab_Ret_Org = bp_disk.Org
                entry.ab_Org_Flag = bp_disk.Emerging_Org_Flag
                entry.ab_Abx_Flag = bp_disk.Emerging_Abx_Flag
                entry.ab_Abx_Phenotype = bp_disk.Emerging_Pheno_Flag
                entry.ab_Abx_Phenotype_Other = bp_disk.Emerging_Pheno_Flag_Other
                entry.ab_Ret_R_breakpoint   = bp_disk.R_val
                entry.ab_Ret_I_breakpoint   = bp_disk.I_val
                entry.ab_Ret_SDD_breakpoint = bp_disk.SDD_val
                entry.ab_Ret_S_breakpoint   = bp_disk.S_val
                ret_bp_applied = True


        # apply mic breakpoints for retest antibiotics if existing
        if mic_value is not None:
            bp_mic = (
                BreakpointsTable.objects
                .filter(
                    Antibiotic_list_id=abx_code,
                    Year=effective_year,
                    Test_Method="MIC"
                )
                .filter(
                    Q(Org__iexact=resolved_ars_org) |
                    Q(Org='')
                )
                .order_by(
                    Case(
                        When(Org__iexact=resolved_ars_org, then=0),
                        When(Org='', then=1),
                        default=2,
                    )
                )
                .first()
            )

            if bp_mic:
                entry.ab_breakpoints_id.add(bp_mic)  # for mic
                entry.ab_Ret_Org = bp_mic.Org
                entry.ab_Org_Flag = bp_mic.Emerging_Org_Flag
                entry.ab_Abx_Flag = bp_mic.Emerging_Abx_Flag
                entry.ab_Abx_Phenotype = bp_mic.Emerging_Pheno_Flag
                entry.ab_Abx_Phenotype_Other = bp_mic.Emerging_Pheno_Flag_Other
                entry.ab_Ret_R_breakpoint   = bp_mic.R_val
                entry.ab_Ret_I_breakpoint   = bp_mic.I_val
                entry.ab_Ret_SDD_breakpoint = bp_mic.SDD_val
                entry.ab_Ret_S_breakpoint   = bp_mic.S_val
                entry.ab_Retest_Alert_val = bp_mic.Alert_val if alert_mic else ""
                ret_bp_applied = True
            
        if not ret_bp_applied:
            entry.ab_Ret_Org = None
            entry.ab_Org_Flag = None
            entry.ab_Abx_Flag = None
            entry.ab_Abx_Phenotype = None
            entry.ab_Abx_Phenotype_Other = None
            entry.ab_Ret_R_breakpoint   = None
            entry.ab_Ret_I_breakpoint   = None
            entry.ab_Ret_SDD_breakpoint = None
            entry.ab_Ret_S_breakpoint   = None
            entry.ab_Retest_Alert_val = ""


        entry.save(update_fields=[
            "ab_AccessionNo",
            "ab_Ret_Org",
            "ab_Org_Flag",
            "ab_Abx_Flag",
            "ab_Abx_Phenotype",
            "ab_Abx_Phenotype_Other",
            "ab_Retest_DiskValue",
            "ab_Retest_Disk_enRIS",
            "ab_Retest_MICValue",
            "ab_Retest_MIC_enRIS",
            "ab_Retest_MIC_operand",
            "ab_Retest_AlertMIC",
            "ab_Ret_R_breakpoint",
            "ab_Ret_I_breakpoint",
            "ab_Ret_SDD_breakpoint",
            "ab_Ret_S_breakpoint",
            "ab_Retest_Alert_val",
        ])

    messages.success(request, "Data saved successfully.")
    return redirect("show_batches")







################ Retrieve all raw data
@login_required(login_url="/login/")
def show_data(request):
    
    query = request.GET.get("q", "")
    sort_by = request.GET.get('sort', 'Date_of_Entry')  # Default sort field
    order = request.GET.get('order', 'desc')  # Default sort order

    sort_field = f"-{sort_by}" if order == 'desc' else sort_by

    isolates = Referred_Data.objects.prefetch_related(
        'antibiotic_entries'
    ).order_by(sort_field)

    if query:
        isolates = isolates.filter(
            Q(AccessionNo__icontains=query) |
            Q(First_Name__icontains=query) |
            Q(Last_Name__icontains=query) |
            Q(Patient_ID__icontains=query) |
            Q(Spec_Type__Specimen_code__icontains=query) |  # search in specimen code as well
            Q(Spec_Type__Specimen_name__icontains=query) |  
            Q(Site_Org__icontains=query) |
            Q(Batch_Code__icontains=query) 
        )

    copied_ids = Final_Data.objects.values_list("f_AccessionNo", flat=True)

    paginator = Paginator(isolates, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'current_sort': sort_by,
        'current_order': order,
        'copied_ids': copied_ids,
        'query': query,
    }

    return render(request, 'home/tables.html', context)








########### edit data view


### working and orgiginal version, but might run into a problem in the future -filtering of specimen year....

# @login_required(login_url="/login/")
# @transaction.atomic
# def edit_data(request, id):

#    # fetch the isolate
#     isolates = get_object_or_404(Referred_Data, pk=id)

#     # # determine breakpoint year based on specimen date
#     specimen_year = isolates.Spec_Date.year if isolates.Spec_Date else None

#     if specimen_year:
#         breakpoint_year = (
#             BreakpointsTable.objects
#             .filter(Year__lte=specimen_year)
#             .order_by("-Year")
#             .values_list("Year", flat=True)
#             .first()
#         )
#     else:
#         breakpoint_year = None

#     # helper to get breakpoint year
#     def get_effective_breakpoint_year():
#         if breakpoint_year:
#             return breakpoint_year
#         return (
#             BreakpointsTable.objects
#             .order_by("-Year")
#             .values_list("Year", flat=True)
#             .first()
#         )



#    # get the display form
#     if request.method == "GET":

#         form = Referred_Form(instance=isolates)

#         antibiotics_main = (
#             Antibiotic_List.objects
#             .filter(Show=True)
#             .order_by("Antibiotic")
#         )

#         antibiotics_retest = (
#             Antibiotic_List.objects
#             .filter(Retest=True)
#             .order_by("Antibiotic")
#         )

#         existing_entries = AntibioticEntry.objects.filter(
#             ab_idNum_referred=isolates
#         )

#         retest_entries = existing_entries.exclude(
#             ab_Retest_Abx_code__isnull=True
#         )

#         return render(request, "home/edit.html", {
#             "form": form,
#             "isolates": isolates,
#             "antibiotics_main": antibiotics_main,
#             "antibiotics_retest": antibiotics_retest,
#             "existing_entries": existing_entries,
#             "retest_entries": retest_entries,
#             "edit_mode": True,
#         })

#     # save form first before processing antibiotics
#     old_site_org = (isolates.Site_Org or "").strip()
#     old_ars_org  = (isolates.ars_OrgCode or "").strip()

#     form = Referred_Form(request.POST, instance=isolates)
#     if not form.is_valid():
#         messages.error(request, "Error: Saving unsuccessful")
#         return redirect("edit_data", id=id)

#     isolates = form.save()

#     new_site_org = (isolates.Site_Org or "").strip()
#     new_ars_org  = (isolates.ars_OrgCode or "").strip()

    
#     # resolve organism codes
#     resolved_site_org = (isolates.Site_Org or "").strip()
#     resolved_ars_org  = (isolates.ars_OrgCode or "").strip()




#     # delete existing antibiotic entries if organism code changed
#     if old_site_org != new_site_org:
#         AntibioticEntry.objects.filter(
#             ab_idNum_referred=isolates,
#             ab_Abx_code__isnull=False
#         ).delete()

#     if old_ars_org != new_ars_org:
#         AntibioticEntry.objects.filter(
#             ab_idNum_referred=isolates,
#             ab_Retest_Abx_code__isnull=False
#         ).delete()

#     effective_year = get_effective_breakpoint_year()

#    # save the MAIN ANTIBIOTICS (RAW DATA)
#     antibiotics_main = Antibiotic_List.objects.filter(Show=True)

#     for abx in antibiotics_main:
#         abx_code = (abx.Whonet_Abx or "").strip().upper()

#         disk_value  = request.POST.get(f"disk_{abx_code}")
#         mic_value   = request.POST.get(f"mic_{abx_code}")
#         disk_enris  = request.POST.get(f"disk_enris_{abx_code}", "").strip()
#         mic_enris   = request.POST.get(f"mic_enris_{abx_code}", "").strip()
#         mic_operand = request.POST.get(f"mic_operand_{abx_code}", "").strip()
#         alert_mic   = f"alert_mic_{abx_code}" in request.POST

#         try:
#             disk_value = int(disk_value) if disk_value else None
#         except ValueError:
#             disk_value = None

#         try:
#             mic_value = float(mic_value) if mic_value else None
#         except ValueError:
#             mic_value = None

#         if disk_value is None and mic_value is None:
#             continue

#         entry, _ = AntibioticEntry.objects.update_or_create(
#             ab_idNum_referred=isolates,
#             ab_Abx_code=abx_code,
#             defaults={
#                 "ab_AccessionNo": isolates.AccessionNo,
#                 "ab_Antibiotic": abx.Antibiotic,
#                 "ab_Abx": abx.Abx_code,
#                 "ab_Disk_value": disk_value,
#                 "ab_Disk_enRIS": disk_enris,
#                 "ab_MIC_value": mic_value,
#                 "ab_MIC_enRIS": mic_enris,
#                 "ab_MIC_operand": mic_operand,
#                 "ab_AlertMIC": alert_mic,
#             }
#         )


#         entry.ab_breakpoints_id.clear()  

#         bp_applied = False
      
#       # apply disk breakpoints
#         if disk_value is not None:
#             bp_disk = (
#                 BreakpointsTable.objects
#                 .filter(
#                     Antibiotic_list_id=abx_code,
#                     Year=effective_year,
#                     Test_Method="DISK"
#                 )
#                 .filter(
#                     Q(Org__iexact=resolved_site_org) |
#                     Q(Org='')
#                 )
#                 .order_by(
#                     Case(
#                         When(Org__iexact=resolved_site_org, then=0),
#                         When(Org='', then=1),
#                         default=2,
#                     )
#                 )
#                 .first()
#             )

#             if bp_disk:
#                 entry.ab_breakpoints_id.set([bp_disk])  # for disk
#                 entry.ab_Site_Org = bp_disk.Org
#                 entry.ab_R_breakpoint   = bp_disk.R_val
#                 entry.ab_I_breakpoint   = bp_disk.I_val
#                 entry.ab_SDD_breakpoint = bp_disk.SDD_val
#                 entry.ab_S_breakpoint   = bp_disk.S_val
#                 bp_applied = True
        

#        # apply mic breakpoints
#         if mic_value is not None:
#             bp_mic = (
#                 BreakpointsTable.objects
#                 .filter(
#                     Antibiotic_list_id=abx_code,
#                     Year=effective_year,
#                     Test_Method="MIC"
#                 )
#                 .filter(
#                     Q(Org__iexact=resolved_site_org) |
#                     Q(Org='')
#                 )
#                 .order_by(
#                     Case(
#                         When(Org__iexact=resolved_site_org, then=0),
#                         When(Org='', then=1),
#                         default=2,
#                     )
#                 )
#                 .first()
#             )

#             if bp_mic:
#                 entry.ab_breakpoints_id.set([bp_mic])   # for mic (overrides)
#                 entry.ab_Site_Org = bp_mic.Org
#                 entry.ab_R_breakpoint   = bp_mic.R_val
#                 entry.ab_I_breakpoint   = bp_mic.I_val
#                 entry.ab_SDD_breakpoint = bp_mic.SDD_val
#                 entry.ab_S_breakpoint   = bp_mic.S_val

#                 entry.ab_Alert_val = bp_mic.Alert_val if alert_mic else ""
#                 bp_applied = True
        
#         if not bp_applied:
#             entry.ab_Site_Org = None
#             entry.ab_R_breakpoint = None
#             entry.ab_I_breakpoint = None
#             entry.ab_SDD_breakpoint = None
#             entry.ab_S_breakpoint = None
#             entry.ab_Alert_val = ""


#         entry.save(update_fields=[
#             "ab_AccessionNo",
#             "ab_Site_Org",
#             "ab_Disk_value",
#             "ab_Disk_enRIS",
#             "ab_MIC_value",
#             "ab_MIC_enRIS",
#             "ab_MIC_operand",
#             "ab_AlertMIC",
#             "ab_Alert_val",
#             "ab_R_breakpoint",
#             "ab_I_breakpoint",
#             "ab_SDD_breakpoint",
#             "ab_S_breakpoint",
#         ])


#     # save the RETEST ANTIBIOTICS arsrl data
#     antibiotics_retest = Antibiotic_List.objects.filter(Retest=True)

#     for abx in antibiotics_retest:
#         abx_code = (abx.Whonet_Abx or "").strip().upper()

#         disk_value  = request.POST.get(f"retest_disk_{abx_code}")
#         disk_enris  = request.POST.get(f"retest_disk_enris_{abx_code}", "").strip()
       
#         try:
#             disk_value = int(disk_value) if disk_value else None
#         except ValueError:
#             disk_value = None

        
#         mic_value   = request.POST.get(f"retest_mic_{abx_code}")
#         mic_enris   = request.POST.get(f"retest_mic_enris_{abx_code}", "").strip()
#         mic_operand = request.POST.get(f"retest_mic_operand_{abx_code}", "").strip()
#         alert_mic   = f"retest_alert_mic_{abx_code}" in request.POST


        
#         try:
#             mic_value = float(mic_value) if mic_value else None
#         except ValueError:
#             mic_value = None


#         if disk_value is None and mic_value is None:
#             continue

#         entry, _ = AntibioticEntry.objects.update_or_create(
#             ab_idNum_referred=isolates,
#             ab_Retest_Abx_code=abx_code,
#             defaults={
#                 "ab_AccessionNo": isolates.AccessionNo,
#                 "ab_Retest_Antibiotic": abx.Antibiotic,
#                 "ab_Retest_Abx": abx.Abx_code,
#                 "ab_Retest_DiskValue": disk_value,
#                 "ab_Retest_Disk_enRIS": disk_enris,
#                 "ab_Retest_MICValue": mic_value,
#                 "ab_Retest_MIC_enRIS": mic_enris,
#                 "ab_Retest_MIC_operand": mic_operand,
#                 "ab_Retest_AlertMIC": alert_mic,
#             }
#         )

#         entry.ab_breakpoints_id.clear()  

#         ret_bp_applied = False
#        # apply retest disk breakpoints
#         if disk_value is not None:
#             bp_disk = (
#                 BreakpointsTable.objects
#                 .filter(
#                     Antibiotic_list_id=abx_code,
#                     Year=effective_year,
#                     Test_Method="DISK"
#                 )
#                 .filter(
#                     Q(Org__iexact=resolved_ars_org) |
#                     Q(Org='')
#                 )
#                 .order_by(
#                     Case(
#                         When(Org__iexact=resolved_ars_org, then=0),
#                         When(Org='', then=1),
#                         default=2,
#                     )
#                 )
#                 .first()
#             )

#             if bp_disk:
#                 entry.ab_breakpoints_id.set([bp_disk])  # for disk
#                 entry.ab_Ret_Org = bp_disk.Org
#                 entry.ab_Ret_R_breakpoint   = bp_disk.R_val
#                 entry.ab_Ret_I_breakpoint   = bp_disk.I_val
#                 entry.ab_Ret_SDD_breakpoint = bp_disk.SDD_val
#                 entry.ab_Ret_S_breakpoint   = bp_disk.S_val
#                 ret_bp_applied = True


#         # apply retest mic breakpoints
#         if mic_value is not None:
#             bp_mic = (
#                 BreakpointsTable.objects
#                 .filter(
#                     Antibiotic_list_id=abx_code,
#                     Year=effective_year,
#                     Test_Method="MIC"
#                 )
#                 .filter(
#                     Q(Org__iexact=resolved_ars_org) |
#                     Q(Org='')
#                 )
#                 .order_by(
#                     Case(
#                         When(Org__iexact=resolved_ars_org, then=0),
#                         When(Org='', then=1),
#                         default=2,
#                     )
#                 )
#                 .first()
#             )

#             if bp_mic:
#                 entry.ab_breakpoints_id.set([bp_mic])   # for mic (overrides)
#                 entry.ab_Ret_Org = bp_mic.Org
#                 entry.ab_Ret_R_breakpoint   = bp_mic.R_val
#                 entry.ab_Ret_I_breakpoint   = bp_mic.I_val
#                 entry.ab_Ret_SDD_breakpoint = bp_mic.SDD_val
#                 entry.ab_Ret_S_breakpoint   = bp_mic.S_val
#                 entry.ab_Retest_Alert_val = bp_mic.Alert_val if alert_mic else ""
#                 ret_bp_applied = True
        
#         if not ret_bp_applied:
#             entry.ab_Ret_Org = None
#             entry.ab_Ret_R_breakpoint = None
#             entry.ab_Ret_I_breakpoint = None
#             entry.ab_Ret_SDD_breakpoint = None
#             entry.ab_Ret_S_breakpoint = None
#             entry.ab_Retest_Alert_val = ""


#         entry.save(update_fields=[
#             "ab_AccessionNo",
#             "ab_Ret_Org",
#             "ab_Retest_DiskValue",
#             "ab_Retest_Disk_enRIS",
#             "ab_Retest_MICValue",
#             "ab_Retest_MIC_enRIS",
#             "ab_Retest_MIC_operand",
#             "ab_Retest_AlertMIC",
#             "ab_Ret_R_breakpoint",
#             "ab_Ret_I_breakpoint",
#             "ab_Ret_SDD_breakpoint",
#             "ab_Ret_S_breakpoint",
#             "ab_Retest_Alert_val",
#         ])

#     messages.success(request, "Data saved successfully.")
#     return redirect("show_data")



### much safer error-proof version 

@login_required(login_url="/login/")
@transaction.atomic
def edit_data(request, id):

   # fetch the isolate
    isolates = get_object_or_404(Referred_Data, pk=id)


   # get the display form
    if request.method == "GET":

        form = Referred_Form(instance=isolates)

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

        existing_entries = AntibioticEntry.objects.filter(
            ab_idNum_referred=isolates
        )

        retest_entries = existing_entries.exclude(
            ab_Retest_Abx_code__isnull=True
        )

        return render(request, "home/edit.html", {
            "form": form,
            "isolates": isolates,
            "antibiotics_main": antibiotics_main,
            "antibiotics_retest": antibiotics_retest,
            "existing_entries": existing_entries,
            "retest_entries": retest_entries,
            "edit_mode": True,
        })

    # save form first before processing antibiotics
    old_site_org = (isolates.Site_Org or "").strip()
    old_ars_org  = (isolates.ars_OrgCode or "").strip()

    form = Referred_Form(request.POST, instance=isolates)
    if not form.is_valid():
        messages.error(request, "Error: Saving unsuccessful")
        return redirect("edit_data", id=id)

    isolates = form.save()


    specimen_year = isolates.Spec_Date.year if isolates.Spec_Date else None

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



    new_site_org = (isolates.Site_Org or "").strip()
    new_ars_org  = (isolates.ars_OrgCode or "").strip()

    
    # resolve organism codes
    resolved_site_org = (isolates.Site_Org or "").strip()
    resolved_ars_org  = (isolates.ars_OrgCode or "").strip()




    # delete existing antibiotic entries if organism code changed
    if old_site_org != new_site_org:
        AntibioticEntry.objects.filter(
            ab_idNum_referred=isolates,
            ab_Abx_code__isnull=False
        ).delete()

    if old_ars_org != new_ars_org:
        AntibioticEntry.objects.filter(
            ab_idNum_referred=isolates,
            ab_Retest_Abx_code__isnull=False
        ).delete()


   # save the MAIN ANTIBIOTICS (RAW DATA)
    antibiotics_main = Antibiotic_List.objects.filter(Show=True)

    for abx in antibiotics_main:
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

        entry, _ = AntibioticEntry.objects.update_or_create(
            ab_idNum_referred=isolates,
            ab_Abx_code=abx_code,
            defaults={
                "ab_AccessionNo": isolates.AccessionNo,
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

      # Apply breakpoints
        if disk_value is not None:
            bp_disk = (
                BreakpointsTable.objects
                .filter(
                    Antibiotic_list_id=abx_code,
                    Year=effective_year,
                    Test_Method="DISK"
                )
                .filter(
                    Q(Org__iexact=resolved_site_org) |
                    Q(Org='')
                )
                .order_by(
                    Case(
                        When(Org__iexact=resolved_site_org, then=0),
                        When(Org='', then=1),
                        default=2,
                    )
                )
                .first()
            )

            if bp_disk:
                entry.ab_breakpoints_id.set([bp_disk])  # for disk
                entry.ab_Site_Org = bp_disk.Org
                entry.ab_R_breakpoint   = bp_disk.R_val
                entry.ab_I_breakpoint   = bp_disk.I_val
                entry.ab_SDD_breakpoint = bp_disk.SDD_val
                entry.ab_S_breakpoint   = bp_disk.S_val
                bp_applied = True
        

        # apply mic breakpoints
        if mic_value is not None:
            bp_mic = (
                BreakpointsTable.objects
                .filter(
                    Antibiotic_list_id=abx_code,
                    Year=effective_year,
                    Test_Method="MIC"
                )
                .filter(
                    Q(Org__iexact=resolved_site_org) |
                    Q(Org='')
                )
                .order_by(
                    Case(
                        When(Org__iexact=resolved_site_org, then=0),
                        When(Org='', then=1),
                        default=2,
                    )
                )
                .first()
            )

            if bp_mic:
                entry.ab_breakpoints_id.set([bp_mic])   # for mic (overrides)
                entry.ab_Site_Org = bp_mic.Org
                entry.ab_R_breakpoint   = bp_mic.R_val
                entry.ab_I_breakpoint   = bp_mic.I_val
                entry.ab_SDD_breakpoint = bp_mic.SDD_val
                entry.ab_S_breakpoint   = bp_mic.S_val

                entry.ab_Alert_val = bp_mic.Alert_val if alert_mic else ""
                bp_applied = True
        
        if not bp_applied:
            entry.ab_Site_Org = None
            entry.ab_R_breakpoint = None
            entry.ab_I_breakpoint = None
            entry.ab_SDD_breakpoint = None
            entry.ab_S_breakpoint = None
            entry.ab_Alert_val = ""


        entry.save(update_fields=[
            "ab_AccessionNo",
            "ab_Site_Org",
            "ab_Disk_value",
            "ab_Disk_enRIS",
            "ab_MIC_value",
            "ab_MIC_enRIS",
            "ab_MIC_operand",
            "ab_AlertMIC",
            "ab_Alert_val",
            "ab_R_breakpoint",
            "ab_I_breakpoint",
            "ab_SDD_breakpoint",
            "ab_S_breakpoint",
        ])


    # save the RETEST ANTIBIOTICS arsrl data
    antibiotics_retest = Antibiotic_List.objects.filter(Retest=True)

    for abx in antibiotics_retest:
        abx_code = (abx.Whonet_Abx or "").strip().upper()

        disk_value  = request.POST.get(f"retest_disk_{abx_code}")
        disk_enris  = request.POST.get(f"retest_disk_enris_{abx_code}", "").strip()
       
        try:
            disk_value = int(disk_value) if disk_value else None
        except ValueError:
            disk_value = None

        
        mic_value   = request.POST.get(f"retest_mic_{abx_code}")
        mic_enris   = request.POST.get(f"retest_mic_enris_{abx_code}", "").strip()
        mic_operand = request.POST.get(f"retest_mic_operand_{abx_code}", "").strip()
        alert_mic   = f"retest_alert_mic_{abx_code}" in request.POST


        
        try:
            mic_value = float(mic_value) if mic_value else None
        except ValueError:
            mic_value = None


        if disk_value is None and mic_value is None:
            continue

        entry, _ = AntibioticEntry.objects.update_or_create(
            ab_idNum_referred=isolates,
            ab_Retest_Abx_code=abx_code,
            defaults={
                "ab_AccessionNo": isolates.AccessionNo,
                "ab_Retest_Antibiotic": abx.Antibiotic,
                "ab_Retest_Abx": abx.Abx_code,
                "ab_Retest_DiskValue": disk_value,
                "ab_Retest_Disk_enRIS": disk_enris,
                "ab_Retest_MICValue": mic_value,
                "ab_Retest_MIC_enRIS": mic_enris,
                "ab_Retest_MIC_operand": mic_operand,
                "ab_Retest_AlertMIC": alert_mic,
            }
        )

        entry.ab_breakpoints_id.clear()  

        ret_bp_applied = False
       # apply retest disk value breakpoints
        if disk_value is not None:
            bp_disk = (
                BreakpointsTable.objects
                .filter(
                    Antibiotic_list_id=abx_code,
                    Year=effective_year,
                    Test_Method="DISK"
                )
                .filter(
                    Q(Org__iexact=resolved_ars_org) |
                    Q(Org='')
                )
                .order_by(
                    Case(
                        When(Org__iexact=resolved_ars_org, then=0),
                        When(Org='', then=1),
                        default=2,
                    )
                )
                .first()
            )

            if bp_disk:
                entry.ab_breakpoints_id.set([bp_disk])  # for disk
                entry.ab_Ret_Org = bp_disk.Org
                entry.ab_Org_Flag = bp_disk.Emerging_Org_Flag
                entry.ab_Abx_Flag = bp_disk.Emerging_Abx_Flag
                entry.ab_Abx_Phenotype = bp_disk.Emerging_Pheno_Flag
                entry.ab_Abx_Phenotype_Other = bp_disk.Emerging_Pheno_Flag_Other
                entry.ab_Ret_R_breakpoint   = bp_disk.R_val
                entry.ab_Ret_I_breakpoint   = bp_disk.I_val
                entry.ab_Ret_SDD_breakpoint = bp_disk.SDD_val
                entry.ab_Ret_S_breakpoint   = bp_disk.S_val
                ret_bp_applied = True


        # apply retest mic breakpoints
        if mic_value is not None:
            bp_mic = (
                BreakpointsTable.objects
                .filter(
                    Antibiotic_list_id=abx_code,
                    Year=effective_year,
                    Test_Method="MIC"
                )
                .filter(
                    Q(Org__iexact=resolved_ars_org) |
                    Q(Org='')
                )
                .order_by(
                    Case(
                        When(Org__iexact=resolved_ars_org, then=0),
                        When(Org='', then=1),
                        default=2,
                    )
                )
                .first()
            )

            if bp_mic:
                entry.ab_breakpoints_id.set([bp_mic])   # for mic (overrides)
                entry.ab_Ret_Org = bp_mic.Org
                entry.ab_Org_Flag = bp_mic.Emerging_Org_Flag
                entry.ab_Abx_Flag = bp_mic.Emerging_Abx_Flag
                entry.ab_Abx_Phenotype = bp_mic.Emerging_Pheno_Flag
                entry.ab_Abx_Phenotype_Other = bp_mic.Emerging_Pheno_Flag_Other
                entry.ab_Ret_R_breakpoint   = bp_mic.R_val
                entry.ab_Ret_I_breakpoint   = bp_mic.I_val
                entry.ab_Ret_SDD_breakpoint = bp_mic.SDD_val
                entry.ab_Ret_S_breakpoint   = bp_mic.S_val
                entry.ab_Retest_Alert_val = bp_mic.Alert_val if alert_mic else ""
                ret_bp_applied = True
        
        if not ret_bp_applied:
            entry.ab_Ret_Org = None
            entry.ab_Org_Flag = None
            entry.ab_Abx_Flag = None
            entry.ab_Abx_Phenotype = None
            entry.ab_Abx_Phenotype_Other = None
            entry.ab_Ret_R_breakpoint = None
            entry.ab_Ret_I_breakpoint = None
            entry.ab_Ret_SDD_breakpoint = None
            entry.ab_Ret_S_breakpoint = None
            entry.ab_Retest_Alert_val = ""


        entry.save(update_fields=[
            "ab_AccessionNo",
            "ab_Ret_Org",
            "ab_Org_Flag",
            "ab_Abx_Flag",
            "ab_Abx_Phenotype",
            "ab_Abx_Phenotype_Other",
            "ab_Retest_DiskValue",
            "ab_Retest_Disk_enRIS",
            "ab_Retest_MICValue",
            "ab_Retest_MIC_enRIS",
            "ab_Retest_MIC_operand",
            "ab_Retest_AlertMIC",
            "ab_Ret_R_breakpoint",
            "ab_Ret_I_breakpoint",
            "ab_Ret_SDD_breakpoint",
            "ab_Ret_S_breakpoint",
            "ab_Retest_Alert_val",
        ])

    messages.success(request, "Data saved successfully.")
    return redirect("show_data")




# DELETE DATA VIEW ONE isolate and the associated final data
@login_required(login_url="/login/")
@transaction.atomic
def delete_data(request, id):
    isolate = get_object_or_404(Referred_Data, pk=id)

    # delete corresponding final data FIRST (if it exists)
    Final_Data.objects.filter(
        f_AccessionNo=isolate.AccessionNo
    ).delete()

    # now delete raw data
    isolate.delete()

    messages.success(
        request,
        f"Isolate {isolate.AccessionNo} and its final data were deleted."
    )

    return redirect("show_data")


########## PDF GENERATION VIEWS

# link callback for xhtml2pdf to handle static and media files DO NOT DELETE!!
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



# Generate single PDF report
@login_required(login_url="/login/")
def generate_pdf(request, id):

    isolate = get_object_or_404(Referred_Data, pk=id)

    # ANTIBIOTIC MASTER LIST
    abx_master = (
        Antibiotic_List.objects
        .filter(Show_Print=True, Show_Value=True)
        .order_by("Abx_code")
        .values("Whonet_Abx", "Abx_code")
    )

    abx_map = {
        row["Whonet_Abx"]: row["Abx_code"]
        for row in abx_master
    }

    retest_master = (
        Antibiotic_List.objects
        .filter(Show_Print=True, Show_Value=True, Retest=True)
        .order_by("Abx_code")
        .values("Whonet_Abx", "Abx_code")
    )

    retest_map = {
        row["Whonet_Abx"]: row["Abx_code"]
        for row in retest_master
    }

    # FETCH ALL ANTIBIOTIC ENTRIES FOR THIS ISOLATE
    entries = AntibioticEntry.objects.filter(ab_idNum_referred=isolate)

    # FETCHED GROUPED ENTRIES
    grouped_entries = {
        abx_map[w]: {"disk": None, "mic": None}
        for w in abx_map
    }

    for e in entries:
        whonet = e.ab_Abx_code
        if whonet not in abx_map:
            continue

        abx_code = abx_map[whonet]

        if e.ab_Disk_Abx:
            grouped_entries[abx_code]["disk"] = e
        else:
            grouped_entries[abx_code]["mic"] = e

    # FETCHED GROUPED RETEST ENTRIES
    grouped_retest = {
        retest_map[w]: {"disk": None, "mic": None}
        for w in retest_map
    }

    for e in entries:
        whonet = e.ab_Retest_Abx_code
        if whonet not in retest_map:
            continue

        abx_code = retest_map[whonet]

        if e.ab_Disk_Abx:
            grouped_retest[abx_code]["disk"] = e
        else:
            grouped_retest[abx_code]["mic"] = e

    # CHUNKING FOR TABLE DISPLAY
    MAX_COLS = 29
    MAX_ROWS = 2

    def chunked(items, size):
        for i in range(0, len(items), size):
            yield items[i:i + size]

    grouped_rows = list(
        chunked(sorted(grouped_entries.items()), MAX_COLS)
    )[:MAX_ROWS]

    grouped_ars_rows = list(
        chunked(sorted(grouped_retest.items()), MAX_COLS)
    )[:MAX_ROWS]

    # CONTEXT FOR TEMPLATE
    context = {
        "isolate": isolate,
        "grouped_rows": grouped_rows,
        "grouped_ars_rows": grouped_ars_rows,
        "now": timezone.now(),
        "logo_path": static("assets/img/brand/arsplogo.jpg"),
    }

    # CREATE PDF RESPONSE
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'filename="Lab_Result_Report.pdf"'

    template = get_template("home/Lab_result.html")
    html = template.render(context)

    pisa.CreatePDF(html, dest=response, link_callback=link_callback)

    return response



# Generate batch PDF (2 isolates per page)


# @login_required(login_url="/login/")
# def generate_batch_pdf(request, id):

#    # Fetch batch
#     batch = get_object_or_404(Batch_Table, pk=id)

#     isolates = (
#         Referred_Data.objects
#         .filter(Batch_id=batch)
#         .order_by("bat_seq")
#     )


#   # chunk isolates into pages (2 per page)
#     def chunked(qs, size):
#         for i in range(0, qs.count(), size):
#             yield qs[i:i + size]

#     isolate_pages = list(chunked(isolates, 2))

#    # antibiotic master list
#     abx_master = (
#         Antibiotic_List.objects
#         .filter(Show_Print=True, Show_Value=True)
#         .order_by("Abx_code")
#         .values("Whonet_Abx", "Abx_code")
#     )

#     abx_map = {
#         row["Whonet_Abx"]: row["Abx_code"]
#         for row in abx_master
#     }

#     retest_master = (
#         Antibiotic_List.objects
#         .filter(Show_Print=True, Show_Value=True, Retest=True)
#         .order_by("Abx_code")
#         .values("Whonet_Abx", "Abx_code")
#     )

#     retest_map = {
#         row["Whonet_Abx"]: row["Abx_code"]
#         for row in retest_master
#     }

#    # chunking constants
#     MAX_COLS = 29
#     MAX_ROWS = 2

#     def chunk_list(items, size):
#         for i in range(0, len(items), size):
#             yield items[i:i + size]

#    # build pages data
#     pages_data = []

#     for page_isolates in isolate_pages:
#         page_entries = []

#         for isolate in page_isolates:

#             entries = AntibioticEntry.objects.filter(
#                 ab_idNum_referred=isolate
#             )

#             # grouped MAIN
#             grouped_entries = {
#                 abx_map[w]: {"disk": None, "mic": None}
#                 for w in abx_map
#             }

#             # grouped RETEST
#             grouped_retest = {
#                 retest_map[w]: {"disk": None, "mic": None}
#                 for w in retest_map
#             }

#             for e in entries:
#                 # MAIN - site
#                 if e.ab_Abx_code in abx_map:
#                     abx_code = abx_map[e.ab_Abx_code]
#                     if e.ab_Disk_Abx:
#                         grouped_entries[abx_code]["disk"] = e
#                     else:
#                         grouped_entries[abx_code]["mic"] = e

#                 # RETEST - arsrl
#                 if e.ab_Retest_Abx_code in retest_map:
#                     abx_code = retest_map[e.ab_Retest_Abx_code]
#                     if e.ab_Disk_Abx:
#                         grouped_retest[abx_code]["disk"] = e
#                     else:
#                         grouped_retest[abx_code]["mic"] = e

#             # show chunked rows
#             grouped_rows = list(
#                 chunk_list(sorted(grouped_entries.items()), MAX_COLS)
#             )[:MAX_ROWS]

#             grouped_ars_rows = list(
#                 chunk_list(sorted(grouped_retest.items()), MAX_COLS)
#             )[:MAX_ROWS]

#             page_entries.append({
#                 "isolate": isolate,
#                 "grouped_rows": grouped_rows,
#                 "grouped_ars_rows": grouped_ars_rows,
#             })

#         pages_data.append(page_entries)


#     context = {
#         "batch": batch,
#         "pages": pages_data,
#         "now": timezone.now(),
#         "logo_path": static("assets/img/brand/arsplogo.jpg"),
#     }

# # pdf response
#     response = HttpResponse(content_type="application/pdf")
#     response["Content-Disposition"] = 'filename="Batch_Report.pdf"'

#     template = get_template("home/Lab_result_batch.html")
#     html = template.render(context)

#     pisa.CreatePDF(html, dest=response, link_callback=link_callback)

#     return response




########### Version 2 - for All antibiotics printing


@transaction.atomic
def generate_batch_pdf(request, id):

    # fetch batch isolates
    batch = get_object_or_404(Batch_Table, pk=id)

    isolates = (
        Referred_Data.objects
        .filter(Batch_id=batch)
        .order_by("bat_seq")
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

            site_org = isolate.Site_Org
            ars_org = isolate.ars_OrgCode

            # fetch the entries
            entries = AntibioticEntry.objects.filter(
                ab_idNum_referred=isolate
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

    template = get_template("home/Lab_result_panel_portrait.html")
    html = template.render(context)

    pisa.CreatePDF(
        html,
        dest=response,
        link_callback=link_callback
    )

    return response



# # generate gram stain report  !!! WILL DELETE THIS LATER
# @login_required(login_url="/login/")

# def generate_gs(request, id):
#     # Get the record from the database using the provided ID
#     try:
#         isolate = Referred_Data.objects.get(pk=id)
#     except Referred_Data.DoesNotExist:
#         return HttpResponse("Error: Data not found.", status=404)
    
#     # Context data to pass to the template
#     context = {
#         'isolate': isolate,
#         'now': timezone.now(),  # Current timestamp
#     }

#     # Create a Django response object with PDF content type
#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = 'inline; filename="Gram_Stain_Report.pdf"'

#     # Load and render the template
#     template_path = 'home/GS_result.html'  # Adjust if needed
#     template = get_template(template_path)
#     html = template.render(context)

#     # Generate PDF using Pisa
#     pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)

#     # Check for errors
#     if pisa_status.err:
#         return HttpResponse(f'Error generating PDF: {html}')

#     return response



######### QUICK SEARCH VIEW

# @login_required(login_url="/login/")
# # for Quick search
# def search(request):
#    query = request.GET.get('q')
#    items = Referred_Data.objects.filter(AccessionNo__icontains=query)
#    return render (request, 'home/search_results.html',{'items': items, 'query':query})


# Quick Search for both
@login_required(login_url="/login/")
def search(request):
    query = request.GET.get("q", "").strip()

    referred_items = []
    final_items = []

    if query:
        referred_items = Referred_Data.objects.filter(
            AccessionNo__icontains=query
        ).order_by("-id")

        final_items = Final_Data.objects.filter(
            f_AccessionNo__icontains=query
        ).order_by("-id")

    return render(
        request,
        "home/search_results.html",
        {
            "query": query,
            "referred_items": referred_items,
            "final_items": final_items,
        }
    )



############## site code dropdown views
@login_required(login_url="/login/")
def add_dropdown(request):
    if request.method != "POST":
        return redirect("/settings/?tab=sitecode")

    site_form = SiteCode_Form(request.POST)

    if site_form.is_valid():
        site_form.save()
        messages.success(request, "Site code added successfully.")
    else:
        messages.error(request, "Failed to add site code. Please check the form.")
        print(site_form.errors)

    return redirect("/settings/?tab=sitecode")


@login_required(login_url="/login/")
def edit_sitecode(request, pk):
    site = get_object_or_404(SiteData, pk=pk)

    if request.method == "POST":
        site_form = SiteCode_Form(request.POST, instance=site)

        if site_form.is_valid():
            site_form.save()
            messages.success(request, "Site code updated successfully.")
            return redirect("site_view")
        else:
            messages.error(request, "Failed to update site code.")
            print(site_form.errors)

    else:
        site_form = SiteCode_Form(instance=site)

    return render(
        request,
        "home/SiteCodeForm.html",   # ✅ SEPARATE FULL PAGE
        {
            "site_form": site_form,
            "site": site,
            "editing": True,
        },
    )


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


@login_required(login_url="/login/")
def upload_sitecode(request):
    if request.method != "POST":
        return redirect("/settings/?tab=sitecode")

    site_upload_form = SiteCode_uploadForm(request.POST, request.FILES)

    if not site_upload_form.is_valid():
        messages.error(request, "Invalid upload form.")
        return redirect("/settings/?tab=sitecode")

    site_uploaded_file = site_upload_form.save()
    file = site_uploaded_file.File_uploadSite

    try:
        file.open()

        # Load file
        if file.name.lower().endswith(".csv"):
            df = pd.read_csv(file, dtype=str)
        elif file.name.lower().endswith((".xlsx", ".xls")):
            df = pd.read_excel(file, dtype=str)
        else:
            messages.error(request, "Unsupported file format.")
            return redirect("/settings/?tab=sitecode")

        # Normalize columns
        df.columns = (
            df.columns
            .str.strip()
            .str.replace(" ", "_")
            .str.lower()
        )

        df.fillna("", inplace=True)

        success = 0

        for _, row in df.iterrows():
            site_code = str(row.get("sitecode", "")).strip().upper()
            site_name = str(row.get("sitename", "")).strip()

            if not site_code or not site_name:
                continue

            SiteData.objects.update_or_create(
                SiteCode=site_code,
                defaults={"SiteName": site_name}
            )
            success += 1

        messages.success(
            request,
            f"Upload successful. {success} site codes processed."
        )

    except Exception as e:
        messages.error(request, f"Error processing file: {e}")

    return redirect("/settings/?tab=sitecode")






########## breakpoints views
@login_required(login_url="/login/")
def add_breakpoints(request):
    if request.method == "POST":
        form = BreakpointsForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Breakpoint added successfully.")
        else:
            messages.error(request, "Please correct the errors below.")

    # ALWAYS redirect back to settings tab
    return redirect("/settings/?tab=breakpoints")


@login_required(login_url="/login/")
def edit_breakpoints(request, pk):
    breakpoint = get_object_or_404(BreakpointsTable, pk=pk)
    bp_upload_form = Breakpoint_uploadForm()  # keep upload support

    if request.method == "POST":
        form = BreakpointsForm(request.POST, instance=breakpoint)

        if form.is_valid():
            form.save()
            messages.success(request, "Breakpoint updated successfully.")
            return redirect("/settings/?tab=breakpoints")

        messages.error(request, "Please correct the errors below.")
    else:
        form = BreakpointsForm(instance=breakpoint)

    return render(
        request,
        "home/Breakpoints.html",   # ✅ SEPARATE EDIT PAGE
        {
            "breakpoint_form": form,
            "breakpoint": breakpoint,
            "editing": True,
            "bp_upload_form": bp_upload_form,
        },
    )




@login_required(login_url="/login/")
def breakpoints_view(request):
    q = request.GET.get('q', '').strip()
    breakpoints = BreakpointsTable.objects.all().order_by('-Date_Modified')

    if q:
        breakpoints = breakpoints.filter(
            Q(Antibiotic__icontains=q) |
            Q(Whonet_Abx__icontains=q) |
            Q(Abx_code__icontains=q) |
            Q(Guidelines__icontains=q) |
            Q(Year__icontains=q) |
            Q(Org__icontains=q) |
            Q(Spec_code__icontains=q) |
            Q(Test_Method__icontains=q) |
            Q(Potency__icontains=q) |
            Q(Tier__icontains=q) |
            Q(R_val__icontains=q) |
            Q(I_val__icontains=q) |
            Q(SDD_val__icontains=q) |
            Q(S_val__icontains=q) |
            Q(Alert_val__icontains=q)
        ).distinct()

    paginator = Paginator(breakpoints, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'home/BreakpointsView.html',
        {
            'breakpoints': breakpoints,
            'page_obj': page_obj,
            'q': q,
        }
    )



@login_required(login_url="/login/")
#Delete breakpoints
def breakpoints_del(request, id):
    breakpoints = get_object_or_404(BreakpointsTable, pk=id)
    breakpoints.delete()
    return redirect('breakpoints_view')





# works but blindly deletes records with existing whonet_abx code
# @login_required(login_url="/login/")
# @transaction.atomic
# def upload_breakpoints(request):
#     """
#     Upload and replace BreakpointsTable data from Excel/CSV.
#     Links to existing Antibiotic_List entries via Whonet_Abx.
#     Does NOT create or update Antibiotic_List records.
#     """
#     if request.method == "POST":
#         bp_upload_form = Breakpoint_uploadForm(request.POST, request.FILES)
#         if bp_upload_form.is_valid():
#             uploaded_file = bp_upload_form.save()
#             file = uploaded_file.File_uploadBP
#             print("Uploaded file:", file)

#             try:
#                 # --- Read uploaded file into DataFrame ---
#                 if file.name.endswith(".csv"):
#                     df = pd.read_csv(file)
#                 elif file.name.endswith((".xls", ".xlsx")):
#                     df = pd.read_excel(file)
#                 else:
#                     messages.error(request, "Unsupported file format. Please upload CSV or Excel.")
#                     return redirect("upload_breakpoints")

#                 print("DataFrame contents:\n", df.head())

#                 # Clean data
#                 df.fillna("", inplace=True)
#                 df.columns = df.columns.str.strip()

#                 # Replace existing breakpoints with same WHONET codes
#                 whonet_abx_values = df["Whonet_Abx"].astype(str).str.strip().unique()
#                 BreakpointsTable.objects.filter(Whonet_Abx__in=whonet_abx_values).delete()

#                 # --- Iterate and link ---
#                 skipped = 0
#                 linked = 0
#                 for _, row in df.iterrows():
#                     whonet_code = str(row.get("Whonet_Abx", "")).strip().upper()
#                     if not whonet_code:
#                         continue

#                     # Try to find matching Antibiotic_List record
#                     antibiotic_ref = Antibiotic_List.objects.filter(Whonet_Abx=whonet_code).first()
#                     if not antibiotic_ref:
#                         skipped += 1
#                         print(f"⚠️ Skipped: No Antibiotic_List entry for {whonet_code}")
#                         continue

#                     # Parse date safely
#                     date_modified = pd.to_datetime(row.get("Date_Modified", ""), errors="coerce")
#                     if pd.isna(date_modified):
#                         date_modified = None

#                     # Create BreakpointsTable record linked to Antibiotic_List
#                     BreakpointsTable.objects.create(
#                         # Show=bool(row.get("Show", False)),
#                         # Retest=bool(row.get("Retest", False)),
#                         Disk_Abx=bool(row.get("Disk_Abx", False)),
#                         Emerging_Org_Flag=bool(row.get("Emerging_Org_Flag", False)), 
#                         Emerging_Abx_Flag=bool(row.get("Emerging_Abx_Flag", False)), 
#                         Emerging_Pheno_Flag=row.get("Emerging_Pheno_Flag", ""),
#                         Year=row.get("Year", ""),
#                         Org_Grp=row.get("Org_Grp", ""),
#                         Org=row.get("Org", ""),
#                         Guidelines=row.get("Guidelines", ""),
#                         Tier=row.get("Tier", ""),
#                         Test_Method=row.get("Test_Method", ""),
#                         Potency=row.get("Potency", ""),
#                         Abx_code=row.get("Abx_code", ""),
#                         Antibiotic=row.get("Antibiotic", ""),
#                         Alert_val=row.get("Alert_val", ""),
#                         Whonet_Abx=whonet_code,
#                         R_val=row.get("R_val", ""),
#                         I_val=row.get("I_val", ""),
#                         SDD_val=row.get("SDD_val", ""),
#                         S_val=row.get("S_val", ""),
#                         Date_Modified=date_modified,
#                         Antibiotic_list=antibiotic_ref,  # ✅ Link to existing antibiotic
#                     )
#                     linked += 1

#                 messages.success(
#                     request,
#                     f"✅ Uploaded successfully: {linked} linked, {skipped} skipped (no match in Antibiotic List)."
#                 )
#                 return redirect("breakpoints_view")

#             except Exception as e:
#                 print(" Error during processing:", e)
#                 messages.error(request, f"Error processing file: {e}")
#                 return redirect("add_breakpoints")

#         else:
#             messages.error(request, "Form is not valid.")
#     else:
#         upload_form = Breakpoint_uploadForm()

#     return render(request, "home/Breakpoints.html", {"upload_form": upload_form})




# @login_required(login_url="/login/")
# @transaction.atomic
# def upload_breakpoints(request):
#     """
#     Upload and replace BreakpointsTable data from Excel/CSV.
#     Links to existing Antibiotic_List entries via Whonet_Abx.
#     Does NOT create or update Antibiotic_List records.
#     """
#     if request.method == "POST":
#         bp_upload_form = Breakpoint_uploadForm(request.POST, request.FILES)
#         if bp_upload_form.is_valid():
#             uploaded_file = bp_upload_form.save()
#             file = uploaded_file.File_uploadBP
#             print("Uploaded file:", file)

#             try:
#                 # --- Read uploaded file into DataFrame ---
#                 if file.name.endswith(".csv"):
#                     df = pd.read_csv(file)
#                 elif file.name.endswith((".xls", ".xlsx")):
#                     df = pd.read_excel(file)
#                 else:
#                     messages.error(request, "Unsupported file format. Please upload CSV or Excel.")
#                     return redirect("upload_breakpoints")

#                 print("DataFrame contents:\n", df.head())

#                 # Clean data
#                 df.fillna("", inplace=True)
#                 df.columns = df.columns.str.strip()

#                 # --------------------------------------------------
#                 # SAFE REPLACEMENT LOGIC (full-coverage check)
#                 # --------------------------------------------------

#                 # Normalize dataframe columns used for comparison
#                 df["Whonet_Abx"] = df["Whonet_Abx"].astype(str).str.strip().str.upper()
#                 df["Year"] = df["Year"].astype(str).str.strip()
#                 df["Test_Method"] = df["Test_Method"].astype(str).str.strip()
#                 df["Org"] = df["Org"].fillna("").astype(str).str.strip()

#                 # Build uploaded breakpoint identity keys
#                 uploaded_keys = set(
#                     zip(
#                         df["Whonet_Abx"],
#                         df["Year"],
#                         df["Test_Method"],
#                         df["Org"],
#                     )
#                 )

#                 # Fetch existing breakpoint identity keys from DB
#                 existing_bps = BreakpointsTable.objects.filter(
#                     Whonet_Abx__in=df["Whonet_Abx"].unique()
#                 ).values_list(
#                     "Whonet_Abx",
#                     "Year",
#                     "Test_Method",
#                     "Org",
#                 )

#                 existing_keys = set(
#                     (w.strip().upper(), y.strip(), t.strip(), (o or "").strip())
#                     for w, y, t, o in existing_bps
#                 )

#                 # Only delete if upload fully replaces existing rows
#                 if existing_keys and not existing_keys.issubset(uploaded_keys):
#                     raise ValueError(
#                         "Upload does not fully replace existing breakpoint definitions. "
#                         "Partial overwrite is not allowed."
#                     )

#                 # Safe to delete
#                 BreakpointsTable.objects.filter(
#                     Whonet_Abx__in=df["Whonet_Abx"].unique()
#                 ).delete()


#                 # --- Iterate and link ---
#                 skipped = 0
#                 linked = 0
#                 for _, row in df.iterrows():
#                     whonet_code = str(row.get("Whonet_Abx", "")).strip().upper()
#                     if not whonet_code:
#                         continue

#                     # Try to find matching Antibiotic_List record
#                     antibiotic_ref = Antibiotic_List.objects.filter(Whonet_Abx=whonet_code).first()
#                     if not antibiotic_ref:
#                         skipped += 1
#                         print(f"⚠️ Skipped: No Antibiotic_List entry for {whonet_code}")
#                         continue

#                     # Parse date safely
#                     date_modified = pd.to_datetime(row.get("Date_Modified", ""), errors="coerce")
#                     if pd.isna(date_modified):
#                         date_modified = None

#                     # Create BreakpointsTable record linked to Antibiotic_List
#                     BreakpointsTable.objects.create(
#                         # Show=bool(row.get("Show", False)),
#                         # Retest=bool(row.get("Retest", False)),
#                         Disk_Abx=bool(row.get("Disk_Abx", False)),
#                         Emerging_Org_Flag=bool(row.get("Emerging_Org_Flag", False)), 
#                         Emerging_Abx_Flag=bool(row.get("Emerging_Abx_Flag", False)), 
#                         Emerging_Pheno_Flag=row.get("Emerging_Pheno_Flag", ""),
#                         Year=row.get("Year", ""),
#                         Org=row.get("Org", ""),
#                         Spec_code=row.get("Spec_code", ""),
#                         Guidelines=row.get("Guidelines", ""),
#                         Tier=row.get("Tier", ""),
#                         Test_Method=row.get("Test_Method", ""),
#                         Potency=row.get("Potency", ""),
#                         Abx_code=row.get("Abx_code", ""),
#                         Antibiotic=row.get("Antibiotic", ""),
#                         Alert_val=row.get("Alert_val", ""),
#                         Whonet_Abx=whonet_code,
#                         R_val=row.get("R_val", ""),
#                         I_val=row.get("I_val", ""),
#                         SDD_val=row.get("SDD_val", ""),
#                         S_val=row.get("S_val", ""),
#                         Date_Modified=date_modified,
#                         Antibiotic_list=antibiotic_ref,  # ✅ Link to existing antibiotic
#                     )
#                     linked += 1

#                 messages.success(
#                     request,
#                     f"✅ Uploaded successfully: {linked} linked, {skipped} skipped (no match in Antibiotic List)."
#                 )
#                 return redirect("breakpoints_view")

#             except Exception as e:
#                 print(" Error during processing:", e)
#                 messages.error(request, f"Error processing file: {e}")
#                 return redirect("add_breakpoints")

#         else:
#             messages.error(request, "Form is not valid.")
#     else:
#         upload_form = Breakpoint_uploadForm()

#     return render(request, "home/Breakpoints.html", {"upload_form": upload_form})


@login_required(login_url="/login/")
@transaction.atomic
def upload_breakpoints(request):
    """
    Upload and replace BreakpointsTable data from Excel/CSV.
    Links to existing Antibiotic_List entries via Whonet_Abx.
    Does NOT create or update Antibiotic_List records.
    """

    if request.method != "POST":
        return render(
            request,
            "home/Breakpoints.html",
            {"upload_form": Breakpoint_uploadForm()}
        )

    bp_upload_form = Breakpoint_uploadForm(request.POST, request.FILES)
    if not bp_upload_form.is_valid():
        messages.error(request, "Form is not valid.")
        return redirect("add_breakpoints")

    uploaded_file = bp_upload_form.save()
    file = uploaded_file.File_uploadBP
    print("Uploaded file:", file)

    try:
        # --------------------------------------------------
        # READ FILE
        # --------------------------------------------------
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        elif file.name.endswith((".xls", ".xlsx")):
            df = pd.read_excel(file)
        else:
            raise ValueError("Unsupported file format")

        print("DataFrame preview:\n", df.head())

        # --------------------------------------------------
        # CLEAN DATA
        # --------------------------------------------------
        df.fillna("", inplace=True)
        df.columns = df.columns.str.strip()

        df["Whonet_Abx"] = df["Whonet_Abx"].astype(str).str.strip().str.upper()
        df["Year"] = df["Year"].astype(str).str.strip()
        df["Org"] = df["Org"].astype(str).str.strip()
        df["Test_Method"] = df["Test_Method"].astype(str).str.strip()
        df["Spec_code"] = df.get("Spec_code", "").astype(str).str.strip()

        # --------------------------------------------------
        # SAFE OVERWRITE CHECK
        # --------------------------------------------------
        uploaded_keys = set(
            zip(
                df["Whonet_Abx"],
                df["Year"],
                df["Test_Method"],
                df["Org"],
            )
        )

        existing_keys = set(
            BreakpointsTable.objects
            .filter(Whonet_Abx__in=df["Whonet_Abx"].unique())
            .values_list("Whonet_Abx", "Year", "Test_Method", "Org")
        )

        if existing_keys and not existing_keys.issubset(uploaded_keys):
            raise ValueError(
                "Upload does not fully replace existing breakpoint definitions. "
                "Partial overwrite is not allowed."
            )

        # --------------------------------------------------
        # DELETE OLD BREAKPOINTS
        # --------------------------------------------------
        BreakpointsTable.objects.filter(
            Whonet_Abx__in=df["Whonet_Abx"].unique()
        ).delete()

        # --------------------------------------------------
        # CREATE NEW BREAKPOINTS
        # --------------------------------------------------
        skipped = 0
        linked = 0

        for _, row in df.iterrows():
            whonet_code = row["Whonet_Abx"]
            if not whonet_code:
                continue

            antibiotic_ref = (
                Antibiotic_List.objects
                .filter(Whonet_Abx=whonet_code)
                .first()
            )

            if not antibiotic_ref:
                skipped += 1
                print(f"⚠️ Skipped: No Antibiotic_List entry for {whonet_code}")
                continue

            date_modified = pd.to_datetime(
                row.get("Date_Modified", ""),
                errors="coerce"
            )
            if pd.isna(date_modified):
                date_modified = None

            print(
                f"✔ Linking breakpoint → "
                f"{whonet_code} → Antibiotic_List.id={antibiotic_ref.id}"
            )

            BreakpointsTable.objects.create(
                Antibiotic_list=antibiotic_ref,

                Whonet_Abx=whonet_code,
                Antibiotic=row.get("Antibiotic", ""),
                Abx_code=row.get("Abx_code", ""),

                Guidelines=row.get("Guidelines", ""),
                Year=row.get("Year", ""),
                Org=row.get("Org", ""),
                Spec_code=row.get("Spec_code", ""),

                Test_Method=row.get("Test_Method", ""),
                Tier=row.get("Tier", ""),
                Potency=row.get("Potency", ""),

                Disk_Abx=bool(row.get("Disk_Abx", False)),
                Emerging_Org_Flag=bool(row.get("Emerging_Org_Flag", False)),
                Emerging_Abx_Flag=bool(row.get("Emerging_Abx_Flag", False)),
                Emerging_Pheno_Flag=row.get("Emerging_Pheno_Flag", ""),

                R_val=row.get("R_val", ""),
                I_val=row.get("I_val", ""),
                SDD_val=row.get("SDD_val", ""),
                S_val=row.get("S_val", ""),
                Alert_val=row.get("Alert_val", ""),

                Date_Modified=date_modified,
            )

            linked += 1

        messages.success(
            request,
            f"✅ Uploaded successfully: {linked} linked, "
            f"{skipped} skipped (no Antibiotic_List match)."
        )
        return redirect("breakpoints_view")

    except Exception as e:
        print("❌ Error during processing:", e)
        messages.error(request, f"Error processing file: {e}")
        return redirect("add_breakpoints")



@login_required(login_url="/login/")
#for exporting into excel
def export_breakpoints(request):
    objects = BreakpointsTable.objects.all()
    data = []

    for obj in objects:
        data.append({
            # "Show": obj.Show,
            # "Retest": obj.Retest,
            "Disk_Abx": obj.Disk_Abx,
            "Emerging_Org_Flag": obj.Emerging_Org_Flag,
            "Emerging_Abx_Flag": obj.Emerging_Abx_Flag,
            "Emerging_Pheno_Flag": obj.Emerging_Pheno_Flag,
            "Year": obj.Year,
            "Org_Grp" :obj.Org_Grp,
            "Org": obj.Org,
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
        RIS = entry.ab_Disk_enRIS or entry.ab_MIC_enRIS
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


############ Specimen

@login_required(login_url="/login/")
# View to display all specimen types
def specimen_list(request):
    q = request.GET.get("q", "").strip()
    sort_by = request.GET.get('sort', 'Specimen_code')  # Default sort field
    order = request.GET.get('order', 'desc')  # Default sort order

    sort_field = f"-{sort_by}" if order == 'desc' else sort_by
    specimen_items = SpecimenTypeModel.objects.all().order_by(sort_field)

    if q:
        specimen_items = specimen_items.filter(
            Q(Specimen_code__icontains=q) |
            Q(Specimen_name__icontains=q) 
        )
    paginator = Paginator(specimen_items, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)


    return render(request, 'home/SpecimenView.html', {'specimen_items': specimen_items, 'page_obj': page_obj, 'q': q, 'sort_by': sort_by, 'order': order})




@login_required(login_url="/login/")
def add_specimen(request):
    
    if request.method != "POST":
        return redirect("/settings/?tab=specimen")

    specimen_form = SpecimenTypeForm(request.POST)

    if specimen_form.is_valid():
        specimen_form.save()
        messages.success(request, "Specimen added successfully.")
    else:
        messages.error(request, "Failed to add specimen. Please check the form.")
        print(specimen_form.errors)

    return redirect("/settings/?tab=specimen")




@login_required(login_url="/login/")
# Edit an existing specimen
@login_required(login_url="/login/")
def edit_specimen(request, pk):
    specimen = get_object_or_404(SpecimenTypeModel, pk=pk)

    if request.method == "POST":
        form = SpecimenTypeForm(request.POST, instance=specimen)
        if form.is_valid():
            form.save()
            return redirect("specimen_list")
    else:
        form = SpecimenTypeForm(instance=specimen)

    return render(
        request,
        "home/SpecimenEdit.html",
        {
            "form": form,
            "specimen": specimen,
            "editing": True,   
        }
    )



@login_required(login_url="/login/")
# View to delete a specimen type
def delete_specimen(request, pk):
    specimen = get_object_or_404(SpecimenTypeModel, pk=pk)
    specimen.delete()
    return redirect('specimen_list')



@login_required(login_url="/login/")
@transaction.atomic
def upload_specimen_code(request):

    if request.method == "POST":
        specimen_upload = SpecimenUploadForm(request.POST, request.FILES)

        if specimen_upload.is_valid():
            uploaded_file = specimen_upload.save()
            file = uploaded_file.File_uploadSpec

            try:
                if file.name.endswith(".csv"):
                    df = pd.read_csv(file, dtype=str)
                elif file.name.endswith((".xls", ".xlsx")):
                    df = pd.read_excel(file, dtype=str)
                else:
                    messages.error(request, "Unsupported file format.")
                    return redirect("upload_specimen_code")

                # Normalize columns
                df.columns = (
                    df.columns
                    .str.strip()
                    .str.lower()
                )

                REQUIRED_COL = "specimen_code"
                if REQUIRED_COL not in df.columns:
                    messages.error(
                        request,
                        "Missing required column: Specimen_code"
                    )
                    return redirect("upload_specimen_code")

                skipped = 0
                updated = 0
                created = 0

                for idx, row in df.iterrows():
                    specimen_code = str(row.get("specimen_code", "")).strip().lower()

                    if not specimen_code:
                        skipped += 1
                        continue

                    flag = str(row.get("emerging_spec_flag", "")).strip().upper() in [
                        "1", "true", "yes", "y"
                    ]

                    grp_code = str(row.get("specimen_code_grp", "")).strip().lower()
                    grp_obj = None
                    if grp_code:
                        grp_obj, _ = SpecimenTypeModel.objects.get_or_create(
                            Specimen_code=grp_code
                        )

                    obj, created_flag = SpecimenTypeModel.objects.update_or_create(
                        Specimen_code=specimen_code,
                        defaults={
                            "Emerging_Spec_Flag": flag,
                            "Specimen_name": row.get("specimen_name", ""),
                            "Specimen_Code_Grp": grp_obj,
                            "Specimen_Grp_Name": row.get("specimen_grp_name", ""),
                        }
                    )

                    if created_flag:
                        created += 1
                    else:
                        updated += 1

                messages.success(
                    request,
                    f"✅ Upload complete: {created} created, {updated} updated, {skipped} skipped."
                )
                return redirect("specimen_list")

            except Exception as e:
                messages.error(request, f"❌ Error processing file: {e}")
                return redirect("upload_specimen_code")

        messages.error(request, "Form is not valid.")

    return render(request, "Settings.html", {
        "specimen_upload": SpecimenUploadForm()
    })


@login_required(login_url="/login/")
def delete_all_specimens(request):
    SpecimenTypeModel.objects.all().delete()
    messages.success(request, "All specimen types have been deleted successfully.")
    return redirect('specimen_list')  # Redirect to the specimen list view




####### Download Antibiotic Entries

@login_required(login_url="/login/")
def export_Antibioticentry(request):
    objects = AntibioticEntry.objects.all()
    data = []

    for obj in objects:
        data.append({
            "ab_idNumber_egasp": obj.ab_idNum_referred.AccessionNo if obj.ab_idNum_referred else None,
            "Accession_No": obj.ab_AccessionNo,
            "Site_Org": obj.ab_Site_Org,
            "Antibiotic": obj.ab_Antibiotic,
            "Abx_code": obj.ab_Abx_code,
            "Abx": obj.ab_Abx,
            "Disk_value": obj.ab_Disk_value,
            "Disk_enRIS": obj.ab_Disk_enRIS,
            "MIC_operand": obj.ab_MIC_operand,
            "MIC_value": obj.ab_MIC_value,
            "MIC_enRIS": obj.ab_MIC_enRIS,
            "Ars_Org":obj.ab_Ret_Org,
            "Retest_Antibiotic": obj.ab_Retest_Antibiotic,
            "Retest_Abx_code": obj.ab_Retest_Abx_code,
            "Retest_Abx": obj.ab_Retest_Abx,
            "Retest_DiskValue": obj.ab_Retest_DiskValue,
            "Retest_Disk_enRIS": obj.ab_Retest_Disk_enRIS,
            "Ret_MIC_Operand": obj.ab_Retest_MIC_operand,
            "Retest_MICValue": obj.ab_Retest_MICValue,
            "Retest_MIC_enRIS": obj.ab_Retest_MIC_enRIS,
            "ab_R_breakpoint": obj.ab_R_breakpoint,
            "ab_I_breakpoint": obj.ab_I_breakpoint,
            "ab_SDD_breakpoint": obj.ab_SDD_breakpoint,
            "ab_S_breakpoint":obj.ab_S_breakpoint,
            "ab_Ret_R_breakpoint": obj.ab_Ret_R_breakpoint,
            "ab_Ret_I_breakpoint": obj.ab_Ret_I_breakpoint,
            "ab_Ret_SDD_breakpoint": obj.ab_Ret_SDD_breakpoint,
            "ab_Ret_S_breakpoint": obj.ab_Ret_S_breakpoint
        })
    
    # Define file path
    file_path = "AntibioticEntry_referred.xlsx"

    # Convert data to DataFrame and save as Excel
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False)

    # Return the file as a response
    return FileResponse(open(file_path, "rb"), as_attachment=True, filename="AntibioticEntry_referred.xlsx")



######## Contact Details views
@login_required(login_url="/login/")
def add_contact(request):
    if request.method != "POST":
        return redirect("/settings/?tab=contact")

    contact_form = ContactForm(request.POST)

    if contact_form.is_valid():
        contact_form.save()
        messages.success(request, "Contact added successfully.")
    else:
        messages.error(request, "Failed to add contact. Please check the form.")
        print(contact_form.errors)

    return redirect("/settings/?tab=contact")



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






########## Download Combined Table
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
    response['Content-Disposition'] = 'attachment; filename="combined_raw_data.csv"'
    response.write('\ufeff')  # UTF-8 BOM
    writer = csv.writer(response)


    # Static fields (as you defined)
    static_fields = [
    "bat_seq",
    "Batch_id",
    "Hide",
    "Copy_data",
    "Batch_Name",
    "Batch_Code",
    "Date_of_Entry",
    "Date_Modified",
    "RefNo",
    "BatchNo",
    "Total_batch",
    "AccessionNo",
    "AccessionNoGen",
    "Default_Year",
    "SiteCode",
    "Site_Name",
    "Referral_Date",

    "Patient_ID",
    "First_Name",
    "Mid_Name",
    "Last_Name",
    "Date_Birth",
    "Age",
    "Emerging_Flag_Age",
    "Sex",
    "Date_Admis",
    "Nosocomial",
    "Diagnosis",
    "Diagnosis_ICD10",
    "Ward",
    "Ward_Type",
    "Service_Type",

    "Spec_Num",
    "Spec_Date",
    "Spec_Type",
    "Reason",
    "Growth",
    "Urine_ColCt",

    "ampC",
    "ESBL",
    "CARB",
    "MBL",
    "BL",
    "MR",
    "mecA",
    "ICR",
    "OtherResMech",

    "Site_Pre",
    "Site_Org",
    "Site_OrgName",
    "Site_Pos",
    "Comments",

    "ars_ampC",
    "ars_ESBL",
    "ars_CARB",
    "ars_ECIM",
    "ars_MCIM",
    "ars_EC_MCIM",
    "ars_MBL",
    "ars_BL",
    "ars_MR",
    "ars_mecA",
    "ars_ICR",
    "ars_Pre",
    "ars_Post",
    "ars_OrgCode",
    "ars_OrgName",
    "ars_ct_ctl",
    "ars_tz_tzl",
    "ars_cn_cni",
    "ars_ip_ipi",
    "ars_reco_Code",
    "ars_description",
    "ars_reco",

    "arsp_Encoder",
    "arsp_Enc_Lic",
    "arsp_Checker",
    "arsp_Chec_Lic",
    "arsp_Verifier",
    "arsp_Ver_Lic",
    "arsp_LabManager",
    "arsp_Lab_Lic",
    "arsp_Head",
    "arsp_Head_Lic",
    "Date_Accomplished_ARSP",

    "x_mrse",
    "x_mrsamrse",
    "x_entbac",
    "edta",
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
                    ris = ab.ab_Disk_enRIS or ab.ab_MIC_enRIS
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
                    rt_ris = ab.ab_Retest_Disk_enRIS or ab.ab_Retest_MIC_enRIS
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


### helper for copy data to final
def nz(val):
    """Normalize NULLs for non-nullable CharFields"""
    return val if val not in (None,) else ""





### copy batch




# @login_required(login_url="/login/")
# @transaction.atomic
# def copy_batch_to_final(request, batch_id):
    
#     def to_bool(val):
#         if isinstance(val, bool):
#             return val
#         if isinstance(val, str):
#             return val.lower() in ("true", "1", "yes", "y")
#         return False

#     batch = get_object_or_404(Batch_Table, pk=batch_id)

#     isolates = Referred_Data.objects.filter(
#         Batch_id=batch
#     )

#     copied = 0

#     for isolate in isolates:

#         raw_entries = AntibioticEntry.objects.filter(
#             ab_idNum_referred=isolate
#         )

#         # final data
#         final_obj, _ = Final_Data.objects.update_or_create(
#             f_AccessionNo=isolate.AccessionNo,
#             defaults={

#                 # ===== BATCH / META =====
#                 "f_bat_seq": isolate.bat_seq,
#                 "f_Batch_id": isolate.Batch_id,
#                 "f_Hide": getattr(isolate, "Hide", False),
#                 "f_Batch_Code": isolate.Batch_Code,
#                 "f_Batch_Name": isolate.Batch_Name,
#                 "f_RefNo": isolate.RefNo,
#                 "f_BatchNo": isolate.BatchNo,
#                 "f_Total_batch": isolate.Total_batch,

#                 "f_AccessionNoGen": getattr(isolate, "AccessionNoGen", ""),

#                 "f_SiteCode": isolate.SiteCode,
#                 "f_Site_Name": isolate.Site_Name,
#                 "f_Referral_Date": isolate.Referral_Date,

#                 # ===== PATIENT =====
#                 "f_Patient_ID": isolate.Patient_ID,
#                 "f_First_Name": isolate.First_Name,
#                 "f_Mid_Name": isolate.Mid_Name,
#                 "f_Last_Name": isolate.Last_Name,
#                 "f_Date_Birth": isolate.Date_Birth,
#                 "f_Age": isolate.Age,
#                 "f_Sex": isolate.Sex,

#                 "f_Date_Admis": isolate.Date_Admis,
#                 "f_Nosocomial": isolate.Nosocomial,
#                 "f_Diagnosis": isolate.Diagnosis,
#                 "f_Diagnosis_ICD10": isolate.Diagnosis_ICD10,
#                 "f_Ward": isolate.Ward,
#                 "f_Ward_Type": isolate.Ward_Type,
#                 "f_Service_Type": isolate.Service_Type,

#                 # ===== SPECIMEN =====
#                 "f_Spec_Num": isolate.Spec_Num,
#                 "f_Spec_Date": isolate.Spec_Date,
#                 "f_Spec_Type": isolate.Spec_Type,
#                 "f_Reason": isolate.Reason,
#                 "f_Growth": isolate.Growth,
#                 "f_Urine_ColCt": isolate.Urine_ColCt,

#                 # ===== PHENOTYPE =====
#                 "f_ampC": isolate.ampC,
#                 "f_ESBL": isolate.ESBL,
#                 "f_CARB": isolate.CARB,
#                 "f_MBL": isolate.MBL,
#                 "f_BL": isolate.BL,
#                 "f_MR": isolate.MR,
#                 "f_mecA": isolate.mecA,
#                 "f_ICR": isolate.ICR,
#                 "f_OtherResMech": isolate.OtherResMech,

#                 # ===== SENTINEL ORGANISM =====
#                 "f_Site_Pre": nz(isolate.Site_Pre),
#                 "f_Site_Org": nz(isolate.Site_Org),
#                 "f_Site_OrgName": nz(isolate.Site_OrgName),
#                 "f_Site_Pos": nz(isolate.Site_Pos),
#                 "f_Comments": nz(isolate.Comments),

#                 # ===== ARSRL =====
#                 "f_ars_ampC": isolate.ars_ampC,
#                 "f_ars_ESBL": isolate.ars_ESBL,
#                 "f_ars_CARB": isolate.ars_CARB,
#                 "f_ars_ECIM": isolate.ars_ECIM,
#                 "f_ars_MCIM": isolate.ars_MCIM,
#                 "f_ars_EC_MCIM": isolate.ars_EC_MCIM,
#                 "f_ars_MBL": isolate.ars_MBL,
#                 "f_ars_BL": isolate.ars_BL,
#                 "f_ars_MR": isolate.ars_MR,
#                 "f_ars_mecA": isolate.ars_mecA,
#                 "f_ars_ICR": isolate.ars_ICR,

#                 "f_ars_Pre": nz(isolate.ars_Pre),
#                 "f_ars_Post": nz(isolate.ars_Post),
#                 "f_ars_OrgCode": nz(isolate.ars_OrgCode),
#                 "f_ars_OrgName": nz(isolate.ars_OrgName),

#                 "f_ars_ct_ctl": isolate.ars_ct_ctl,
#                 "f_ars_tz_tzl": isolate.ars_tz_tzl,
#                 "f_ars_cn_cni": isolate.ars_cn_cni,
#                 "f_ars_ip_ipi": isolate.ars_ip_ipi,

#                 "f_ars_reco_Code": isolate.ars_reco_Code,
#                 "f_ars_description": isolate.ars_description,
#                 "f_ars_reco": isolate.ars_reco,

#                 # ===== SIGNATORIES =====
#                 "f_arsp_Encoder": isolate.arsp_Encoder,
#                 "f_arsp_Enc_Lic": isolate.arsp_Enc_Lic,
#                 "f_arsp_Checker": isolate.arsp_Checker,
#                 "f_arsp_Chec_Lic": isolate.arsp_Chec_Lic,
#                 "f_arsp_Verifier": isolate.arsp_Verifier,
#                 "f_arsp_Ver_Lic": isolate.arsp_Ver_Lic,
#                 "f_arsp_LabManager": isolate.arsp_LabManager,
#                 "f_arsp_Lab_Lic": isolate.arsp_Lab_Lic,
#                 "f_arsp_Head": isolate.arsp_Head,
#                 "f_arsp_Head_Lic": isolate.arsp_Head_Lic,
#                 "f_Date_Accomplished_ARSP": isolate.Date_Accomplished_ARSP,

#                 # ===== EXTRA =====
#                 "f_x_mrse": getattr(isolate, "x_mrse", ""),
#                 "f_x_mrsamrse": getattr(isolate, "x_mrsamrse", ""),
#                 "f_x_entbac": getattr(isolate, "x_entbac", ""),
#                 "f_edta": getattr(isolate, "edta", ""),
#             }
#         )


#         # reset final antibiotics
#         Final_AntibioticEntry.objects.filter(
#             ab_idNum_f_referred=final_obj
#         ).delete()

#         # copy abx and breakopints
#         for e in raw_entries:

#             fe = Final_AntibioticEntry(
#                 ab_idNum_f_referred=final_obj,

#                 ab_AccessionNo=e.ab_AccessionNo,
#                 ab_RefNo=e.ab_RefNo,

#                 ab_Antibiotic=e.ab_Antibiotic,
#                 ab_Abx_code=e.ab_Abx_code,
#                 ab_Abx=e.ab_Abx,

#                 ab_Disk_value=e.ab_Disk_value,
#                 ab_Disk_enRIS=e.ab_Disk_enRIS,

#                 ab_MIC_operand=e.ab_MIC_operand,
#                 ab_MIC_value=e.ab_MIC_value,
#                 ab_MIC_enRIS=e.ab_MIC_enRIS,

#                 ab_AlertMIC=e.ab_AlertMIC,

#                 ab_Retest_Antibiotic=e.ab_Retest_Antibiotic,
#                 ab_Retest_Abx_code=e.ab_Retest_Abx_code,
#                 ab_Retest_Abx=e.ab_Retest_Abx,

#                 ab_Retest_DiskValue=e.ab_Retest_DiskValue,
#                 ab_Retest_Disk_enRIS=e.ab_Retest_Disk_enRIS,

#                 ab_Retest_MIC_operand=e.ab_Retest_MIC_operand,
#                 ab_Retest_MICValue=e.ab_Retest_MICValue,
#                 ab_Retest_MIC_enRIS=e.ab_Retest_MIC_enRIS,

#                 ab_Retest_AlertMIC=e.ab_Retest_AlertMIC,
#             )

#             # REQUIRED FOR M2M
#             fe.save()



#             # COPY BREAKPOINT RELATION
#             raw_bps = e.ab_breakpoints_id.all()
#             if raw_bps.exists():
#                 fe.ab_breakpoints_id.add(*raw_bps)


#             # COPY BREAKPOINT VALUES
#             fe.ab_Site_Org = e.ab_Site_Org
#             fe.ab_R_breakpoint = e.ab_R_breakpoint
#             fe.ab_I_breakpoint = e.ab_I_breakpoint
#             fe.ab_SDD_breakpoint = e.ab_SDD_breakpoint
#             fe.ab_S_breakpoint = e.ab_S_breakpoint

#             fe.ab_Ret_Org = e.ab_Ret_Org
#             fe.ab_Org_Flag = to_bool(e.ab_Org_Flag)
#             fe.ab_Abx_Flag = to_bool(e.ab_Abx_Flag)
#             fe.ab_Abx_Phenotype = (e.ab_Abx_Phenotype or "").strip()
#             fe.ab_Ret_R_breakpoint = e.ab_Ret_R_breakpoint
#             fe.ab_Ret_I_breakpoint = e.ab_Ret_I_breakpoint
#             fe.ab_Ret_SDD_breakpoint = e.ab_Ret_SDD_breakpoint
#             fe.ab_Ret_S_breakpoint = e.ab_Ret_S_breakpoint

#             fe.ab_Alert_val = e.ab_Alert_val
#             fe.ab_Retest_Alert_val = e.ab_Retest_Alert_val
            
            
#             fe.save(update_fields=[
#                 "ab_Site_Org",
#                 "ab_R_breakpoint",
#                 "ab_I_breakpoint",
#                 "ab_SDD_breakpoint",
#                 "ab_S_breakpoint",
#                 "ab_Ret_Org",
#                 "ab_Org_Flag",
#                 "ab_Abx_Flag",
#                 "ab_Abx_Phenotype",
#                 "ab_Ret_R_breakpoint",
#                 "ab_Ret_I_breakpoint",
#                 "ab_Ret_SDD_breakpoint",
#                 "ab_Ret_S_breakpoint",
#                 "ab_Alert_val",
#                 "ab_Retest_Alert_val",
#             ])

#         copied += 1

#     messages.success(
#         request,
#         f"{copied} isolates from batch {batch.bat_Batch_Name} "
#         f"copied to Final successfully. Breakpoints preserved."
#     )

#     return redirect("show_data")



@login_required(login_url="/login/")
@transaction.atomic
def copy_batch_to_final(request, batch_id):

    def to_bool(val):
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes", "y")
        return False

    batch = get_object_or_404(Batch_Table, pk=batch_id)

    isolates = Referred_Data.objects.filter(
        Batch_id=batch
    )

    copied = 0
    last_final_obj = None 


    for isolate in isolates:

        spec_obj = None
        if isolate.Spec_Type:
                spec_obj = SpecimenTypeModel.objects.filter(
                    Specimen_code=isolate.Spec_Type
                ).first()
                raw_entries = AntibioticEntry.objects.filter(
                    ab_idNum_referred=isolate
                )



        # ================= FINAL DATA =================
        final_obj, _ = Final_Data.objects.update_or_create(
            f_AccessionNo=isolate.AccessionNo,
            defaults={

                # ===== BATCH / META =====
                "f_bat_seq": isolate.bat_seq,
                "f_Batch_id": isolate.Batch_id,
                "f_Hide": getattr(isolate, "Hide", False),
                "f_Batch_Code": isolate.Batch_Code,
                "f_Batch_Name": isolate.Batch_Name,
                "f_RefNo": isolate.RefNo,
                "f_BatchNo": isolate.BatchNo,
                "f_Total_batch": isolate.Total_batch,

                "f_AccessionNoGen": getattr(isolate, "AccessionNoGen", ""),

                "f_SiteCode": isolate.SiteCode,
                "f_Site_Name": isolate.Site_Name,
                "f_Referral_Date": isolate.Referral_Date,

                # ===== PATIENT =====
                "f_Patient_ID": isolate.Patient_ID,
                "f_First_Name": isolate.First_Name,
                "f_Mid_Name": isolate.Mid_Name,
                "f_Last_Name": isolate.Last_Name,
                "f_Date_Birth": isolate.Date_Birth,
                "f_Age": isolate.Age,
                "f_Sex": isolate.Sex,

                "f_Date_Admis": isolate.Date_Admis,
                "f_Nosocomial": isolate.Nosocomial,
                "f_Diagnosis": isolate.Diagnosis,
                "f_Diagnosis_ICD10": isolate.Diagnosis_ICD10,
                "f_Ward": isolate.Ward,
                "f_Ward_Type": isolate.Ward_Type,
                "f_Service_Type": isolate.Service_Type,

                # ===== SPECIMEN =====
                "f_Spec_Num": isolate.Spec_Num,
                "f_Spec_Date": isolate.Spec_Date,
                "f_Reason": isolate.Reason,
                "f_Growth": isolate.Growth,
                "f_Urine_ColCt": isolate.Urine_ColCt,

                # ===== PHENOTYPE =====
                "f_ampC": isolate.ampC,
                "f_ESBL": isolate.ESBL,
                "f_CARB": isolate.CARB,
                "f_MBL": isolate.MBL,
                "f_BL": isolate.BL,
                "f_MR": isolate.MR,
                "f_mecA": isolate.mecA,
                "f_ICR": isolate.ICR,
                "f_OtherResMech": isolate.OtherResMech,


                "f_Spec_Type": spec_obj,


                # ===== SENTINEL ORGANISM =====
                "f_Site_Pre": nz(isolate.Site_Pre),
                "f_Site_Org": nz(isolate.Site_Org),
                "f_Site_OrgName": nz(isolate.Site_OrgName),
                "f_Site_Pos": nz(isolate.Site_Pos),
                "f_Comments": nz(isolate.Comments),

                # ===== ARSRL =====
                "f_ars_ampC": isolate.ars_ampC,
                "f_ars_ESBL": isolate.ars_ESBL,
                "f_ars_CARB": isolate.ars_CARB,
                "f_ars_ECIM": isolate.ars_ECIM,
                "f_ars_MCIM": isolate.ars_MCIM,
                "f_ars_EC_MCIM": isolate.ars_EC_MCIM,
                "f_ars_MBL": isolate.ars_MBL,
                "f_ars_BL": isolate.ars_BL,
                "f_ars_MR": isolate.ars_MR,
                "f_ars_mecA": isolate.ars_mecA,
                "f_ars_ICR": isolate.ars_ICR,

                "f_ars_Pre": nz(isolate.ars_Pre),
                "f_ars_Post": nz(isolate.ars_Post),
                "f_ars_OrgCode": nz(isolate.ars_OrgCode),
                "f_ars_OrgName": nz(isolate.ars_OrgName),

                "f_ars_ct_ctl": isolate.ars_ct_ctl,
                "f_ars_tz_tzl": isolate.ars_tz_tzl,
                "f_ars_cn_cni": isolate.ars_cn_cni,
                "f_ars_ip_ipi": isolate.ars_ip_ipi,

                "f_ars_reco_Code": isolate.ars_reco_Code,
                "f_ars_description": isolate.ars_description,
                "f_ars_reco": isolate.ars_reco,

                # ===== SIGNATORIES =====
                "f_arsp_Encoder": isolate.arsp_Encoder,
                "f_arsp_Enc_Lic": isolate.arsp_Enc_Lic,
                "f_arsp_Checker": isolate.arsp_Checker,
                "f_arsp_Chec_Lic": isolate.arsp_Chec_Lic,
                "f_arsp_Verifier": isolate.arsp_Verifier,
                "f_arsp_Ver_Lic": isolate.arsp_Ver_Lic,
                "f_arsp_LabManager": isolate.arsp_LabManager,
                "f_arsp_Lab_Lic": isolate.arsp_Lab_Lic,
                "f_arsp_Head": isolate.arsp_Head,
                "f_arsp_Head_Lic": isolate.arsp_Head_Lic,
                "f_Date_Accomplished_ARSP": isolate.Date_Accomplished_ARSP,

                # ===== EXTRA =====
                "f_x_mrse": getattr(isolate, "x_mrse", ""),
                "f_x_mrsamrse": getattr(isolate, "x_mrsamrse", ""),
                "f_x_entbac": getattr(isolate, "x_entbac", ""),
                "f_edta": getattr(isolate, "edta", ""),
            }
        )


        last_final_obj = final_obj  # 🔑 TRACK ACTIVE ISOLATE

        # ================= RESET FINAL ANTIBIOTICS =================
        Final_AntibioticEntry.objects.filter(
            ab_idNum_f_referred=final_obj
        ).delete()

        # ================= COPY ANTIBIOTICS + BREAKPOINTS =================
        for e in raw_entries:

            fe = Final_AntibioticEntry(
                ab_idNum_f_referred=final_obj,

                ab_AccessionNo=e.ab_AccessionNo,
                ab_RefNo=e.ab_RefNo,

                ab_Antibiotic=e.ab_Antibiotic,
                ab_Abx_code=e.ab_Abx_code,
                ab_Abx=e.ab_Abx,

                ab_Disk_value=e.ab_Disk_value,
                ab_Disk_enRIS=e.ab_Disk_enRIS,

                ab_MIC_operand=e.ab_MIC_operand,
                ab_MIC_value=e.ab_MIC_value,
                ab_MIC_enRIS=e.ab_MIC_enRIS,

                ab_AlertMIC=e.ab_AlertMIC,

                ab_Retest_Antibiotic=e.ab_Retest_Antibiotic,
                ab_Retest_Abx_code=e.ab_Retest_Abx_code,
                ab_Retest_Abx=e.ab_Retest_Abx,

                ab_Retest_DiskValue=e.ab_Retest_DiskValue,
                ab_Retest_Disk_enRIS=e.ab_Retest_Disk_enRIS,

                ab_Retest_MIC_operand=e.ab_Retest_MIC_operand,
                ab_Retest_MICValue=e.ab_Retest_MICValue,
                ab_Retest_MIC_enRIS=e.ab_Retest_MIC_enRIS,

                ab_Retest_AlertMIC=e.ab_Retest_AlertMIC,
            )

            fe.save()

            raw_bps = e.ab_breakpoints_id.all()
            if raw_bps.exists():
                fe.ab_breakpoints_id.add(*raw_bps)

            fe.ab_Site_Org = e.ab_Site_Org
            fe.ab_R_breakpoint = e.ab_R_breakpoint
            fe.ab_I_breakpoint = e.ab_I_breakpoint
            fe.ab_SDD_breakpoint = e.ab_SDD_breakpoint
            fe.ab_S_breakpoint = e.ab_S_breakpoint

            fe.ab_Ret_Org = e.ab_Ret_Org
            fe.ab_Org_Flag = to_bool(e.ab_Org_Flag)
            fe.ab_Abx_Flag = to_bool(e.ab_Abx_Flag)
            fe.ab_Abx_Phenotype = (e.ab_Abx_Phenotype or "").strip()
            fe.ab_Abx_Phenotype_Other = (e.ab_Abx_Phenotype_Other or "").strip()

            fe.ab_Ret_R_breakpoint = e.ab_Ret_R_breakpoint
            fe.ab_Ret_I_breakpoint = e.ab_Ret_I_breakpoint
            fe.ab_Ret_SDD_breakpoint = e.ab_Ret_SDD_breakpoint
            fe.ab_Ret_S_breakpoint = e.ab_Ret_S_breakpoint

            fe.ab_Alert_val = e.ab_Alert_val
            fe.ab_Retest_Alert_val = e.ab_Retest_Alert_val

            fe.save(update_fields=[
                "ab_Site_Org",
                "ab_R_breakpoint",
                "ab_I_breakpoint",
                "ab_SDD_breakpoint",
                "ab_S_breakpoint",
                "ab_Ret_Org",
                "ab_Org_Flag",
                "ab_Abx_Flag",
                "ab_Abx_Phenotype",
                "ab_Abx_Phenotype_Other",
                "ab_Ret_R_breakpoint",
                "ab_Ret_I_breakpoint",
                "ab_Ret_SDD_breakpoint",
                "ab_Ret_S_breakpoint",
                "ab_Alert_val",
                "ab_Retest_Alert_val",
            ])

        copied += 1

    # 🔑 SESSION ISOLATE SET ONCE, AFTER COPY
    if last_final_obj:
        request.session["current_final_isolate_id"] = last_final_obj.id

    messages.success(
        request,
        f"{copied} isolates from batch {batch.bat_Batch_Name} "
        f"copied to Final successfully. Breakpoints preserved."
    )

    return redirect("show_data")



### undo batch copy
@login_required(login_url="/login/")
@transaction.atomic
def undo_copy_batch_to_final(request, batch_id):
    try:
        # Get batch
        batch = get_object_or_404(Batch_Table, pk=batch_id)

        # Get all referred isolates in this batch
        isolates = Referred_Data.objects.filter(
            Batch_id=batch
        )

        if not isolates.exists():
            messages.warning(
                request,
                "No referred isolates found for this batch."
            )
            return redirect("show_data")

        accession_numbers = isolates.values_list(
            "AccessionNo", flat=True
        )

        # Find corresponding Final_Data records
        final_qs = Final_Data.objects.filter(
            f_AccessionNo__in=accession_numbers
        )

        if not final_qs.exists():
            messages.warning(
                request,
                "No Final Data records found to undo for this batch."
            )
            return redirect("show_data")

        # Delete Final Antibiotic Entries first
        Final_AntibioticEntry.objects.filter(
            ab_idNum_f_referred__in=final_qs
        ).delete()

         # 2. CLEAR THE SESSION (The Fix)
        # If the isolate currently being edited is in this batch, remove it from session
        current_session_id = request.session.get("current_final_isolate_id")
        if current_session_id and final_qs.filter(pk=current_session_id).exists():
            request.session.pop("current_final_isolate_id", None)

        # Delete Final Data records
        deleted_count, _ = final_qs.delete()

        messages.success(
            request,
            f"Undo successful: {deleted_count} Final records "
            f"from batch {batch.bat_Batch_Name} were removed."
        )

        return redirect("show_data")

    except Exception as e:
        import traceback
        traceback.print_exc()
        messages.error(
            request,
            f"Error undoing batch copy: {e}"
        )
        return redirect("show_data")





##### copy one isolate only
@login_required(login_url="/login/")
@transaction.atomic
def copy_data_to_final(request, id):
    
    def to_bool(val):
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes", "y")
        return False
        

    isolate = get_object_or_404(Referred_Data, pk=id)

    raw_entries = AntibioticEntry.objects.filter(
        ab_idNum_referred=isolate
    )

    # fnial data
    final_obj, _ = Final_Data.objects.update_or_create(
        f_AccessionNo=isolate.AccessionNo,
        defaults={

            # batch meta
            "f_bat_seq": isolate.bat_seq,
            "f_Batch_id": isolate.Batch_id,
            "f_Hide": isolate.Hide if hasattr(isolate, "Hide") else False,
            "f_Batch_Code": isolate.Batch_Code,
            "f_Batch_Name": isolate.Batch_Name,
            "f_RefNo": isolate.RefNo,
            "f_BatchNo": isolate.BatchNo,
            "f_Total_batch": isolate.Total_batch,

            "f_AccessionNoGen": getattr(isolate, "AccessionNoGen", ""),

            "f_SiteCode": isolate.SiteCode,
            "f_Site_Name": isolate.Site_Name,
            "f_Referral_Date": isolate.Referral_Date,

            # PATIENT 
            "f_Patient_ID": isolate.Patient_ID,
            "f_First_Name": isolate.First_Name,
            "f_Mid_Name": isolate.Mid_Name,
            "f_Last_Name": isolate.Last_Name,
            "f_Date_Birth": isolate.Date_Birth,
            "f_Age": isolate.Age,
            "f_Sex": isolate.Sex,

            "f_Date_Admis": isolate.Date_Admis,
            "f_Nosocomial": isolate.Nosocomial,
            "f_Diagnosis": isolate.Diagnosis,
            "f_Diagnosis_ICD10": isolate.Diagnosis_ICD10,
            "f_Ward": isolate.Ward,
            "f_Ward_Type": isolate.Ward_Type,
            "f_Service_Type": isolate.Service_Type,

            # SPECIMEN 
            "f_Spec_Num": isolate.Spec_Num,
            "f_Spec_Date": isolate.Spec_Date,
            "f_Spec_Type": isolate.Spec_Type,
            "f_Reason": isolate.Reason,
            "f_Growth": isolate.Growth,
            "f_Urine_ColCt": isolate.Urine_ColCt,

            # PHENOTYPE 
            "f_ampC": isolate.ampC,
            "f_ESBL": isolate.ESBL,
            "f_CARB": isolate.CARB,
            "f_MBL": isolate.MBL,
            "f_BL": isolate.BL,
            "f_MR": isolate.MR,
            "f_mecA": isolate.mecA,
            "f_ICR": isolate.ICR,
            "f_OtherResMech": isolate.OtherResMech,

            # SENTINEL ORGANISM 
            "f_Site_Pre": nz(isolate.Site_Pre),
            "f_Site_Org": nz(isolate.Site_Org),
            "f_Site_OrgName": nz(isolate.Site_OrgName),
            "f_Site_Pos": nz(isolate.Site_Pos),
            "f_Comments": nz(isolate.Comments),

            # ARSRL
            "f_ars_ampC": isolate.ars_ampC,
            "f_ars_ESBL": isolate.ars_ESBL,
            "f_ars_CARB": isolate.ars_CARB,
            "f_ars_ECIM": isolate.ars_ECIM,
            "f_ars_MCIM": isolate.ars_MCIM,
            "f_ars_EC_MCIM": isolate.ars_EC_MCIM,
            "f_ars_MBL": isolate.ars_MBL,
            "f_ars_BL": isolate.ars_BL,
            "f_ars_MR": isolate.ars_MR,
            "f_ars_mecA": isolate.ars_mecA,
            "f_ars_ICR": isolate.ars_ICR,

            "f_ars_Pre": nz(isolate.ars_Pre),
            "f_ars_Post": nz(isolate.ars_Post),
            "f_ars_OrgCode": nz(isolate.ars_OrgCode),
            "f_ars_OrgName": nz(isolate.ars_OrgName),

            "f_ars_ct_ctl": isolate.ars_ct_ctl,
            "f_ars_tz_tzl": isolate.ars_tz_tzl,
            "f_ars_cn_cni": isolate.ars_cn_cni,
            "f_ars_ip_ipi": isolate.ars_ip_ipi,

            "f_ars_reco_Code": isolate.ars_reco_Code,
            "f_ars_description": isolate.ars_description,
            "f_ars_reco": isolate.ars_reco,

            # SIGNATORIES
            "f_arsp_Encoder": isolate.arsp_Encoder,
            "f_arsp_Enc_Lic": isolate.arsp_Enc_Lic,
            "f_arsp_Checker": isolate.arsp_Checker,
            "f_arsp_Chec_Lic": isolate.arsp_Chec_Lic,
            "f_arsp_Verifier": isolate.arsp_Verifier,
            "f_arsp_Ver_Lic": isolate.arsp_Ver_Lic,
            "f_arsp_LabManager": isolate.arsp_LabManager,
            "f_arsp_Lab_Lic": isolate.arsp_Lab_Lic,
            "f_arsp_Head": isolate.arsp_Head,
            "f_arsp_Head_Lic": isolate.arsp_Head_Lic,
            "f_Date_Accomplished_ARSP": isolate.Date_Accomplished_ARSP,

            # EXTRA
            "f_x_mrse": getattr(isolate, "x_mrse", ""),
            "f_x_mrsamrse": getattr(isolate, "x_mrsamrse", ""),
            "f_x_entbac": getattr(isolate, "x_entbac", ""),
            "f_edta": getattr(isolate, "edta", ""),
        }
    )

    # RESET FINAL ANTIBIOTICS
    Final_AntibioticEntry.objects.filter(
        ab_idNum_f_referred=final_obj
    ).delete()

    # COPY ABX AND BREAKPOINTS
    for e in raw_entries:

        fe = Final_AntibioticEntry(
            ab_idNum_f_referred=final_obj,

            ab_AccessionNo=e.ab_AccessionNo,
            ab_RefNo=e.ab_RefNo,

            ab_Antibiotic=e.ab_Antibiotic,
            ab_Abx_code=e.ab_Abx_code,
            ab_Abx=e.ab_Abx,

            ab_Disk_value=e.ab_Disk_value,
            ab_Disk_enRIS=e.ab_Disk_enRIS,

            ab_MIC_operand=e.ab_MIC_operand,
            ab_MIC_value=e.ab_MIC_value,
            ab_MIC_enRIS=e.ab_MIC_enRIS,

            ab_AlertMIC=e.ab_AlertMIC,

            ab_Retest_Antibiotic=e.ab_Retest_Antibiotic,
            ab_Retest_Abx_code=e.ab_Retest_Abx_code,
            ab_Retest_Abx=e.ab_Retest_Abx,

            ab_Retest_DiskValue=e.ab_Retest_DiskValue,
            ab_Retest_Disk_enRIS=e.ab_Retest_Disk_enRIS,

            ab_Retest_MIC_operand=e.ab_Retest_MIC_operand,
            ab_Retest_MICValue=e.ab_Retest_MICValue,
            ab_Retest_MIC_enRIS=e.ab_Retest_MIC_enRIS,

            ab_Retest_AlertMIC=e.ab_Retest_AlertMIC,
        )

        # SAVE IT FIRST
        fe.save()

        # COPY THE BREAKPOINTS
        raw_bps = e.ab_breakpoints_id.all()
        if raw_bps.exists():
            fe.ab_breakpoints_id.add(*raw_bps)
        

        fe.ab_Site_Org = e.ab_Site_Org
        fe.ab_R_breakpoint = e.ab_R_breakpoint
        fe.ab_I_breakpoint = e.ab_I_breakpoint
        fe.ab_SDD_breakpoint = e.ab_SDD_breakpoint
        fe.ab_S_breakpoint = e.ab_S_breakpoint

        fe.ab_Ret_Org = e.ab_Ret_Org
        fe.ab_Org_Flag = to_bool(e.ab_Org_Flag)
        fe.ab_Abx_Flag = to_bool(e.ab_Abx_Flag)
        fe.ab_Abx_Phenotype = (e.ab_Abx_Phenotype or "").strip()
        fe.ab_Abx_Phenotype_Other = (e.ab_Abx_Phenotype_Other or "").strip()
        fe.ab_Ret_R_breakpoint = e.ab_Ret_R_breakpoint
        fe.ab_Ret_I_breakpoint = e.ab_Ret_I_breakpoint
        fe.ab_Ret_SDD_breakpoint = e.ab_Ret_SDD_breakpoint
        fe.ab_Ret_S_breakpoint = e.ab_Ret_S_breakpoint

        fe.ab_Alert_val = e.ab_Alert_val
        fe.ab_Retest_Alert_val = e.ab_Retest_Alert_val

        fe.save(update_fields=[
            "ab_Site_Org",
            "ab_R_breakpoint",
            "ab_I_breakpoint",
            "ab_SDD_breakpoint",
            "ab_S_breakpoint",
            "ab_Ret_Org",
            "ab_Org_Flag",
            "ab_Abx_Flag",
            "ab_Abx_Phenotype",
            "ab_Abx_Phenotype_Other",
            "ab_Ret_R_breakpoint",
            "ab_Ret_I_breakpoint",
            "ab_Ret_SDD_breakpoint",
            "ab_Ret_S_breakpoint",
            "ab_Alert_val",
            "ab_Retest_Alert_val",
        ])


    messages.success(
        request,
        f"Final data copied successfully for Accession {isolate.AccessionNo}. "
        f"Breakpoints copied correctly."
    )

    return redirect("show_data")




### undo copy of one isolate only
@login_required(login_url="/login/")
def undo_copy_to_final(request, id):
    try:
        # id here is Referred_Data.id
        isolate = get_object_or_404(Referred_Data, pk=id)

        with transaction.atomic():

            #  Delete FINAL data by AccessionNo
            final_qs = Final_Data.objects.filter(
                f_AccessionNo=isolate.AccessionNo
            )

            # Delete related Final_AntibioticEntry first
            Final_AntibioticEntry.objects.filter(
                ab_idNum_f_referred__in=final_qs
            ).delete()

            # Delete Final_Data record
            deleted_count, _ = final_qs.delete()

            if deleted_count == 0:
                messages.warning(
                    request,
                    "No final data copy found to undo."
                )
            else:
                messages.success(
                    request,
                    "Final data copy successfully removed."
                )

        return redirect("show_data")

    except Exception as e:
        import traceback
        traceback.print_exc()
        messages.error(request, f"Error undoing final copy: {e}")
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
                messages.warning(request, " No saved field mappings found. Using raw headers.")

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

            for field_name, value in valid_fields.items():
                if isinstance(value, str) and len(value) > 255:
                    print(f"[WARNING] {accession} - Field '{field_name}' exceeds 255 chars ({len(value)} chars)")
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
                f"Upload complete! "
                f"{created_ref} new Referred_Data, {updated_ref} updated; "
                f"{created_abx} new AntibioticEntry, {updated_abx} updated."
            )
            return redirect("show_data")

        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f" Error processing file: {e}")

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




############ FIELD MAPPER TOOL ############

 # this is the updated field mapper tool with temp file saving and session management
@login_required
def field_mapper_tool(request):
    # upload a raw file and preview headers for mapping.
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
            Antibiotic_List.objects.filter(Retest=True)
            .values_list("Whonet_Abx", flat=True)
            .distinct().order_by("Whonet_Abx")
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


    return render(request, "home/upload_raw.html")


# AJAX endpoint to save/update a field mapping used in the field mapper tool
@login_required
@require_POST
def update_field_mapping(request):
    import json

    data = json.loads(request.body)
    raw_field = data.get("raw_field")
    mapped_field = data.get("mapped_field", "").strip()

    if not raw_field:
        return JsonResponse({"status": "error", "msg": "Missing raw_field"}, status=400)

    if mapped_field == "":
        #  Clear mapping
        FieldMapping.objects.filter(
            user=request.user,
            raw_field=raw_field
        ).delete()
    else:
        FieldMapping.objects.update_or_create(
            user=request.user,
            raw_field=raw_field,
            defaults={"mapped_field": mapped_field, "field_type": data.get("field_type", "demog")},
        )

    return JsonResponse({"status": "ok"})



# clear all saved mappings for the user
@login_required
def clear_mappings(request):

    if request.method == "POST":
        FieldMapping.objects.filter(user=request.user).delete()
        messages.success(request, "Your saved field mappings were cleared.")
    return redirect("field_mapper_tool")


# helped function to delete temp file after download
@login_required
def cleanup_temp_file(file_path, request):
   
    if file_path and os.path.exists(file_path):
            os.remove(file_path)


@login_required
def download_mapping_summary(request):
    # function to normalize strings for comparison 
    def normalize(val):
        return re.sub(r"[^a-z0-9]", "", str(val).lower())

   # load uploaded file headers
    temp_path = request.session.get("temp_file_path")
    original_name = request.session.get("temp_file_name", "mapping_summary")

    if not temp_path or not os.path.exists(temp_path):
        messages.error(request, "Temporary file not found. Please upload again.")
        return redirect("field_mapper_tool")

    if temp_path.endswith(".csv"):
        df = pd.read_csv(temp_path, nrows=0)
    else:
        df = pd.read_excel(temp_path, nrows=0)

    uploaded_headers = list(df.columns)

  # load saved mappings
    mappings = FieldMapping.objects.filter(user=request.user)

    mapped_norm = {
        normalize(m.raw_field) for m in mappings
    }


    # load database columns
    
    final_fields = [
        f.name for f in Final_Data._meta.fields
        if f.name != "id"
    ]

    abx_fields = list(
        Antibiotic_List.objects.values_list("Whonet_Abx", flat=True)
        .distinct()
        .order_by("Whonet_Abx")
    )

    database_columns = sorted(set(final_fields + abx_fields))

    db_norm = {
        normalize(c) for c in database_columns
    }

    # determine unmapped headers
    uploaded_norm_map = {
        normalize(h): h for h in uploaded_headers
    }

    unmapped_headers = [
        original_name
        for norm, original_name in uploaded_norm_map.items()
        if norm not in mapped_norm and norm not in db_norm
    ]

   # build dataframes for each sheet
    df_db = pd.DataFrame({
        "Database_Column_Name": database_columns
    })

    df_uploaded = pd.DataFrame({
        "Uploaded_Column_Name": uploaded_headers
    })

    df_unmapped = pd.DataFrame({
        "Unmapped_Column_Name": unmapped_headers
    })

    # create 3 sheet excel file
    safe_name = os.path.splitext(original_name)[0]
    filename = f"{safe_name}_FIELD_MAPPING_SUMMARY.xlsx"

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    with pd.ExcelWriter(response, engine="openpyxl") as writer:
        df_db.to_excel(writer, index=False, sheet_name="Database_Columns")
        df_uploaded.to_excel(writer, index=False, sheet_name="Uploaded_Columns")
        df_unmapped.to_excel(writer, index=False, sheet_name="Unmapped_Columns")

    return response




def extract_antibiotics(df):
    """
    Antibiotic extraction rules (STRICT):
    - Disk:     <ABX>_ND<potency>
    - Disk RIS: <ABX>_ND<potency>_RIS
    - MIC OP:   <ABX>_NM_OP
    - MIC:      <ABX>_NM
    - MIC RIS:  <ABX>_NM_RIS
    """

    def clean_series(s):
        if isinstance(s, pd.DataFrame):
            s = s.iloc[:, 0]
        if not isinstance(s, pd.Series):
            s = pd.Series(s)
        return (
            s.replace([None, "None", "nan", "NaN", "NAN", "null"], "")
             .fillna("")
             .astype(str)
        )

    def split_operand(val):
        if not val:
            return "", ""
        m = re.match(r"^(<=|>=|<|>|=)?\s*([\d.]+)$", str(val).strip())
        return (m.group(1) or "", m.group(2)) if m else ("", val)

    cols = list(df.columns)
    abx_df = pd.DataFrame(index=df.index)

   # disk VALUES + RIS no operands
    disk_vals = [c for c in cols if re.fullmatch(r"[A-Za-z]+_ND\d+", c)]

    for col in disk_vals:
        abx_df[col.upper()] = clean_series(df[col]).str.upper()

        ris_col = f"{col}_RIS"
        if ris_col in df.columns:
            abx_df[f"{col.upper()}_RIS"] = clean_series(df[ris_col]).str.upper()
        else:
            abx_df[f"{col.upper()}_RIS"] = ""

    # mic VALUES + OPS + RIS
    mic_vals = [c for c in cols if re.fullmatch(r"[A-Za-z]+_NM", c)]

    for col in mic_vals:
        base = col[:-3]  # remove _NM

        ops, vals = [], []
        for v in clean_series(df[col]):
            op, val = split_operand(v)
            ops.append(op)
            vals.append(val.upper())

        abx_df[f"{base.upper()}_NM_OP"] = ops
        abx_df[f"{base.upper()}_NM"] = vals

        ris_col = f"{col}_RIS"
        if ris_col in df.columns:
            abx_df[f"{base.upper()}_NM_RIS"] = clean_series(df[ris_col]).str.upper()
        else:
            abx_df[f"{base.upper()}_NM_RIS"] = ""

    return abx_df



# WORKING VERSION AND CORRECTED ERROR IN DEMOGRAPHICS MAPPING
@login_required
def generate_mapped_excel(request):
    if request.method != "POST":
        return redirect("field_mapper_tool")

    try:
        import os, io, re
        import pandas as pd
        from django.http import HttpResponse
        from django.contrib import messages
        from apps.home.models import FieldMapping  # this ensures the model is imported

        # -HELPER FUNCTIONS-

        # Clean series function to standardize data formatting and missing values
        def clean_series(s):
            if isinstance(s, pd.DataFrame):
                s = s.iloc[:, 0]
            if not isinstance(s, pd.Series):
                s = pd.Series(s)
            return s.replace([None, "None", "nan", "NaN", "NAN", "null"], "").fillna("").astype(str)

        # Split operand function for MIC values
        def split_operand(val):
            if not val: return "", ""
            m = re.match(r"^(<=|>=|<|>|=)?\s*([\d.]+)$", str(val).strip())
            return (m.group(1) or "", m.group(2)) if m else ("", val)

        # --- Load File ---
        temp_file_path = request.session.get("temp_file_path")
        temp_file_name = request.session.get("temp_file_name", "uploaded.xlsx")

        if not temp_file_path or not os.path.exists(temp_file_path):
            messages.error(request, "File not found.")
            return redirect("field_mapper_tool")

        df = pd.read_csv(temp_file_path) if temp_file_name.lower().endswith(".csv") else pd.read_excel(temp_file_path)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Build original col_map BEFORE any renaming
        col_map = {c.lower(): c for c in df.columns}

        # accession and year extraction
        acc_col = next((c for c in df.columns if "accession" in c.lower()), None)
        spec_date_col = next((c for c in df.columns if "spec" in c.lower() and "date" in c.lower()), None)
        year_vals = [""] * len(df)
        if spec_date_col:
            year_vals = pd.to_datetime(df[spec_date_col], errors="coerce").dt.year.apply(lambda x: "" if pd.isna(x) else str(int(x))).tolist()

        # build antibiotic entries
        abx_df = pd.DataFrame()
        abx_df["f_AccessionNo"] = clean_series(df[acc_col]) if acc_col else ""
        abx_df["Year"] = year_vals

        # Disk & MIC Loops - Using col_map to find real column names - ensures disk antibiotics are captured correctly

        # Disk columns
        disk_cols = [c for c in col_map if re.fullmatch(r"[a-z]+_nd\d+", c)]
        for lc in disk_cols:
            real = col_map[lc]
            ris_lc = f"{lc}_ris"
            raw_vals = df[real]
            if isinstance(raw_vals, pd.DataFrame): raw_vals = raw_vals.iloc[:, 0]
            disk_vals = pd.to_numeric(raw_vals, errors="coerce").astype("Int64").astype(str)
            disk_vals = ["" if v == "<NA>" else v for v in disk_vals]
            abx_df[real.upper()] = disk_vals
            if ris_lc in col_map:
                ris_series = df[col_map[ris_lc]]
                if isinstance(ris_series, pd.DataFrame): ris_series = ris_series.iloc[:, 0]
                abx_df[f"{real.upper()}_RIS"] = clean_series(ris_series).str.upper()
            else:
                abx_df[f"{real.upper()}_RIS"] = ""
        # MIC columns
        mic_cols = [c for c in col_map if re.fullmatch(r"[a-z]+_nm", c)]
        for lc in mic_cols:
            real = col_map[lc]
            base = real[:-3]
            ris_lc = f"{lc}_ris"
            target_col = df[real]
            if isinstance(target_col, pd.DataFrame): target_col = target_col.iloc[:, 0]
            ops, vals = [], []
            for v in clean_series(target_col):
                op, val = split_operand(v)
                ops.append(op)
                vals.append(val.upper())
            abx_df[f"{base.upper()}_NM_OP"] = ops
            abx_df[f"{base.upper()}_NM"] = vals
            if ris_lc in col_map:
                ris_series = df[col_map[ris_lc]]
                if isinstance(ris_series, pd.DataFrame): ris_series = ris_series.iloc[:, 0]
                abx_df[f"{base.upper()}_NM_RIS"] = clean_series(ris_series).str.upper()
            else:
                abx_df[f"{base.upper()}_NM_RIS"] = ""

        # Build demogs dataframe
        user_mappings = FieldMapping.objects.filter(user=request.user, mapped_field__isnull=False)
        rename_dict = {m.raw_field: m.mapped_field for m in user_mappings}

        # Filter for strictly non-antibiotic columns
        demogs_cols = [
            c for c in df.columns 
            if not re.search(r"_(nd\d+|nm)(_ris)?$", c, re.I)
        ]

        # Create the demogs slice and rename them based on model fields
        demogs_df = df[demogs_cols].copy()
        demogs_df.rename(columns=rename_dict, inplace=True)

        # Clean all data in demogs
        for c in demogs_df.columns:
            demogs_df[c] = clean_series(demogs_df[c])

       # output to excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            demogs_df.to_excel(writer, index=False, sheet_name="Demogs")
            abx_df.to_excel(writer, index=False, sheet_name="Antibiotic_Entries")

        output.seek(0)
        response = HttpResponse(output.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        base_name = os.path.splitext(temp_file_name)[0]
        response["Content-Disposition"] = f'attachment; filename="{base_name}_Mapped.xlsx"'
        return response

    except Exception as e:
        import traceback
        traceback.print_exc()
        messages.error(request, f"⚠️ Error: {e}")
        return redirect("field_mapper_tool")







############# Antibiotics Configuration

@login_required(login_url="/login/")
def add_antibiotics(request):
    if request.method == "POST":
        form = AntibioticsForm(request.POST)

        if form.is_valid():
            antibiotic = form.save()
            messages.success(
                request,
                f"Antibiotic '{antibiotic.Antibiotic}' added successfully."
            )
        else:
            messages.error(request, "Form validation failed. Please check your inputs.")

    # Always go back to Settings → Antibiotics tab
    return redirect("/settings/?tab=antibiotics")


@login_required(login_url="/login/")
def edit_antibiotics(request, pk):
    antibiotic = get_object_or_404(Antibiotic_List, pk=pk)
    abx_upload_form = Antibiotics_uploadForm()  
    if request.method == "POST":
        form = AntibioticsForm(request.POST, instance=antibiotic)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Antibiotic '{antibiotic.Antibiotic}' updated successfully."
            )

            return redirect("/settings/?tab=antibiotics")

        messages.error(request, "Form validation failed. Please check your inputs.")
    else:
        form = AntibioticsForm(instance=antibiotic)

    return render(
        request,
        "home/Antibiotic_list.html",   # SEPARATE EDIT PAGE
        {
            "form": form,
            "antibiotic": antibiotic,
            "abx_upload_form": abx_upload_form,
            "editing": True,        # to indicate edit mode # optional but useful
        },
    )


@login_required(login_url="/login/")
def antibiotics_view(request):
    q = request.GET.get("q", "").strip()

    antibiotics = Antibiotic_List.objects.all().order_by("Whonet_Abx")

    if q:
        antibiotics = antibiotics.filter(
            Q(Antibiotic__icontains=q) |
            Q(Whonet_Abx__icontains=q) |
            Q(Abx_code__icontains=q) |
            Q(Guidelines__icontains=q) |
            Q(Test_Method__icontains=q) |
            Q(Potency__icontains=q) |
            Q(Tier__icontains=q) |
            Q(Class__icontains=q) |
            Q(Subclass__icontains=q)
        )

    paginator = Paginator(antibiotics, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "home/Antibiotic_View.html",
        {
            "antibiotics": antibiotics,
            "page_obj": page_obj,
            "q": q,
        },
    )



@login_required(login_url="/login/")
#Delete breakpoints
def antibiotics_del(request, id):
    antibiotics = get_object_or_404(Antibiotic_List, pk=id)
    antibiotics.delete()
    return redirect('antibiotics_view')



@login_required(login_url="/login/")
# for uploading and replacing existing breakpoints data
def upload_antibiotics(request):
    if request.method == "POST":
        abx_upload_form = Antibiotics_uploadForm(request.POST, request.FILES)
        if abx_upload_form.is_valid():
            # Save the uploaded file instance
            uploaded_file = abx_upload_form.save()
            file = uploaded_file.File_uploadAbx  # Get the actual file field
            print("Uploaded file:", file)  # Debugging statement
            try:
                # Load file into a DataFrame using file's temporary path
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)  # For CSV files
                    
                elif file.name.endswith('.xlsx'):
                    df = pd.read_excel(file)  # For Excel files

                else:
                    messages.error(request, messages.INFO, 'Unsupported file format. Please upload a CSV or Excel file.')
                    return redirect('upload_antibiotics')

                # Check the DataFrame for debugging
                print(df)
                
                # Check the DataFrame for debugging
                print("DataFrame contents:\n", df.head())  # Print the first few rows

                # Check column and Replace NaN values with empty strings to avoid validation errors
                df.fillna(value={col: "" for col in df.columns}, inplace=True)


                 # Use this to Clear existing records with matching Whonet_Abx values
                whonet_abx_values = df['Whonet_Abx'].unique()
                Antibiotic_List.objects.filter(Whonet_Abx__in=whonet_abx_values).delete()


                # Insert rows into BreakpointsTable
                for _, row in df.iterrows():
                    # Parse Date_Modified if it's present and valid
                    date_modified = None
                    if row.get('Date_Modified'):
                        date_modified = pd.to_datetime(row['Date_Modified'], errors='coerce')
                        if pd.isna(date_modified):
                            date_modified = None

                    # Create a new instance of BreakpointsTable
                    Antibiotic_List.objects.update_or_create(
                        Whonet_Abx=row.get('Whonet_Abx', ''),   # lookup field
                        defaults={
                            'Show': bool(row.get('Show', False)),
                            'Show_Site': bool(row.get('Show_Site', False)),
                            'Show_Ars': bool(row.get('Show_Ars', False)),
                            'Show_Value': bool(row.get('Show_Value', False)),
                            'Retest': bool(row.get('Retest', False)),
                            'Disk_Abx': bool(row.get('Disk_Abx', False)),
                            'Test_Method': row.get('Test_Method', ''),
                            'Tier': row.get('Tier', ''),
                            'Abx_code': row.get('Abx_code', ''),
                            'Whonet_Abx': row.get('Whonet_Abx', ''),
                            'Antibiotic': row.get('Antibiotic', ''),
                            'Guidelines': row.get('Guidelines', ''),
                            'Potency': row.get('Potency', ''),
                            'Class': row.get('Class', ''),
                            'Subclass': row.get('Subclass', ''),
                            'Date_Modified': date_modified,
                        }
                    )

                
                messages.success(request, messages.INFO, 'File uploaded and data was updated successfully!')
                return redirect('antibiotics_view')

            except Exception as e:
                print("Error during processing:", e)  # Debug statement
                messages.error(request, f"Error processing file: {e}")
                return redirect('add_antibiotics')
        else:
            messages.error(request, messages.INFO, "Form is not valid.")

    else:
        abx_upload_form = Antibiotics_uploadForm()

    return render(request, 'settings.html', {'abx_upload_form': abx_upload_form})




@login_required(login_url="/login/")
#for exporting into excel
def export_antibiotics(request):
    objects = Antibiotic_List.objects.all()
    data = []

    for obj in objects:
        data.append({
            "Show": obj.Show,
            "Retest": obj.Retest,
            "Show_Site": obj.Show_Site,
            "Show_Ars": obj.Show_Ars,
            "Show_Value": obj.Show_Value,
            "Disk_Abx": obj.Disk_Abx,
            "Guidelines": obj.Guidelines,
            "Tier": obj.Tier,
            "Test_Method": obj.Test_Method,
            "Potency": obj.Potency,
            "Abx_code": obj.Abx_code,
            "Whonet_Abx": obj.Whonet_Abx,
            "Antibiotic": obj.Antibiotic,
            "Class": obj.Class,
            "Subclass": obj.Subclass,
            "Date_Modified": obj.Date_Modified,
        })
    
    # Define file path
    file_path = "Antibiotic_list.xlsx"

    # Convert data to DataFrame and save as Excel
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False)

    # Return the file as a response
    return FileResponse(open(file_path, "rb"), as_attachment=True, filename="Antibiotic_list.xlsx")




@login_required(login_url="/login/")
def delete_all_antibiotics(request):
    Antibiotic_List.objects.all().delete()
    messages.success(request, "All records have been deleted successfully.")
    return redirect('antibiotics_view')  # Redirect to the table view




######################## Organism 
@login_required(login_url="/login/")
def add_organism(request):

    if request.method == "POST":
        org_form = OrganismForm(request.POST)

        if org_form.is_valid():
            org_form.save()
            messages.success(request, "Organism added successfully.")
        else:
            messages.error(request, "Form validation failed. Please check your inputs.")

    # Always return to Settings → Organisms tab
    return redirect("/settings/?tab=organisms")



@login_required(login_url="/login/")
def edit_organism(request, pk):
    organism = get_object_or_404(Organism_List, pk=pk)
    org_upload_form = Organism_uploadForm()  # keep upload support

    if request.method == "POST":
        org_form = OrganismForm(request.POST, instance=organism)

        if org_form.is_valid():
            org_form.save()
            messages.success(request, "Organism updated successfully.")
            return redirect("/settings/?tab=organisms")

        messages.error(request, "Form validation failed. Please check your inputs.")
    else:
        org_form = OrganismForm(instance=organism)

    return render(request, "home/Organism.html", {
        "org_form": org_form,
        "organism": organism,
        "org_upload_form": org_upload_form,
    })


@login_required(login_url="/login/")
def view_organism(request):
    q = request.GET.get("q", "").strip()

    organisms = Organism_List.objects.order_by("Whonet_Org_Code")

    if q:
        organisms = organisms.filter(
            Q(Organism__icontains=q) |
            Q(Whonet_Org_Code__icontains=q) |
            Q(Genus_Group__icontains=q) |
            Q(Genus_Code__icontains=q) |
            Q(Species_Group__icontains=q) |
            Q(Serovar_Group__icontains=q) |
            Q(Organism_Type__icontains=q) |
            Q(Kingdom__icontains=q) |
            Q(Phylum__icontains=q) |
            Q(Class__icontains=q) |
            Q(Order__icontains=q) |
            Q(Family_Code__icontains=q)
        )

    paginator = Paginator(organisms, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "home/Organism_view.html", {
        "page_obj": page_obj,
        "organisms": page_obj.object_list,  # optional cleanup
        "search_query": q,
    })





@login_required(login_url="/login/")
#Delete Organism
def del_organism (request, id):
    organism = get_object_or_404(Organism_List, pk=id)
    organism.delete()
    return redirect('view_organism')


@login_required(login_url="/login/")
def del_all_organism(request):
    Organism_List.objects.all().delete()
    messages.success(request, "All records have been deleted successfully.")
    return redirect('view_organism')  # Redirect to the table view




@login_required(login_url="/login/")
def upload_organisms(request):

    if request.method == "POST":
        org_upload_form = Organism_uploadForm(request.POST, request.FILES)

        if org_upload_form.is_valid():
            uploaded_file = org_upload_form.save()
            file = uploaded_file.File_uploadOrg

            try:
                # Load file depending on extension
                if file.name.endswith(".csv"):
                    df = pd.read_csv(file)
                elif file.name.endswith(".xlsx"):
                    df = pd.read_excel(file)
                else:
                    messages.error(request, "Unsupported file format. Please upload CSV or Excel.")
                    return redirect("upload_organisms")

                # Fill NaN with empty string
                df = df.fillna("")

                # Required column
                if "Whonet_Org_Code" not in df.columns:
                    messages.error(request, "Missing required column: Whonet_Org_Code")
                    return redirect("upload_organisms")

                # Delete existing records matching incoming Whonet_Org_Code
                whonet_codes = df["Whonet_Org_Code"].unique()
                Organism_List.objects.filter(Whonet_Org_Code__in=whonet_codes).delete()

                # Loop through DataFrame rows
                for _, row in df.iterrows():
                    Organism_List.objects.update_or_create(
                        Whonet_Org_Code=row.get("Whonet_Org_Code", ""),
                        defaults={
                            "Replaced_by": row.get("Replaced_by", ""),
                            "Organism": row.get("Organism", ""),
                            "Organism_Type": row.get("Organism_Type", ""),
                            "Family_Code": row.get("Family_Code", ""),
                            "Genus_Group": row.get("Genus_Group", ""),
                            "Genus_Code": row.get("Genus_Code", ""),
                            "Species_Group": row.get("Species_Group", ""),
                            "Serovar_Group": row.get("Serovar_Group", ""),
                            "Kingdom": row.get("Kingdom", ""),
                            "Phylum": row.get("Phylum", ""),
                            "Class": row.get("Class", ""),
                            "Order": row.get("Order", ""),
                            "Family": row.get("Family", ""),
                            "Genus": row.get("Genus", ""),
                        }
                    )

                messages.success(request, "Organism list uploaded and updated successfully!")
                return redirect("view_organism")

            except Exception as e:
                print("Upload error:", e)
                messages.error(request, f"Error processing file: {e}")
                return redirect("add_organism")

        else:
            messages.error(request, "Upload form is not valid.")

    else:
        org_upload_form = Organism_uploadForm()

    return render(request, "Settings.html", {
        "org_upload_form": org_upload_form
    })




@login_required(login_url="/login/")
#for exporting into excel
def export_organisms(request):
    objects = Organism_List.objects.all()
    data = []

    for obj in objects:
        data.append({
            "Whonet_Org_Code": obj.Whonet_Org_Code or "",
            "Organism": obj.Organism or "",
            "Organism_Type": obj.Organism_Type or "",
            "Replaced_by": obj.Replaced_by or "",

            "Family_Code": obj.Family_Code or "",
            "Genus_Group": obj.Genus_Group or "",
            "Genus_Code": obj.Genus_Code or "",
            "Species_Group": obj.Species_Group or "",
            "Serovar_Group": obj.Serovar_Group or "",

            "Kingdom": obj.Kingdom or "",
            "Phylum": obj.Phylum or "",
            "Class": obj.Class or "",
            "Order": obj.Order or "",
            "Family": obj.Family or "",
            "Genus": obj.Genus or "",
        })

    
    # Define file path
    file_path = "Organism_list.xlsx"

    # Convert data to DataFrame and save as Excel
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False)

    # Return the file as a response
    return FileResponse(open(file_path, "rb"), as_attachment=True, filename="Organism_list.xlsx")



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




############ TAT Process Configuration
@login_required(login_url="/login/")
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



############ Emerging Resistance
@login_required(login_url="/login/")
def add_emerging_age(request):

    if request.method == "POST":
        eme_form = Emerge_Pheno_Form(request.POST)

        if eme_form.is_valid():
            eme_form.save()
            messages.success(request, "You have successfully created an Emerging Resistance Criteria")
        else:
            messages.error(request, "Form validation failed. Please check your inputs.")

    # Always return to Settings → Emerging
    return redirect("/settings/?tab=emerging")


@login_required(login_url="/login/")
def view_eme_age(request):
    criteria = Emerging_Filter_Age.order_by("Eme_Organism")

    paginator = Paginator(criteria, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "home/Emerge_Phen_View.html", {
        "page_obj": page_obj,
        "criteria": page_obj.object_list,  # optional cleanup
    })


@login_required(login_url="/login/")
def edit_eme_age(request, pk):
    criteria = get_object_or_404(Emerging_Filter_Age, pk=pk)
    eme_upload_form = Eme_Crit_Upload_Form()

    if request.method == "POST":
        eme_form = Emerge_Pheno_Form(request.POST, instance=criteria)

        if eme_form.is_valid():
            eme_form.save()
            messages.success(request, "Emerging Criteria updated successfully.")
            return redirect("settings_page")  # clean redirect

        messages.error(request, "Form validation failed. Please check your inputs.")
    else:
        eme_form = Emerge_Pheno_Form(instance=criteria)

    return render(request, "settings/settings_page.html", {
        "eme_form": eme_form,
        "criteria": criteria,
        "eme_upload_form": eme_upload_form,
        "active_tab": "emerging",   
    })






# download list of emerging
@login_required(login_url="/login/")
def download_emerging_csv(request):
    queryset = (
        Referred_Data.objects
        .filter(
            Emerging_Flag_Age=True,
            Specimen_Type__Emerging_Spec_Flag=True,
            antibiotic_entries__ab_breakpoints_id__Emerging_Abx_Flag=True,
        )
        .distinct()
        .prefetch_related("antibiotic_entries")
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="emerging_cases.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Accession No",
        "Age",
        "Specimen",
        "Antibiotics"
    ])

    for case in queryset:
        antibiotics = ", ".join(
            ab.ab_Abx_code for ab in case.antibiotic_entries.all()
        )

        writer.writerow([
            case.AccessionNo,
            case.Age,
            str(case.Specimen_Type),
            antibiotics
        ])

    return response


########### Phenotypes --- PRE

@login_required(login_url="/login/")
def add_phenotype_pre(request):

    if request.method != "POST":
        return redirect("/settings/?tab=pheno_pre_tab")

    form = Phenotype_Pre_Form(request.POST)

    
    context = {
        "pheno_pre_form": form,
        "editing": False,
    }


    if form.is_valid():
        form.save()
        messages.success(request, "Phenotype (Pre) added successfully.")
    else:
        messages.error(request, "Failed to add Phenotype (Pre).")
        print(form.errors)

    return redirect("/settings/?tab=pheno_pre_tab")




@login_required(login_url="/login/")
def edit_phenotype_pre(request, pk):

    phenotype = get_object_or_404(Phenotype_Pre, pk=pk)

    form = Phenotype_Pre_Form(instance=phenotype)

    context = {
        "pheno_pre_form": form,
        "editing": True,
        "edit_id": phenotype.id,
    }

    return render(
    request,
    "home/Pheno_Pre.html",
    {
        "form": Phenotype_Pre_Form(instance=phenotype),
        "object": phenotype,
    }
)




@login_required(login_url="/login/")
def update_phenotype_pre(request, id):

    phenotype = get_object_or_404(Phenotype_Pre, pk=pk)

    if request.method != "POST":
        return redirect("/settings/?tab=pheno_pre_tab")

    form = Phenotype_Pre_Form(request.POST, instance=phenotype)

    if form.is_valid():
        form.save()
        messages.success(request, "Phenotype (Pre) updated successfully.")
    else:
        messages.error(request, "Failed to update Phenotype (Pre).")
        print(form.errors)

    return redirect("/settings/?tab=pheno_pre_tab")



@login_required(login_url="/login/")
def upload_phenotype_pre(request):

    if request.method != "POST":
        return redirect("/settings/?tab=pheno_pre_tab")

    pheno_pre_upload_form = Pheno_pre_upForm(request.POST, request.FILES)

    if not pheno_pre_upload_form.is_valid():
        messages.error(request, "Invalid upload file.")
        return redirect("/settings/?tab=pheno_pre_tab")

    file = request.FILES["File_Pheno_pre"]


    Phenotype_Pre.objects.all().delete()

    try:
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        for _, row in df.iterrows():
            Phenotype_Pre.objects.create(
                Pre_Phenotypes=row.get("Pre_Phenotypes")
            )

        messages.success(request, "Phenotype (Pre) uploaded successfully.")

    except Exception as e:
        messages.error(request, "Upload failed.")
        print(e)

    return redirect("view_phenotype_pre")


@login_required(login_url="/login/")
def delete_phenotype_pre(request, pk):

    phenotype = get_object_or_404(Phenotype_Pre, pk=pk)
    phenotype.delete()

    messages.success(request, "Phenotype (Pre) deleted.")
    return redirect("/settings/?tab=pheno_pre_tab")


@login_required(login_url="/login/")
def delete_all_phenotype_pre(request):

    if request.method == "POST":
        Phenotype_Pre.objects.all().delete()
        messages.success(request, "All Phenotype (Pre) records deleted.")

    return redirect("/settings/?tab=pheno_pre_tab")



@login_required(login_url="/login/")
# View to display all specimen types
def view_phenotype_pre(request):
    q = request.GET.get("q", "").strip()
    sort_by = request.GET.get('sort', 'Pre_Phenotypes')  # Default sort field
    order = request.GET.get('order', 'desc')  # Default sort order

    sort_field = f"-{sort_by}" if order == 'desc' else sort_by
    pheno_pre_items = Phenotype_Pre.objects.all().order_by(sort_field)

    if q:
        pheno_pre_items = pheno_pre_items.filter(
            Q(Pre_Phenotypes__icontains=q)
        )

    paginator = Paginator(pheno_pre_items, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)


    return render(request, 'home/Pheno_Pre_View.html', {'pheno_pre_items': pheno_pre_items, 'page_obj': page_obj, 'q': q, 'sort_by': sort_by, 'order': order})





################ Phenotypes --- POST


@login_required(login_url="/login/")
def add_phenotype_post(request):

    if request.method != "POST":
        return redirect("/settings/?tab=pheno_post_tab")

    form = Phenotype_Post_Form(request.POST)

    context = {
        "pheno_post_form": form,
        "editing": False,
    }

    if form.is_valid():
        form.save()
        messages.success(request, "Phenotype (Post) added successfully.")
    else:
        messages.error(request, "Failed to add Phenotype (Post).")
        print(form.errors)

    return redirect("/settings/?tab=pheno_post_tab")


@login_required(login_url="/login/")
def view_phenotype_post(request):

    q = request.GET.get("q", "").strip()

    phenotype_posts = Phenotype_Post.objects.all()

    if q:
        phenotype_posts = phenotype_posts.filter(
            Post_Phenotypes__icontains=q
        )

    phenotype_posts = phenotype_posts.order_by("Post_Phenotypes")

    paginator = Paginator(phenotype_posts, 25)  # rows per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "q": q,
    }

    return render(
        request,
        "home/Pheno_Post_View.html",
        context
    )


@login_required(login_url="/login/")
def upload_phenotype_post(request):

    if request.method != "POST":
        return redirect("/settings/?tab=pheno_post_tab")

    upload_file = request.FILES.get("File_Pheno_post")

    if not upload_file:
        messages.error(request, "No file selected for upload.")
        return redirect("/settings/?tab=pheno_post_tab")

    # Save uploaded file (optional audit trail)
    Pheno_upload_Post.objects.create(File_Pheno_post=upload_file)

    try:
        # Read file
        if upload_file.name.endswith(".csv"):
            df = pd.read_csv(upload_file)
        else:
            df = pd.read_excel(upload_file)

        # Normalize column names
        df.columns = [c.strip() for c in df.columns]

        # Expected column name
        expected_column = "Post_Phenotypes"

        if expected_column not in df.columns:
            messages.error(
                request,
                f"Missing required column: {expected_column}"
            )
            return redirect("/settings/?tab=pheno_post_tab")

        # OVERWRITE existing data
        Phenotype_Post.objects.all().delete()

        phenotype_objects = []
        for value in df[expected_column].dropna():
            phenotype_objects.append(
                Phenotype_Post(
                    Post_Phenotypes=str(value).strip()
                )
            )

        Phenotype_Post.objects.bulk_create(phenotype_objects)

        messages.success(
            request,
            f"{len(phenotype_objects)} Phenotype (Post) records uploaded successfully."
        )

    except Exception as e:
        messages.error(request, f"Upload failed: {str(e)}")

    return redirect("/settings/?tab=pheno_post_tab")



@login_required(login_url="/login/")
def edit_phenotype_post(request, pk):

    phenotype_post = get_object_or_404(Phenotype_Post, pk=pk)
    form = Phenotype_Post_Form(instance=phenotype_post)

    context = {
        "form": form,
        "object": phenotype_post,
        "editing": True,
    }

    return render(
        request,
        "home/Pheno_Post.html",
        context
    )



@login_required(login_url="/login/")
def update_phenotype_post(request, pk):

    phenotype_post = get_object_or_404(Phenotype_Post, pk=pk)

    if request.method != "POST":
        return redirect("view_phenotype_post")

    form = Phenotype_Post_Form(
        request.POST,
        instance=phenotype_post
    )

    if form.is_valid():
        form.save()
        messages.success(
            request,
            "Phenotype (Post) updated successfully."
        )
    else:
        messages.error(
            request,
            "Failed to update Phenotype (Post)."
        )
        print(form.errors)

    return redirect("view_phenotype_post")





@login_required(login_url="/login/")
def delete_phenotype_post(request, pk):

    phenotype_post = get_object_or_404(Phenotype_Post, pk=pk)

    phenotype_post.delete()

    messages.success(
        request,
        "Phenotype (Post) deleted successfully."
    )

    return redirect("view_phenotype_post")

################ Recommendations


@login_required(login_url="/login/")
def add_recommendation_item(request):

    if request.method != "POST":
        return redirect("/settings/?tab=recommendation_tab")

    form = Recco_item_Form(request.POST)

    if form.is_valid():
        form.save()
        messages.success(request, "Recommendation item added successfully.")
    else:
        messages.error(request, "Failed to add recommendation item.")
        print(form.errors)

    return redirect("/settings/?tab=recommendation_tab")




@login_required(login_url="/login/")
def upload_recommendation_items(request):

    if request.method != "POST":
        return redirect("/settings/?tab=recommendation_tab")

    reco_desc_upload = request.FILES.get("File_reco_desc")

    if not reco_desc_upload:
        messages.error(request, "No file selected for upload.")
        return redirect("/settings/?tab=recommendation_tab")

    # optional: keep upload record
    Reco_item_upload.objects.create(File_reco_desc=reco_desc_upload)

    try:
        if reco_desc_upload.name.endswith(".csv"):
            df = pd.read_csv(reco_desc_upload)
        else:
            df = pd.read_excel(reco_desc_upload)

        df.columns = [c.strip() for c in df.columns]

        required_cols = {"RecoCode", "Description"}
        if not required_cols.issubset(df.columns):
            messages.error(
                request,
                "File must contain columns: RecoCode, Description"
            )
            return redirect("/settings/?tab=recommendation_tab")

        # overwrite existing
        Recommendation_items.objects.all().delete()

        objs = [
            Recommendation_items(
                RecoCode=str(row["RecoCode"]).strip(),
                Description=str(row["Description"]).strip()
            )
            for _, row in df.iterrows()
            if pd.notna(row["RecoCode"])
        ]

        Recommendation_items.objects.bulk_create(objs)

        messages.success(
            request,
            f"{len(objs)} recommendation items uploaded successfully."
        )

    except Exception as e:
        messages.error(request, f"Upload failed: {e}")

    return redirect("/settings/?tab=recommendation_tab")



@login_required(login_url="/login/")
def view_recommendation_items(request):

    q = request.GET.get("q", "").strip()

    recommendation_items = Recommendation_items.objects.all()

    if q:
        recommendation_items = recommendation_items.filter(
            RecoCode__icontains=q
        ) | recommendation_items.filter(
            Description__icontains=q
        )

    recommendation_items = recommendation_items.order_by("RecoCode")

    paginator = Paginator(recommendation_items, 25)  # rows per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "q": q,
    }

    return render(
        request,
        "home/Recommendation_View.html",
        context
    )



def edit_recommendation_item(request, pk):

    item = get_object_or_404(Recommendation_items, pk=pk)

    if request.method == "POST":
        form = Recco_item_Form(request.POST, instance=item)

        if form.is_valid():
            form.save()
            messages.success(request, "Recommendation item updated successfully.")
            return redirect("view_recommendation_items")
        else:
            messages.error(request, "Failed to update recommendation item.")
            print(form.errors)
    else:
        form = Recco_item_Form(instance=item)

    context = {
        "form": form,
        "object": item,
        "editing": True,
    }

    return render(
        request,
        "home/Recommendation_Edit.html",
        context
    )


@login_required(login_url="/login/")
def delete_recommendation_item(request, pk):

    item = get_object_or_404(Recommendation_items, pk=pk)

    if request.method == "POST":
        item.delete()
        messages.success(request, "Recommendation item deleted successfully.")
        return redirect("view_recommendation_items")

    # fallback for GET (confirm via JS already)
    item.delete()
    messages.success(request, "Recommendation item deleted successfully.")
    return redirect("view_recommendation_items")




@require_GET
def get_recommendation_description(request):

    reco_code = request.GET.get("reco_code")

    if not reco_code:
        return JsonResponse({"description": ""})

    try:
        reco = Recommendation_items.objects.get(RecoCode=reco_code)
        return JsonResponse({"description": reco.Description})
    except Recommendation_items.DoesNotExist:
        return JsonResponse({"description": ""})



################  PROJECTS

@login_required
def projects_page(request):

    active_tab = request.GET.get("tab", "wgs_classification")

    referred_list = (
        Referred_Data.objects
        .all()
        .order_by("-Date_Modified", "-id")
    )

    context = {
        "active_tab": active_tab,
        "referred_list": referred_list,
        "editing": False,
    }

    return render(
        request,
        "projects/Projects.html",
        context
    )



@login_required
def update_wgs_classification_inline(request, accession_no):

    if request.method != "POST":
        return redirect("/projects/?tab=wgs_classification")

    referred = get_object_or_404(
        Referred_Data,
        AccessionNo=accession_no
    )

    classification, _ = Classification_Table.objects.get_or_create(
        Class_idNumReferred=referred,
        defaults={"Class_AccessionNo": referred.AccessionNo}
    )

    classification.Class_Chk_Emerging = "Class_Chk_Emerging" in request.POST
    classification.Class_Chk_Satscan = "Class_Chk_Satscan" in request.POST
    classification.Class_Chk_Serotyping = "Class_Chk_Serotyping" in request.POST
    classification.Class_Chk_GHRU_all = "Class_Chk_GHRU_all" in request.POST
    classification.Class_Chk_GHRU_Neo = "Class_Chk_GHRU_Neo" in request.POST
    classification.Class_Chk_Tricycle = "Class_Chk_Tricycle" in request.POST

    classification.save()

    messages.success(
        request,
        f"WGS classification updated for {accession_no}"
    )

    return redirect("/projects/?tab=wgs_classification")



@login_required
def wgs_classification_view(request, accession_no):

    # Always resolve referred data first
    referred = get_object_or_404(
        Referred_Data,
        AccessionNo=accession_no
    )

    # Create or fetch classification row
    classification, created = Classification_Table.objects.get_or_create(
        Class_idNumReferred=referred,
        defaults={
            "Class_AccessionNo": referred.AccessionNo
        }
    )

    if request.method == "POST":
        form = Classification_Form(
            request.POST,
            instance=classification
        )

        if form.is_valid():
            try:
                with transaction.atomic():
                    obj = form.save(commit=False)
                    obj.Class_AccessionNo = referred.AccessionNo
                    obj.Class_idNumReferred = referred
                    obj.save()

                messages.success(
                    request,
                    "WGS classification updated successfully."
                )
                return redirect("projects_page")

            except Exception as e:
                messages.error(
                    request,
                    f"Error saving classification: {e}"
                )

        else:
            messages.error(
                request,
                "Failed to update WGS classification."
            )
    else:
        form = Classification_Form(instance=classification)

    return render(
        request,
        "projects/Classification.html",
        {
            "form": form,
            "referred": referred,
            "editing": True,
        }
    )