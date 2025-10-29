from django import template
from operator import attrgetter

register = template.Library()

@register.filter
def dict_lookup(dictionary, key):
    """Safely retrieve a value from a dictionary using a key."""
    if isinstance(dictionary, dict):
        return dictionary.get(key, None)
    return None

@register.filter
def get_item(dictionary, key):
    """Retrieve a value from a dictionary using a key."""
    return dictionary.get(key, None)

@register.filter
def make_tuple(value1, value2):
    """Creates a tuple with two values."""
    return (value1, value2)

# @register.simple_tag
# def get_existing_value(existing_entries, entry_id, value_type):
#     """
#     Retrieves the existing value for a given breakpoint entry.
#     """
#     # entry = existing_entries.filter(ab_breakpoints_id=entry_id).first()
#     entry = existing_entries.filter(ab_breakpoints_id__in=[entry_id]).first()

#     if entry:
#         if value_type == 'disk':
#             return entry.ab_Disk_value 
#         elif value_type == 'mic':
#             return entry.ab_MIC_value
#         elif value_type == 'retest_disk':
#             return entry.ab_Retest_DiskValue
#         elif value_type == 'retest_mic':
#             return entry.ab_Retest_MICValue
#         elif value_type == 'mic_operand':
#             return entry.ab_MIC_operand or ''
#         elif value_type == 'retest_mic_operand':
#             return entry.ab_Retest_MIC_operand or ''
#         elif value_type == 'alert_mic':
#             return entry.ab_AlertMIC
#         elif value_type == 'retest_alert_mic':
#             return entry.ab_Retest_AlertMIC
#         # for encoded RIS values
#         elif value_type == 'disk_enris':
#             return entry.ab_Disk_enRIS
#         elif value_type == 'mic_enris':
#             return entry.ab_MIC_enRIS
#         elif value_type == 'retest_disk_enris':
#             return entry.ab_Retest_Disk_enRIS
#         elif value_type == 'retest_mic_enris':
#             return entry.ab_Retest_MIC_enRIS
#     return ''


# @register.simple_tag
# def get_existing_value(existing_entries, entry_id, value_type):
#     """
#     Retrieves the existing value for a given breakpoint entry.
#     Supports main and retest antibiotics.
#     """
#     # Try to fetch main entry first
#     entry = existing_entries.filter(ab_breakpoints_id=entry_id, ab_Abx_code__isnull=False).first()

#     # If not found, try retest entry
#     if not entry:
#         entry = existing_entries.filter(ab_breakpoints_id=entry_id, ab_Retest_Abx_code__isnull=False).first()
    
#     if entry:
#         if value_type == 'disk':
#             return entry.ab_Disk_value or ''
#         elif value_type == 'mic':
#             return entry.ab_MIC_value or ''
#         elif value_type == 'retest_disk':
#             return entry.ab_Retest_DiskValue or ''
#         elif value_type == 'retest_mic':
#             return entry.ab_Retest_MICValue or ''
#         elif value_type == 'mic_operand':
#             return entry.ab_MIC_operand or ''
#         elif value_type == 'retest_mic_operand':
#             return entry.ab_Retest_MIC_operand or ''
#         elif value_type == 'alert_mic':
#             return entry.ab_AlertMIC
#         elif value_type == 'retest_alert_mic':
#             return entry.ab_Retest_AlertMIC
#         elif value_type == 'disk_enris':
#             return entry.ab_Disk_enRIS or ''
#         elif value_type == 'mic_enris':
#             return entry.ab_MIC_enRIS or ''
#         elif value_type == 'retest_disk_enris':
#             return entry.ab_Retest_Disk_enRIS or ''
#         elif value_type == 'retest_mic_enris':
#             return entry.ab_Retest_MIC_enRIS or ''
#     return ''



@register.simple_tag
def get_existing_value(existing_entries, identifier, value_type):
    """
    Retrieves the existing value for a given antibiotic entry.
    Supports both Breakpoints-linked entries (by ID)
    and Antibiotic_List entries (by Whonet_Abx string).
    Also supports both main and retest antibiotic fields.
    """

    # --- Try to detect identifier type ---
    entry = None
    if str(identifier).isdigit():
        # Numeric = BreakpointsTable ID
        entry = existing_entries.filter(ab_breakpoints_id=identifier).first()
    else:
        # String = Whonet_Abx code (e.g., "AMC_ND20")
        entry = existing_entries.filter(ab_Abx_code=identifier).first()
        if not entry:
            entry = existing_entries.filter(ab_Retest_Abx_code=identifier).first()

    # --- If found, return appropriate field ---
    if entry:
        match value_type:
            case 'disk':
                return entry.ab_Disk_value or ''
            case 'mic':
                return entry.ab_MIC_value or ''
            case 'retest_disk':
                return entry.ab_Retest_DiskValue or ''
            case 'retest_mic':
                return entry.ab_Retest_MICValue or ''
            case 'mic_operand':
                return entry.ab_MIC_operand or ''
            case 'retest_mic_operand':
                return entry.ab_Retest_MIC_operand or ''
            case 'alert_mic':
                return entry.ab_AlertMIC
            case 'retest_alert_mic':
                return entry.ab_Retest_AlertMIC
            case 'disk_enris':
                return entry.ab_Disk_enRIS or ''
            case 'mic_enris':
                return entry.ab_MIC_enRIS or ''
            case 'retest_disk_enris':
                return entry.ab_Retest_Disk_enRIS or ''
            case 'retest_mic_enris':
                return entry.ab_Retest_MIC_enRIS or ''
            case _:
                return ''
    return ''



@register.filter
def multi_sort(queryset, fields):
    fields = fields.split(',')
    return sorted(queryset, key=attrgetter(*fields))

@register.filter 
def getattr(obj, attr_name):
    """Template filter to dynamically get object attribute."""
    return getattr(obj, attr_name, "")
