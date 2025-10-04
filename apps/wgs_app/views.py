from django.shortcuts import render, redirect
from .forms import *
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

        project_saved = False
        fastq_uploaded = False
        gambit_uploaded = False
        mlst_uploaded = False
        checkm2_uploaded = False
        assembly_uploaded = False
        amrfinder_uploaded = False

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
        if project_saved or fastq_uploaded or gambit_uploaded or mlst_uploaded or checkm2_uploaded or assembly_uploaded or amrfinder_uploaded:
            return redirect("upload_wgs_view")

    else:
        form = WGSProjectForm()
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
    wgs_projects = WGS_Project.objects.all().order_by("id")  # optional ordering

    total_records = WGS_Project.objects.count()
     # Paginate the queryset to display 20 records per page
    paginator = Paginator(wgs_projects, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Render the template with paginated data
    return render(
        request,
        "wgs_app/show_wgs_proj.html",
        {"page_obj": page_obj,
         "total_records": total_records,
         },  # only send page_obj
    )

@login_required
def delete_wgs(request, pk):
    wgs_item = get_object_or_404(WGS_Project, pk=pk)

    if request.method == "POST":
        wgs_item.delete()
        messages.success(request, f"Record {wgs_item.Ref_Accession} deleted successfully!")
        return redirect('show_wgs_projects')  # <-- Correct URL name

    messages.error(request, "Invalid request for deletion.")
    return redirect('show_wgs_projects')  # <-- Correct URL name

def format_fastq_accession(raw_name: str, site_codes) -> str:
    """
    Convert raw sample name like:
        15ARS-BGH0054-20220718A
    into:
        15ARS_BGH0054

    Returns "" if it doesn’t match expected pattern or site not found.
    """
    if not raw_name:
        return ""

    # Match PREFIX (15ARS), site (BGH), number (0054)
    match = re.match(r"^(?P<prefix>\d+ARS)-(?P<site>[A-Z]{2,6})(?P<num>\d+)", raw_name, re.IGNORECASE)
    if not match:
        return ""

    site = match.group("site").upper()
    if site not in site_codes:
        return ""

    return f"{match.group('prefix')}_{site}{match.group('num')}"

@login_required
def upload_fastq(request):
    form = WGSProjectForm()
    fastq_form = FastqUploadForm()
    editing = False  

    if request.method == "POST" and request.FILES.get("fastqfile"):
        fastq_form = FastqUploadForm(request.POST, request.FILES)
        if fastq_form.is_valid():
            upload = fastq_form.save()
            excel_file = upload.fastqfile

            # Load Excel
            df = pd.read_excel(excel_file)
            df.columns = df.columns.str.strip().str.replace(".", "", regex=False)

            # Load valid site codes from DB
            site_codes = set(SiteData.objects.values_list("SiteCode", flat=True))

            

            for _, row in df.iterrows():
                sample_name = str(row.get("sample", "")).strip()
                fastq_accession = format_fastq_accession(sample_name, site_codes)

                # Look up in referred data
                referred_obj = (
                    Referred_Data.objects.filter(AccessionNo=fastq_accession).first()
                    if fastq_accession else ""
                )

                # Create or update project
                connect_project, _ = WGS_Project.objects.get_or_create(
                    Ref_Accession=referred_obj,
                    defaults={
                        "WGS_GambitSummary": False,
                        "WGS_FastqSummary": False,
                        "WGS_MlstSummary": False,
                        "WGS_Checkm2Summary": False,
                        "WGS_AssemblySummary": False,
                        "WGS_AmrfinderSummary": False
                    }
                )

                connect_project.WGS_FastQ_Acc = fastq_accession
                connect_project.WGS_FastqSummary = (
                    bool(referred_obj)
                    and fastq_accession == getattr(referred_obj, "AccessionNo", None)
                )
                connect_project.save()

                # Save fastq summary each time
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
                    raw_reads_qc_summary=row.get("raw_reads_qc_summary", "")
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
            upload = gambit_form.save()
            excel_file = upload.GambitFile

            df = pd.read_excel(excel_file)
            df.columns = df.columns.str.replace(".", "_", regex=False)  # normalize column names

            for _, row in df.iterrows():
                sample_name = str(row.get("sample", "")).strip()
                gambit_accession = "_".join(sample_name.split("-")[:2])  # parse accession

                # 🔎 Step 1: try to find Referred_Data with this accession
                referred_obj = Referred_Data.objects.filter(
                    AccessionNo=gambit_accession
                ).first()

                # 🔎 Step 2: create or get WGS_Project
                connect_project, _ = WGS_Project.objects.get_or_create(
                    Ref_Accession=referred_obj if referred_obj else None,
                    defaults={
                        "WGS_GambitSummary": False,
                        "WGS_FastqSummary": False,
                        "WGS_MlstSummary": False,
                        "WGS_Checkm2Summary": False,
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
                Gambit.objects.update_or_create(
                    Gambit_Accession=gambit_accession,
                    defaults={
                        "gambit_project": connect_project,
                        "sample": sample_name,
                        "predicted_name": row.get("predicted_name", ""),
                        "predicted_rank": row.get("predicted_rank", ""),
                        "predicted_ncbi_id": row.get("predicted_ncbi_id", ""),
                        "predicted_threshold": row.get("predicted_threshold", ""),
                        "closest_distance": row.get("closest_distance", ""),
                        "closest_description": row.get("closest_description", ""),
                        "next_name": row.get("next_name", ""),
                        "next_rank": row.get("next_rank", ""),
                        "next_ncbi_id": row.get("next_ncbi_id", ""),
                        "next_threshold": row.get("next_threshold", ""),
                    },
                )

            messages.success(request, "Gambit records updated successfully.")
            return redirect("show_gambit")

    return render(request, "wgs_app/Add_wgs.html", {
        "form": form,
        "fastq_form": FastqUploadForm(),
        "gambit_form": gambit_form,
        "mlst_form": MlstUploadForm(),
        "checkm2_form": Checkm2UploadForm(),
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
        if mlst_form.is_valid():
            upload = mlst_form.save()
            excel_file = upload.Mlstfile

            # Read Excel
            df = pd.read_excel(excel_file)
            df.columns = df.columns.str.strip().str.replace(".", "_", regex=False)  # normalize headers


            site_codes = set(SiteData.objects.values_list("SiteCode", flat=True))
            
                        # helper to build accession
            def format_mlst_accession(raw_name: str, site_codes: set) -> str:
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

                # 1) look for SITE#### where SITE is valid
                for part in parts[1:]:
                    m = re.match(r"^([A-Za-z]{2,6})(\d+)$", part)
                    if m:
                        letters, digits = m.group(1).upper(), m.group(2)
                        if letters in site_codes:
                            return f"{prefix}_{letters}{digits}"

                # 2) exact site code, then try to grab digits from next part
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

                return ""

            print("Total rows in dataframe:", len(df))

            for _, row in df.iterrows():
                # Extract sample name
                full_path = str(row.get("name", "")).strip()
                mlst_accession = format_mlst_accession(full_path, site_codes)

                # Step 1: try to find Referred_Data with this accession (only if non-blank)
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

                # Step 3: update project accession & summary flag (safe)
                connect_project.WGS_Mlst_Acc = mlst_accession
                connect_project.WGS_MlstSummary = (
                    mlst_accession != "" and
                    bool(connect_project.Ref_Accession) and
                    mlst_accession == getattr(connect_project.Ref_Accession, "AccessionNo", None)
                )
                connect_project.save()

                # Update or create Mlst record
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

    return render(request, "wgs_app/Add_wgs.html", {
        "form": form,
        "fastq_form": FastqUploadForm(),
        "gambit_form": GambitUploadForm(),
        "mlst_form": mlst_form,
        "checkm2_form": Checkm2UploadForm(),
        "assembly_form": AssemblyUploadForm(),
        "amrfinder_form": AmrUploadForm(),
        "editing": editing,
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
        if checkm2_form.is_valid():
            upload = checkm2_form.save()
            excel_file = upload.Checkm2file

            df = pd.read_excel(excel_file)
            df.columns = df.columns.str.replace(".", "", regex=False)  # normalize column names


            site_codes = set(SiteData.objects.values_list("SiteCode", flat=True))

                        # helper to build accession
            def format_checkm2_accession(raw_name: str) -> str:
                if not raw_name:
                    return ""
                # take basename and remove extension
                base = os.path.basename(raw_name)
                base_noext = os.path.splitext(base)[0].strip()
                # must contain ARS to be eligible
                if "ARS" not in base_noext:
                    return ""
                parts = re.split(r"[-_]", base_noext)
                if not parts:
                    return ""
                prefix = parts[0]  # e.g. "24ARS" or "22ARS"

                # 1) look for a part like LETTERS + DIGITS where LETTERS is a valid site code
                for part in parts[1:]:
                    m = re.match(r"^([A-Za-z]{2,6})(\d+)$", part)
                    if m:
                        letters = m.group(1).upper()
                        digits = m.group(2)
                        if letters in site_codes:
                            return f"{prefix}_{letters}{digits}"

                # 2) look for an exact sitecode part, then try to extract digits from the next part
                for i in range(1, len(parts)):
                    part = parts[i]
                    if part.upper() in site_codes:
                        letters = part.upper()
                        digits = ""
                        # try the next part for a letters+digits pattern or digits
                        if i + 1 < len(parts):
                            next_part = parts[i + 1]
                            m2 = re.match(r"^([A-Za-z]{2,6})(\d+)$", next_part)
                            if m2:
                                digits = m2.group(2)
                            else:
                                # fallback: grab the first run of digits in next_part
                                dmatch = re.search(r"(\d+)", next_part)
                                if dmatch:
                                    digits = dmatch.group(1)
                        # fallback: extract digits from current part
                        if not digits:
                            dmatch2 = re.search(r"(\d+)", part)
                            if dmatch2:
                                digits = dmatch2.group(1)
                        return f"{prefix}_{letters}{digits}" if digits else f"{prefix}_{letters}"

                # 3) as a last attempt, find any part that contains a valid sitecode prefix
                for part in parts[1:]:
                    m = re.match(r"^([A-Za-z]{2,6})(\d+)$", part)
                    if m and m.group(1).upper() in site_codes:
                        return f"{prefix}_{m.group(1).upper()}{m.group(2)}"

                # none matched → return blank
                return ""

            print("Total rows in dataframe:", len(df))
            
            for _, row in df.iterrows():
                sample_name = str(row.get("Name", "")).strip().replace(".fna", "")
                checkm2_accession = format_checkm2_accession(sample_name)


                # Step 1: try to find Referred_Data with this accession (only if non-blank)
                referred_obj = (
                    Referred_Data.objects.filter(AccessionNo=checkm2_accession).first()
                    if checkm2_accession else None
                )

                # 🔎 Step 2: create or get WGS_Project
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

               # Step 3: update project accession & summary flag (safe)
                connect_project.WGS_Checkm2_Acc = checkm2_accession
                connect_project.WGS_Checkm2Summary = (
                    checkm2_accession != "" and
                    bool(connect_project.Ref_Accession) and
                    checkm2_accession == getattr(connect_project.Ref_Accession, "AccessionNo", None)
                )

                connect_project.save()

                # 🔄 Step 4: get or create Checkm2 record
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
        if assembly_form.is_valid():
            upload = assembly_form.save()
            excel_file = upload.Assemblyfile

            df = pd.read_excel(excel_file)
            df.columns = df.columns.str.replace(".", "_", regex=False)  # normalize column names


            site_codes = set(SiteData.objects.values_list("SiteCode", flat=True))
            # helper to build accession
            def format_assembly_accession(raw_name: str) -> str:
                if not raw_name:
                    return ""
                # take basename and remove extension
                base = os.path.basename(raw_name)
                base_noext = os.path.splitext(base)[0].strip()
                # must contain ARS to be eligible
                if "ARS" not in base_noext:
                    return ""
                parts = re.split(r"[-_]", base_noext)
                if not parts:
                    return ""
                prefix = parts[0]  # e.g. "24ARS" or "22ARS"

                # 1) look for a part like LETTERS + DIGITS where LETTERS is a valid site code
                for part in parts[1:]:
                    m = re.match(r"^([A-Za-z]{2,6})(\d+)$", part)
                    if m:
                        letters = m.group(1).upper()
                        digits = m.group(2)
                        if letters in site_codes:
                            return f"{prefix}_{letters}{digits}"

                # 2) look for an exact sitecode part, then try to extract digits from the next part
                for i in range(1, len(parts)):
                    part = parts[i]
                    if part.upper() in site_codes:
                        letters = part.upper()
                        digits = ""
                        # try the next part for a letters+digits pattern or digits
                        if i + 1 < len(parts):
                            next_part = parts[i + 1]
                            m2 = re.match(r"^([A-Za-z]{2,6})(\d+)$", next_part)
                            if m2:
                                digits = m2.group(2)
                            else:
                                # fallback: grab the first run of digits in next_part
                                dmatch = re.search(r"(\d+)", next_part)
                                if dmatch:
                                    digits = dmatch.group(1)
                        # fallback: extract digits from current part
                        if not digits:
                            dmatch2 = re.search(r"(\d+)", part)
                            if dmatch2:
                                digits = dmatch2.group(1)
                        return f"{prefix}_{letters}{digits}" if digits else f"{prefix}_{letters}"

                # 3) as a last attempt, find any part that contains a valid sitecode prefix
                for part in parts[1:]:
                    m = re.match(r"^([A-Za-z]{2,6})(\d+)$", part)
                    if m and m.group(1).upper() in site_codes:
                        return f"{prefix}_{m.group(1).upper()}{m.group(2)}"

                # none matched → return blank
                return ""

            print("Total rows in dataframe:", len(df))



            for _, row in df.iterrows():
                sample_name = str(row.get("sample", "")).strip()
                assembly_accession = format_assembly_accession(sample_name)


                # Step 1: try to find Referred_Data with this accession (only if non-blank)
                referred_obj = (
                    Referred_Data.objects.filter(AccessionNo=assembly_accession).first()
                    if assembly_accession else None
                )


                # 🔎 Step 2: create or get WGS_Project
                connect_project, _ = WGS_Project.objects.get_or_create(
                    Ref_Accession=referred_obj if referred_obj else None,
                    defaults={
                        "WGS_GambitSummary": False,
                        "WGS_FastqSummary": False,
                        "WGS_MlstSummary": False,
                        "WGS_Checkm2Summary": False,
                        "WGS_AssemblySummary": False,
                        "WGS_AmrfinderSummary": False
                    }
                )

                # Step 3: update project accession & summary flag (safe)
                connect_project.WGS_Assembly_Acc = assembly_accession
                connect_project.WGS_AssemblySummary = (
                    assembly_accession != "" and
                    bool(connect_project.Ref_Accession) and
                    assembly_accession == getattr(connect_project.Ref_Accession, "AccessionNo", None)
                )
                connect_project.save()

                # 🔄 Step 4: get or create AssemblyScan record
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
        if amrfinder_form.is_valid():
            upload = amrfinder_form.save()
            excel_file = upload.Amrfinderfile

            df = pd.read_excel(excel_file)
            df.columns = (
                df.columns
                  .str.strip()
                  .str.replace(" ", "_", regex=False)
                  .str.replace("%", "pct", regex=False)
                  .str.replace(".", "_", regex=False)
                  .str.lower()
            )

            # preload all valid site codes from SiteData (uppercase)
            site_codes = set(SiteData.objects.values_list("SiteCode", flat=True))
            # helper to build accession
            def format_amrfinder_accession(raw_name: str) -> str:
                if not raw_name:
                    return ""
                # take basename and remove extension
                base = os.path.basename(raw_name)
                base_noext = os.path.splitext(base)[0].strip()
                # must contain ARS to be eligible
                if "ARS" not in base_noext:
                    return ""
                parts = re.split(r"[-_]", base_noext)
                if not parts:
                    return ""
                prefix = parts[0]  # e.g. "24ARS" or "22ARS"

                # 1) look for a part like LETTERS + DIGITS where LETTERS is a valid site code
                for part in parts[1:]:
                    m = re.match(r"^([A-Za-z]{2,6})(\d+)$", part)
                    if m:
                        letters = m.group(1).upper()
                        digits = m.group(2)
                        if letters in site_codes:
                            return f"{prefix}_{letters}{digits}"

                # 2) look for an exact sitecode part, then try to extract digits from the next part
                for i in range(1, len(parts)):
                    part = parts[i]
                    if part.upper() in site_codes:
                        letters = part.upper()
                        digits = ""
                        # try the next part for a letters+digits pattern or digits
                        if i + 1 < len(parts):
                            next_part = parts[i + 1]
                            m2 = re.match(r"^([A-Za-z]{2,6})(\d+)$", next_part)
                            if m2:
                                digits = m2.group(2)
                            else:
                                # fallback: grab the first run of digits in next_part
                                dmatch = re.search(r"(\d+)", next_part)
                                if dmatch:
                                    digits = dmatch.group(1)
                        # fallback: extract digits from current part
                        if not digits:
                            dmatch2 = re.search(r"(\d+)", part)
                            if dmatch2:
                                digits = dmatch2.group(1)
                        return f"{prefix}_{letters}{digits}" if digits else f"{prefix}_{letters}"

                # 3) as a last attempt, find any part that contains a valid sitecode prefix
                for part in parts[1:]:
                    m = re.match(r"^([A-Za-z]{2,6})(\d+)$", part)
                    if m and m.group(1).upper() in site_codes:
                        return f"{prefix}_{m.group(1).upper()}{m.group(2)}"

                # none matched → return blank
                return ""

            print("Total rows in dataframe:", len(df))

            for _, row in df.iterrows():
                sample_name = str(row.get("name", "")).strip()
                amrfinder_accession = format_amrfinder_accession(sample_name)

                # Step 1: try to find Referred_Data with this accession (only if non-blank)
                referred_obj = (
                    Referred_Data.objects.filter(AccessionNo=amrfinder_accession).first()
                    if amrfinder_accession else None
                )

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

                # Step 3: update project accession & summary flag (safe)
                connect_project.WGS_Amrfinder_Acc = amrfinder_accession
                connect_project.WGS_AmrfinderSummary = (
                    amrfinder_accession != "" and
                    bool(connect_project.Ref_Accession) and
                    amrfinder_accession == getattr(connect_project.Ref_Accession, "AccessionNo", None)
                )
                connect_project.save()

                # Step 4: create Amrfinderplus record (store every row)
                Amrfinderplus.objects.create(
                    Amrfinder_Accession=amrfinder_accession,
                    name=sample_name,
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
                    amrfinder_project=connect_project,
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

