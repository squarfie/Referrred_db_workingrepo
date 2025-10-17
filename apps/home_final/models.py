from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.validators import EmailValidator
from django.apps import apps
from apps.home.models import *
from apps.wgs_app.models import *
from .models import *
from phonenumber_field.modelfields import PhoneNumberField


# Create your models here.
# for final edit table
class Final_Data(models.Model):
    f_Common_Choices = (
        ('n/a','n/a'),
        ('Yes', 'Yes'),
        ('No', 'No'),
    )

    f_Common_pheno = (
        ('n/a','n/a'),
        ('(+)','(+)'),
        ('(-)', '(-)'),
        ('NT', 'NT'),
    )
    f_SexatbirthChoice=(
        ('n/a','n/a'),
        ('Male', 'Male'),
        ('Female', 'Female')
    )

    f_ServiceTypeChoice=(
        ('n/a','n/a'),
        ('In','In'),
        ('Out','Out')
        
    )
    f_ReasonChoices=(
        ('n/a','n/a'),
        ('a & d','a & d'),
        ('confirmation of org and ast','a'),
        ('for ast only','b'),
        ('difficult to ID','c'),
        ('for serotyping','d'),
        ('for research','e'),
        ('Others','o')
    )

 
   
    # Batch Data
    f_Date_uploaded_fd = models.DateField(auto_now_add=True)
    f_Hide=models.BooleanField(default=False)
    f_Batch_Code=models.CharField(max_length=255, blank=True, null=True)
    f_Batch_Name=models.CharField(max_length=255, blank=True, null=True)
    f_Date_of_Entry =models.DateTimeField(auto_now_add=True, null=True)
    f_RefNo=models.CharField(max_length=20, blank=True, null=True)
    f_BatchNo=models.CharField(max_length=255, blank=True, null=True)
    f_Total_batch=models.CharField(max_length=100, blank=True, null=True)
    f_AccessionNo=models.CharField(max_length=255, blank=True, unique=True)
    f_AccessionNoGen=models.CharField(max_length=100, blank=True)
    f_Default_Year=models.DateField(null=True, blank=True)
    f_SiteCode=models.CharField(max_length=255, blank=True, null=True, default="") #
    f_Site_Name=models.CharField(max_length=255, blank=True, null=True, default="") #
    f_Referral_Date=models.DateField(null=True, blank=True)
    #Patient Information
    f_Patient_ID=models.CharField(max_length=255, blank=True, null=True)
    f_First_Name=models.CharField(max_length=255, blank=True, null=True, default="")
    f_Mid_Name=models.CharField(max_length=255, blank=True, null=True, default="")
    f_Last_Name = models.CharField(max_length=255, blank=True, null=True, default="")
    f_Date_Birth = models.DateField(null=True, blank=True)
    f_Age = models.CharField(max_length=255, blank=True, null=True, default="")
    f_Sex = models.CharField(max_length=255, blank=True, null=True, default="")
    f_Date_Admis = models.DateField(null=True, blank=True)
    f_Nosocomial = models.CharField(max_length=255, choices=f_Common_Choices, default="n/a")
    f_Diagnosis = models.CharField(max_length=255, blank=True, null=True, default="")
    f_Diagnosis_ICD10 = models.CharField(max_length=255, blank=True, null=True, default="")
    f_Ward = models.CharField(max_length=255, blank=True, null=True, default="")
    f_Ward_Type = models.CharField(max_length=255, blank=True, null=True, default="")
    f_Service_Type = models.CharField(max_length=255, choices=f_ServiceTypeChoice, default="n/a")

    #Isolate Information
    f_Spec_Num=models.CharField(max_length=255, blank=True, null=True, default="")
    f_Spec_Date = models.DateField(null=True, blank=True)
    f_Spec_Type = models.CharField(max_length=255, blank=True, null=True, default="")
    f_Reason = models.TextField(max_length=255, choices=f_ReasonChoices, default="n/a")
    f_Growth = models.CharField(max_length=255, blank=True, null=True, default="")
    f_Urine_ColCt = models.CharField(max_length=255, blank=True, null=True, default="")

    # Phenotypic Results
    f_ampC = models.CharField(max_length=255, choices=f_Common_pheno, default="n/a")
    f_ESBL = models.CharField(max_length=255, choices=f_Common_pheno, default="n/a")
    f_CARB = models.CharField(max_length=255, choices=f_Common_pheno, default="n/a")
    f_MBL = models.CharField(max_length=255, choices=f_Common_pheno, default="n/a")
    f_BL = models.CharField(max_length=255, choices=f_Common_pheno, default="n/a")
    f_MR = models.CharField(max_length=255, choices=f_Common_pheno, default="n/a")
    f_mecA = models.CharField(max_length=255, choices=f_Common_pheno, default="n/a")
    f_ICR = models.CharField(max_length=255, choices=f_Common_pheno, default="n/a")
    f_OtherResMech = models.CharField(max_length=255, blank=True, null=True, default="")

    # Organism Result
    f_Site_Pre = models.CharField(max_length=255, blank=True, null=True, default="")
    f_Site_Org = models.CharField(max_length=255, blank=True, null=True, default="")
    f_Site_Pos = models.CharField(max_length=255, blank=True, null=True, default="")
    f_OrganismCode = models.CharField(max_length=255, blank=True, null=True, default="")
    f_Comments = models.TextField(blank=True, null=True, default="")

    # ARSRL Sty Results
    f_ars_ampC = models.CharField(max_length=255, choices=f_Common_pheno, default="n/a")
    f_ars_ESBL = models.CharField(max_length=255, choices=f_Common_pheno, default="n/a")
    f_ars_CARB = models.CharField(max_length=255, choices=f_Common_pheno, default="n/a")
    f_ars_ECIM = models.CharField(max_length=255, choices=f_Common_pheno, default="n/a")
    f_ars_MCIM = models.CharField(max_length=255, choices=f_Common_pheno, default="n/a")
    f_ars_EC_MCIM = models.CharField(max_length=255, choices=f_Common_pheno, default="n/a")
    f_ars_MBL = models.CharField(max_length=255, choices=f_Common_pheno, default="n/a")
    f_ars_BL = models.CharField(max_length=255, choices=f_Common_pheno, default="n/a")
    f_ars_MR = models.CharField(max_length=255, choices=f_Common_pheno, default="n/a")
    f_ars_mecA = models.CharField(max_length=255, choices=f_Common_pheno, default="n/a")
    f_ars_ICR = models.CharField(max_length=255, choices=f_Common_pheno, default="n/a")
    f_ars_Pre = models.CharField(max_length=255, blank=True, null=True, default="")
    f_ars_Post = models.CharField(max_length=255, blank=True, null=True, default="")
    f_ars_OrgCode = models.CharField(max_length=255, blank=True, null=True, default="")
    f_ars_OrgName = models.CharField(max_length=255, blank=True, null=True, default="")
    f_ars_ct_ctl = models.CharField(max_length=255, blank=True, null=True, default="")
    f_ars_tz_tzl = models.CharField(max_length=255, blank=True, null=True, default="")
    f_ars_cn_cni = models.CharField(max_length=255, blank=True, null=True, default="")
    f_ars_ip_ipi = models.CharField(max_length=255, blank=True, null=True, default="")
    f_ars_reco_Code = models.CharField(max_length=255, blank=True, null=True, default="")
    f_ars_reco = models.TextField(blank=True, null=True, default="")

    # Batch Table Data
    f_SiteName = models.CharField(max_length=255, blank=True, null=True, default="")
    f_Month_Date = models.DateField(null=True, blank=True)
    f_Day_Date = models.DateField(null=True, blank=True)
    f_Year_Date = models.DateField(null=True, blank=True)
    f_RefDate = models.DateField(null=True, blank=True)
    f_Start_AccNo = models.IntegerField(null=True, blank=True)
    f_End_AccNo = models.IntegerField(null=True, blank=True)
    f_No_Isolates = models.IntegerField(null=True, blank=True)
    f_Encoded_by = models.CharField(max_length=255, blank=True)
    f_Encoded_by_Initials = models.CharField(max_length=255, blank=True)
    f_Edited_by = models.CharField(max_length=255, blank=True)
    f_Edited_by_Initials = models.CharField(max_length=255, blank=True)
    f_Checked_by = models.CharField(max_length=255, blank=True)
    f_Checked_by_Initials = models.CharField(max_length=255, blank=True)
    f_Verified_by_Senior = models.CharField(max_length=255, blank=True)
    f_Verified_by_Senior_Initials = models.CharField(max_length=255, blank=True)
    f_Verified_by_LabManager = models.CharField(max_length=255, blank=True)
    f_Verified_by_LabManager_Initials = models.CharField(max_length=255, blank=True)
    f_Noted_by = models.CharField(max_length=255, blank=True)
    f_Noted_by_Initials = models.CharField(max_length=255, blank=True)
    f_Concordance_Check = models.CharField(max_length=255, blank=True)
    f_Concordance_by = models.CharField(max_length=255, blank=True)
    f_Concordance_by_Initials = models.CharField(max_length=255, blank=True)
    f_abx_code = models.CharField(max_length=25, blank=True, default="")


    f_x_mrse = models.CharField(max_length=255, blank=True, null=True, default="")
    f_x_mrsamrse = models.CharField(max_length=255, blank=True, null=True, default="")
    f_x_entbac = models.CharField(max_length=255, blank=True, null=True, default="")
    f_edta = models.CharField(max_length=255, blank=True, null=True, default="")

    def __str__(self):
        return self.f_AccessionNo
    
    
    class Meta:
        db_table ="Final_Data"

