# EDX FSU / FSA Handler & Shipment FSU DocType — Implementation Plan

> **Goal:** Add inbound EDX message handlers for **FSU/14** (Functional Status Update) and its
> structural sibling **FSA/14** (Freight Status Advice), both Cargo-IMP, built as parser-only
> handlers with one `EDX Message Definition` each. FSA reuses the FSU parser (§12). The shared
> target for both is the new **`Shipment FSU`** DocType (§3–§7), which stores all parsed status events
> keyed by AWB. FSU/FSA never write to the parent `Shipment`.
>
> Implemented entirely inside the existing EDX framework — **no engine/core changes**.
>
> **Canonical references (in `awbix/edx/.claude/`):**
> - `FSU.csv` — field spec: ref # · M/O · element name · format · DE# · fixed value
> - `FSU.md` — formatted documentation by section
> - `FSU.xlsx` — Excel workbook version
> - `fsu sample.txt` — real FSU/14 message sample

---

## 1. What FSU is, and how it differs from FWB

| | FWB | FSU |
|---|---|---|
| Meaning | One Air Waybill (Master) | Shipment status/movement record |
| Target DocType | `Shipment` | `Shipment FSU` |
| Top line | `FWB/16` | `FSU/14` |
| Direction | Inbound & Outbound | **Inbound only** (no composer) |
| Repeating segments | — | Status/movement/handling records |

FSU is a **functional status update**: one message reports status events (RCS, DEP, ARR, BKD, DLV,
etc.) for a single AWB. Many FSU messages over time all key to the **same** `Shipment FSU` document,
each adding a new status event row. The parser reads and stores these events; no outbound/composer
capability exists.

### FSU message anatomy (from `fsu sample.txt`)

```
FSU/14                                           ← Ref 1    message id + version
157-53806270HKGNLU/P2K505.0T10                  ← Ref 2    AWB ref (prefix-serial, O&D, qty/wt)
FIW/QR8403/20JUN1039/DOH/P2K505.0/S0720/A1008  ← Ref 3.1+ status detail block
  OCI/HK/ISS/RA/28490                           ← Ref 3.x  customs/compliance info
  /HK//SS/SPX                                   ← Ref 3.x  continuation lines
ULD/PMC72534QR/PMC77313QR                       ← Ref 3.x  ULD detail (repeatable)
```

---

## 2. File Layout

```
awbix/edx/handlers/fsu/
├── __init__.py                  # empty (package marker)
├── fsu_parser.py                # FSUParser(BaseParser)      — inbound parser
├── fsa_parser.py                # FSAParser(FSUParser)       — FSA sibling (§12)
└── test_fsu_parser.py           # FrappeTestCase (parse + validate + process; covers FSU & FSA)

awbix/shipment/doctype/shp_fsu/
├── __init__.py                  # empty (package marker)
├── shp_fsu.json                 # schema definition
└── shp_fsu.py                   # Shipment FSU Document class

awbix/shipment/doctype/shp_fsu_status_record/
├── __init__.py
└── shp_fsu_status_record.json   # child table for repeating status events
```

**Reuse `awbix/edx/handlers/fwb/cargoimp.py` as-is** — the line tokenizer (`normalize`,
`tokenize`, `by_code`, `first`, `continuation_text`, `segment`, `join`) is message-agnostic and
already shared by FWB/FNA/FMA.

---

## 3. Shipment FSU DocType — Data Model

**Name** (primary key): `awb_number` (e.g., `157-53806270`) — the air waybill extracted from FSU
message line 1. Ensures one `Shipment FSU` document per AWB; many FSU/FSA messages merge into it.

**Link to Shipment** (optional): `shipment` (Link → `Shipment`). Linked if the master Shipment
already exists; otherwise left blank (FSU may arrive before Shipment creation). Never auto-created.
The `shipment` link is **reference-only** — FSU/FSA never write to `Shipment` fields.

**Core scalar fields:**

| Fieldname | Type | Cond | Notes |
|---|---|---|---|
| `awb_number` | Data | M | Primary key; IATA format `PREFIX-SERIAL` |
| `shipment` | Link → Shipment | O | Reference only; `Shipment` is never written to |
| `origin` | Link → Airport | M | AWB origin (from consignment line) |
| `destination` | Link → Airport | M | AWB destination |
| `status_code` | Data | O | **Latest** status code (free `Data`, not `Select` — see §5) |
| `handling_information` | Text | O | Free-text handling data |
| `last_updated` | Datetime | R | Auto-set on each save via `validate()` |
| `raw_message` | Long Text | O | Full raw FSU message; audit trail; read-only after insert |

