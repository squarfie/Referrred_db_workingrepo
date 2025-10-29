
from collections import defaultdict
import datetime
from io import TextIOWrapper
import io
import re
from django.db import transaction
import csv
from django.db.models import Q, F, Func
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from .forms import *
from apps.home.forms import *
from apps.home_final.forms import *
import pandas as pd
from apps.home.models import *
from apps.home_final.models import *
from .models import *
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.contrib import messages
import os
from django.core.paginator import Paginator
import re
from .utils import format_accession
from django.contrib.auth.decorators import login_required
from django.conf import settings
from datetime import datetime
from django.utils.dateparse import parse_date
from django.template.loader import render_to_string
# helper to read uploaded file (csv or excel)
def read_uploaded_file(uploaded_file):
    import pandas as pd

    filename = uploaded_file.name.lower()
    if filename.endswith('.csv'):
        return pd.read_csv(uploaded_file)
    elif filename.endswith(('.xls', '.xlsx')):
        return pd.read_excel(uploaded_file)
    else:
        raise ValueError("Unsupported file format. Please upload a CSV or Excel file.")
    

# handles the connection of WGS project to referred data
@login_required
def upload_wgs_view(request):

    if request.method == "POST":
        form = WGSProjectForm(request.POST)
        fastq_form = FastqUploadForm(request.POST, request.FILES)
        gambit_form = GambitUploadForm(request.POST, request.FILES)
        mlst_form = MlstUploadForm(request.POST, request.FILES)
        checkm2_form = Checkm2UploadForm(request.POST, request.FILES)
        assembly_form = AssemblyUploadForm(request.POST, request.FILES)
        amrfinder_form = AmrUploadForm(request.POST, request.FILES)
        referred_form = FinalDataUploadForm(request.POST, request.FILES)
        antibiotic_form = FinalAntibioticUploadForm(request.POST, request.FILES)

        final_data_uploaded = False
        final_antibiotic_uploaded = False
        project_saved = False
        fastq_uploaded = False
        gambit_uploaded = False
        mlst_uploaded = False
        checkm2_uploaded = False
        assembly_uploaded = False
        amrfinder_uploaded = False
        
         # Final Data upload
        if referred_form.is_valid():
            form.save()
            final_data_uploaded = True

         # Final Data upload
        if antibiotic_form.is_valid():
            form.save()
            final_antibiotic_uploaded = True

        # WGS Project
        if form.is_valid():
            form.save()
            project_saved = True

        # FASTQ Upload
        if fastq_form.is_valid():
            fastq_form.save()
            fastq_uploaded = True

        # Gambit Upload
        if gambit_form.is_valid():
            gambit_form.save()
            gambit_uploaded = True
        
        # Mlst Upload
        if mlst_form.is_valid():
            mlst_form.save()
            mlst_uploaded = True
        
        # Checkm2 Upload
        if checkm2_form.is_valid():
            checkm2_form.save()
            checkm2_uploaded = True
        
        # Assembly scan Upload
        if assembly_form.is_valid():
            assembly_form.save()
            assembly_uploaded = True

        
        # Amrfinder Upload
        if amrfinder_form.is_valid():
            amrfinder_form.save()
            amrfinder_uploaded = True

        # If any form worked, refresh
        if project_saved or final_data_uploaded or final_antibiotic_uploaded or fastq_uploaded or gambit_uploaded or mlst_uploaded or checkm2_uploaded or assembly_uploaded or amrfinder_uploaded:
            return redirect("upload_wgs_view")

    else:
        form = WGSProjectForm()
        referred_form = FinalDataUploadForm()
        antibiotic_form = FinalAntibioticUploadForm()
        fastq_form = FastqUploadForm()
        gambit_form = GambitUploadForm()
        mlst_form = MlstUploadForm()
        checkm2_form = Checkm2UploadForm()
        assembly_form = AssemblyUploadForm()
        amrfinder_form = AmrUploadForm()

    return render(
        request,
        "wgs_app/Add_wgs.html",
        {
            "form": form,
            "referred_form": referred_form,
            "antibiotic_form": antibiotic_form,
            "fastq_form": fastq_form,
            "gambit_form": gambit_form,
            "mlst_form": mlst_form,
            "checkm2_form": checkm2_form,
            "assembly_form": assembly_form,
            "amrfinder_form": amrfinder_form,
            "editing": False,
        },
    )


# @login_required
# def show_wgs_projects(request):
#     wgs_projects = WGS_Project.objects.all().order_by("id")  # optional ordering

#     total_records = WGS_Project.objects.count()
#      # Paginate the queryset to display 20 records per page
#     paginator = Paginator(wgs_projects, 20)
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)

#     # Render the template with paginated data
#     return render(
#         request,
#         "wgs_app/show_wgs_proj.html",
#         {"page_obj": page_obj,
#          "total_records": total_records,
#          },  # only send page_obj
#     )


@login_required
def show_wgs_projects(request):
    # Get all Referred_Data that have associated WGS projects
    referred_with_wgs = Final_Data.objects.filter(
        f_AccessionNo__isnull=False
    ).distinct()
    
    context = {
        'referred_list': referred_with_wgs,
    }
    return render(request, 'wgs_app/view_match.html', context)


@login_required
def delete_wgs(request, pk):
    wgs_item = get_object_or_404(WGS_Project, pk=pk)

    if request.method == "POST":
        wgs_item.delete()
        messages.success(request, f"Record {wgs_item.Ref_Accession} deleted successfully!")
        return redirect('show_wgs_projects')  # <-- Correct URL name

    messages.error(request, "Invalid request for deletion.")
    return redirect('show_wgs_projects')  # <-- Correct URL name


############## FASTQ

@login_required
def upload_fastq(request):
    form = WGSProjectForm()
    fastq_form = FastqUploadForm()
    editing = False  

    if request.method == "POST" and request.FILES.get("fastqfile"):
        fastq_form = FastqUploadForm(request.POST, request.FILES)
        if fastq_form.is_valid():
            try:
                upload = fastq_form.save()
                df = read_uploaded_file(upload.fastqfile)
                df.columns = df.columns.str.strip().str.replace(".", "", regex=False)
            except Exception as e:
                messages.error(request, f"Error processing FASTQ file: {e}")
                return render(request, "wgs_app/Add_wgs.html", {
                    "form": form,
                    "fastq_form": fastq_form,
                    "gambit_form": GambitUploadForm(),
                    "mlst_form": MlstUploadForm(),
                    "checkm2_form": Checkm2UploadForm(),
                    "amrfinder_form": AmrUploadForm(),
                    "assembly_form": AssemblyUploadForm(),
                    "referred_form": FinalDataUploadForm(),
                    "antibiotic_form": FinalAntibioticUploadForm(),
                    "editing": editing,
                })

            # Load all valid site codes from the SiteData table
            site_codes = set(SiteData.objects.values_list("SiteCode", flat=True))

            def format_fastq_accession(raw_name: str, site_codes: set) -> str:
                """
                Returns formatted accession only if BOTH 'ARS' and a valid SiteCode from SiteData exist in the name.
                """
                if not raw_name:
                    return ""

                name = raw_name.strip().upper() # normalize case

                # Reject invalid patterns
                if "UTPR" in name or "UTPN" in name or "BL" in name:
                    return ""
                
                # ✅ Must contain 'ARS' - if not, return empty immediately
                if "ARS" not in name:
                    return ""

                # ✅ Find if any valid SiteCode from DB exists in the sample name
                # Use word boundaries to match complete site codes only
                valid_code = None
                for code in site_codes:
                    code_upper = code.upper()
                    # Look for the site code with word boundaries (hyphens, start/end of string)
                    # Pattern: site code must be followed by a hyphen and digits
                    pattern = rf"[-]?{re.escape(code_upper)}[-]?\d+"
                    if re.search(pattern, name):
                        valid_code = code_upper
                        break

                # No valid site code found → blank
                if not valid_code:
                    return ""

                # Extract prefix that includes ARS (e.g., "18ARS")
                prefix_match = re.search(r"(\d*ARS)", name)
                prefix = prefix_match.group(1) if prefix_match else "ARS"

                # Extract numeric digits after the site code (e.g., 0055)
                num_match = re.search(rf"{re.escape(valid_code)}[-]?(\d+)", name)
                digits = num_match.group(1) if num_match else ""

                return f"{prefix}_{valid_code}{digits}" if digits else ""

            # === Loop through rows ===
            for _, row in df.iterrows():
                sample_name = str(row.get("sample", "")).strip()
                fastq_accession = format_fastq_accession(sample_name, site_codes)

                # if invalid accession keep blank
                if not fastq_accession: 
                    fastq_accession = ""

                referred_obj = None
                if fastq_accession:
                    referred_obj = Final_Data.objects.filter(
                        f_AccessionNo=fastq_accession
                    ).first()

                # Allow multiple WGS_Project per accession
                connect_project = WGS_Project.objects.create(
                    Ref_Accession=referred_obj if referred_obj else None,
                    WGS_GambitSummary=False,
                    WGS_FastqSummary=False,
                    WGS_MlstSummary=False,
                    WGS_Checkm2Summary=False,
                    WGS_AssemblySummary=False,
                    WGS_AmrfinderSummary=False,
                )

                connect_project.WGS_FastQ_Acc = fastq_accession
                connect_project.WGS_FastqSummary = (
                    bool(fastq_accession)
                    and bool(connect_project.Ref_Accession)
                    and fastq_accession == getattr(connect_project.Ref_Accession, "f_AccessionNo", None)
                )
                connect_project.save()

                # ✅ Always create summary, even if accession is blank
                FastqSummary.objects.create(
                    FastQ_Accession=fastq_accession,
                    fastq_project=connect_project,
                    sample=sample_name,
                    fastp_version=row.get("fastp_version", ""),
                    sequencing=row.get("sequencing", ""),
                    before_total_reads=row.get("before_total_reads", ""),
                    before_total_bases=row.get("before_total_bases", ""),
                    before_q20_rate=row.get("before_q20_rate", ""),
                    before_q30_rate=row.get("before_q30_rate", ""),
                    before_read1_mean_len=row.get("before_read1_mean_len", ""),
                    before_read2_mean_len=row.get("before_read2_mean_len", ""),
                    before_gc_content=row.get("before_gc_content", ""),
                    after_total_reads=row.get("after_total_reads", ""),
                    after_total_bases=row.get("after_total_bases", ""),
                    after_q20_rate=row.get("after_q20_rate", ""),
                    after_q30_rate=row.get("after_q30_rate", ""),
                    after_read1_mean_len=row.get("after_read1_mean_len", ""),
                    after_read2_mean_len=row.get("after_read2_mean_len", ""),
                    after_gc_content=row.get("after_gc_content", ""),
                    passed_filter_reads=row.get("passed_filter_reads", ""),
                    low_quality_reads=row.get("low_quality_reads", ""),
                    too_many_N_reads=row.get("too_many_N_reads", ""),
                    too_short_reads=row.get("too_short_reads", ""),
                    too_long_reads=row.get("too_long_reads", ""),
                    combined_total_bp=row.get("combined_total_bp", ""),
                    combined_qual_mean=row.get("combined_qual_mean", ""),
                    post_trim_q30_rate=row.get("post_trim_q30_rate", ""),
                    post_trim_q30_pct=row.get("post_trim_q30_pct", ""),
                    post_trim_q20_rate=row.get("post_trim_q20_rate", ""),
                    post_trim_q20_pct=row.get("post_trim_q20_pct", ""),
                    after_gc_pct=row.get("after_gc_pct", ""),
                    duplication_rate=row.get("duplication_rate", ""),
                    read_length_mean_after=row.get("read_length_mean_after", ""),
                    adapter_trimmed_reads=row.get("adapter_trimmed_reads", ""),
                    adapter_trimmed_reads_pct=row.get("adapter_trimmed_reads_pct", ""),
                    adapter_trimmed_bases=row.get("adapter_trimmed_bases", ""),
                    adapter_trimmed_bases_pct=row.get("adapter_trimmed_bases_pct", ""),
                    insert_size_peak=row.get("insert_size_peak", ""),
                    insert_size_unknown=row.get("insert_size_unknown", ""),
                    overrep_r1_count=row.get("overrep_r1_count", ""),
                    overrep_r2_count=row.get("overrep_r2_count", ""),
                    ns_overrep_none=row.get("ns_overrep_none", ""),
                    qc_q30_pass=row.get("qc_q30_pass", ""),
                    q30_status=row.get("q30_status", ""),
                    q20_status=row.get("q20_status", ""),
                    adapter_reads_status=row.get("adapter_reads_status", ""),
                    adapter_bases_status=row.get("adapter_bases_status", ""),
                    duplication_status=row.get("duplication_status", ""),
                    readlen_status=row.get("readlen_status", ""),
                    ns_overrep_status=row.get("ns_overrep_status", ""),
                    raw_reads_qc_summary=row.get("raw_reads_qc_summary", ""),
                )

            messages.success(request, "FastQ records updated successfully.")
            return redirect("show_fastq")

    return render(request, "wgs_app/Add_wgs.html", {
        "form": form,
        "fastq_form": fastq_form,
        "gambit_form": GambitUploadForm(),
        "mlst_form": MlstUploadForm(),
        "checkm2_form": Checkm2UploadForm(),
        "amrfinder_form": AmrUploadForm(),
        "assembly_form": AssemblyUploadForm(),
        "referred_form": FinalDataUploadForm(),
        "antibiotic_form": FinalAntibioticUploadForm(),
        "editing": editing,
    })


