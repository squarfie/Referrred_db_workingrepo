from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver

from apps.home_final.views import regenerate_concordance_snapshot
from apps.home_final.models import Final_AntibioticEntry, Final_Data, Classification_Table, Emerging_Table
from .models import *
import re
from django.db.models import Q, F



def get_active_value_and_mode(instance, is_retest=False):
    """
    Returns (value, is_disk) based on which result is active.
    MIC always overrides DISK.
    """

    if is_retest:
        if instance.ab_Retest_MICValue not in ("", None):
            return instance.ab_Retest_MICValue, False
        if instance.ab_Retest_DiskValue not in ("", None):
            return instance.ab_Retest_DiskValue, True
    else:
        if instance.ab_MIC_value not in ("", None):
            return instance.ab_MIC_value, False
        if instance.ab_Disk_value not in ("", None):
            return instance.ab_Disk_value, True

    return None, None




def determine_ris(value, r_breakpoint, i_breakpoint, s_breakpoint, sdd_breakpoint, is_disk=False):
    """
    Safely determine RIS interpretation for Disk or MIC results.
    Returns "" if interpretation cannot be determined.
    """

    # --- Guard: value must exist ---
    if value in ("", None):
        return ""

    # --- Convert value ---
    try:
        value = int(value) if is_disk else float(value)
    except (TypeError, ValueError):
        return ""

    # --- Helper to convert breakpoint safely ---
    def to_number(bp):
        if bp in ("", None):
            return None
        try:
            return int(bp) if is_disk else float(bp)
        except (TypeError, ValueError):
            return None

    r = to_number(r_breakpoint)
    s = to_number(s_breakpoint)
    sdd = to_number(sdd_breakpoint)

    # --- INTERMEDIATE (range support) ---
    if i_breakpoint not in ("", None):
        try:
            if "-" in str(i_breakpoint):
                low, high = str(i_breakpoint).split("-")
                low = to_number(low)
                high = to_number(high)
                if low is not None and high is not None and low <= value <= high:
                    return "I"
            else:
                i = to_number(i_breakpoint)
                if i is not None and value == i:
                    return "I"
        except Exception:
            pass

    # --- SDD ---
    if sdd is not None:
        if value == sdd:
            return "SDD"

    # --- BOTH R AND S EXIST ---
    if r is not None and s is not None:
        if is_disk:
            if value <= r:
                return "R"
            elif value >= s:
                return "S"
            else:
                return "I"
        else:  # MIC
            if value >= r:
                return "R"
            elif value <= s:
                return "S"
            else:
                return "I"

    # --- ONLY S EXISTS ---
    if s is not None:
        if is_disk:
            return "S" if value >= s else "R"
        else:
            return "S" if value <= s else "R"

    # --- ONLY R EXISTS ---
    if r is not None:
        if is_disk:
            return "R" if value <= r else "S"
        else:
            return "R" if value >= r else "S"

    # --- No interpretation possible ---
    return ""