**Child table:**
- `fsu_status_records` (Table → `Shipment FSU Status Record`) — one row per status event; the timeline
  accumulates across FSU/FSA messages for the same AWB.

---

## 4. Shipment FSU DocType — Validations

**Mandatory on every save:**
- `awb_number`: IATA format — prefix (1–3 digits) + dash + 8-digit serial; digit 8 must equal
  `int(serial[:7]) % 7` (IATA CSC Res. 600a). **Not a digit-sum** — must match the parser exactly
  (see §9 cross-plan note), or messages that pass `validate()` will throw on `process.save()`.
- `origin ≠ destination` when both are present.

**Auto-set:**
- `last_updated` = `frappe.utils.now()` on each save.

**Not validated here:**
- `status_code` is free `Data` — real Cargo-IMP messages use codes such as `FIW`, `BKD`, `DLV`
  that are not in a fixed list; a `Select` would reject valid messages.

---

## 5. Shipment FSU DocType — Permissions

| Role | Read | Write | Create | Delete |
|---|---|---|---|---|
| `System Manager` | ✓ | ✓ | ✓ | ✓ |
| `awbix-admin` | ✓ | ✓ | ✓ | ✓ |
| `awbix-user` | ✓ | — | — | — |

Submit/Amend: not applicable (DocType is not workflow-enabled). The parser sets
`doc.flags.ignore_permissions = True` so pipeline writes always succeed.

---

## 6. Shipment FSU — JSON Schema (`shp_fsu.json`)

```json
{
  "doctype": "DocType",
  "name": "Shipment FSU",
  "module": "Shipment",
  "document_type": "Document",
  "autoname": "field:awb_number",
  "editable_grid": 0,
  "engine": "InnoDB",
  "track_changes": 0,
  "fields": [
    {
      "fieldname": "awb_number",
      "label": "AWB Number",
      "fieldtype": "Data",
      "unique": 1,
      "reqd": 1,
      "search_index": 1,
      "description": "Master air waybill number (e.g., 157-53806270)"
    },
    {
      "fieldname": "shipment",
      "label": "Shipment",
      "fieldtype": "Link",
      "options": "Shipment",
      "reqd": 0
    },
    {
      "fieldname": "origin",
      "label": "Origin",
      "fieldtype": "Link",
      "options": "Airport",
      "reqd": 1
    },
    {
      "fieldname": "destination",
      "label": "Destination",
      "fieldtype": "Link",
      "options": "Airport",
      "reqd": 1
    },
    {
      "fieldname": "status_code",
      "label": "Status Code",
      "fieldtype": "Data",
      "reqd": 0,
      "description": "Latest status code (RCS, BKD, DEP, ARR, DLV, FIW, …). Free Data — a Select would reject valid Cargo-IMP codes."
    },
    {
      "fieldname": "handling_information",
      "label": "Handling Information",
      "fieldtype": "Text",
      "reqd": 0
    },
    {
      "fieldname": "last_updated",
      "label": "Last Updated",
      "fieldtype": "Datetime",
      "read_only": 1
    },
    {
      "fieldname": "raw_message",
      "label": "Raw FSU Message",
      "fieldtype": "Long Text",
      "reqd": 0,
      "read_only": 1
    },
    {
      "fieldname": "fsu_status_records",
      "label": "Status Records",
      "fieldtype": "Table",
      "options": "Shipment FSU Status Record",
      "reqd": 0
    }
  ],
  "permissions": [
    {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1},
    {"role": "awbix-admin",    "read": 1, "write": 1, "create": 1, "delete": 1},
    {"role": "awbix-user",     "read": 1, "write": 0, "create": 0, "delete": 0}
  ]
}
```

---

## 7. Shipment FSU — Python Class (`shp_fsu.py`) and Child Table

### `shp_fsu.py`

