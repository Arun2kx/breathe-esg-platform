# TRADEOFFS.md — Three Things I Deliberately Did Not Build

---

## 1. CO₂e calculation and emission factors

**What it would be:** Apply IPCC/GHG Protocol emission factors to convert activity data (litres of diesel, kWh of electricity, km of flight) into CO₂-equivalent tonnes. Display scope-wise emissions totals on the dashboard.

**Why I didn't build it:**
Emission factors are not simple lookup tables. The right factor depends on:
- Fuel type and purity (diesel from different refineries has different carbon content)
- Grid emission factor (varies by state in India — BESCOM's grid is cleaner than Jharkhand's)
- Flight class and aircraft type (economy vs. business doubles per-km emissions)
- Country-year combination (factors change annually as the grid gets greener)

Building this correctly requires a maintained emission factor database (DEFRA, IEA, or GreenShield). Hard-coding IPCC 2006 values would produce numbers that look precise but aren't defensible. I'd rather show no CO₂e number than show a wrong one to an auditor.

**What I'd do next sprint:** Integrate with DEFRA's emission factor dataset as a lookup service. Store the factor version used alongside each calculation so results are reproducible.

---

## 2. Multi-tenant data isolation

**What it would be:** Client separation at the database level — each enterprise client's data is isolated so one client can't see another's records.

**Why I didn't build it:**
Multi-tenancy adds complexity in two ways: schema isolation (separate schemas per tenant, harder to maintain) or row-level isolation (tenant_id on every table, easy to mess up and expose data). For a 4-day prototype with a single client in mind, the risk doesn't exist yet. Adding it prematurely would slow down the model iteration without benefit.

**What I'd do before production:** Add a `tenant_id` field to `IngestionBatch` and `NormalizedRecord`, enforce it at the API serializer level (filter by tenant on every query), and add a composite index on `(tenant_id, source, status)`.

---

## 3. Re-ingestion / change tracking for updated source files

**What it would be:** If a client re-sends a corrected version of a file they already uploaded, detect which rows changed, update them, and preserve the history of the change.

**Why I didn't build it:**
This requires either row-level deduplication keys (SAP document number + line item, utility meter ID + period) or a diff-based comparison between the new file and the existing batch. SAP document numbers are a reasonable key for fuel records, but utility and travel exports don't have stable unique row identifiers. Building a reliable deduplication strategy would take more time than the scope allows.

**Current behavior:** Re-uploading a file creates a new batch with new records. The analyst can reject the duplicate batch. Not ideal, but safe — it never silently overwrites data.

**What I'd do next sprint:** Define a composite natural key per source (e.g., SAP: `MBLNR + line_item`, Utility: `meter_id + period_start`, Travel: `traveler + date + origin + destination`) and implement an upsert with conflict detection on that key.
