from datetime import timezone
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.validators import EmailValidator
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import User

# Create your models here.


class Batch_Table(models.Model):

    Batch_Status = (
        ('n/a',''),
        ('Encoding','Encoding'),
        ('First Draft', '1st Draft'),
        ('Second Draft', '2nd Draft'),
        ('Third Draft', '3rd Draft'),
        ('Verification','Verification'),
        ('Other','Other'),
    )

    bat_SiteCode = models.CharField(max_length=255, blank=True, default='')
    bat_Seq_No = models.IntegerField(null=True, blank=True)
    bat_Site_Name = models.CharField(max_length=255, blank=True)
    bat_Site_NameGen = models.CharField(max_length=255, blank=True)
    bat_Batch_Name = models.CharField(max_length=255, blank=True)
    bat_Batch_Code = models.CharField(max_length=255, blank=True)

    bat_Date_of_Entry = models.DateTimeField(auto_now_add=True)
    bat_RefNo = models.CharField(null=True, blank=True)
    bat_BatchNo = models.CharField(max_length=255, blank=True)
    bat_Total_batch = models.CharField(max_length=100, blank=True)
    bat_AccessionNo = models.CharField(max_length=255, blank=True)
    bat_AccessionNoGen = models.CharField(max_length=100, blank=True)
    bat_Default_Year = models.DateField(null=True, blank=True)
    bat_Referral_Date = models.DateField(null=True, blank=True)

    bat_Status = models.CharField(max_length=100, choices=Batch_Status, default='')

    bat_Encoder = models.CharField(max_length=255, blank=True, default='')
    bat_Enc_Lic = models.CharField(max_length=100, blank=True, default='')

    bat_Checker = models.CharField(max_length=255, blank=True, default='')
    bat_Chec_Lic = models.CharField(max_length=100, blank=True, default='')

    bat_Verifier = models.CharField(max_length=255, blank=True, default='')
    bat_Ver_Lic = models.CharField(max_length=100, blank=True, default='')

    bat_LabManager = models.CharField(max_length=255, blank=True, default='')
    bat_Lab_Lic = models.CharField(max_length=100, blank=True, default='')

    bat_Head = models.CharField(max_length=255, blank=True, default='')
    bat_Head_Lic = models.CharField(max_length=100, blank=True, default='')

    bat_Date_Encoded = models.DateField(null=True, blank=True)
    bat_Date_Checked = models.DateField(null=True, blank=True)
    bat_Date_Verified = models.DateField(null=True, blank=True)
    bat_Date_LabManager = models.DateField(null=True, blank=True)
    bat_Date_Head = models.DateField(null=True, blank=True)

    bat_Date_Accomplished = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "Batch_Table"


    def save(self, *args, **kwargs):

        today = timezone.now().date()

        # Encoder
        if self.bat_Encoder and not self.bat_Date_Encoded:
            self.bat_Date_Encoded = today

        # Checker
        if self.bat_Checker and not self.bat_Date_Checked:
            self.bat_Date_Checked = today

        # Verifier
        if self.bat_Verifier and not self.bat_Date_Verified:
            self.bat_Date_Verified = today

        # Lab Manager
        if self.bat_LabManager and not self.bat_Date_LabManager:
            self.bat_Date_LabManager = today

        # Head
        if self.bat_Head and not self.bat_Date_Head:
            self.bat_Date_Head = today

        super().save(*args, **kwargs)



        def __init__(self, *args, **kwargs):
                editing = kwargs.pop("editing", False)
                super().__init__(*args, **kwargs)

                if editing:
                    LOCKED_FIELDS = [
                        "bat_SiteCode",
                        "bat_Referral_Date",
                        "bat_BatchNo",
                        "bat_Total_batch",
                        "bat_RefNo",
                        "bat_Site_NameGen",
                        "bat_Batch_Name",
                    ]

                    for field in LOCKED_FIELDS:
                        self.fields[field].disabled = True