```python
import frappe
from frappe.model.document import Document


class SHPFsu(Document):
	def validate(self):
		self._validate_awb_number()
		self._validate_route()
		self._update_timestamp()

	def _validate_awb_number(self):
		if not self.awb_number or "-" not in self.awb_number:
			frappe.throw("AWB Number must be in format PREFIX-SERIAL (e.g., 157-53806270)")

		parts = self.awb_number.split("-")
		if len(parts) != 2:
			frappe.throw("AWB Number must contain exactly one dash")

		prefix, serial = parts
		if not prefix.isdigit() or not (1 <= len(prefix) <= 3):
			frappe.throw("AWB prefix must be 1–3 digits")

		if len(serial) != 8 or not serial.isdigit():
			frappe.throw("AWB serial must be exactly 8 digits")

		# IATA CSC Res. 600a: digit 8 = int(serial[:7]) % 7 — NOT a digit-sum.
		# Must match FSUParser.validate() exactly (§9 cross-plan note).
		check_digit = int(serial[7])
		expected_check = int(serial[:7]) % 7
		if check_digit != expected_check:
			frappe.throw(f"AWB check digit incorrect: expected {expected_check}, got {check_digit}")

	def _validate_route(self):
		if self.origin and self.destination and self.origin == self.destination:
			frappe.throw("Origin and Destination cannot be the same")

	def _update_timestamp(self):
		self.last_updated = frappe.utils.now()
```

### `shp_fsu_status_record.json` (child table)

```json
{
  "doctype": "DocType",
  "name": "Shipment FSU Status Record",
  "module": "Shipment",
  "document_type": "Child",
  "istable": 1,
  "editable_grid": 1,
  "fields": [
    {"fieldname": "status_code",      "label": "Status Code",      "fieldtype": "Data",     "reqd": 1, "in_list_view": 1},
    {"fieldname": "status_timestamp", "label": "Status Timestamp", "fieldtype": "Datetime", "reqd": 1, "in_list_view": 1},
    {"fieldname": "location",         "label": "Location",         "fieldtype": "Link",     "options": "Airport", "in_list_view": 1},
    {"fieldname": "flight_number",    "label": "Flight Number",    "fieldtype": "Data"},
    {"fieldname": "carrier_code",     "label": "Carrier Code",     "fieldtype": "Data"},
    {"fieldname": "description",      "label": "Description",      "fieldtype": "Text"}
  ]
}
```

> The natural upsert key for event deduplication (§8.4 step 3) is `(status_code, status_timestamp,
> location)`. A row is appended only when that triple isn't already present, so re-processing the
> same FSU message is a no-op.

---

## 8. Parser — `fsu_parser.py` (`FSUParser(BaseParser)`)

`message_type = "FSU"`, `version = "14"`. Implements the four `BaseParser` hooks (`parse`,
`business_key`, `validate`, `process`). `parse`, `business_key`, `validate` are **pure** (no
DB/network); only `process` writes.

### 8.1 `parse(raw) -> dict`

Output shape:
```python
{
  "message":       {"type": "FSU", "version": "14"},
  "awb_reference": {"awb_number": "157-53806270", "origin": "HKG", "destination": "NLU"},
  "fsu_data":      {"status_code": "FIW", "handling_info": "…", "movement_records": […]},
  "raw_detail":    "<full raw>",
  "segments_seen": ["FIW", "OCI", "ULD"],
}
```

Steps:

0. **Strip the Type-B telex preamble.** Real FSU messages arrive wrapped:
   ```
   QD SIN05XH
   .HDQFMQR 200739
   FSU/14          ← actual SMI
   ```
   `cargoimp.tokenize()` expects line[0] to be the SMI. Drop everything before it:
   ```python
   _SMI_RE = re.compile(r"^(?:FSU|FSA)/\d", re.MULTILINE)

   def _strip_preamble(raw: str) -> str:
       m = _SMI_RE.search(raw or "")
       return raw[m.start():] if m else (raw or "")
   ```
   Works for both FSU and FSA (subclass reuse); also safe when no envelope is present.

1. `t = cargoimp.tokenize(_strip_preamble(raw))`
2. Parse line[0]: message id/version (`FSU/14`).
3. Parse line[1] as AWB reference. Origin & destination are **optional** (FSU.md §2.2 = O):
   ```python
   _AWB_RE = re.compile(r"^(\d{1,3})-(\d{8})(?:([A-Z]{3})([A-Z]{3}))?(?:/(.*))?$")
   ```
   A valid AWB with no O&D must parse without raising `AWB_REF`.
