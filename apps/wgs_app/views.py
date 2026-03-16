
from collections import defaultdict
import datetime
from decimal import Decimal, InvalidOperation
from io import TextIOWrapper
import io
import re
from django.db import transaction
import csv
from django.db.models import Q, F, Func
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import render, redirect

from apps.home.views import nz

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
from django.views.decorators.http import require_POST
import openpyxl
from datetime import date, datetime


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
        sampleinfo_form = SampleInfoUpload(request.POST, request.FILES)
        bactscout_form = BactScoutUploadForm(request.POST, request.FILES)
        gtdbtk_form = GtdbTkUploadForm(request.POST, request.FILES)
        fastq_form = FastqUploadForm(request.POST, request.FILES)
        gambit_form = GambitUploadForm(request.POST, request.FILES)
        mlst_form = MlstUploadForm(request.POST, request.FILES)
        checkm2_form = Checkm2UploadForm(request.POST, request.FILES)
        assembly_form = AssemblyUploadForm(request.POST, request.FILES)
        amrfinder_form = AmrUploadForm(request.POST, request.FILES)
        demogs_form = DemogsDataUploadForm(request.POST, request.FILES)
        antibiotic_form = FinalAntibioticUploadForm(request.POST, request.FILES)
        raw_antibiotic_form = RawAntibioticUploadForm(request.POST, request.FILES)

        final_data_uploaded = False
        final_antibiotic_uploaded = False
        raw_antibiotic_uploaded = False
        project_saved = False
        sampleinfo_uploaded = False
        bacscout_uploaded = False
        gtdbtk_uploaded = False
        fastq_uploaded = False
        gambit_uploaded = False
        mlst_uploaded = False
        checkm2_uploaded = False
        assembly_uploaded = False
        amrfinder_uploaded = False
        
        
         # Final Data upload
        if demogs_form.is_valid():
            form.save()
            final_data_uploaded = True

         # Final Data upload
        if antibiotic_form.is_valid():
            form.save()
            final_antibiotic_uploaded = True

                 # Final Data upload
        if raw_antibiotic_form.is_valid():
            form.save()
            raw_antibiotic_uploaded = True


        # WGS Project
        if form.is_valid():
            form.save()
            project_saved = True

        # SampleInfo Upload
        if sampleinfo_form.is_valid():
            sampleinfo_form.save()
            sampleinfo_uploaded = True

        # Bacscout Upload
        if bactscout_form.is_valid():
            bactscout_form.save()
            bactscout_uploaded = True


        # Bacscout Upload
        if gtdbtk_form.is_valid():
            gtdbtk_form.save()
            gtdbtk_uploaded = True

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
        if project_saved or final_data_uploaded or final_antibiotic_uploaded or raw_antibiotic_uploaded or sampleinfo_uploaded  or bactscout_uploaded or gtdbtk_uploaded or fastq_uploaded or gambit_uploaded or mlst_uploaded or checkm2_uploaded or assembly_uploaded or amrfinder_uploaded:
            return redirect("upload_wgs_view")

    else:
        form = WGSProjectForm()
        demogs_form = DemogsDataUploadForm()
        antibiotic_form = FinalAntibioticUploadForm()
        raw_antibiotic_form = RawAntibioticUploadForm()
        sampleinfo_form = SampleInfoUploadForm()
        bactscout_form = BactScoutUploadForm()
        gtdbtk_form = GtdbTkUploadForm()
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
            "demogs_form": demogs_form,
            "antibiotic_form": antibiotic_form,
            "raw_antibiotic_form": raw_antibiotic_form,
            "sampleinfo_form": sampleinfo_form,
            "bactscout_form": bactscout_form,
            "gtdbtk_form": gtdbtk_form,
            "fastq_form": fastq_form,
            "gambit_form": gambit_form,
            "mlst_form": mlst_form,
            "checkm2_form": checkm2_form,
            "assembly_form": assembly_form,
            "amrfinder_form": amrfinder_form,
            "editing": False,
        },
    )


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
                    "demogs_form": DemogsDataUploadForm(),
                    "antibiotic_form": FinalAntibioticUploadForm(),
                    "raw_antibiotic_form": RawAntibioticUploadForm(),
                    "sampleinfo_form" : SampleInfoUploadForm(),
                    "bacscout_form": BactScoutUploadForm(),
                    "gtdbtk_form": GtdbTkUploadForm(),
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
                    WGS_SampleInfoSummary=False,
                    WGS_BactScoutSummary=False,
                    WGS_GtdbTkSummary=False,
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
        "demogs_form": DemogsDataUploadForm(),
        "antibiotic_form": FinalAntibioticUploadForm(),
        "raw_antibiotic_form": RawAntibioticUploadForm(),
        "sampleinfo_form" : SampleInfoUploadForm(),
        "bacscout_form": BactScoutUploadForm(),
        "gtdbtk_form": GtdbTkUploadForm(),
        "editing": editing,
    })



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
                    "demogs_form": DemogsDataUploadForm(),
                    "antibiotic_form": FinalAntibioticUploadForm(),
                    "sampleinfo_form" : SampleInfoUploadForm(),
                    "bacscout_form": BactScoutUploadForm(),
                    "gtdbtk_form": GtdbTkUploadForm(),
                    "raw_antibiotic_form": RawAntibioticUploadForm(),
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
                    WGS_SampleInfoSummary=False,
                    WGS_BactScoutSummary=False,
                    WGS_GtdbTkSummary=False,
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
        "demogs_form": DemogsDataUploadForm(),
        "antibiotic_form": FinalAntibioticUploadForm(),
        "sampleinfo_form" : SampleInfoUploadForm(),
        "bacscout_form": BactScoutUploadForm(),
        "gtdbtk_form": GtdbTkUploadForm(),
        "raw_antibiotic_form": RawAntibioticUploadForm(),
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
                "demogs_form": DemogsDataUploadForm(),
                "antibiotic_form": FinalAntibioticUploadForm(),
                "sampleinfo_form" : SampleInfoUploadForm(),
                "bacscout_form": BactScoutUploadForm(),
                "gtdbtk_form": GtdbTkUploadForm(),
                "raw_antibiotic_form": RawAntibioticUploadForm(),
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
                    WGS_SampleInfoSummary=False,
                    WGS_BactScoutSummary=False,
                    WGS_GtdbTkSummary=False,
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
        "demogs_form": DemogsDataUploadForm(),
        "antibiotic_form": FinalAntibioticUploadForm(),
        "sampleinfo_form" : SampleInfoUploadForm(),
        "bacscout_form": BactScoutUploadForm(),
        "gtdbtk_form": GtdbTkUploadForm(),
        "raw_antibiotic_form": RawAntibioticUploadForm(),
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
                "demogs_form": DemogsDataUploadForm(),
                "antibiotic_form": FinalAntibioticUploadForm(),
                "sampleinfo_form" : SampleInfoUploadForm(),
                "bacscout_form": BactScoutUploadForm(),
                "gtdbtk_form": GtdbTkUploadForm(),
                "raw_antibiotic_form": RawAntibioticUploadForm(),
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
                    WGS_SampleInfoSummary=False,
                    WGS_BactScoutSummary=False,
                    WGS_GtdbTkSummary=False,
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
        "demogs_form": DemogsDataUploadForm(),
        "antibiotic_form": FinalAntibioticUploadForm(),
        "sampleinfo_form" : SampleInfoUploadForm(),
        "bacscout_form": BactScoutUploadForm(),
        "gtdbtk_form": GtdbTkUploadForm(),
        "raw_antibiotic_form": RawAntibioticUploadForm(),
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
                "demogs_form": DemogsDataUploadForm(),
                "antibiotic_form": FinalAntibioticUploadForm(),
                "sampleinfo_form" : SampleInfoUploadForm(),
                "bacscout_form": BactScoutUploadForm(),
                "gtdbtk_form": GtdbTkUploadForm(),
                "raw_antibiotic_form": RawAntibioticUploadForm(),
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
                    WGS_SampleInfoSummary=False,
                    WGS_BactScoutSummary=False,
                    WGS_GtdbTkSummary=False,
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
        "demogs_form": DemogsDataUploadForm(),
        "antibiotic_form": FinalAntibioticUploadForm(),
        "sampleinfo_form" : SampleInfoUploadForm(),
        "bacscout_form": BactScoutUploadForm(),
        "gtdbtk_form": GtdbTkUploadForm(),
        "raw_antibiotic_form": RawAntibioticUploadForm(),
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
                "demogs_form": DemogsDataUploadForm(),
                "antibiotic_form": FinalAntibioticUploadForm(),
                "sampleinfo_form" : SampleInfoUploadForm(),
                "bacscout_form": BactScoutUploadForm(),
                "gtdbtk_form": GtdbTkUploadForm(),
                "raw_antibiotic_form": RawAntibioticUploadForm(),
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
                WGS_SampleInfoSummary=False,
                WGS_BactScoutSummary=False,
                WGS_GtdbTkSummary=False,
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
        "demogs_form": DemogsDataUploadForm(),
        "antibiotic_form": FinalAntibioticUploadForm(),
        "sampleinfo_form" : SampleInfoUploadForm(),
        "bacscout_form": BactScoutUploadForm(),
        "gtdbtk_form": GtdbTkUploadForm(),
        "raw_antibiotic_form": RawAntibioticUploadForm(),
        "editing": editing,
    })




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




############## Sample Information
@login_required
def upload_sample_information(request):

    form = WGSProjectForm()
    sampleinfo_form = SampleInfoUploadForm()
    editing = False

    if request.method == "POST" and request.FILES.get("sampleinfo"):

        sampleinfo_form = SampleInfoUploadForm(request.POST, request.FILES)

        try:
            upload = sampleinfo_form.save()

            df = read_uploaded_file(upload.sampleinfo)

            df.columns = df.columns.str.strip().str.replace(".", "", regex=False)

        except Exception as e:

            messages.error(request, f"Error processing Sample Information file: {e}")

            return render(request, "wgs_app/Add_wgs.html", {
                "form": form,
                "sampleinfo_form": sampleinfo_form,
                "fastq_form": FastqUploadForm(),
                "gambit_form": GambitUploadForm(),
                "mlst_form": MlstUploadForm(),
                "checkm2_form": Checkm2UploadForm(),
                "amrfinder_form": AmrUploadForm(),
                "assembly_form": AssemblyUploadForm(),
                "demogs_form": DemogsDataUploadForm(),
                "antibiotic_form": FinalAntibioticUploadForm(),
                "bacscout_form": BactScoutUploadForm(),
                "gtdbtk_form": GtdbTkUploadForm(),
                "raw_antibiotic_form": RawAntibioticUploadForm(),
                "editing": editing,
            })

        site_codes = set(SiteData.objects.values_list("SiteCode", flat=True))

        # Same extraction logic used in Assembly
        def format_sample_accession(raw_name: str) -> str:

            if not raw_name:
                return ""

            base = os.path.basename(raw_name)

            base_noext = os.path.splitext(base)[0].strip()

            if "ARS" not in base_noext:
                return ""

            parts = re.split(r"[-_]", base_noext)

            if not parts:
                return ""

            prefix = parts[0]

            for part in parts[1:]:

                m = re.match(r"^([A-Za-z]{2,6})(\d+)", part)

                if m:

                    letters = m.group(1).upper()

                    digits = m.group(2)

                    if letters in site_codes:
                        return f"{prefix}_{letters}{digits}"

            for i in range(1, len(parts) - 1):

                if parts[i].upper() in site_codes:

                    letters = parts[i].upper()

                    digits_match = re.search(r"(\d+)", parts[i + 1])

                    if digits_match:
                        return f"{prefix}_{letters}{digits_match.group(1)}"

                    return f"{prefix}_{letters}"

            return ""

        # Process rows
        for _, row in df.iterrows():

            sample_name = str(row.get("sample_name", "")).strip()

            sample_accession = format_sample_accession(sample_name)

            referred_obj = (
                Final_Data.objects.filter(f_AccessionNo=sample_accession).first()
                if sample_accession else None
            )

            connect_project = WGS_Project.objects.create(
                Ref_Accession=referred_obj if referred_obj else None,
                WGS_SampleInfoSummary=False,
                WGS_BactScoutSummary=False,
                WGS_GtdbTkSummary=False,
                WGS_GambitSummary=False,
                WGS_FastqSummary=False,
                WGS_MlstSummary=False,
                WGS_Checkm2Summary=False,
                WGS_AssemblySummary=False,
                WGS_AmrfinderSummary=False,
            )

            connect_project.save()

            SampleInformation.objects.create(
                sample_project=connect_project,
                sample_accession=sample_accession,
                batch_code=row.get("batch_code", ""),
                sample_name=sample_name,
                status=row.get("status", ""),
                emerging=row.get("emerging", False),
                structured=row.get("structured", False),
                satscan=row.get("satscan", False),
                serotyping=row.get("serotyping", False),
                ghru=row.get("ghru", False),
                egasp=row.get("egasp", False),
                tricycle=row.get("tricycle", False),
                pulsenet=row.get("pulsenet", False),
                tulip=row.get("tulip", False),
            )

        messages.success(request, "Sample Information records uploaded successfully.")

        return redirect("show_sample_information")

    return render(request, "wgs_app/Add_wgs.html", {

        "form": form,
        "sampleinfo_form": sampleinfo_form,
        "bacscout_form": BactScoutUploadForm(),
        "gtdbtk_form" : GtdbTkUploadForm(),
        "fastq_form": FastqUploadForm(),
        "gambit_form": GambitUploadForm(),
        "mlst_form": MlstUploadForm(),
        "checkm2_form": Checkm2UploadForm(),
        "amrfinder_form": AmrUploadForm(),
        "assembly_form": AssemblyUploadForm(),
        "demogs_form": DemogsDataUploadForm(),
        "antibiotic_form": FinalAntibioticUploadForm(),
        "raw_antibiotic_form": RawAntibioticUploadForm(),
        "editing": editing,
    })






@login_required
def show_sample_information(request):

    records = SampleInformation.objects.all().order_by('-Date_uploaded_si')

    upload_dates = (
        SampleInformation.objects
        .exclude(Date_uploaded_si__isnull=True)
        .values_list('Date_uploaded_si', flat=True)
        .distinct()
        .order_by('-Date_uploaded_si')
    )

    total_records = SampleInformation.objects.count()

    paginator = Paginator(records, 20)

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    return render(request, "wgs_app/show_sampleinfo.html", {

        "page_obj": page_obj,

        "upload_dates": upload_dates,

        "total_records": total_records,

    })



@login_required
def delete_sample_information(request, pk):

    item = get_object_or_404(SampleInformation, pk=pk)

    if request.method == "POST":

        item.delete()

        messages.success(
            request,
            f"Sample {item.sample_name} deleted successfully!"
        )

        return redirect("show_sample_information")

    messages.error(request, "Invalid request.")

    return redirect("show_sample_information")



