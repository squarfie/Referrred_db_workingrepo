from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import EmailValidator


# Create your models here.
#For province and Cities

class Province(models.Model):
    provincename = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.provincename

class City(models.Model):
    cityname = models.CharField(max_length=100)
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name="cities")

    def __str__(self):
        return f"{self.cityname} ({self.province.provincename})"

# Model for Province File Upload
class LocationUpload(models.Model):
    file = models.FileField(upload_to='uploads/locations/', null=True, blank=True)

    class Meta:
        db_table = "LocationUpload"


####   Clinical Data TAB
class Egasp_Data(models.Model):
    Common_Choices = (
        ('Yes', 'Yes'),
        ('No', 'No'),
        ('No Answer', 'No Answer')
    )
    SpeciesChoices =(
        ('ngo', 'Neisseria gonorrhoeae'),
        ('nngi','No Neisseria gonorrhoeae isolated'),
        ('Other','Other'))
    ConsultTypeChoices =(
        ('Initial Visit', 'Initial Visit'),
        ('Follow Up', 'Follow-up'),
        ('No Answer', 'No Answer'))
    ClientTypeChoice =(
        ('Referral', 'Referral'),
        ('Walk-in', 'Walk-in'),
        ('No Answer', 'No Answer'))
    SexatbirthChoice=(
        ('Male', 'Male'),
        ('Female', 'Female')
    )
    GenderChoice=(
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Transgender Male', 'Transgender Male'),
        ('Transgender Female', 'Transgender Female'),
        ('Unknown', 'Unknown')
    )
    Civil_StatusChoice=(
        ('Single', 'Single'),
        ('Married', 'Married'),
        ('Live-in Partner', 'Live-in Partner'),
        ('No Answer', 'No Answer')
    )
    Nationality_Choice=(
        ('Filipino', 'Filipino'),
        ('No Answer', 'No Answer'))
    
    TravelHistory_Choice=(
        ('Within Country', 'Within the Country'),
        ('Outside Country', 'Outside the Country'),
        ('Both','Both'),
        ('No Travel','No Travel History')
    )
    Client_Risk_Choice=(
        ('MSM', 'MSM'),
        ('Transgender','Transgender'),
        ('Heterosexual','Heterosexual'),
        ('PWID', 'PWID'),
        ('POL', 'POL'),
        ('OFW/Partner of OFW', 'OFW/Partner of OFW'),
        ('Female Partner of MSIM or PWID', 'Female Partner of MSIM of PWID' ),
        ('Registered Sex Worker', 'Registered Sex Worker'),
        ('Freelance Sex Worker', 'Freelance Sex Worker'),
        ('General Population', 'General Population')
    )
    Sex_PartnerChoice=(
        ('with Both sex','with Both sex'),
        ('with Male', 'with Male'),
        ('with Female', 'with Female'),
        ('Unknown', 'Unknown')
    )

    NationalityofPartner_Choice=(
        ('Filipino', 'Filipino'),
        ('Filipino and', 'Filipino and'),
        ('No Answer', 'No Answer'),
    )
    Relationship_to_partnerChoice=(
        ('Spouse/live-in partner', 'Spouse/live-in partner'),
        ('Regular non-spouse', 'Regular non-spouse'),
        ('Casual', 'Casual')
    )
    Illicit_Drug_Use_Choices=(
        ('Drug Use, Current', 'Drug Use, Current'),
        ('Drug Use, past 30 days', 'Drug Use, >past(30 days)'),
        ('No Drug Use', 'No Drug Use'),
        ('No Answer', 'No Answer')
    )
    Symp_Gonorrhoea_Choice=(
        ('Yes with Discharge and/or pain', 'Yes with Discharge and/or pain'),
        ('No discharge nor pain', 'No discharge nor pain'),
        ('No answer', 'No answer')
        )
    Outcome_Followup_Choice=(
        ('Returned to Clinic with Symptoms', 'Returned to Clinic with Symptoms'),
        ('Returned to Clinic without Symptoms', 'Returned to Clinic without Symptoms' ),
        ('No follow-up visit', "No follow-up visit"),
        ('No follow-up visit(Foreigner)', "No follow-up visit(Foreigner)"),
        ('No Answer', 'No Answer')
                             )
    Result_TestCure_Choice=(
        ('Positive','Positive'),
        ('Negative','Negative'),
        ('No TOC Performed', 'No TOC Performed'),
        ('No Answer', 'No Answer')
    )
    NoTOC_ResultofTest=(
        ('Positive', 'Positive'),
        ('Negative', 'Negative'),
        ('No Answer', 'No Answer')
                       )
    Gonnorhea_Treatment_Choice=(
        ('Medications Prescribed and Provided by Clinic', 'Medications Prescribed and Provided by Clinic'),
        ('Prescribed Medications Only','Prescribed Medications Only' ),
        ('Referred to physician', 'Referred to physician'),
        ('None given', 'None given'),
        ('No Answer', 'No Answer')
    )
    Treatment_Outcome_Choice=(
        ('Treatment Completed', 'Treatment Completed'),
        ('Partial Treatment Completed','Partial Treatment Completed'),
        ('No Treatment-patient refused', 'No Treatment-patient refused'),
        ('No Treatment-patient didnt come back', 'No Treatment-patient didnt come back' ),
        ('No Answer', 'No Answer')
    )
    Primary_Antibiotics=(
        ('None', 'None'),
        ('CRO 250mg', 'Ceftriaxone 250mg'),
        ('CRO 500mg', 'Ceftriaxone 500mg'),
        ('CRO 1g', 'Ceftriaxone 1g'),
        ('CFM 400mg','Cefixime 400mg'),
        ('CFM 800mg', 'Cefixime 800mg'),
        ('AZM 1g', 'Azithromycin 1g'),
        ('AZM 2g', 'Azithromycin 2g'),
        ('Unknown', 'Unknown')
    )
    Secondary_Antibiotics=(
        ('None','None'),
        ('AZM 1g','Azithromycin 1g' ),
        ('AZM 2g', 'Azithromycin 2g'),
        ('DOX 100mg', 'Doxycycline 100mg'),
        ('TCY 500mg', 'Tetracycline 500mg'),
        ('Unknown', 'Unknown')
    )

    OtherDrugsRoute_Choices=(
        ('Oral', 'Oral'),
        ('Injectable(IV/IM)',"Injectable(IV/IM)"),
        ('Dermal','Dermal'),
        ('Suppository', 'Suppository'),
        ('No Answer', 'No Answer'),
        ('Not Applicable', 'Not Applicable')
    )
    Pus_cellsChoice=(
        ('Negative','Negative'),
        ('Rare','Rare'),
        ('1+','1+'),
        ('2+','2+'),
        ('3+','3+'),
        ('4+','4+'),
    )
    Sp_TypeChoice=(
        ('Genital Male Urethral','Genital Male Urethral'),
        ('Female Cervical','Female Cervical'),
        ('Pharynx','Pharynx'),
        ('Rectum','Other'),

    )
    Sp_QualChoice=(
        ('Acceptable','Acceptable'),
        ('Contaminated','Contaminated'),
        ('Non-viable','Non-viable'),
        ('Improperly Transported','Improperly Transported'),
    )
    Diagnosis_Choice=(
        ('Gonococcal Infection','Gonococcal Infection'),
        ('Non-Gonococcal Infection','Non-Gonococcal Infection'),
        ('Other','Other'),
        ('No Answer','No Answer'),
    )
    CultureResult_Choice=(
        ('Positive','Positive'),
        ('Negative','Negative'),
    )
    OtherInfo_Choice=(
        ('Positive','+'),
        ('Negative','-'),
        ('Not Tested','NT'),
        ('No Answer','NA'),
    )
    
    Country_Choice=(
        ('Philippines','Philippines'),
    )
    # DEMOGRAPHIC DATA
    Date_of_Entry =models.DateTimeField(auto_now_add=True)
    ID_Number = models.CharField(max_length=100, blank=True,)
    Egasp_Id = models.CharField(max_length=25,blank=True,  )
    PTIDCode = models.CharField(max_length=100, blank=True)
    Laboratory = models.CharField(max_length=100,blank=True,)
    Clinic = models.CharField(max_length=100,blank=True,)
    Consult_Date = models.DateField(blank=True, null=True)
    Consult_Type = models.CharField(max_length=100,blank=True, choices=ConsultTypeChoices)
    Client_Type = models.CharField(max_length=100,blank=True, choices=ClientTypeChoice)
    Uic_Ptid = models.CharField(max_length=100,blank=True,)
    Clinic_Code = models.CharField(max_length=100,blank=True,)
    ClinicCodeGen = models.CharField(max_length=100, blank=True)
    First_Name = models.CharField(max_length=100,blank=True,)
    Middle_Name = models.CharField(max_length=100,blank=True,)
    Last_Name = models.CharField(max_length=100,blank=True,)
    Suffix = models.CharField(max_length=100,blank=True,)
    Birthdate = models.DateField(null=True, blank=True)
    Age = models.CharField(max_length=100,blank=True,)
    Sex = models.CharField(max_length=100,blank=True,choices=SexatbirthChoice)
    Gender_Identity = models.CharField(max_length=100,blank=True, choices=GenderChoice)
    Gender_Identity_Other = models.CharField(max_length=100,blank=True,)
    Occupation = models.CharField(max_length=100, blank=True)
    Civil_Status = models.CharField(max_length=100, blank=True, choices=Civil_StatusChoice)
    Civil_Status_Other = models.CharField(max_length=100, blank=True)
    Current_Province = models.CharField(max_length=100, blank=True, null=True)
    Current_City = models.CharField(max_length=100, blank=True, null=True)
    Current_Country =models.CharField(max_length=100, blank=True, choices=Country_Choice, default='Philippines')
    Permanent_Province = models.CharField(max_length=100, blank=True, null=True)
    Permanent_City = models.CharField(max_length=100, blank=True, null=True)
    Permanent_Country = models.CharField(max_length=100, blank=True, choices=Country_Choice, default='Philippines')
    Nationality = models.CharField(max_length=100,blank=True, choices=Nationality_Choice)
    Nationality_Other = models.CharField(max_length=100,blank=True, )
    Travel_History = models.CharField(max_length=100,blank=True, choices=TravelHistory_Choice)
    Travel_History_Specify= models.CharField(max_length=100,blank=True,)


    ## BEHAVIORAL DATA
    Client_Group = models.CharField(max_length=100,blank=True, choices=Client_Risk_Choice)
    Client_Group_Other = models.CharField(max_length=100,blank=True)
    History_Of_Sex_Partner = models.CharField(max_length=100,blank=True, choices=Sex_PartnerChoice)
    Nationality_Sex_Partner = models.CharField(max_length=100,blank=True, choices=NationalityofPartner_Choice)
    Date_of_Last_Sex = models.DateField(null=True, blank=True)
    Nationality_Sex_Partner_Other = models.CharField(max_length=100,blank=True,)
    Number_Of_Sex_Partners= models.CharField(max_length=100,blank=True,)
    Relationship_to_Partners = models.CharField(max_length=100, blank=True, choices=Relationship_to_partnerChoice)
    SB_Urethral = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    SB_Vaginal = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    SB_Anal_Insertive = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    SB_Anal_Receptive = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    SB_Oral_Insertive = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    SB_Oral_Receptive = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Sharing_of_Sex_Toys = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    SB_Others = models.CharField(max_length=100,blank=True, )
    Sti_None = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Sti_Hiv = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Sti_Hepatitis_B = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Sti_Hepatitis_C = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Sti_NGI = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Sti_Syphilis = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Sti_Chlamydia = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Sti_Anogenital_Warts = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Sti_Genital_Ulcer = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Sti_Herpes= models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Sti_Other = models.CharField(max_length=100,blank=True,)
    
    Illicit_Drug_Use = models.CharField(max_length=100,blank=True, choices=Illicit_Drug_Use_Choices)
    Illicit_Drug_Specify = models.CharField(max_length=100,blank=True,)
    Abx_Use_Prescribed = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Abx_Use_Prescribed_Specify = models.CharField(max_length=100,blank=True,)
    Abx_Use_Self_Medicated = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Abx_Use_Self_Medicated_Specify = models.CharField(max_length=100,blank=True,)
    Abx_Use_None = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Abx_Use_Other = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Abx_Use_Other_Specify = models.CharField(max_length=100,blank=True,)
    
    #ROUTE OF ADMINISTRATION
    Route_Oral = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Route_Injectable_IV= models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Route_Dermal= models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Route_Suppository= models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Route_Other= models.CharField(max_length=100,blank=True)

    #MEDICAL HISTORY
    Symp_With_Discharge = models.CharField(max_length=100,blank=True, choices=Symp_Gonorrhoea_Choice)
    Symp_No = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Symp_Discharge_Urethra = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Symp_Discharge_Vagina = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Symp_Discharge_Anus = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Symp_Discharge_Oropharyngeal = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Symp_Pain_Lower_Abdomen = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Symp_Tender_Testicles = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Symp_Painful_Urination = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Symp_Painful_Intercourse = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Symp_Rectal_Pain = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Symp_Other = models.CharField(max_length=100,blank=True)
    Outcome_Of_Follow_Up_Visit = models.CharField(max_length=100,blank=True, choices=Outcome_Followup_Choice)
    Prev_Test_Pos = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Prev_Test_Pos_Date = models.DateField(null= True, blank=True)
    Result_Test_Cure_Initial = models.CharField(max_length=100,blank=True, choices=Result_TestCure_Choice)
    Result_Test_Cure_Followup = models.CharField(max_length=100,blank=True,choices=Result_TestCure_Choice )
    NoTOC_Other_Test = models.CharField(max_length=100,blank=True)
    NoTOC_DatePerformed = models.DateField(null= True, blank=True)
    NoTOC_Result_of_Test = models.CharField(max_length=100,blank=True, choices=NoTOC_ResultofTest)
    Patient_Compliance_Antibiotics = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    OtherDrugs_Specify= models.CharField(max_length=100,blank=True)
    OtherDrugs_Dosage = models.CharField(max_length=100,blank=True)
    OtherDrugs_Route = models.CharField(max_length=100,blank=True, choices=OtherDrugsRoute_Choices)
    OtherDrugs_Duration= models.CharField(max_length=100,  blank=True)


    #treatment information
    Gonorrhea_Treatment = models.CharField(max_length=100,blank=True, choices=Gonnorhea_Treatment_Choice)
    Treatment_Outcome = models.CharField(max_length=100,blank=True, choices=Treatment_Outcome_Choice)
    Primary_Antibiotic = models.CharField(max_length=100,blank=True, choices=Primary_Antibiotics)
    Primary_Abx_Other = models.CharField(max_length=100,blank=True,)
    Secondary_Antibiotic = models.CharField(max_length=100,blank=True,choices=Secondary_Antibiotics)
    Secondary_Abx_Other = models.CharField(max_length=100,blank=True,)
    Notes = models.TextField(blank=True, max_length=255)
    Clinic_Staff = models.CharField(max_length=100,blank=True,)
    Requesting_Physician = models.CharField(max_length=100,blank=True,)
    Telephone_Number = models.CharField(max_length=100,blank=True,)
    Email_Address = models.EmailField(max_length=100, blank=True, null=True, validators=[EmailValidator()])
    Date_Accomplished_Clinic = models.DateField(blank=True, null=True, auto_now = False)
    Date_Requested_Clinic = models.DateField(blank=True, null=True)
   