4. Walk remaining segments. Treat the status-code set as **open**: the sample's `FIW` is not in
   `FSU.md`'s status table — store any unrecognized code verbatim rather than rejecting it.

Keep per-field parsing defensive (`raw_*` fallbacks) so malformed lines surface in `validate`,
not as parse exceptions.

### 8.2 `business_key(data) -> str`

Return `data["awb_reference"]["awb_number"]` (e.g. `"157-53806270"`). One AWB = one `Shipment FSU`
document; many FSU messages over time accumulate into it.

### 8.3 `validate(data) -> list[dict]`

Pure pre-checks; mirrors FWB's issue shape `{level, code, field, message}`:

| Check | Level | Code |
|---|---|---|
| Message id/version present | Error | `MESSAGE_ID` |
| AWB prefix + serial present (O&D may be absent) | Error | `AWB_REF` |
| AWB serial 8 digits + `int(serial[:7]) % 7` check digit | Error | `AWB_SERIAL` / `AWB_CHECKDIGIT` |
| At least one FSU segment present | Warning | `NO_DATA` |
| Origin ≠ destination (only when both present) | Warning | `ROUTE` |

> **Check digit: `int(serial[:7]) % 7` — not a digit-sum.** Must match `Shipment FSU._validate_awb_number()`
> exactly (§9 cross-plan note). A digit-sum gives a different result and would reject valid AWBs.

### 8.4 `process(data, message_in) -> str`

Idempotent create-or-update:

1. **Link reference `Shipment` only if it exists** — never create it:
   ```python
   if frappe.db.exists("Shipment", awb_number):
       doc.shipment = awb_number
   ```
   FSU legitimately arrives before the Shipment; an auto-created blank Shipment would fail its
   own `validate()`. Mirrors the FMA/FNA `apply_ack` rule.

2. **Ensure `Airport` lookup records** exist for every airport the parser sets (origin, destination,
   movement airports) using the `_ensure` create-if-missing guard. Skip plain `Data` fields.

3. **Find or create `Shipment FSU`** by `awb_number`, then **merge** this message's events:
   - `frappe.db.exists("Shipment FSU", awb_number)` → use it; else `frappe.new_doc("Shipment FSU")`.
   - Set/refresh scalar fields (`awb_number`, `origin`, `destination`, `raw_message`,
     `last_updated`, latest `status_code`).
   - **Do not rebuild the status child table.** FSU is an additive stream; clearing rows would
     erase history. Instead **upsert by natural key** `(status_code, status_timestamp, location)`:
     append only when that triple is not already present. Re-processing the same message is a no-op.

4. `doc.flags.ignore_permissions = True; doc.save()` — triggers `Shipment FSU.validate()`.

5. Return the **AWB number** (the `Shipment FSU` name) on success. A falsy return → pipeline marks
   *Needs Review*.

---

## 9. Amendment Handling — `bypass_amendment`

FSU runs with `bypass_amendment: 1`, so it follows the engine's annotation path
(`pipeline._process_annotation`): **no `EDX Delivery` ledger, no stale guard** — every message
reaches `process()`.

This is correct because FSU is an additive stream, not a replaceable snapshot. The
`_amendment_decision` stale guard (built for FWB) would mark a late-arriving older event
*Superseded* and silently drop it. FSU needs every event, including out-of-order arrivals.

Idempotency comes from the **event-level upsert** in `process` §8.4 step 3.

**Cross-plan consistency (blocks end-to-end processing if violated):**
1. **Check digit:** `Shipment FSU._validate_awb_number()` uses `int(serial[:7]) % 7` (not a
   digit-sum), identical to `FSUParser.validate()`. If they diverge, messages that pass the parser
   will throw on `doc.save()` and fail processing.
2. **`status_code` field:** stored as free `Data`, not constrained `Select`, so real codes (`FIW`,
   `BKD`, `DLV`, etc.) are accepted.

---

## 10. Registration — `EDX Message Definition` (`install.py`)

Add two dicts to `_DEFINITIONS` in `awbix/edx/install.py` (seeded idempotently by `after_migrate`):

