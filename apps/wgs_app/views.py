
from io import TextIOWrapper
import io
import re
from django.db import transaction
import csv

from django.http import HttpResponse
from django.shortcuts import render, redirect
from .forms import *
from apps.home.forms import *
import pandas as pd
from apps.home.models import *
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
        referred_form = ReferredUploadForm(request.POST, request.FILES)

        referred_uploaded = False
        project_saved = False
        fastq_uploaded = False
        gambit_uploaded = False
        mlst_uploaded = False
        checkm2_uploaded = False
        assembly_uploaded = False
        amrfinder_uploaded = False
        
         # WGS Project
        if referred_form.is_valid():
            form.save()
            referred_uploaded = True

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
        if project_saved or referred_uploaded or fastq_uploaded or gambit_uploaded or mlst_uploaded or checkm2_uploaded or assembly_uploaded or amrfinder_uploaded:
            return redirect("upload_wgs_view")

    else:
        form = WGSProjectForm()
        referred_form = ReferredUploadForm()
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
    referred_with_wgs = Referred_Data.objects.filter(
        AccessionNo__isnull=False
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
                    "referred_form": ReferredUploadForm(),
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

                # ✅ Extract prefix that includes ARS (e.g., "18ARS")
                prefix_match = re.search(r"(\d*ARS)", name)
                prefix = prefix_match.group(1) if prefix_match else "ARS"

                # ✅ Extract numeric digits after the site code (e.g., 0055)
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
                    referred_obj = Referred_Data.objects.filter(
                        AccessionNo=fastq_accession
                    ).first()

                connect_project, _ = WGS_Project.objects.get_or_create(
                    Ref_Accession=referred_obj if referred_obj else None,
                    defaults={
                        "WGS_GambitSummary": False,
                        "WGS_FastqSummary": False,
                        "WGS_MlstSummary": False,
                        "WGS_Checkm2Summary": False,
                        "WGS_AssemblySummary": False,
                        "WGS_AmrfinderSummary": False,
                    },
                )

                connect_project.WGS_FastQ_Acc = fastq_accession
                connect_project.WGS_FastqSummary = (
                    bool(fastq_accession)
                    and bool(connect_project.Ref_Accession)
                    and fastq_accession == getattr(connect_project.Ref_Accession, "AccessionNo", None)
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
        "referred_form": ReferredUploadForm(),
        "editing": editing,
    })


@login_required
def show_fastq(request):
    fastq_summaries = FastqSummary.objects.all().order_by("id")  # optional ordering

    total_records = FastqSummary.objects.count()
     # Paginate the queryset to display 20 records per page
    paginator = Paginator(fastq_summaries, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Render the template with paginated data
    return render(
        request,
        "wgs_app/show_fastq.html",
        {"page_obj": page_obj,
         "total_records": total_records,
         },  # only send page_obj
    )


@login_required
def delete_fastq(request, pk):
    fastq_item = get_object_or_404(FastqSummary, pk=pk)

    if request.method == "POST":
        fastq_item.delete()
        messages.success(request, f"Record {fastq_item.sample} deleted successfully!")
        return redirect('show_fastq')  # <-- Correct URL name

    messages.error(request, "Invalid request for deletion.")
    return redirect('show_fastq')  # <-- Correct URL name


def delete_all_fastq(request):
    FastqSummary.objects.all().delete()
    messages.success(request, "FastQ Records have been deleted successfully.")
    return redirect('show_fastq')  # Redirect to the table view



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
                    "referred_form": ReferredUploadForm(),
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

                # Step 1: try to find Referred_Data with this accession
                referred_obj = Referred_Data.objects.filter(
                    AccessionNo=gambit_accession
                ).first()

                # Step 2: create or get WGS_Project
                connect_project, _ = WGS_Project.objects.get_or_create(
                    Ref_Accession=referred_obj if referred_obj else None,
                    defaults={
                        "WGS_GambitSummary": False,
                        "WGS_FastqSummary": False,
                        "WGS_MlstSummary": False,
                        "WGS_Checkm2Summary": False,
                        "WGS_AssemblySummary": False,
                        "WGS_AmrfinderSummary": False,
                    }
                )

                # 🔎 Step 3: update Gambit accession in project
                connect_project.WGS_Gambit_Acc = gambit_accession

                # 🔎 Step 4: summary flag = True if gambit_accession matches Ref_Accession.AccessionNo
                connect_project.WGS_GambitSummary = (
                    bool(connect_project.Ref_Accession) 
                    and gambit_accession == connect_project.Ref_Accession.AccessionNo
                )

                connect_project.save()

                # 🔄 Step 5: update or create Gambit record
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
        "referred_form": ReferredUploadForm(),
        "editing": editing,
    })



