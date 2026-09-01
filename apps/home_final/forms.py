from apps.home.models import *
from apps.wgs_app.models import *
from .models import *

from django import forms
from apps.home.forms import *
from apps.wgs_app.forms import *
from phonenumber_field.formfields import PhoneNumberField
import re


def final_accession_year_prefix(accession):
    match = re.match(r"\s*(\d{2})ARS", str(accession or "").strip(), re.IGNORECASE)
    return match.group(1) if match else ""



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
            error_messages={
                "invalid_choice": "Invalid specimen type. Select a specimen from the list.",
            },
        )


        f_ars_OrgCode = forms.ModelChoiceField(
            queryset=Organism_List.objects.all().order_by('Whonet_Org_Code'),
            to_field_name='Whonet_Org_Code',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Organism",
            required=False,
            
        )
        f_Site_Org = forms.ModelChoiceField(
            queryset=Organism_List.objects.all().order_by('Whonet_Org_Code'),
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

        
        f_ars_reco_Code = forms.ChoiceField(
            choices=recommendation_code_choices,
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            required=False,
            
        )

        f_Site_Pre = forms.ModelChoiceField(
            queryset=Phenotype_Pre.objects.all().order_by('Pre_Phenotypes'),
            to_field_name='Pre_Phenotypes',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Phenotype",
            required=False,
            
        )

        f_Site_Pos = forms.ModelChoiceField(
            queryset=Phenotype_Post.objects.all().order_by('Post_Phenotypes'),
            to_field_name='Post_Phenotypes',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Phenotype",
            required=False,
            
        )


        f_ars_Pre = forms.ModelChoiceField(
            queryset=Phenotype_Pre.objects.all().order_by('Pre_Phenotypes'),
            to_field_name='Pre_Phenotypes',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Phenotype",
            required=False,
            
        )

        f_ars_Post = forms.ModelChoiceField(
            queryset=Phenotype_Post.objects.all().order_by('Post_Phenotypes'),
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
            'f_Site_Pre_ed': forms.TextInput(attrs={'class': 'form-control'}),
            'f_Site_Pos_ed': forms.TextInput(attrs={'class': 'form-control'}),
            'f_Comments': forms.Textarea(attrs={'class': 'textarea form-control', 'rows': '3'}),
            'f_ars_Pre_ed': forms.TextInput(attrs={'class': 'form-control'}),
            'f_ars_Post_ed': forms.TextInput(attrs={'class': 'form-control'}),
            'f_ars_reco': forms.Textarea(attrs={'class': 'textarea form-control', 'rows': '14'}),
            'f_ars_description': forms.Textarea(attrs={'class': 'textarea form-control', 'rows': '9'}),
            "f_Batch_id": forms.HiddenInput(),
            
            
            # Add more fields as needed
            }
            
       
            

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # self.fields['SiteCode'].queryset = SiteData.objects.all() # Always load the latest Site Code
            self.fields['f_bat_seq'].widget.attrs['readonly'] = True
            accession = (
                self.data.get("f_AccessionNo")
                if self.is_bound
                else getattr(self.instance, "f_AccessionNo", "")
            )
            derived_seq = final_accession_ref_sequence(accession)
            if derived_seq is not None:
                self.initial["f_bat_seq"] = derived_seq
                self.fields["f_bat_seq"].initial = derived_seq
                if self.instance:
                    self.instance.f_bat_seq = derived_seq
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
            self.fields['f_Age_Display'].widget.attrs['readonly'] = True
            self.fields['f_Age_Display'].widget.attrs['class'] = 'form-control'
            self.fields['f_Age_Display'].widget.attrs['tabindex'] = '-1'
            self.fields['f_Site_Org'].queryset = Organism_List.objects.all() # Always load the latest Site Code
            self.fields['f_Site_Org'].label_from_instance = lambda obj: obj.Whonet_Org_Code # Specify the field to display
            self.fields['f_Site_OrgName'].label_from_instance = lambda obj: obj.Organism # Specify the field to display
            self.fields['f_ars_OrgCode'].queryset = Organism_List.objects.all() # Always load the latest Site Code
            self.fields['f_ars_OrgCode'].label_from_instance = lambda obj: obj.Whonet_Org_Code # Specify the field to display
            self.fields['f_ars_OrgName'].label_from_instance = lambda obj: obj.Organism # Specify the field to display
            if not self.is_bound and getattr(self.instance, "pk", None):
                site_org = (getattr(self.instance, "f_Site_Org", "") or "").strip()
                ars_org = (getattr(self.instance, "f_ars_OrgCode", "") or "").strip()
                site_choice = resolve_organism_choice(
                    site_org,
                    getattr(self.instance, "f_Site_OrgName", ""),
                )
                ars_choice = resolve_organism_choice(
                    ars_org,
                    getattr(self.instance, "f_ars_OrgName", ""),
                )
                if site_choice:
                    self.initial["f_Site_Org"] = site_choice.Whonet_Org_Code
                    self.fields["f_Site_Org"].initial = site_choice.Whonet_Org_Code
                    self.initial["f_Site_OrgName"] = site_choice.Organism
                elif site_org:
                    self.initial["f_Site_Org"] = site_org
                    self.fields["f_Site_Org"].initial = site_org
                if ars_choice:
                    self.initial["f_ars_OrgCode"] = ars_choice.Whonet_Org_Code
                    self.fields["f_ars_OrgCode"].initial = ars_choice.Whonet_Org_Code
                    self.initial["f_ars_OrgName"] = ars_choice.Organism
                elif ars_org:
                    self.initial["f_ars_OrgCode"] = ars_org
                    self.fields["f_ars_OrgCode"].initial = ars_org
           
        def clean_f_bat_seq(self):
            accession = (
                self.cleaned_data.get("f_AccessionNo")
                or getattr(self.instance, "f_AccessionNo", "")
            )
            derived_seq = final_accession_ref_sequence(accession)
            if derived_seq is not None:
                return derived_seq
            return self.cleaned_data.get("f_bat_seq")

        def clean(self):
            cleaned_data = super().clean()
            accession = (
                cleaned_data.get("f_AccessionNo")
                or getattr(self.instance, "f_AccessionNo", "")
            )
            derived_seq = final_accession_ref_sequence(accession)
            if derived_seq is not None:
                cleaned_data["f_bat_seq"] = derived_seq

            return cleaned_data



class Final_AntibioticEntryForm(forms.ModelForm):
        ab_Abx_code = forms.ModelChoiceField(
            queryset=BreakpointsTable.objects.all(),
            to_field_name='Antibiotic',
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Antibiotic",
            required=False,
        )
        
        class Meta:
            model = Final_AntibioticEntry
            fields = '__all__'

        def __init__(self, *args, **kwargs):
            super(Final_AntibioticEntryForm, self).__init__(*args, **kwargs)
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
    


########## Concordance Analysis Form

class ConcordanceReportFilterForm(forms.Form):

    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control"
            }
        )
    )

    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control"
            }
        )
    )

    confirm_generate = forms.BooleanField(
        required=True,
        label="Confirm snapshot generation",
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input"}
        )
    )

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_date")
        end = cleaned_data.get("end_date")

        if start and end and start > end:
            raise forms.ValidationError("Start date cannot be after end date.")

        return cleaned_data