```python
{
    "message_type": "FSU",
    "version": "14",
    "title": "FSU/14 — Functional Status Update (Cargo-IMP)",
    "standard": "Cargo-IMP",
    "parser_class": "awbix.edx.handlers.fsu.fsu_parser.FSUParser",
    "composer_class": None,
    "target_doctype": "Shipment FSU",
    "is_parser_enabled": 1,
    "is_composer_enabled": 0,
    "auto_promote": 1,
    "auto_process": 1,
    "detection_pattern": "^FSU/14",
    "bypass_amendment": 1,
},
{
    "message_type": "FSA",
    "version": "14",
    "title": "FSA/14 — Freight Status Advice (Cargo-IMP)",
    "standard": "Cargo-IMP",
    "parser_class": "awbix.edx.handlers.fsu.fsa_parser.FSAParser",
    "composer_class": None,
    "target_doctype": "Shipment FSU",
    "is_parser_enabled": 1,
    "is_composer_enabled": 0,
    "auto_promote": 1,
    "auto_process": 1,
    "detection_pattern": "^FSA/14",
    "bypass_amendment": 1,
},
```

`classify` iterates `enabled_parser_definitions()` and returns the first pattern that matches;
`^FSU/14` and `^FSA/14` are anchored per line (`re.MULTILINE | re.IGNORECASE`) and do not collide
with `^FWB/16`, `^FHL/5`, `^FMA`, `^FNA`. Classification works on the wrapped message (Type-B
envelope still present); the parser strips it internally (§8.1 step 0).

---

## 11. FSA/14 — Sibling Status Handler

FSA/14 is structurally identical to FSU/14: same Cargo-IMP version, same consignment-detail line,
and the same repeating status sections per `FSA.csv`. It writes to the **same `Shipment FSU` target**.

### 11.1 `fsa_parser.py`

```python
from awbix.edx.handlers.fsu.fsu_parser import FSUParser


class FSAParser(FSUParser):
    message_type = "FSA"
    version = "14"
    # parse / business_key / validate / process inherited unchanged.
```

Two generalizations already required in `FSUParser` so the subclass needs no overrides:
- `_strip_preamble` uses `^(?:FSU|FSA)/\d` (already specified in §8.1).
- `parse` sets `message.type`/`version` from `self.message_type`/`self.version`, not hard-coded
  literals.

`business_key` is still the AWB number, so FSU and FSA messages for the same AWB funnel into the
**one** `Shipment FSU` document.

### 11.2 Tests (FSA-specific, added to `test_fsu_parser.py`)

Using the sample (`fsa simple.md`):
```
FSA/14
157-41266466DOHLHR/T60K1428
DLV/24MAY1223/LHR/T60K1428/DART AIR SERVICES LTD
```

- `FSAParser().parse(...)` → `message.type == "FSA"`, `business_key == "157-41266466"`,
  origin `DOH` / destination `LHR`, `DLV` event with date `24MAY`, time `1223`, location `LHR`.
- `process` creates/updates `Shipment FSU` for `157-41266466`; a subsequent FSU for the same AWB merges
  into the same document (shared-target, history-accumulation test).
- AWB check digit: `int("4126646") % 7 == 6` = digit 8. ✓

---

## 12. Tests — `test_fsu_parser.py`

| Test | What it asserts |
|---|---|
| **G1 — Envelope** | Raw sample with `QD …` / `.HDQFMQR …` preamble parses to `message.id == "FSU/14"` and correct AWB. Regression for `_strip_preamble`. |
| **G2 — Parse pure** | Sample `157-53806270HKGNLU…` → correct message, AWB ref, `business_key`. |
| **G3 — Optional O&D** | AWB line with no origin/destination parses and does **not** raise `AWB_REF`. |
| **G4 — Validate** | Valid data → no issues; bad serial → `AWB_CHECKDIGIT`; no FSU data → `NO_DATA` warning. |
| **G5 — Check digit algorithm** | Confirm `int(serial[:7]) % 7`, not digit-sum, is used. |
| **G6 — Process (DB)** | Parse + process sample → `Shipment FSU` exists; `shipment` blank (no Shipment seeded); no Shipment auto-created. Re-process same message → no duplicate rows. |
| **G7 — History merge** | Process two different status messages for same AWB (FIW then BKD) → `Shipment FSU` retains both events. |
| **G8 — Open status code** | `FIW` (absent from FSU.md status table) stored verbatim, not rejected. |
| **G9 — FSA parse** | `FSAParser` on FSA sample → `message.type == "FSA"`, correct AWB. |
| **G10 — FSA shared target** | FSA process followed by FSU process for same AWB → one `Shipment FSU` with both events. |
| **Negative** | Malformed AWB ref, bad check digit, missing required segments. |

