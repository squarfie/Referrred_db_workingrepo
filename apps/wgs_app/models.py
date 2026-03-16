from django.db import models

# Create your models here.


class DemogsData_upload(models.Model):
    DemogsDataFile = models.FileField(upload_to='uploads/final/', null=True, blank=True)

    class Meta:
        db_table ="DemogsData_upload"




# Connector Table for WGS Projects
class WGS_Project(models.Model):
    Ref_Accession = models.ForeignKey(
        'home_final.Final_Data',    # connects to Final_Data model
        on_delete=models.CASCADE,   #DELETE WHEN FINAL REFERRED DATA ACCESSION IS DELETED
        null=True,
        blank=True,
        related_name='project_entries',
        to_field='f_AccessionNo'
    )

    WGS_SampleInfo_Acc = models.CharField(max_length=255, blank=True, null=True)
    WGS_SampleInfoSummary = models.BooleanField(default=False, blank=True)

    WGS_BactScout_Acc = models.CharField(max_length=255, blank=True, null=True)
    WGS_BactScoutSummary = models.BooleanField(default=False, blank=True)

    WGS_GtdbTk_Acc = models.CharField(max_length=255, blank=True, null=True)
    WGS_GtdbTkSummary = models.BooleanField(default=False, blank=True)


    WGS_FastQ_Acc = models.CharField(max_length=255, blank=True, null=True)
    WGS_FastqSummary = models.BooleanField(default=False, blank=True)  # indicates if FastqSummary entries exist
    WGS_Gambit_Acc = models.CharField(max_length=255, blank=True, null=True)
    WGS_GambitSummary = models.BooleanField(default=False, blank=True)
    WGS_Mlst_Acc = models.CharField(max_length=255, blank=True, null=True)
    WGS_MlstSummary = models.BooleanField(default=False, blank=True, null=True)
    WGS_Checkm2_Acc = models.CharField(max_length=255, blank=True, null=True)
    WGS_Checkm2Summary = models.BooleanField(default=False, blank=True)
    WGS_Assembly_Acc = models.CharField(max_length=255, blank=True, null=True)
    WGS_AssemblySummary = models.BooleanField(default=False, blank=True)
    WGS_Amrfinder_Acc = models.CharField(max_length=255, blank=True, null=True)
    WGS_AmrfinderSummary = models.BooleanField(default=False, blank=True)

    class Meta:
        db_table = "WGS_Project"  # table name in DB
        verbose_name = "WGS Project"
        verbose_name_plural = "WGS Projects"


    def __str__(self):
        return str(self.Ref_Accession) if self.Ref_Accession else ""


# ──────────────────────────────────────────────
# Sample Information
# ──────────────────────────────────────────────
class SampleInformation(models.Model):
    sample_project = models.ForeignKey(
        "wgs_app.WGS_Project",
        on_delete=models.SET_NULL,
        null=True,
        related_name="sample_information_entries"
    )
    sample_accession = models.CharField(max_length=255, blank=True, null=True)
    batch_code = models.CharField(max_length=255, blank=True, null=True)
    sample_name = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)

    # surveillance / programme flags
    emerging = models.BooleanField(default=False)
    structured = models.BooleanField(default=False)
    satscan = models.BooleanField(default=False)
    serotyping = models.BooleanField(default=False)
    ghru = models.BooleanField(default=False)
    egasp = models.BooleanField(default=False)
    tricycle = models.BooleanField(default=False)
    pulsenet = models.BooleanField(default=False)
    tulip = models.BooleanField(default=False)

    Date_uploaded_si = models.DateField(auto_now_add=True)

    class Meta:
        db_table = "sample_information"
        verbose_name = "Sample Information"
        verbose_name_plural = "Sample Information"

    def __str__(self):
        return self.sample_name or ""


class SampleInfoUpload(models.Model):
    sampleinfo = models.FileField(upload_to='uploads/wgs/bactscout/', null=True, blank=True)

    class Meta:
        db_table = "SampleInfoUpload"


