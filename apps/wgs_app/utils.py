# egasp/utils.py
import os
import re
from apps.home.models import SiteData

def format_accession(raw_name: str) -> str:
    """
    Given a raw file path like:
      '/path/18ARS-BGH0055-20220426A.fna'
    Returns a normalized accession:
      '18ARS_BGH0055'
    Rules:
      - Must contain 'ARS'
      - Find known site codes from SiteData
      - Drop other non-site parts (like STC)
    """
    if not raw_name:
        return ""

    # Load site codes from DB (e.g. JLM, BGH, CVM, etc.)
    site_codes = set(SiteData.objects.values_list("SiteCode", flat=True))

    # Extract filename without extension
    base = os.path.basename(raw_name)
    base_noext = os.path.splitext(base)[0].strip()

    if "ARS" not in base_noext:
        return ""

    parts = re.split(r"[-_]", base_noext)
    if not parts:
        return ""

    prefix = parts[0]  # e.g. "18ARS"

    # Case 1: Look for SITE#### where SITE matches SiteData
    for part in parts[1:]:
        m = re.match(r"^([A-Za-z]{2,6})(\d+)$", part)
        if m:
            letters, digits = m.group(1).upper(), m.group(2)
            if letters in site_codes:
                return f"{prefix}_{letters}{digits}"

    # Case 2: SITE code alone, then look ahead for digits
    for i in range(1, len(parts)):
        part = parts[i].upper()
        if part in site_codes:
            digits = ""
            if i + 1 < len(parts):
                next_part = parts[i + 1]
                m2 = re.match(r"^([A-Za-z]{2,6})(\d+)$", next_part)
                if m2:
                    digits = m2.group(2)
                else:
                    dmatch = re.search(r"(\d+)", next_part)
                    if dmatch:
                        digits = dmatch.group(1)
            return f"{prefix}_{part}{digits}" if digits else f"{prefix}_{part}"

    return ""