## Laboratory Results TAB
    Date_Specimen_Collection = models.DateField(null= True, blank=True)
    Specimen_Code = models.CharField(max_length=5, blank=True, null=True)
    Specimen_Type = models.CharField(max_length=100,blank=True, choices=Sp_TypeChoice, default='')
    Specimen_Quality = models.CharField(max_length=100,blank=True, choices=Sp_QualChoice)
    Date_Of_Gram_Stain = models.DateField( null=True, blank=True)
    Diagnosis_At_This_Visit = models.CharField(max_length=100,blank=True, choices=Diagnosis_Choice)
    Gram_Neg_Intracellular = models.CharField(max_length=100,blank=True,choices=Pus_cellsChoice)
    Gram_Neg_Extracellular = models.CharField(max_length=100,blank=True,choices=Pus_cellsChoice)
    Gs_Presence_Of_Pus_Cells = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Presence_GN_Intracellular=models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Presence_GN_Extracellular=models.CharField(max_length=100,blank=True, choices=Common_Choices)
    GS_Pus_Cells=models.CharField(max_length=100,blank=True, choices=Pus_cellsChoice)
    Epithelial_Cells = models.CharField(max_length=100,blank=True, choices=Pus_cellsChoice)
    GS_Date_Released = models.DateField( null= True, blank=True)
    GS_Others = models.TextField(blank=True, null=True, max_length=255)
    GS_Negative=models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Date_Received_in_lab = models.DateField( null= True,  blank=True)
    Positive_Culture_Date = models.DateField(null= True, blank=True)
    Culture_Result = models.CharField(max_length=100,blank=True, choices=CultureResult_Choice)
    
    Species_Identification = models.CharField(max_length=100,blank=True, choices=SpeciesChoices)
    Other_species_ID=models.CharField(max_length=100,blank=True,)
    Specimen_Quality_Cs = models.CharField(max_length=100,blank=True, choices=Sp_QualChoice)
    Susceptibility_Testing_Date = models.DateField(null=True, blank=True)
    Retested_Mic = models.CharField(max_length=100,blank=True, choices=Common_Choices)
    Confirmation_Ast_Date = models.DateField(null= True, blank=True)

    Beta_Lactamase=models.CharField(max_length=100,blank=True, choices=OtherInfo_Choice)
    PPng=models.CharField(max_length=100,blank=True, choices=OtherInfo_Choice)
    TRng=models.CharField(max_length=100,blank=True, choices=OtherInfo_Choice)
    Date_Released = models.DateField(blank=True, null=True)
    For_possible_WGS=models.CharField(max_length=101,blank=True, choices=Common_Choices)
    Date_stocked=models.DateField(blank=True, null=True)
    Location=models.CharField(max_length=103,blank=True,)
    abx_code=models.CharField(max_length=25, blank=True)
    #laboratory personnel
    Laboratory_Staff = models.CharField(max_length=100,blank=True, default='', null=True)
    Date_Accomplished_ARSP=models.DateField(blank=True, null=True)
    ars_notes = models.TextField(blank=True, max_length=255, null=True)
    ars_contact = PhoneNumberField(blank=True, null=True)
    ars_email = models.EmailField(blank=True, null=True, validators=[EmailValidator()])

    def __str__(self):
        return self.Egasp_Id
    
    def formatted_number(self):
        return self.Telephone_Number.as_e164  # Returns the number in +639XXXXXXX format
    
    def __str__(self):
        return f"Current: {self.Current_City}, {self.Current_Province} | Permanent: {self.Permanent_City}, {self.Permanent_Province}"

    
