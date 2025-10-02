
from .models import *
from django import forms
from apps.home.models import *



# WGS Projects
class WGSProjectForm(forms.ModelForm):
    class Meta:
        model = WGS_Project
        fields = '__all__'
        widgets = {
               'WGS_FastqSummary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
               'WGS_GambitSummary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
               'WGS_MlstSummary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
               'WGS_Checkm2Summary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            }

class FastqUploadForm(forms.ModelForm):
     class Meta:
          model = FastqUpload
          fields = ['fastqfile']


class FastqForm(forms.ModelForm):
        class Meta:
            model = FastqSummary
            fields = '__all__'


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