# @login_required
# def show_fastq(request):
#     fastq_summaries = FastqSummary.objects.all().order_by("id")  # optional ordering

#     total_records = FastqSummary.objects.count()
#      # Paginate the queryset to display 20 records per page
#     paginator = Paginator(fastq_summaries, 20)
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)

#     # Render the template with paginated data
#     return render(
#         request,
#         "wgs_app/show_fastq.html",
#         {"page_obj": page_obj,
#          "total_records": total_records,
#          },  # only send page_obj
#     )

@login_required
def show_fastq(request):
    fastq_summaries = FastqSummary.objects.all().order_by('-Date_uploaded_f')
    upload_dates = (
        FastqSummary.objects.exclude(Date_uploaded_f__isnull=True)
        .values_list('Date_uploaded_f', flat=True)
        .distinct()
        .order_by('-Date_uploaded_f')
    )

    total_records = FastqSummary.objects.count()
     # Paginate the queryset to display 20 records per page
    paginator = Paginator(fastq_summaries, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "wgs_app/show_fastq.html", {
        "page_obj": page_obj,
        "upload_dates": upload_dates,
        "total_records": total_records,
    })



# @login_required
# def delete_fastq(request, pk):
#     fastq_item = get_object_or_404(FastqSummary, pk=pk)

#     if request.method == "POST":
#         fastq_item.delete()
#         messages.success(request, f"Record {fastq_item.sample} deleted successfully!")
#         return redirect('show_fastq')  # <-- Correct URL name

#     messages.error(request, "Invalid request for deletion.")
#     return redirect('show_fastq')  # <-- Correct URL name


@login_required
def delete_fastq(request, pk):
    fastq_item = get_object_or_404(FastqSummary, pk=pk)

    if request.method == "POST":
        # Before deleting, clear related field in WGS_Project
        WGS_Project.objects.filter(WGS_FastQ_Acc=fastq_item.FastQ_Accession).update(
            WGS_FastQ_Acc="",
            WGS_FastqSummary=False
        )
  
        fastq_item.delete()
        messages.success(request, f"Record {fastq_item.sample} deleted successfully!")
        return redirect('show_fastq')

    messages.error(request, "Invalid request for deletion.")
    return redirect('show_fastq')



# def delete_all_fastq(request):
#     FastqSummary.objects.all().delete()
#     messages.success(request, "FastQ Records have been deleted successfully.")
#     return redirect('show_fastq')  # Redirect to the table view


@login_required
def delete_all_fastq(request):
    """
    Safely delete all FastQ records but preserve WGS_Project links
    for other data types (MLST, CheckM2, Gambit, etc.).
    """
    # Step 1: Clear only FastQ fields in existing WGS_Project records
    updated_count = WGS_Project.objects.filter(
        WGS_FastQ_Acc__isnull=False
    ).exclude(WGS_FastQ_Acc="").update(
        WGS_FastQ_Acc="",
        WGS_FastqSummary=False
    )

    # Step 2: Delete all FastQ summary data
    FastqSummary.objects.all().delete()

    # Step 3: Show success message
    messages.success(
        request,
        f"All FastQ records deleted successfully, and {updated_count} WGS Project(s) were unlinked from FastQ data."
    )

    return redirect("show_fastq")


@login_required
def delete_fastq_by_date(request):
    if request.method == "POST":
        upload_date_str = request.POST.get("upload_date")
        print("🕒 Received upload_date_str:", upload_date_str)

        if not upload_date_str:
            messages.error(request, "Please select an upload date to delete.")
            return redirect("show_fastq")

        # Use Django’s date parser
        upload_date = parse_date(upload_date_str)

        if not upload_date:
            messages.error(request, f"Invalid date format: {upload_date_str}")
            return redirect("show_fastq")

        deleted_count, _ = FastqSummary.objects.filter(Date_uploaded_f=upload_date).delete()
        messages.success(request, f"✅ Deleted {deleted_count} FASTQ records uploaded on {upload_date}.")
        return redirect("show_fastq")

    messages.error(request, "Invalid request method.")
    return redirect("show_fastq")


#########   Gambit
@login_required
def upload_gambit(request):
    form = WGSProjectForm()
    gambit_form = GambitUploadForm()
    editing = False  

    if request.method == "POST" and request.FILES.get("GambitFile"):
        gambit_form = GambitUploadForm(request.POST, request.FILES)
        if gambit_form.is_valid():
            try:
                upload = gambit_form.save()
                df = read_uploaded_file(upload.GambitFile)
                df.columns = df.columns.str.strip().str.replace(".", "_", regex=False)
            except Exception as e:
                messages.error(request, f"Error processing FASTQ file: {e}")
                return render(request, "wgs_app/Add_wgs.html", {
                    "form": form,
                    "fastq_form": FastqUploadForm(),
                    "gambit_form": gambit_form,
                    "mlst_form": MlstUploadForm(),
                    "checkm2_form": Checkm2UploadForm(),
                    "amrfinder_form": AmrUploadForm(),
                    "assembly_form": AssemblyUploadForm(),
                    "referred_form": FinalDataUploadForm(),
                    "antibiotic_form": FinalAntibioticUploadForm(),
                    "editing": editing,
                })

            site_codes = set(SiteData.objects.values_list("SiteCode", flat=True))
                # helper to build accession
            def format_gambit_accession(raw_name: str, site_codes: set) -> str:
                """
                Returns formatted accession only if BOTH 'ARS' and a valid SiteCode from SiteData exist in the name.
                """
                if not raw_name:
                    return ""

                name = raw_name.strip().upper() # normalize case

                # Reject invalid patterns
                if "UTPR" in name or "UTPN" in name or "BL" in name:
                    return ""
                
                # ✅ Must contain 'ARS' - if not, return empty immediately
                if "ARS" not in name:
                    return ""

                # ✅ Find if any valid SiteCode from DB exists in the sample name
                # Use word boundaries to match complete site codes only
                valid_code = None
                for code in site_codes:
                    code_upper = code.upper()
                    # Look for the site code with word boundaries (hyphens, start/end of string)
                    # Pattern: site code must be followed by a hyphen and digits
                    pattern = rf"[-]?{re.escape(code_upper)}[-]?\d+"
                    if re.search(pattern, name):
                        valid_code = code_upper
                        break

                # No valid site code found → blank
                if not valid_code:
                    return ""

                # ✅ Extract prefix that includes ARS (e.g., "18ARS")
                prefix_match = re.search(r"(\d*ARS)", name)
                prefix = prefix_match.group(1) if prefix_match else "ARS"

                # ✅ Extract numeric digits after the site code (e.g., 0055)
                num_match = re.search(rf"{re.escape(valid_code)}[-]?(\d+)", name)
                digits = num_match.group(1) if num_match else ""

                return f"{prefix}_{valid_code}{digits}" if digits else ""


            for _, row in df.iterrows():
                sample_name = str(row.get("sample", "")).strip()
                gambit_accession = format_gambit_accession(sample_name, site_codes)

                # if invalid accession keep blank
                if not gambit_accession: 
                    gambit_accession = ""

                # try to find Referred_Data with this accession
                referred_obj = Final_Data.objects.filter(
                    f_AccessionNo=gambit_accession
                ).first()

              # Allow multiple WGS_Project per accession
                connect_project = WGS_Project.objects.create(
                    Ref_Accession=referred_obj if referred_obj else None,
                    WGS_GambitSummary=False,
                    WGS_FastqSummary=False,
                    WGS_MlstSummary=False,
                    WGS_Checkm2Summary=False,
                    WGS_AssemblySummary=False,
                    WGS_AmrfinderSummary=False,
                )

                connect_project.WGS_FastQ_Acc = gambit_accession
                connect_project.WGS_FastqSummary = (
                    bool(gambit_accession)
                    and bool(connect_project.Ref_Accession)
                    and gambit_accession == getattr(connect_project.Ref_Accession, "f_AccessionNo", None)
                )
                connect_project.save()
                # update or create Gambit record
                Gambit.objects.create(
                    Gambit_Accession=gambit_accession,
                    gambit_project=connect_project,
                    sample=row.get("sample", sample_name),
                    predicted_name=row.get("predicted_name", ""),
                    predicted_rank=row.get("predicted_rank", ""),
                    predicted_ncbi_id=row.get("predicted_ncbi_id", ""),
                    predicted_threshold=row.get("predicted_threshold", ""),
                    closest_distance=row.get("closest_distance", ""),
                    closest_description=row.get("closest_description", ""),
                    next_name=row.get("next_name", ""),
                    next_rank=row.get("next_rank", ""),
                    next_ncbi_id=row.get("next_ncbi_id", ""),
                    next_threshold=row.get("next_threshold", ""),
                )


            messages.success(request, "Gambit records updated successfully.")
            return redirect("show_gambit")

    return render(request, "wgs_app/Add_wgs.html", {
        "form": form,
        "fastq_form": FastqUploadForm(),
        "gambit_form": gambit_form,
        "mlst_form": MlstUploadForm(),
        "checkm2_form": Checkm2UploadForm(),
        "assembly_form": AssemblyUploadForm(),
        "amrfinder_form": AmrUploadForm(),
        "referred_form": FinalDataUploadForm(),
        "antibiotic_form": FinalAntibioticUploadForm(),
        "editing": editing,
    })