@login_required
def show_gambit(request):
    gambit_summaries = Gambit.objects.all()
    
    total_records = Gambit.objects.count()
         # Paginate the queryset to display 20 records per page
    paginator = Paginator(gambit_summaries, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Render the template with paginated data
    return render(
        request,
        "wgs_app/show_gambit.html",
        {"page_obj": page_obj,
         "total_records": total_records,
         },  # only send page_obj
    )


@login_required
def delete_gambit(request, pk):
    gambit_item = get_object_or_404(Gambit, pk=pk)

    if request.method == "POST":
        gambit_item.delete()
        messages.success(request, f"Record {gambit_item.sample} deleted successfully!")
        return redirect('show_gambit')  # <-- Correct URL name

    messages.error(request, "Invalid request for deletion.")
    return redirect('show_gambit')  # <-- Correct URL name


def delete_all_gambit(request):
    Gambit.objects.all().delete()
    messages.success(request, "Gambit Records have been deleted successfully.")
    return redirect('show_gambit')  # Redirect to the table view



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
                "referred_form": ReferredUploadForm(),
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
                Referred_Data.objects.filter(AccessionNo=mlst_accession).first()
                if mlst_accession else None
            )

            # Get or create WGS_Project
            connect_project, _ = WGS_Project.objects.get_or_create(
                Ref_Accession=referred_obj if referred_obj else None,
                defaults={
                    "WGS_GambitSummary": False,
                    "WGS_FastqSummary": False,
                    "WGS_MlstSummary": False,
                    "WGS_Checkm2Summary": False,
                    "WGS_AssemblySummary": False,
                    "WGS_AmrfinderSummary": False,
                }
            )

            # Update project MLST accession and summary status
            connect_project.WGS_Mlst_Acc = mlst_accession
            connect_project.WGS_MlstSummary = (
                mlst_accession
                and bool(connect_project.Ref_Accession)
                and mlst_accession == getattr(connect_project.Ref_Accession, "AccessionNo", None)
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
        "referred_form": ReferredUploadForm(),
        "editing": editing
    })




@login_required
def show_mlst(request):
    mlst_summaries = Mlst.objects.all().order_by("id")  # optional ordering

    total_records = Mlst.objects.count()
     # Paginate the queryset to display 20 records per page
    paginator = Paginator(mlst_summaries, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Render the template with paginated data
    return render(
        request,
        "wgs_app/show_mlst.html",
        {"page_obj": page_obj,
         "total_records": total_records,
         },  # only send page_obj
    )




@login_required
def delete_mlst(request, pk):
    mlst_item = get_object_or_404(Mlst, pk=pk)

    if request.method == "POST":
        mlst_item.delete()
        messages.success(request, f"Record {mlst_item.sample} deleted successfully!")
        return redirect('show_mlst')  # <-- Correct URL name

    messages.error(request, "Invalid request for deletion.")
    return redirect('show_mlst')  # <-- Correct URL name

@login_required
def delete_all_mlst(request):
    Mlst.objects.all().delete()
    messages.success(request, "Mlst Records have been deleted successfully.")
    return redirect('show_mlst')  # Redirect to the table view



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
                "referred_form": ReferredUploadForm(),
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
                Referred_Data.objects.filter(AccessionNo=checkm2_accession).first()
                if checkm2_accession else None
            )

            # Step 2: Create or get WGS_Project
            connect_project, _ = WGS_Project.objects.get_or_create(
                Ref_Accession=referred_obj if referred_obj else None,
                defaults={
                    "WGS_GambitSummary": False,
                    "WGS_FastqSummary": False,
                    "WGS_MlstSummary": False,
                    "WGS_Checkm2Summary": False,
                    "WGS_AssemblySummary": False,
                    "WGS_AmrfinderSummary": False,
                }
            )

            # Step 3: Update project accession & summary flag (safe)
            connect_project.WGS_Checkm2_Acc = checkm2_accession
            connect_project.WGS_Checkm2Summary = (
                checkm2_accession != "" and
                bool(connect_project.Ref_Accession) and
                checkm2_accession == getattr(connect_project.Ref_Accession, "AccessionNo", None)
            )
            connect_project.save()

            # Step 4: Create Checkm2 record
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
        "referred_form": ReferredUploadForm(),
        "editing": editing,
    })








