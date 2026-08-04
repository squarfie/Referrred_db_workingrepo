
from .models import *
from django import forms
from apps.home.models import *
from apps.home_final.models import *



# WGS Projects
class WGSProjectForm(forms.ModelForm):
    class Meta:
        model = WGS_Project
        fields = '__all__'
        widgets = {
               'WGS_SampleInfoSummary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
               'WGS_BactScoutSummary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
               'WGS_GtdbTkSummary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
               'WGS_GambitSummary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
               'WGS_MlstSummary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
               'WGS_Checkm2Summary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            }


# Final Referred Data Upload Form
class DemogsDataUploadForm(forms.ModelForm):
     class Meta:
          model = DemogsData_upload
          fields = ['DemogsDataFile']

# display yes/no field for boolean fields in the form
def yes_no_field():
    return forms.TypedChoiceField(
        choices=(
            (False, "No"),
            (True, "Yes"),
        ),
        coerce=lambda value: value in (
            True,
            "True",
            "true",
            "1",
            1,
        ),
        initial=False,
        required=False,
    )


class SampleInfoForm(forms.ModelForm):
     DNA_extraction = yes_no_field()
     library_preparation = yes_no_field()
     sequencing_platform = yes_no_field()
     class Meta:
            model = SampleInformation
            fields = '__all__'

class SampleInfoUploadForm(forms.ModelForm):
     class Meta:
          model = SampleInfoUpload
          fields = ['sampleinfo']



class BactScoutForm(forms.ModelForm):
        class Meta:
            model = BactScout
            fields = '__all__'

class BactScoutUploadForm(forms.ModelForm):
     class Meta:
          model = BactScoutUpload
          fields = ['bactscoutfile']




class GtdbTkForm(forms.ModelForm):
        class Meta:
            model = GtdbTk
            fields = '__all__'


class GtdbTkUploadForm(forms.ModelForm):
     class Meta:
          model = GtdbTkUpload
          fields = ['GtdbTkFile']


class GambitUploadForm(forms.ModelForm):
     class Meta:
          model = GambitUpload
          fields = ['GambitFile']


class GambitForm(forms.ModelForm):
        class Meta:
            model = Gambit
            fields = '__all__'


class MlstUploadForm(forms.ModelForm):
     class Meta:
          model = MlstUpload
          fields = ['Mlstfile']


class MlstForm(forms.ModelForm):
        class Meta:
            model = Mlst
            fields = '__all__'

class Checkm2UploadForm(forms.ModelForm):
     class Meta:
          model = Checkm2Upload
          fields = ['Checkm2file']


class Checkm2Form(forms.ModelForm):
     class Meta:
          model = Checkm2
          fields = '__all__'



class AssemblyUploadForm(forms.ModelForm):
     class Meta:
          model = AssemblyUpload
          fields = ['Assemblyfile']


class AssemblyForm(forms.ModelForm):
     class Meta:
          model = AssemblyScan
          fields = '__all__'


class AmrUploadForm(forms.ModelForm):
     class Meta:
          model = AmrfinderUpload
          fields = ['Amrfinderfile']


class AmrfinderForm(forms.ModelForm):
     class Meta:
          model = Amrfinderplus
          fields = '__all__'

class DeleteRangeForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))


class CustomWGSPipelineForm(forms.ModelForm):
     category = forms.MultipleChoiceField(
          label="Categories",
          choices=CustomWGSPipeline.CATEGORY_CHOICES,
          required=False,
          widget=forms.CheckboxSelectMultiple,
     )

     def __init__(self, *args, **kwargs):
          super().__init__(*args, **kwargs)
          self.fields["slug"].required = False
          if self.instance and self.instance.pk:
               current_category = self.instance.category
               if isinstance(current_category, list):
                    self.initial["category"] = current_category
               elif current_category:
                    self.initial["category"] = [current_category]

     def clean_category(self):
          return self.cleaned_data.get("category") or []

     def clean_platform(self):
          return (self.cleaned_data.get("platform") or "").strip() or "Illumina"

     class Meta:
          model = CustomWGSPipeline
          fields = [
               "name", "slug", "description", "sequencing_type", "platform",
               "category", "sheet_name", "accession_column", "sample_name_column",
               "date_column", "show_in_upload_center", "show_in_overview", "is_active",
          ]
          widgets = {
               "description": forms.Textarea(attrs={"rows": 3}),
               "slug": forms.TextInput(attrs={"placeholder": "auto-filled from name if blank"}),
               "platform": forms.TextInput(attrs={"placeholder": "ex. Illumina, Oxford Nanopore, PacBio Revio"}),
               "sheet_name": forms.TextInput(attrs={"placeholder": "Optional Excel sheet name"}),
               "accession_column": forms.TextInput(attrs={"placeholder": "ex. Accession No"}),
               "sample_name_column": forms.TextInput(attrs={"placeholder": "ex. sample"}),
               "date_column": forms.TextInput(attrs={"placeholder": "Optional upload date column"}),
          }


class CustomWGSPipelineFieldForm(forms.ModelForm):
     def __init__(self, *args, **kwargs):
          super().__init__(*args, **kwargs)
          self.fields["field_key"].required = False

     class Meta:
          model = CustomWGSPipelineField
          fields = [
               "field_key", "display_label", "source_column", "column_aliases",
               "data_type", "required", "default_value", "show_in_table",
               "show_in_detail", "show_in_export", "sort_order",
          ]
          widgets = {
               "column_aliases": forms.Textarea(attrs={"rows": 3, "placeholder": "Optional: one alternate column name per line"}),
               "field_key": forms.TextInput(attrs={"placeholder": "ex. genome_size"}),
               "display_label": forms.TextInput(attrs={"placeholder": "ex. Genome Size"}),
               "source_column": forms.TextInput(attrs={"placeholder": "Exact upload column name"}),
          }


class CustomPipelineUploadForm(forms.Form):
     file = forms.FileField()
     replace_existing = forms.BooleanField(
          required=False,
          initial=True,
          label="Replace existing records for matching accessions in this pipeline",
     )