@login_required
def show_gambit(request):
    gambit_summaries = Gambit.objects.all().order_by('-Date_uploaded_g')
    upload_dates = (
        Gambit.objects.exclude(Date_uploaded_g__isnull=True)
        .values_list('Date_uploaded_g', flat=True)
        .distinct()
        .order_by('-Date_uploaded_g')
    )

    total_records = Gambit.objects.count()
     # Paginate the queryset to display 20 records per page
    paginator = Paginator(gambit_summaries, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "wgs_app/show_gambit.html", {
        "page_obj": page_obj,
        "upload_dates": upload_dates,
        "total_records": total_records,
    })




@login_required
def delete_gambit(request, pk):
    gambit_item = get_object_or_404(Gambit, pk=pk)

    if request.method == "POST":
        # Before deleting, clear related field in WGS_Project
        WGS_Project.objects.filter(WGS_FastQ_Acc=gambit_item.Gambit_Accession).update(
            WGS_FastQ_Acc="",
            WGS_FastqSummary=False
        )

        gambit_item.delete()
        messages.success(request, f"Record {gambit_item.sample} deleted successfully!")
        return redirect('show_gambit')

    messages.error(request, "Invalid request for deletion.")
    return redirect('show_gambit')


# @login_required
# def delete_all_gambit(request):
#     Gambit.objects.all().delete()
#     messages.success(request, "Gambit Records have been deleted successfully.")
#     return redirect('show_gambit')  # Redirect to the table view



@login_required
def delete_all_gambit(request):
    """
    Safely delete all Gambit records but preserve WGS_Project links
    for other WGS data types (FastQ, MLST, CheckM2, Assembly, AMRFinder, etc.).
    """
    # Step 1: Clear only Gambit fields in existing WGS_Project records
    updated_count = WGS_Project.objects.filter(
        WGS_Gambit_Acc__isnull=False
    ).exclude(WGS_Gambit_Acc="").update(
        WGS_Gambit_Acc="",
        WGS_GambitSummary=False
    )

    # Step 2: Delete all Gambit summary data
    Gambit.objects.all().delete()

    # Step 3: Display success message
    messages.success(
        request,
        f"All Gambit records deleted successfully, and {updated_count} WGS Project(s) were unlinked from Gambit data."
    )

    return redirect("show_gambit")




@login_required
def delete_gambit_by_date(request):
    if request.method == "POST":
        upload_date_str = request.POST.get("upload_date")
        print("🕒 Received upload_date_str:", upload_date_str)

        if not upload_date_str:
            messages.error(request, "Please select an upload date to delete.")
            return redirect("show_gambit")

        # Use Django’s date parser
        upload_date = parse_date(upload_date_str)

        if not upload_date:
            messages.error(request, f"Invalid date format: {upload_date_str}")
            return redirect("show_gambit")

        deleted_count, _ = Gambit.objects.filter(Date_uploaded_f=upload_date).delete()
        messages.success(request, f"✅ Deleted {deleted_count} Gambit records uploaded on {upload_date}.")
        return redirect("show_gambit")

    messages.error(request, "Invalid request method.")
    return redirect("show_gambit")


#########   MLST
@login_required
def upload_mlst(request):
    form = WGSProjectForm()
    mlst_form = MlstUploadForm()
    editing = False  

    if request.method == "POST" and request.FILES.get("Mlstfile"):
        mlst_form = MlstUploadForm(request.POST, request.FILES)
        try:
            upload = mlst_form.save()
            df = read_uploaded_file(upload.Mlstfile)
            df.columns = df.columns.str.strip().str.replace(".", "", regex=False)
        except Exception as e:
            messages.error(request, f"Error processing MLST file: {e}")
            return render(request, "wgs_app/Add_wgs.html", {
                "form": form,
                "fastq_form": FastqUploadForm(),
                "gambit_form": GambitUploadForm(),
                "mlst_form": mlst_form,
                "checkm2_form": Checkm2UploadForm(),
                "amrfinder_form": AmrUploadForm(),
                "assembly_form": AssemblyUploadForm(),
                "referred_form": FinalDataUploadForm(),
                "antibiotic_form": FinalAntibioticUploadForm(),
                "editing": editing,
            })

        # ✅ Load all valid site codes from the SiteData table
        site_codes = set(SiteData.objects.values_list("SiteCode", flat=True))

        # === Helper: build accession from file name ===
        def format_mlst_accession(raw_name: str, site_codes: set) -> str:
            if not raw_name:
                return ""

            base_noext = os.path.splitext(os.path.basename(raw_name))[0].strip()

            # Must contain 'ARS' to be valid
            if "ARS" not in base_noext:
                return ""

            parts = re.split(r"[-_]", base_noext)
            if not parts:
                return ""

            prefix = parts[0]

            # Look for SITE#### pattern where SITE is valid
            for part in parts[1:]:
                match = re.match(r"^([A-Za-z]{2,6})(\d+)$", part)
                if match:
                    letters, digits = match.group(1).upper(), match.group(2)
                    if letters in site_codes:
                        return f"{prefix}_{letters}{digits}"

            # 2Look for a separate valid site code, then grab digits from next part
            for i in range(1, len(parts)):
                part = parts[i]
                if part.upper() in site_codes:
                    letters = part.upper()
                    digits = ""

                    if i + 1 < len(parts):
                        next_part = parts[i + 1]
                        next_match = re.match(r"^([A-Za-z]{2,6})(\d+)$", next_part)
                        if next_match:
                            digits = next_match.group(2)
                        else:
                            digit_match = re.search(r"(\d+)", next_part)
                            if digit_match:
                                digits = digit_match.group(1)

                    # fallback — digits inside current part
                    if not digits:
                        digit_match2 = re.search(r"(\d+)", part)
                        if digit_match2:
                            digits = digit_match2.group(1)

                    return f"{prefix}_{letters}{digits}" if digits else f"{prefix}_{letters}"

            return ""

        print("✅ Total rows in DataFrame:", len(df))

        # === Loop through rows ===
        for _, row in df.iterrows():
            full_path = str(row.get("name", "")).strip()
            mlst_accession = format_mlst_accession(full_path, site_codes)

            # Find Referred_Data (optional)
            referred_obj = (
                Final_Data.objects.filter(f_AccessionNo=mlst_accession).first()
                if mlst_accession else None
            )

             # Allow multiple WGS_Project per accession
            connect_project = WGS_Project.objects.create(
                    Ref_Accession=referred_obj if referred_obj else None,
                    WGS_GambitSummary=False,
                    WGS_FastqSummary=False,
                    WGS_MlstSummary=False,
                    WGS_Checkm2Summary=False,
                    WGS_AssemblySummary=False,
                    WGS_AmrfinderSummary=False,
                )

            connect_project.WGS_Mlst_Acc = mlst_accession
            connect_project.WGS_MlstSummary = (
                    bool(mlst_accession)
                    and bool(connect_project.Ref_Accession)
                    and mlst_accession == getattr(connect_project.Ref_Accession, "f_AccessionNo", None)
                )
            connect_project.save()

            # Always create new MLST record
            Mlst.objects.create(
                Mlst_Accession=mlst_accession,
                mlst_project=connect_project,
                name=row.get("name", ""),
                scheme=row.get("scheme", ""),
                mlst=row.get("MLST", ""),
                allele1=row.get("allele1", ""),
                allele2=row.get("allele2", ""),
                allele3=row.get("allele3", ""),
                allele4=row.get("allele4", ""),
                allele5=row.get("allele5", ""),
                allele6=row.get("allele6", ""),
                allele7=row.get("allele7", "")
                
            )

        messages.success(request, "MLST records updated successfully.")
        return redirect("show_mlst")

    # === GET request fallback ===
    return render(request, "wgs_app/Add_wgs.html", {
        "form": form,
        "fastq_form": FastqUploadForm(),
        "gambit_form": GambitUploadForm(),
        "mlst_form": mlst_form,
        "checkm2_form": Checkm2UploadForm(),
        "amrfinder_form": AmrUploadForm(),
        "assembly_form": AssemblyUploadForm(),
        "referred_form": FinalDataUploadForm(),
        "antibiotic_form": FinalAntibioticUploadForm(),
        "editing": editing
    })



@login_required
def show_mlst(request):
    mlst_summaries = Mlst.objects.all().order_by('-Date_uploaded_m')
    upload_dates = (
        Mlst.objects.exclude(Date_uploaded_m__isnull=True)
        .values_list('Date_uploaded_m', flat=True)
        .distinct()
        .order_by('-Date_uploaded_m')
    )

    total_records = Mlst.objects.count()
     # Paginate the queryset to display 20 records per page
    paginator = Paginator(mlst_summaries, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "wgs_app/show_mlst.html", {
        "page_obj": page_obj,
        "upload_dates": upload_dates,
        "total_records": total_records,
    })




