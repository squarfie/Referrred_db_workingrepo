# apps/wgs_app/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import FastqSummary, WGS_Project

@receiver([post_save, post_delete], sender=FastqSummary)
def update_wgs_fastqsummary_flag(sender, instance, **kwargs):
    project = instance.fastq_project
    if project:
        has_fastq = project.fastq_entries.exists()
        project.WGS_FastqSummary = has_fastq
        project.save(update_fields=["WGS_FastqSummary"])