# ──────────────────────────────────────────────
# BactScout
# ──────────────────────────────────────────────
class BactScout(models.Model):
    bactscout_project = models.ForeignKey(
        "wgs_app.WGS_Project",
        on_delete=models.SET_NULL,
        null=True,
        related_name="bactscout_entries"
    )
    BactScout_Accession = models.CharField(max_length=255, blank=True, null=True)

    # sample information
    name = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)

    # integrated checkm2 columns
    completeness = models.FloatField(blank=True, null=True)                         # e.g. 99.99
    contamination = models.FloatField(blank=True, null=True)                        # e.g. 0.16
    completeness_model_used = models.CharField(max_length=255, blank=True, null=True)
    translation_table_used = models.IntegerField(blank=True, null=True)             # e.g. 11
    coding_density = models.FloatField(blank=True, null=True)                       # e.g. 0.841
    contig_n50 = models.IntegerField(blank=True, null=True)                         # e.g. 44250
    average_gene_length = models.FloatField(blank=True, null=True)                  # e.g. 276.16
    genome_size = models.IntegerField(blank=True, null=True)                        # e.g. 2191704
    checkm2_gc_content = models.FloatField(blank=True, null=True)                   # GC_Content from checkm2 (e.g. 0.52)
    total_coding_sequences = models.IntegerField(blank=True, null=True)             # e.g. 2230
    total_contigs = models.IntegerField(blank=True, null=True)                      # e.g. 114
    max_contig_length = models.IntegerField(blank=True, null=True)                  # e.g. 207591
    additional_notes = models.TextField(blank=True, null=True)                      # e.g. None

    # overall status flags
    a_final_status = models.CharField(max_length=255, blank=True, null=True)
    adapter_detection_status = models.CharField(max_length=255, blank=True, null=True)
    contamination_status = models.CharField(max_length=255, blank=True, null=True)
    species_status = models.CharField(max_length=255, blank=True, null=True)
    coverage_status = models.CharField(max_length=255, blank=True, null=True)
    coverage_estimate_qualibact_status = models.CharField(max_length=255, blank=True, null=True)
    duplication_status = models.CharField(max_length=255, blank=True, null=True)
    gc_content_status = models.CharField(max_length=255, blank=True, null=True)
    mlst_status = models.CharField(max_length=255, blank=True, null=True)
    n_content_status = models.CharField(max_length=255, blank=True, null=True)
    read_length_status = models.CharField(max_length=255, blank=True, null=True)
    read_q30_status = models.CharField(max_length=255, blank=True, null=True)

    # species
    species = models.CharField(max_length=255, blank=True, null=True)
    species_abundance = models.FloatField(blank=True, null=True)                    # e.g. 93.875
    species_coverage = models.FloatField(blank=True, null=True)                     # e.g. 254.4
    species_message = models.TextField(blank=True, null=True)

    # contamination
    contamination_message = models.TextField(blank=True, null=True)

    # coverage
    coverage_estimate_sylph = models.FloatField(blank=True, null=True)              # e.g. 54.4
    coverage_estimate_sylph_message = models.TextField(blank=True, null=True)
    coverage_estimate_qualibact = models.FloatField(blank=True, null=True)          # e.g. 79.12
    coverage_estimate_qualibact_message = models.TextField(blank=True, null=True)

    # duplication
    duplication_rate = models.FloatField(blank=True, null=True)                     # e.g. 0.001143
    duplication_message = models.TextField(blank=True, null=True)

    # GC content (bactscout)
    gc_content = models.FloatField(blank=True, null=True)                           # e.g. 50.707
    gc_content_lower = models.IntegerField(blank=True, null=True)                   # e.g. 50
    gc_content_upper = models.IntegerField(blank=True, null=True)                   # e.g. 52
    gc_content_message = models.TextField(blank=True, null=True)

    # N content
    n_content_rate = models.FloatField(blank=True, null=True)                       # e.g. 0.0
    n_content_message = models.TextField(blank=True, null=True)

    # MLST (summary from bactscout)
    mlst_st = models.CharField(max_length=255, blank=True, null=True)               # e.g. "405" or text
    mlst_message = models.TextField(blank=True, null=True)

    # read length
    read1_mean_length = models.IntegerField(blank=True, null=True)                  # e.g. 129
    read2_mean_length = models.IntegerField(blank=True, null=True)                  # e.g. 130
    read_length_message = models.TextField(blank=True, null=True)

    # read quality
    read_q20_bases = models.FloatField(blank=True, null=True)                       # e.g. 3.88E+08 (stored as float)
    read_q20_rate = models.FloatField(blank=True, null=True)                        # e.g. 0.9421
    read_q30_bases = models.FloatField(blank=True, null=True)                       # e.g. 3.81E+08
    read_q30_rate = models.FloatField(blank=True, null=True)                        # e.g. 0.9258
    read_q30_message = models.TextField(blank=True, null=True)
    read_total_bases = models.FloatField(blank=True, null=True)                     # e.g. 4.11E+08
    read_total_reads = models.IntegerField(blank=True, null=True)                   # e.g. 3162342

    # adapter
    adapter_detection_message = models.TextField(blank=True, null=True)

    # reference
    ref_genome = models.CharField(max_length=255, blank=True, null=True)            # e.g. GCF_003697165.2
    genome_size_expected = models.IntegerField(blank=True, null=True)               # e.g. 5200000

    Date_uploaded_bs = models.DateField(auto_now_add=True)

    class Meta:
        db_table = "BactScout"

    def __str__(self):
        return self.sample_name or ""