class Referred_Data(models.Model):
    Common_Choices = (
        ('n/a','n/a'),
        ('Yes', 'Yes'),
        ('No', 'No'),
    )

    Common_pheno = (
        ('n/a','n/a'),
        ('(+)','(+)'),
        ('(-)', '(-)'),
        ('NT', 'NT'),
    )
    SexatbirthChoice=(
        ('n/a','n/a'),
        ('Male', 'Male'),
        ('Female', 'Female')
    )

    ServiceTypeChoice=(
        ('n/a','n/a'),
        ('In','In'),
        ('Out','Out')
        
    )
    ReasonChoices=(
        ('n/a','n/a'),
        ('a & d','a & d'),
        ('confirmation of org and ast','a'),
        ('for ast only','b'),
        ('difficult to ID','c'),
        ('for serotyping','d'),
        ('for research','e'),
        ('Others','o')
    )

    Status_Choice = (
        ('n/a','n/a'),
        ('Encoding','Encoding'),
        ('First Draft', '1st Draft'),
        ('Second Draft', '2nd Draft'),
        ('Third Draft', '3rd Draft'),
        ('Verification','Verification'),
        ('Other','Other'),

    )

    Growth_Choice = (
        ('n/a','n/a'),
        ('light growth','light growth'),
        ('light to moderate growth','light to moderate growth'),
        ('heavy growth', 'heavy growth'),
        ('moderately heavy growth', 'moderately heavy growth'),
        ('positive growth', 'positive growth'),
        ('no growth','no growth'),


    )
   
    Gender_Choice = (
        ('n/a','n/a'),
        ('f','f'),
        ('m','m'),
     
    )
   
   
    #isolates
    bat_seq = models.PositiveIntegerField(null=True, blank=True, help_text="Auto sequence number per batch")
    Batch_id = models.ForeignKey(Batch_Table, on_delete=models.CASCADE, related_name='Batch_isolates', null=True,)
    Hide=models.BooleanField(default=False)
    Copy_data=models.BooleanField(default=False)
    Batch_Name=models.CharField(max_length=255, blank=True,)
    Batch_Code = models.CharField(max_length=255, blank=True)
    Date_of_Entry =models.DateTimeField(auto_now_add=True)
    Date_Modified =models.DateTimeField(auto_now=True)
    RefNo = models.CharField(max_length=20, blank=True, null=True)
    BatchNo=models.CharField(max_length=255, blank=True,)
    Total_batch=models.CharField(max_length=100, blank=True,)
    AccessionNo=models.CharField(max_length=255, blank=True, unique=True)
    AccessionNoGen=models.CharField(max_length=100, blank=True)
    Default_Year=models.DateField(null=True, blank=True)
    SiteCode=models.CharField(max_length=255, blank=True,) #
    Site_Name=models.CharField(max_length=255, blank=True,) #
    # Site_NameGen = models.CharField(max_length=255, blank=True,) #
    Referral_Date=models.DateField(null=True, blank=True)
    #Patient Information
    Patient_ID=models.CharField(max_length=255, blank=True,)
    First_Name=models.CharField(max_length=255, blank=True,)
    Mid_Name=models.CharField(max_length=255, blank=True,)
    Last_Name=models.CharField(max_length=255, blank=True,)
    Date_Birth=models.DateField(null=True, blank=True)
    Age = models.IntegerField(
    blank=True,
    null=True,
    validators=[MinValueValidator(0), MaxValueValidator(120)]
    )
    Sex=models.CharField(max_length=255, blank=True, choices=Gender_Choice, default="n/a")
    Date_Admis=models.DateField(null=True, blank=True)
    Nosocomial=models.CharField(max_length=255, choices=Common_Choices, default="n/a")
    Diagnosis=models.CharField(max_length=255, blank=True,)
    Diagnosis_ICD10=models.CharField(max_length=255, blank=True,)
    Ward=models.CharField(max_length=255, blank=True,)
    Ward_Type = models.CharField(max_length=255, blank=True,)
    Service_Type=models.CharField(max_length=255, choices=ServiceTypeChoice, default="n/a")
    #Isolate Information
    Spec_Num=models.CharField(max_length=255, blank=True,)
    Spec_Date=models.DateField(null=True, blank=True)
    # Spec_Type=models.CharField(max_length=255, blank=True, null=True)
    Spec_Type = models.ForeignKey("SpecimenTypeModel", on_delete=models.SET_NULL, null=True,blank=True, related_name='specimen_type_entries')
    Reason=models.TextField(max_length=255, choices=ReasonChoices, default="n/a")
    Growth=models.CharField(max_length=255, blank=True, choices=Growth_Choice, default="n/a")
    Urine_ColCt=models.CharField(max_length=255, blank=True,)
    #Phenotypic Results
    ampC=models.CharField(max_length=255, choices=Common_pheno, default="n/a")
    ESBL=models.CharField(max_length=255, choices=Common_pheno, default="n/a")
    CARB=models.CharField(max_length=255, choices=Common_pheno, default="n/a")
    MBL=models.CharField(max_length=255, choices=Common_pheno, default="n/a")
    BL=models.CharField(max_length=255, choices=Common_pheno, default="n/a")
    MR=models.CharField(max_length=255, choices=Common_pheno, default="n/a")
    mecA=models.CharField(max_length=255, choices=Common_pheno, default="n/a")
    ICR=models.CharField(max_length=255, choices=Common_pheno, default="n/a")
    OtherResMech=models.CharField(max_length=255, blank=True)
    #Organism Result
    Site_Pre=models.CharField(max_length=255, blank=True, default='', null=True)
    Site_Org=models.CharField(max_length=255, blank=True, default="")
    Site_OrgName=models.CharField(max_length=255, blank=True, null=True)
    Site_Pos=models.CharField(max_length=255, blank=True, null=True, default="")
    Comments=models.TextField(blank=True, null=True)
    
    #ARSRL Sty Results
    ars_ampC=models.CharField(max_length=255, choices=Common_pheno, default="n/a")
    ars_ESBL=models.CharField(max_length=255, choices=Common_pheno, default="n/a")
    ars_CARB=models.CharField(max_length=255, choices=Common_pheno, default="n/a")
    ars_ECIM=models.CharField(max_length=255, choices=Common_pheno, default="n/a")
    ars_MCIM=models.CharField(max_length=255, choices=Common_pheno, default="n/a")
    ars_EC_MCIM=models.CharField(max_length=255, choices=Common_pheno, default="n/a")
    ars_MBL=models.CharField(max_length=255, choices=Common_pheno, default="n/a")
    ars_BL=models.CharField(max_length=255, choices=Common_pheno, default="n/a")
    ars_MR=models.CharField(max_length=255, choices=Common_pheno, default="n/a")
    ars_mecA=models.CharField(max_length=255, choices=Common_pheno, default="n/a")
    ars_ICR=models.CharField(max_length=255, choices=Common_pheno, default="n/a")
    ars_Pre=models.CharField( max_length=255, blank=True, default="", null=True)
    ars_Post=models.CharField(max_length=255, blank=True, default="", null=True)
    ars_OrgCode=models.CharField(max_length=255, blank=True, default="")
    ars_OrgName=models.CharField(max_length=255, blank=True,)
    ars_ct_ctl=models.CharField(max_length=255, blank=True,)
    ars_tz_tzl=models.CharField(max_length=255, blank=True,)
    ars_cn_cni=models.CharField(max_length=255, blank=True,)
    ars_ip_ipi=models.CharField(max_length=255, blank=True,)
    ars_reco_Code=models.CharField(max_length=255, blank=True, null=True)
    ars_description = models.TextField(blank=True, null=True)
    ars_reco=models.TextField(blank=True, null=True, default='')
    
    #Batch Table Data
    SiteName=models.CharField(max_length=255, blank=True,)
    Status = models.CharField(max_length=100, choices=Status_Choice, default="n/a")
    Month_Date=models.DateField(null=True, blank=True)
    Day_Date=models.DateField(null=True, blank=True)
    Year_Date=models.DateField(null=True, blank=True)
    RefDate=models.DateField(null=True, blank=True)
    Start_AccNo=models.IntegerField(null=True, blank=True)
    End_AccNo=models.IntegerField(null=True, blank=True)
    No_Isolates=models.IntegerField(null=True, blank=True)
    Concordance_Check=models.CharField(max_length=255, blank=True,)
    Concordance_by=models.CharField(max_length=255, blank=True,)
    Concordance_by_Initials=models.CharField(max_length=255, blank=True,)
    abx_code=models.CharField(max_length=25, blank=True, default="")

    
    arsp_Encoder = models.CharField(max_length=255, blank=True, null=True, default="")
    arsp_Enc_Lic = models.CharField(max_length=100,blank=True, null=True, default="")
    arsp_Checker = models.CharField(max_length=255, blank=True, null=True, default="") 
    arsp_Chec_Lic = models.CharField(max_length=100,blank=True, null=True, default="")
    arsp_Verifier = models.CharField(max_length=255, blank=True, null=True, default="")
    arsp_Ver_Lic = models.CharField(max_length=100,blank=True, null=True, default="")
    arsp_LabManager = models.CharField(max_length=255, blank=True, null=True, default="")
    arsp_Lab_Lic = models.CharField(max_length=100,blank=True, null=True, default="")
    arsp_Head = models.CharField(max_length=255, blank=True, null=True, default="")
    arsp_Head_Lic = models.CharField(max_length=100,blank=True, null=True, default="")
    Date_Accomplished_ARSP=models.DateField(blank=True, null=True)
    
    x_mrse = models.CharField(max_length=255, blank=True)
    x_mrsamrse = models.CharField(max_length=255, blank=True)
    x_entbac = models.CharField(max_length=255, blank=True)
    edta = models.CharField(max_length=255, blank=True)




    def save(self, *args, **kwargs):
        # Fill defaults to prevent NULL insertion
        self.arsp_Encoder = self.arsp_Encoder or ""
        self.arsp_Enc_Lic = self.arsp_Enc_Lic or ""
        self.arsp_Checker = self.arsp_Checker or ""
        self.arsp_Chec_Lic = self.arsp_Chec_Lic or ""
        self.arsp_Verifier = self.arsp_Verifier or ""
        self.arsp_Ver_Lic = self.arsp_Ver_Lic or ""
        self.arsp_LabManager = self.arsp_LabManager or ""
        self.arsp_Lab_Lic = self.arsp_Lab_Lic or ""
        self.arsp_Head = self.arsp_Head or ""
        self.arsp_Head_Lic = self.arsp_Head_Lic or ""
        self.Site_Org = self.Site_Org or ""
        self.ars_OrgCode = self.ars_OrgCode or ""
        self.Site_OrgName = self.Site_OrgName or ""



        # Normalize Age for IntegerField
        if self.Age in ("", " ", None):
            self.Age = None


        super().save(*args, **kwargs)


    def __str__(self):
        return self.AccessionNo
    
    class Meta:
        db_table ="Referred_Data"
        constraints = [
            models.UniqueConstraint(fields=['AccessionNo', 'Batch_Code'], name='unique_accession_batch'),
            models.UniqueConstraint(fields=["Batch_id", "bat_seq"],name="unique_bat_seq_per_batch")
        
        ]





