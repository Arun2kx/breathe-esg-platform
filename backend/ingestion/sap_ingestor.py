"""
SAP fuel and procurement ingestion service.

Real SAP exports (IDoc flat file or OData CSV) look nothing like tutorial data.
We chose the flat CSV export format (transaction ME2M / MB51) because:
1. It's the most common format clients actually provide
2. IDoc parsing requires SAP middleware we don't have
3. BAPI calls need RFC connectivity which is out of scope for 4 days

Column mapping handles the most common SAP export column names including
German variants (SAP defaults to the system language).
"""

from __future__ import annotations
import csv
import io
from decimal import Decimal
from typing import Optional

from django.utils import timezone

from ingestion.models import IngestionBatch, NormalizedRecord
from utils.normalizers import (
    normalize_date,
    normalize_unit,
    normalize_quantity,
    compute_flags,
)


# SAP exports have inconsistent column names depending on the transaction,
# language setting, and client customization. We map every variant we know.
COLUMN_MAP = {
    "quantity": ["menge", "quantity", "qty", "amount", "liefermenge", "bestellmenge"],
    "unit": ["meins", "unit", "uom", "unit of measure", "einheit", "basismengeneinheit"],
    "date": [
        "budat", "bldat", "posting date", "document date", "datum", "buchungsdatum",
        "date", "movement date",
    ],
    "material": ["matnr", "material", "material number", "material no", "materialnummer"],
    "plant": ["werks", "plant", "plant code", "werk"],
    "supplier": ["lifnr", "vendor", "supplier", "lieferant", "vendor name"],
    "description": ["maktx", "material description", "description", "bezeichnung"],
    "document": ["mblnr", "ebeln", "document", "po number", "material document"],
}


def _find_column(headers: list[str], key: str) -> Optional[str]:
    """Return the actual CSV header that matches our canonical field name."""
    aliases = COLUMN_MAP.get(key, [])
    for h in headers:
        if h.strip().lower() in aliases:
            return h
    return None


def ingest_sap_csv(file_obj, filename: str, uploaded_by: str = "analyst") -> dict:
    """
    Parse a SAP CSV export and persist normalised records.
    Returns a summary dict with counts and any row-level errors.
    """
    content = file_obj.read()
    if isinstance(content, bytes):
        # SAP exports are often latin-1 encoded, not UTF-8
        for encoding in ("utf-8-sig", "latin-1", "cp1252"):
            try:
                text = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            text = content.decode("utf-8", errors="replace")
    else:
        text = content

    reader = csv.DictReader(io.StringIO(text))
    headers = reader.fieldnames or []

    # Map canonical fields to actual column names
    col = {key: _find_column(headers, key) for key in COLUMN_MAP}

    batch = IngestionBatch.objects.create(
        source=IngestionBatch.Source.SAP,
        filename=filename,
        uploaded_by=uploaded_by,
    )

    records_to_create = []
    row_errors = []
    suspicious_count = 0

    for i, row in enumerate(reader, start=2):  # start=2 because row 1 is headers
        warnings = []

        # --- Date ---
        raw_date = row.get(col["date"], "") if col["date"] else ""
        activity_date, date_warn = normalize_date(raw_date)
        if date_warn:
            warnings.append(date_warn)

        # --- Unit ---
        raw_unit = row.get(col["unit"], "") if col["unit"] else ""
        unit, unit_warn = normalize_unit(raw_unit)
        if unit_warn:
            warnings.append(unit_warn)

        # --- Quantity ---
        raw_qty = row.get(col["quantity"], "") if col["quantity"] else ""
        quantity, unit, qty_warn = normalize_quantity(raw_qty, unit)
        if qty_warn:
            warnings.append(qty_warn)

        # --- Context fields ---
        plant = row.get(col["plant"], "").strip() if col["plant"] else ""
        supplier = row.get(col["supplier"], "").strip() if col["supplier"] else ""
        description = row.get(col["description"], "").strip() if col["description"] else ""

        # Scope 1: direct combustion (fuel)
        # We assume SAP fuel exports are Scope 1 unless the material description
        # suggests electricity purchasing (Scope 2). A real implementation would
        # use a material master lookup table.
        scope = NormalizedRecord.Scope.SCOPE_1
        if description.lower() in ("electricity", "strom", "power"):
            scope = NormalizedRecord.Scope.SCOPE_2

        required = {
            "date": raw_date,
            "quantity": raw_qty,
            "unit": raw_unit,
        }
        is_suspicious, flag_reasons = compute_flags(quantity, unit, activity_date, required, warnings)

        if is_suspicious:
            suspicious_count += 1

        records_to_create.append(
            NormalizedRecord(
                batch=batch,
                source=IngestionBatch.Source.SAP,
                scope=scope,
                activity_date=activity_date,
                quantity=quantity,
                unit=unit or raw_unit,
                site_code=plant,
                entity_name=supplier or description,
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
        "source": "sap",
        "total_rows": len(records_to_create),
        "suspicious_rows": suspicious_count,
        "errors": row_errors,
    }
