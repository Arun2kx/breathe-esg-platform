"""
Utility electricity ingestion service.

We chose the portal CSV export format (not PDF bill, not API) because:
- PDF parsing requires OCR and is fragile across utility providers
- Most utility portals (BESCOM, Tata Power, MSEDCL, etc.) do offer CSV export
- The API option requires OAuth tokens per-account which varies per utility

Key challenges handled here:
- Billing periods that span two calendar months
- Meter IDs vs account numbers vs location names
- Mixed kWh / MWh readings
- Demand charges vs consumption charges (we only track consumption)
"""

from __future__ import annotations
import csv
import io
from decimal import Decimal
from typing import Optional

from ingestion.models import IngestionBatch, NormalizedRecord
from utils.normalizers import normalize_date, normalize_unit, normalize_quantity, compute_flags


COLUMN_MAP = {
    "meter_id": ["meter id", "meter_id", "meter number", "account number", "account no", "consumer no"],
    "location": ["location", "site", "site name", "premise", "address", "facility"],
    "period_start": ["period start", "billing period start", "from date", "start date", "from"],
    "period_end": ["period end", "billing period end", "to date", "end date", "to"],
    "consumption": ["consumption", "units consumed", "kwh", "energy consumed", "usage", "net consumption"],
    "unit": ["unit", "uom", "unit of measure"],
    "tariff": ["tariff", "rate", "tariff code", "tariff type"],
    "amount": ["amount", "bill amount", "charges", "total amount"],
}


def _find_column(headers: list[str], key: str) -> Optional[str]:
    aliases = COLUMN_MAP.get(key, [])
    for h in headers:
        if h.strip().lower() in aliases:
            return h
    return None


def ingest_utility_csv(file_obj, filename: str, uploaded_by: str = "analyst") -> dict:
    """
    Parse a utility portal CSV export.
    Billing periods are split to the period_start date for activity_date.
    """
    content = file_obj.read()
    text = content.decode("utf-8-sig") if isinstance(content, bytes) else content

    reader = csv.DictReader(io.StringIO(text))
    headers = reader.fieldnames or []
    col = {key: _find_column(headers, key) for key in COLUMN_MAP}

    batch = IngestionBatch.objects.create(
        source=IngestionBatch.Source.UTILITY,
        filename=filename,
        uploaded_by=uploaded_by,
    )

    records_to_create = []
    suspicious_count = 0

    for row in reader:
        warnings = []

        # Use period_start as the canonical date.
        # Billing periods don't align with calendar months, so we record the start
        # rather than inventing a month boundary.
        raw_date = row.get(col["period_start"], "") if col["period_start"] else ""
        if not raw_date and col.get("period_end"):
            raw_date = row.get(col["period_end"], "")

        activity_date, date_warn = normalize_date(raw_date)
        if date_warn:
            warnings.append(date_warn)

        # Unit: default to kWh for utility data if not specified
        raw_unit = row.get(col["unit"], "kWh") if col["unit"] else "kWh"
        if not raw_unit.strip():
            raw_unit = "kWh"

        unit, unit_warn = normalize_unit(raw_unit)
        if unit_warn:
            warnings.append(unit_warn)

        raw_qty = row.get(col["consumption"], "") if col["consumption"] else ""
        quantity, unit, qty_warn = normalize_quantity(raw_qty, unit)
        if qty_warn:
            warnings.append(qty_warn)

        meter_id = row.get(col["meter_id"], "").strip() if col["meter_id"] else ""
        location = row.get(col["location"], "").strip() if col["location"] else ""

        required = {"date": raw_date, "consumption": raw_qty}
        is_suspicious, flag_reasons = compute_flags(quantity, unit, activity_date, required, warnings)

        if is_suspicious:
            suspicious_count += 1

        records_to_create.append(
            NormalizedRecord(
                batch=batch,
                source=IngestionBatch.Source.UTILITY,
                scope=NormalizedRecord.Scope.SCOPE_2,
                activity_date=activity_date,
                quantity=quantity,
                unit=unit or raw_unit,
                site_code=meter_id,
                entity_name=location,
                raw_quantity=str(raw_qty),
                raw_unit=str(raw_unit),
                raw_date=str(raw_date),
                raw_data=dict(row),
                is_suspicious=is_suspicious,
                flag_reasons=flag_reasons,
            )
        )

    NormalizedRecord.objects.bulk_create(records_to_create)

    batch.row_count = len(records_to_create)
    batch.suspicious_count = suspicious_count
    batch.save(update_fields=["row_count", "suspicious_count"])

    return {
        "batch_id": batch.id,
        "source": "utility",
        "total_rows": len(records_to_create),
        "suspicious_rows": suspicious_count,
    }
