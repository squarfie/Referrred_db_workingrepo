from apps.home.models import *
from apps.wgs_app.models import *
from .models import *

from django import forms
from apps.home.forms import *
from apps.wgs_app.forms import *
from phonenumber_field.formfields import PhoneNumberField





# Final Referred Data Upload Form
class FinalDataUploadForm(forms.ModelForm):
     class Meta:
          model = FinalData_upload
          fields = ['FinalDataFile']



#### Final referred form
class FinalReferred_Form(forms.ModelForm):

        # #using modelchoicefield for dynamic rendering
        # SiteCode = forms.ModelChoiceField(
        #     queryset=SiteData.objects.all(),
        #     to_field_name='SiteCode',  # Specify the field you want as the value
        #     widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
        #     empty_label="Select Site Code",
        #     required=False
            
        # )


        f_Spec_Type = forms.ModelChoiceField(
            queryset=SpecimenTypeModel.objects.all(),
            to_field_name='Specimen_code',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Specimen",
            required=False,
            
        )

        # f_arsp_Checker = forms.ModelChoiceField(
        #     queryset=arsStaff_Details.objects.all(),
        #     to_field_name='Staff_Name',  # Specify the field you want as the value
        #     widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
        #     empty_label="Select Staff",
        #     required=False,
        # )

        # f_arsp_Verifier = forms.ModelChoiceField(
        #     queryset=arsStaff_Details.objects.all(),
        #     to_field_name='Staff_Name',  # Specify the field you want as the value
        #     widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
        #     empty_label="Select Staff",
        #     required=False,
        # )

        # f_arsp_LabManager = forms.ModelChoiceField(
        #     queryset=arsStaff_Details.objects.all(),
        #     to_field_name='Staff_Name',  # Specify the field you want as the value
        #     widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
        #     empty_label="Select Staff",
        #     required=False,
        # )

        # f_arsp_Encoder= forms.ModelChoiceField(
        #     queryset=arsStaff_Details.objects.all(),
        #     to_field_name='Staff_Name',  # Specify the field you want as the value
        #     widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
        #     empty_label="Select Staff",
        #     required=False,
        # )

        # f_arsp_Head= forms.ModelChoiceField(
        #     queryset=arsStaff_Details.objects.all(),
        #     to_field_name='Staff_Name',  # Specify the field you want as the value
        #     widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
        #     empty_label="Select Staff",
        #     required=False,
        # )


        class Meta:
            model = Final_Data
            fields ='__all__'
            widgets = {
            'f_Referral_Date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'MM/DD/YYYY'}),
            'f_Date_Birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'MM/DD/YYYY'}),
            'f_Date_Admis' :forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'MM/DD/YYYY'}),
            'f_Spec_Date' :forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'MM/DD/YYYY'}),
            'f_RefNo' :forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'ex. 0001'}),
            'f_BatchNo' :forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'ex. 1.1'}),
            'f_Comments': forms.Textarea(attrs={'class': 'textarea form-control', 'rows': '3'}),
            'f_ars_reco': forms.Textarea(attrs={'class': 'textarea form-control', 'rows': '3'}),
            
            # Add more fields as needed
            }
            
       
            

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # self.fields['SiteCode'].queryset = SiteData.objects.all() # Always load the latest Site Code
            self.fields['f_SiteCode'].widget.attrs['readonly'] = True
            self.fields['f_Batch_Code'].widget.attrs['readonly'] = True
            self.fields['f_AccessionNo'].widget.attrs['readonly'] = True
            self.fields['f_Batch_id'].required=False
            self.fields['f_RefNo'].widget.attrs['readonly'] = True
            self.fields['f_Referral_Date'].widget.attrs['readonly'] = True
            self.fields['f_BatchNo'].widget.attrs['readonly'] = True
            self.fields['f_Site_Name'].widget.attrs['readonly'] = True
           
        