@login_required
def delete_all_sample_information(request):

    deleted_count, _ = SampleInformation.objects.all().delete()

    messages.success(
        request,
        f"{deleted_count} Sample Information records deleted successfully."
    )

    return redirect("show_sample_information")


@login_required
def delete_sample_information_by_date(request):

    if request.method == "POST":

        upload_date_str = request.POST.get("upload_date")

        if not upload_date_str:

            messages.error(request, "Please select a date.")

            return redirect("show_sample_information")

        upload_date = parse_date(upload_date_str)

        if not upload_date:

            messages.error(request, "Invalid date format.")

            return redirect("show_sample_information")

        deleted_count, _ = SampleInformation.objects.filter(
            Date_uploaded_si=upload_date
        ).delete()

        messages.success(
            request,
            f"Deleted {deleted_count} records uploaded on {upload_date}."
        )

        return redirect("show_sample_information")

    messages.error(request, "Invalid request method.")

    return redirect("show_sample_information")


################## Bactscout
@login_required
def upload_bactscout(request):

    form = WGSProjectForm()
    bactscout_form = BactScoutUploadForm()
    editing = False

    if request.method == "POST" and request.FILES.get("bactscoutfile"):

        bactscout_form = BactScoutUploadForm(request.POST, request.FILES)

        try:
            upload = bactscout_form.save()
            df = read_uploaded_file(upload.bactscoutfile)

            df.columns = df.columns.str.strip().str.replace(".", "", regex=False)

        except Exception as e:

            messages.error(request, f"Error processing BactScout file: {e}")

            return render(request, "wgs_app/Add_wgs.html", {
                "form": form,
                "sampleinfo_form": SampleInfoUploadForm(),
                "fastq_form": FastqUploadForm(),
                "bacscout_form": bactscout_form,
                "gtdbtk_form" : GtdbTkUploadForm(),
                "gambit_form": GambitUploadForm(),
                "mlst_form": MlstUploadForm(),
                "checkm2_form": Checkm2UploadForm(),
                "amrfinder_form": AmrUploadForm(),
                "assembly_form": AssemblyUploadForm(),
                "demogs_form": DemogsDataUploadForm(),
                "antibiotic_form": FinalAntibioticUploadForm(),
                "raw_antibiotic_form": RawAntibioticUploadForm(),
                "editing": editing,
            })

        site_codes = set(SiteData.objects.values_list("SiteCode", flat=True))

        # accession extractor
        def format_bactscout_accession(raw_name: str):

            if not raw_name:
                return ""

            base = os.path.basename(raw_name)
            base_noext = os.path.splitext(base)[0].strip()

            if "ARS" not in base_noext:
                return ""

            parts = re.split(r"[-_]", base_noext)

            if not parts:
                return ""

            prefix = parts[0]

            for part in parts[1:]:

                m = re.match(r"^([A-Za-z]{2,6})(\d+)", part)

                if m:

                    letters = m.group(1).upper()
                    digits = m.group(2)

                    if letters in site_codes:
                        return f"{prefix}_{letters}{digits}"

            for i in range(1, len(parts) - 1):

                if parts[i].upper() in site_codes:

                    letters = parts[i].upper()

                    digits_match = re.search(r"(\d+)", parts[i + 1])

                    if digits_match:
                        return f"{prefix}_{letters}{digits_match.group(1)}"

                    return f"{prefix}_{letters}"

            return ""

        for _, row in df.iterrows():

            name = str(row.get("name", "")).strip()

            bactscout_accession = format_bactscout_accession(name)

            referred_obj = (
                Final_Data.objects.filter(f_AccessionNo=bactscout_accession).first()
                if bactscout_accession else None
            )

            connect_project = WGS_Project.objects.create(
                Ref_Accession=referred_obj if referred_obj else None,
                WGS_SampleInfoSummary=False,
                WGS_BactScoutSummary=False,
                WGS_GtdbTkSummary=False,
                WGS_GambitSummary=False,
                WGS_FastqSummary=False,
                WGS_MlstSummary=False,
                WGS_Checkm2Summary=False,
                WGS_AssemblySummary=False,
                WGS_AmrfinderSummary=False,
            )

            connect_project.save()

            BactScout.objects.create(

                bactscout_project=connect_project,

                BactScout_Accession=bactscout_accession,

                name=name,

                status=row.get("status"),

                completeness=row.get("completeness"),
                contamination=row.get("contamination"),
                completeness_model_used=row.get("completeness_model_used"),
                translation_table_used=row.get("translation_table_used"),
                coding_density=row.get("coding_density"),
                contig_n50=row.get("contig_n50"),
                average_gene_length=row.get("average_gene_length"),
                genome_size=row.get("genome_size"),
                checkm2_gc_content=row.get("checkm2_gc_content"),
                total_coding_sequences=row.get("total_coding_sequences"),
                total_contigs=row.get("total_contigs"),
                max_contig_length=row.get("max_contig_length"),
                additional_notes=row.get("additional_notes"),

                a_final_status=row.get("a_final_status"),
                adapter_detection_status=row.get("adapter_detection_status"),
                contamination_status=row.get("contamination_status"),
                species_status=row.get("species_status"),
                coverage_status=row.get("coverage_status"),
                coverage_estimate_qualibact_status=row.get("coverage_estimate_qualibact_status"),
                duplication_status=row.get("duplication_status"),
                gc_content_status=row.get("gc_content_status"),
                mlst_status=row.get("mlst_status"),
                n_content_status=row.get("n_content_status"),
                read_length_status=row.get("read_length_status"),
                read_q30_status=row.get("read_q30_status"),

                species=row.get("species"),
                species_abundance=row.get("species_abundance"),
                species_coverage=row.get("species_coverage"),
                species_message=row.get("species_message"),

                contamination_message=row.get("contamination_message"),

                coverage_estimate_sylph=row.get("coverage_estimate_sylph"),
                coverage_estimate_sylph_message=row.get("coverage_estimate_sylph_message"),
                coverage_estimate_qualibact=row.get("coverage_estimate_qualibact"),
                coverage_estimate_qualibact_message=row.get("coverage_estimate_qualibact_message"),

                duplication_rate=row.get("duplication_rate"),
                duplication_message=row.get("duplication_message"),

                gc_content=row.get("gc_content"),
                gc_content_lower=row.get("gc_content_lower"),
                gc_content_upper=row.get("gc_content_upper"),
                gc_content_message=row.get("gc_content_message"),

                n_content_rate=row.get("n_content_rate"),
                n_content_message=row.get("n_content_message"),

                mlst_st=row.get("mlst_st"),
                mlst_message=row.get("mlst_message"),

                read1_mean_length=row.get("read1_mean_length"),
                read2_mean_length=row.get("read2_mean_length"),
                read_length_message=row.get("read_length_message"),

                read_q20_bases=row.get("read_q20_bases"),
                read_q20_rate=row.get("read_q20_rate"),
                read_q30_bases=row.get("read_q30_bases"),
                read_q30_rate=row.get("read_q30_rate"),
                read_q30_message=row.get("read_q30_message"),
                read_total_bases=row.get("read_total_bases"),
                read_total_reads=row.get("read_total_reads"),

                adapter_detection_message=row.get("adapter_detection_message"),

                ref_genome=row.get("ref_genome"),
                genome_size_expected=row.get("genome_size_expected"),
            )

        messages.success(request, "BactScout records uploaded successfully.")

        return redirect("show_bactscout")

    return render(request, "wgs_app/Add_wgs.html", {

        "form": form,
        "sampleinfo_form": SampleInfoUploadForm(),
        "bacscout_form": bactscout_form,
        "gtdbtk_form" : GtdbTkUploadForm(),
        "fastq_form": FastqUploadForm(),
        "gambit_form": GambitUploadForm(),
        "mlst_form": MlstUploadForm(),
        "checkm2_form": Checkm2UploadForm(),
        "amrfinder_form": AmrUploadForm(),
        "assembly_form": AssemblyUploadForm(),
        "demogs_form": DemogsDataUploadForm(),
        "antibiotic_form": FinalAntibioticUploadForm(),
        "raw_antibiotic_form": RawAntibioticUploadForm(),
        "editing": editing,

    })


@login_required
def show_bactscout(request):

    records = BactScout.objects.all().order_by('-Date_uploaded_bs')

    upload_dates = (
        BactScout.objects.exclude(Date_uploaded_bs__isnull=True)
        .values_list('Date_uploaded_bs', flat=True)
        .distinct()
        .order_by('-Date_uploaded_bs')
    )

    total_records = BactScout.objects.count()

    paginator = Paginator(records, 20)

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    return render(request, "wgs_app/show_bactscout.html", {

        "page_obj": page_obj,
        "upload_dates": upload_dates,
        "total_records": total_records,

    })


@login_required
def delete_bactscout(request, pk):

    item = get_object_or_404(BactScout, pk=pk)

    if request.method == "POST":

        item.delete()

        messages.success(request, f"Record {item.name} deleted successfully!")

        return redirect("show_bactscout")

    messages.error(request, "Invalid request.")

    return redirect("show_bactscout")


@login_required
def delete_all_bactscout(request):

    deleted_count, _ = BactScout.objects.all().delete()

    messages.success(request, f"{deleted_count} BactScout records deleted.")

    return redirect("show_bactscout")



@login_required
def delete_bactscout_by_date(request):

    if request.method == "POST":

        upload_date_str = request.POST.get("upload_date")

        if not upload_date_str:
            messages.error(request, "Please select an upload date.")
            return redirect("show_bactscout")

        upload_date = parse_date(upload_date_str)

        if not upload_date:
            messages.error(request, "Invalid date format.")
            return redirect("show_bactscout")

        deleted_count, _ = BactScout.objects.filter(
            Date_uploaded_bs=upload_date
        ).delete()

        messages.success(
            request,
            f"Deleted {deleted_count} records uploaded on {upload_date}."
        )

        return redirect("show_bactscout")

    messages.error(request, "Invalid request.")

    return redirect("show_bactscout")

############## GtdbTk 

@login_required
def upload_gtdbtk(request):

    form = WGSProjectForm()
    gtdbtk_form = GtdbTkUploadForm()
    editing = False

    if request.method == "POST" and request.FILES.get("GtdbTkFile"):

        gtdbtk_form = GtdbTkUploadForm(request.POST, request.FILES)

        try:
            upload = gtdbtk_form.save()
            df = read_uploaded_file(upload.GtdbTkFile)

            df.columns = df.columns.str.strip().str.replace(".", "", regex=False)

        except Exception as e:

            messages.error(request, f"Error processing GTDB-Tk file: {e}")

            return render(request, "wgs_app/Add_wgs.html", {
            "form": form,
            "sampleinfo_form": SampleInfoUploadForm(),
            "bacscout_form": BactScoutUploadForm(),
            "gtdbtk_form" : gtdbtk_form,
            "fastq_form": FastqUploadForm(),
            "gambit_form": GambitUploadForm(),
            "mlst_form": MlstUploadForm(),
            "checkm2_form": Checkm2UploadForm(),
            "amrfinder_form": AmrUploadForm(),
            "assembly_form": AssemblyUploadForm(),
            "demogs_form": DemogsDataUploadForm(),
            "antibiotic_form": FinalAntibioticUploadForm(),
            "raw_antibiotic_form": RawAntibioticUploadForm(),
            "editing": editing,

            })

        site_codes = set(SiteData.objects.values_list("SiteCode", flat=True))

        # accession extractor
        def format_gtdbtk_accession(raw_name: str):

            if not raw_name:
                return ""

            base = os.path.basename(raw_name)
            base_noext = os.path.splitext(base)[0].strip()

            if "ARS" not in base_noext:
                return ""

            parts = re.split(r"[-_]", base_noext)

            if not parts:
                return ""

            prefix = parts[0]

            for part in parts[1:]:

                m = re.match(r"^([A-Za-z]{2,6})(\d+)", part)

                if m:

                    letters = m.group(1).upper()
                    digits = m.group(2)

                    if letters in site_codes:
                        return f"{prefix}_{letters}{digits}"

            for i in range(1, len(parts) - 1):

                if parts[i].upper() in site_codes:

                    letters = parts[i].upper()

                    digits_match = re.search(r"(\d+)", parts[i + 1])

                    if digits_match:
                        return f"{prefix}_{letters}{digits_match.group(1)}"

                    return f"{prefix}_{letters}"

            return ""

        for _, row in df.iterrows():

            user_genome = str(row.get("user_genome", "")).strip()

            gtdbtk_accession = format_gtdbtk_accession(user_genome)

            referred_obj = (
                Final_Data.objects.filter(f_AccessionNo=gtdbtk_accession).first()
                if gtdbtk_accession else None
            )

            connect_project = WGS_Project.objects.create(
                Ref_Accession=referred_obj if referred_obj else None,
                WGS_SampleInfoSummary=False,
                WGS_BactScoutSummary=False,
                WGS_GtdbTkSummary=False,
                WGS_GambitSummary=False,
                WGS_FastqSummary=False,
                WGS_MlstSummary=False,
                WGS_Checkm2Summary=False,
                WGS_AssemblySummary=False,
                WGS_AmrfinderSummary=False,
            )

            connect_project.save()

            GtdbTk.objects.create(

                gtdbtk_project=connect_project,

                GtdbTk_Accession=gtdbtk_accession,

                user_genome=user_genome,
                classification=row.get("classification"),

                closest_genome_reference=row.get("closest_genome_reference"),
                closest_genome_reference_radius=row.get("closest_genome_reference_radius"),
                closest_genome_taxonomy=row.get("closest_genome_taxonomy"),
                closest_genome_ani=row.get("closest_genome_ani"),
                closest_genome_af=row.get("closest_genome_af"),

                closest_placement_reference=row.get("closest_placement_reference"),
                closest_placement_radius=row.get("closest_placement_radius"),
                closest_placement_taxonomy=row.get("closest_placement_taxonomy"),
                closest_placement_ani=row.get("closest_placement_ani"),
                closest_placement_af=row.get("closest_placement_af"),

                pplacer_taxonomy=row.get("pplacer_taxonomy"),
                classification_method=row.get("classification_method"),
                note=row.get("note"),
                other_related_references=row.get("other_related_references"),
                msa_percent=row.get("msa_percent"),
                translation_table=row.get("translation_table"),
                red_value=row.get("red_value"),
                warnings=row.get("warnings"),
            )

        messages.success(request, "GTDB-Tk records uploaded successfully.")

        return redirect("show_gtdbtk")

    return render(request, "wgs_app/Add_wgs.html", {

        "form": form,
        "sampleinfo_form": SampleInfoUploadForm(),
        "bacscout_form": BactScoutUploadForm(),
        "gtdbtk_form" : gtdbtk_form,
        "fastq_form": FastqUploadForm(),
        "gambit_form": GambitUploadForm(),
        "mlst_form": MlstUploadForm(),
        "checkm2_form": Checkm2UploadForm(),
        "amrfinder_form": AmrUploadForm(),
        "assembly_form": AssemblyUploadForm(),
        "demogs_form": DemogsDataUploadForm(),
        "antibiotic_form": FinalAntibioticUploadForm(),
        "raw_antibiotic_form": RawAntibioticUploadForm(),
        "editing": editing,


    })