class BactScoutUpload(models.Model):
    bactscoutfile = models.FileField(upload_to='uploads/wgs/bactscout/', null=True, blank=True)

    class Meta:
        db_table = "BactScoutUpload"




# ──────────────────────────────────────────────
# GTDB-Tk
# ──────────────────────────────────────────────
class GtdbTk(models.Model):
    gtdbtk_project = models.ForeignKey(
        "wgs_app.WGS_Project",
        on_delete=models.SET_NULL,
        null=True,
        related_name="gtdbtk_entries"
    )
    GtdbTk_Accession = models.CharField(max_length=255, blank=True, null=True)
    user_genome = models.CharField(max_length=255, blank=True, null=True)           # sample ID
    classification = models.TextField(blank=True, null=True)                        # full taxonomy string d__;p__;...

    # closest genome (always populated)
    closest_genome_reference = models.CharField(max_length=255, blank=True, null=True)     # e.g. GCF_003315235.1
    closest_genome_reference_radius = models.IntegerField(blank=True, null=True)           # e.g. 95
    closest_genome_taxonomy = models.TextField(blank=True, null=True)                      # full taxonomy string
    closest_genome_ani = models.FloatField(blank=True, null=True)                          # e.g. 99.56
    closest_genome_af = models.FloatField(blank=True, null=True)                           # e.g. 0.974

    # closest placement (N/A when ani_screen method used)
    closest_placement_reference = models.CharField(max_length=255, blank=True, null=True)  # N/A or GCF_...
    closest_placement_radius = models.FloatField(blank=True, null=True)                    # N/A → null
    closest_placement_taxonomy = models.TextField(blank=True, null=True)
    closest_placement_ani = models.FloatField(blank=True, null=True)                       # N/A → null
    closest_placement_af = models.FloatField(blank=True, null=True)                        # N/A → null

    pplacer_taxonomy = models.TextField(blank=True, null=True)                             # N/A or taxonomy
    classification_method = models.CharField(max_length=255, blank=True, null=True)        # e.g. ani_screen
    note = models.TextField(blank=True, null=True)                                         # e.g. classification based on ANI only
    other_related_references = models.TextField(blank=True, null=True)                     # genome_id, species_name, radius, ANI, AF (long)
    msa_percent = models.FloatField(blank=True, null=True)                                 # N/A → null
    translation_table = models.IntegerField(blank=True, null=True)                         # N/A → null
    red_value = models.FloatField(blank=True, null=True)                                   # N/A → null
    warnings = models.TextField(blank=True, null=True)

    Date_uploaded_gt = models.DateField(auto_now_add=True)

    class Meta:
        db_table = "gtdbtk"

    def __str__(self):
        return self.user_genome or ""


class GtdbTkUpload(models.Model):
    GtdbTkFile = models.FileField(upload_to='uploads/wgs/gtdbtk/', null=True, blank=True)

    class Meta:
        db_table = "GtdbTkUpload"