class ReferredData_upload(models.Model):
    ReferredDataFile = models.FileField(upload_to='uploads/referred/', null=True, blank=True)

    class Meta:
        db_table ="Referred_upload"
  



class TATform(models.Model):
     #Running TAT form
    Batch_Isolates = models.ForeignKey(Referred_Data, on_delete=models.CASCADE, null=True, related_name='tat_entries')
    AccessionNum = models.CharField(max_length=255, blank=True,)
    Unit_DateRec = models.DateField(blank=True, null=True)
    Target_Days = models.CharField(max_length=3, blank=True,)
    Days_Count = models.CharField(max_length=3, blank=True,)
    Running_TAT = models.CharField(max_length=3, blank=True,)
    Num_Isolate = models.CharField(max_length=3, blank=True,)
    Total_Batch = models.CharField(max_length=3, blank=True,)
    ars_Encoder = models.CharField(max_length=255, blank=True,)
    ars_Date_Encoded = models.DateField(blank=True, null=True)
    ars_Checker = models.CharField(max_length=255, blank=True,) 
    ars_Date_Checked = models.DateField(blank=True, null=True)
    ars_Verifier = models.CharField(max_length=255, blank=True,)
    ars_Date_Verified = models.DateField(blank=True, null=True)
    ars_LabManager = models.CharField(max_length=255, blank=True,)
    ars_Date_LabManager = models.DateField(blank=True, null=True)
    ars_Head = models.CharField(max_length=255, blank=True,)
    ars_Date_Head = models.DateField(blank=True, null=True)

    class Meta:
        db_table ="TATform"