@login_required
def show_gtdbtk(request):

    records = GtdbTk.objects.all().order_by('-Date_uploaded_gt')

    upload_dates = (
        GtdbTk.objects.exclude(Date_uploaded_gt__isnull=True)
        .values_list('Date_uploaded_gt', flat=True)
        .distinct()
        .order_by('-Date_uploaded_gt')
    )

    total_records = GtdbTk.objects.count()

    paginator = Paginator(records, 20)

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    return render(request, "wgs_app/show_gtdbtk.html", {

        "page_obj": page_obj,
        "upload_dates": upload_dates,
        "total_records": total_records,

    })


@login_required
def delete_gtdbtk(request, pk):

    item = get_object_or_404(GtdbTk, pk=pk)

    if request.method == "POST":

        item.delete()

        messages.success(request, f"Record {item.user_genome} deleted successfully!")

        return redirect("show_gtdbtk")

    messages.error(request, "Invalid request.")

    return redirect("show_gtdbtk")


@login_required
def delete_all_gtdbtk(request):

    deleted_count, _ = GtdbTk.objects.all().delete()

    messages.success(request, f"{deleted_count} GTDB-Tk records deleted.")

    return redirect("show_gtdbtk")


@login_required
def delete_gtdbtk_by_date(request):

    if request.method == "POST":

        upload_date_str = request.POST.get("upload_date")

        if not upload_date_str:
            messages.error(request, "Please select an upload date.")
            return redirect("show_gtdbtk")

        upload_date = parse_date(upload_date_str)

        if not upload_date:
            messages.error(request, "Invalid date format.")
            return redirect("show_gtdbtk")

        deleted_count, _ = GtdbTk.objects.filter(
            Date_uploaded_gt=upload_date
        ).delete()

        messages.success(
            request,
            f"Deleted {deleted_count} records uploaded on {upload_date}."
        )

        return redirect("show_gtdbtk")

    messages.error(request, "Invalid request.")

    return redirect("show_gtdbtk")


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
    q = request.GET.get("q", "").strip()

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
    ).filter(
        f_AccessionNo__in=wgs_accessions
    )

    if q:
        referred_list = referred_list.filter(
            Q(f_AccessionNo__icontains=q) |
            Q(f_Patient_ID__icontains=q) |
            Q(f_Last_Name__icontains=q) |
            Q(f_First_Name__icontains=q) |
            Q(f_ars_OrgCode__icontains=q) |
            Q(f_SiteCode__icontains=q)
        )

    referred_list = referred_list.order_by("f_AccessionNo")



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
        "q": q,
    })




# View WGS overview with antibiotic entries but optimized to reduce queries
# Shows isolates that have WGS data in ANY of the WGS tables

@login_required
def get_wgs_details(request, accession):
    print(f"\n=== FETCHING DETAILS FOR ACCESSION: {accession} ===")

    # Fetch the referred isolate
    referred = Final_Data.objects.filter(f_AccessionNo=accession).first()
    if not referred:
        return JsonResponse({"error": "Accession not found."}, status=404)

    # ============================================================
    # ✔ FIX: Convert antibiotic entries to SAFE dictionary format
    # ============================================================
    antibiotics_qs = Final_AntibioticEntry.objects.filter(
        ab_idNum_f_referred__f_AccessionNo=accession
    ).only(
        "ab_Abx_code",
        "ab_Disk_value", "ab_Disk_enRIS",
        "ab_MIC_value", "ab_MIC_enRIS",
        "ab_MIC_operand",
    )

    antibiotics = []
    for ab in antibiotics_qs:
        antibiotics.append({
            "code": ab.ab_Abx_code,

            # Disk
            "disk": ab.ab_Disk_value or "",
            "d_ris": ab.ab_Disk_enRIS or "",

            # MIC
            "mic": ab.ab_MIC_value or "",
            "m_ris": ab.ab_MIC_enRIS or "",
            "m_op": ab.ab_MIC_operand or "",
        })

    print(f" Found {len(antibiotics)} antibiotic entries (SAFE FORMAT)")

    # ============================================================
    # WGS Related Data
    # ============================================================
    projects = WGS_Project.objects.filter(
        Q(WGS_FastQ_Acc=accession)
        | Q(WGS_FastQ_Acc=accession)
        | Q(WGS_Mlst_Acc=accession)
        | Q(WGS_Checkm2_Acc=accession)
        | Q(WGS_Assembly_Acc=accession)
        | Q(WGS_Gambit_Acc=accession)
        | Q(WGS_Amrfinder_Acc=accession)
    ).distinct()

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

    # ============================================================
    # Build context required by the template
    # ============================================================
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

    # Render HTML for AJAX response
    html = render_to_string(
        "wgs_app/Wgs_detail.html",
        context,
        request=request,
    )

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
    abx_df["ab_idNum_f_referred_id"] = abx_df["ab_idNum_f_referred_id"].astype(str)
    final_df["id"] = final_df["id"].astype(str)

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


@login_required
def projects_page(request):

    active_tab = request.GET.get("tab", "wgs_classification")

    referred_list = (
        Referred_Data.objects
        .all()
        .order_by("-Date_Modified", "-id")
    )

    context = {
        "active_tab":      active_tab,
        "referred_list":   referred_list,

        # WGS upload forms — passed to the modal forms rendered inside the tab
        "fastq_form":      FastqUploadForm(),
        "gambit_form":     GambitUploadForm(),
        "mlst_form":       MlstUploadForm(),
        "checkm2_form":    Checkm2UploadForm(),
        "assembly_form":   AssemblyUploadForm(),
        "amrfinder_form":  AmrUploadForm(),
    }
    return render(request, "projects/projects.html", context)





##############################  New Upload Final View HELPERS



# ─────────────────────────────────────────────────────────────────────────────
# MAIN UPLOAD VIEW
# ─────────────────────────────────────────────────────────────────────────────
#######  refrain from using this until i polished it
@login_required
@require_POST
def upload_final_data(request):
    """
    POST — receives a multipart Excel file (.xlsx) and saves rows into
    Final_Data and Final_AntibioticEntry (retest antibiotic entries only).

    Returns JSON: { success, created, updated, skipped, errors }
    """
    f = request.FILES.get("final_data_file")
    if not f:
        return JsonResponse({"success": False, "error": "No file uploaded."}, status=400)

    overwrite = request.POST.get("overwrite", "false").lower() == "true"

    try:
        wb = openpyxl.load_workbook(f, read_only=True, data_only=True)
    except Exception as e:
        return JsonResponse({"success": False, "error": f"Cannot open file: {e}"}, status=400)

    results = {"created": 0, "updated": 0, "skipped": 0, "errors": []}

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            continue

        headers = rows[0]
        h_lower = [str(c).lower().strip() if c else "" for c in headers]
        col     = {name: idx for idx, name in enumerate(h_lower) if name}

        if 'accession_no' not in col:
            continue  # sheet has no required column — skip

        # Detect retest antibiotic column groups once per sheet
        abx_groups = _parse_abx_columns(headers)

        for row_num, row in enumerate(rows[1:], start=2):

            accession_no = _clean(row[col['accession_no']])
            if not accession_no:
                continue

            # ── Helper: safe column read ──────────────────────────────────────
            def g(key, default=""):
                return _clean(row[col[key]], default) if key in col else default

            # ── Final_Data fields ─────────────────────────────────────────────
            fd_kwargs = {
                "f_AccessionNo":     accession_no,
                "f_Batch_Code":      g('batch_code'),
                "f_Batch_Name":      g('batch_name'),
                "f_SiteCode":        g('site_code'),
                "f_BatchNo":         g('batchno'),
                "f_Total_batch":     g('total_batch'),
                "f_RefNo":           g('refno'),
                "f_Referral_Date":   _date(row[col['referral_date']]) if 'referral_date' in col else None,
                # patient
                "f_Patient_ID":      g('patient_id'),
                "f_First_Name":      g('first_name'),
                "f_Mid_Name":        g('mid_name'),
                "f_Last_Name":       g('last_name'),
                "f_Date_Birth":      _date(row[col['date_birth']]) if 'date_birth' in col else None,
                "f_Age":             _int(row[col['age']]) if 'age' in col else None,
                "f_Sex":             g('sex', 'n/a'),
                "f_Date_Admis":      _date(row[col['date_admis']]) if 'date_admis' in col else None,
                "f_Nosocomial":      g('nosocomial', 'n/a'),
                "f_Diagnosis":       g('diagnosis'),
                "f_Diagnosis_ICD10": g('diagnosis_icd10'),
                "f_Ward":            g('ward'),
                "f_Ward_Type":       g('ward_type'),
                "f_Service_Type":    g('service_type', 'n/a'),
                # specimen
                "f_Spec_Num":        g('spec_num'),
                "f_Spec_Date":       _date(row[col['spec_date']]) if 'spec_date' in col else None,
                "f_Reason":          g('reason', 'n/a'),
                "f_Growth":          g('growth'),
                "f_Urine_ColCt":     g('urine_colct'),
                # organism (ARSRL)
                "f_ars_Pre":         g('arsrl_pre'),
                "f_ars_OrgName":     g('arsrl_org'),
                "f_ars_OrgCode":     g('organismcode'),
                "f_ars_Post":        g('arsrl_post'),
                # extra
                "f_x_mrse":          g('x_mrse'),
                "f_x_mrsamrse":      g('x_mrsamrse'),
                "f_x_entbac":        g('x_entbac'),
                "f_edta":            g('edta'),
                "f_ars_ct_ctl":      g('ct.ctl'),
                "f_ars_tz_tzl":      g('tz.tzl'),
                "f_ars_cn_cni":      g('cn.cni'),
                "f_ars_ip_ipi":      g('ip.ipi'),
                "f_Comments":        g('comments'),
                "f_ars_reco":        g('recommendation'),
            }

            # Phenotype fields
            for excel_key, model_field in PHENO_FIELD_MAP.items():
                if excel_key in col:
                    fd_kwargs[model_field] = _pheno(row[col[excel_key]])
            for excel_key, model_field in SITE_PHENO_MAP.items():
                if excel_key in col:
                    fd_kwargs[model_field] = _pheno(row[col[excel_key]])

            # Resolve SpecimenType FK
            spec_type_code = g('spec_type')
            if spec_type_code:
                fd_kwargs["f_Spec_Type"] = SpecimenTypeModel.objects.filter(
                    Specimen_code__iexact=spec_type_code
                ).first()

            # Resolve Batch FK
            if fd_kwargs["f_Batch_Code"]:
                batch_obj = Batch_Table.objects.filter(
                    bat_Batch_Code=fd_kwargs["f_Batch_Code"]
                ).first()
                if batch_obj:
                    fd_kwargs["f_Batch_id"] = batch_obj

            # ── Persist Final_Data ────────────────────────────────────────────
            try:
                with transaction.atomic():
                    existing = Final_Data.objects.filter(
                        f_AccessionNo=accession_no
                    ).first()

                    if existing and not overwrite:
                        results["skipped"] += 1
                        continue

                    if existing:
                        for k, v in fd_kwargs.items():
                            if k != "f_AccessionNo":
                                setattr(existing, k, v)
                        existing.save()
                        isolate = existing
                        results["updated"] += 1
                    else:
                        isolate = Final_Data(**fd_kwargs)
                        isolate.save()
                        results["created"] += 1

                    # ── Effective breakpoint year (same logic as edit view) ────
                    effective_year   = _resolve_effective_year(isolate.f_Spec_Date)
                    # ── ARSRL organism code for breakpoint lookup ─────────────
                    resolved_ars_org = (isolate.f_ars_OrgCode or "").strip()

                    # ── Remove old retest entries on overwrite ────────────────
                    if existing and overwrite:
                        Final_AntibioticEntry.objects.filter(
                            ab_idNum_f_referred=isolate,
                            ab_Retest_Abx_code__isnull=False,
                        ).exclude(ab_Retest_Abx_code="").delete()

                    # ── Save one retest entry per antibiotic with data ─────────
                    for abx_code, grp in abx_groups.items():

                        disk_raw = row[grp['disk_col']]  if grp['disk_col']  is not None else None
                        disk_ris = _clean(row[grp['disk_ris_col']]) if grp['disk_ris_col'] is not None else ""
                        mic_raw  = row[grp['mic_col']]   if grp['mic_col']   is not None else None
                        mic_ris  = _clean(row[grp['mic_ris_col']])  if grp['mic_ris_col']  is not None else ""

                        # Skip entirely empty antibiotic columns
                        if all(
                            v is None or _clean(v) == ""
                            for v in [disk_raw, disk_ris, mic_raw, mic_ris]
                        ):
                            continue

                        disk_int              = _int(disk_raw)
                        mic_value, mic_operand = _decimal(mic_raw)

                        # Nothing numeric to save
                        if disk_int is None and mic_value is None:
                            continue

                        _save_retest_entry(
                            isolate          = isolate,
                            abx_code         = abx_code,
                            disk_int         = disk_int,
                            disk_ris         = disk_ris,
                            mic_value        = mic_value,
                            mic_operand      = mic_operand,
                            mic_ris          = mic_ris,
                            resolved_ars_org = resolved_ars_org,
                            effective_year   = effective_year,
                        )

            except Exception as e:
                results["errors"].append({
                    "row":       row_num,
                    "accession": accession_no,
                    "sheet":     sheet_name,
                    "error":     str(e),
                })

    wb.close()
    results["success"] = True
    return JsonResponse(results)






########### uploading of Final Data - Demographics 


## new version aligns with the new final data model


def parse_int(val):

    if val is None:
        return None

    s = str(val).strip().lower()

    if s in {"", "nan", "none"}:
        return None

    # extract numeric portion (10d → 10)
    match = re.search(r"\d+", s)

    if match:
        return int(match.group())

    return None



# @login_required
# @transaction.atomic
# def upload_final_combined_table(request):



#     if request.method == "POST" and request.FILES.get("DemogsDataFile"):


#         try:

#             uploaded_file = request.FILES["DemogsDataFile"]
#             file_name = uploaded_file.name.lower()

#             # ================= LOAD FILE =================
#             if file_name.endswith(".csv"):
#                 df = pd.read_csv(uploaded_file)

#             elif file_name.endswith((".xlsx", ".xls")):
#                 df = pd.read_excel(uploaded_file)

#             else:
#                 messages.error(request, "Unsupported file format.")
#                 return redirect("upload_final_combined_table")

#             # ================= PREP DATA =================
#             df.columns = [str(c).strip() for c in df.columns]
#             rows = df.to_dict("records")

#             model_fields = {f.name for f in Final_Data._meta.fields}