# fastq summary
class FastqSummary(models.Model):
    fastq_project = models.ForeignKey(
        "wgs_app.WGS_Project",   # connects to WGS_Project model
        on_delete=models.SET_NULL,
        null=True,
        related_name="fastq_entries"
    )
    FastQ_Accession = models.CharField(max_length=255, blank=True, null=True)
    sample = models.CharField(max_length=255, blank=True, null=True)
    fastp_version = models.CharField(max_length=255, blank=True, null=True)
    sequencing = models.CharField(max_length=255, blank=True, null=True)
    before_total_reads = models.CharField(max_length=255, blank=True, null=True)
    before_total_bases = models.CharField(max_length=255, blank=True, null=True)
    before_q20_rate = models.CharField(max_length=255, blank=True, null=True)
    before_q30_rate = models.CharField(max_length=255, blank=True, null=True)
    before_read1_mean_len = models.CharField(max_length=255, blank=True, null=True)
    before_read2_mean_len = models.CharField(max_length=255, blank=True, null=True)
    before_gc_content = models.CharField(max_length=255, blank=True, null=True)
    after_total_reads = models.CharField(max_length=255, blank=True, null=True)
    after_total_bases = models.CharField(max_length=255, blank=True, null=True)
    after_q20_rate = models.CharField(max_length=255, blank=True, null=True)
    after_q30_rate = models.CharField(max_length=255, blank=True, null=True)
    after_read1_mean_len = models.CharField(max_length=255, blank=True, null=True)
    after_read2_mean_len = models.CharField(max_length=255, blank=True, null=True)
    after_gc_content = models.CharField(max_length=255, blank=True, null=True)
    passed_filter_reads = models.CharField(max_length=255, blank=True, null=True)
    low_quality_reads = models.CharField(max_length=255, blank=True, null=True)
    too_many_N_reads = models.CharField(max_length=255, blank=True, null=True)
    too_short_reads = models.CharField(max_length=255, blank=True, null=True)
    too_long_reads = models.CharField(max_length=255, blank=True, null=True)
    combined_total_bp = models.CharField(max_length=255, blank=True, null=True)
    combined_qual_mean = models.CharField(max_length=255, blank=True, null=True)
    post_trim_q30_rate = models.CharField(max_length=255, blank=True, null=True)
    post_trim_q30_pct = models.CharField(max_length=255, blank=True, null=True)
    post_trim_q20_rate = models.CharField(max_length=255, blank=True, null=True)
    post_trim_q20_pct = models.CharField(max_length=255, blank=True, null=True)
    after_gc_pct = models.CharField(max_length=255, blank=True, null=True)
    duplication_rate = models.CharField(max_length=255, blank=True, null=True)
    read_length_mean_after = models.CharField(max_length=255, blank=True, null=True)
    adapter_trimmed_reads = models.CharField(max_length=255, blank=True, null=True)
    adapter_trimmed_reads_pct = models.CharField(max_length=255, blank=True, null=True)
    adapter_trimmed_bases = models.CharField(max_length=255, blank=True, null=True)
    adapter_trimmed_bases_pct = models.CharField(max_length=255, blank=True, null=True)
    insert_size_peak = models.CharField(max_length=255, blank=True, null=True)
    insert_size_unknown = models.CharField(max_length=255, blank=True, null=True)
    overrep_r1_count = models.CharField(max_length=255, blank=True, null=True)
    overrep_r2_count = models.CharField(max_length=255, blank=True, null=True)
    ns_overrep_none = models.CharField(max_length=255, blank=True, null=True)
    qc_q30_pass = models.CharField(max_length=255, blank=True, null=True)
    q30_status = models.CharField(max_length=255, blank=True, null=True)
    q20_status = models.CharField(max_length=255, blank=True, null=True)
    adapter_reads_status = models.CharField(max_length=255, blank=True, null=True)
    adapter_bases_status = models.CharField(max_length=255, blank=True, null=True)
    duplication_status = models.CharField(max_length=255, blank=True, null=True)
    readlen_status = models.CharField(max_length=255, blank=True, null=True)
    ns_overrep_status = models.CharField(max_length=255, blank=True, null=True)
    raw_reads_qc_summary = models.CharField(max_length=255, blank=True, null=True)
    Date_uploaded_f = models.DateField(auto_now_add=True)
   

    class Meta:
        db_table = "FastqSummary"

    def __str__(self):
        return self.sample or ""

    
    
# uploading project files
class FastqUpload(models.Model):
    fastqfile = models.FileField(upload_to='uploads/wgs/fastq/', null=True, blank=True)

    class Meta:
        db_table = "FastqUpload"


# gambit
class Gambit(models.Model):
    gambit_project = models.ForeignKey(
        "wgs_app.WGS_Project",   # connects to WGS_Project model
        on_delete=models.SET_NULL,
        null=True,
        related_name="gambit_entries"
    )
    Gambit_Accession = models.CharField(max_length=255, blank=True, null=True)
    sample = models.CharField(max_length=255, blank=True, null=True)
    predicted_name = models.CharField(max_length=255, blank=True, null=True)
    predicted_rank = models.CharField(max_length=255, blank=True, null=True)
    predicted_ncbi_id = models.CharField(max_length=255, blank=True, null=True)
    predicted_threshold = models.CharField(max_length=255, blank=True, null=True)
    closest_distance = models.CharField(max_length=255, blank=True, null=True)
    closest_description = models.CharField(max_length=255, blank=True, null=True)
    next_name = models.CharField(max_length=255, blank=True, null=True)
    next_rank = models.CharField(max_length=255, blank=True, null=True)
    next_ncbi_id = models.CharField(max_length=255, blank=True, null=True)
    next_threshold = models.CharField(max_length=255, blank=True, null=True)
    Date_uploaded_g= models.DateField(auto_now_add=True)

    class Meta:
        db_table = "gambit"
    def __str__(self):
        return self.sample or ""


