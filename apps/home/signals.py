from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import AntibioticEntry, Referred_Data
import re

def determine_ris(value, r_breakpoint, i_breakpoint, s_breakpoint, sdd_breakpoint, is_disk=False):
    # Ensure value and at least one of the breakpoints are provided
    if value is not None and (r_breakpoint is not None or s_breakpoint is not None or i_breakpoint is not None or sdd_breakpoint is not None):
         # Convert breakpoint values from string to numbers
        try:
            value = int(value) if is_disk else float(value)  # Convert to int for disk, float otherwise
        except ValueError:
            return None  # Handle cases where the value cannot be converted

        # Check if the intermediate breakpoint is a range (e.g., "24-27")
        if i_breakpoint is not None:
            try:
                if "-" in str(i_breakpoint):
                    lower, upper = map(int if is_disk else float, str(i_breakpoint).split("-"))
                    if lower <= value <= upper:
                        return "I"
                else:
                    i_breakpoint = int(i_breakpoint) if is_disk and i_breakpoint and i_breakpoint.strip().isdigit() else float(i_breakpoint) if i_breakpoint else None
                    if value == i_breakpoint:
                        return "I"
            except ValueError:
                pass

      # For SDD breakpoint
        if sdd_breakpoint is not None:
            try:
                sdd_breakpoint = int(sdd_breakpoint) if is_disk and sdd_breakpoint and sdd_breakpoint.strip().isdigit() else float(sdd_breakpoint) if sdd_breakpoint else None
            except ValueError:
                return None  # Return None if conversion fails
            
            if value == sdd_breakpoint:
                return "SDD"

            
        # If both r_breakpoint and s_breakpoint are provided, compare the value
        if r_breakpoint is not None and s_breakpoint is not None:
            try:
                r_breakpoint = int(r_breakpoint) if is_disk and r_breakpoint and r_breakpoint.strip().isdigit() else float(r_breakpoint) if r_breakpoint else None
                s_breakpoint = int(s_breakpoint) if is_disk and s_breakpoint and s_breakpoint.strip().isdigit() else float(s_breakpoint) if s_breakpoint else None
            except ValueError:
                return None  # Handle cases where the breakpoints cannot be converted
            if is_disk:
                if value <= r_breakpoint:
                    return "R"  
                elif value >= s_breakpoint:
                    return "S" 
                else:
                    return "I"  # Intermediate if value is between the two breakpoints
            else:
                if value >= r_breakpoint: # if MIC antibiotic
                    return "R"
                elif value <= s_breakpoint:
                    return "S"
                else:
                    return "I"
            
        # If only s_breakpoint is provided, use it for comparison
        if s_breakpoint is not None:
            try:
                 s_breakpoint = int(s_breakpoint) if is_disk and s_breakpoint and s_breakpoint.strip().isdigit() else float(s_breakpoint) if s_breakpoint else None
            except ValueError:
                return None  # Handle cases where the breakpoint cannot be converted
            if is_disk:
                if value >= s_breakpoint:
                    return "S"  
                else:
                    return "R"
            else:
                if value <= s_breakpoint: #if MIC antibiotic
                    return "S"
                else:
                    return "R"
        # If only r_breakpoint is provided, use it for comparison
        if r_breakpoint is not None:
            try:
                 r_breakpoint = int(r_breakpoint) if is_disk and r_breakpoint and r_breakpoint.strip().isdigit() else float(r_breakpoint) if r_breakpoint else None
            except ValueError:
                return None  # Handle cases where the breakpoint cannot be converted
            if is_disk:
                if value <= r_breakpoint:
                    return "R"  
                else:
                    return "S"
            else:
                if value >= r_breakpoint: #if MIC antibiotic
                    return "R"
                else:
                    return "S"
        return None  # Return None if no valid interpretation can be made








@receiver(post_save, sender=AntibioticEntry)
def update_ris_interpretation(sender, instance, **kwargs):
    updated_fields = []

    # Retrieve the BreakpointsTable entry associated with the AntibioticEntry
    breakpoint_entry = instance.ab_breakpoints_id.first()
    is_disk = breakpoint_entry.Disk_Abx if breakpoint_entry else False

    # Update ab_Disk_RIS
    print(f"{instance.ab_Antibiotic}: MIC={instance.ab_MIC_value}, Disk={instance.ab_Disk_value}, Retest={instance.ab_Retest_DiskValue},Retest={instance.ab_Retest_MICValue},"
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