#             IMMUTABLE_FIELDS = {
#                 "f_Date_of_Entry",
#                 "f_Date_Modified",
#             }

#             INT_FIELDS = {
#                 "f_Age",
#                 "f_bat_seq",
#             }

#             created = 0
#             updated = 0

#             # ================= FK LOOKUP CACHE =================
#             specimen_map = {
#                 str(s.Specimen_code).strip().lower(): s
#                 for s in SpecimenTypeModel.objects.all()
#             }

#             site_map = {
#                 str(s.SiteCode).strip().upper(): s.SiteName
#                 for s in SiteData.objects.all()
#             }

#             # ================= HELPERS =================
#             def parse_date(val):

#                 if not val or str(val).lower() in {"nan", "nat", "none", ""}:
#                     return None

#                 dt = pd.to_datetime(val, errors="coerce")
#                 return None if pd.isna(dt) else dt.date()

#             # ================= PROCESS ROWS =================
#             for row in rows:

#                 accession = str(row.get("f_AccessionNo", "")).strip()
#                 batch_code = str(row.get("f_Batch_Code", "")).strip()

#                 if not accession or not batch_code:
#                     continue

#                 # ---- normalize accession
#                 accession = accession.upper()

#                 # ---- parse date fields
#                 for d in (
#                     "f_Referral_Date",
#                     "f_Spec_Date",
#                     "f_Date_Birth",
#                     "f_Date_Admis",
#                 ):
#                     if d in row:
#                         row[d] = parse_date(row[d])

#                 # ---- keep ONLY Final_Data fields
#                 clean_row = {
#                     k: v
#                     for k, v in row.items()
#                     if k in model_fields and k not in IMMUTABLE_FIELDS
#                 }

#                 # ---- normalize integers
#                 for f in INT_FIELDS:
#                     if f in clean_row:
#                         clean_row[f] = parse_int(clean_row[f])

#                 # ================= FK RESOLUTION =================

#                 # Specimen Type FK
#                 if "f_Spec_Type" in clean_row:

#                     raw_val = clean_row["f_Spec_Type"]

#                     if pd.isna(raw_val) or raw_val is None:
#                         clean_row["f_Spec_Type"] = None

#                     else:
#                         spec_val = str(raw_val).strip().lower()
#                         clean_row["f_Spec_Type"] = specimen_map.get(spec_val)

                
#                 # ================= SITE NAME AUTO ASSIGN =================
#                 site_code = str(clean_row.get("f_SiteCode", "")).strip().upper()

#                 if site_code:
#                     clean_row["f_Site_Name"] = site_map.get(site_code, "")


#                 # NEVER assign batch FK directly
#                 clean_row.pop("f_Batch_id", None)

#                 # ================= UPSERT =================
#                 obj, is_created = Final_Data.objects.update_or_create(
#                     f_AccessionNo=accession,
#                     f_Batch_Code=batch_code,
#                     defaults=clean_row
#                 )

#                 created += int(is_created)
#                 updated += int(not is_created)

#             # ================= SUCCESS =================
#             messages.success(
#                 request,
#                 f"Upload complete! {created} created, {updated} updated."
#             )

#             return redirect("show_final_data")

#         except Exception as e:

#             import traceback
#             traceback.print_exc()

#             messages.error(request, f"Upload failed: {e}")
#             return redirect("upload_final_combined_table")

#     return render(request, "wgs_app/Add_wgs.html")

### HELPER TO RECOGNIZE EITHER DATASET FROM REFERRED_DATA AND FINAL_DATA
def get_value(row, *keys):
    """
    Return first existing value from possible column names
    """
    for k in keys:
        if k in row and str(row.get(k)).strip() != "":
            return row.get(k)
    return None



# @login_required
# @transaction.atomic
# def upload_final_combined_table(request):

#     if request.method != "POST" or not request.FILES.get("DemogsDataFile"):
#         return render(request, "wgs_app/Add_wgs.html")

#     try:

#         uploaded_file = request.FILES["DemogsDataFile"]
#         file_name = uploaded_file.name.lower()

#         # ================= LOAD FILE =================
#         if file_name.endswith(".csv"):
#             df = pd.read_csv(uploaded_file)

#         elif file_name.endswith((".xlsx", ".xls")):
#             df = pd.read_excel(uploaded_file)

#         else:
#             messages.error(request, "Unsupported file format.")
#             return redirect("upload_final_combined_table")

#         df.columns = [str(c).strip() for c in df.columns]
#         rows = df.to_dict("records")

#         # ================= FIELD DEFINITIONS =================
#         final_fields = {f.name for f in Final_Data._meta.fields}

#         IMMUTABLE_FIELDS = {
#             "f_Date_of_Entry",
#             "f_Date_Modified",
#         }

#         INT_FIELDS = {
#             "f_Age",
#             "f_bat_seq",
#         }

#         # ================= LOOKUP CACHE =================
#         specimen_map = {
#             str(s.Specimen_code).strip().lower(): s
#             for s in SpecimenTypeModel.objects.all()
#         }

#         site_map = {
#             str(s.SiteCode).strip().upper(): s.SiteName
#             for s in SiteData.objects.all()
#         }

#         created = 0
#         updated = 0

#         # ================= PROCESS ROWS =================

#         for row in rows:

#             accession = str(get_value(row, "f_AccessionNo", "AccessionNo") or "").strip().upper()
#             batch_code = str(get_value(row, "f_Batch_Code", "Batch_Code") or "").strip()

#             if not accession:
#                 continue

#             referral_date = parse_date(get_value(row, "f_Referral_Date", "Referral_Date"))
#             spec_date = parse_date(get_value(row, "f_Spec_Date", "Spec_Date"))
#             birth_date = parse_date(get_value(row, "f_Date_Birth", "Date_Birth"))
#             admis_date = parse_date(get_value(row, "f_Date_Admis", "Date_Admis"))

#             site_code = str(get_value(row, "f_SiteCode", "SiteCode") or "").strip().upper()
#             site_name = site_map.get(site_code, "")

#             # ================= REFERRED DATA =================

#             Referred_Data.objects.update_or_create(
#                 AccessionNo=accession,
#                 defaults={
#                     "SiteCode": site_code,
#                     "Site_Name": site_name,
#                     "Referral_Date": referral_date,
#                 }
#             )

#             # ================= PREP FINAL DATA =================

#             clean_row = {}

#             for k, v in row.items():

#                 if k not in final_fields or k in IMMUTABLE_FIELDS:
#                     continue

#                 clean_row[k] = v

#             clean_row["f_AccessionNo"] = accession
#             clean_row["f_Batch_Code"] = batch_code
#             clean_row["f_Referral_Date"] = referral_date
#             clean_row["f_Spec_Date"] = spec_date
#             clean_row["f_Date_Birth"] = birth_date
#             clean_row["f_Date_Admis"] = admis_date
#             clean_row["f_SiteCode"] = site_code
#             clean_row["f_Site_Name"] = site_name

#             # normalize integers
#             for field in INT_FIELDS:
#                 if field in clean_row:
#                     clean_row[field] = parse_int(clean_row[field])

#             # specimen FK
#             if "f_Spec_Type" in clean_row:

#                 raw_val = clean_row["f_Spec_Type"]

#                 if pd.isna(raw_val) or raw_val is None:
#                     clean_row["f_Spec_Type"] = None
#                 else:
#                     spec_val = str(raw_val).strip().lower()
#                     clean_row["f_Spec_Type"] = specimen_map.get(spec_val)

#             # ================= FINAL DATA UPSERT =================

#             obj, is_created = Final_Data.objects.update_or_create(
#                 f_AccessionNo=accession,
#                 defaults=clean_row
#             )

#             if is_created:
#                 created += 1
#             else:
#                 updated += 1

#         # ================= SUCCESS =================
#         created_batches = generate_batches_from_referred()

#         messages.success(
#             request,
#             f"Upload complete! {created} created, {updated} updated. "
#             f"{created_batches} batch(es) generated automatically."
#         )


#         return redirect("show_final_data")

#     except Exception as e:

#         import traceback
#         traceback.print_exc()

#         messages.error(request, f"Upload failed: {e}")
#         return redirect("upload_wgs_view")


def parse_date(val):

    if val is None:
        return None

    if pd.isna(val):
        return None

    if isinstance(val, pd.Timestamp):
        return val.date()

    if isinstance(val, datetime):
        return val.date()

    if isinstance(val, date):
        return val

    try:
        return pd.to_datetime(val, errors="coerce").date()
    except Exception:
        return None
    


########### uploding of demogs view

# @login_required
# @transaction.atomic
# def upload_final_combined_table(request):

#     if request.method != "POST" or not request.FILES.get("DemogsDataFile"):
#         return render(request, "wgs_app/Add_wgs.html")

#     try:

#         uploaded_file = request.FILES["DemogsDataFile"]
#         file_name = uploaded_file.name.lower()

#         # ================= READ FILE =================
#         if file_name.endswith(".csv"):
#             df = pd.read_csv(uploaded_file)

#         elif file_name.endswith((".xlsx", ".xls")):
#             df = pd.read_excel(uploaded_file)

#         else:
#             messages.error(request, "Unsupported file format.")
#             return redirect("upload_final_combined_table")

#         df.columns = [str(c).strip() for c in df.columns]
#         rows = df.to_dict("records")

#         # ================= FIELD LISTS =================
#         referred_fields = {
#             f.name for f in Referred_Data._meta.fields
#             if not f.auto_created
#         }

#         final_fields = {
#             f.name for f in Final_Data._meta.fields
#             if not f.auto_created
#         }

#         IMMUTABLE_FIELDS = {
#             "f_Date_of_Entry",
#             "f_Date_Modified",
#         }

#         INT_FIELDS = {
#             "Age",
#             "f_Age",
#             "bat_seq",
#             "f_bat_seq"
#         }

#         # ================= LOOKUP CACHE =================
#         specimen_map = {
#             str(s.Specimen_code).strip().lower(): s
#             for s in SpecimenTypeModel.objects.all()
#         }

#         site_map = {
#             str(s.SiteCode).strip().upper(): s.SiteName
#             for s in SiteData.objects.all()
#         }

#         # ================= EXISTING CACHE =================
#         existing_referred = {
#             obj.AccessionNo: obj
#             for obj in Referred_Data.objects.all()
#         }

#         existing_final = {
#             obj.f_AccessionNo: obj
#             for obj in Final_Data.objects.all()
#         }

#         referred_create = []
#         referred_update = []

#         final_create = []
#         final_update = []

#         # ================= PROCESS ROWS =================
#         for row in rows:

#             row = {str(k).strip(): v for k, v in row.items()}

#             accession = str(get_value(row, "AccessionNo", "accession_no")).strip().upper()

#             if not accession:
#                 continue

#             site_code = str(get_value(row, "SiteCode", "site_code") or "").strip().upper()
#             site_name = site_map.get(site_code, "")

#             referral_date = parse_date(get_value(row, "Referral_Date", "referral_date"))
#             birth_date = parse_date(get_value(row, "Date_Birth", "date_birth"))
#             admis_date = parse_date(get_value(row, "Date_Admis", "date_admis"))
#             spec_date = parse_date(get_value(row, "Spec_Date", "spec_date"))

#             batch_code = get_value(row, "Batch_Code", "batch_code")

#             # ================= REFERRED DATA =================
#             clean_referred = {
#                 k: v
#                 for k, v in row.items()
#                 if k in referred_fields
#             }

#             clean_referred["AccessionNo"] = accession
#             clean_referred["Referral_Date"] = referral_date
#             clean_referred["Date_Birth"] = birth_date
#             clean_referred["Date_Admis"] = admis_date
#             clean_referred["Spec_Date"] = spec_date
#             clean_referred["SiteCode"] = site_code
#             clean_referred["Site_Name"] = site_name
#             clean_referred["Batch_Code"] = batch_code

#             # integer cleanup
#             for field in INT_FIELDS:
#                 if field in clean_referred:
#                     clean_referred[field] = parse_int(clean_referred[field])

#             # specimen FK
#             if "Spec_Type" in clean_referred:

#                 raw_val = clean_referred["Spec_Type"]

#                 if raw_val:
#                     clean_referred["Spec_Type"] = specimen_map.get(
#                         str(raw_val).strip().lower()
#                     )

#             if accession in existing_referred:

#                 obj = existing_referred[accession]

#                 for k, v in clean_referred.items():
#                     setattr(obj, k, v)

#                 referred_update.append(obj)

#             else:

#                 referred_create.append(
#                     Referred_Data(**clean_referred)
#                 )

#             # ================= FINAL DATA =================
#             clean_final = {}

#             for k, v in row.items():

#                 fk = f"f_{k}"

#                 if fk in final_fields and fk not in IMMUTABLE_FIELDS:
#                     clean_final[fk] = v

#             clean_final["f_AccessionNo"] = accession
#             clean_final["f_Referral_Date"] = referral_date
#             clean_final["f_Date_Birth"] = birth_date
#             clean_final["f_Date_Admis"] = admis_date
#             clean_final["f_Spec_Date"] = spec_date
#             clean_final["f_SiteCode"] = site_code
#             clean_final["f_Site_Name"] = site_name
#             clean_final["f_Batch_Code"] = batch_code

#             for field in INT_FIELDS:
#                 if field in clean_final:
#                     clean_final[field] = parse_int(clean_final[field])

#             if "f_Spec_Type" in clean_final:

#                 raw_val = clean_final["f_Spec_Type"]

#                 if raw_val:
#                     clean_final["f_Spec_Type"] = specimen_map.get(
#                         str(raw_val).strip().lower()
#                     )

#             if accession in existing_final:

#                 obj = existing_final[accession]

#                 for k, v in clean_final.items():
#                     setattr(obj, k, v)

#                 final_update.append(obj)

#             else:

#                 final_create.append(
#                     Final_Data(**clean_final)
#                 )

#         # ================= REMOVE DUPLICATES =================
#         referred_update = list({o.AccessionNo: o for o in referred_update}.values())
#         final_update = list({o.f_AccessionNo: o for o in final_update}.values())

#         # ================= BULK SAVE =================
#         if referred_create:
#             Referred_Data.objects.bulk_create(referred_create)

#         if referred_update:
#             Referred_Data.objects.bulk_update(
#                 referred_update,
#                 [f for f in referred_fields if f != "id"]
#             )

#         if final_create:
#             Final_Data.objects.bulk_create(final_create)

#         if final_update:
#             Final_Data.objects.bulk_update(
#                 final_update,
#                 [f for f in final_fields if f not in IMMUTABLE_FIELDS and f != "id"]
#             )

#         created = len(final_create)
#         updated = len(final_update)

#         # ================= BATCH GENERATION =================
#         created_batches = generate_batches_from_referred()

#         messages.success(
#             request,
#             f"Upload complete! {created} created, {updated} updated. "
#             f"{created_batches} batch(es) generated."
#         )

