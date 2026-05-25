# SOURCES.md — Research Notes per Data Source

---

## 1. SAP Fuel & Procurement

**Format researched:** SAP MB51 Material Document List (flat CSV via SE16 or MB51 transaction)

**What I learned:**
- SAP exports default to the system language. German SAP instances output column headers like `MENGE` (quantity), `MEINS` (unit of measure), `BUDAT` (posting date), `WERKS` (plant), `LIFNR` (vendor).
- Dates come in German format by default: `DD.MM.YYYY`. Some instances output `YYYYMMDD` (compact). We handle both.
- Quantities use European decimal notation: `1.234,56` (period as thousand separator, comma as decimal). We detect and normalize this.
- Units are inconsistent even within one export: `L`, `LT`, `Ltr`, `Litres` are all real values seen in production exports.
- Plant codes (`WERKS`) are 4-character codes meaningful only with a plant master lookup table. We store them and surface them to the analyst.

**What would break in real deployment:**
- Clients on S/4HANA may have custom fields or renamed standard fields
- IDoc-based integration (common for system-to-system) has a completely different structure — our CSV parser won't work
- Very large SAP exports (100K+ rows) would need streaming CSV parsing instead of loading the full file into memory

**Sample data design:** I used realistic Indian plant codes (PLNT-MUM, PLNT-DEL, etc.), real fuel types (Diesel EN590, LPG, Furnace Oil), and deliberately included rows with missing quantities, negative values, European number formatting, and an unconventional unit (GALLONS) to test the normalization pipeline.

---

## 2. Utility Electricity

**Format researched:** Portal CSV export (BESCOM, MSEDCL, Tata Power portal formats)

**What I learned:**
- Most utility portals let you download billing history as CSV. The column names vary but core fields are consistent: meter/account number, consumption (kWh), billing period start/end.
- Some portals export in MWh for high-tension connections (industrial consumers). We convert MWh → kWh.
- Billing periods don't align with calendar months. A bill might run Jan 3 to Feb 2. This is intentional — utilities stagger billing to distribute meter reading workload.
- Demand charges appear alongside consumption charges in the CSV. We track only consumption (kWh) since demand charges don't translate to emissions.
- Tariff codes (HT-II-A, LT-II, etc.) are utility-specific. We store them in `raw_data` but don't parse them.

**What would break in real deployment:**
- Different utilities have completely different column names — the column mapping approach works only if we maintain a per-utility mapping config
- Some utilities require PDF bill parsing (no CSV export) — Tesseract OCR would be needed
- Real-time smart meter data (15-minute intervals) would require a different ingestion model

**Sample data design:** I used Indian utility tariff codes (HT = high tension, LT = low tension), realistic consumption values for office/campus/data center use cases, and included rows with missing consumption, a negative reading (data entry error), and a MWh value to test conversion.

---

## 3. Corporate Travel

**Format researched:** Concur Travel "Expense Report" CSV export and Navan "Trip export" CSV

**What I learned:**
- Concur's export schema: Trip Date, Segment Type (Air/Hotel/Car), Origin/Destination airport codes, Distance, Fare, Vendor.
- Navan's export is similar but uses "Travel Type" instead of "Segment Type" and includes traveler department.
- Flights: IATA airport codes (BOM, DEL, LHR) are standard. Distance is sometimes provided, sometimes not — depends on the booking tool configuration.
- Hotels: billed per night. Emission factor for hotels depends on country (energy grid intensity varies). We store nights and country/city but don't compute an emission factor.
- Ground transport: distance in km or miles. Rental car vs. taxi vs. company car have different emission factors (ignored in this prototype).
- International flights sometimes come with miles instead of km. We convert.

**What would break in real deployment:**
- Traveler names/IDs need masking for GDPR in EU deployments
- Airport code → distance lookup requires an airport distance API (e.g., OpenFlights, DistanceFromTo) — we flag missing distances but don't fill them
- Multi-leg flights sometimes appear as one row, sometimes split by segment — our model assumes one row = one segment

**Sample data design:** I used realistic Indian corporate travel patterns (Mumbai-Delhi-Bangalore being the most common routes), included international trips (LHR, SIN, DXB), used real airline names, and deliberately added rows with missing distance, a negative distance (data error), and a mixed miles/km file.
