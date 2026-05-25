# DECISIONS.md — Every Ambiguity I Resolved

This document records the decisions made during implementation and what I'd ask the PM if we had more time.

---

## 1. SAP export format: flat CSV, not IDoc or BAPI

**Decision:** Implement CSV (MB51 / ME2M export) ingestion only.

**Why:** SAP exposes data through multiple mechanisms:
- IDoc flat file: used for system-to-system integration; requires an EDI parser
- BAPI/RFC calls: require SAP RFC SDK and network connectivity to the SAP system
- OData service: available in S/4HANA but requires API credentials and client-specific setup
- CSV export: available in every SAP version via transaction MB51 or SE16; no special access needed

For client onboarding where we don't have system-level SAP access, CSV is the realistic choice.

**What I'd ask the PM:** "Do your clients have direct SAP system access or do they always send file exports? If they have direct access, OData is better and I'd prioritize that next."

---

## 2. Utility data: portal CSV, not PDF bill parsing

**Decision:** Accept portal CSV export only.

**Why:** PDF bill parsing requires OCR (Tesseract or a paid API) and is fragile — every utility has a different PDF layout. Portal CSV exports are standardized enough that a column-mapping approach works. Most major Indian utilities (MSEDCL, BESCOM, TPDDL) offer CSV export.

**Ignored:** API ingestion (some utilities offer real-time API) — too many credentials to manage for a prototype.

---

## 3. Billing periods don't align with calendar months — I use period_start

**Decision:** Use `period_start` as `activity_date` rather than inventing a month split.

**Why:** A billing period might run 03/Jan to 02/Feb. Splitting this into Jan/Feb proportions requires assumptions about daily consumption patterns we don't have. Using period_start is honest about what we know.

**Implication for reporting:** Monthly aggregation reports will show slightly off numbers for cross-month bills. In a production system, you'd want a proper period → calendar-month allocation.

---

## 4. Travel: store trips without distance when distance is absent

**Decision:** Ingest the trip record but flag it as suspicious if distance is missing.

**Why:** Concur and Navan both sometimes omit distance from exports, especially for hotel stays and ad-hoc ground transport. The trip still happened; we don't want to silently drop it. An analyst can review and decide whether to reject or approve with a note.

**What I'd ask the PM:** "Do you want me to call an airport-distance API (like OpenFlights) to fill in missing distances, or is that out of scope?"

---

## 5. Scope assignment is heuristic, not master-data-driven

**Decision:** SAP materials are Scope 1 by default; we check the material description for "electricity" or "strom" to reclassify as Scope 2.

**Why:** A real implementation would use a material master table (MATNR → emission category). We don't have that, so we use description-matching.

**Risk:** This will misclassify edge cases (e.g., a material called "Diesel Generator for Electricity Production" would stay Scope 1 even though the end use is power generation). Acceptable for prototype; real deployment needs the master table.

---

## 6. No authentication in the prototype

**Decision:** No login, fixed reviewer identity "analyst".

**Why:** Implementing auth in 4 days would consume time better spent on the data model and normalization logic. The reviewer identity is a string field in the request body — easy to wire up to real auth later.

**What I'd ask the PM:** "What's the reviewer team size? If there are 3+ analysts reviewing simultaneously, auth is needed before launch."

---

## 7. Suspicious flag is based on data quality, not emissions magnitude

**Decision:** "Suspicious" means data quality issues (missing fields, negative values, unsupported units, abnormally large values), not whether the emission number seems high.

**Why:** We don't have emissions benchmarks to compare against — that would require industry-specific emission factors and historical baselines. Data quality flags are objective and explainable.

---

## 8. Deployment: single Postgres, no Redis/Celery

**Decision:** Synchronous file processing, no task queue.

**Why:** For files under 20 MB (our upload limit), synchronous processing takes < 2 seconds. Adding Celery would require Redis and worker processes — significant operational overhead for a prototype. If files grow to 100K+ rows, async processing would be necessary.