# uploading project files
class GambitUpload(models.Model):
    GambitFile = models.FileField(upload_to='uploads/wgs/gambit/', null=True, blank=True)

    class Meta:
        db_table = "GambitUpload"


class GambitDisplayConfig(models.Model):
    field_name = models.CharField(max_length=100, unique=True)
    show = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.field_name} ({'Show' if self.show else 'Hide'})"



# mlst
class Mlst(models.Model):
    mlst_project = models.ForeignKey(
        "wgs_app.WGS_Project",   # connects to WGS_Project model
        on_delete=models.SET_NULL,
        null=True,
        related_name="mlst_entries"
    )
    Mlst_Accession = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    scheme = models.CharField(max_length=255, blank=True, null=True)
    mlst = models.CharField(max_length=255, blank=True, null=True)
    allele1 = models.CharField(max_length=255, blank=True, null=True)
    allele2 = models.CharField(max_length=255, blank=True, null=True)
    allele3 = models.CharField(max_length=255, blank=True, null=True)
    allele4 = models.CharField(max_length=255, blank=True, null=True)
    allele5 = models.CharField(max_length=255, blank=True, null=True)
    allele6 = models.CharField(max_length=255, blank=True, null=True)
    allele7 = models.CharField(max_length=255, blank=True, null=True)
    Date_uploaded_m = models.DateField(auto_now_add=True)
    class Meta:
        db_table = "mlst"
    def __str__(self):
        return self.name or ""

class MlstUpload(models.Model):
    Mlstfile = models.FileField(upload_to='uploads/wgs/mlst/', null=True, blank=True)

    class Meta:
        db_table = "MlstUpload"


# Checkm2
class Checkm2(models.Model):
    checkm2_project = models.ForeignKey(
        "wgs_app.WGS_Project",   # connects to WGS_Project model
        on_delete=models.SET_NULL,
        null=True,
        related_name="checkm2_entries"
    )
    Checkm2_Accession = models.CharField(max_length=255, blank=True, null=True)
    Name = models.CharField(max_length=255, blank=True, null=True)
    Completeness = models.CharField(max_length=255, blank=True, null=True)
    Contamination = models.CharField(max_length=255, blank=True, null=True)
    Completeness_Model_Used = models.CharField(max_length=255, blank=True, null=True)
    Translation_Table_Used = models.CharField(max_length=255, blank=True, null=True)
    Coding_Density = models.CharField(max_length=255, blank=True, null=True)
    Contig_N50 = models.CharField(max_length=255, blank=True, null=True)
    Average_Gene_Length = models.CharField(max_length=255, blank=True, null=True)
    Genome_Size = models.CharField(max_length=255, blank=True, null=True)
    GC_Content = models.CharField(max_length=255, blank=True, null=True)
    Total_Coding_Sequences = models.CharField(max_length=255, blank=True, null=True)
    Total_Contigs = models.CharField(max_length=255, blank=True, null=True)
    Max_Contig_Length = models.CharField(max_length=255, blank=True, null=True)
    Additional_Notes = models.CharField(max_length=255, blank=True, null=True)
    Date_uploaded_c = models.DateField(auto_now_add=True)
    class Meta:
        db_table = "checkm2"
    def __str__(self):
        return self.Name or ""

class Checkm2Upload(models.Model):
    Checkm2file = models.FileField(upload_to='uploads/wgs/checkm2/', null=True, blank=True)

    class Meta:
        db_table = "Checkm2Upload"


