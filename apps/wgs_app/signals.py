# apps/wgs_app/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import *



def update_summary_flag(project, field_name):
    """Recalculate the flag value dynamically based on whether related records still exist."""
    related_model_map = {
        'WGS_FastqSummary': (FastqSummary, 'fastq_project'),
        'WGS_MlstSummary': (Mlst, 'mlst_project'),
        'WGS_Checkm2Summary': (Checkm2, 'checkm2_project'),
        'WGS_AssemblySummary': (AssemblyScan, 'assembly_project'),
        'WGS_GambitSummary': (Gambit, 'gambit_project'),
        'WGS_AmrfinderSummary': (Amrfinderplus, 'amrfinder_project'),
    }

    model, rel_field = related_model_map[field_name]
    has_records = model.objects.filter(**{rel_field: project}).exists()
    setattr(project, field_name, has_records)
    project.save(update_fields=[field_name])

# === Fastq ===
@receiver([post_save, post_delete], sender=FastqSummary)
def sync_fastq_flag(sender, instance, **kwargs):
    if instance.fastq_project:
        update_summary_flag(instance.fastq_project, 'WGS_FastqSummary')

# === MLST ===
@receiver([post_save, post_delete], sender=Mlst)
def sync_mlst_flag(sender, instance, **kwargs):
    if instance.mlst_project:
        update_summary_flag(instance.mlst_project, 'WGS_MlstSummary')

# === CheckM2 ===
@receiver([post_save, post_delete], sender=Checkm2)
def sync_checkm2_flag(sender, instance, **kwargs):
    if instance.checkm2_project:
        update_summary_flag(instance.checkm2_project, 'WGS_Checkm2Summary')

# === Assembly ===
@receiver([post_save, post_delete], sender=AssemblyScan)
def sync_assembly_flag(sender, instance, **kwargs):
    if instance.assembly_project:
        update_summary_flag(instance.assembly_project, 'WGS_AssemblySummary')

# === Gambit ===
@receiver([post_save, post_delete], sender=Gambit)
def sync_gambit_flag(sender, instance, **kwargs):
    if instance.gambit_project:
        update_summary_flag(instance.gambit_project, 'WGS_GambitSummary')

# === AMRFinder ===
@receiver([post_save, post_delete], sender=Amrfinderplus)
def sync_amrfinder_flag(sender, instance, **kwargs):
    if instance.amrfinder_project:
        update_summary_flag(instance.amrfinder_project, 'WGS_AmrfinderSummary')