class TATprocess(models.Model):
    #Running_TAT upload form
    TAT_Process = models.CharField(max_length=255, blank=True,)
    Unit_code = models.CharField(max_length=3, blank=True,)

    class Meta:
        db_table ="TATprocess"


class TATexclusion(models.Model):
     Date_Excluded = models.DateField(blank=True, null=True)
     Exclusion_Details = models.CharField(max_length=255, blank=True)

     class Meta:
         db_table = "Date_Excluded"

class TATUpload(models.Model):
    file = models.FileField(upload_to='uploads/TAT/', null=True, blank=True)

    class Meta:
        db_table = "TATUpload"



# for specific indexing use this
    # indexes = [
    #             models.Index(fields=['Egasp_Id']),  # Index for field1
    #             models.Index(fields=['Uic_Ptid']),  # Index for field2
    #             models.Index(fields=['First_Name']),  # Index for field3
    #             models.Index(fields=['Last_Name']),  # Index for field4
    #             # add more indexes as needed
    #         ]


class SiteData(models.Model):
    SiteCode=models.CharField(max_length=3, blank=True)
    SiteName=models.CharField(max_length=155, blank=True)
    def __str__(self):
        return self.SiteCode 
    
class Meta:
    db_table ="SiteData"

class SiteCode_upload(models.Model):
    File_uploadSite = models.FileField(upload_to='uploads/site/', null=True, blank=True)

    class Meta:
        db_table = "SiteCode_upload"