# AssemblyScan
class AssemblyScan(models.Model):
    assembly_project = models.ForeignKey(
        "wgs_app.WGS_Project",   # connects to WGS_Project model
        on_delete=models.SET_NULL,
        null=True,
        related_name="assembly_entries"
    )
    Assembly_Accession = models.CharField(max_length=255, blank=True, null=True)
    sample = models.CharField(max_length=255, blank=True, null=True)
    total_contig = models.CharField(max_length=255, blank=True, null=True)
    total_contig_length = models.CharField(max_length=255, blank=True, null=True)
    max_contig_length = models.CharField(max_length=255, blank=True, null=True)
    mean_contig_length = models.CharField(max_length=255, blank=True, null=True)
    median_contig_length = models.CharField(max_length=255, blank=True, null=True)
    min_contig_length = models.CharField(max_length=255, blank=True, null=True)
    n50_contig_length = models.CharField(max_length=255, blank=True, null=True)
    l50_contig_count = models.CharField(max_length=255, blank=True, null=True)
    num_contig_non_acgtn = models.CharField(max_length=255, blank=True, null=True)
    contig_percent_a = models.CharField(max_length=255, blank=True, null=True)
    contig_percent_c = models.CharField(max_length=255, blank=True, null=True)
    contig_percent_g = models.CharField(max_length=255, blank=True, null=True)
    contig_percent_t = models.CharField(max_length=255, blank=True, null=True)
    contig_percent_n = models.CharField(max_length=255, blank=True, null=True)
    contig_non_acgtn = models.CharField(max_length=255, blank=True, null=True)
    contigs_greater_1m = models.CharField(max_length=255, blank=True, null=True)
    contigs_greater_100k = models.CharField(max_length=255, blank=True, null=True)
    contigs_greater_10k = models.CharField(max_length=255, blank=True, null=True)
    contigs_greater_1k = models.CharField(max_length=255, blank=True, null=True)
    percent_contigs_greater_1m = models.CharField(max_length=255, blank=True, null=True)
    percent_contigs_greater_100k = models.CharField(max_length=255, blank=True, null=True)
    percent_contigs_greater_10k = models.CharField(max_length=255, blank=True, null=True)
    percent_contigs_greater_1k = models.CharField(max_length=255, blank=True, null=True)
    Date_uploaded_as = models.DateField(auto_now_add=True)
    class Meta:
        db_table = "assembly-scan"
    def __str__(self):
        return self.sample or ""
    
class AssemblyUpload(models.Model):
    Assemblyfile = models.FileField(upload_to='uploads/wgs/assemblyscan/', null=True, blank=True)

    class Meta:
        db_table = "AssemblyUpload"

# Amrfinderplus
class Amrfinderplus(models.Model):
    amrfinder_project = models.ForeignKey(
        "wgs_app.WGS_Project",   # connects to WGS_Project model
        on_delete=models.SET_NULL,
        null=True,
        related_name="amrfinder_entries"
    )
    Amrfinder_Accession = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    protein_id = models.CharField(max_length=255, blank=True, null=True)
    contig_id = models.CharField(max_length=255, blank=True, null=True)
    start = models.CharField(max_length=255, blank=True, null=True)
    stop = models.CharField(max_length=255, blank=True, null=True)
    strand = models.CharField(max_length=255, blank=True, null=True)
    element_symbol = models.CharField(max_length=255, blank=True, null=True)
    element_name = models.CharField(max_length=255, blank=True, null=True)
    scope = models.CharField(max_length=255, blank=True, null=True)
    type_field = models.CharField(max_length=255, blank=True, null=True)  # renamed from "Type"
    subtype = models.CharField(max_length=255, blank=True, null=True)
    class_field = models.CharField(max_length=255, blank=True, null=True)  # renamed from "Class"
    subclass = models.CharField(max_length=255, blank=True, null=True)
    method = models.CharField(max_length=255, blank=True, null=True)
    target_length = models.CharField(max_length=255, blank=True, null=True)
    reference_sequence_length = models.CharField(max_length=255, blank=True, null=True)
    percent_coverage_of_reference = models.CharField(max_length=255, blank=True, null=True)
    percent_identity_to_reference = models.CharField(max_length=255, blank=True, null=True)
    alignment_length = models.CharField(max_length=255, blank=True, null=True)
    closest_reference_accession = models.CharField(max_length=255, blank=True, null=True)
    closest_reference_name = models.CharField(max_length=255, blank=True, null=True)
    hmm_accession = models.CharField(max_length=255, blank=True, null=True)
    hmm_description = models.CharField(max_length=255, blank=True, null=True)
    Date_uploaded_am = models.DateField(auto_now_add=True)
    class Meta:
        db_table = "amrfinderplus"
    def __str__(self):
        return self.name or "No name"


class AmrfinderUpload(models.Model):
    Amrfinderfile = models.FileField(upload_to='uploads/wgs/amrfinder/', null=True, blank=True)

    class Meta:
        db_table = "AmrfinderUpload"
