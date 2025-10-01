from django.shortcuts import render, redirect
from .forms import *
import pandas as pd
from apps.home.models import Referred_Data
from .models import *
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.contrib import messages
import os
from django.core.paginator import Paginator

# handles the connection of WGS project to referred data
@login_required
# def upload_wgs_view(request):
#     if request.method == "POST":
#         form = WGSProjectForm(request.POST)
#         upload_form = FastqUploadForm(request.POST, request.FILES)

#         if form.is_valid():
#             form.save()
#             return redirect("upload_fastq")  # refresh after save

#         if upload_form.is_valid():
#             upload_form.save()
#             return redirect("upload_fastq")  # refresh after upload
#     else:
#         form = WGSProjectForm()
#         upload_form = FastqUploadForm()

#     return render(request, "wgs_app/Add_wgs.html", {
#         "form": form,
#         "upload_form": upload_form,
#         "editing": False,
#     })



def upload_wgs_view(request):

    if request.method == "POST":
        form = WGSProjectForm(request.POST)
        fastq_form = FastqUploadForm(request.POST, request.FILES)
        gambit_form = GambitUploadForm(request.POST, request.FILES)
        mlst_form = MlstUploadForm(request.POST, request.FILES)
        checkm2_form = Checkm2UploadForm(request.POST, request.FILES)
        assembly_form = AssemblyUploadForm(request.POST, request.FILES)

        project_saved = False
        fastq_uploaded = False
        gambit_uploaded = False
        mlst_uploaded = False
        checkm2_uploaded = False
        assembly_uploaded = False

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

        # If any form worked, refresh
        if project_saved or fastq_uploaded or gambit_uploaded or mlst_uploaded or checkm2_uploaded or assembly_uploaded:
            return redirect("upload_wgs_view")

    else:
        form = WGSProjectForm()
        fastq_form = FastqUploadForm()
        gambit_form = GambitUploadForm()
        mlst_form = MlstUploadForm()
        checkm2_form = Checkm2UploadForm()
        assembly_form = AssemblyUploadForm()

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



# handles the upload of fastq summary excel file
# @login_required
# def upload_fastq(request):
#     form = WGSProjectForm()          # Form for Connect_Project
#     fastq_form = FastqUploadForm()  # Form for file upload
#     editing = False  

#     if request.method == "POST" and request.FILES.get("fastqfile"):
#         fastq_form = FastqUploadForm(request.POST, request.FILES)
#         if fastq_form.is_valid():
#             upload = fastq_form.save()
#             excel_file = upload.fastqfile

#             df = pd.read_excel(excel_file)

#             for _, row in df.iterrows():
#                 sample_name = str(row.get("sample", "")).strip()
#                 fastq_accession = "_".join(sample_name.split("-")[:2])  # auto accession

#                 # Find referred_data match
#                 referred_obj = Referred_Data.objects.filter(
#                     AccessionNo=fastq_accession
#                 ).first()

#                 connect_project = None
#                 if referred_obj:
#                     connect_project, created = WGS_Project.objects.get_or_create(
#                         Ref_Accession=referred_obj
#                     )

#                     # ✅ Always assign accession to project
#                     connect_project.WGS_FastQ_Acc = fastq_accession

#                     # ✅ If it matches Referred_Data AccessionNo, set summary flag
#                     if fastq_accession == referred_obj.AccessionNo:
#                         connect_project.WGS_FastqSummary = True
#                     else:
#                         connect_project.WGS_FastqSummary = False

#                     connect_project.save()

