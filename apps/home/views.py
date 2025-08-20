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
from .forms import *
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

# @login_required(login_url="/login/")
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

# Generate Accession Number
@login_required(login_url="/login/")
def accession_data(request):
    generated_accessions = []  # Store multiple accessions in batch if needed later

    if request.method == "POST":
        form = Referred_Form(request.POST)

        if form.is_valid():
            raw_instance = form.save(commit=False)
            site_code = raw_instance.SiteCode.SiteCode if raw_instance.SiteCode else ''
            referral_date = raw_instance.Referral_Date.strftime('%m%d%Y') if raw_instance.Referral_Date else ''
            ref_no_raw = raw_instance.RefNo or ''
            ref_no = raw_instance.RefNo.zfill(4) if raw_instance.RefNo else ''
            batch_no = raw_instance.BatchNo or ''
            site_name = raw_instance.Site_NameGen or ''  
            accession_no = f"{site_code}{referral_date}{ref_no}"
            batch_code = f"{site_code}_{referral_date}_{batch_no}_{ref_no_raw}"
            raw_instance.AccessionNo = accession_no
            raw_instance.Batch_Code = batch_code
            raw_instance.Site_Name = site_name
            raw_instance.save()


            messages.success(request, "Accession number generated.")
            generated_accessions.append(accession_no)
   
            return redirect('index')
        
        else:
            messages.error(request, "Invalid data. Please check the form.")
    else:
        form = Referred_Form()

    return render(
        request,
        'home/Batchname_form.html',
        {
            'form': form,
            'batch_accession_numbers': generated_accessions,  # Match your template
           
        }
    )

# show all accession numbers with the same batch names
@login_required(login_url="/login/")
def show_accessions(request):
    # If batch_name is already in session, use it
    batch_name = request.session.get('Batch_Code')

    # If not in session, find the latest one and store it
    if not batch_name:
        latest_record = Referred_Data.objects.order_by('-Date_of_Entry').first()
        if latest_record:
            batch_name = latest_record.batch_name
            request.session['Batch_Code'] = batch_name

    # Query only that batch_name
    accessions = Referred_Data.objects.filter(batch_name=batch_name) \
        .prefetch_related('antibiotic_entries') \
        .order_by('-AccessionNo')

    # Pagination
    paginator = Paginator(accessions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'home/Batchname_form.html', {
        'page_obj': page_obj,
        'batch_name': batch_name
    })


#automatically save the generated accession number in the database and carry-over values in the referred_form
@login_required(login_url="/login/")
def generate_accession(request):
    site_code = request.GET.get('site_code', '').upper()
    referral_date = request.GET.get('referral_date', '')
    ref_no = request.GET.get('ref_no', '')
    batch_no = request.GET.get('batch_no', '')
    site_name = request.GET.get('site_name', '')
    batch_name = request.GET.get('batch_name', '')

    if not site_code or not referral_date or not ref_no:
        return JsonResponse({'error': 'Missing required fields'}, status=400)

    try:
        referral_date_obj = datetime.strptime(referral_date, '%Y-%m-%d')
        year_short = referral_date_obj.strftime('%y')
        year_long = referral_date_obj.strftime('%m%d%Y')  # e.g. 08252025
    except ValueError:
        return JsonResponse({'error': 'Invalid referral date format. Expected YYYY-MM-DD.'}, status=400)

    # Build list of numbers: support ranges "0001-0003"
    ref_numbers = []
    if '-' in ref_no:
        try:
            start, end = ref_no.split('-')
            start_num = int(start)
            end_num = int(end)
            ref_numbers = range(start_num, end_num + 1)
        except Exception:
            ref_numbers = [int(ref_no)]
    else:
        ref_numbers = [int(ref_no)]

    accession_numbers = []
    # If SiteCode is a FK, get object; otherwise leave as string (adjust as model)
    site_obj = None
    try:
        # Example: SiteModel has field 'SiteCode' (string). Change to your actual model name.
        site_obj = SiteData.objects.filter(SiteCode__iexact=site_code).first()
    except Exception:
        site_obj = None

    for num in ref_numbers:
        ref_no_padded = str(num).zfill(4)
        accession_number = f"{year_short}ARS_{site_code}{ref_no_padded}"
        batch_codegen = f"{site_code}_{year_long}_{batch_no}_{ref_no}"

        if Referred_Data.objects.filter(AccessionNo=accession_number).exists():
            continue

        # Create object (if SiteCode is FK use site_obj else pass string)
        create_kwargs = {
            'AccessionNo': accession_number,
            'Referral_Date': referral_date,  # store as string or convert to date field if model expects date
            'RefNo': ref_no_padded,
            'Batch_Code': batch_codegen,
            'Site_Name': site_name,
            'BatchNo': batch_no,
            'Batch_Name': batch_name,
        }
        if site_obj:
            create_kwargs['SiteCode'] = site_obj
        else:
            # if your model expects a string for SiteCode, use this
            create_kwargs['SiteCode'] = site_code

        try:
            Referred_Data.objects.create(**create_kwargs)
            accession_numbers.append(accession_number)
        except IntegrityError:
            continue

    if not accession_numbers:
        return JsonResponse({'error': 'All accession numbers already exist.'}, status=409)

    return JsonResponse({'accession_numbers': accession_numbers})