# @login_required
# def delete_mlst(request, pk):
#     mlst_item = get_object_or_404(Mlst, pk=pk)

#     if request.method == "POST":
#         mlst_item.delete()
#         messages.success(request, f"Record {mlst_item.sample} deleted successfully!")
#         return redirect('show_mlst')  # <-- Correct URL name

#     messages.error(request, "Invalid request for deletion.")
#     return redirect('show_mlst')  # <-- Correct URL name


@login_required
def delete_mlst(request, pk):
    mlst_item = get_object_or_404(Mlst, pk=pk)

    if request.method == "POST":
        # Before deleting, clear related field in WGS_Project
        WGS_Project.objects.filter(WGS_Mlst_Acc=mlst_item.Mlst_Accession).update(
            WGS_Mlst_Acc="",
            WGS_MlstSummary=False
        )

        mlst_item.delete()
        messages.success(request, f"Record {mlst_item.sample} deleted successfully!")
        return redirect('show_mlst')

    messages.error(request, "Invalid request for deletion.")
    return redirect('show_mlst')



# @login_required
# def delete_all_mlst(request):
#     Mlst.objects.all().delete()
#     messages.success(request, "Mlst Records have been deleted successfully.")
#     return redirect('show_mlst')  # Redirect to the table view


@login_required
def delete_all_mlst(request):
    """
    Safely delete all MLST records but preserve WGS_Project links
    for other WGS data types (FastQ, CheckM2, Assembly, Gambit, AMRFinder, etc.).
    """
    # Step 1: Clear only MLST fields in existing WGS_Project records
    updated_count = WGS_Project.objects.filter(
        WGS_Mlst_Acc__isnull=False
    ).exclude(WGS_Mlst_Acc="").update(
        WGS_Mlst_Acc="",
        WGS_MlstSummary=False
    )

    # Step 2: Delete all MLST summary data
    Mlst.objects.all().delete()

    # Step 3: Display success message
    messages.success(
        request,
        f"All MLST records deleted successfully, and {updated_count} WGS Project(s) were unlinked from MLST data."
    )

    return redirect("show_mlst")




@login_required
def delete_mlst_by_date(request):
    if request.method == "POST":
        upload_date_str = request.POST.get("upload_date")
        print("🕒 Received upload_date_str:", upload_date_str)

        if not upload_date_str:
            messages.error(request, "Please select an upload date to delete.")
            return redirect("show_mlst")

        # Use Django’s date parser
        upload_date = parse_date(upload_date_str)

        if not upload_date:
            messages.error(request, f"Invalid date format: {upload_date_str}")
            return redirect("show_mlst")

        deleted_count, _ = Gambit.objects.filter(Date_uploaded_f=upload_date).delete()
        messages.success(request, f"✅ Deleted {deleted_count} Mlst records uploaded on {upload_date}.")
        return redirect("show_mlst")

    messages.error(request, "Invalid request method.")
    return redirect("show_mlst")




###################  Checkm2 
@login_required
def upload_checkm2(request):
    form = WGSProjectForm()
    checkm2_form = Checkm2UploadForm()
    editing = False

    if request.method == "POST" and request.FILES.get("Checkm2file"):
        checkm2_form = Checkm2UploadForm(request.POST, request.FILES)
        try:
            upload = checkm2_form.save()
            df = read_uploaded_file(upload.Checkm2file)
            df.columns = df.columns.str.strip().str.replace(".", "", regex=False)
        except Exception as e:
            messages.error(request, f"Error processing MLST file: {e}")
            return render(request, "wgs_app/Add_wgs.html", {
                "form": form,
                "fastq_form": FastqUploadForm(),
                "gambit_form": GambitUploadForm(),
                "mlst_form": MlstUploadForm(),
                "checkm2_form": checkm2_form,
                "amrfinder_form": AmrUploadForm(),
                "assembly_form": AssemblyUploadForm(),
                "referred_form": FinalDataUploadForm(),
                "antibiotic_form": FinalAntibioticUploadForm(),
                "editing": editing,
            })

        site_codes = set(SiteData.objects.values_list("SiteCode", flat=True))

        # Helper to build accession
        def format_checkm2_accession(raw_name: str) -> str:
            if not raw_name:
                return ""
            # Take basename and remove extension
            base = os.path.basename(raw_name)
            base_noext = os.path.splitext(base)[0].strip()

            if "ARS" not in base_noext:
                return ""

            parts = re.split(r"[-_]", base_noext)
            if not parts:
                return ""

            prefix = parts[0]  # e.g. "18ARS"

            # Look for a part that matches sitecode+digits (e.g. BGH0055, CVM0162)
            for part in parts[1:]:
                m = re.match(r"^([A-Za-z]{2,6})(\d+)", part)
                if m:
                    letters = m.group(1).upper()
                    digits = m.group(2)
                    if letters in site_codes:
                        return f"{prefix}_{letters}{digits}"

            # If sitecode and digits are separated (rare case)
            for i in range(1, len(parts) - 1):
                if parts[i].upper() in site_codes:
                    letters = parts[i].upper()
                    digits_match = re.search(r"(\d+)", parts[i + 1])
                    if digits_match:
                        return f"{prefix}_{letters}{digits_match.group(1)}"
                    return f"{prefix}_{letters}"

            return ""

        print("Total rows in dataframe:", len(df))

        for _, row in df.iterrows():
            sample_name = str(row.get("Name", "")).strip().replace(".fna", "")
            checkm2_accession = format_checkm2_accession(sample_name)

            # Step 1: Try to find Referred_Data with this accession (only if non-blank)
            referred_obj = (
                Final_Data.objects.filter(f_AccessionNo=checkm2_accession).first()
                if checkm2_accession else None
            )

            # Create WGS_Project
            connect_project = WGS_Project.objects.create(
                    Ref_Accession=referred_obj if referred_obj else None,
                    WGS_GambitSummary=False,
                    WGS_FastqSummary=False,
                    WGS_MlstSummary=False,
                    WGS_Checkm2Summary=False,
                    WGS_AssemblySummary=False,
                    WGS_AmrfinderSummary=False,
                )

            connect_project.WGS_Checkm2_Acc = checkm2_accession
            connect_project.WGS_Checkm2Summary = (
                    bool(checkm2_accession)
                    and bool(connect_project.Ref_Accession)
                    and checkm2_accession == getattr(connect_project.Ref_Accession, "f_AccessionNo", None)
                )
            connect_project.save()

            # Create Checkm2 record
            Checkm2.objects.create(
                Checkm2_Accession=checkm2_accession,
                Name=sample_name,
                checkm2_project=connect_project,
                Completeness=row.get("Completeness", ""),
                Contamination=row.get("Contamination", ""),
                Completeness_Model_Used=row.get("Completeness_Model_Used", ""),
                Translation_Table_Used=row.get("Translation_Table_Used", ""),
                Coding_Density=row.get("Coding_Density", ""),
                Contig_N50=row.get("Contig_N50", ""),
                Average_Gene_Length=row.get("Average_Gene_Length", ""),
                GC_Content=row.get("GC_Content", ""),
                Total_Coding_Sequences=row.get("Total_Coding_Sequences", ""),
                Total_Contigs=row.get("Total_Contigs", ""),
                Max_Contig_Length=row.get("Max_Contig_Length", ""),
                Additional_Notes=row.get("Additional_Notes", ""),
            )

        messages.success(request, "Checkm2 records uploaded successfully.")
        return redirect("show_checkm2")

    return render(request, "wgs_app/Add_wgs.html", {
        "form": form,
        "fastq_form": FastqUploadForm(),
        "gambit_form": GambitUploadForm(),
        "mlst_form": MlstUploadForm(),
        "checkm2_form": checkm2_form,
        "assembly_form": AssemblyUploadForm(),
        "amrfinder_form": AmrUploadForm(),
        "referred_form": FinalDataUploadForm(),
        "antibiotic_form": FinalAntibioticUploadForm(),
        "editing": editing,
    })



@login_required
def show_checkm2(request):
    checkm2_summaries = Checkm2.objects.all().order_by('-Date_uploaded_c')
    upload_dates = (
        Checkm2.objects.exclude(Date_uploaded_c__isnull=True)
        .values_list('Date_uploaded_c', flat=True)
        .distinct()
        .order_by('-Date_uploaded_c')
    )

    total_records = Checkm2.objects.count()
     # Paginate the queryset to display 20 records per page
    paginator = Paginator(checkm2_summaries, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "wgs_app/show_checkm2.html", {
        "page_obj": page_obj,
        "upload_dates": upload_dates,
        "total_records": total_records,
    })




# @login_required
# def delete_checkm2(request, pk):
#     checkm2_item = get_object_or_404(Checkm2, pk=pk)

#     if request.method == "POST":
#         checkm2_item.delete()
#         messages.success(request, f"Record {checkm2_item.Name} deleted successfully!")
#         return redirect('show_checkm2')  # <-- Correct URL name

#     messages.error(request, "Invalid request for deletion.")
#     return redirect('show_checkm2')  # <-- Correct URL name



@login_required
def delete_checkm2(request, pk):
    checkm2_item = get_object_or_404(Checkm2, pk=pk)

    if request.method == "POST":
        # Before deleting, clear related field in WGS_Project
        WGS_Project.objects.filter(WGS_Checkm2_Acc=checkm2_item.Checkm2_Accession).update(
            WGS_Checkm2_Acc="",
            WGS_Checkm2Summary=False
        )

        checkm2_item.delete()
        messages.success(request, f"Record {checkm2_item.Name} deleted successfully!")
        return redirect('show_checkm2')

    messages.error(request, "Invalid request for deletion.")
    return redirect('show_checkm2')




# @login_required
# def delete_all_checkm2(request):
#     Checkm2.objects.all().delete()
#     messages.success(request, "Checkm2 Records have been deleted successfully.")
#     return redirect('show_checkm2')  # Redirect to the table view