class Meta:
    db_table ="Egasp_Data"

    

# for specific indexing use this
    indexes = [
                models.Index(fields=['Egasp_Id']),  # Index for field1
                models.Index(fields=['Uic_Ptid']),  # Index for field2
                models.Index(fields=['First_Name']),  # Index for field3
                models.Index(fields=['Last_Name']),  # Index for field4
                # add more indexes as needed
            ]

class ClinicData(models.Model):
    PTIDCode=models.CharField(max_length=2, blank=True, unique=True)
    ClinicCode=models.CharField(max_length=3, blank=True)
    ClinicName=models.CharField(max_length=155, blank=True)
    def __str__(self):
        return self.PTIDCode  
    
class Meta:
    db_table ="ClinicData"



class BreakpointsTable(models.Model):
    TestMethodChoices =(
        ('DISK', 'DISK'),
        ('MIC','MIC'),
    )
    
    GuidelineChoices = (
        ('CLSI', 'CLSI'),        
    )

    Guidelines = models.CharField(max_length=100, choices=GuidelineChoices, blank=True, default='')
    Test_Method = models.CharField(max_length=20, choices=TestMethodChoices, blank=True, default='')
    Potency = models.CharField(max_length=5, blank=True, default='')
    Abx_code = models.CharField(max_length=15, blank=True, default='')
    Tier = models.CharField(max_length=10, blank=True, default='')
    Show = models.BooleanField(default=True)
    Retest = models.BooleanField(default=False)
    Antibiotic = models.CharField(max_length=100, blank=True, default='')
    Whonet_Abx = models.CharField(max_length=100, blank=True, default='')
    Disk_Abx = models.BooleanField(default=False)
    R_val = models.CharField(max_length=10, blank=True, default='')
    I_val = models.CharField(max_length=10, blank=True, default='')
    SDD_val = models.CharField(max_length=10, blank=True, default='')
    S_val = models.CharField(max_length=10, blank=True, default='')
    Date_Modified = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return self.Abx_code 