@login_required(login_url="/login/")
def raw_data(request):
    whonet_abx_data = BreakpointsTable.objects.filter(Show=True)
    whonet_retest_data = BreakpointsTable.objects.filter(Retest=True)

    accession = request.GET.get('accession')

    initial_data = {}
    for field in ['SiteCode', 'Referral_Date', 'BatchNo', 'RefNo', 'Site_NameGen', 'Batch_Name', 'AccessionNo']:
        value = request.GET.get(field)
        if value:
            initial_data[field] = value
    if accession:
        initial_data['AccessionNo'] = accession

    instance = None
    if accession:
        try:
            instance = Referred_Data.objects.get(AccessionNo=accession)
        except Referred_Data.DoesNotExist:
            instance = None

    if request.method == "POST":
        form = Referred_Form(request.POST, instance=instance)
        if accession:
            existing = Referred_Data.objects.filter(AccessionNo=accession)
            if existing.exists() and instance is None:
                messages.error(request, f"The accession number {accession} already exists.")
                form = Referred_Form(initial=initial_data)
                return render(request, 'home/Referred_form.html', {
                    'form': form,
                    'whonet_abx_data': whonet_abx_data,
                    'whonet_retest_data': whonet_retest_data,
                    'current_accession': accession,
                })

        if form.is_valid():
            raw_instance = form.save(commit=False)
            lab_staff = form.cleaned_data.get('Laboratory_Staff')

            if lab_staff:
                raw_instance.ars_contact = lab_staff.LabStaff_Telnum
                raw_instance.ars_email = lab_staff.LabStaff_EmailAdd

            try:
                raw_instance.save()
            except IntegrityError:
                messages.error(request, f"Accession number {accession} already exists in the database.")
                form = Referred_Form(initial=initial_data)
                return render(request, 'home/Referred_form.html', {
                    'form': form,
                    'whonet_abx_data': whonet_abx_data,
                    'whonet_retest_data': whonet_retest_data,
                    'current_accession': accession,
                })

            for entry in whonet_abx_data:
                abx_code = entry.Whonet_Abx
                if entry.Disk_Abx:
                    disk_value = request.POST.get(f'disk_{entry.id}')
                    mic_value = ''
                    mic_operand = ''
                    alert_mic = False
                else:
                    mic_value = request.POST.get(f'mic_{entry.id}')
                    mic_operand = request.POST.get(f'mic_operand_{entry.id}')
                    alert_mic = f'alert_mic_{entry.id}' in request.POST
                    disk_value = ''

                mic_operand = mic_operand if mic_operand else ""

                antibiotic_entry = AntibioticEntry.objects.create(
                    ab_idNum_referred=raw_instance,
                    ab_AccessionNo=raw_instance.AccessionNo,
                    ab_Antibiotic=entry.Antibiotic,
                    ab_Abx=entry.Abx_code,
                    ab_Abx_code=abx_code,
                    ab_Disk_value=int(disk_value) if disk_value and disk_value.strip().isdigit() else None,
                    ab_MIC_value=mic_value or None,
                    ab_MIC_operand=mic_operand or '',
                    ab_R_breakpoint=entry.R_val or None,
                    ab_I_breakpoint=entry.I_val or None,
                    ab_SDD_breakpoint=entry.SDD_val or None,
                    ab_S_breakpoint=entry.S_val or None,
                    ab_AlertMIC=alert_mic,
                    ab_Alert_val=entry.Alert_val if alert_mic else '',
                )
                antibiotic_entry.ab_breakpoints_id.set([entry])

            for retest in whonet_retest_data:
                retest_abx_code = retest.Whonet_Abx
                if retest.Disk_Abx:
                    retest_disk_value = request.POST.get(f'retest_disk_{retest.id}')
                    retest_mic_value = ''
                    retest_mic_operand = ''
                    retest_alert_mic = False
                else:
                    retest_mic_value = request.POST.get(f'retest_mic_{retest.id}')
                    retest_mic_operand = request.POST.get(f'retest_mic_operand_{retest.id}')
                    retest_alert_mic = f'retest_alert_mic_{retest.id}' in request.POST
                    retest_disk_value = ''

                retest_mic_operand = retest_mic_operand if retest_mic_operand else ""

                if retest_disk_value or retest_mic_value:
                    retest_entry = AntibioticEntry.objects.create(
                        ab_idNum_referred=raw_instance,
                        ab_Retest_Abx_code=retest_abx_code,
                        ab_Retest_DiskValue=int(retest_disk_value) if retest_disk_value and retest_disk_value.strip().isdigit() else None,
                        ab_Retest_MICValue=retest_mic_value or None,
                        ab_Retest_MIC_operand=retest_mic_operand or '',
                        ab_Retest_Antibiotic=retest.Antibiotic,
                        ab_Retest_Abx=retest.Abx_code,
                        ab_Ret_R_breakpoint=retest.R_val or None,
                        ab_Ret_I_breakpoint=retest.I_val or None,
                        ab_Ret_SDD_breakpoint=retest.SDD_val or None,
                        ab_Ret_S_breakpoint=retest.S_val or None,
                        ab_Retest_AlertMIC=retest_alert_mic,
                        ab_Retest_Alert_val=retest.Alert_val if retest_alert_mic else '',
                    )
                    retest_entry.ab_breakpoints_id.set([retest])

            messages.success(request, 'Added Successfully')
            return redirect('accession_data')
        else:
            messages.error(request, 'Error / Adding Unsuccessful')
            print(form.errors)
    else:
        if instance:
            form = Referred_Form(instance=instance)
        elif initial_data:
            form = Referred_Form(initial=initial_data)
        else:
            form = Referred_Form()

    return render(request, 'home/Referred_form.html', {
        'form': form,
        'whonet_abx_data': whonet_abx_data,
        'whonet_retest_data': whonet_retest_data,
        'current_accession': accession,
    })