#         return redirect("show_final_data")

#     except Exception as e:

#         import traceback
#         traceback.print_exc()

#         messages.error(request, f"Upload failed: {e}")
#         return redirect("upload_wgs_view")

def copy_batches_to_final(batch_ids):

    def to_bool(val):
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes", "y")
        return False

    copied = 0
    last_final_obj = None

    batches = Batch_Table.objects.filter(id__in=batch_ids)

    for batch in batches:

        isolates = Referred_Data.objects.filter(
            Batch_id=batch
        ).order_by("bat_seq")

        for isolate in isolates:

            spec_obj = None

            raw_entries = AntibioticEntry.objects.filter(
                ab_idNum_referred=isolate
            )

            if isolate.Spec_Type:
                spec_obj = SpecimenTypeModel.objects.filter(
                    Specimen_code=isolate.Spec_Type
                ).first()

            # ===== CREATE / UPDATE FINAL =====
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

            last_final_obj = final_obj

            # ===== RESET ANTIBIOTICS =====
            Final_AntibioticEntry.objects.filter(
                ab_idNum_f_referred=final_obj
            ).delete()

            # ===== COPY ANTIBIOTICS =====
            for e in raw_entries:

                fe = Final_AntibioticEntry.objects.create(
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

                fe.ab_Ret_R_breakpoint = e.ab_Ret_R_breakpoint
                fe.ab_Ret_I_breakpoint = e.ab_Ret_I_breakpoint
                fe.ab_Ret_SDD_breakpoint = e.ab_Ret_SDD_breakpoint
                fe.ab_Ret_S_breakpoint = e.ab_Ret_S_breakpoint

                fe.ab_Alert_val = e.ab_Alert_val
                fe.ab_Retest_Alert_val = e.ab_Retest_Alert_val

                fe.save()

            copied += 1

    return copied, last_final_obj


########## UPLOADING DEMOGS
@login_required
@transaction.atomic
def upload_referred_table(request):

    if request.method != "POST" or not request.FILES.get("DemogsDataFile"):
        return render(request, "wgs_app/Add_wgs.html")

    try:

        uploaded_file = request.FILES["DemogsDataFile"]
        file_name = uploaded_file.name.lower()

        # ================= READ FILE =================
        if file_name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)

        elif file_name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(uploaded_file)

        else:
            messages.error(request, "Unsupported file format.")
            return redirect("upload_wgs_view")

        df.columns = [str(c).strip() for c in df.columns]
        rows = df.to_dict("records")

        # ================= FIELD LIST =================
        referred_fields = {
            f.name for f in Referred_Data._meta.fields
            if not f.auto_created
        }

        INT_FIELDS = {
            "Age",
            "bat_seq"
        }

        # ================= LOOKUPS =================
        specimen_map = {
            str(s.Specimen_code).strip().lower(): s
            for s in SpecimenTypeModel.objects.all()
        }

        site_map = {
            str(s.SiteCode).strip().upper(): s.SiteName
            for s in SiteData.objects.all()
        }

        # ================= EXISTING CACHE =================
        existing = {
            obj.AccessionNo: obj
            for obj in Referred_Data.objects.all()
        }

        to_create = []
        to_update = []

        # ================= PROCESS ROWS =================
        for row in rows:

            row = {str(k).strip(): v for k, v in row.items()}

            accession = str(
                get_value(row, "AccessionNo", "accession_no")
            ).strip().upper()

            if not accession:
                continue

            site_code = str(
                get_value(row, "SiteCode", "site_code") or ""
            ).strip().upper()

            site_name = site_map.get(site_code, "")

            referral_date = parse_date(
                get_value(row, "Referral_Date", "referral_date")
            )

            birth_date = parse_date(
                get_value(row, "Date_Birth", "date_birth")
            )

            admis_date = parse_date(
                get_value(row, "Date_Admis", "date_admis")
            )

            spec_date = parse_date(
                get_value(row, "Spec_Date", "spec_date")
            )

            batch_code = get_value(row, "Batch_Code", "batch_code")

            clean = {
                k: v for k, v in row.items()
                if k in referred_fields
            }

            clean["AccessionNo"] = accession
            clean["Referral_Date"] = referral_date
            clean["Date_Birth"] = birth_date
            clean["Date_Admis"] = admis_date
            clean["Spec_Date"] = spec_date
            clean["SiteCode"] = site_code
            clean["Site_Name"] = site_name
            clean["Batch_Code"] = batch_code

            # integer cleanup
            for field in INT_FIELDS:
                if field in clean:
                    clean[field] = parse_int(clean[field])

            # specimen FK
            if "Spec_Type" in clean:

                raw_val = clean["Spec_Type"]

                if raw_val:
                    clean["Spec_Type"] = specimen_map.get(
                        str(raw_val).strip().lower()
                    )

            # ================= CREATE / UPDATE =================
            if accession in existing:

                obj = existing[accession]

                for k, v in clean.items():
                    setattr(obj, k, v)

                to_update.append(obj)

            else:

                to_create.append(
                    Referred_Data(**clean)
                )

        # ================= REMOVE DUPLICATES =================
        to_update = list({o.AccessionNo: o for o in to_update}.values())

        # ================= SAVE =================
        if to_create:
            Referred_Data.objects.bulk_create(to_create)

        if to_update:
            Referred_Data.objects.bulk_update(
                to_update,
                [f for f in referred_fields if f != "id"]
            )

        created = len(to_create)
        updated = len(to_update)

        # ================= GENERATE BATCH =================
        created_batches = generate_batches_from_referred()
        batch_ids = Batch_Table.objects.values_list("id", flat=True)
        copied_batches = copy_batches_to_final(batch_ids)

        messages.success(
            request,
            f"Upload complete! {created} created, {updated} updated. "
            f"{created_batches} batches generated. "
            f"{copied_batches} isolates copied to Final."
        )

        return redirect("show_batches")

    except Exception as e:

        import traceback
        traceback.print_exc()

        messages.error(request, f"Upload failed: {e}")
        return redirect("upload_wgs_view")