class ConcordanceOptionsForm(forms.ModelForm):
    ALL_ORGANISMS_VALUE = "__ALL_ORGANISMS__"

    applied_org = forms.ChoiceField(
        required=False,
        label="Organism",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    applied_org_grp = forms.MultipleChoiceField(
        required=False,
        label="Organism groups",
        widget=forms.SelectMultiple(attrs={"class": "form-control", "size": "6"}),
    )

    class Meta:
        model = ConcordanceOptions
        fields = [
            "prioritize_mic_site",
            "prioritize_disk_site",
            "no_serotyping",
            "applied_org",
            "applied_org_grp",
            "is_active",
        ]
        widgets = {
            "prioritize_mic_site": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "prioritize_disk_site": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "no_serotyping": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        org_choices = [
            ("", "n/a"),
            (self.ALL_ORGANISMS_VALUE, "All organisms"),
        ]
        org_choices.extend(
            (org.Whonet_Org_Code, f"{org.Whonet_Org_Code} - {org.Organism}")
            for org in Organism_List.objects.all().order_by("Whonet_Org_Code")
        )
        self.fields["applied_org"].choices = org_choices
        group_codes = (
            Organism_List.objects
            .exclude(Genus_Code__isnull=True)
            .exclude(Genus_Code="")
            .values_list("Genus_Code", flat=True)
            .distinct()
            .order_by("Genus_Code")
        )
        self.fields["applied_org_grp"].choices = [
            (code, code)
            for code in group_codes
        ]
        if self.instance and self.instance.pk:
            if (self.instance.applied_org or "").strip().upper() in {"-", "N/A", "NA"}:
                self.initial["applied_org"] = ""
            self.initial["applied_org_grp"] = [
                code.strip()
                for code in (self.instance.applied_org_grp or "").split(",")
                if code.strip()
            ]
        elif not self.is_bound:
            self.initial["is_active"] = True

    def clean(self):
        cleaned_data = super().clean()
        has_rule = any(
            cleaned_data.get(field)
            for field in ("prioritize_mic_site", "prioritize_disk_site", "no_serotyping")
        )
        if not has_rule:
            raise forms.ValidationError("Select at least one concordance rule option.")
        if cleaned_data.get("prioritize_mic_site") and cleaned_data.get("prioritize_disk_site"):
            raise forms.ValidationError("Choose either MIC priority or disk priority, not both.")
        if has_rule and not cleaned_data.get("applied_org") and not cleaned_data.get("applied_org_grp"):
            raise forms.ValidationError("Select an organism or at least one organism group for the special rule.")
        return cleaned_data
