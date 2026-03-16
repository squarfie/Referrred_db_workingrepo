from .models import *
from django import forms




# Referred Data Upload Form
class ReferredUploadForm(forms.ModelForm):
     class Meta:
          model = ReferredData_upload
          fields = ['ReferredDataFile']


    
class Referred_Form(forms.ModelForm):

        Spec_Type = forms.ModelChoiceField(
            queryset=SpecimenTypeModel.objects.all(),
            widget=forms.Select(attrs={'class': "form-select fw-bold"}),
            empty_label="Select Specimen",
            required=False,
        )

        ars_OrgCode = forms.ModelChoiceField(
            queryset=Organism_List.objects.all(),
            to_field_name='Whonet_Org_Code',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Organism",
            required=False,
            
        )
        Site_Org = forms.ModelChoiceField(
            queryset=Organism_List.objects.all(),
            to_field_name='Whonet_Org_Code', 
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Organism",
            required=False,
            
        )

        Site_OrgName = forms.CharField(
            required=False,
            widget=forms.TextInput(attrs={
                "class": "form-control fw-bold",
                "readonly": True
            })
        )

        ars_OrgName = forms.CharField(
            required=False,
            widget=forms.TextInput(attrs={
                "class": "form-control fw-bold",
                "readonly": True
            })
        )

        
        ars_reco_Code = forms.ModelChoiceField(
            queryset=Recommendation_items.objects.all(),
            to_field_name='RecoCode',  
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select no",
            required=False,
            
        )

        Site_Pre = forms.ModelChoiceField(
            queryset=Phenotype_Pre.objects.all(),
            to_field_name='Pre_Phenotypes',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Phenotype",
            required=False,
            
        )

        Site_Pos = forms.ModelChoiceField(
            queryset=Phenotype_Post.objects.all(),
            to_field_name='Post_Phenotypes',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Phenotype",
            required=False,
            
        )


        ars_Pre = forms.ModelChoiceField(
            queryset=Phenotype_Pre.objects.all(),
            to_field_name='Pre_Phenotypes',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Phenotype",
            required=False,
            
        )

        ars_Post = forms.ModelChoiceField(
            queryset=Phenotype_Post.objects.all(),
            to_field_name='Post_Phenotypes',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Phenotype",
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
            'Date_Accomplished_ARSP' :forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'MM/DD/YYYY'}),
            'RefNo' :forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'ex. 0001'}),
            'BatchNo' :forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'ex. 1.1'}),
            'Growth_others' :forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex. after 24 hrs of incubation'}),
            'Comments': forms.Textarea(attrs={'class': 'textarea form-control', 'rows': '3'}),
            'ars_reco': forms.Textarea(attrs={'class': 'textarea form-control', 'rows': '11'}),
            'ars_description': forms.Textarea(attrs={'class': 'textarea form-control', 'rows': '6'}),
            "Batch_id": forms.HiddenInput(),
            
            }

                

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['bat_seq'].widget.attrs['readonly'] = True
            self.fields["Batch_id"].disabled = True      
            self.fields['SiteCode'].widget.attrs['readonly'] = True
            self.fields['Batch_Code'].widget.attrs['readonly'] = True
            self.fields['AccessionNo'].widget.attrs['readonly'] = True
            self.fields['Status'].required=False
            self.fields['Batch_id'].required=False
            self.fields['RefNo'].widget.attrs['readonly'] = True
            self.fields['Referral_Date'].widget.attrs['readonly'] = True
            self.fields['BatchNo'].widget.attrs['readonly'] = True
            self.fields['Site_Name'].widget.attrs['readonly'] = True
            self.fields['Age'].widget.attrs['readonly'] = True
            # Dynamic queryset loading
            self.fields['Site_Org'].queryset = Organism_List.objects.all() # Always load the latest Site Code
            self.fields['Site_Org'].label_from_instance = lambda obj: obj.Whonet_Org_Code # Specify the field to display
            self.fields['Site_OrgName'].label_from_instance = lambda obj: obj.Organism 
            self.fields['ars_OrgCode'].queryset = Organism_List.objects.all() # Always load the latest Organism_List
            self.fields['ars_OrgCode'].label_from_instance = lambda obj: obj.Whonet_Org_Code # Specify the field to display
            self.fields['ars_OrgName'].label_from_instance = lambda obj: obj.Organism 


        
        

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
            'bat_Date_Accomplished': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'MM/DD/YYYY'}),
            
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