########## end of uploading view

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
def show_referred_data(request):
    rawdata_summaries = Referred_Data.objects.all().order_by("Referral_Date")  # optional ordering

    total_records = Referred_Data.objects.count()
     # Paginate the queryset to display 20 records per page
    paginator = Paginator(rawdata_summaries, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Render the template with paginated data
    return render(
        request,
        "wgs_app/show_referred_data.html",
        {"page_obj": page_obj,
         "total_records": total_records,
         },  # only send page_obj
    )





@login_required
@transaction.atomic
def delete_final_data(request, pk):

    final_item = get_object_or_404(Final_Data, pk=pk)

    if request.method == "POST":
        accession = final_item.f_AccessionNo
        final_item.delete()   #  This triggers the signal

        messages.success(
            request,
            f"Record {accession} deleted. Concordance report invalidated."
        )

        return redirect('show_final_data')

    messages.error(request, "Invalid request for deleting Final data.")
    return redirect('show_final_data')



@login_required
@transaction.atomic
def delete_referred_data(request, pk):

    referred_item = get_object_or_404(Referred_Data, pk=pk)

    if request.method == "POST":
        accession = referred_item.AccessionNo
        referred_item.delete()   #  This triggers the signal

        messages.success(
            request,
            f"Record {accession} deleted. Concordance report invalidated."
        )

        return redirect('show_referred_data')

    messages.error(request, "Invalid request for deleting Final data.")
    return redirect('show_referred_data')




@login_required
def delete_all_final_data(request):
    Final_Data.objects.all().delete()
    messages.success(request, "Final Referred Isolates have been deleted successfully.")
    return redirect('show_final_data')  # Redirect to the table view



@login_required
def delete_all_referred_data(request):
    Referred_Data.objects.all().delete()
    messages.success(request, "Referred Isolates have been deleted successfully.")
    return redirect('show_referred_data')  # Redirect to the table view



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


@login_required
def delete_referreddata_by_date(request):
    if request.method == "POST":
        upload_date_str = request.POST.get("Date_Modified")
        print(" Received upload_date_str:", upload_date_str)

        if not upload_date_str:
            messages.error(request, "Please select an upload date to delete.")
            return redirect("show_referred_data")

        # Use Django’s date parser
        upload_date = parse_date(upload_date_str)

        if not upload_date:
            messages.error(request, f"Invalid date format: {upload_date_str}")
            return redirect("show_referred_data")

        deleted_count, _ = Referred_Data.objects.filter(Date_uploaded_rd=upload_date).delete()
        messages.success(request, f" Deleted {deleted_count} Final Isolates records uploaded on {upload_date}.")
        return redirect("show_referred_data")

    messages.error(request, "Invalid request method.")
    return redirect("show_referred_data")



############# Uploading of Final Antibiotic Entries


########### HELPERS ################
# ─────────────────────────────────────────────────────────────────────────────
# COLUMN PATTERNS  (all retest / ARSRL results)
#   <abx>_nd<n>        → retest disk value
#   <abx>_nd<n>_ris    → retest disk RIS
#   <abx>_nm           → retest MIC value
#   <abx>_nm_ris       → retest MIC RIS
# ─────────────────────────────────────────────────────────────────────────────

DISK_PAT     = re.compile(r'^([a-z0-9]{2,6})_(nd\d+(?:_\d+)?)$')
DISK_RIS_PAT = re.compile(r'^([a-z0-9]{2,6})_(nd\d+(?:_\d+)?)_ris$')
MIC_PAT      = re.compile(r'^([a-z0-9]{2,6})_(nm)$')
MIC_RIS_PAT  = re.compile(r'^([a-z0-9]{2,6})_(nm)_ris$')

# Excel col → f_ars_* (ARSRL phenotype)
PHENO_FIELD_MAP = {
    'ampc':      'f_ars_ampC',
    'esbl':      'f_ars_ESBL',
    'carb':      'f_ars_CARB',
    'mbl':       'f_ars_MBL',
    'bl':        'f_ars_BL',
    'mr':        'f_ars_MR',
    'meca':      'f_ars_mecA',
    'icr':       'f_ars_ICR',
    'ecim':      'f_ars_ECIM',
    'mcim':      'f_ars_MCIM',
    'ecim.mcim': 'f_ars_EC_MCIM',
}

# Excel col → f_* (site phenotype)
SITE_PHENO_MAP = {
    'ampc': 'f_ampC',
    'esbl': 'f_ESBL',
    'carb': 'f_CARB',
    'mbl':  'f_MBL',
    'bl':   'f_BL',
    'mr':   'f_MR',
    'meca': 'f_mecA',
    'icr':  'f_ICR',
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _clean(val, default=""):
    if val is None:
        return default
    s = str(val).strip()
    return s if s not in ("None", "") else default


def _date(val):
    if val is None:
        return None
    if isinstance(val, (date, datetime)):
        return val.date() if isinstance(val, datetime) else val
    try:
        return datetime.strptime(str(val).strip(), "%Y-%m-%d").date()
    except Exception:
        return None


def _int(val):
    try:
        return int(float(str(val).strip()))
    except Exception:
        return None


def _decimal(val):

    if val is None:
        return None, ""

    s = str(val).strip()
    operand = ""

    for op in ("<=", ">=", "<", ">"):
        if s.startswith(op):
            operand = op
            s = s[len(op):]
            break

    try:
        return Decimal(s), operand
    except Exception:
        return None, ""
    

def _pheno(val):
    s = _clean(val)
    return s if s in ("(+)", "(-)", "NT") else "n/a"


# ─────────────────────────────────────────────────────────────────────────────
# ANTIBIOTIC COLUMN DETECTION
# ─────────────────────────────────────────────────────────────────────────────

def _parse_abx_columns(headers):

    groups = {}

    for idx, col in enumerate(headers):

        if not col:
            continue

        col = str(col).strip().lower()

        parts = col.split("_")

        if len(parts) < 2:
            continue

        abx = parts[0].upper()

        g = groups.setdefault(abx, {
            "disk_col": None,
            "disk_ris_col": None,
            "mic_col": None,
            "mic_ris_col": None,
            "mic_op_col": None,
        })

        # DISK VALUE
        if parts[1].startswith("nd") and "ris" not in col:
            g["disk_col"] = idx

        # DISK RIS
        elif parts[1].startswith("nd") and "ris" in col:
            g["disk_ris_col"] = idx

        # MIC OPERAND
        elif parts[1] == "nm" and len(parts) > 2 and parts[2] == "op":
            g["mic_op_col"] = idx

        # MIC VALUE
        elif parts[1] == "nm" and len(parts) == 2:
            g["mic_col"] = idx

        # MIC RIS
        elif parts[1] == "nm" and "ris" in col:
            g["mic_ris_col"] = idx

    return groups



def _empty_group(abx):
    return {
        'abx_code':     abx,
        'disk_label':   None,
        'disk_col':     None,
        'disk_ris_col': None,
        'mic_col':      None,
        'mic_ris_col':  None,
    }




def _resolve_effective_year(spec_date):
    """
    Returns the nearest breakpoint year relative to the specimen year.

    Rules:
    1. Use closest breakpoint year <= specimen year
    2. If specimen year is earlier than all breakpoints → use earliest
    3. If specimen year is later than all breakpoints → use latest
    """

    years = list(
        BreakpointsTable.objects
        .values_list("Year", flat=True)
        .distinct()
    )

    if not years:
        return None

    years = sorted(int(y) for y in years)

    if spec_date:
        specimen_year = spec_date.year

        # find closest <= specimen year
        eligible = [y for y in years if y <= specimen_year]

        if eligible:
            return str(max(eligible))

        # specimen earlier than all breakpoints
        return str(years[0])

    # if specimen date missing → use newest
    return str(years[-1])




############################
# BREAKPOINT HELPERS
############################

def _apply_bp_to_entry(entry, bp, is_disk, alert_mic=False):

    entry.ab_breakpoints_id.set([bp])

    entry.ab_Site_Org = bp.Org
    entry.ab_Org_Flag = bool(bp.Emerging_Org_Flag)
    entry.ab_Abx_Flag = bool(bp.Emerging_Abx_Flag)
    entry.ab_Abx_Phenotype = bp.Emerging_Pheno_Flag or ""

    entry.ab_R_breakpoint   = bp.R_val
    entry.ab_I_breakpoint   = bp.I_val
    entry.ab_SDD_breakpoint = bp.SDD_val
    entry.ab_S_breakpoint   = bp.S_val

    if not is_disk:
        entry.ab_Alert_val = bp.Alert_val if alert_mic else ""


def _apply_bp_to_retest_entry(entry, bp, is_disk, alert_mic=False):

    entry.ab_breakpoints_id.set([bp])

    entry.ab_Ret_Org = bp.Org
    entry.ab_Org_Flag = bool(bp.Emerging_Org_Flag)
    entry.ab_Abx_Flag = bool(bp.Emerging_Abx_Flag)
    entry.ab_Abx_Phenotype = bp.Emerging_Pheno_Flag or ""

    entry.ab_Ret_R_breakpoint   = bp.R_val
    entry.ab_Ret_I_breakpoint   = bp.I_val
    entry.ab_Ret_SDD_breakpoint = bp.SDD_val
    entry.ab_Ret_S_breakpoint   = bp.S_val

    if not is_disk:
        entry.ab_Retest_Alert_val = bp.Alert_val if alert_mic else ""


############################
# CLEAR BREAKPOINT FIELDS
############################

def _clear_bp_fields(entry):

    entry.ab_Site_Org = None
    entry.ab_Org_Flag = False
    entry.ab_Abx_Flag = False
    entry.ab_Abx_Phenotype = ""

    entry.ab_R_breakpoint   = None
    entry.ab_I_breakpoint   = None
    entry.ab_SDD_breakpoint = None
    entry.ab_S_breakpoint   = None

    entry.ab_Alert_val = ""


def _clear_retest_bp_fields(entry):

    entry.ab_Ret_Org = None
    entry.ab_Org_Flag = False
    entry.ab_Abx_Flag = False
    entry.ab_Abx_Phenotype = ""

    entry.ab_Ret_R_breakpoint   = None
    entry.ab_Ret_I_breakpoint   = None
    entry.ab_Ret_SDD_breakpoint = None
    entry.ab_Ret_S_breakpoint   = None

    entry.ab_Retest_Alert_val = ""


############################
# SAVE SITE ANTIBIOTIC
############################

def _save_site_entry(
    isolate,
    abx_code,
    disk_int,
    disk_ris,
    mic_value,
    mic_operand,
    mic_ris,
    resolved_org,
    effective_year,
    abx_obj=None
):

    entry, _ = AntibioticEntry.objects.update_or_create(

        ab_idNum_referred=isolate,
        ab_Abx_code=abx_code.upper(),

        defaults={

            "ab_AccessionNo": isolate.AccessionNo,
            "ab_RefNo": isolate.RefNo,

            "ab_Antibiotic": abx_obj.Antibiotic if abx_obj else abx_code,
            "ab_Abx": abx_obj.Abx_code if abx_obj else abx_code,

            "ab_Disk_value": disk_int,
            "ab_Disk_enRIS": disk_ris,

            "ab_MIC_value": mic_value,
            "ab_MIC_operand": mic_operand,
            "ab_MIC_enRIS": mic_ris,
        }
    )

    entry.ab_breakpoints_id.clear()

    bp_applied = False

    if disk_int is not None:

        bp = BreakpointsTable.objects.filter(
            Antibiotic_list_id=abx_code.upper(),
            Year=effective_year,
            Test_Method="DISK",
            Org__in=[resolved_org, ""]
        ).order_by("-Org").first()

        if bp:
            _apply_bp_to_entry(entry, bp, True)
            bp_applied = True

    if mic_value is not None:

        bp = BreakpointsTable.objects.filter(
            Antibiotic_list_id=abx_code.upper(),
            Year=effective_year,
            Test_Method="MIC",
            Org__in=[resolved_org, ""]
        ).order_by("-Org").first()

        if bp:
            _apply_bp_to_entry(entry, bp, False)
            bp_applied = True

    if not bp_applied:
        _clear_bp_fields(entry)

    entry.save()

    return entry


############################
# SAVE RETEST ANTIBIOTIC
############################

def _save_retest_entry(
    entry_model,
    isolate,
    abx_code,
    disk_int,
    disk_ris,
    mic_value,
    mic_operand,
    mic_ris,
    resolved_ars_org,
    effective_year,
    abx_obj=None
):

    # --------------------------------
    # Resolve accession + refno
    # --------------------------------
    accession = getattr(isolate, "AccessionNo", None) or getattr(isolate, "f_AccessionNo", "")
    refno = getattr(isolate, "RefNo", None) or getattr(isolate, "f_RefNo", "")

    # --------------------------------
    # Determine correct FK field
    # --------------------------------
    fk_field = (
        "ab_idNum_f_referred"
        if entry_model.__name__ == "Final_AntibioticEntry"
        else "ab_idNum_referred"
    )

    filter_kwargs = {
        fk_field: isolate,
        "ab_Retest_Abx_code": abx_code.upper()
    }

    # --------------------------------
    # Create / Update entry
    # --------------------------------
    entry, created = entry_model.objects.update_or_create(

        **filter_kwargs,

        defaults={

            "ab_AccessionNo": accession,
            "ab_RefNo": refno,

            "ab_Retest_Antibiotic": abx_obj.Antibiotic if abx_obj else abx_code,
            "ab_Retest_Abx": abx_obj.Abx_code if abx_obj else abx_code,

            "ab_Retest_DiskValue": disk_int,
            "ab_Retest_Disk_enRIS": disk_ris,

            "ab_Retest_MICValue": mic_value,
            "ab_Retest_MIC_operand": mic_operand,
            "ab_Retest_MIC_enRIS": mic_ris,
        }
    )

    # --------------------------------
    # Clear breakpoints
    # --------------------------------
    entry.ab_breakpoints_id.clear()

    bp_applied = False

    # --------------------------------
    # DISK BREAKPOINT
    # --------------------------------
    if disk_int is not None:

        bp = BreakpointsTable.objects.filter(
            Antibiotic_list_id=abx_code.upper(),
            Year=effective_year,
            Test_Method="DISK",
            Org__in=[resolved_ars_org, ""]
        ).order_by("-Org").first()

        if bp:
            _apply_bp_to_retest_entry(entry, bp, True)
            bp_applied = True

    # --------------------------------
    # MIC BREAKPOINT
    # --------------------------------
    if mic_value is not None:

        bp = BreakpointsTable.objects.filter(
            Antibiotic_list_id=abx_code.upper(),
            Year=effective_year,
            Test_Method="MIC",
            Org__in=[resolved_ars_org, ""]
        ).order_by("-Org").first()

        if bp:
            _apply_bp_to_retest_entry(entry, bp, False)
            bp_applied = True

    # --------------------------------
    # No breakpoint found
    # --------------------------------
    if not bp_applied:
        _clear_retest_bp_fields(entry)

    entry.save()

    return entry, created

########## END OF HELPERS ################
# @login_required
# @require_POST
# @transaction.atomic
# def upload_final_antibiotics(request):

#     file = request.FILES.get("FinalAntibioticFile")

#     if not file:
#         messages.error(request, "No file uploaded")
#         return redirect("show_final_antibiotic")

#     try:
#         wb = openpyxl.load_workbook(file, read_only=True, data_only=True)
#     except Exception as e:
#         messages.error(request, str(e))
#         return redirect("show_final_antibiotic")

#     created = 0
#     updated = 0
#     skipped = 0

#     # -----------------------------
#     # LOAD REFERENCE DATA
#     # -----------------------------

#     breakpoint_keys = set(
#         (x or "").strip().upper()
#         for x in BreakpointsTable.objects.values_list("Whonet_Abx", flat=True)
#     )

#     antibiotics = {
#         (a.Abx_code or "").strip().upper(): a
#         for a in Antibiotic_List.objects.filter(Retest=True)
#     }

#     def normalize_accession(val):
#         return str(val).strip().replace(" ", "").upper()

#     isolates = {
#         normalize_accession(i.f_AccessionNo): i
#         for i in Final_Data.objects.all()
#     }
#     # -----------------------------
#     # PROCESS WORKBOOK
#     # -----------------------------

#     for sheet in wb.sheetnames:

#         ws = wb[sheet]
#         rows = ws.iter_rows(values_only=True)

#         headers = next(rows)
#         headers_lower = [str(c).lower().strip() if c else "" for c in headers]

#         if "f_accessionno" not in headers_lower:
#             continue

#         accession_idx = headers_lower.index("f_accessionno")

#         abx_groups = {
#             k: v for k, v in _parse_abx_columns(headers).items()
#             if v["disk_col"] is not None or v["mic_col"] is not None
#         }

#         for row in rows:

#             accession = _clean(row[accession_idx]).upper()

#             if not accession:
#                 continue

#             isolate = isolates.get(accession)

#             if not isolate:
#                 skipped += 1
#                 continue

#             effective_year = _resolve_effective_year(isolate.f_Spec_Date)
#             resolved_ars_org = (isolate.f_ars_OrgCode or "").strip()

#             for abx_code, grp in abx_groups.items():

#                 abx_code = abx_code.upper()

#                 # resolve antibiotic object
#                 abx_obj = antibiotics.get(abx_code)

#                 if not abx_obj:
#                     continue

#                 disk_key = headers[grp["disk_col"]].upper() if grp["disk_col"] is not None else None
#                 mic_key = headers[grp["mic_col"]].upper() if grp["mic_col"] is not None else None

#                 # remove accidental _OP
#                 if mic_key and mic_key.endswith("_OP"):
#                     mic_key = mic_key.replace("_OP", "")

#                 # ----------------------------
#                 # EXCEL VALUES
#                 # ----------------------------

#                 disk_raw = row[grp["disk_col"]] if grp["disk_col"] is not None else None
#                 disk_ris = _clean(row[grp["disk_ris_col"]]) if grp["disk_ris_col"] is not None else ""

#                 mic_raw = row[grp["mic_col"]] if grp["mic_col"] is not None else None
#                 mic_ris = _clean(row[grp["mic_ris_col"]]) if grp["mic_ris_col"] is not None else ""

#                 mic_operand = ""
#                 if grp["mic_op_col"] is not None:
#                     mic_operand = _clean(row[grp["mic_op_col"]])

#                 disk_val = _int(disk_raw)
#                 mic_val, parsed_operand = _decimal(mic_raw)

#                 if not mic_operand:
#                     mic_operand = parsed_operand

#                 # ----------------------------
#                 # DELETE IF EMPTY
#                 # --------------------  --------

#                 if disk_val is None and mic_val is None:

#                     Final_AntibioticEntry.objects.filter(
#                         ab_idNum_f_referred=isolate,
#                         ab_Retest_Abx_code=abx_code
#                     ).delete()

#                     continue

#                 # ----------------------------
#                 # CREATE / UPDATE ENTRY
#                 # ----------------------------
#                 whonet_code = disk_key if disk_val is not None else mic_key

#                 entry, created_flag = Final_AntibioticEntry.objects.update_or_create(

#                     ab_idNum_f_referred=isolate,
#                     ab_Retest_Abx_code=whonet_code,

#                     defaults={

#                         "ab_AccessionNo": isolate.f_AccessionNo,
#                         "ab_RefNo": isolate.f_RefNo,

#                         "ab_Retest_Antibiotic": abx_obj.Antibiotic,
#                         "ab_Retest_Abx": abx_obj.Abx_code,
                        
#                         "ab_Retest_DiskValue": disk_val,
#                         "ab_Retest_MICValue": mic_val,

#                         "ab_Retest_Disk_enRIS": disk_ris,
#                         "ab_Retest_MIC_enRIS": mic_ris,
#                         "ab_Retest_MIC_operand": mic_operand,
#                     }
#                 )

#                 entry.ab_breakpoints_id.clear()

#                 ret_bp_applied = False

#                 # ----------------------------
#                 # DISK BREAKPOINT
#                 # ----------------------------

#                 if disk_val is not None and disk_key and disk_key in breakpoint_keys:

#                     bp_disk = BreakpointsTable.objects.filter(
#                         Whonet_Abx__iexact=disk_key,
#                         Year=effective_year,
#                         Test_Method="DISK",
#                         Org__in=[resolved_ars_org, ""]
#                     ).order_by("-Org").first()

#                     if bp_disk:

#                         entry.ab_breakpoints_id.set([bp_disk])

#                         entry.ab_Ret_Org = bp_disk.Org
#                         entry.ab_Org_Flag = bool(bp_disk.Emerging_Org_Flag)
#                         entry.ab_Abx_Flag = bool(bp_disk.Emerging_Abx_Flag)
#                         entry.ab_Abx_Phenotype = bp_disk.Emerging_Pheno_Flag or ""

#                         entry.ab_Ret_R_breakpoint = bp_disk.R_val
#                         entry.ab_Ret_I_breakpoint = bp_disk.I_val
#                         entry.ab_Ret_SDD_breakpoint = bp_disk.SDD_val
#                         entry.ab_Ret_S_breakpoint = bp_disk.S_val

#                         ret_bp_applied = True

#                 # ----------------------------
#                 # MIC BREAKPOINT
#                 # ----------------------------

#                 if mic_val is not None and mic_key and mic_key in breakpoint_keys:

#                     bp_mic = BreakpointsTable.objects.filter(
#                         Whonet_Abx__iexact=mic_key,
#                         Year=effective_year,
#                         Test_Method="MIC",
#                         Org__in=[resolved_ars_org, ""]
#                     ).order_by("-Org").first()

#                     if bp_mic:

#                         entry.ab_breakpoints_id.set([bp_mic])

#                         entry.ab_Ret_Org = bp_mic.Org
#                         entry.ab_Org_Flag = bool(bp_mic.Emerging_Org_Flag)
#                         entry.ab_Abx_Flag = bool(bp_mic.Emerging_Abx_Flag)
#                         entry.ab_Abx_Phenotype = bp_mic.Emerging_Pheno_Flag or ""

#                         entry.ab_Ret_R_breakpoint = bp_mic.R_val
#                         entry.ab_Ret_I_breakpoint = bp_mic.I_val
#                         entry.ab_Ret_SDD_breakpoint = bp_mic.SDD_val
#                         entry.ab_Ret_S_breakpoint = bp_mic.S_val

#                         entry.ab_Retest_Alert_val = bp_mic.Alert_val

#                         ret_bp_applied = True

#                 # ----------------------------
#                 # NO BREAKPOINT
#                 # ----------------------------

#                 if not ret_bp_applied:

#                     entry.ab_Ret_Org = None
#                     entry.ab_Org_Flag = False
#                     entry.ab_Abx_Flag = False
#                     entry.ab_Abx_Phenotype = ""

#                     entry.ab_Ret_R_breakpoint = None
#                     entry.ab_Ret_I_breakpoint = None
#                     entry.ab_Ret_SDD_breakpoint = None
#                     entry.ab_Ret_S_breakpoint = None

#                     entry.ab_Retest_Alert_val = ""

#                 entry.save()

#                 if created_flag:
#                     created += 1
#                 else:
#                     updated += 1

#     wb.close()

#     messages.success(
#         request,
#         f"{created} antibiotics uploaded successfully. "
#         f"{updated} updated, {skipped} skipped."
#     )

#     return redirect("show_final_antibiotic")


########### implements sentinel site & ars antitbioc fields upload
@login_required
@require_POST
@transaction.atomic
def upload_final_antibiotics(request):

    file = request.FILES.get("FinalAntibioticFile")

    if not file:
        messages.error(request, "No file uploaded")
        return redirect("show_final_antibiotic")

    try:
        wb = openpyxl.load_workbook(file, read_only=True, data_only=True)
    except Exception as e:
        messages.error(request, str(e))
        return redirect("show_final_antibiotic")

    created = 0
    updated = 0
    skipped = 0

    # -----------------------------
    # LOAD REFERENCE DATA
    # -----------------------------

    antibiotics = {
        (a.Abx_code or "").strip().upper(): a
        for a in Antibiotic_List.objects.all()
    }


    def normalize_accession(val):
        return str(val).strip().replace(" ", "").upper()

    isolates = {
        normalize_accession(i.f_AccessionNo): i
        for i in Final_Data.objects.all()
    }

    # -----------------------------
    # PROCESS WORKBOOK
    # -----------------------------

    for sheet in wb.sheetnames:

        ws = wb[sheet]
        rows = ws.iter_rows(values_only=True)

        headers = next(rows)
        headers_lower = [str(c).lower().strip() if c else "" for c in headers]

        if "f_accessionno" not in headers_lower:
            continue

        accession_idx = headers_lower.index("f_accessionno")

        abx_groups = {
            k: v for k, v in _parse_abx_columns(headers).items()
            if v["disk_col"] is not None or v["mic_col"] is not None
        }

        for row in rows:

            accession = _clean(row[accession_idx]).upper()

            if not accession:
                continue

            isolate = isolates.get(accession)

            if not isolate:
                skipped += 1
                continue

            effective_year = _resolve_effective_year(isolate.f_Spec_Date)
            resolved_ars_org = (isolate.f_ars_OrgCode or "").strip()

            for abx_code, grp in abx_groups.items():

                abx_code = abx_code.upper()

                abx_obj = antibiotics.get(abx_code)

                if not abx_obj:
                    continue

                # ----------------------------
                # EXCEL VALUES
                # ----------------------------

                disk_raw = row[grp["disk_col"]] if grp["disk_col"] is not None else None
                disk_ris = _clean(row[grp["disk_ris_col"]]) if grp["disk_ris_col"] is not None else ""

                mic_raw = row[grp["mic_col"]] if grp["mic_col"] is not None else None
                mic_ris = _clean(row[grp["mic_ris_col"]]) if grp["mic_ris_col"] is not None else ""

                mic_operand = ""
                if grp["mic_op_col"] is not None:
                    mic_operand = _clean(row[grp["mic_op_col"]])

                disk_val = _int(disk_raw)
                mic_val, parsed_operand = _decimal(mic_raw)

                if not mic_operand:
                    mic_operand = parsed_operand

                # ----------------------------
                # DELETE IF EMPTY
                # ----------------------------

                if disk_val is None and mic_val is None:

                    Final_AntibioticEntry.objects.filter(
                        ab_idNum_f_referred=isolate,
                        ab_Retest_Abx_code=abx_code
                    ).delete()

                    continue

                # ----------------------------
                # SAVE USING HELPER
                # ----------------------------
                disk_key = headers[grp["disk_col"]].upper() if grp["disk_col"] is not None else None
                mic_key  = headers[grp["mic_col"]].upper() if grp["mic_col"] is not None else None

                whonet_code = disk_key if disk_val is not None else mic_key

                entry, created_flag = _save_retest_entry(

                    entry_model=Final_AntibioticEntry,
                    isolate=isolate,
                    abx_code=whonet_code,
                    disk_int=disk_val,
                    disk_ris=disk_ris,
                    mic_value=mic_val,
                    mic_operand=mic_operand,
                    mic_ris=mic_ris,
                    resolved_ars_org=resolved_ars_org,
                    effective_year=effective_year,
                    abx_obj=abx_obj
                )
                if entry._state.adding:
                    created += 1
                else:
                    updated += 1

    wb.close()

    messages.success(
        request,
        f"{created} antibiotics uploaded successfully. "
        f"{updated} updated, {skipped} skipped."
    )

    return redirect("show_final_antibiotic")



# @login_required
# @require_POST
# @transaction.atomic
# def upload_raw_antibiotics(request):

#     file = request.FILES.get("RawAntibioticFile")

#     if not file:
#         messages.error(request, "No file uploaded")
#         return redirect("show_raw_antibiotic")

#     try:
#         wb = openpyxl.load_workbook(file, read_only=True, data_only=True)
#     except Exception as e:
#         messages.error(request, str(e))
#         return redirect("show_raw_antibiotic")

#     created = 0
#     updated = 0
#     skipped = 0

#     # -----------------------------
#     # LOAD REFERENCE DATA
#     # -----------------------------

#     breakpoint_keys = set(
#         (x or "").strip().upper()
#         for x in BreakpointsTable.objects.values_list("Whonet_Abx", flat=True)
#     )

#     antibiotics = {
#         (a.Abx_code or "").strip().upper(): a
#         for a in Antibiotic_List.objects.filter(Show=True)
#     }

#     def normalize_accession(val):
#         return str(val).strip().replace(" ", "").upper()

#     isolates = {
#         normalize_accession(i.AccessionNo): i
#         for i in Referred_Data.objects.all()
#     }
#     # -----------------------------
#     # PROCESS WORKBOOK
#     # -----------------------------

#     for sheet in wb.sheetnames:

#         ws = wb[sheet]
#         rows = ws.iter_rows(values_only=True)

#         headers = next(rows)
#         headers_lower = [str(c).lower().strip() if c else "" for c in headers]

#         if "accessionno" not in headers_lower:
#             continue

#         accession_idx = headers_lower.index("accessionno")

#         abx_groups = {
#             k: v for k, v in _parse_abx_columns(headers).items()
#             if v["disk_col"] is not None or v["mic_col"] is not None
#         }

#         for row in rows:

#             accession = _clean(row[accession_idx]).upper()

#             if not accession:
#                 continue

#             isolate = isolates.get(accession)

#             if not isolate:
#                 skipped += 1
#                 continue

#             effective_year = _resolve_effective_year(isolate.Spec_Date)
#             resolved_ars_org = (isolate.ars_OrgCode or "").strip()

#             for abx_code, grp in abx_groups.items():

#                 abx_code = abx_code.upper()

#                 # resolve antibiotic object
#                 abx_obj = antibiotics.get(abx_code)

#                 if not abx_obj:
#                     continue

#                 disk_key = headers[grp["disk_col"]].upper() if grp["disk_col"] is not None else None
#                 mic_key = headers[grp["mic_col"]].upper() if grp["mic_col"] is not None else None

#                 # remove accidental _OP
#                 if mic_key and mic_key.endswith("_OP"):
#                     mic_key = mic_key.replace("_OP", "")

#                 # ----------------------------
#                 # EXCEL VALUES
#                 # ----------------------------

#                 disk_raw = row[grp["disk_col"]] if grp["disk_col"] is not None else None
#                 disk_ris = _clean(row[grp["disk_ris_col"]]) if grp["disk_ris_col"] is not None else ""

#                 mic_raw = row[grp["mic_col"]] if grp["mic_col"] is not None else None
#                 mic_ris = _clean(row[grp["mic_ris_col"]]) if grp["mic_ris_col"] is not None else ""

#                 mic_operand = ""
#                 if grp["mic_op_col"] is not None:
#                     mic_operand = _clean(row[grp["mic_op_col"]])

#                 disk_val = _int(disk_raw)
#                 mic_val, parsed_operand = _decimal(mic_raw)

#                 if not mic_operand:
#                     mic_operand = parsed_operand

#                 # ----------------------------
#                 # DELETE IF EMPTY
#                 # --------------------  --------

#                 if disk_val is None and mic_val is None:

#                     AntibioticEntry.objects.filter(
#                         ab_idNum_referred=isolate,
#                         ab_Retest_Abx_code=abx_code
#                     ).delete()

#                     continue

#                 # ----------------------------
#                 # CREATE / UPDATE ENTRY
#                 # ----------------------------
#                 whonet_code = disk_key if disk_val is not None else mic_key

#                 entry, created_flag = AntibioticEntry.objects.update_or_create(

#                     ab_idNum_referred=isolate,
#                     ab_Abx_code=whonet_code,

#                     defaults={

#                         "ab_AccessionNo": isolate.AccessionNo,
#                         "ab_RefNo": isolate.RefNo,

#                         "ab_Antibiotic": abx_obj.Antibiotic,
#                         "ab_Abx_code": abx_obj.Abx_code,
                        
#                         "ab_Disk_value": disk_val,
#                         "ab_MIC_value": mic_val,

#                         "ab_Disk_enRIS": disk_ris,
#                         "ab_MIC_enRIS": mic_ris,
#                         "ab_MIC_operand": mic_operand,
#                     }
#                 )

#                 entry.ab_breakpoints_id.clear()

#                 bp_applied = False

#                 # ----------------------------
#                 # DISK BREAKPOINT
#                 # ----------------------------

#                 if disk_val is not None and disk_key and disk_key in breakpoint_keys:

#                     bp_disk = BreakpointsTable.objects.filter(
#                         Whonet_Abx__iexact=disk_key,
#                         Year=effective_year,
#                         Test_Method="DISK",
#                         Org__in=[resolved_ars_org, ""]
#                     ).order_by("-Org").first()

#                     if bp_disk:

#                         entry.ab_breakpoints_id.set([bp_disk])

#                         entry.ab_Site_Org = bp_disk.Org
#                         entry.ab_Org_Flag = bool(bp_disk.Emerging_Org_Flag)
#                         entry.ab_Abx_Flag = bool(bp_disk.Emerging_Abx_Flag)
#                         entry.ab_Abx_Phenotype = bp_disk.Emerging_Pheno_Flag or ""

#                         entry.ab_R_breakpoint = bp_disk.R_val
#                         entry.ab_I_breakpoint = bp_disk.I_val
#                         entry.ab_SDD_breakpoint = bp_disk.SDD_val
#                         entry.ab_S_breakpoint = bp_disk.S_val

#                         bp_applied = True

#                 # ----------------------------
#                 # MIC BREAKPOINT
#                 # ----------------------------

#                 if mic_val is not None and mic_key and mic_key in breakpoint_keys:

#                     bp_mic = BreakpointsTable.objects.filter(
#                         Whonet_Abx__iexact=mic_key,
#                         Year=effective_year,
#                         Test_Method="MIC",
#                         Org__in=[resolved_ars_org, ""]
#                     ).order_by("-Org").first()

#                     if bp_mic:

#                         entry.ab_breakpoints_id.set([bp_mic])

#                         entry.ab_Site_Org = bp_mic.Org
#                         entry.ab_Org_Flag = bool(bp_mic.Emerging_Org_Flag)
#                         entry.ab_Abx_Flag = bool(bp_mic.Emerging_Abx_Flag)
#                         entry.ab_Abx_Phenotype = bp_mic.Emerging_Pheno_Flag or ""

#                         entry.ab_R_breakpoint = bp_mic.R_val
#                         entry.ab_I_breakpoint = bp_mic.I_val
#                         entry.ab_SDD_breakpoint = bp_mic.SDD_val
#                         entry.ab_S_breakpoint = bp_mic.S_val

#                         entry.ab_Alert_val = bp_mic.Alert_val

#                         bp_applied = True

#                 # ----------------------------
#                 # NO BREAKPOINT
#                 # ----------------------------

#                 if not bp_applied:

#                     entry.ab_Site_Org = None
#                     entry.ab_Org_Flag = False
#                     entry.ab_Abx_Flag = False
#                     entry.ab_Abx_Phenotype = ""

#                     entry.ab_R_breakpoint = None
#                     entry.ab_I_breakpoint = None
#                     entry.ab_SDD_breakpoint = None
#                     entry.ab_S_breakpoint = None

#                     entry.ab_Alert_val = ""

#                 entry.save()

#                 if created_flag:
#                     created += 1
#                 else:
#                     updated += 1

#     wb.close()

#     messages.success(
#         request,
#         f"{created} antibiotics uploaded successfully. "
#         f"{updated} updated, {skipped} skipped."
#     )

#     return redirect("show_raw_antibiotic")


############## implements uploading on both sentinel and ars antibiotic fields

@login_required
@require_POST
@transaction.atomic
def upload_raw_antibiotics(request):

    file = request.FILES.get("RawAntibioticFile")

    if not file:
        messages.error(request, "No file uploaded")
        return redirect("show_raw_antibiotic")

    try:
        wb = openpyxl.load_workbook(file, read_only=True, data_only=True)
    except Exception as e:
        messages.error(request, str(e))
        return redirect("show_raw_antibiotic")

    created = 0
    updated = 0
    skipped = 0

    # -----------------------------
    # LOAD REFERENCE DATA
    # -----------------------------

    breakpoint_keys = set(
        (x or "").strip().upper()
        for x in BreakpointsTable.objects.values_list("Whonet_Abx", flat=True)
    )

    antibiotics = {
        (a.Abx_code or "").strip().upper(): a
        for a in Antibiotic_List.objects.all()
    }

    def normalize_accession(val):
        return str(val).strip().replace(" ", "").upper()

    isolates = {
        normalize_accession(i.AccessionNo): i
        for i in Referred_Data.objects.all()
    }

    # -----------------------------
    # PROCESS WORKBOOK
    # -----------------------------

    for sheet in wb.sheetnames:

        ws = wb[sheet]
        rows = ws.iter_rows(values_only=True)

        headers = next(rows)
        headers_lower = [str(c).lower().strip() if c else "" for c in headers]

        if "accessionno" not in headers_lower:
            continue

        accession_idx = headers_lower.index("accessionno")

        abx_groups = {
            k: v for k, v in _parse_abx_columns(headers).items()
            if v["disk_col"] is not None or v["mic_col"] is not None
        }

        for row in rows:

            accession = _clean(row[accession_idx]).upper()

            if not accession:
                continue

            isolate = isolates.get(accession)

            if not isolate:
                skipped += 1
                continue

            effective_year = _resolve_effective_year(isolate.Spec_Date)
            resolved_ars_org = (isolate.ars_OrgCode or "").strip()

            for abx_code, grp in abx_groups.items():

                abx_code = abx_code.upper()

                abx_obj = antibiotics.get(abx_code)

                if not abx_obj:
                    continue

                disk_key = headers[grp["disk_col"]].upper() if grp["disk_col"] is not None else None
                mic_key = headers[grp["mic_col"]].upper() if grp["mic_col"] is not None else None

                if mic_key and mic_key.endswith("_OP"):
                    mic_key = mic_key.replace("_OP", "")

                # ----------------------------
                # RT DETECTION
                # ----------------------------

                is_retest = False

                if disk_key and "_RT" in disk_key:
                    is_retest = True

                if mic_key and "_RT" in mic_key:
                    is_retest = True

                if disk_key:
                    disk_key = disk_key.replace("_RT", "")

                if mic_key:
                    mic_key = mic_key.replace("_RT", "")

                # ----------------------------
                # EXCEL VALUES
                # ----------------------------

                disk_raw = row[grp["disk_col"]] if grp["disk_col"] is not None else None
                disk_ris = _clean(row[grp["disk_ris_col"]]) if grp["disk_ris_col"] is not None else ""

                mic_raw = row[grp["mic_col"]] if grp["mic_col"] is not None else None
                mic_ris = _clean(row[grp["mic_ris_col"]]) if grp["mic_ris_col"] is not None else ""

                mic_operand = ""
                if grp["mic_op_col"] is not None:
                    mic_operand = _clean(row[grp["mic_op_col"]])

                disk_val = _int(disk_raw)
                mic_val, parsed_operand = _decimal(mic_raw)

                if not mic_operand:
                    mic_operand = parsed_operand

                whonet_code = disk_key if disk_val is not None else mic_key

                if not whonet_code:
                    continue

                # ----------------------------
                # DELETE IF EMPTY
                # ----------------------------

                if disk_val is None and mic_val is None:

                    if is_retest:
                        AntibioticEntry.objects.filter(
                            ab_idNum_referred=isolate,
                            ab_Abx_code=whonet_code
                        ).delete()
                    else:
                        AntibioticEntry.objects.filter(
                            ab_idNum_referred=isolate,
                            ab_Abx_code=whonet_code
                        ).delete()

                    continue

                # ----------------------------
                # CREATE / UPDATE ENTRY
                # ----------------------------

                if is_retest:

                    entry, created_flag = AntibioticEntry.objects.update_or_create(

                        ab_idNum_referred=isolate,
                        ab_Abx_code=whonet_code,

                        defaults={

                            "ab_AccessionNo": isolate.AccessionNo,
                            "ab_RefNo": isolate.RefNo,

                            "ab_Retest_Antibiotic": abx_obj.Antibiotic,
                            "ab_Retest_Abx": abx_obj.Abx_code,

                            "ab_Retest_DiskValue": disk_val,
                            "ab_Retest_MICValue": mic_val,

                            "ab_Retest_Disk_enRIS": disk_ris,
                            "ab_Retest_MIC_enRIS": mic_ris,
                            "ab_Retest_MIC_operand": mic_operand,
                        }
                    )

                else:

                    entry, created_flag = AntibioticEntry.objects.update_or_create(

                        ab_idNum_referred=isolate,
                        ab_Abx_code=whonet_code,

                        defaults={

                            "ab_AccessionNo": isolate.AccessionNo,
                            "ab_RefNo": isolate.RefNo,

                            "ab_Antibiotic": abx_obj.Antibiotic,
                            "ab_Abx": abx_obj.Abx_code,

                            "ab_Disk_value": disk_val,
                            "ab_MIC_value": mic_val,

                            "ab_Disk_enRIS": disk_ris,
                            "ab_MIC_enRIS": mic_ris,
                            "ab_MIC_operand": mic_operand,
                        }
                    )

                entry.ab_breakpoints_id.clear()

                bp_applied = False

                # ----------------------------
                # DISK BREAKPOINT
                # ----------------------------

                if disk_val is not None and disk_key and disk_key in breakpoint_keys:

                    bp_disk = BreakpointsTable.objects.filter(
                        Whonet_Abx__iexact=disk_key,
                        Year=effective_year,
                        Test_Method="DISK",
                        Org__in=[resolved_ars_org, ""]
                    ).order_by("-Org").first()

                    if bp_disk:

                        entry.ab_breakpoints_id.set([bp_disk])

                        if is_retest:

                            entry.ab_Ret_Org = bp_disk.Org
                            entry.ab_Ret_R_breakpoint = bp_disk.R_val
                            entry.ab_Ret_I_breakpoint = bp_disk.I_val
                            entry.ab_Ret_SDD_breakpoint = bp_disk.SDD_val
                            entry.ab_Ret_S_breakpoint = bp_disk.S_val

                        else:

                            entry.ab_Site_Org = bp_disk.Org
                            entry.ab_R_breakpoint = bp_disk.R_val
                            entry.ab_I_breakpoint = bp_disk.I_val
                            entry.ab_SDD_breakpoint = bp_disk.SDD_val
                            entry.ab_S_breakpoint = bp_disk.S_val

                        bp_applied = True

                # ----------------------------
                # MIC BREAKPOINT
                # ----------------------------

                if mic_val is not None and mic_key and mic_key in breakpoint_keys:

                    bp_mic = BreakpointsTable.objects.filter(
                        Whonet_Abx__iexact=mic_key,
                        Year=effective_year,
                        Test_Method="MIC",
                        Org__in=[resolved_ars_org, ""]
                    ).order_by("-Org").first()

                    if bp_mic:

                        entry.ab_breakpoints_id.set([bp_mic])

                        if is_retest:

                            entry.ab_Ret_Org = bp_mic.Org
                            entry.ab_Ret_R_breakpoint = bp_mic.R_val
                            entry.ab_Ret_I_breakpoint = bp_mic.I_val
                            entry.ab_Ret_SDD_breakpoint = bp_mic.SDD_val
                            entry.ab_Ret_S_breakpoint = bp_mic.S_val
                            entry.ab_Retest_Alert_val = bp_mic.Alert_val

                        else:

                            entry.ab_Site_Org = bp_mic.Org
                            entry.ab_R_breakpoint = bp_mic.R_val
                            entry.ab_I_breakpoint = bp_mic.I_val
                            entry.ab_SDD_breakpoint = bp_mic.SDD_val
                            entry.ab_S_breakpoint = bp_mic.S_val
                            entry.ab_Alert_val = bp_mic.Alert_val

                        bp_applied = True

                # ----------------------------
                # NO BREAKPOINT
                # ----------------------------

                if not bp_applied:

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

                if created_flag:
                    created += 1
                else:
                    updated += 1

    wb.close()

    messages.success(
        request,
        f"{created} antibiotics uploaded successfully. "
        f"{updated} updated, {skipped} skipped."
    )

    return redirect("show_raw_antibiotic")

















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
        "wgs_app/show_final_antibiotic.html",
        {
            "page_obj": page_obj,
            "abx_data": dict(page_obj.object_list),
            "abx_codes": abx_columns,
            "total_records": len(abx_data),  # number of isolates
        }
    )



# updated version
@login_required
def show_raw_antibiotic(request):

    entries = (
        AntibioticEntry.objects
        .select_related("ab_idNum_referred")
        .order_by("ab_idNum_referred__AccessionNo")
    )

    abx_data = {}
    abx_columns = set()

    for entry in entries:

        # Skip invalid entries
        if not entry.ab_Abx_code or not entry.ab_idNum_referred:
            continue

        acc = entry.ab_idNum_referred.AccessionNo
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
        "wgs_app/show_raw_antibiotic.html",
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
def delete_raw_antibiotic(request, pk):

    target = get_object_or_404(AntibioticEntry, pk=pk)
    acc = target.ab_idNum_referred.AccessionNo

    if request.method == "POST":
        AntibioticEntry.objects.filter(
            ab_idNum_referred__AccessionNo=acc
        ).delete()

        messages.success(
            request,
            f"All antibiotic records for accession {acc} deleted successfully!"
        )
        return redirect("show_raw_antibiotic")

    messages.error(request, "Invalid request method.")
    return redirect("show_raw_antibiotic")





@login_required
def delete_all_final_antibiotic(request):
    Final_AntibioticEntry.objects.all().delete()
    messages.success(request, "Final antibiotic entries have been deleted successfully.")
    return redirect('show_final_antibiotic')  # Redirect to the table view




@login_required
def delete_all_raw_antibiotic(request):
    AntibioticEntry.objects.all().delete()
    messages.success(request, "Raw antibiotic entries have been deleted successfully.")
    return redirect('show_raw_antibiotic')  # Redirect to the table view





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



@login_required
def delete_rawantibiotic_by_date(request):

    if request.method == "POST":
        upload_date_str = request.POST.get("upload_date")

        if not upload_date_str:
            messages.error(request, "Please select an upload date to delete.")
            return redirect("show_raw_antibiotic")

        upload_date = parse_date(upload_date_str)

        if not upload_date:
            messages.error(request, f"Invalid date format: {upload_date_str}")
            return redirect("show_raw_antibiotic")

        deleted_count, _ = AntibioticEntry.objects.filter(
            ab_Date_uploaded_rd=upload_date
        ).delete()

        messages.success(
            request,
            f"Deleted {deleted_count} Antibiotic entries uploaded on {upload_date}."
        )
        return redirect("show_raw_antibiotic")

    messages.error(request, "Invalid request method.")
    return redirect("show_raw_antibiotic")




@login_required(login_url="/login/")
def export_Final_Antibioticentry(request):
    objects = Final_AntibioticEntry.objects.all()
    data = []

    for obj in objects:
        data.append({
            "ab_idNum_f_referred": obj.ab_idNum_f_referred.f_AccessionNo if obj.ab_idNum_f_referred else None,
            "f_Accession_No": obj.ab_AccessionNo,
            "f_Site_Org": obj.ab_Site_Org,
            "Antibiotic": obj.ab_Antibiotic,
            "Abx_code": obj.ab_Abx_code,
            "Abx": obj.ab_Abx,
            "Disk_value": obj.ab_Disk_value,
            "Disk_enRIS": obj.ab_Disk_enRIS,
            "MIC_operand": obj.ab_MIC_operand,
            "MIC_value": obj.ab_MIC_value,
            "MIC_enRIS": obj.ab_MIC_enRIS,
            "f_Ars_Org":obj.ab_Ret_Org,
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
    file_path = "Final_AntibioticEntry.xlsx"

    # Convert data to DataFrame and save as Excel
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False)

    # Return the file as a response
    return FileResponse(open(file_path, "rb"), as_attachment=True, filename="Final_AntibioticEntry.xlsx")





@login_required(login_url="/login/")
def export_raw_Antibioticentry(request):
    objects = AntibioticEntry.objects.all()
    data = []

    for obj in objects:
        data.append({
            "ab_idNum_f_referred": obj.ab_idNum_referred.AccessionNo if obj.ab_idNum_referred else None,
            "f_Accession_No": obj.ab_AccessionNo,
            "f_Site_Org": obj.ab_Site_Org,
            "Antibiotic": obj.ab_Antibiotic,
            "Abx_code": obj.ab_Abx_code,
            "Abx": obj.ab_Abx,
            "Disk_value": obj.ab_Disk_value,
            "Disk_enRIS": obj.ab_Disk_enRIS,
            "MIC_operand": obj.ab_MIC_operand,
            "MIC_value": obj.ab_MIC_value,
            "MIC_enRIS": obj.ab_MIC_enRIS,
            "f_Ars_Org":obj.ab_Ret_Org,
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
    file_path = "AntibioticEntry.xlsx"

    # Convert data to DataFrame and save as Excel
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False)

    # Return the file as a response
    return FileResponse(open(file_path, "rb"), as_attachment=True, filename="AntibioticEntry.xlsx")



################ BATCH GENERATOR
############ Auto-Generate Batch
def generate_batches_from_referred():

    from itertools import groupby

    isolates = (
        Referred_Data.objects
        .filter(Batch_id__isnull=True)
        .exclude(Batch_Code__exact="")
        .order_by("Batch_Code", "AccessionNo")
    )

    created_batches = 0

    for batch_code, group in groupby(isolates, key=lambda x: x.Batch_Code):

        group = list(group)

        if not group:
            continue

        first = group[0]

        site_code = first.SiteCode
        referral_date = first.Referral_Date
        batch_name = first.Batch_Name or batch_code
        batch_no = first.BatchNo or "1"
        total_batch = first.Total_batch or "1"
        ref_no = first.RefNo or ""

        site_name = ""
        site_obj = SiteData.objects.filter(SiteCode=site_code).first()
        if site_obj:
            site_name = site_obj.SiteName

        batch_obj, created = Batch_Table.objects.get_or_create(
            bat_Batch_Code=batch_code,
            defaults={
                "bat_Batch_Name": batch_name,
                "bat_Site_Name": site_name,
                "bat_SiteCode": site_code,
                "bat_Referral_Date": referral_date,
                "bat_RefNo": ref_no,
                "bat_BatchNo": batch_no,
                "bat_Total_batch": total_batch
            }
        )

        # -------- Assign bat_seq --------
        seq = 1
        updated_isolates = []

        for iso in group:

            iso.Batch_id = batch_obj
            iso.Batch_Code = batch_code
            iso.Batch_Name = batch_name
            iso.bat_seq = seq

            updated_isolates.append(iso)

            seq += 1

        Referred_Data.objects.bulk_update(
            updated_isolates,
            ["Batch_id", "Batch_Code", "Batch_Name", "bat_seq"]
        )


        created_batches += 1

    return created_batches





# @login_required
# @transaction.atomic
# def create_batch_from_referred(request):

#     isolates = (
#         Referred_Data.objects
#         .filter(Batch_id__isnull=True)
#         .order_by("SiteCode", "Referral_Date", "AccessionNo")
#     )

#     from itertools import groupby

#     created_batches = 0

#     for (site, ref_date), group in groupby(
#         isolates,
#         key=lambda x: (x.SiteCode, x.Referral_Date)
#     ):

#         group = list(group)

#         if not group:
#             continue

#         year_short = ref_date.strftime("%y")
#         year_long = ref_date.strftime("%m%d%Y")

#         ref_numbers = [
#             int(i.AccessionNo[-4:])
#             for i in group
#             if i.AccessionNo[-4:].isdigit()
#         ]

#         start_ref = min(ref_numbers)
#         end_ref = max(ref_numbers)

#         ref_range = f"{start_ref}-{end_ref}"

#         batch_code = f"{site}_{year_long}_1.1_{ref_range}"

#         site_name = ""
#         site_obj = SiteData.objects.filter(SiteCode=site).first()
#         if site_obj:
#             site_name = site_obj.SiteName

#         batch_obj = Batch_Table.objects.create(
#             bat_Batch_Name=batch_code,
#             bat_AccessionNo=", ".join(i.AccessionNo for i in group),
#             bat_Batch_Code=batch_code,
#             bat_Site_Name=site_name,
#             bat_SiteCode=site,
#             bat_Referral_Date=ref_date,
#             bat_RefNo=ref_range,
#             bat_BatchNo="1",
#             bat_Total_batch="1"
#         )

#         seq = 1

#         for iso in group:

#             iso.Batch_id = batch_obj
#             iso.Batch_Code = batch_code
#             iso.Batch_Name = batch_code
#             iso.bat_seq = seq

#             iso.save(update_fields=[
#                 "Batch_id",
#                 "Batch_Code",
#                 "Batch_Name",
#                 "bat_seq"
#             ])

#             seq += 1

#         created_batches += 1

#     messages.success(
#         request,
#         f"{created_batches} batch(es) created successfully."
#     )

#     return redirect("show_batches")


@login_required
@transaction.atomic
def create_batch_from_referred(request):

    created_batches = generate_batches_from_referred()

    messages.success(
        request,
        f"{created_batches} batch(es) created successfully."
    )

    return redirect("show_batches")