#Retrieve all data
@login_required(login_url="/login/")
def show_data(request):
    # Prefetch related objects to optimize database queries
    isolates = Referred_Data.objects.prefetch_related(
        'antibiotic_entries'
    ).order_by('-Date_of_Entry')


    # Paginate the queryset to display 20 records per page
    paginator = Paginator(isolates, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Render the template with paginated data
    return render(request, 'home/tables.html', {'page_obj': page_obj})

    
    # normal view without paginators
    # return render(request, 'home/tables.html',{'isolates' :isolates}




@login_required(login_url="/login/")
def edit_data(request, id):
    # Fetch the Egasp_Data instance to edit
    isolates = get_object_or_404(Referred_Data, pk=id)

    # Fetch related data for antibiotics
  
    whonet_abx_data = BreakpointsTable.objects.filter(Show=True)
    whonet_retest_data = BreakpointsTable.objects.filter(Retest=True)

    if request.method == 'POST':
        # Print received data for debugging
        print("POST Data:", request.POST)

        form = Referred_Form(request.POST, instance=isolates)
        if form.is_valid():
            raw_instance = form.save(commit=False)
            lab_staff = form.cleaned_data.get('Laboratory_Staff')
            if lab_staff:
                raw_instance.ars_contact = lab_staff.LabStaff_Telnum
                raw_instance.ars_email = lab_staff.LabStaff_EmailAdd
            raw_instance.save()

            # Update or Create Antibiotic Entries (whonet_abx_data)
            for entry in whonet_abx_data:
                abx_code = entry.Whonet_Abx

                # Fetch user input values for MIC and Disk
                if entry.Disk_Abx:
                    disk_value = request.POST.get(f'disk_{entry.id}')
                    mic_value = ''
                    mic_operand = ''
                    alert_mic = False  
                else:
                    mic_value = request.POST.get(f'mic_{entry.id}')
                    mic_operand = request.POST.get(f'mic_operand_{entry.id}')
                    alert_mic = f'alert_mic_{entry.id}' in request.POST
                    disk_value = ''
                
                # Check and update mic_operand if needed
                mic_operand = mic_operand.strip() if mic_operand else ''

                # Convert `disk_value` safely
                disk_value = int(disk_value) if disk_value and disk_value.strip().isdigit() else None

                # Debugging: Print the values before saving
                print(f"Saving values for Antibiotic Entry {entry.id}:", {
                    'mic_operand': mic_operand,
                    'disk_value': disk_value,
                    'mic_value': mic_value,
                })

                # Get or create antibiotic entry
                antibiotic_entry, created = AntibioticEntry.objects.update_or_create(
                    ab_idNum_referred=raw_instance,
                    ab_Abx_code=abx_code,
                    defaults={
                        "ab_AccessionNo": raw_instance.AccessionNo,
                        "ab_Antibiotic": entry.Antibiotic,
                        "ab_Abx": entry.Abx_code,
                        "ab_Disk_value": disk_value,
                        "ab_MIC_value": mic_value or None,
                        "ab_MIC_operand": mic_operand,
                        "ab_R_breakpoint": entry.R_val or None,
                        "ab_I_breakpoint": entry.I_val or None,
                        "ab_SDD_breakpoint": entry.SDD_val or None,
                        "ab_S_breakpoint": entry.S_val or None,
                        "ab_AlertMIC": alert_mic,
                        "ab_Alert_val": entry.Alert_val if alert_mic else '',
                    }
                )

                antibiotic_entry.ab_breakpoints_id.set([entry.pk])

            # Separate loop for Retest Data
            for retest in whonet_retest_data:
                retest_abx_code = retest.Whonet_Abx

                # Fetch user input values for MIC and Disk
                if retest.Disk_Abx:
                    retest_disk_value = request.POST.get(f'retest_disk_{retest.id}')
                    retest_mic_value = ''
                    retest_mic_operand = ''
                    retest_alert_mic = False
                else:
                    retest_mic_value = request.POST.get(f'retest_mic_{retest.id}')
                    retest_mic_operand = request.POST.get(f'retest_mic_operand_{retest.id}')
                    retest_alert_mic = f'retest_alert_mic_{retest.id}' in request.POST
                    retest_disk_value = ''

                # Check and update retest mic_operand if needed
                retest_mic_operand = retest_mic_operand.strip() if retest_mic_operand else ''

                # Convert `retest_disk_value` safely
                retest_disk_value = int(retest_disk_value) if retest_disk_value and retest_disk_value.strip().isdigit() else None

                # Debugging: Print the values before saving
                print(f"Saving values for Retest Entry {retest.id}:", {
                    'retest_mic_operand': retest_mic_operand,
                    'retest_disk_value': retest_disk_value,
                    'retest_mic_value': retest_mic_value,
                    'retest_alert_mic': retest_alert_mic,
                    'retest_alert_val': retest.Alert_val if retest_alert_mic else '',
                })

                # Get or update retest antibiotic entry
                retest_entry, created = AntibioticEntry.objects.update_or_create(
                    ab_idNum_referred=raw_instance,
                    ab_Retest_Abx_code=retest_abx_code,
                    defaults={
                        "ab_Retest_DiskValue": retest_disk_value,
                        "ab_Retest_MICValue": retest_mic_value or None,
                        "ab_Retest_MIC_operand": retest_mic_operand,
                        "ab_Retest_Antibiotic": retest.Antibiotic,
                        "ab_Retest_Abx": retest.Abx_code,
                        "ab_Ret_R_breakpoint": retest.R_val or None,
                        "ab_Ret_S_breakpoint": retest.S_val or None,
                        "ab_Ret_SDD_breakpoint": retest.SDD_val or None,
                        "ab_Ret_I_breakpoint": retest.I_val or None,
                        "ab_Retest_AlertMIC": retest_alert_mic,
                        "ab_Retest_Alert_val": retest.Alert_val if retest_alert_mic else '',
                    }
                )

                retest_entry.ab_breakpoints_id.set([retest.pk])

            messages.success(request, 'Data updated successfully')
            return redirect('/show/')
        else:
            messages.error(request, 'There was an error with your form')
            print(form.errors)
    else:
        form = Referred_Form(instance=isolates)

    # Fetch all entries in one query
    all_entries = AntibioticEntry.objects.filter(ab_idNum_referred=isolates)

    # Separate them based on the 'retest' condition
    existing_entries = all_entries.filter(ab_Abx_code__isnull=True)  # Regular entries
    retest_entries = all_entries.filter(ab_Retest_Abx_code__isnull=False)   # Retest entries

    context = {
        'isolates': isolates,
        'form': form,
        'whonet_abx_data': whonet_abx_data,
        'whonet_retest_data': whonet_retest_data,
        'existing_entries': existing_entries,
        'retest_entries': retest_entries,
    
    }
    return render(request, 'home/edit.html', context)





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
    contacts = Lab_Staff_Details.objects.all()
    
    return render(request, 'home/Contact_Form.html', {'form': form, 'contacts': contacts})


@login_required(login_url="/login/")
def delete_contact(request, id):
    contact_items = get_object_or_404(Lab_Staff_Details, pk=id)
    contact_items.delete()
    return redirect('contact_view')


@login_required(login_url="/login/")
def contact_view(request):
    contact_items = Lab_Staff_Details.objects.all()  # Fetch all contact data
    return render(request, 'home/Contact_View.html', {'contact_items': contact_items})


@login_required(login_url="/login/")
def get_Lab_Staff_Details(request):
    lab_staff_name = request.GET.get('lab_staff_id')  # Actually contains a name, not an ID
    lab_staff = Lab_Staff_Details.objects.filter(LabStaff_Name=lab_staff_name).first()

    if lab_staff:
        return JsonResponse({
            'LabStaff_Telnum': str(lab_staff.LabStaff_Telnum),  # Convert PhoneNumber to string
            'LabStaff_EmailAdd': lab_staff.LabStaff_EmailAdd
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
        'Date_of_Entry','ID_Number','Egasp_Id','PTIDCode','Laboratory','Clinic','Consult_Date','Consult_Type','Client_Type','Uic_Ptid','Clinic_Code','ClinicCodeGen','First_Name','Middle_Name','Last_Name','Suffix','Birthdate','Age','Sex','Gender_Identity','Gender_Identity_Other','Occupation','Civil_Status','Civil_Status_Other','Current_Province','Current_City','Current_Country','Permanent_Province','Permanent_City','Permanent_Country','Nationality','Nationality_Other','Travel_History','Travel_History_Specify','Client_Group','Client_Group_Other','History_Of_Sex_Partner','Nationality_Sex_Partner','Date_of_Last_Sex','Nationality_Sex_Partner_Other','Number_Of_Sex_Partners','Relationship_to_Partners','SB_Urethral','SB_Vaginal','SB_Anal_Insertive','SB_Anal_Receptive','SB_Oral_Insertive','SB_Oral_Receptive','Sharing_of_Sex_Toys','SB_Others','Sti_None','Sti_Hiv','Sti_Hepatitis_B','Sti_Hepatitis_C','Sti_NGI','Sti_Syphilis','Sti_Chlamydia','Sti_Anogenital_Warts','Sti_Genital_Ulcer','Sti_Herpes','Sti_Other','Illicit_Drug_Use','Illicit_Drug_Specify','Abx_Use_Prescribed','Abx_Use_Prescribed_Specify','Abx_Use_Self_Medicated','Abx_Use_Self_Medicated_Specify','Abx_Use_None','Abx_Use_Other','Abx_Use_Other_Specify','Route_Oral','Route_Injectable_IV','Route_Dermal','Route_Suppository','Route_Other','Symp_With_Discharge','Symp_No','Symp_Discharge_Urethra','Symp_Discharge_Vagina','Symp_Discharge_Anus','Symp_Discharge_Oropharyngeal','Symp_Pain_Lower_Abdomen','Symp_Tender_Testicles','Symp_Painful_Urination','Symp_Painful_Intercourse','Symp_Rectal_Pain','Symp_Other','Outcome_Of_Follow_Up_Visit','Prev_Test_Pos','Prev_Test_Pos_Date','Result_Test_Cure_Initial','Result_Test_Cure_Followup','NoTOC_Other_Test','NoTOC_DatePerformed','NoTOC_Result_of_Test','Patient_Compliance_Antibiotics','OtherDrugs_Specify','OtherDrugs_Dosage','OtherDrugs_Route','OtherDrugs_Duration','Gonorrhea_Treatment','Treatment_Outcome','Primary_Antibiotic','Primary_Abx_Other','Secondary_Antibiotic','Secondary_Abx_Other','Notes','Clinic_Staff','Requesting_Physician','Telephone_Number','Email_Address','Date_Accomplished_Clinic','Date_Requested_Clinic','Date_Specimen_Collection','Specimen_Code','Specimen_Type','Specimen_Quality','Date_Of_Gram_Stain','Diagnosis_At_This_Visit','Gram_Neg_Intracellular','Gram_Neg_Extracellular','Gs_Presence_Of_Pus_Cells','Presence_GN_Intracellular','Presence_GN_Extracellular','GS_Pus_Cells','Epithelial_Cells','GS_Date_Released','GS_Others','GS_Negative','Date_Received_in_lab','Positive_Culture_Date','Culture_Result','Species_Identification','Other_species_ID','Specimen_Quality_Cs','Susceptibility_Testing_Date','Retested_Mic','Confirmation_Ast_Date','Beta_Lactamase','PPng','TRng','Date_Released','For_possible_WGS','Date_stocked','Location','abx_code','Laboratory_Staff','Date_Accomplished_ARSP','ars_notes','ars_contact','ars_email',

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
        'Date_of_Entry','ID_Number','Egasp_Id','PTIDCode','Laboratory','Clinic','Consult_Date','Consult_Type','Client_Type','Uic_Ptid','Clinic_Code','ClinicCodeGen','First_Name','Middle_Name','Last_Name','Suffix','Birthdate','Age','Sex','Gender_Identity','Gender_Identity_Other','Occupation','Civil_Status','Civil_Status_Other','Current_Province','Current_City','Current_Country','Permanent_Province','Permanent_City','Permanent_Country','Nationality','Nationality_Other','Travel_History','Travel_History_Specify','Client_Group','Client_Group_Other','History_Of_Sex_Partner','Nationality_Sex_Partner','Date_of_Last_Sex','Nationality_Sex_Partner_Other','Number_Of_Sex_Partners','Relationship_to_Partners','SB_Urethral','SB_Vaginal','SB_Anal_Insertive','SB_Anal_Receptive','SB_Oral_Insertive','SB_Oral_Receptive','Sharing_of_Sex_Toys','SB_Others','Sti_None','Sti_Hiv','Sti_Hepatitis_B','Sti_Hepatitis_C','Sti_NGI','Sti_Syphilis','Sti_Chlamydia','Sti_Anogenital_Warts','Sti_Genital_Ulcer','Sti_Herpes','Sti_Other','Illicit_Drug_Use','Illicit_Drug_Specify','Abx_Use_Prescribed','Abx_Use_Prescribed_Specify','Abx_Use_Self_Medicated','Abx_Use_Self_Medicated_Specify','Abx_Use_None','Abx_Use_Other','Abx_Use_Other_Specify','Route_Oral','Route_Injectable_IV','Route_Dermal','Route_Suppository','Route_Other','Symp_With_Discharge','Symp_No','Symp_Discharge_Urethra','Symp_Discharge_Vagina','Symp_Discharge_Anus','Symp_Discharge_Oropharyngeal','Symp_Pain_Lower_Abdomen','Symp_Tender_Testicles','Symp_Painful_Urination','Symp_Painful_Intercourse','Symp_Rectal_Pain','Symp_Other','Outcome_Of_Follow_Up_Visit','Prev_Test_Pos','Prev_Test_Pos_Date','Result_Test_Cure_Initial','Result_Test_Cure_Followup','NoTOC_Other_Test','NoTOC_DatePerformed','NoTOC_Result_of_Test','Patient_Compliance_Antibiotics','OtherDrugs_Specify','OtherDrugs_Dosage','OtherDrugs_Route','OtherDrugs_Duration','Gonorrhea_Treatment','Treatment_Outcome','Primary_Antibiotic','Primary_Abx_Other','Secondary_Antibiotic','Secondary_Abx_Other','Notes','Clinic_Staff','Requesting_Physician','Telephone_Number','Email_Address','Date_Accomplished_Clinic','Date_Requested_Clinic','Date_Specimen_Collection','Specimen_Code','Specimen_Type','Specimen_Quality','Date_Of_Gram_Stain','Diagnosis_At_This_Visit','Gram_Neg_Intracellular','Gram_Neg_Extracellular','Gs_Presence_Of_Pus_Cells','Presence_GN_Intracellular','Presence_GN_Extracellular','GS_Pus_Cells','Epithelial_Cells','GS_Date_Released','GS_Others','GS_Negative','Date_Received_in_lab','Positive_Culture_Date','Culture_Result','Species_Identification','Other_species_ID','Specimen_Quality_Cs','Susceptibility_Testing_Date','Retested_Mic','Confirmation_Ast_Date','Beta_Lactamase','PPng','TRng','Date_Released','For_possible_WGS','Date_stocked','Location','abx_code','Laboratory_Staff','Date_Accomplished_ARSP','ars_notes','ars_contact','ars_email',

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