@receiver(post_save, sender=Final_AntibioticEntry)
def update_ris_interpretation(sender, instance, **kwargs):
    print("\n[DEBUG] update_ris_interpretation fired...")
    updated_fields = []

    # Retrieve the BreakpointsTable entry associated with the AntibioticEntry
    breakpoint_entry = instance.ab_breakpoints_id.first()
    is_disk = breakpoint_entry.Disk_Abx if breakpoint_entry else False

    # Update ab_Disk_RIS
    print(f"{instance.ab_Antibiotic} : MIC={instance.ab_MIC_value}, Disk={instance.ab_Disk_value}, Retest-{instance.ab_Retest_Antibiotic} : Retest-DISK={instance.ab_Retest_DiskValue}, Retest-MIC={instance.ab_Retest_MICValue},"
      f"R={instance.ab_R_breakpoint}, I={instance.ab_I_breakpoint}, S={instance.ab_S_breakpoint}, SDD={instance.ab_SDD_breakpoint}")
    
    disk_ris = determine_ris(instance.ab_Disk_value, instance.ab_R_breakpoint, instance.ab_I_breakpoint, instance.ab_S_breakpoint, instance.ab_SDD_breakpoint, is_disk=is_disk)
    if disk_ris and disk_ris != instance.ab_Disk_RIS:
        instance.ab_Disk_RIS = disk_ris
        updated_fields.append("ab_Disk_RIS")

    # Update ab_MIC_RIS
    mic_ris = determine_ris(instance.ab_MIC_value, instance.ab_R_breakpoint, instance.ab_I_breakpoint, instance.ab_S_breakpoint, instance.ab_SDD_breakpoint)
    if mic_ris and mic_ris != instance.ab_MIC_RIS:
        instance.ab_MIC_RIS = mic_ris
        updated_fields.append("ab_MIC_RIS")

    # Update ab_Retest_Disk_RIS
    retest_disk_ris = determine_ris(instance.ab_Retest_DiskValue, instance.ab_Ret_R_breakpoint, instance.ab_Ret_I_breakpoint, instance.ab_Ret_S_breakpoint, instance.ab_Ret_SDD_breakpoint, is_disk=is_disk)
    if retest_disk_ris and retest_disk_ris != instance.ab_Retest_Disk_RIS:
        instance.ab_Retest_Disk_RIS = retest_disk_ris
        updated_fields.append("ab_Retest_Disk_RIS")

    # Update ab_Retest_MIC_RIS
    retest_mic_ris = determine_ris(instance.ab_Retest_MICValue, instance.ab_Ret_R_breakpoint, instance.ab_Ret_I_breakpoint, instance.ab_Ret_S_breakpoint, instance.ab_Ret_SDD_breakpoint)
    if retest_mic_ris and retest_mic_ris != instance.ab_Retest_MIC_RIS:
        instance.ab_Retest_MIC_RIS = retest_mic_ris
        updated_fields.append("ab_Retest_MIC_RIS")

    # Only save if there are updates
    if updated_fields:
        instance.save(update_fields=updated_fields)





# version 1 - original
# @receiver(post_save, sender=Final_AntibioticEntry)
# def update_ris_interpretation(sender, instance, **kwargs):
#     print("Final_AntibioticEntry saved:", instance.id)
#     updated_fields = []

#     bp = instance.ab_breakpoints_id.first()
#     if not bp:
#         return

#     # -------- MAIN ----------
#     value, is_disk = get_active_value_and_mode(instance, is_retest=False)
#     if value is not None:
#         ris = determine_ris(
#             value,
#             instance.ab_R_breakpoint,
#             instance.ab_I_breakpoint,
#             instance.ab_S_breakpoint,
#             instance.ab_SDD_breakpoint,
#             is_disk=is_disk
#         )

#         if ris and is_disk and ris != instance.ab_Disk_RIS:
#             instance.ab_Disk_RIS = ris
#             updated_fields.append("ab_Disk_RIS")

#         if ris and not is_disk and ris != instance.ab_MIC_RIS:
#             instance.ab_MIC_RIS = ris
#             updated_fields.append("ab_MIC_RIS")


#     # -------- RETEST ----------
#     value, is_disk = get_active_value_and_mode(instance, is_retest=True)
#     if value is not None:
#         ris = determine_ris(
#             value,
#             instance.ab_Ret_R_breakpoint,
#             instance.ab_Ret_I_breakpoint,
#             instance.ab_Ret_S_breakpoint,
#             instance.ab_Ret_SDD_breakpoint,
#             is_disk=is_disk
#         )

#         if is_disk and ris != instance.ab_Retest_Disk_RIS:
#             instance.ab_Retest_Disk_RIS = ris
#             updated_fields.append("ab_Retest_Disk_RIS")

#         if not is_disk and ris != instance.ab_Retest_MIC_RIS:
#             instance.ab_Retest_MIC_RIS = ris
#             updated_fields.append("ab_Retest_MIC_RIS")