@login_required
def delete_all_checkm2(request):
    """
    Safely delete all CheckM2 records but preserve WGS_Project links
    for other WGS data types (FastQ, MLST, Assembly, Gambit, AMRFinder, etc.).
    """
    # Step 1: Clear only CheckM2 fields in existing WGS_Project records
    updated_count = WGS_Project.objects.filter(
        WGS_Checkm2_Acc__isnull=False
    ).exclude(WGS_Checkm2_Acc="").update(
        WGS_Checkm2_Acc="",
        WGS_Checkm2Summary=False
    )

    # Step 2: Delete all CheckM2 summary data
    Checkm2.objects.all().delete()

    # Step 3: Display success message
    messages.success(
        request,
        f"All CheckM2 records deleted successfully, and {updated_count} WGS Project(s) were unlinked from CheckM2 data."
    )

    return redirect("show_checkm2")




@login_required
def delete_checkm2_by_date(request):
    if request.method == "POST":
        upload_date_str = request.POST.get("upload_date")
        print("🕒 Received upload_date_str:", upload_date_str)

        if not upload_date_str:
            messages.error(request, "Please select an upload date to delete.")
            return redirect("show_checkm2")

        # Use Django’s date parser
        upload_date = parse_date(upload_date_str)

        if not upload_date:
            messages.error(request, f"Invalid date format: {upload_date_str}")
            return redirect("show_checkm2")

        deleted_count, _ = Gambit.objects.filter(Date_uploaded_f=upload_date).delete()
        messages.success(request, f"✅ Deleted {deleted_count} Checkm2 records uploaded on {upload_date}.")
        return redirect("show_checkm2")

    messages.error(request, "Invalid request method.")
    return redirect("show_checkm2")




###################  Assembly Scan
@login_required
def upload_assembly(request):
    form = WGSProjectForm()
    assembly_form = AssemblyUploadForm()
    editing = False

    if request.method == "POST" and request.FILES.get("Assemblyfile"):
        assembly_form = AssemblyUploadForm(request.POST, request.FILES)
        try:
            upload = assembly_form.save()
            df = read_uploaded_file(upload.Assemblyfile)
            df.columns = df.columns.str.strip().str.replace(".", "", regex=False)
        except Exception as e:
            messages.error(request, f"Error processing Assembly file: {e}")
            return render(request, "wgs_app/Add_wgs.html", {
                "form": form,
                "fastq_form": FastqUploadForm(),
                "gambit_form": GambitUploadForm(),
                "mlst_form": MlstUploadForm(),
                "checkm2_form": Checkm2UploadForm(),
                "amrfinder_form": AmrUploadForm(),
                "assembly_form": assembly_form,
                "referred_form": FinalDataUploadForm(),
                "antibiotic_form": FinalAntibioticUploadForm(),
                "editing": editing,
            })

        site_codes = set(SiteData.objects.values_list("SiteCode", flat=True))

        # Helper to build accession
        def format_assembly_accession(raw_name: str) -> str:
            if not raw_name:
                return ""
            # Take basename and remove extension
            base = os.path.basename(raw_name)
            base_noext = os.path.splitext(base)[0].strip()

            if "ARS" not in base_noext:
                return ""

            parts = re.split(r"[-_]", base_noext)
            if not parts:
                return ""

            prefix = parts[0]  # e.g. "18ARS"

            # Look for a part that matches sitecode+digits (e.g. BGH0055, CVM0162)
            for part in parts[1:]:
                m = re.match(r"^([A-Za-z]{2,6})(\d+)", part)
                if m:
                    letters = m.group(1).upper()
                    digits = m.group(2)
                    if letters in site_codes:
                        return f"{prefix}_{letters}{digits}"

            # If sitecode and digits are separated (rare case)
            for i in range(1, len(parts) - 1):
                if parts[i].upper() in site_codes:
                    letters = parts[i].upper()
                    digits_match = re.search(r"(\d+)", parts[i + 1])
                    if digits_match:
                        return f"{prefix}_{letters}{digits_match.group(1)}"
                    return f"{prefix}_{letters}"

            return ""

        for _, row in df.iterrows():
            sample_name = str(row.get("sample", "")).strip()
            assembly_accession = format_assembly_accession(sample_name)

            # Step 1: Try to find Referred_Data with this accession (only if non-blank)
            referred_obj = (
                Final_Data.objects.filter(f_AccessionNo=assembly_accession).first()
                if assembly_accession else None
            )

            # Step 2: Create or get WGS_Project
            connect_project = WGS_Project.objects.create(
                    Ref_Accession=referred_obj if referred_obj else None,
                    WGS_GambitSummary=False,
                    WGS_FastqSummary=False,
                    WGS_MlstSummary=False,
                    WGS_Checkm2Summary=False,
                    WGS_AssemblySummary=False,
                    WGS_AmrfinderSummary=False,
                )

            connect_project.WGS_Assembly_Acc = assembly_accession
            connect_project.WGS_AssemblySummary = (
                    bool(assembly_accession)
                    and bool(connect_project.Ref_Accession)
                    and assembly_accession == getattr(connect_project.Ref_Accession, "f_AccessionNo", None)
                )
            connect_project.save()

            # Step 4: Create AssemblyScan record
            AssemblyScan.objects.create(
                Assembly_Accession=assembly_accession,
                sample=sample_name,
                assembly_project=connect_project,
                total_contig=row.get("total_contig", ""),
                total_contig_length=row.get("total_contig_length", ""),
                max_contig_length=row.get("max_contig_length", ""),
                mean_contig_length=row.get("mean_contig_length", ""),
                median_contig_length=row.get("median_contig_length", ""),
                min_contig_length=row.get("min_contig_length", ""),
                n50_contig_length=row.get("n50_contig_length", ""),
                l50_contig_count=row.get("l50_contig_count", ""),
                num_contig_non_acgtn=row.get("num_contig_non_acgtn", ""),
                contig_percent_a=row.get("contig_percent_a", ""),
                contig_percent_c=row.get("contig_percent_c", ""),
                contig_percent_g=row.get("contig_percent_g", ""),
                contig_percent_t=row.get("contig_percent_t", ""),
                contig_percent_n=row.get("contig_percent_n", ""),
                contig_non_acgtn=row.get("contig_non_acgtn", ""),
                contigs_greater_1m=row.get("contigs_greater_1m", ""),
                contigs_greater_100k=row.get("contigs_greater_100k", ""),
                contigs_greater_10k=row.get("contigs_greater_10k", ""),
                contigs_greater_1k=row.get("contigs_greater_1k", ""),
                percent_contigs_greater_1m=row.get("percent_contigs_greater_1m", ""),
                percent_contigs_greater_100k=row.get("percent_contigs_greater_100k", ""),
                percent_contigs_greater_10k=row.get("percent_contigs_greater_10k", ""),
                percent_contigs_greater_1k=row.get("percent_contigs_greater_1k", ""),
            )

        messages.success(request, "AssemblyScan records uploaded successfully.")
        return redirect("show_assembly")

    return render(request, "wgs_app/Add_wgs.html", {
        "form": form,
        "fastq_form": FastqUploadForm(),
        "gambit_form": GambitUploadForm(),
        "mlst_form": MlstUploadForm(),
        "checkm2_form": Checkm2UploadForm(),
        "amrfinder_form": AmrUploadForm(),
        "assembly_form": assembly_form,
        "referred_form": FinalDataUploadForm(),
        "antibiotic_form": FinalAntibioticUploadForm(),
        "editing": editing,
    })




@login_required
def show_assembly(request):
    assembly_summaries = AssemblyScan.objects.all().order_by('-Date_uploaded_as')
    upload_dates = (
        AssemblyScan.objects.exclude(Date_uploaded_as__isnull=True)
        .values_list('Date_uploaded_as', flat=True)
        .distinct()
        .order_by('-Date_uploaded_as')
    )

    total_records = AssemblyScan.objects.count()
     # Paginate the queryset to display 20 records per page
    paginator = Paginator(assembly_summaries, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "wgs_app/show_assembly.html", {
        "page_obj": page_obj,
        "upload_dates": upload_dates,
        "total_records": total_records,
    })




@login_required
def delete_assembly(request, pk):
    assembly_item = get_object_or_404(AssemblyScan, pk=pk)

    if request.method == "POST":
        # Before deleting, clear related field in WGS_Project
        WGS_Project.objects.filter(WGS_Assembly_Acc=assembly_item.Assembly_Accession).update(
            WGS_Assembly_Acc="",
            WGS_AssemblySummary=False
        )

        assembly_item.delete()
        messages.success(request, f"Record {assembly_item.sample} deleted successfully!")
        return redirect('show_assembly')

    messages.error(request, "Invalid request for deletion.")
    return redirect('show_assembly')




@login_required
def delete_all_assembly(request):
    """
    Safely delete all Assembly records but preserve WGS_Project links
    for other WGS data types (FastQ, MLST, CheckM2, Gambit, AMRFinder, etc.).
    """
    # Step 1: Clear only Assembly fields in existing WGS_Project records
    updated_count = WGS_Project.objects.filter(
        WGS_Assembly_Acc__isnull=False
    ).exclude(WGS_Assembly_Acc="").update(
        WGS_Assembly_Acc="",
        WGS_AssemblySummary=False
    )

    # Step 2: Delete all Assembly summary data
    AssemblyScan.objects.all().delete()

    # Step 3: Display success message
    messages.success(
        request,
        f"All Assembly records deleted successfully, and {updated_count} WGS Project(s) were unlinked from Assembly data."
    )

    return redirect("show_assembly")




@login_required
def delete_assembly_by_date(request):
    if request.method == "POST":
        upload_date_str = request.POST.get("upload_date")
        print("🕒 Received upload_date_str:", upload_date_str)

        if not upload_date_str:
            messages.error(request, "Please select an upload date to delete.")
            return redirect("show_assembly")

        # Use Django’s date parser
        upload_date = parse_date(upload_date_str)

        if not upload_date:
            messages.error(request, f"Invalid date format: {upload_date_str}")
            return redirect("show_assembly")

        deleted_count, _ = AssemblyScan.objects.filter(Date_uploaded_as=upload_date).delete()
        messages.success(request, f"✅ Deleted {deleted_count} AssemblyScan records uploaded on {upload_date}.")
        return redirect("show_assembly")

    messages.error(request, "Invalid request method.")
    return redirect("show_assembly")