class FinalData_upload(models.Model):
    FinalDataFile = models.FileField(upload_to='uploads/final/', null=True, blank=True)

    class Meta:
        db_table ="FinalData_upload"




#for final antibiotic test entries
class Final_AntibioticEntry(models.Model):
#  links to main and breakpoints table
    ab_idNum_f_referred = models.ForeignKey(Final_Data, on_delete=models.CASCADE, null=True, related_name='final_entries', to_field='f_AccessionNo')
    ab_AccessionNo= models.CharField(max_length=100, blank=True, null=True)
    ab_RefNo = models.CharField(max_length=100, blank=True, null=True)
    ab_breakpoints_id = models.ManyToManyField('home.BreakpointsTable', max_length=6)
    
    ab_Antibiotic = models.CharField(max_length=100, blank=True, null=True)
    ab_Abx_code= models.CharField(max_length=100, blank=True, null=True)
    ab_Abx=models.CharField(max_length=100, blank=True, null=True)

    #sentinel site results
    ab_Disk_value = models.IntegerField(blank=True, null=True)
    ab_Disk_RIS = models.CharField(max_length=4, blank=True) 
    ab_Disk_enRIS = models.CharField(max_length=4, blank=True, default='') 
    
    ab_MIC_operand=models.CharField(max_length=4, blank=True, null=True, default='')
    ab_MIC_value = models.DecimalField(max_digits=5, decimal_places=3, blank=True, null=True)
    ab_MIC_RIS = models.CharField(max_length=4, blank=True)
    ab_MIC_enRIS = models.CharField(max_length=4, blank=True, default='')
    
    ab_AlertMIC = models.BooleanField(default=False)
    ab_Alert_val = models.CharField(max_length=30, blank=True, null=True, default='')

    ab_R_breakpoint = models.CharField(max_length=10, blank=True, null=True)
    ab_I_breakpoint = models.CharField(max_length=10, blank=True, null=True)
    ab_SDD_breakpoint = models.CharField(max_length=10, blank=True, null=True)  
    ab_S_breakpoint = models.CharField(max_length=10, blank=True, null=True)
    
    #arsrl results
    ab_Retest_Antibiotic = models.CharField(max_length=100, blank=True, null=True)
    ab_Retest_Abx_code = models.CharField(max_length=100, blank=True, null=True)
    ab_Retest_Abx = models.CharField(max_length=100, blank=True, null=True)
    
    ab_Retest_DiskValue = models.IntegerField(blank=True, null=True)
    ab_Retest_Disk_RIS = models.CharField(max_length=4, blank=True)
    ab_Retest_Disk_enRIS = models.CharField(max_length=4, blank=True, default='')
    
    ab_Retest_MIC_operand=models.CharField(max_length=4, blank=True, null=True, default='')
    ab_Retest_MICValue = models.DecimalField(max_digits=5, decimal_places=3, blank=True, null=True)
    ab_Retest_MIC_RIS = models.CharField(max_length=4, blank=True)
    ab_Retest_MIC_enRIS = models.CharField(max_length=4, blank=True, default='')    
    
    ab_Retest_AlertMIC = models.BooleanField(default=False)
    ab_Retest_Alert_val = models.CharField(max_length=30, blank=True, null=True, default='')
    ab_Ret_R_breakpoint = models.CharField(max_length=10, blank=True, null=True)
    ab_Ret_I_breakpoint = models.CharField(max_length=10, blank=True, null=True)
    ab_Ret_SDD_breakpoint = models.CharField(max_length=10, blank=True, null=True)
    ab_Ret_S_breakpoint = models.CharField(max_length=10, blank=True, null=True)    

    ab_MICJoined = models.CharField(max_length=7, blank=True, null=True)
    def __str__(self):
        return ", ".join([abx.Whonet_Abx for abx in self.ab_breakpoints_id.all()]) 

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Save the instance first
        

    class Meta:
        db_table = "FinalAntibioticEntry"