class BreakpointsTable(models.Model):
    TestMethodChoices =(
        ('DISK', 'DISK'),
        ('MIC','MIC'),
    )
    
    GuidelineChoices = (
        ('CLSI', 'CLSI'),        
    )
    
    Emerg_Int_Choices = (
        ('','-'),
        ('R','R'),
        ('I', 'I'),
        ('S', 'S'),
        ('NS','NS'),
        ('SDD','SDD'),

    )
    Antibiotic_list = models.ForeignKey(
        'Antibiotic_List',
        on_delete=models.CASCADE,
        related_name='breakpoints',
        to_field='Whonet_Abx',   # this tells Django to link by the Whonet_Abx field
        db_column='Abx_List_Whonet_Abx',  # keeps database column name clear
        null=True,
        blank=True
    )
    Guidelines = models.CharField(max_length=100, choices=GuidelineChoices, blank=True, default='')
    Year = models.CharField(max_length=100, blank=True, default='')
    Org = models.CharField(max_length=100, blank=True, default='')
    Spec_code = models.CharField(max_length=100, blank=True, null=True)
    Emerging_specimen =models.BooleanField(default=False)
    Test_Method = models.CharField(max_length=20, choices=TestMethodChoices, blank=True, default='')
    Potency = models.CharField(max_length=20, blank=True, default='')
    Abx_code = models.CharField(max_length=15, blank=True, default='')
    Tier = models.CharField(max_length=10, blank=True, default='')
    # Show = models.BooleanField(default=True)
    # Retest = models.BooleanField(default=False)

    Emerging_Org_Flag= models.BooleanField(default=False)
    Emerging_Abx_Flag=models.BooleanField(default=False)
    Emerging_Pheno_Flag=models.CharField(max_length=100, blank=True, default="", choices=Emerg_Int_Choices)
    Emerging_Pheno_Flag_Other=models.CharField(max_length=100, blank=True, default="", choices=Emerg_Int_Choices)
    

    Antibiotic = models.CharField(max_length=100, blank=True, default='')
    Whonet_Abx = models.CharField(max_length=100, blank=True, default='')
    Disk_Abx = models.BooleanField(default=False)
    R_val = models.CharField(max_length=30, blank=True, default='')
    I_val = models.CharField(max_length=30, blank=True, default='')
    SDD_val = models.CharField(max_length=30, blank=True, default='')
    S_val = models.CharField(max_length=30, blank=True, default='')
    Alert_val = models.CharField(max_length=30, blank=True, default='')
    Date_Modified = models.DateField(auto_now_add=True)
    def __str__(self):
        return self.Abx_code 

    class Meta:
        db_table ="BreakpointsTable"
        ordering = ["Whonet_Abx"]