@login_required
def show_checkm2(request):
    checkm2_summaries = Checkm2.objects.all().order_by("id")  # optional ordering

    total_records = Checkm2.objects.count()
     # Paginate the queryset to display 20 records per page
    paginator = Paginator(checkm2_summaries, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Render the template with paginated data
    return render(
        request,
        "wgs_app/show_checkm2.html",
        {"page_obj": page_obj,
         "total_records": total_records,
         },  # only send page_obj
    )




@login_required
def delete_checkm2(request, pk):
    checkm2_item = get_object_or_404(Checkm2, pk=pk)

    if request.method == "POST":
        checkm2_item.delete()
        messages.success(request, f"Record {checkm2_item.Name} deleted successfully!")
        return redirect('show_checkm2')  # <-- Correct URL name

    messages.error(request, "Invalid request for deletion.")
    return redirect('show_checkm2')  # <-- Correct URL name


@login_required
def delete_all_checkm2(request):
    Checkm2.objects.all().delete()
    messages.success(request, "Checkm2 Records have been deleted successfully.")
    return redirect('show_checkm2')  # Redirect to the table view



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
            df = read_uploaded_file(upload.Mlstfile)
            df.columns = df.columns.str.strip().str.replace(".", "", regex=False)
        except Exception as e:
            messages.error(request, f"Error processing MLST file: {e}")
            return render(request, "wgs_app/Add_wgs.html", {
                "form": form,
                "fastq_form": FastqUploadForm(),
                "gambit_form": GambitUploadForm(),
                "mlst_form": MlstUploadForm(),
                "checkm2_form": Checkm2UploadForm(),
                "amrfinder_form": AmrUploadForm(),
                "assembly_form": assembly_form,
                "referred_form": ReferredUploadForm(),
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
                Referred_Data.objects.filter(AccessionNo=assembly_accession).first()
                if assembly_accession else None
            )

            # Step 2: Create or get WGS_Project
            connect_project, _ = WGS_Project.objects.get_or_create(
                Ref_Accession=referred_obj if referred_obj else None,
                defaults={
                    "WGS_GambitSummary": False,
                    "WGS_FastqSummary": False,
                    "WGS_MlstSummary": False,
                    "WGS_Checkm2Summary": False,
                    "WGS_AssemblySummary": False,
                    "WGS_AmrfinderSummary": False,
                }
            )

            # Step 3: Update project accession & summary flag (safe)
            connect_project.WGS_Assembly_Acc = assembly_accession
            connect_project.WGS_AssemblySummary = (
                assembly_accession != "" and
                bool(connect_project.Ref_Accession) and
                assembly_accession == getattr(connect_project.Ref_Accession, "AccessionNo", None)
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
        "referred_form": ReferredUploadForm(),
        "editing": editing,
    })




# @login_required
# def show_assembly(request):
#     assembly_summaries = AssemblyScan.objects.all()
#     return render(request, "wgs_app/show_assembly.html", {"assembly_summaries": assembly_summaries})



@login_required
def show_assembly(request):
    assembly_summaries = AssemblyScan.objects.all().order_by("id")  # optional ordering

    total_records = AssemblyScan.objects.count()
     # Paginate the queryset to display 20 records per page
    paginator = Paginator(assembly_summaries, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Render the template with paginated data
    return render(
        request,
        "wgs_app/show_assembly.html",
        {"page_obj": page_obj,
         "total_records": total_records,
         },  # only send page_obj
    )





@login_required
def delete_assembly(request, pk):
    assembly_item = get_object_or_404(AssemblyScan, pk=pk)

    if request.method == "POST":
        assembly_item.delete()
        messages.success(request, f"Record {assembly_item.sample} deleted successfully!")
        return redirect('show_assembly')  # <-- Correct URL name

    messages.error(request, "Invalid request for deletion.")
    return redirect('show_assembly')  # <-- Correct URL name


@login_required
def delete_all_assembly(request):
    AssemblyScan.objects.all().delete()
    messages.success(request, "AssemblyScan Records have been deleted successfully.")
    return redirect('show_assembly')  # Redirect to the table view



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
                "referred_form": ReferredUploadForm(),
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
                Referred_Data.objects.filter(AccessionNo=amrfinder_accession).first()
                if amrfinder_accession else None
            )

            # Step 2: Create or get WGS_Project
            connect_project, _ = WGS_Project.objects.get_or_create(
                Ref_Accession=referred_obj if referred_obj else None,
                defaults={
                    "WGS_GambitSummary": False,
                    "WGS_FastqSummary": False,
                    "WGS_MlstSummary": False,
                    "WGS_Checkm2Summary": False,
                    "WGS_AssemblySummary": False,
                    "WGS_AmrfinderSummary": False,
                }
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
        "referred_form": ReferredUploadForm(),
        "editing": editing,
    })