#                 # Save or update FastqSummary table
#                 FastqSummary.objects.update_or_create(
#                     FastQ_Accession=fastq_accession,
#                     defaults={
#                         'fastq_project': connect_project,
#                         'sample': sample_name,
#                         'fastp_version': row.get("fastp_version", ""),
#                         'sequencing': row.get("sequencing", ""),
#                         'before_total_reads': row.get("before_total_reads", ""),
#                         'before_total_bases': row.get("before_total_bases", ""),
#                         'before_q20_rate': row.get("before_q20_rate", ""),
#                         'before_q30_rate': row.get("before_q30_rate", ""),
#                         'before_read1_mean_len': row.get("before_read1_mean_len", ""),
#                         'before_read2_mean_len': row.get("before_read2_mean_len", ""),
#                         'before_gc_content': row.get("before_gc_content", ""),
#                         'after_total_reads': row.get("after_total_reads", ""),
#                         'after_total_bases': row.get("after_total_bases", ""),
#                         'after_q20_rate': row.get("after_q20_rate", ""),
#                         'after_q30_rate': row.get("after_q30_rate", ""),
#                         'after_read1_mean_len': row.get("after_read1_mean_len", ""),
#                         'after_read2_mean_len': row.get("after_read2_mean_len", ""),
#                         'after_gc_content': row.get("after_gc_content", ""),
#                         'passed_filter_reads': row.get("passed_filter_reads", ""),
#                         'low_quality_reads': row.get("low_quality_reads", ""),
#                         'too_many_N_reads': row.get("too_many_N_reads", ""),
#                         'too_short_reads': row.get("too_short_reads", ""),
#                         'too_long_reads': row.get("too_long_reads", ""),
#                         'combined_total_bp': row.get("combined_total_bp", ""),
#                         'combined_qual_mean': row.get("combined_qual_mean", ""),
#                         'post_trim_q30_rate': row.get("post_trim_q30_rate", ""),
#                         'post_trim_q30_pct': row.get("post_trim_q30_pct", ""),
#                         'post_trim_q20_rate': row.get("post_trim_q20_rate", ""),
#                         'post_trim_q20_pct': row.get("post_trim_q20_pct", ""),
#                         'after_gc_pct': row.get("after_gc_pct", ""),
#                         'duplication_rate': row.get("duplication_rate", ""),
#                         'read_length_mean_after': row.get("read_length_mean_after", ""),
#                         'adapter_trimmed_reads': row.get("adapter_trimmed_reads", ""),
#                         'adapter_trimmed_reads_pct': row.get("adapter_trimmed_reads_pct", ""),
#                         'adapter_trimmed_bases': row.get("adapter_trimmed_bases", ""),
#                         'adapter_trimmed_bases_pct': row.get("adapter_trimmed_bases_pct", ""),
#                         'insert_size_peak': row.get("insert_size_peak", ""),
#                         'insert_size_unknown': row.get("insert_size_unknown", ""),
#                         'overrep_r1_count': row.get("overrep_r1_count", ""),
#                         'overrep_r2_count': row.get("overrep_r2_count", ""),
#                         'ns_overrep_none': row.get("ns_overrep_none", ""),
#                         'qc_q30_pass': row.get("qc_q30_pass", ""),
#                         'q30_status': row.get("q30_status", ""),
#                         'q20_status': row.get("q20_status", ""),
#                         'adapter_reads_status': row.get("adapter_reads_status", ""),
#                         'adapter_bases_status': row.get("adapter_bases_status", ""),
#                         'duplication_status': row.get("duplication_status", ""),
#                         'readlen_status': row.get("readlen_status", ""),
#                         'ns_overrep_status': row.get("ns_overrep_status", ""),
#                         'raw_reads_qc_summary': row.get("raw_reads_qc_summary", ""),
#                     }
#                 )

#             messages.success(request, "FastQ records updated successfully.")
#             return redirect("show_fastq")

