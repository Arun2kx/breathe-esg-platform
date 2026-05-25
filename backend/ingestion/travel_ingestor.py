"""
Corporate travel ingestion service (flights, hotels, ground transport).

Platform research: Concur Travel and Navan both expose exports as CSV.
Concur's "Expense Report" export and Navan's "Trip export" have different schemas.
We handle both by mapping common column names.

Key challenges:
- Flights: distance is often absent, only airport codes given.
  We store origin/destination codes and note that distance estimation would
  require an airport-distance API (not in scope for this prototype).
- Hotels: nights × emission_factor, location matters (grid intensity varies).
- Ground transport: mode determines emission factor category.

Scope 3 for all travel (Category 6: Business travel per GHG Protocol).
"""

from __future__ import annotations
import csv
import io
from typing import Optional

from ingestion.models import IngestionBatch, NormalizedRecord
from utils.normalizers import normalize_date, normalize_unit, normalize_quantity, compute_flags


COLUMN_MAP = {
    "travel_date": ["travel date", "departure date", "date", "trip date", "check-in date", "booking date"],
    "traveler": ["traveler", "traveller", "employee", "employee name", "name", "passenger"],
    "travel_type": ["travel type", "type", "mode", "transport mode", "category", "segment type"],
    "origin": ["origin", "from", "departure", "departure city", "origin airport"],
    "destination": ["destination", "to", "arrival", "arrival city", "destination airport"],
    "distance": ["distance", "distance (km)", "distance km", "miles", "km"],
    "distance_unit": ["distance unit", "unit", "uom"],
    "nights": ["nights", "hotel nights", "num nights", "duration (nights)"],
    "cost": ["cost", "amount", "fare", "total cost", "spend"],
    "cost_currency": ["currency", "cost currency"],
    "vendor": ["vendor", "airline", "hotel", "carrier", "hotel name", "provider"],
    "department": ["department", "cost center", "dept", "cost centre"],
}


def _find_column(headers: list[str], key: str) -> Optional[str]:
    aliases = COLUMN_MAP.get(key, [])
    for h in headers:
        if h.strip().lower() in aliases:
            return h
    return None


def ingest_travel_csv(file_obj, filename: str, uploaded_by: str = "analyst") -> dict:
    content = file_obj.read()
    text = content.decode("utf-8-sig") if isinstance(content, bytes) else content

    reader = csv.DictReader(io.StringIO(text))
    headers = reader.fieldnames or []
    col = {key: _find_column(headers, key) for key in COLUMN_MAP}

    batch = IngestionBatch.objects.create(
        source=IngestionBatch.Source.TRAVEL,
        filename=filename,
        uploaded_by=uploaded_by,
    )

    records_to_create = []
    suspicious_count = 0

    for row in reader:
        warnings = []

        raw_date = row.get(col["travel_date"], "") if col["travel_date"] else ""
        activity_date, date_warn = normalize_date(raw_date)
        if date_warn:
            warnings.append(date_warn)

        travel_type = row.get(col["travel_type"], "").strip().lower() if col["travel_type"] else ""
        origin = row.get(col["origin"], "").strip() if col["origin"] else ""
        destination = row.get(col["destination"], "").strip() if col["destination"] else ""
        vendor = row.get(col["vendor"], "").strip() if col["vendor"] else ""
        traveler = row.get(col["traveler"], "").strip() if col["traveler"] else ""

        # Determine quantity:
        # - Flights: distance in km (if available) or number of segments (1)
        # - Hotels: number of nights
        # - Ground: distance in km
        raw_qty = ""
        raw_unit = ""

        if travel_type in ("hotel", "accommodation", "lodging"):
            raw_qty = row.get(col["nights"], "1") if col["nights"] else "1"
            raw_unit = "nights"
            # nights is not in our standard unit set – store as-is, flag for analyst
            unit = "nights"
            quantity, _, qty_warn = normalize_quantity(raw_qty, None)
            if qty_warn:
                warnings.append(qty_warn)
        else:
            raw_qty = row.get(col["distance"], "") if col["distance"] else ""
            raw_unit_val = row.get(col["distance_unit"], "km") if col["distance_unit"] else "km"
            raw_unit = raw_unit_val if raw_unit_val.strip() else "km"

            unit, unit_warn = normalize_unit(raw_unit)
            if unit_warn:
                warnings.append(unit_warn)

            quantity, unit, qty_warn = normalize_quantity(raw_qty, unit)
            if qty_warn:
                warnings.append(qty_warn)

            # If no distance provided, we still record the trip but flag it.
            if not raw_qty:
                warnings.append("distance not provided – emission factor cannot be applied")

        required = {"date": raw_date, "type": travel_type}
        is_suspicious, flag_reasons = compute_flags(quantity, unit, activity_date, required, warnings)

        if is_suspicious:
            suspicious_count += 1

        records_to_create.append(
            NormalizedRecord(
                batch=batch,
                source=IngestionBatch.Source.TRAVEL,
                scope=NormalizedRecord.Scope.SCOPE_3,
                activity_date=activity_date,
                quantity=quantity,
                unit=unit or raw_unit,
                site_code=f"{origin}→{destination}" if origin or destination else "",
                entity_name=vendor or traveler,
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
        "source": "travel",
        "total_rows": len(records_to_create),
        "suspicious_rows": suspicious_count,
    }
