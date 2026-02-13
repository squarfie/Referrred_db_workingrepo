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



class FinalAntibioticUploadForm(forms.ModelForm):
    class Meta:
        model = FinalAntibiotic_upload
        fields = ['FinalAntibioticFile']
        widgets = {
            'FinalAntibioticFile': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }


#### Final referred form
class FinalReferred_Form(forms.ModelForm):

        f_Spec_Type = forms.ModelChoiceField(
            queryset=SpecimenTypeModel.objects.all(),
            widget=forms.Select(attrs={'class': "form-select fw-bold"}),
            empty_label="Select Specimen",
            required=False,
        )


        f_ars_OrgCode = forms.ModelChoiceField(
            queryset=Organism_List.objects.all(),
            to_field_name='Whonet_Org_Code',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Organism",
            required=False,
            
        )
        f_Site_Org = forms.ModelChoiceField(
            queryset=Organism_List.objects.all(),
            to_field_name='Whonet_Org_Code', 
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Organism",
            required=False,
            
        )

        f_Site_OrgName = forms.CharField(
            required=False,
            widget=forms.TextInput(attrs={
                "class": "form-control fw-bold",
                "readonly": True
            })
        )

        f_ars_OrgName = forms.CharField(
            required=False,
            widget=forms.TextInput(attrs={
                "class": "form-control fw-bold",
                "readonly": True
            })
        )

        
        f_ars_reco_Code = forms.ModelChoiceField(
            queryset=Recommendation_items.objects.all(),
            to_field_name='RecoCode',  
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select no",
            required=False,
            
        )

        f_Site_Pre = forms.ModelChoiceField(
            queryset=Phenotype_Pre.objects.all(),
            to_field_name='Pre_Phenotypes',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Phenotype",
            required=False,
            
        )

        f_Site_Pos = forms.ModelChoiceField(
            queryset=Phenotype_Post.objects.all(),
            to_field_name='Post_Phenotypes',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Phenotype",
            required=False,
            
        )


        f_ars_Pre = forms.ModelChoiceField(
            queryset=Phenotype_Pre.objects.all(),
            to_field_name='Pre_Phenotypes',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Phenotype",
            required=False,
            
        )

        f_ars_Post = forms.ModelChoiceField(
            queryset=Phenotype_Post.objects.all(),
            to_field_name='Post_Phenotypes',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Phenotype",
            required=False,
            
        )


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
            'f_ars_reco': forms.Textarea(attrs={'class': 'textarea form-control', 'rows': '14'}),
            'f_ars_description': forms.Textarea(attrs={'class': 'textarea form-control', 'rows': '9'}),
            "f_Batch_id": forms.HiddenInput(),
            
            
            # Add more fields as needed
            }
            
       
            

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # self.fields['SiteCode'].queryset = SiteData.objects.all() # Always load the latest Site Code
            self.fields['f_bat_seq'].widget.attrs['readonly'] = True
            self.fields["f_Batch_id"].disabled = True
            self.fields['f_SiteCode'].widget.attrs['readonly'] = True
            self.fields['f_Batch_Code'].widget.attrs['readonly'] = True
            self.fields['f_AccessionNo'].widget.attrs['readonly'] = True
            self.fields['f_Batch_id'].required=False
            self.fields['f_RefNo'].widget.attrs['readonly'] = True
            self.fields['f_Referral_Date'].widget.attrs['readonly'] = True
            self.fields['f_BatchNo'].widget.attrs['readonly'] = True
            self.fields['f_Site_Name'].widget.attrs['readonly'] = True
            self.fields['f_Age'].widget.attrs['readonly'] = True
            self.fields['f_Site_Org'].queryset = Organism_List.objects.all() # Always load the latest Site Code
            self.fields['f_Site_Org'].label_from_instance = lambda obj: obj.Whonet_Org_Code # Specify the field to display
            self.fields['f_Site_OrgName'].label_from_instance = lambda obj: obj.Organism # Specify the field to display
            self.fields['f_ars_OrgCode'].queryset = Organism_List.objects.all() # Always load the latest Site Code
            self.fields['f_ars_OrgCode'].label_from_instance = lambda obj: obj.Whonet_Org_Code # Specify the field to display
            self.fields['f_ars_OrgName'].label_from_instance = lambda obj: obj.Organism # Specify the field to display
           


class Final_AntibioticEntryForm(forms.ModelForm):
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
            self.fields['ab_AccessionNo'].widget.attrs['readonly'] = True  





class Classification_Form(forms.ModelForm):
     class Meta:
          model = Classification_Table
          fields = '__all__'
          
          def __init__(self, *args, **kwargs):
                super(Classification_Form, self).__init__(*args, **kwargs)
                self.fields['Class_Chk_Emerging'].widget.attrs['readonly'] = True  


class Emerging_List_Form(forms.ModelForm):
     class Meta:
          model = Emerging_Table
          fields = '__all__'
    
