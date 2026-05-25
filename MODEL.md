# MODEL.md — Data Model and Design Rationale

## Core Design Decisions

### Single canonical table (`NormalizedRecord`)

All three sources — SAP fuel/procurement, utility electricity, and corporate travel — land in one table after normalization. The alternative was three separate tables (one per source). I chose a single table because:

1. **The review workflow is identical across sources.** An analyst approves or rejects a row. Having a single table lets the review UI, audit log, and status queries work without source-specific branching.
2. **Scope tagging replaces source-specific tables.** The GHG Protocol scopes (1, 2, 3) already segment records by emissions category. We don't need a separate table for that.
3. **Source-specific fields go in `raw_data` (JSONField).** This avoids a fat table with 20+ nullable columns. The downside is that you can't filter on source-specific fields at the DB level without JSON queries — acceptable for a 4-day prototype.

If this were a production system with 10M+ rows, we'd consider partitioning the table by source or scope.

---

### Multi-tenancy: Scope 1/2/3 categorization

The `scope` field is an explicit string enum ("1", "2", "3") per GHG Protocol. Source-to-scope mapping at ingestion time:

| Source   | Default Scope | Exception |
|----------|--------------|-----------|
| SAP      | Scope 1 (direct combustion) | Scope 2 if material description = electricity/power |
| Utility  | Scope 2 (purchased energy) | None |
| Travel   | Scope 3, Category 6 (business travel) | None |

In a production system, scope assignment would be driven by a material master lookup table (SAP uses MATNR codes). We don't have that, so we use description-matching as a proxy.

---

### Source-of-truth tracking

Every `NormalizedRecord` has a FK to `IngestionBatch`. The batch records:
- Which file was uploaded
- When and by whom
- How many rows were in it
- How many were flagged suspicious

This means you can always trace a normalized record back to the original upload event. Deleting a batch cascades to delete its records.

---

### Raw values preserved

For each record, we store both the raw value from the CSV (`raw_quantity`, `raw_unit`, `raw_date`) and the normalized version (`quantity`, `unit`, `activity_date`). This is important for:
1. Debugging: an analyst can see exactly what came in vs. what we produced
2. Auditability: auditors may want to inspect the source data
3. Re-processing: if our normalization logic changes, we can recompute without re-ingesting

---

### Unit normalization target set

After normalization, all records should have one of: `L`, `kWh`, `km`, `kg`. Conversions:
- MWh → kWh (× 1000)
- miles → km (× 1.60934)
- gallons → L (× 3.78541)
- metric tonnes → kg (× 1000)

Units like `nights` (hotel stays) are stored as-is with a flag, since there's no meaningful conversion.

---

### Audit trail (`AuditLog`)

The audit log is append-only (no updates). Each row records:
- Record ID (not a FK, to survive record deletion)
- Action (ingested / approved / rejected / flagged)
- Previous and new status
- Who performed it and when
- Optional note

Keeping record_id as an integer (not FK) means the audit log is preserved even if the record is deleted — important for compliance.

---

## Schema Diagram (simplified)

```
IngestionBatch
  id, source, filename, uploaded_at, uploaded_by, row_count, suspicious_count

NormalizedRecord
  id, batch_id → IngestionBatch
  source, scope, activity_date
  quantity, unit
  site_code, entity_name
  raw_quantity, raw_unit, raw_date, raw_data (JSON)
  status, is_suspicious, flag_reasons (JSON array)
  reviewed_by, reviewed_at, review_note
  ingested_at

AuditLog
  id, record_id (int), batch_id (int), source
  action, performed_by, note, timestamp
  previous_status, new_status
```
