from .models import *
from django import forms
from phonenumber_field.formfields import PhoneNumberField


    
class Referred_Form(forms.ModelForm):

        # #using modelchoicefield for dynamic rendering
        # SiteCode = forms.ModelChoiceField(
        #     queryset=SiteData.objects.all(),
        #     to_field_name='SiteCode',  # Specify the field you want as the value
        #     widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
        #     empty_label="Select Site Code",
        #     required=False
            
        # )


        Spec_Type = forms.ModelChoiceField(
            queryset=SpecimenTypeModel.objects.all(),
            to_field_name='Specimen_code',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Specimen",
            required=False,
            
        )

        arsp_Checker = forms.ModelChoiceField(
            queryset=arsStaff_Details.objects.all(),
            to_field_name='Staff_Name',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Staff",
            required=False,
        )

        arsp_Verifier = forms.ModelChoiceField(
            queryset=arsStaff_Details.objects.all(),
            to_field_name='Staff_Name',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Staff",
            required=False,
        )

        arsp_LabManager = forms.ModelChoiceField(
            queryset=arsStaff_Details.objects.all(),
            to_field_name='Staff_Name',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Staff",
            required=False,
        )

        arsp_Encoder= forms.ModelChoiceField(
            queryset=arsStaff_Details.objects.all(),
            to_field_name='Staff_Name',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Staff",
            required=False,
        )

        arsp_Head= forms.ModelChoiceField(
            queryset=arsStaff_Details.objects.all(),
            to_field_name='Staff_Name',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Staff",
            required=False,
        )


        class Meta:
            model = Referred_Data
            fields ='__all__'
            widgets = {
            'Referral_Date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'MM/DD/YYYY'}),
            'Date_Birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'MM/DD/YYYY'}),
            'Date_Admis' :forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'MM/DD/YYYY'}),
            'Spec_Date' :forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'MM/DD/YYYY'}),
            'RefNo' :forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'ex. 0001'}),
            'BatchNo' :forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'ex. 1.1'}),
            'Growth_others' :forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex. after 24 hrs of incubation'}),
            'Comments': forms.Textarea(attrs={'class': 'textarea form-control', 'rows': '3'}),
            'ars_reco': forms.Textarea(attrs={'class': 'textarea form-control', 'rows': '3'}),
            
            # Add more fields as needed
            }
            
       
            

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # self.fields['SiteCode'].queryset = SiteData.objects.all() # Always load the latest Site Code
            self.fields['SiteCode'].widget.attrs['readonly'] = True
            self.fields['Batch_Code'].widget.attrs['readonly'] = True
            self.fields['AccessionNo'].widget.attrs['readonly'] = True
            self.fields['Status'].required=False
            self.fields['Batch_id'].required=False
            self.fields['RefNo'].widget.attrs['readonly'] = True
            self.fields['Referral_Date'].widget.attrs['readonly'] = True
            self.fields['BatchNo'].widget.attrs['readonly'] = True
            self.fields['Site_Name'].widget.attrs['readonly'] = True
            self.fields['arsp_Encoder'].required=False
            self.fields['arsp_Checker'].required=False
            self.fields['arsp_Verifier'].required=False
            self.fields['arsp_LabManager'].required=False
            self.fields['arsp_Head'].required=False
            self.fields['arsp_Enc_Lic'].widget.attrs['readonly'] = True  
            self.fields['arsp_Chec_Lic'].widget.attrs['readonly'] = True  
            self.fields['arsp_Ver_Lic'].widget.attrs['readonly'] = True  
            self.fields['arsp_Lab_Lic'].widget.attrs['readonly'] = True  
            self.fields['arsp_Head_Lic'].widget.attrs['readonly'] = True
        



