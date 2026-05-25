"""
Normalization utilities for ESG data ingestion.

These functions handle the messy reality of enterprise data:
- SAP exports with German column names and inconsistent units
- Utility CSVs with non-calendar billing periods
- Travel exports with airport codes but no distances

Design decision: keep these as pure functions (no DB access) so they're
easy to test and reuse across all three ingestion pipelines.
"""

from __future__ import annotations
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional


# ---------------------------------------------------------------------------
# Unit normalisation
# ---------------------------------------------------------------------------

# Map every variant we've seen in real SAP / utility exports to a canonical unit.
# L  = litres, kWh = kilowatt-hours, km = kilometres, kg = kilograms, t = metric tonnes
UNIT_ALIASES: dict[str, str] = {
    # Litres
    "l": "L",
    "lt": "L",
    "ltr": "L",
    "ltrs": "L",
    "litre": "L",
    "litres": "L",
    "liter": "L",
    "liters": "L",
    # Kilowatt-hours
    "kwh": "kWh",
    "kw-h": "kWh",
    "kilowatt-hour": "kWh",
    "kilowatt hours": "kWh",
    "kilowatt-hours": "kWh",
    # Megawatt-hours (converted to kWh below)
    "mwh": "MWh",
    "megawatt-hour": "MWh",
    "megawatt hours": "MWh",
    # Kilometres
    "km": "km",
    "kms": "km",
    "kilometres": "km",
    "kilometers": "km",
    "kilometre": "km",
    # Miles (converted to km below)
    "mi": "mi",
    "miles": "mi",
    "mile": "mi",
    # Kilograms
    "kg": "kg",
    "kgs": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    # Metric tonnes
    "t": "t",
    "mt": "t",
    "tonne": "t",
    "tonnes": "t",
    "metric ton": "t",
    "metric tons": "t",
    # Gallons (US – show up in US-sourced SAP exports)
    "gal": "gal",
    "gals": "gal",
    "gallon": "gal",
    "gallons": "gal",
}

# Units we convert to a base unit at ingestion time.
# Value is (target_unit, multiplier_to_apply_to_quantity).
CONVERSIONS: dict[str, tuple[str, float]] = {
    "MWh": ("kWh", 1000.0),
    "mi": ("km", 1.60934),
    "gal": ("L", 3.78541),
    "t": ("kg", 1000.0),
}

SUPPORTED_UNITS = {"L", "kWh", "km", "kg"}  # canonical units after conversion


def normalize_unit(raw: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """
    Returns (canonical_unit, warning_message).
    warning_message is None if everything is fine.
    """
    if not raw or not str(raw).strip():
        return None, "missing unit"

    cleaned = str(raw).strip().lower()
    canonical = UNIT_ALIASES.get(cleaned)

    if canonical is None:
        return raw, f"unrecognised unit '{raw}'"

    return canonical, None


def normalize_quantity(
    raw: Optional[str | float | int],
    unit: Optional[str],
) -> tuple[Optional[Decimal], Optional[str], Optional[str]]:
    """
    Returns (quantity_decimal, final_unit, warning_message).

    Handles unit conversion (MWh → kWh, miles → km, etc.) in addition to
    parsing the raw value.
    """
    if raw is None or str(raw).strip() == "":
        return None, unit, "missing quantity"

    # Strip common thousand-separators from SAP exports (e.g. "1.234,56")
    raw_str = str(raw).strip().replace(" ", "")
    # European decimal notation: "1.234,56" → "1234.56"
    if re.match(r"^\d{1,3}(\.\d{3})*(,\d+)?$", raw_str):
        raw_str = raw_str.replace(".", "").replace(",", ".")

    try:
        qty = Decimal(raw_str)
    except InvalidOperation:
        return None, unit, f"unparseable quantity '{raw}'"

    if qty < 0:
        return qty, unit, "negative quantity"

    # Apply unit conversion if needed
    if unit in CONVERSIONS:
        target_unit, multiplier = CONVERSIONS[unit]
        qty = qty * Decimal(str(multiplier))
        unit = target_unit

    # Flag implausibly large values – these are almost always data entry errors.
    # Thresholds are intentionally generous; the goal is to catch obvious problems.
    LARGE_VALUE_THRESHOLDS = {
        "L": Decimal("500000"),    # 500,000 litres in a single row
        "kWh": Decimal("1000000"),  # 1 GWh in a single row
        "km": Decimal("100000"),   # 100,000 km in a single entry
        "kg": Decimal("500000"),   # 500 tonnes in a single row
    }
    if unit in LARGE_VALUE_THRESHOLDS and qty > LARGE_VALUE_THRESHOLDS[unit]:
        return qty, unit, f"abnormally large value ({qty} {unit})"

    return qty, unit, None


# ---------------------------------------------------------------------------
# Date normalisation
# ---------------------------------------------------------------------------

# Date formats we encounter in the wild. Order matters – try most specific first.
DATE_FORMATS = [
    "%Y-%m-%d",        # ISO 8601 (preferred)
    "%d/%m/%Y",        # UK/EU style
    "%m/%d/%Y",        # US style
    "%d-%m-%Y",
    "%Y%m%d",          # SAP compact format
    "%d.%m.%Y",        # German/European SAP exports
    "%B %d, %Y",       # "January 01, 2024"
    "%b %d, %Y",       # "Jan 01, 2024"
    "%d %B %Y",        # "01 January 2024"
    "%Y/%m/%d",
]


def normalize_date(raw: Optional[str]) -> tuple[Optional[date], Optional[str]]:
    """
    Returns (parsed_date, warning_message).
    Tries a list of known formats before giving up.
    """
    if not raw or not str(raw).strip():
        return None, "missing date"

    raw_str = str(raw).strip()

    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw_str, fmt).date(), None
        except ValueError:
            continue

    return None, f"unparseable date '{raw_str}'"


# ---------------------------------------------------------------------------
# Suspicious row detection
# ---------------------------------------------------------------------------

def compute_flags(
    quantity: Optional[Decimal],
    unit: Optional[str],
    activity_date: Optional[date],
    required_fields: dict,
    warnings: list[str],
) -> tuple[bool, list[str]]:
    """
    Returns (is_suspicious, list_of_flag_reasons).

    Called after normalisation so we work with clean values where possible.
    Warnings accumulated during normalisation are passed in and included.
    """
    flags: list[str] = list(warnings)  # include normalisation warnings

    # Missing required fields
    missing = [k for k, v in required_fields.items() if v is None or str(v).strip() == ""]
    if missing:
        flags.append(f"missing required fields: {', '.join(missing)}")

    # Quantity issues
    if quantity is not None and quantity < 0:
        if not any("negative" in f for f in flags):
            flags.append("negative quantity")

    # Unit issues
    if unit is not None and unit not in SUPPORTED_UNITS:
        if not any("unit" in f for f in flags):
            flags.append(f"unsupported unit: {unit}")

    is_suspicious = len(flags) > 0
    return is_suspicious, flags