class Breakpoint_upload(models.Model):
    File_uploadBP = models.FileField(upload_to='uploads/breakpoints/', null=True, blank=True)

    class Meta:
        db_table = "Breakpoint_upload"

    
#for antibiotic test entries
class AntibioticEntry(models.Model):

#  links to main and breakpoints table
    ab_idNum_referred = models.ForeignKey(Referred_Data, on_delete=models.CASCADE, null=True, related_name='antibiotic_entries', to_field='AccessionNo')
    ab_Site_Org = models.CharField(max_length=100, blank=True, null=True)
    ab_Ret_Org = models.CharField(max_length=100, blank=True, null=True)
    
   

    ab_Disk_Abx = models.BooleanField(default=False)
    ab_Ret_Disk_Abx= models.BooleanField(default=False)
    ab_AccessionNo= models.CharField(max_length=100, blank=True, null=True)
    ab_RefNo = models.CharField(max_length=100, blank=True, null=True)
    ab_breakpoints_id = models.ManyToManyField(BreakpointsTable, max_length=6)
    
    ab_Antibiotic = models.CharField(max_length=100, blank=True, null=True)
    ab_Abx_code= models.CharField(max_length=100, blank=True, null=True)
    ab_Abx=models.CharField(max_length=100, blank=True, null=True)

    #sentinel site results
    ab_Disk_value = models.IntegerField(blank=True, null=True)
    ab_Disk_RIS = models.CharField(max_length=4, blank=True) 
    ab_Disk_enRIS = models.CharField(max_length=4, blank=True, default='') 


    ab_MIC_operand=models.CharField(max_length=4, blank=True, null=True, default='')
    ab_MIC_value = models.DecimalField(max_digits=7, decimal_places=3, blank=True, null=True)
    ab_MIC_RIS = models.CharField(max_length=4, blank=True)
    ab_MIC_enRIS = models.CharField(max_length=4, blank=True, default='')
    
    ab_AlertMIC = models.BooleanField(default=False)
    ab_Alert_val = models.CharField(max_length=30, blank=True, null=True, default='')

    ab_R_breakpoint = models.CharField(max_length=10, blank=True, null=True)
    ab_I_breakpoint = models.CharField(max_length=10, blank=True, null=True)
    ab_SDD_breakpoint = models.CharField(max_length=10, blank=True, null=True)  
    ab_S_breakpoint = models.CharField(max_length=10, blank=True, null=True)
    
    #arsrl results
     #### this will apply on retest only
    ab_Org_Flag = models.BooleanField(default=False)
    ab_Abx_Flag = models.BooleanField(default=False)
    ab_Abx_Phenotype = models.CharField(max_length=100, blank=True, null=True)
    ab_Abx_Phenotype_Other = models.CharField(max_length=100, blank=True, null=True)

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
        if self.ab_Disk_enRIS:
            self.ab_Disk_enRIS = self.ab_Disk_enRIS.upper()

        if self.ab_MIC_enRIS:
            self.ab_MIC_enRIS = self.ab_MIC_enRIS.upper()
        
        if self.ab_Retest_Disk_enRIS:
            self.ab_Retest_Disk_enRIS = self.ab_Retest_Disk_enRIS.upper()

        if self.ab_Retest_MIC_enRIS:
            self.ab_Retest_MIC_enRIS = self.ab_Retest_MIC_enRIS.upper()

        super().save(*args, **kwargs)  # Save the instance first
        

    class Meta:
        db_table = "AntibioticEntry"