```bash
bench run-tests awbix.edx.handlers.fsu.test_fsu_parser
```

---

## 13. Build Order

Each step should leave migrations clean and tests green before proceeding.

1. **Create `Shipment FSU` DocType**: `shp_fsu.json`, `shp_fsu.py`, `__init__.py`.

2. **Create `Shipment FSU Status Record` child table**: `shp_fsu_status_record.json`, `__init__.py`.

3. `bench migrate` — creates both new tables.

4. **Scaffold** `handlers/fsu/__init__.py` + skeleton parser (NotImplemented bodies).

5. **Implement `parse` + `business_key`** (incl. `_strip_preamble`); pure parse tests (G1–G3).

6. **Implement `validate`**; negative-case tests (G4–G5).

7. **Register definitions** in `install.py`; `bench migrate`; confirm `classify` detects `^FSU/14`
   on staged sample.

8. **Implement `process`** (link Shipment if exists; ensure Airports; event-level upsert);
   DB-backed process tests (G6–G8).

9. **Add FSA subclass** (`fsa_parser.py`); FSA tests (G9–G10). `bench migrate`.

10. **Docs:** update `edx_implemented.md` and EDX strategy doc for FSU and FSA. Run
    `ruff check . && ruff format .` and `pre-commit run --all-files`.

---

## 14. Out of Scope

- Outbound FSU/FSA composition — inbound only.
- Any write-back to the parent `Shipment` — including `flight_bookings` and all other fields.
  The optional `shipment` link is reference-only; all status data lives solely in `Shipment FSU`.
- Auto-creation of new `Shipment` documents if FSU/FSA arrives first — stored in `Shipment FSU` with
  a blank `shipment` link; manual reconciliation required.
- Workflow/approval for `Shipment FSU` (no submit/amend; read-only status records).
- Custom reports/dashboards on FSU/FSA data (future; basic list view sufficient for v1).
- Multi-part message reassembly across physical messages — single-message only.

---

## Appendix A — FSU/14 Message Sample (`fsu sample.txt`)

```
QD SIN05XH
.HDQFMQR 200739
FSU/14
157-53806270HKGNLU/P2K505.0T10
FIW/QR8403/20JUN1039/DOH/P2K505.0/S0720/A1008
OCI/HK/ISS/RA/28490
/HK//SS/SPX
/HK//SM/XRY
/HK//SN/XING WEIJI
/HK//SD/18JUN262100
ULD/PMC72534QR/PMC77313QR
```

**Line-by-line:**
- `FSU/14` — message type/version
- `157-53806270HKGNLU/P2K505.0T10` — AWB `157-53806270`, origin `HKG`, destination `NLU`,
  qty/weight `P2K505.0`, total indicator `T10`
- `FIW/…` — Free In & Out status block with flight ref, date, location (DOH), quantity, handling
- `OCI/…` — customs/compliance info + continuation lines
- `ULD/…` — two PMC pallets (repeatable)

---

## Appendix B — FSU/14 Field Specification Summary

Complete definitions in `FSU.csv` / `FSU.md` / `FSU.xlsx` (`awbix/edx/.claude/`).

**Key structural sections:**
1. **§1 Standard Message Identification** — SMI `FSU/14`, separators
2. **§2 Consignment Detail** — AWB prefix-serial (M), O&D (O), quantity/weight (O)
3. **§3–§22 Status Details** — one section per status code, each containing:
   - Status code (fixed value per section)
   - Movement date/time and airport
   - Quantity/weight at status (optional)
   - Party name (optional)
   - Volume/density (optional)
   - Special handling & remarks (optional)
   - Equipment/ULD detail (repeatable)
   - OCI customs detail (repeatable)
4. **§23 OCI** — country, identifier, supplementary customs info
5. **§24 ULD** — ULD type, serial, owner, loading indicator
6. **§25 OSI** — Other Service Information (up to 65 chars)

**Data format codes:**
- `nnn` = numeric 3 digits; `n[8]` = exactly 8 digits; `aaa` = alphabetic 3 chars;
- `mm` = alphanumeric 2 chars (carrier code); `n[...7]p` = decimal weight/volume;
- `t[...35]` = text up to 35 chars
