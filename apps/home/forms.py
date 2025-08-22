from .models import *
from django import forms



    
class Referred_Form(forms.ModelForm):

        #using modelchoicefield for dynamic rendering
        SiteCode = forms.ModelChoiceField(
            queryset=SiteData.objects.all(),
            to_field_name='SiteCode',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Site Code",
            required=False
            
        )


        Spec_Type = forms.ModelChoiceField(
            queryset=SpecimenTypeModel.objects.all(),
            to_field_name='Specimen_code',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Specimen",
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
            
            # Add more fields as needed
            }
            
        def __init__(self, *args, **kwargs):
            super(Referred_Form, self).__init__(*args, **kwargs)
            self.fields['Site_Name'].widget.attrs['readonly'] = True  # Site_Name read-only
            self.fields['AccessionNo'].widget.attrs['readonly'] = True  # AccessionNo read-only
            self.fields['Batch_Name'].widget.attrs['readonly'] = True  # Batch_Name read-only
            self.fields['AccessionNoGen'].widget = forms.HiddenInput()
            # self.fields['Batch_Code'].widget = forms.HiddenInput()
            

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields['SiteCode'].queryset = SiteData.objects.all() # Always load the latest ClinicData instances into the PTIDCode field
               # Set default queryset for country

    

class SiteCode_Form(forms.ModelForm):
    class Meta:
        model = SiteData
        fields = ['SiteCode', 'SiteName']



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
        model = Lab_Staff_Details
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        self.fields['LabStaff_Telnum'].widget = forms.TextInput(attrs={
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