###################  Amr finder
@login_required
def upload_amrfinder(request):
    form = WGSProjectForm()
    amrfinder_form = AmrUploadForm()
    editing = False

    if request.method == "POST" and request.FILES.get("Amrfinderfile"):
        amrfinder_form = AmrUploadForm(request.POST, request.FILES)
        try:
            upload = amrfinder_form.save()
            df = read_uploaded_file(upload.Amrfinderfile)
            df.columns = df.columns.str.strip().str.replace(".", "", regex=False)
        except Exception as e:
            messages.error(request, f"Error processing MLST file: {e}")
            return render(request, "wgs_app/Add_wgs.html", {
                "form": form,
                "fastq_form": FastqUploadForm(),
                "gambit_form": GambitUploadForm(),
                "mlst_form": MlstUploadForm(),
                "checkm2_form": Checkm2UploadForm(),
                "amrfinder_form": amrfinder_form,
                "assembly_form": AssemblyUploadForm(),
                "referred_form": FinalDataUploadForm(),
                "antibiotic_form": FinalAntibioticUploadForm(),
                "editing": editing,
            })

        # Clean and standardize column names
        df.columns = (
            df.columns
            .str.strip()
            .str.replace(" ", "_", regex=False)
            .str.replace("%", "pct", regex=False)
            .str.replace(".", "_", regex=False)
            .str.lower()
        )

        # Preload all valid site codes from SiteData (uppercase)
        site_codes = set(SiteData.objects.values_list("SiteCode", flat=True))

        # Helper to build accession
        def format_amrfinder_accession(raw_name: str) -> str:
            if not raw_name:
                return ""
            base_noext = os.path.splitext(os.path.basename(raw_name))[0].strip()

            # Must contain ARS to be eligible
            if "ARS" not in base_noext:
                return ""

            parts = re.split(r"[-_]", base_noext)
            if not parts:
                return ""

            prefix = parts[0]  # e.g., "24ARS"

            # 1) Look for LETTERS + DIGITS where LETTERS is a valid site code
            for part in parts[1:]:
                m = re.match(r"^([A-Za-z]{2,6})(\d+)$", part)
                if m:
                    letters = m.group(1).upper()
                    digits = m.group(2)
                    if letters in site_codes:
                        return f"{prefix}_{letters}{digits}"

            # 2) Check if sitecode is a separate part followed by digits
            for i in range(1, len(parts)):
                part = parts[i]
                if part.upper() in site_codes:
                    letters = part.upper()
                    digits = ""
                    if i + 1 < len(parts):
                        next_part = parts[i + 1]
                        m2 = re.match(r"^([A-Za-z]{2,6})(\d+)$", next_part)
                        if m2:
                            digits = m2.group(2)
                        else:
                            dmatch = re.search(r"(\d+)", next_part)
                            if dmatch:
                                digits = dmatch.group(1)
                    if not digits:
                        dmatch2 = re.search(r"(\d+)", part)
                        if dmatch2:
                            digits = dmatch2.group(1)
                    return f"{prefix}_{letters}{digits}" if digits else f"{prefix}_{letters}"

            # 3) As a fallback, match any valid sitecode prefix
            for part in parts[1:]:
                m = re.match(r"^([A-Za-z]{2,6})(\d+)$", part)
                if m and m.group(1).upper() in site_codes:
                    return f"{prefix}_{m.group(1).upper()}{m.group(2)}"

            return ""

        print("Total rows in dataframe:", len(df))

        for _, row in df.iterrows():
            sample_name = str(row.get("name", "")).strip()
            amrfinder_accession = format_amrfinder_accession(sample_name)

            # Step 1: Try to find Referred_Data with this accession (only if non-blank)
            referred_obj = (
                Final_Data.objects.filter(f_AccessionNo=amrfinder_accession).first()
                if amrfinder_accession else None
            )

            # Safely get or create WGS_Project
            connect_project = (
                WGS_Project.objects.filter(Ref_Accession=referred_obj).first()
                if referred_obj else None
            )

            # Step 2: Allow multiple WGS_Project per accession
            connect_project = WGS_Project.objects.create(
                Ref_Accession=referred_obj if referred_obj else None,
                WGS_GambitSummary=False,
                WGS_FastqSummary=False,
                WGS_MlstSummary=False,
                WGS_Checkm2Summary=False,
                WGS_AssemblySummary=False,
                WGS_AmrfinderSummary=False,
            )

            # Step 3: Update project accession & summary flag
            connect_project.WGS_Amrfinder_Acc = amrfinder_accession
            connect_project.WGS_AmrfinderSummary = (
                amrfinder_accession != "" and
                bool(connect_project.Ref_Accession) and
                amrfinder_accession == getattr(connect_project.Ref_Accession, "AccessionNo", None)
            )
            connect_project.save()

            # Step 4: Create Amrfinderplus record
            Amrfinderplus.objects.create(
                Amrfinder_Accession=amrfinder_accession,
                name=sample_name,
                amrfinder_project=connect_project,
                protein_id=row.get("protein_id", ""),
                contig_id=row.get("contig_id", ""),
                start=row.get("start", ""),
                stop=row.get("stop", ""),
                strand=row.get("strand", ""),
                element_symbol=row.get("element_symbol", ""),
                element_name=row.get("element_name", ""),
                scope=row.get("scope", ""),
                type_field=row.get("type", ""),
                subtype=row.get("subtype", ""),
                class_field=row.get("class", ""),
                subclass=row.get("subclass", ""),
                method=row.get("method", ""),
                target_length=row.get("target_length", ""),
                reference_sequence_length=row.get("reference_sequence_length", ""),
                percent_coverage_of_reference=row.get("pct_coverage_of_reference", ""),
                percent_identity_to_reference=row.get("pct_identity_to_reference", ""),
                alignment_length=row.get("alignment_length", ""),
                closest_reference_accession=row.get("closest_reference_accession", ""),
                closest_reference_name=row.get("closest_reference_name", ""),
                hmm_accession=row.get("hmm_accession", ""),
                hmm_description=row.get("hmm_description", ""),
                Date_uploaded_am = row.get("date_uploaded_am","")

            )

        messages.success(request, "Amrfinder records uploaded successfully.")
        return redirect("show_amrfinder")

    return render(request, "wgs_app/Add_wgs.html", {
        "form": form,
        "fastq_form": FastqUploadForm(),
        "gambit_form": GambitUploadForm(),
        "mlst_form": MlstUploadForm(),
        "checkm2_form": Checkm2UploadForm(),
        "assembly_form": AssemblyUploadForm(),
        "amrfinder_form": amrfinder_form,
        "referred_form": FinalDataUploadForm(),
        "antibiotic_form": FinalAntibioticUploadForm(),
        "editing": editing,
    })


# @login_required
# def show_amrfinder(request):
#     records = Amrfinderplus.objects.all().order_by('-Date_uploaded_am')
#     upload_dates = (
#         Amrfinderplus.objects.exclude(Date_uploaded_am__isnull=True)
#         .values_list('Date_uploaded_am', flat=True)
#         .distinct()
#         .order_by('-Date_uploaded_am')
#     )

#     return render(request, "wgs_app/show_amrfinder.html", {
#         "records": records,
#         "upload_dates": upload_dates,
#     })



@login_required
def show_amrfinder(request):
    amrfinder_summaries = Amrfinderplus.objects.all().order_by('-Date_uploaded_am')
    upload_dates = (
        Amrfinderplus.objects.exclude(Date_uploaded_am__isnull=True)
        .values_list('Date_uploaded_am', flat=True)
        .distinct()
        .order_by('-Date_uploaded_am')
    )

    total_records = Amrfinderplus.objects.count()
     # Paginate the queryset to display 20 records per page
    paginator = Paginator(amrfinder_summaries, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "wgs_app/show_amrfinder.html", {
        "page_obj": page_obj,
        "upload_dates": upload_dates,
        "total_records": total_records,
    })




# @login_required
# def delete_amrfinder(request, pk):
#     amrfinder_item = get_object_or_404(Amrfinderplus, pk=pk)

#     if request.method == "POST":
#         amrfinder_item.delete()
#         messages.success(request, f"Record {amrfinder_item.name} deleted successfully!")
#         return redirect('show_amrfinder')  # <-- Correct URL name

#     messages.error(request, "Invalid request for deletion.")
#     return redirect('show_amrfinder')  # <-- Correct URL name



@login_required
def delete_amrfinder(request, pk):
    amrfinder_item = get_object_or_404(Amrfinderplus, pk=pk)

    if request.method == "POST":
        # Before deleting, clear related field in WGS_Project
        WGS_Project.objects.filter(WGS_Amrfinder_Acc=amrfinder_item.Amrfinder_Accession).update(
            WGS_Amrfinder_Acc="",
            WGS_AmrfinderSummary=False
        )

        amrfinder_item.delete()
        messages.success(request, f"Record {amrfinder_item.name} deleted successfully!")
        return redirect('show_amrfinder')

    messages.error(request, "Invalid request for deletion.")
    return redirect('show_amrfinder')


# @login_required
# def delete_all_amrfinder(request):
#     Amrfinderplus.objects.all().delete()
#     messages.success(request, "AmrfinderPlus Records have been deleted successfully.")
#     return redirect('show_amrfinder')  # Redirect to the table view



@login_required
def delete_all_amrfinder(request):
    """
    Safely delete all AMRFinder records but preserve WGS_Project links
    for other WGS data types (FastQ, MLST, CheckM2, Assembly, Gambit, etc.).
    """
    # Step 1: Clear only AMRFinder fields in existing WGS_Project records
    updated_count = WGS_Project.objects.filter(
        WGS_Amrfinder_Acc__isnull=False
    ).exclude(WGS_Amrfinder_Acc="").update(
        WGS_Amrfinder_Acc="",
        WGS_AmrfinderSummary=False
    )

    # Step 2: Delete all AMRFinder summary data
    Amrfinderplus.objects.all().delete()

    # Step 3: Display success message
    messages.success(
        request,
        f"All AMRFinder records deleted successfully, and {updated_count} WGS Project(s) were unlinked from AMRFinder data."
    )

    return redirect("show_amrfinder")




@login_required
def delete_amrfinder_by_date(request):
    if request.method == "POST":
        upload_date_str = request.POST.get("upload_date")
        if not upload_date_str:
            messages.error(request, "Please select an upload date to delete.")
            return redirect("show_amrfinder")

        try:
            target_date = datetime.strptime(upload_date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")
            return redirect("show_amrfinder")

        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date + datetime.timedelta(days=1), datetime.min.time())

        deleted_count, _ = Amrfinderplus.objects.filter(
            Date_uploaded_am__gte=start,
            Date_uploaded_am__lt=end
        ).delete()

        messages.success(request, f"✅ Deleted {deleted_count} records uploaded on {target_date}.")

    else:
        messages.error(request, "Invalid request method.")

    return redirect("show_amrfinder")






########### Show all WGS project entries for one Referred_Data AccessionNo,
##########  including FastQ, CheckM2, AMRFinder tables.