class BatchEditForm(forms.ModelForm):
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
        fields = [
            # ONLY fields allowed to change in edit
            "bat_Encoder",
            "bat_Enc_Lic",
            "bat_Checker",
            "bat_Chec_Lic",
            "bat_Verifier",
            "bat_Ver_Lic",
            "bat_LabManager",
            "bat_Lab_Lic",
            "bat_Head",
            "bat_Head_Lic",
            "bat_Date_Accomplished",
        ]
        widgets = {
            'bat_Date_of_Entry': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'MM/DD/YYYY'}),
            'bat_Date_Accomplished': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'MM/DD/YYYY'}),
        }

    def __init__(self, *args, **kwargs):
                super(BatchEditForm, self).__init__(*args, **kwargs)
                self.fields['bat_Enc_Lic'].widget.attrs['readonly'] = True  
                self.fields['bat_Chec_Lic'].widget.attrs['readonly'] = True  
                self.fields['bat_Ver_Lic'].widget.attrs['readonly'] = True  
                self.fields['bat_Lab_Lic'].widget.attrs['readonly'] = True  
                self.fields['bat_Head_Lic'].widget.attrs['readonly'] = True


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

    Org = forms.ModelChoiceField(
        queryset=Organism_List.objects.all(),
        to_field_name='Whonet_Org_Code',
        widget=forms.Select(attrs={'class': "form-select fw-bold"}),
        empty_label="Select Organism",
        required=False,
    )

    Whonet_Abx = forms.ModelChoiceField(
            queryset=Antibiotic_List.objects.all(),
            to_field_name='Whonet_Abx',  # Specify the field you want as the value
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Antibiotic Code",
            required=False,
            
        )

    Antibiotic = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "readonly": True, "style": "background-color: #e9ecef !important; cursor: not-allowed;"})
    )

    Abx_code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "readonly": True, "style": "background-color: #e9ecef !important; cursor: not-allowed;"})
    )

    Tier = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "readonly": True, "style": "background-color: #e9ecef !important; cursor: not-allowed;"})
    )

    Spec_code = forms.ModelChoiceField(
            queryset=SpecimenTypeModel.objects.all(),
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Specimen",
            required=False,
            
        )


    class Meta:
        model = BreakpointsTable
        fields = "__all__"


    def save(self, commit=True):
        instance = super().save(commit=False)

        if instance.Whonet_Abx:
            try:
                abx = Antibiotic_List.objects.get(
                    Antibiotic=instance.Whonet_Abx
                )

                instance.Antibiotic = abx.Antibiotic
                instance.Abx_code = abx.Abx_code
                instance.Tier = abx.Tier

            except Antibiotic_List.DoesNotExist:
                pass

        if commit:
            instance.save()

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
            self.fields['ab_AccessionNo'].widget.attrs['readonly'] = True  # Make Accssion read-only


class RawAntibioticUploadForm(forms.ModelForm):
    class Meta:
        model = RawAntibiotic_upload
        fields = ['RawAntibioticFile']
        widgets = {
            'RawAntibioticFile': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }




class SpecimenTypeForm(forms.ModelForm):
    class Meta:
        model = SpecimenTypeModel  
        fields = ['Specimen_name', 'Specimen_code', 'Emerging_Spec_Flag', 'Specimen_Code_Grp', 'Specimen_Grp_Name']  # Include the fields you want in the form
        widgets = {
             "Emerging_Spec_Flag": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            vals = SpecimenTypeModel.objects.values_list("Specimen_code", flat=True).distinct()
            self.fields["Specimen_Code_Grp"].choices = [(v, v) for v in vals]


class SpecimenUploadForm(forms.ModelForm):
    class Meta:
        model = Specimen_upload
        fields = ['File_uploadSpec']
        widgets = {
            'File_uploadSpec': forms.FileInput(attrs={'class': 'form-control'})
        }



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



#Antibiotic Data
class AntibioticsForm(forms.ModelForm):
     class Meta:
          model = Antibiotic_List
          fields = '__all__'
          widgets = {
               'Antibiotitc' :forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex. Amoxicillin'}),
               'Abx_code' :forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex. AMX'}),
               'Whonet_Abx':forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex. AMX_ND10 if disk or AMX_NM'}), 
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

class Antibiotics_uploadForm(forms.ModelForm):
     class Meta:
          model = Antibiotic_upload
          fields = ['File_uploadAbx']


# Organism Data
class OrganismForm(forms.ModelForm):
     class Meta:
          model = Organism_List
          fields = '__all__'


class Organism_uploadForm(forms.ModelForm):
     class Meta:
          model = Organism_upload
          fields =['File_uploadOrg']


class Emerge_Pheno_Form(forms.ModelForm):

        class Meta:
          model = Emerging_Filter_Age
          fields = '__all__'


class Eme_Crit_Upload_Form(forms.ModelForm):
     class Meta:
          model = Emerging_Crit_upload
          fields =['File_uploadEme']



class Phenotype_Pre_Form(forms.ModelForm):
     class Meta:
          model = Phenotype_Pre
          fields = '__all__'

class Pheno_pre_upForm(forms.ModelForm):
     class Meta:
          model = Pheno_upload_Pre
          fields = ['File_Pheno_pre']



class Phenotype_Post_Form(forms.ModelForm):
     class Meta:
          model = Phenotype_Post
          fields = '__all__'

class Pheno_post_upForm(forms.ModelForm):
     class Meta:
          model = Pheno_upload_Post
          fields = ['File_Pheno_post']




class Recco_item_Form(forms.ModelForm):
     class Meta:
          model = Recommendation_items
          fields = '__all__'
          


class Reco_item_upForm (forms.ModelForm):
     class Meta:
          model = Reco_item_upload
          fields = ['File_reco_desc']



#for tat monitoring
class TATStepConfigUploadForm(forms.ModelForm):
    class Meta:
        model = TATStepConfigUpload
        fields = ['tat_file']
        widgets = {
            'tat_file': forms.FileInput(attrs={'class': 'form-control'})
        }


class TATMonitoringForm(forms.ModelForm):
    class Meta:
        model = TATform
        exclude = ['tat_Date_Last_Update', 'tat_Batch_Isolates']
        widgets = {
            'tat_Referral_Date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'tat_Date_Released': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'tat_Running_TAT': forms.TextInput(attrs={
                'class': 'form-control bg-light', 
                'readonly': 'readonly',
                'style': 'cursor: not-allowed;'  # inject inline CSS here!
            }),
            'tat_Final_TAT': forms.TextInput(attrs={
                'class': 'form-control bg-light', 
                'readonly': 'readonly',
                'style': 'cursor: not-allowed;'  # inject inline CSS here!
            }),
        }

class TATStepConfigForm(forms.ModelForm):
    class Meta:
        model = TATStepConfig
        fields = '__all__'
        widgets = {
            'step_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter step name'
            }),
            'step_owner': forms.Select(attrs={
                'class': 'form-control'
            }),
            'target_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        step_type = cleaned_data.get('step_type')
        step_owner = cleaned_data.get('step_owner')

        if TATStepConfig.objects.filter(
            step_type=step_type,
            step_owner=step_owner
        ).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(
                "This step configuration already exists."
            )

        return cleaned_data



class TATStepForm(forms.ModelForm):
    performed_by = forms.ModelChoiceField(
            queryset=arsStaff_Details.objects.all(),
            widget=forms.Select(attrs={'class': "form-select fw-bold", 'style': 'max-width: auto;'}),
            empty_label="Select Staff",
            required=False,
        )

    class Meta:
        model = TATStep
        fields = [
            'step_config',
            'date_received',
            'date_finished',
            'performed_by',
            'remarks',
        ]
        widgets = {
            'step_config': forms.Select(attrs={'class': 'form-control'}),
            'date_received': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_finished': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }


TATStepFormSet = forms.inlineformset_factory(
    TATform, 
    TATStep, 
    form=TATStepForm,  
    extra=1, 
    can_delete=True
)



class NonWorkingDayForm(forms.ModelForm):
    class Meta:
        model = NonWorkingDay
        fields = ['date', 'description', 'applies_to']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'applies_to': forms.Select(attrs={'class': 'form-control'}),
        }
