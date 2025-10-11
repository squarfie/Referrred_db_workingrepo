# apps/wgs_app/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import *



@receiver(post_save, sender=FastqSummary)
def update_fastq_summary_flag(sender, instance, **kwargs):
    project = instance.fastq_project
    if project:
        project.WGS_FastqSummary = True
        project.save(update_fields=['WGS_FastqSummary'])

@receiver(post_save, sender=Gambit)
def update_gambit_summary_flag(sender, instance, **kwargs):
    project = instance.gambit_project
    if project:
        project.WGS_GambitSummary = True
        project.save(update_fields=['WGS_GambitSummary'])

@receiver(post_save, sender=Mlst)
def update_mlst_summary_flag(sender, instance, **kwargs):
    project = instance.mlst_project
    if project:
        project.WGS_MlstSummary = True
        project.save(update_fields=['WGS_MlstSummary'])

@receiver(post_save, sender=Checkm2)
def update_checkm2_summary_flag(sender, instance, **kwargs):
    project = instance.checkm2_project
    if project:
        project.WGS_Checkm2Summary = True
        project.save(update_fields=['WGS_Checkm2Summary'])

@receiver(post_save, sender=AssemblyScan)
def update_assembly_summary_flag(sender, instance, **kwargs):
    project = instance.assembly_project
    if project:
        project.WGS_AssemblySummary = True
        project.save(update_fields=['WGS_AssemblySummary'])

@receiver(post_save, sender=Amrfinderplus)
def update_amrfinder_summary_flag(sender, instance, **kwargs):
    project = instance.amrfinder_project
    if project:
        project.WGS_AmrfinderSummary = True
        project.save(update_fields=['WGS_AmrfinderSummary'])