# @login_required

@login_required
def view_wgs_overview(request):
    """
    Displays only isolates (Final_Data) that have matched WGS data
    across any WGS table (FastQ, MLST, CheckM2, Assembly, Gambit, AMRFinder).
    Includes antibiotic entries if available.
    Works even if WGS_Project or FastQ data are deleted.
    """

    # --- Step 1: Gather all accessions from any WGS table, safely ---

    fastq_accs = list(FastqSummary.objects.values_list("sample", flat=True).distinct())
    mlst_accs = list(Mlst.objects.values_list("mlst_project__WGS_Mlst_Acc", flat=True).distinct())
    checkm2_accs = list(Checkm2.objects.values_list("checkm2_project__WGS_Checkm2_Acc", flat=True).distinct())
    assembly_accs = list(AssemblyScan.objects.values_list("assembly_project__WGS_Assembly_Acc", flat=True).distinct())
    gambit_accs = list(Gambit.objects.values_list("Gambit_Accession", flat=True).distinct())
    amrfinder_accs = list(Amrfinderplus.objects.values_list("amrfinder_project__WGS_Amrfinder_Acc", flat=True).distinct())

    # --- Debug logging ---
    print(f"FastQ accessions: {len(fastq_accs)} - Sample: {fastq_accs[:3]}")
    print(f"MLST accessions: {len(mlst_accs)} - Sample: {mlst_accs[:3]}")
    print(f"CheckM2 accessions: {len(checkm2_accs)} - Sample: {checkm2_accs[:3]}")
    print(f"Assembly accessions: {len(assembly_accs)} - Sample: {assembly_accs[:3]}")
    print(f"Gambit accessions: {len(gambit_accs)} - Sample: {gambit_accs[:3]}")
    print(f"AMRFinder accessions: {len(amrfinder_accs)} - Sample: {amrfinder_accs[:3]}")

    # --- Combine all into one set ---
    wgs_accessions = set(
         fastq_accs + mlst_accs + checkm2_accs + assembly_accs + gambit_accs + amrfinder_accs
    )

    # --- Remove blanks, None values, and normalize ---
    wgs_accessions = {
        str(acc).strip() for acc in wgs_accessions 
        if acc and acc != 'None' and str(acc).strip() != ''
    }

    print(f"Total unique WGS accessions found: {len(wgs_accessions)}")
    print(f"WGS Accessions sample: {list(wgs_accessions)[:10]}")

    # --- Step 2: Load only matched isolates ---
    referred_list = Final_Data.objects.only(
        "f_AccessionNo",
        "f_Patient_ID",
        "f_Last_Name",
        "f_First_Name",
        "f_Mid_Name",
        "f_Age",
        "f_Sex",
        "f_Ward",
        "f_Spec_Type",
        "f_ars_OrgCode",
        "f_SiteCode",
        "f_Diagnosis_ICD10",
        "f_Growth",
        "f_Spec_Date",
        "f_Referral_Date",
    ).filter(f_AccessionNo__in=wgs_accessions).order_by("f_AccessionNo")

    print(f"Matched isolates found: {referred_list.count()}")
    
    # --- Debug: Show what accessions exist in Final_Data ---
    all_final_data_accs = set(
        Final_Data.objects.values_list("f_AccessionNo", flat=True).distinct()
    )
    print(f"Total accessions in Final_Data: {len(all_final_data_accs)}")
    print(f"Sample Final_Data accessions: {list(all_final_data_accs)[:10]}")

    # --- Check for mismatches ---
    missing_in_final_data = wgs_accessions - all_final_data_accs
    if missing_in_final_data:
        print(f" WARNING: {len(missing_in_final_data)} WGS accessions not found in Final_Data")
        print(f"Examples: {list(missing_in_final_data)[:5]}")

    # --- Step 3: Preload antibiotic entries ---
    all_antibiotics = Final_AntibioticEntry.objects.select_related(
        "ab_idNum_f_referred"
    ).only(
        "ab_idNum_f_referred__f_AccessionNo",
        "ab_Abx_code",
        "ab_MIC_RIS",
        "ab_MIC_value",
        "ab_Disk_value",
    )

    abx_map = {}
    for ab in all_antibiotics:
        acc = getattr(ab.ab_idNum_f_referred, "f_AccessionNo", None)
        if acc:
            abx_map.setdefault(acc, []).append({
                "code": ab.ab_Abx_code,
                "ris": ab.ab_MIC_RIS or "",
                "disk": ab.ab_Disk_value or "",
                "mic": ab.ab_MIC_value or "",
            })

    table_data = []

    # --- Step 4: For each referred isolate ---
    for referred in referred_list:
        acc = referred.f_AccessionNo.strip() if referred.f_AccessionNo else None
        if not acc:
            continue

        # Get projects if any exist
        projects = WGS_Project.objects.filter(
            Q(WGS_FastQ_Acc=acc)
            | Q(WGS_Mlst_Acc=acc)
            | Q(WGS_Checkm2_Acc=acc)
            | Q(WGS_Assembly_Acc=acc)
            | Q(WGS_Gambit_Acc=acc)
            | Q(WGS_Amrfinder_Acc=acc)
        ).distinct()

        # Determine which WGS data exist
        summary_flags = {
            "fastq": FastqSummary.objects.filter(
                Q(fastq_project__in=projects) | Q(sample=acc)
            ).exists(),
            "mlst": Mlst.objects.filter(
                Q(mlst_project__in=projects) | Q(mlst_project__WGS_Mlst_Acc=acc)
            ).exists(),
            "checkm2": Checkm2.objects.filter(
                Q(checkm2_project__in=projects) | Q(checkm2_project__WGS_Checkm2_Acc=acc)
            ).exists(),
            "assembly": AssemblyScan.objects.filter(
                Q(assembly_project__in=projects) | Q(assembly_project__WGS_Assembly_Acc=acc)
            ).exists(),
            "gambit": Gambit.objects.filter(
                Q(gambit_project__in=projects) | Q(Gambit_Accession=acc)
            ).exists(),
            "amrfinder": Amrfinderplus.objects.filter(
                Q(amrfinder_project__in=projects) | Q(amrfinder_project__WGS_Amrfinder_Acc=acc)
            ).exists(),
        }

        # Collect related data
        related_data = {}
        if summary_flags["fastq"]:
            related_data["fastq"] = FastqSummary.objects.filter(
                Q(fastq_project__in=projects) | Q(sample=acc)
            )
        if summary_flags["mlst"]:
            related_data["mlst"] = Mlst.objects.filter(
                Q(mlst_project__in=projects) | Q(mlst_project__WGS_Mlst_Acc=acc)
            )
        if summary_flags["checkm2"]:
            related_data["checkm2"] = Checkm2.objects.filter(
                Q(checkm2_project__in=projects) | Q(checkm2_project__WGS_Checkm2_Acc=acc)
            )
        if summary_flags["assembly"]:
            related_data["assembly"] = AssemblyScan.objects.filter(
                Q(assembly_project__in=projects) | Q(assembly_project__WGS_Assembly_Acc=acc)
            )
        if summary_flags["gambit"]:
            related_data["gambit"] = Gambit.objects.filter(
                Q(gambit_project__in=projects) | Q(Gambit_Accession=acc)
            )
        if summary_flags["amrfinder"]:
            related_data["amrfinder"] = Amrfinderplus.objects.filter(
                Q(amrfinder_project__in=projects) | Q(amrfinder_project__WGS_Amrfinder_Acc=acc)
            )

        # Antibiotics
        abx_entries = abx_map.get(acc, [])

        # Append final table entry
        table_data.append({
            "accession": acc,
            "patient_id": referred.f_Patient_ID,
            "patient_name": f"{referred.f_Last_Name}, {referred.f_First_Name} {referred.f_Mid_Name or ''}".strip(),
            "age": referred.f_Age,
            "sex": referred.f_Sex,
            "ward": referred.f_Ward,
            "specimen": referred.f_Spec_Type,
            "organism": referred.f_ars_OrgCode,
            "sitecode": referred.f_SiteCode,
            "diagnosis": referred.f_Diagnosis_ICD10,
            "growth": referred.f_Growth,
            "date_collected": referred.f_Spec_Date,
            "referral_date": referred.f_Referral_Date,
            "summary_flags": summary_flags,
            "related_data": related_data,
            "antibiotics": abx_entries,
        })

    # --- Generate summary counts ---
    counts = {
        "total": len(table_data),
        "fastq": sum(1 for e in table_data if e["summary_flags"]["fastq"]),
        "mlst": sum(1 for e in table_data if e["summary_flags"]["mlst"]),
        "checkm2": sum(1 for e in table_data if e["summary_flags"]["checkm2"]),
        "assembly": sum(1 for e in table_data if e["summary_flags"]["assembly"]),
        "gambit": sum(1 for e in table_data if e["summary_flags"]["gambit"]),
        "amrfinder": sum(1 for e in table_data if e["summary_flags"]["amrfinder"]),
        "with_antibiotics": sum(1 for e in table_data if e["antibiotics"]),
    }

    print(f"Final counts: {counts}")

    return render(request, "wgs_app/Wgs_overview.html", {
        "table_data": table_data,
        "counts": counts,
    })



# View WGS overview with antibiotic entries but optimized to reduce queries
# Shows isolates that have WGS data in ANY of the WGS tables