class Meta:
    db_table ="BreakpointsTable"


class Breakpoint_upload(models.Model):
    File_uploadBP = models.FileField(upload_to='uploads/breakpoints/', null=True, blank=True)

class Meta:
    db_table = "Breakpoint_upload"

    
#for antibiotic test entries
class AntibioticEntry(models.Model):
    ab_idNumber_egasp = models.ForeignKey(Egasp_Data, on_delete=models.CASCADE, null=True, related_name='antibiotic_entries')
    ab_breakpoints_id = models.ManyToManyField(BreakpointsTable, max_length=6)
    ab_EgaspId= models.CharField(max_length=100, blank=True, null=True)

   
    ab_Antibiotic = models.CharField(max_length=100, blank=True, null=True)
    ab_Abx_code= models.CharField(max_length=100, blank=True, null=True)
    ab_Abx=models.CharField(max_length=100, blank=True, null=True)

    ab_Disk_value = models.IntegerField(blank=True, null=True)
    ab_Disk_RIS = models.CharField(max_length=4, blank=True)
    ab_MIC_operand=models.CharField(max_length=4, blank=True, null=True, default='')
    ab_MIC_value = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    ab_MIC_RIS = models.CharField(max_length=4, blank=True)

    ab_Retest_Antibiotic = models.CharField(max_length=100, blank=True, null=True)
    ab_Retest_Abx_code = models.CharField(max_length=100, blank=True, null=True)
    ab_Retest_Abx = models.CharField(max_length=100, blank=True, null=True)
    ab_Retest_DiskValue = models.IntegerField(blank=True, null=True)
    ab_Retest_Disk_RIS = models.CharField(max_length=4, blank=True)
    ab_Retest_MIC_operand=models.CharField(max_length=4, blank=True, null=True, default='')
    ab_Retest_MICValue = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    ab_Retest_MIC_RIS = models.CharField(max_length=4, blank=True)
    
    
    ab_R_breakpoint = models.CharField(max_length=10, blank=True, null=True)
    ab_I_breakpoint = models.CharField(max_length=10, blank=True, null=True)
    ab_SDD_breakpoint = models.CharField(max_length=10, blank=True, null=True)  
    ab_S_breakpoint = models.CharField(max_length=10, blank=True, null=True)

    ab_Ret_R_breakpoint = models.CharField(max_length=10, blank=True, null=True)
    ab_Ret_I_breakpoint = models.CharField(max_length=10, blank=True, null=True)
    ab_Ret_SDD_breakpoint = models.CharField(max_length=10, blank=True, null=True)
    ab_Ret_S_breakpoint = models.CharField(max_length=10, blank=True, null=True)    

    def __str__(self):
        return ", ".join([abx.Whonet_Abx for abx in self.ab_breakpoints_id.all()]) 

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Save the instance first
        

    class Meta:
        db_table = "AntibioticEntry"


class SpecimenTypeModel(models.Model):
    Specimen_name = models.CharField(max_length=100, blank=True, null=True)
    Specimen_code = models.CharField(max_length=4, blank=True, null=True)
    def __str__(self):
        return self.Specimen_code 

class Meta:
    db_table = "SpecimenTypeTable"


# Address Book
class Clinic_Staff_Details(models.Model):
    ClinStaff_Name = models.CharField(max_length=100, blank=True, null=True)
    ClinStaff_Telnum = PhoneNumberField(blank=True, region="PH", null=True)
    ClinStaff_EmailAdd = models.EmailField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.ClinStaff_Name if self.ClinStaff_Name else "Unnamed Staff"