@login_required
def show_amrfinder(request):
    amrfinder_summaries = Amrfinderplus.objects.all().order_by("id")  # optional ordering

    total_records = Amrfinderplus.objects.count()
     # Paginate the queryset to display 20 records per page
     
    paginator = Paginator(amrfinder_summaries, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Render the template with paginated data
    return render(
        request,
        "wgs_app/show_amrfinder.html",
        {"page_obj": page_obj,
         "total_records": total_records,
         },  # only send page_obj
    )





@login_required
def delete_amrfinder(request, pk):
    amrfinder_item = get_object_or_404(Amrfinderplus, pk=pk)

    if request.method == "POST":
        amrfinder_item.delete()
        messages.success(request, f"Record {amrfinder_item.name} deleted successfully!")
        return redirect('show_amrfinder')  # <-- Correct URL name

    messages.error(request, "Invalid request for deletion.")
    return redirect('show_amrfinder')  # <-- Correct URL name


@login_required
def delete_all_amrfinder(request):
    Amrfinderplus.objects.all().delete()
    messages.success(request, "AmrfinderPlus Records have been deleted successfully.")
    return redirect('show_amrfinder')  # Redirect to the table view




#### uploading referred data
@login_required
@transaction.atomic
def upload_combined_table(request):
    form = WGSProjectForm()
    referred_form = ReferredUploadForm()
    
    if request.method == "POST" and request.FILES.get("ReferredDataFile"):
        try:
            uploaded_file = request.FILES["ReferredDataFile"]
            file_name = uploaded_file.name.lower()
            
            # Determine file type and read accordingly
            if file_name.endswith('.csv'):
                # Read CSV file
                file = TextIOWrapper(uploaded_file.file, encoding="utf-8-sig")
                reader = csv.DictReader(file)
                rows = list(reader)
            elif file_name.endswith(('.xlsx', '.xls')):
                # Read Excel file
                df = pd.read_excel(uploaded_file)
                # Convert DataFrame to list of dictionaries
                rows = df.to_dict('records')
            else:
                messages.error(request, "Unsupported file format. Please upload CSV, XLSX, or XLS file.")
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

            created_ref, updated_ref, created_abx, updated_abx = 0, 0, 0, 0

            # Get all antibiotic codes known to the system
            known_abx = set(BreakpointsTable.objects.values_list("Whonet_Abx", flat=True))

            # Helper: extract MIC operand and numeric part (handles ≤, ≥, etc.)
            def parse_mic_value(value_str):
                if not value_str or pd.isna(value_str):
                    return "", None
                value_str = str(value_str).strip()
                match = re.match(r"^([<>=≤≥]+)?\s*([\d.]+)$", value_str)
                if match:
                    operand = match.group(1) or ""
                    mic_val = float(match.group(2))
                    return operand, mic_val
                try:
                    return "", float(value_str)
                except ValueError:
                    return "", None

            # === LOOP THROUGH ROWS ===
            for row in rows:
                # Handle both dict keys (CSV) and potential NaN values (Excel)
                accession = row.get("AccessionNo") or row.get("ID_Number")
                if not accession or pd.isna(accession):
                    continue  # skip if missing

                # Convert row values, handling NaN from Excel
                cleaned_row = {}
                for k, v in row.items():
                    if pd.isna(v):
                        cleaned_row[k] = ""
                    else:
                        cleaned_row[k] = v

                # --- Create or update Referred_Data ---
                ref_obj, ref_created = Referred_Data.objects.update_or_create(
                    AccessionNo=str(accession).strip(),
                    defaults={
                        k: v for k, v in cleaned_row.items()
                        if k in [f.name for f in Referred_Data._meta.get_fields()]
                    },
                )
                if ref_created:
                    created_ref += 1
                else:
                    updated_ref += 1

                # --- Create/update AntibioticEntry records ---
                for abx in known_abx:
                    abx_val = cleaned_row.get(f"{abx}", "")
                    abx_ris = cleaned_row.get(f"{abx}_RIS", "")
                    abx_rt_val = cleaned_row.get(f"{abx}_RT", "")
                    abx_rt_ris = cleaned_row.get(f"{abx}_RT_RIS", "")
                    
                    # Convert to string and strip
                    abx_val = str(abx_val).strip() if abx_val else ""
                    abx_ris = str(abx_ris).strip() if abx_ris else ""
                    abx_rt_val = str(abx_rt_val).strip() if abx_rt_val else ""
                    abx_rt_ris = str(abx_rt_ris).strip() if abx_rt_ris else ""

                    # Skip if all empty
                    if not any([abx_val, abx_ris, abx_rt_val, abx_rt_ris]):
                        continue

                    mic_operand, mic_value = parse_mic_value(abx_val)
                    ret_mic_operand, ret_mic_value = parse_mic_value(abx_rt_val)

                    ab_entry, ab_created = AntibioticEntry.objects.update_or_create(
                        ab_idNum_referred=ref_obj,
                        ab_Abx_code=abx,
                        defaults={
                            # Sentinel (Initial) values
                            "ab_MIC_operand": mic_operand or "",
                            "ab_MIC_value": mic_value if mic_value is not None else None,
                            "ab_MIC_RIS": abx_ris or "",
                            "ab_Disk_value": None,
                            "ab_Disk_RIS": "",

                            # Retest (ARSRL) values
                            "ab_Retest_MIC_operand": ret_mic_operand or "",
                            "ab_Retest_MICValue": ret_mic_value if ret_mic_value is not None else None,
                            "ab_Retest_MIC_RIS": abx_rt_ris or "",
                            "ab_Retest_DiskValue": None,
                            "ab_Retest_Disk_RIS": "",
                        },
                    )

                    if ab_created:
                        created_abx += 1
                    else:
                        updated_abx += 1

            messages.success(
                request,
                f" Upload complete! "
                f"{created_ref} new Referred_Data, {updated_ref} updated; "
                f"{created_abx} new AntibioticEntry, {updated_abx} updated."
            )
            return redirect("show_data")

        except Exception as e:
            messages.error(request, f"⚠️ Error processing file: {e}")
            import traceback
            print(traceback.format_exc())  # For debugging

    # --- Default view ---
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



########### Show all WGS project entries for one Referred_Data AccessionNo,
##########  including FastQ, CheckM2, AMRFinder tables.


@login_required
def view_wgs_overview(request):
    referred_list = Referred_Data.objects.all().order_by('AccessionNo')
    table_data = []

    for referred in referred_list:
        projects = WGS_Project.objects.filter(Ref_Accession=referred)

        summary_flags = {
            'fastq': projects.filter(WGS_FastqSummary=True).exists(),
            'mlst': projects.filter(WGS_MlstSummary=True).exists(),
            'checkm2': projects.filter(WGS_Checkm2Summary=True).exists(),
            'assembly': projects.filter(WGS_AssemblySummary=True).exists(),
            'gambit': projects.filter(WGS_GambitSummary=True).exists(),
            'amrfinder': projects.filter(WGS_AmrfinderSummary=True).exists(),
        }

        related_data = {}
        if summary_flags['fastq']:
            related_data['fastq'] = FastqSummary.objects.filter(fastq_project__in=projects)
        if summary_flags['mlst']:
            related_data['mlst'] = Mlst.objects.filter(mlst_project__in=projects)
        if summary_flags['checkm2']:
            related_data['checkm2'] = Checkm2.objects.filter(checkm2_project__in=projects)
        if summary_flags['assembly']:
            related_data['assembly'] = AssemblyScan.objects.filter(assembly_project__in=projects)
        if summary_flags['gambit']:
            related_data['gambit'] = Gambit.objects.filter(gambit_project__in=projects)
        if summary_flags['amrfinder']:
            related_data['amrfinder'] = Amrfinderplus.objects.filter(amrfinder_project__in=projects)

        table_data.append({
            'accession': referred,
            'summary_flags': summary_flags,
            'related_data': related_data,
        })

            # Calculate counts
        counts = {
            'total': len(table_data),
            'fastq': sum(1 for entry in table_data if entry['summary_flags']['fastq']),
            'gambit': sum(1 for entry in table_data if entry['summary_flags']['gambit']),
            'mlst': sum(1 for entry in table_data if entry['summary_flags']['mlst']),
            'checkm2': sum(1 for entry in table_data if entry['summary_flags']['checkm2']),
            'assembly': sum(1 for entry in table_data if entry['summary_flags']['assembly']),
            'amrfinder': sum(1 for entry in table_data if entry['summary_flags']['amrfinder']),
        }
        

    context = {
        'table_data': table_data,
        'counts': counts,
    }

    return render(request, 'wgs_app/Wgs_overview.html', context)



### download all wgs data 
@login_required
def download_all_wgs_data(request):
    """
    Export all WGS data (across all tables) into one Excel file with multiple sheets.
    Each sheet corresponds to one WGS data table.
    """

    # Helper to safely convert queryset → DataFrame
    def qs_to_df(qs, model_name):
        if not qs.exists():
            return pd.DataFrame()
        df = pd.DataFrame.from_records(qs.values())
        df.insert(0, 'Table', model_name)
        return df

    # Gather all data
    fastq_qs = FastqSummary.objects.all().select_related('fastq_project__Ref_Accession')
    mlst_qs = Mlst.objects.all().select_related('mlst_project__Ref_Accession')
    checkm2_qs = Checkm2.objects.all().select_related('checkm2_project__Ref_Accession')
    assembly_qs = AssemblyScan.objects.all().select_related('assembly_project__Ref_Accession')
    amrfinder_qs = Amrfinderplus.objects.all().select_related('amrfinder_project__Ref_Accession')
    gambit_qs = Gambit.objects.all().select_related('gambit_project__Ref_Accession')

    # Convert to DataFrames
    fastq_df = qs_to_df(fastq_qs, "FastqSummary")
    mlst_df = qs_to_df(mlst_qs, "Mlst")
    checkm2_df = qs_to_df(checkm2_qs, "CheckM2")
    assembly_df = qs_to_df(assembly_qs, "AssemblyScan")
    amrfinder_df = qs_to_df(amrfinder_qs, "Amrfinderplus")
    gambit_df = qs_to_df(gambit_qs, "Gambit")

    # Add Referred Accession to each if possible
    def add_ref_accession(df, qs, rel_field):
        if df.empty:
            return df
        ref_map = {}
        for obj in qs:
            ref_acc = getattr(obj, rel_field).Ref_Accession.AccessionNo if getattr(obj, rel_field).Ref_Accession else None
            ref_map[obj.id] = ref_acc
        df.insert(1, 'Ref_Accession', df['id'].map(ref_map))
        return df

    fastq_df = add_ref_accession(fastq_df, fastq_qs, 'fastq_project')
    mlst_df = add_ref_accession(mlst_df, mlst_qs, 'mlst_project')
    checkm2_df = add_ref_accession(checkm2_df, checkm2_qs, 'checkm2_project')
    assembly_df = add_ref_accession(assembly_df, assembly_qs, 'assembly_project')
    amrfinder_df = add_ref_accession(amrfinder_df, amrfinder_qs, 'amrfinder_project')
    gambit_df = add_ref_accession(gambit_df, gambit_qs, 'gambit_project')

    # Combine all into Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        fastq_df.to_excel(writer, index=False, sheet_name="FastQ")
        mlst_df.to_excel(writer, index=False, sheet_name="MLST")
        checkm2_df.to_excel(writer, index=False, sheet_name="CheckM2")
        assembly_df.to_excel(writer, index=False, sheet_name="Assembly")
        amrfinder_df.to_excel(writer, index=False, sheet_name="AMRFinder")
        gambit_df.to_excel(writer, index=False, sheet_name="Gambit")

    # Create response
    output.seek(0)
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="All_WGS_Data.xlsx"'
    return response

## download only matched Accessions
@login_required
def download_matched_wgs_data(request):
    """
    Export only WGS data where accession numbers match across ALL WGS tables.
    That means the same Ref_Accession exists in Fastq, MLST, CheckM2, Assembly, AMRFinder, and Gambit.
    """

    # Step 1: Get all accession numbers that appear in each table
    fastq_acc = set(FastqSummary.objects.filter(fastq_project__Ref_Accession__isnull=False)
                    .values_list('fastq_project__Ref_Accession__AccessionNo', flat=True))
    mlst_acc = set(Mlst.objects.filter(mlst_project__Ref_Accession__isnull=False)
                    .values_list('mlst_project__Ref_Accession__AccessionNo', flat=True))
    checkm2_acc = set(Checkm2.objects.filter(checkm2_project__Ref_Accession__isnull=False)
                    .values_list('checkm2_project__Ref_Accession__AccessionNo', flat=True))
    assembly_acc = set(AssemblyScan.objects.filter(assembly_project__Ref_Accession__isnull=False)
                    .values_list('assembly_project__Ref_Accession__AccessionNo', flat=True))
    amrfinder_acc = set(Amrfinderplus.objects.filter(amrfinder_project__Ref_Accession__isnull=False)
                    .values_list('amrfinder_project__Ref_Accession__AccessionNo', flat=True))
    gambit_acc = set(Gambit.objects.filter(gambit_project__Ref_Accession__isnull=False)
                    .values_list('gambit_project__Ref_Accession__AccessionNo', flat=True))

    # Step 2: Find the intersection (accessions present in all WGS tables)
    matched_accessions = fastq_acc & mlst_acc & checkm2_acc & assembly_acc & amrfinder_acc & gambit_acc

    if not matched_accessions:
        # If no matches, return a simple message instead of an empty file
        response = HttpResponse("No accessions have complete WGS data across all tables.", content_type="text/plain")
        return response

    # Step 3: Query only data with matched Ref_Accession values
    fastq_qs = FastqSummary.objects.filter(fastq_project__Ref_Accession__AccessionNo__in=matched_accessions)
    mlst_qs = Mlst.objects.filter(mlst_project__Ref_Accession__AccessionNo__in=matched_accessions)
    checkm2_qs = Checkm2.objects.filter(checkm2_project__Ref_Accession__AccessionNo__in=matched_accessions)
    assembly_qs = AssemblyScan.objects.filter(assembly_project__Ref_Accession__AccessionNo__in=matched_accessions)
    amrfinder_qs = Amrfinderplus.objects.filter(amrfinder_project__Ref_Accession__AccessionNo__in=matched_accessions)
    gambit_qs = Gambit.objects.filter(gambit_project__Ref_Accession__AccessionNo__in=matched_accessions)

    # Step 4: Convert each queryset into a DataFrame
    def qs_to_df(qs, model_name, rel_field):
        if not qs.exists():
            return pd.DataFrame()
        df = pd.DataFrame.from_records(qs.values())
        df.insert(0, "Table", model_name)
        df.insert(1, "Ref_Accession", [
            getattr(getattr(obj, rel_field).Ref_Accession, "AccessionNo", None) for obj in qs
        ])
        return df

    fastq_df = qs_to_df(fastq_qs, "FastqSummary", "fastq_project")
    mlst_df = qs_to_df(mlst_qs, "Mlst", "mlst_project")
    checkm2_df = qs_to_df(checkm2_qs, "Checkm2", "checkm2_project")
    assembly_df = qs_to_df(assembly_qs, "AssemblyScan", "assembly_project")
    amrfinder_df = qs_to_df(amrfinder_qs, "Amrfinderplus", "amrfinder_project")
    gambit_df = qs_to_df(gambit_qs, "Gambit", "gambit_project")

    # Step 5: Write to Excel (multi-sheet)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        fastq_df.to_excel(writer, index=False, sheet_name="FastQ")
        mlst_df.to_excel(writer, index=False, sheet_name="MLST")
        checkm2_df.to_excel(writer, index=False, sheet_name="CheckM2")
        assembly_df.to_excel(writer, index=False, sheet_name="Assembly")
        amrfinder_df.to_excel(writer, index=False, sheet_name="AMRFinder")
        gambit_df.to_excel(writer, index=False, sheet_name="Gambit")

    output.seek(0)
    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="Matched_WGS_Data.xlsx"'
    return response