@login_required
def get_wgs_details(request, accession):
    """
    Returns detailed info for one accession.
    Used for AJAX lazy loading.
    """
    print(f"\n=== FETCHING DETAILS FOR ACCESSION: {accession} ===")
    
    # Fetch the referred data
    referred = Final_Data.objects.filter(f_AccessionNo=accession).first()
    if not referred:
        print(f" Accession {accession} not found in Final_Data")
        return JsonResponse({"error": "Accession not found."}, status=404)

    print(f" Found referred record: {referred}")
    print(f"   - Patient: {referred.f_First_Name} {referred.f_Last_Name}")
    print(f"   - Age: {referred.f_Age}, Sex: {referred.f_Sex}")
    print(f"   - Specimen: {referred.f_Spec_Type}")

    # Fetch antibiotic entries - use values_dict for clarity
    antibiotics_qs = Final_AntibioticEntry.objects.filter(
        ab_idNum_f_referred__f_AccessionNo=accession
    )
    
    antibiotics = []
    for ab in antibiotics_qs:
        antibiotics.append({
            "ab_Abx_code": ab.ab_Abx_code,
            "ab_MIC_RIS": ab.ab_MIC_RIS or "",
            "ab_MIC_value": ab.ab_MIC_value or "",
            "ab_Disk_value": ab.ab_Disk_value or "",
        })
    
    print(f" Found {len(antibiotics)} antibiotic entries")

    # Fetch related WGS projects
    projects = WGS_Project.objects.filter(
        Q(WGS_FastQ_Acc=accession)
        | Q(WGS_Mlst_Acc=accession)
        | Q(WGS_Checkm2_Acc=accession)
        | Q(WGS_Assembly_Acc=accession)
        | Q(WGS_Gambit_Acc=accession)
        | Q(WGS_Amrfinder_Acc=accession)
    ).distinct()

    print(f" Found {projects.count()} WGS projects")

    # Collect all related data
    related_data = {
        "fastq": list(FastqSummary.objects.filter(
            Q(fastq_project__in=projects) | Q(sample=accession)
        )),
        "mlst": list(Mlst.objects.filter(
            Q(mlst_project__in=projects) | Q(mlst_project__WGS_Mlst_Acc=accession)
        )),
        "checkm2": list(Checkm2.objects.filter(
            Q(checkm2_project__in=projects) | Q(checkm2_project__WGS_Checkm2_Acc=accession)
        )),
        "assembly": list(AssemblyScan.objects.filter(
            Q(assembly_project__in=projects) | Q(assembly_project__WGS_Assembly_Acc=accession)
        )),
        "gambit": list(Gambit.objects.filter(
            Q(gambit_project__in=projects) | Q(Gambit_Accession=accession)
        )),
        "amrfinder": list(Amrfinderplus.objects.filter(
            Q(amrfinder_project__in=projects) | Q(amrfinder_project__WGS_Amrfinder_Acc=accession)
        )),
    }

    print(f"   - FastQ records: {len(related_data['fastq'])}")
    print(f"   - MLST records: {len(related_data['mlst'])}")
    print(f"   - CheckM2 records: {len(related_data['checkm2'])}")
    print(f"   - Assembly records: {len(related_data['assembly'])}")
    print(f"   - Gambit records: {len(related_data['gambit'])}")
    print(f"   - AMRFinder records: {len(related_data['amrfinder'])}")

    # Build context - CRITICAL: match template variable names exactly
    context = {
        "entry": {
            "accession": accession,
            "patient_id": referred.f_Patient_ID,
            "patient_name": f"{referred.f_Last_Name}, {referred.f_First_Name} {referred.f_Mid_Name or ''}".strip(),
            "age": referred.f_Age,
            "sex": referred.f_Sex,
            "ward": referred.f_Ward,
            "specimen": referred.f_Spec_Type,
            "organism": referred.f_ars_OrgCode,
            "sitecode": referred.f_SiteCode,
            "diagnosis": referred.f_Diagnosis_ICD10,
            "growth": referred.f_Growth,
            "date_collected": referred.f_Spec_Date,
            "referral_date": referred.f_Referral_Date,
            "antibiotics": antibiotics,
            "related_data": related_data,
        }
    }

    print(f"\n CONTEXT TO RENDER:")
    print(f"   - Accession: {context['entry']['accession']}")
    print(f"   - Patient Name: {context['entry']['patient_name']}")
    print(f"   - Age: {context['entry']['age']}")
    print(f"   - Sex: {context['entry']['sex']}")
    print(f"   - Specimen: {context['entry']['specimen']}")
    print(f"   - Antibiotics: {len(context['entry']['antibiotics'])} entries")

    # Render template
    html = render_to_string(
        "wgs_app/Wgs_detail.html",
        context,
        request=request,
    )

    print(f" Template rendered successfully\n")

    return JsonResponse({"html": html})




@login_required
def download_matched_wgs_data(request):
    """
    Export Final_Data + Antibiotic results (MIC, Disk, RIS)
    along with WGS data (FastQ, MLST, CheckM2, Assembly, AMRFinder, Gambit).

    Mode options:
        ?mode=all  → Complete sets (present in ALL WGS tables)
        ?mode=any  → Partial sets (present in ANY WGS table)
    """
    import io
    import pandas as pd
    from django.http import HttpResponse

    mode = request.GET.get("mode", "any").lower()

    # ---- Step 1: Collect valid accessions from Final_Data ----
    referred_acc = set(Final_Data.objects.values_list("f_AccessionNo", flat=True))

    # ---- Step 2: Collect accessions from each WGS table ----
    fastq_acc = set(FastqSummary.objects.filter(FastQ_Accession__in=referred_acc)
                    .values_list("FastQ_Accession", flat=True))
    mlst_acc = set(Mlst.objects.filter(Mlst_Accession__in=referred_acc)
                    .values_list("Mlst_Accession", flat=True))
    checkm2_acc = set(Checkm2.objects.filter(Checkm2_Accession__in=referred_acc)
                    .values_list("Checkm2_Accession", flat=True))
    assembly_acc = set(AssemblyScan.objects.filter(Assembly_Accession__in=referred_acc)
                    .values_list("Assembly_Accession", flat=True))
    amrfinder_acc = set(Amrfinderplus.objects.filter(Amrfinder_Accession__in=referred_acc)
                    .values_list("Amrfinder_Accession", flat=True))
    gambit_acc = set(Gambit.objects.filter(Gambit_Accession__in=referred_acc)
                    .values_list("Gambit_Accession", flat=True))

    # ---- Step 3: Combine or intersect ----
    if mode == "all":
        matched_accessions = (
            fastq_acc & mlst_acc & checkm2_acc & assembly_acc & amrfinder_acc & gambit_acc
        )
        filename_suffix = "Complete"
    else:
        matched_accessions = (
            fastq_acc | mlst_acc | checkm2_acc | assembly_acc | amrfinder_acc | gambit_acc
        )
        filename_suffix = "Partial"

    if not matched_accessions:
        return HttpResponse(
            "No matching WGS accessions found in Final Referred_Data.",
            content_type="text/plain"
        )

    # ---- Step 4: Query datasets ----
    final_qs = Final_Data.objects.filter(f_AccessionNo__in=matched_accessions)
    abx_qs = Final_AntibioticEntry.objects.filter(
        ab_idNum_f_referred__f_AccessionNo__in=matched_accessions
    )
    fastq_qs = FastqSummary.objects.filter(FastQ_Accession__in=matched_accessions)
    mlst_qs = Mlst.objects.filter(Mlst_Accession__in=matched_accessions)
    checkm2_qs = Checkm2.objects.filter(Checkm2_Accession__in=matched_accessions)
    assembly_qs = AssemblyScan.objects.filter(Assembly_Accession__in=matched_accessions)
    amrfinder_qs = Amrfinderplus.objects.filter(Amrfinder_Accession__in=matched_accessions)
    gambit_qs = Gambit.objects.filter(Gambit_Accession__in=matched_accessions)

    # ---- Step 5: Convert querysets to DataFrames ----
    final_df = pd.DataFrame.from_records(final_qs.values())
    abx_df = pd.DataFrame.from_records(abx_qs.values())

    def qs_to_df(qs, model_name, acc_field):
        if not qs.exists():
            return pd.DataFrame()
        df = pd.DataFrame.from_records(qs.values())
        df.insert(0, "Table", model_name)
        df.insert(1, "f_AccessionNo", df[acc_field])
        return df

    fastq_df = qs_to_df(fastq_qs, "FastqSummary", "FastQ_Accession")
    mlst_df = qs_to_df(mlst_qs, "Mlst", "Mlst_Accession")
    checkm2_df = qs_to_df(checkm2_qs, "Checkm2", "Checkm2_Accession")
    assembly_df = qs_to_df(assembly_qs, "AssemblyScan", "Assembly_Accession")
    amrfinder_df = qs_to_df(amrfinder_qs, "Amrfinderplus", "Amrfinder_Accession")
    gambit_df = qs_to_df(gambit_qs, "Gambit", "Gambit_Accession")

    # ---- Step 6: Merge Final_Data with antibiotics ----
    combined_df = final_df.copy()
    if not abx_df.empty:
        abx_df = abx_df.merge(
            final_df[["id", "f_AccessionNo"]],
            left_on="ab_idNum_f_referred_id",
            right_on="id",
            how="left"
        )

        def pivot_antibiotic(df, value_field, suffix):
            pivot = df.pivot_table(
                index="f_AccessionNo",
                columns="ab_Abx_code",
                values=value_field,
                aggfunc="first"
            )
            pivot.columns = [f"{col}_{suffix}" for col in pivot.columns]
            return pivot

        abx_mic_val = pivot_antibiotic(abx_df, "ab_MIC_value", "MIC")
        abx_mic_ris = pivot_antibiotic(abx_df, "ab_MIC_RIS", "MIC_RIS")
        abx_disk_val = pivot_antibiotic(abx_df, "ab_Disk_value", "Disk")
        abx_disk_ris = pivot_antibiotic(abx_df, "ab_Disk_RIS", "Disk_RIS")

        abx_pivot = pd.concat(
            [abx_mic_val, abx_mic_ris, abx_disk_val, abx_disk_ris], axis=1
        )
        abx_pivot.reset_index(inplace=True)
        combined_df = final_df.merge(abx_pivot, on="f_AccessionNo", how="left")

    # ---- Step 7: Make datetimes timezone-naive ----
    def make_tz_naive(df):
        if df.empty:
            return df
        for col in df.select_dtypes(include=["datetimetz", "datetime"]).columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.tz_localize(None)
            df[col] = df[col].dt.strftime("%Y-%m-%d")
        return df

    combined_df = make_tz_naive(combined_df)

    # ---- Step 8: Write all to Excel ----
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        combined_df.to_excel(writer, index=False, sheet_name="Final_Data_With_Antibiotics")
        if not fastq_df.empty: fastq_df.to_excel(writer, index=False, sheet_name="FastQ")
        if not mlst_df.empty: mlst_df.to_excel(writer, index=False, sheet_name="MLST")
        if not checkm2_df.empty: checkm2_df.to_excel(writer, index=False, sheet_name="CheckM2")
        if not assembly_df.empty: assembly_df.to_excel(writer, index=False, sheet_name="Assembly")
        if not amrfinder_df.empty: amrfinder_df.to_excel(writer, index=False, sheet_name="AMRFinder")
        if not gambit_df.empty: gambit_df.to_excel(writer, index=False, sheet_name="Gambit")

    output.seek(0)
    filename = f"FinalData_WGS_{filename_suffix}_{pd.Timestamp.now().date()}.xlsx"

    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