class SpecimenTypeModel(models.Model):
    Emerging_Spec_Flag= models.BooleanField(default=False)
    Specimen_code = models.CharField(max_length=4, unique=True, db_index=True, blank=True, null=True)
    Specimen_name = models.CharField(max_length=100, blank=True, null=True)
    Specimen_Code_Grp = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True)
    Specimen_Grp_Name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        # Always return a string; prefer Specimen_code, fallback to placeholder
        return str(self.Specimen_code) or "n/a"
    
    class Meta:
        db_table = "SpecimenTypeTable"


class Specimen_upload(models.Model):
    File_uploadSpec = models.FileField(upload_to='uploads/specimen/', null=True, blank=True)

    class Meta:
        db_table = "Specimen_upload"



#Address Book
class arsStaff_Details(models.Model):
    Staff_Name = models.CharField(max_length=100, blank=True, null=True)
    Staff_Designation= models.CharField(max_length=100, blank=True, null=True)
    Staff_Telnum= PhoneNumberField(blank=True, region="PH", null=True)
    Staff_EmailAdd = models.EmailField(max_length=100, blank=True, null=True)
    Staff_License = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.Staff_Name if self.Staff_Name else "Unnamed Staff"

class Recommendation(models.Model):
    Reco_Code = models.CharField(max_length=100, blank=True, null=True)
    Reco_Details = models.TextField(blank=True, null=True)

    def __str__(self):
            return self.Reco_Code 
    