#     return render(request, "wgs_app/Add_wgs.html", {
#         "form": form,
#         "fastq_form": fastq_form,   
#         "gambit_form": GambitUploadForm(),        
#         "mlst_form": MlstUploadForm(),    
#         "editing": editing,
#     })
@login_required
def upload_fastq(request):
    form = WGSProjectForm()          # Form for Connect_Project
    fastq_form = FastqUploadForm()   # Form for file upload
    editing = False  

    if request.method == "POST" and request.FILES.get("fastqfile"):
        fastq_form = FastqUploadForm(request.POST, request.FILES)
        if fastq_form.is_valid():
            upload = fastq_form.save()
            excel_file = upload.fastqfile

            df = pd.read_excel(excel_file)
            df.columns = df.columns.str.strip().str.replace(".", "", regex=False)  # normalize headers

            for _, row in df.iterrows():
                sample_name = str(row.get("sample", "")).strip()
                fastq_accession = "_".join(sample_name.split("-")[:2])  # auto accession

                # 🔎 Step 1: Find referred_data match
                referred_obj = Referred_Data.objects.filter(
                    AccessionNo=fastq_accession
                ).first()

                # 🔎 Step 2: Create or get WGS_Project
                connect_project, _ = WGS_Project.objects.get_or_create(
                    Ref_Accession=referred_obj if referred_obj else None,
                    defaults={
                        "WGS_GambitSummary": False,
                        "WGS_FastqSummary": False,
                        "WGS_MlstSummary": False,
                        "WGS_Checkm2Summary": False,
                    }
                )

                # 🔎 Step 3: Always assign accession to project
                connect_project.WGS_FastQ_Acc = fastq_accession

                # 🔎 Step 4: summary flag = True if matches Ref_Accession
                connect_project.WGS_FastqSummary = (
                    bool(connect_project.Ref_Accession)
                    and fastq_accession == connect_project.Ref_Accession.AccessionNo
                )

                
                # connect_project.WGS_FastqSummary = (
                #     fastq_accession == getattr(connect_project.Ref_Accession, "AccessionNo", None)
                # )


                connect_project.save()

                # 🔎 Step 5: Save or update FastqSummary table
                FastqSummary.objects.update_or_create(
                    FastQ_Accession=fastq_accession,
                    defaults={
                        'fastq_project': connect_project,
                        'sample': sample_name,
                        'fastp_version': row.get("fastp_version", ""),
                        'sequencing': row.get("sequencing", ""),
                        'before_total_reads': row.get("before_total_reads", ""),
                        'before_total_bases': row.get("before_total_bases", ""),
                        'before_q20_rate': row.get("before_q20_rate", ""),
                        'before_q30_rate': row.get("before_q30_rate", ""),
                        'before_read1_mean_len': row.get("before_read1_mean_len", ""),
                        'before_read2_mean_len': row.get("before_read2_mean_len", ""),
                        'before_gc_content': row.get("before_gc_content", ""),
                        'after_total_reads': row.get("after_total_reads", ""),
                        'after_total_bases': row.get("after_total_bases", ""),
                        'after_q20_rate': row.get("after_q20_rate", ""),
                        'after_q30_rate': row.get("after_q30_rate", ""),
                        'after_read1_mean_len': row.get("after_read1_mean_len", ""),
                        'after_read2_mean_len': row.get("after_read2_mean_len", ""),
                        'after_gc_content': row.get("after_gc_content", ""),
                        'passed_filter_reads': row.get("passed_filter_reads", ""),
                        'low_quality_reads': row.get("low_quality_reads", ""),
                        'too_many_N_reads': row.get("too_many_N_reads", ""),
                        'too_short_reads': row.get("too_short_reads", ""),
                        'too_long_reads': row.get("too_long_reads", ""),
                        'combined_total_bp': row.get("combined_total_bp", ""),
                        'combined_qual_mean': row.get("combined_qual_mean", ""),
                        'post_trim_q30_rate': row.get("post_trim_q30_rate", ""),
                        'post_trim_q30_pct': row.get("post_trim_q30_pct", ""),
                        'post_trim_q20_rate': row.get("post_trim_q20_rate", ""),
                        'post_trim_q20_pct': row.get("post_trim_q20_pct", ""),
                        'after_gc_pct': row.get("after_gc_pct", ""),
                        'duplication_rate': row.get("duplication_rate", ""),
                        'read_length_mean_after': row.get("read_length_mean_after", ""),
                        'adapter_trimmed_reads': row.get("adapter_trimmed_reads", ""),
                        'adapter_trimmed_reads_pct': row.get("adapter_trimmed_reads_pct", ""),
                        'adapter_trimmed_bases': row.get("adapter_trimmed_bases", ""),
                        'adapter_trimmed_bases_pct': row.get("adapter_trimmed_bases_pct", ""),
                        'insert_size_peak': row.get("insert_size_peak", ""),
                        'insert_size_unknown': row.get("insert_size_unknown", ""),
                        'overrep_r1_count': row.get("overrep_r1_count", ""),
                        'overrep_r2_count': row.get("overrep_r2_count", ""),
                        'ns_overrep_none': row.get("ns_overrep_none", ""),
                        'qc_q30_pass': row.get("qc_q30_pass", ""),
                        'q30_status': row.get("q30_status", ""),
                        'q20_status': row.get("q20_status", ""),
                        'adapter_reads_status': row.get("adapter_reads_status", ""),
                        'adapter_bases_status': row.get("adapter_bases_status", ""),
                        'duplication_status': row.get("duplication_status", ""),
                        'readlen_status': row.get("readlen_status", ""),
                        'ns_overrep_status': row.get("ns_overrep_status", ""),
                        'raw_reads_qc_summary': row.get("raw_reads_qc_summary", ""),
                    }
                )

            messages.success(request, "FastQ records updated successfully.")
            return redirect("show_fastq")

    return render(request, "wgs_app/Add_wgs.html", {
        "form": form,
        "fastq_form": fastq_form,   
        "gambit_form": GambitUploadForm(),        
        "mlst_form": MlstUploadForm(),    
        "checkm2_form": Checkm2UploadForm(),
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

            for _, row in df.iterrows():
                # Extract sample name
                full_path = str(row.get("name", "")).strip()
                file_name = os.path.basename(full_path)
                file_stem = os.path.splitext(file_name)[0]
                sample_name = "_".join(file_stem.split("-")[:2])  # "18ARS-BGH0055"

                mlst_accession = sample_name  # keep "-" to match Referred_Data

                # Find Referred_Data object
                referred_obj = Referred_Data.objects.filter(
                    AccessionNo=mlst_accession
                ).first()

                # Get or create WGS_Project
                connect_project, _ = WGS_Project.objects.get_or_create(
                    Ref_Accession=referred_obj if referred_obj else None,
                    defaults={
                        "WGS_GambitSummary": False,
                        "WGS_FastqSummary": False,
                        "WGS_MlstSummary": False,
                        "WGS_Checkm2Summary": False,
                    }
                )

                # Update project with MLST info
                connect_project.WGS_Mlst_Acc = mlst_accession
                connect_project.WGS_MlstSummary = (
                    bool(connect_project.Ref_Accession) 
                    and mlst_accession == connect_project.Ref_Accession.AccessionNo
                )
                connect_project.save()

                # Update or create Mlst record
                Mlst.objects.update_or_create(
                    Mlst_Accession=mlst_accession,
                    defaults={
                        'mlst_project': connect_project,
                        'name': row.get("name", ""),
                        'scheme': row.get("scheme", ""),
                        'mlst': row.get("MLST", ""),
                        'allele1': row.get("allele1", ""),
                        'allele2': row.get("allele2", ""),
                        'allele3': row.get("allele3", ""),
                        'allele4': row.get("allele4", ""),
                        'allele5': row.get("allele5", ""),
                        'allele6': row.get("allele6", ""),
                        'allele7': row.get("allele7", "")
                    }
                )

            messages.success(request, "MLST records updated successfully.")
            return redirect("show_mlst")

    return render(request, "wgs_app/Add_wgs.html", {
        "form": form,
        "fastq_form": FastqUploadForm(),
        "gambit_form": GambitUploadForm(),
        "checkm2_form": Checkm2UploadForm(),
        "mlst_form": mlst_form,
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


def delete_all_mlst(request):
    Mlst.objects.all().delete()
    messages.success(request, "Mlst Records have been deleted successfully.")
    return redirect('show_gambit')  # Redirect to the table view



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
            df.columns = df.columns.str.replace(".", "", regex=False) # Replace "." in column names with empty / delete


            for _, row in df.iterrows():
                sample_name = str(row.get("Name", "")).strip() # "Name" is the column name of excel file where accession number is driven
                checkm2_accession = "_".join(sample_name.split("-")[:2])  # parse accession

                # 🔎 Step 1: try to find Referred_Data with this accession
                referred_obj = Referred_Data.objects.filter(
                    AccessionNo=checkm2_accession
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
                connect_project.WGS_Checkm2_Acc = checkm2_accession

                # 🔎 Step 4: summary flag = True if gambit_accession matches Ref_Accession.AccessionNo
                connect_project.WGS_Checkm2Summary = (
                    bool(connect_project.Ref_Accession) 
                    and checkm2_accession == connect_project.Ref_Accession.AccessionNo
                )

                connect_project.save()

                # 🔄 Step 5: update or create Gambit record
                Checkm2.objects.update_or_create(
                    Checkm2_Accession=checkm2_accession,
                    defaults={
                        "checkm2_project": connect_project,
                        "Name": sample_name,
                        "Completeness": row.get("Completeness", ""),
                        "Contamination": row.get("Contamination", ""),
                        "Completeness_Model_Used": row.get("Completeness_Model_Used", ""),
                        "Translation_Table_Used": row.get("Translation_Table_Used", ""),
                        "Coding_Density": row.get("Coding_Density", ""),
                        "Contig_N50": row.get("Contig_N50", ""),
                        "Average_Gene_Length": row.get("Average_Gene_Length", ""),
                        "GC_Content": row.get("GC_Content", ""),
                        "Total_Coding_Sequences": row.get("Total_Coding_Sequences", ""),
                        "Total_Contigs": row.get("Total_Contigs", ""),
                        "Max_Contig_Length": row.get("Max_Contig_Length", ""),
                        "Additional_Notes": row.get("Additional_Notes", ""),
                    },
                )

            messages.success(request, "Checkm2 records updated successfully.")
            return redirect("show_checkm2")

    return render(request, "wgs_app/Add_wgs.html", {
        "form": form,
        "fastq_form": FastqUploadForm(),
        "gambit_form": GambitUploadForm(),
        "mlst_form": MlstUploadForm(),
        "checkm2_form": checkm2_form,
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

            for _, row in df.iterrows():
                sample_name = str(row.get("sample", "")).strip() # "sample" is the column name of excel file where accession number is driven
                assembly_accession = "_".join(sample_name.split("-")[:2])  # parse accession

                # 🔎 Step 1: try to find Referred_Data with this accession
                referred_obj = Referred_Data.objects.filter(
                    AccessionNo=assembly_accession
                ).first()

                # 🔎 Step 2: create or get WGS_Project
                connect_project, _ = WGS_Project.objects.get_or_create(
                    Ref_Accession=referred_obj if referred_obj else None,
                    defaults={
                        "WGS_GambitSummary": False,
                        "WGS_FastqSummary": False,
                        "WGS_MlstSummary": False,
                        "WGS_Checkm2Summary": False,
                        "WGS_AssemblySummary": False,
                    }
                )

                # 🔎 Step 3: update Gambit accession in project
                connect_project.WGS_Assembly_Acc = assembly_accession

                # 🔎 Step 4: summary flag = True if gambit_accession matches Ref_Accession.AccessionNo
                connect_project.WGS_AssemblySummary = (
                    bool(connect_project.Ref_Accession) 
                    and assembly_accession == connect_project.Ref_Accession.AccessionNo
                )

                connect_project.save()

                # 🔄 Step 5: update or create Gambit record
                AssemblyScan.objects.update_or_create(
                    Assembly_Accession=assembly_accession,
                    defaults={
                        "assembly_project": connect_project,
                        "sample": sample_name,
                        "total_contig": row.get("total_contig", ""),
                        "total_contig_length": row.get("total_contig_length", ""),
                        "max_contig_length": row.get("max_contig_length", ""),
                        "mean_contig_length": row.get("mean_contig_length", ""),
                        "median_contig_length": row.get("median_contig_length", ""),
                        "min_contig_length": row.get("min_contig_length", ""),
                        "n50_contig_length": row.get("n50_contig_length", ""),
                        "l50_contig_count": row.get("l50_contig_count", ""),
                        "num_contig_non_acgtn": row.get("num_contig_non_acgtn", ""),
                        "contig_percent_a": row.get("contig_percent_a", ""),
                        "contig_percent_c": row.get("contig_percent_c", ""),
                        "contig_percent_g": row.get("contig_percent_g", ""),
                        "contig_percent_t": row.get("contig_percent_t", ""),
                        "contig_percent_n": row.get("contig_percent_n", ""),
                        "contig_non_acgtn": row.get("contig_non_acgtn", ""),
                        "contigs_greater_1m": row.get("contigs_greater_1m", ""),
                        "contigs_greater_100k": row.get("contigs_greater_100k", ""),
                        "contigs_greater_10k": row.get("contigs_greater_10k", ""),
                        "contigs_greater_1k": row.get("contigs_greater_1k", ""),
                        "percent_contigs_greater_1m": row.get("percent_contigs_greater_1m", ""),
                        "percent_contigs_greater_100k": row.get("percent_contigs_greater_100k", ""),
                        "percent_contigs_greater_10k": row.get("percent_contigs_greater_10k", ""),
                        "percent_contigs_greater_1k": row.get("percent_contigs_greater_1k", ""),
                    },
                )

            messages.success(request, "AssemblyScan records updated successfully.")
            return redirect("show_assembly")

    return render(request, "wgs_app/Add_wgs.html", {
        "form": form,
        "fastq_form": FastqUploadForm(),
        "gambit_form": GambitUploadForm(),
        "mlst_form": MlstUploadForm(),
        "checkm2_form": Checkm2UploadForm(),
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

    total_records = Checkm2.objects.count()
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



def delete_all_assembly(request):
    AssemblyScan.objects.all().delete()
    messages.success(request, "AssemblyScan Records have been deleted successfully.")
    return redirect('show_assembly')  # Redirect to the table view