#     if updated_fields:
#         instance.save(update_fields=updated_fields)




# Emerging → Classification sync




# @receiver(post_save, sender=Emerging_Table)
# def sync_classification_from_emerging(sender, instance, **kwargs):
#     print("\n[DEBUG] sync_classification_from_emerging fired")
#     print(
#         "[DEBUG] completeness:",
#         instance.eme_spec_Type,
#         instance.eme_ars_Org,
#         instance.eme_abx_code_pheno,
#     )

#     is_fully = Emerging_Table.fully_emerging().filter(
#         pk=instance.pk
#     ).exists()

#     Classification_Table.objects.update_or_create(
#         Class_idNumReferred=instance.eme_primary_key,
#         defaults={
#             "Class_AccessionNo": instance.eme_Accession,
#             "Class_Chk_Emerging": is_fully,
#         },
#     )

#     print("  Class_Chk_Emerging =", is_fully)



# @receiver(post_save, sender=Final_Data)
# def update_emerging_spec_flag(sender, instance, **kwargs):
#     spec_flag = False

#     if instance.f_Spec_Type:
#         spec_flag = SpecimenTypeModel.objects.filter(
#             Specimen_code=instance.f_Spec_Type,
#             Emerging_Spec_Flag=True,
#         ).exists()

#     Emerging_Table.objects.update_or_create(
#         eme_primary_key=instance,
#         defaults={
#             "eme_Spec_Flag": spec_flag,
#             "eme_spec_Type": instance.f_Spec_Type or "",
#             "eme_spec_Num": instance.f_Spec_Num or "",
#             "eme_Accession": instance.f_AccessionNo,
#             "eme_Site_Code": instance.f_SiteCode,
#             "eme_ars_Org": instance.f_ars_OrgCode or "",
#         },
#     )



# @receiver(post_save, sender=Final_AntibioticEntry)
# def update_emerging_abx_flags(sender, instance, **kwargs):

#     # Only process retest entries
#     if not instance.ab_Retest_Abx_code:
#         return

#     final = instance.ab_idNum_f_referred

#     # Get all retest antibiotic entries for this isolate
#     retest_entries = Final_AntibioticEntry.objects.filter(
#         ab_idNum_f_referred=final,
#         ab_Retest_Abx_code__isnull=False
#     )

#     emerging_triggered = False
#     triggered_abx_codes = []
#     triggered_phenotypes = []

#     for entry in retest_entries:

#         bp = entry.ab_breakpoints_id.first()
#         if not bp:
#             continue

#         ris = entry.ab_Retest_MIC_enRIS or entry.ab_Retest_Disk_enRIS
#         if not ris:
#             continue

#         pheno_match = (
#             ris == bp.Emerging_Pheno_Flag
#             or ris == bp.Emerging_Pheno_Flag_Other
#         )

#         if bp.Emerging_Abx_Flag and pheno_match:
#             emerging_triggered = True
#             triggered_abx_codes.append(entry.ab_Retest_Abx_code)
#             triggered_phenotypes.append(ris)

#     # Update Emerging table
#     Emerging_Table.objects.update_or_create(
#         eme_primary_key=final,
#         defaults={
#             "eme_org_Flag": emerging_triggered,
#             "eme_abx_Flag": emerging_triggered,
#             "eme_abx_code_pheno": ", ".join(triggered_abx_codes),
#             "eme_abx_Phenotype": ", ".join(triggered_phenotypes),
#             "eme_ars_Org": final.f_ars_OrgCode or "",
#             "eme_spec_Type": (
#                 final.f_Spec_Type.Specimen_code
#                 if final.f_Spec_Type else ""
#             ),
#             "eme_spec_Num": final.f_Spec_Num or "",
#             "eme_Accession": final.f_AccessionNo,
#             "eme_Site_Code": final.f_SiteCode,
#         },
#     )