class FieldMapping(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    raw_field = models.CharField(max_length=255)
    mapped_field = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    class Meta:
        unique_together = ('user', 'raw_field')

    def __str__(self):
        return f"{self.user.username}: {self.raw_field} → {self.mapped_field}"


class Antibiotic_List(models.Model):
    TestMethodChoices =(
        ('DISK', 'DISK'),
        ('MIC','MIC'),
    )
    
    GuidelineChoices = (
        ('CLSI', 'CLSI'),        
    )
    Show=models.BooleanField(default=True) #Show in Sentinel Antibiotiocs in data entry
    Retest=models.BooleanField(default=True) # Show in Retest antibiotics in data entry
    Show_Site=models.BooleanField(default=True) # Show in Sentinel Result
    Show_Ars = models.BooleanField(default=True) # Show in ARSRL Result
    Show_Value=models.BooleanField(default=True) # Show Value Column
    Disk_Abx=models.BooleanField(default=True)
    Tier = models.CharField(max_length=10, blank=True, default='')
    Test_Method=models.CharField(max_length=100, choices=TestMethodChoices, blank=True, default="")
    Abx_code=models.CharField(max_length=100, blank=True, default="",)
    Whonet_Abx=models.CharField(max_length=100, blank=True, default="", unique=True)
    Antibiotic=models.CharField(max_length=100, blank=True, default="")
    Guidelines=models.CharField(max_length=100, choices=GuidelineChoices, blank=True, default="")
    Potency=models.CharField(max_length=100, blank=True, default="")
    Class=models.CharField(max_length=100, blank=True, default="")
    Subclass=models.CharField(max_length=100, blank=True, default="")
    Date_Modified=models.DateField(auto_now_add=True, null=True)

    class Meta:
        db_table = "Antibiotic_List"

    def __str__(self):
        return f"{self.Whonet_Abx}"


class Antibiotic_upload(models.Model):
    File_uploadAbx = models.FileField(upload_to='uploads/breakpoints/', null=True, blank=True)

    class Meta:
        db_table = "Antibiotic_upload"


class Organism_List(models.Model):
    Whonet_Org_Code= models.CharField(max_length=20, unique=True)
    Replaced_by = models.CharField(max_length=20, null=True, blank=True)
    Organism = models.CharField(max_length=255)
    Organism_Type = models.CharField(max_length=5, null=True, blank=True)
    Family_Code = models.CharField(max_length=20, null=True, blank=True)
    Genus_Group = models.CharField(max_length=50, null=True, blank=True)
    Genus_Code = models.CharField(max_length=20, null=True, blank=True)
    Species_Group = models.CharField(max_length=50, null=True, blank=True)
    Serovar_Group = models.CharField(max_length=50, null=True, blank=True)
    Kingdom = models.CharField(max_length=100, null=True, blank=True)
    Phylum = models.CharField(max_length=100, null=True, blank=True)
    Class = models.CharField(max_length=100, null=True, blank=True)
    Order = models.CharField(max_length=100, null=True, blank=True)
    Family= models.CharField(max_length=100, null=True, blank=True)
    Genus = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.Whonet_Org_Code}"


class Organism_upload(models.Model):
    File_uploadOrg = models.FileField(upload_to='uploads/organism/', null=True, blank=True)

    class Meta:
        db_table = "Organism_upload"






class Emerging_Filter_Age(models.Model):

    Eme_Age=models.IntegerField(blank=True, null=True)
    class Meta:
        db_table = "Emerging_Filter_Age"
    
    def __str__(self):
        return str(self.Eme_Age)

class Emerging_Crit_upload(models.Model):
    File_uploadEme = models.FileField(upload_to='uploads/emerging/', null=True, blank=True)

    class Meta:
        db_table = "Emerging_upload"



class Phenotype_Pre(models.Model):
    Pre_Phenotypes = models.CharField(max_length=255, blank=True, null=True)


    class Meta:
        db_table = "Phenotype_Pre"

    
    def __str__(self):
        return f"{self.Pre_Phenotypes}"

class Pheno_upload_Pre(models.Model):
    File_Pheno_pre = models.FileField(upload_to='uploads/pheno_pre/', null=True, blank=True)


class Phenotype_Post(models.Model):
    Post_Phenotypes = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "Phenotype_Post"

    def __str__(self):
        return self.Post_Phenotypes or ""


class Pheno_upload_Post(models.Model):
    File_Pheno_post = models.FileField(
        upload_to='uploads/pheno_post/',
        null=True,
        blank=True
    )

    class Meta:
        db_table = "Pheno_upload_Post"


class Recommendation_items(models.Model):
    RecoCode = models.CharField(max_length=100, blank=True, null=True)
    Description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "Recommendation_items"
    
    def __str__(self):
        return f"{self.RecoCode}" or ""

class Reco_item_upload(models.Model):
    File_reco_desc = models.FileField(upload_to='uploads/reco_desc/', null=True, blank=True)