#for batch table
class BatchTable_form(forms.ModelForm):
        bat_SiteCode = forms.ModelChoiceField(
            queryset=SiteData.objects.all(),
            to_field_name='SiteCode',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Site Code",
            required=False
            
        )

        bat_Checker = forms.ModelChoiceField(
            queryset=arsStaff_Details.objects.all(),
            to_field_name='Staff_Name',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Staff",
            required=False,
        )

        bat_Verifier = forms.ModelChoiceField(
            queryset=arsStaff_Details.objects.all(),
            to_field_name='Staff_Name',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Staff",
            required=False,
        )

        bat_LabManager = forms.ModelChoiceField(
            queryset=arsStaff_Details.objects.all(),
            to_field_name='Staff_Name',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Staff",
            required=False,
        )

        bat_Encoder= forms.ModelChoiceField(
            queryset=arsStaff_Details.objects.all(),
            to_field_name='Staff_Name',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Staff",
            required=False,
        )

        bat_Head= forms.ModelChoiceField(
            queryset=arsStaff_Details.objects.all(),
            to_field_name='Staff_Name',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Staff",
            required=False,
        )

        class Meta:
            model = Batch_Table
            fields = '__all__'
            widgets = {
            'bat_Referral_Date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'MM/DD/YYYY'}),
            'bat_RefNo' :forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'ex. 0001-0002'}),
            'bat_BatchNo' :forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'ex. 1'}),
            'bat_Total_batch' :forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'ex. 1'}),
            
            # Add more fields as needed
            }

        def __init__(self, *args, **kwargs):
            super(BatchTable_form, self).__init__(*args, **kwargs)
            self.fields['bat_SiteCode'].queryset = SiteData.objects.all() # Always load the latest Site Code instances
            self.fields['bat_AccessionNo'].widget.attrs['readonly'] = True  # AccessionNo read-only
            self.fields['bat_Batch_Name'].widget.attrs['readonly'] = True  # Batch_Name read-only
            self.fields['bat_AccessionNoGen'].widget = forms.HiddenInput()
            self.fields['bat_Enc_Lic'].widget.attrs['readonly'] = True  
            self.fields['bat_Chec_Lic'].widget.attrs['readonly'] = True  
            self.fields['bat_Ver_Lic'].widget.attrs['readonly'] = True  
            self.fields['bat_Lab_Lic'].widget.attrs['readonly'] = True  
            self.fields['bat_Head_Lic'].widget.attrs['readonly'] = True
            self.fields['bat_Status'].required=False
            # self.fields['Batch_Code'].widget = forms.HiddenInput()


         # --- Custom cleaning methods to save Staff_Name as string ---
        def clean_bat_Encoder(self):
            encoder = self.cleaned_data.get("bat_Encoder")
            return encoder.Staff_Name if encoder else ""

        def clean_bat_Checker(self):
            checker = self.cleaned_data.get("bat_Checker")
            return checker.Staff_Name if checker else ""

        def clean_bat_Verifier(self):
            verifier = self.cleaned_data.get("bat_Verifier")
            return verifier.Staff_Name if verifier else ""

        def clean_bat_LabManager(self):
            manager = self.cleaned_data.get("bat_LabManager")
            return manager.Staff_Name if manager else ""

        def clean_bat_Head(self):
            head = self.cleaned_data.get("bat_Head")
            return head.Staff_Name if head else ""
        
#for adding of site code
class SiteCode_Form(forms.ModelForm):
    class Meta:
        model = SiteData
        fields = ['SiteCode', 'SiteName']


class SiteCode_uploadForm(forms.ModelForm):
     class Meta:
          model = SiteCode_upload
          fields = ['File_uploadSite']

#to handle many to many relationship saving
def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self.save_m2m()
        return instance


#Breakpoints data
class BreakpointsForm(forms.ModelForm):
     class Meta:
          model = BreakpointsTable
          fields = '__all__'
          widgets = { 
               'Potency': forms.NumberInput(attrs={'min': 0, 'max': 1000}),
                     }
          
     def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Replace None with an empty string or another default value
        for field_name in self.fields:
            value = getattr(instance, field_name)
            if value is None:
                setattr(instance, field_name, '')

        if commit:
            instance.save()
            self.save_m2m()
        return instance

class Breakpoint_uploadForm(forms.ModelForm):
     class Meta:
          model = Breakpoint_upload
          fields = ['File_uploadBP']

#ensure only csv and excel are uploaded
def clean_file_upload(self):
        file = self.cleaned_data.get('File_uploadBP') #make sure this matches the model 
        if file:
            if not file.name.endswith('.csv') and not file.name.endswith('.xlsx'):
                raise forms.ValidationError('File must be a CSV or Excel file.')
        return file

#for antibiotic entry form
class AntibioticEntryForm(forms.ModelForm):
        ab_Abx_code = forms.ModelChoiceField(
            queryset=BreakpointsTable.objects.all(),
            to_field_name='Antibiotic',
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Antibiotic",
            required=False,
        )
        
        class Meta:
            model = AntibioticEntry
            fields = '__all__'

        def __init__(self, *args, **kwargs):
            super(AntibioticEntryForm, self).__init__(*args, **kwargs)
            self.fields['ab_AccessionNo'].widget.attrs['readonly'] = True  # Make Egasp_id read-only


class SpecimenTypeForm(forms.ModelForm):
    class Meta:
        model = SpecimenTypeModel  # Ensure the model is specified
        fields = ['Specimen_name', 'Specimen_code']  # Include the fields you want in the form


class ContactForm(forms.ModelForm):
    class Meta:
        model = arsStaff_Details
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        self.fields['Staff_Telnum'].widget = forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '09171234567',  # Philippine phone number format
            'readonly': False  # Ensure it's not blocking JavaScript updates
        })

# #for locations

# class CityForm(forms.ModelForm):
#     class Meta:
#         model = City
#         fields = ["cityname", "province"]
#         widgets = {
#             "cityname": forms.TextInput(attrs={"class": "form-control"}),
#             "province": forms.Select(attrs={"class": "form-control"}),
#         }


#for tat monitoring
class TATUploadForm(forms.ModelForm):
    class Meta:
        model = TATUpload
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'})
        }

class TAT_form(forms.ModelForm):
     class Meta:
        model = TATform  # Ensure the model is specified
        fields = '__all__'  # Include the fields you want in the form