@receiver(post_save, sender=Final_AntibioticEntry)
def update_emerging_abx_flags(sender, instance, **kwargs):

    if not instance.ab_Retest_Abx_code:
        return

    final = instance.ab_idNum_f_referred

    retest_entries = Final_AntibioticEntry.objects.filter(
        ab_idNum_f_referred=final,
        ab_Retest_Abx_code__isnull=False
    )

    emerging_abx_triggered = False
    organism_triggered = False

    triggered_codes = []
    triggered_phenotypes = []

    for entry in retest_entries:

        bp = entry.ab_breakpoints_id.first()
        if not bp:
            continue

        ris = entry.ab_Retest_MIC_enRIS or entry.ab_Retest_Disk_enRIS
        if not ris:
            continue

        # Organism-level emerging
        if bp.Emerging_Org_Flag:
            organism_triggered = True

        # Phenotype match
        pheno_match = (
            ris == bp.Emerging_Pheno_Flag
            or ris == bp.Emerging_Pheno_Flag_Other
        )

        if bp.Emerging_Abx_Flag and pheno_match:
            emerging_abx_triggered = True
            triggered_codes.append(entry.ab_Retest_Abx_code)
            triggered_phenotypes.append(ris)

    if not Final_Data.objects.filter(pk=final.pk).exists():
        return

    emerging_obj, _ = Emerging_Table.objects.get_or_create(
        eme_primary_key=final
    )

    emerging_obj.eme_org_Flag = organism_triggered
    emerging_obj.eme_abx_Flag = emerging_abx_triggered

    emerging_obj.eme_abx_code_pheno = (
        ", ".join(triggered_codes) if triggered_codes else ""
    )

    emerging_obj.eme_abx_Phenotype = (
        ", ".join(triggered_phenotypes) if triggered_phenotypes else ""
    )

    emerging_obj.save()



@receiver(post_save, sender=Emerging_Table)
def sync_classification_from_emerging(sender, instance, **kwargs):

    is_fully = Emerging_Table.fully_emerging().filter(
        pk=instance.pk
    ).exists()

    Classification_Table.objects.update_or_create(
        Class_idNumReferred=instance.eme_primary_key,
        defaults={
            "Class_AccessionNo": instance.eme_Accession,
            "Class_Chk_Emerging": is_fully,
        },
    )


@receiver(post_save, sender=Final_Data)
def update_emerging_spec_flag(sender, instance, **kwargs):

    specimen = instance.f_Spec_Type

    spec_flag = False
    spec_code = ""

    if specimen:
        spec_flag = bool(specimen.Emerging_Spec_Flag)
        spec_code = specimen.Specimen_code

    

    emerging_obj, _ = Emerging_Table.objects.get_or_create(
        eme_primary_key=instance
    )

    emerging_obj.eme_Spec_Flag = spec_flag
    emerging_obj.eme_spec_Type = spec_code
    emerging_obj.eme_spec_Num = instance.f_Spec_Num or ""
    emerging_obj.eme_spec_Date = (
        instance.f_Spec_Date.strftime("%Y-%m-%d")
        if instance.f_Spec_Date else ""
    )

    emerging_obj.eme_Accession = instance.f_AccessionNo
    emerging_obj.eme_Site_Code = instance.f_SiteCode
    emerging_obj.eme_ars_Org = instance.f_ars_OrgCode or ""

    emerging_obj.save()



@receiver(post_save, sender=Final_Data)
def auto_update_snapshot_on_final_data_save(sender, instance, **kwargs):
    regenerate_concordance_snapshot(instance)


@receiver(post_save, sender=Final_AntibioticEntry)
def auto_update_snapshot_on_antibiotic_save(sender, instance, **kwargs):
    regenerate_concordance_snapshot(instance.ab_idNum_f_referred)


@receiver(post_delete, sender=Final_Data)
def delete_concordance_when_final_deleted(sender, instance, **kwargs):
    """
    If a Final_Data record is deleted,
    delete the ConcordanceReport for that batch.
    """

    batch = instance.f_Batch_id

    if batch:
        ConcordanceReport.objects.filter(batch=batch).delete()