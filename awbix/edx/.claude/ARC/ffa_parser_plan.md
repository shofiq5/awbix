# FFA Parser — Implementation Plan

**Target:** `awbix/edx/handlers/ffa/ffa_parser.py`
**Mirrors:** `awbix/edx/handlers/fwb/fwb16_parser.py`
**Spec:** `awbix/edx/.claude/FFA.md`
**Date:** 2026-06-23

---

## 1. What FFA Is and How It Differs from FWB

An FFA (AWB Space Allocation Answer) is an **inbound amendment** message sent by an airline in response to an FFR booking request. It carries the airline's verdict on requested space: confirmed (KK), rejected (UU), wait-listed (LL), on hold (HK/HL/HN), flight doesn't operate (UN), etc.

Key differences from FWB:

| Dimension | FWB (create/update Shipment) | FFA (amend flight bookings only) |
|---|---|---|
| Target | Creates or fully replaces a `Shipment` | Only updates `flight_bookings` child rows on an *existing* Shipment |
| Segment codes | Named Cargo-IMP codes (FLT, RTG, SHP, …) | Positional: AWB line, then bare flight lines, then SSR/OSI/REF/SRI |
| Flight structure | Carrier + flight + day only | Carrier + flight + day + month + dep airport + arr airport + **space allocation code** |
| Mandatory REF | Optional (sender_reference) | **Mandatory** — the booking reference from the corresponding FFR |

---

## 2. Message Grammar

### 2.1 Wire Format (from FFA.md §7)

```
FFA/{version}                                                   ← segment 1 (mandatory)
{prefix}-{serial}{origin}{dest}/{desc}{pieces}{wt}{[/goods][/sph...]}  ← segment 2 (mandatory)
{carrier}{flight}/{day}{month}/{dep}{arr}/{space_code}          ← segment 3 (mandatory, repeatable)
SSR/{text}[/{text}]                                             ← segment 4 (optional, 1-2 lines)
OSI/{text}[/{text}]                                             ← segment 5 (optional, 1-2 lines)
REF/{office_addr}[/{file_ref}]                                  ← segment 6 (mandatory)
SRI/{ref}[/{supp1}[/{supp2}]]                                   ← segment 7 (optional)
```

### 2.2 Real Examples Cross-Reference

| Example | AWB line | Flight lines | Notes |
|---|---|---|---|
| 6.1 | `125-1234565FRAPHL/T12K950/BOOKS /VAL` | `BA171/19MAR/LHRJFK/KK` | Goods + SHC, KK confirm |
| 6.2 | `057-12345675BHXJFK/T5K400` | `AF077/19MAY/CDGJFK/UU` | File ref in REF |
| 6.8 | `160-76543213HKGYSB/T4K160` | `AC857/19MAR/LHRYYZ/KK`, `AC363/20MAR/YYZYSB/UU` | Multi-flight |
| 6.9 | `021-77777770MSPLHR/P5K5750T9` | `AA001/19MAR/JFKLHR/KK` | SSR + OSI + SRI |
| 6.10 | `020-12345675FRAJFK/T20K800` | `LH404/02JUN/FRAJFK/KK` | SRI time-definite service |

### 2.3 AWB Line Regex

The AWB line in FFA is identical to FWB except version 4 examples show 7-digit serials (spec typo; modern format is 8 digits):

```python
_AWB_RE = re.compile(
    r"^(\d{1,3})-(\d{7,8})([A-Z]{3})([A-Z]{3})(?:/(.*))?$"
)
# groups: (prefix, serial, origin, dest, rest)
```

Quantity detail (in `rest`):

```python
_CONSIGNMENT_RE = re.compile(
    r"^(?P<desc>[TP])(?P<pieces>\d{1,4})(?P<wt_code>[KL])(?P<weight>\d+(?:\.\d+)?)"
    r"(?:(?P<total_desc>T)(?P<total_pieces>\d{1,4}))?"  # conditional 2.4 (P-type ULDs)
)
```

After the quantity block, slant-delimited tokens are either:
- A goods description (≤15 chars, not all-alpha or mixed) — section 2.5
- A special handling code (exactly 3 uppercase alpha chars) — section 2.7, up to 9

### 2.4 Flight Line Regex

FFA flight lines are not prefixed with a Cargo-IMP segment code. They follow section 3's exact format:

```python
_FLIGHT_RE = re.compile(
    r"^([A-Z0-9]{2})(\d{3,4}[A-Z]?)/(\d{2})([A-Z]{3})/([A-Z]{3})([A-Z]{3})/([A-Z]{2})$"
)
# groups: (carrier, flight_number, day, month, dep_airport, arr_airport, space_code)
```

### 2.5 REF Line Formats (section 6)

```
REF/{office}{func}{company}[/{file_ref}]        ← 6.3 present, 7-8 chars
REF//{file_ref}[/{pid}/{pcode}/{airport}]        ← 6.6 present (starts with //)
```

```python
_REF_OFFICE_RE = re.compile(r"^([A-Z]{3}[A-Z]{2}[A-Z0-9]{2})(?:/(.{0,15}))?$")
_REF_PART_RE   = re.compile(r"^/(.{0,15})(?:/([A-Z0-9]{1,3})/([A-Z0-9]{1,17})/([A-Z]{3}))?$")
```

---

## 3. File Layout

```
awbix/edx/handlers/ffa/
    __init__.py          ← empty (already exists or create)
    ffa_parser.py        ← NEW — inbound FFA parser
    ffa_composer.py      ← exists — outbound FFA composer (no changes needed)
```

---

## 4. `FFAParser` Class

### 4.1 Skeleton

```python
# awbix/edx/handlers/ffa/ffa_parser.py
import re
import frappe
from awbix.edx.engine.base_parser import BaseParser
from awbix.edx.handlers.fwb import cargoimp

_AWB_RE       = re.compile(r"^(\d{1,3})-(\d{7,8})([A-Z]{3})([A-Z]{3})(?:/(.*))?$")
_CONSIGNMENT_RE = re.compile(
    r"^(?P<desc>[TP])(?P<pieces>\d{1,4})(?P<wt_code>[KL])(?P<weight>[\d.]+)"
    r"(?:(?P<total_desc>T)(?P<total_pieces>\d{1,4}))?"
)
_FLIGHT_RE    = re.compile(
    r"^([A-Z0-9]{2})(\d{3,4}[A-Z]?)/(\d{2})([A-Z]{3})/([A-Z]{3})([A-Z]{3})/([A-Z]{2})$"
)
_MONTHS = {"JAN":1,"FEB":2,"MAR":3,"APR":4,"MAY":5,"JUN":6,
           "JUL":7,"AUG":8,"SEP":9,"OCT":10,"NOV":11,"DEC":12}
_VALID_ALLOC  = {"NN","NA","SS","CA","XX","HK","HL","HN","KK","UU","UN","LL"}
_SHC_RE       = re.compile(r"^[A-Z]{3}$")


class FFAParser(BaseParser):
    message_type = "FFA"
    version = "6"

    def parse(self, raw: str) -> dict: ...
    def business_key(self, data: dict) -> str | None: ...
    def validate(self, data: dict) -> list[dict]: ...
    def process(self, data: dict, message_in) -> str: ...
```

### 4.2 `parse()` — tokenize then extract

```python
def parse(self, raw: str) -> dict:
    lines = cargoimp.normalize(raw)
    message_id = lines[0] if lines else None
    awb_line   = lines[1] if len(lines) > 1 else None

    flights, ssr_lines, osi_lines, ref_raw, sri_raw = [], [], [], None, None
    last_block = None  # "ssr" | "osi"

    for ln in lines[2:]:
        if _FLIGHT_RE.match(ln):
            flights.append(ln)
            last_block = None
        elif ln.upper().startswith("SSR/"):
            ssr_lines.append(ln[4:])
            last_block = "ssr"
        elif ln.upper().startswith("OSI/"):
            osi_lines.append(ln[4:])
            last_block = "osi"
        elif ln.upper().startswith("REF/"):
            ref_raw = ln[4:]
            last_block = None
        elif ln.upper().startswith("SRI/"):
            sri_raw = ln[4:]
            last_block = None
        elif ln.startswith("/") and last_block == "ssr":
            ssr_lines.append(ln[1:])
        elif ln.startswith("/") and last_block == "osi":
            osi_lines.append(ln[1:])

    version_str = message_id.split("/", 1)[1] if message_id and "/" in message_id else None

    return {
        "message": {
            "type": self.message_type,
            "version": version_str or self.version,
            "id": message_id,
        },
        "awb": self._parse_awb(awb_line),
        "flights": [self._parse_flight(f) for f in flights],
        "ssr": [s.strip() for s in ssr_lines if s.strip()],
        "osi": [o.strip() for o in osi_lines if o.strip()],
        "booking_reference": self._parse_ref(ref_raw),
        "references": self._parse_sri(sri_raw),
    }
```

### 4.3 `_parse_awb(line)` — section 2

```python
def _parse_awb(self, line):
    if not line:
        return {}
    m = _AWB_RE.match(line.strip())
    if not m:
        return {"raw": line}
    prefix, serial, origin, dest, rest = m.groups()
    result = {
        "airline_prefix": prefix,
        "awb_serial_number": serial,
        "awb_number": f"{prefix}-{serial}",
        "origin": origin,
        "destination": dest,
    }
    if rest:
        cm = _CONSIGNMENT_RE.match(rest)
        if cm:
            result["shipment_description_code"] = cm.group("desc")
            result["number_of_pieces"] = int(cm.group("pieces"))
            result["weight_code"] = cm.group("wt_code")
            result["weight"] = float(cm.group("weight"))
            if cm.group("total_pieces"):
                result["total_pieces"] = int(cm.group("total_pieces"))
            tail_tokens = rest[cm.end():].split("/")
            goods_set = False
            sph = []
            for tok in tail_tokens:
                tok = tok.strip()
                if not tok:
                    continue
                if _SHC_RE.match(tok):
                    sph.append(tok)
                elif not goods_set:
                    result["goods_description"] = tok[:15]
                    goods_set = True
            result["special_handling_codes"] = sph[:9]
    return result
```

### 4.4 `_parse_flight(line)` — section 3

```python
def _parse_flight(self, line):
    m = _FLIGHT_RE.match(line.strip())
    if not m:
        return {"raw": line}
    carrier, flt_num, day, month, dep, arr, code = m.groups()
    return {
        "carrier": carrier,
        "flight_number": flt_num,
        "day": int(day),
        "month": month,
        "departure_airport": dep,
        "arrival_airport": arr,
        "space_allocation_code": code,
    }
```

### 4.5 `_parse_ref(raw)` — section 6

```python
def _parse_ref(self, raw):
    if not raw:
        return {}
    # Format A: REF/{7-8 char office address}[/{file_ref}]
    # Format B: REF//{file_ref}[/{pid}/{pcode}/{airport}]
    if raw.startswith("/"):
        # Format B — participant identification (section 6.6)
        parts = raw[1:].split("/")
        return {
            "file_reference": parts[0].strip()[:15] if parts else "",
            "participant_id": parts[1].strip()[:3] if len(parts) > 1 else "",
            "participant_code": parts[2].strip()[:17] if len(parts) > 2 else "",
            "airport": parts[3].strip()[:3] if len(parts) > 3 else "",
        }
    # Format A — office message address (section 6.3)
    parts = raw.split("/", 1)
    return {
        "office_address": parts[0].strip()[:8],
        "file_reference": parts[1].strip()[:15] if len(parts) > 1 else "",
    }
```

### 4.6 `_parse_sri(raw)` — section 7

```python
def _parse_sri(self, raw):
    if not raw:
        return []
    parts = raw.split("/")
    return [{
        "reference_number":   parts[0].strip()[:14] if parts else "",
        "supplementary_1":    parts[1].strip()[:12] if len(parts) > 1 else "",
        "supplementary_2":    parts[2].strip()[:12] if len(parts) > 2 else "",
    }]
```

---

## 5. `business_key()`

Returns the AWB number, identical to FWB:

```python
def business_key(self, data):
    return (data.get("awb") or {}).get("awb_number")
```

This drives the pipeline's amendment/dedup logic. Because FFA amends an existing Shipment whose key is the same AWB number, the pipeline's stale-guard and lock-guard apply automatically.

---

## 6. `validate()`

Returns a list of issue dicts `{"level", "code", "field", "message"}`. An `Error` level blocks `process()`.

### 6.1 Mandatory / structural checks

| Check | Level | Code |
|---|---|---|
| AWB line missing or unparseable | Error | `AWB_LINE` |
| AWB serial not exactly 8 digits | Error | `AWB_SERIAL_LENGTH` |
| AWB check digit (mod-7) invalid | Warning | `AWB_CHECKDIGIT` |
| No flight lines in the message | Error | `NO_FLIGHTS` |
| REF line missing or empty | Error | `REF_MISSING` |
| REF office address not 7 chars (3+2+2) | Warning | `REF_FORMAT` |

### 6.2 Per-flight checks

| Check | Level | Code |
|---|---|---|
| `space_allocation_code` not in `_VALID_ALLOC` | Error | `ALLOC_CODE` |
| Departure and arrival airports are the same | Warning | `FLIGHT_ROUTE` |

### 6.3 Business logic warnings

| Check | Level | Code |
|---|---|---|
| Origin == Destination on the AWB line | Warning | `AWB_ROUTE` |
| `number_of_pieces` is zero (FFA21 allows it) | Info | `ZERO_PIECES` |

```python
def validate(self, data):
    issues = []
    awb = data.get("awb") or {}
    if not awb.get("awb_number"):
        return [{"level":"Error","code":"AWB_LINE","field":"awb",
                 "message":"Could not parse the AWB consignment detail line"}]
    serial = (awb.get("awb_serial_number") or "").strip()
    if not (serial.isdigit() and len(serial) == 8):
        issues.append({"level":"Error","code":"AWB_SERIAL_LENGTH","field":"awb_serial_number",
                       "message":"AWB serial number must be exactly 8 digits"})
    elif int(serial[:7]) % 7 != int(serial[7]):
        issues.append({"level":"Warning","code":"AWB_CHECKDIGIT","field":"awb_serial_number",
                       "message":f"Invalid AWB check digit (expected {int(serial[:7]) % 7})"})
    if awb.get("origin") and awb.get("origin") == awb.get("destination"):
        issues.append({"level":"Warning","code":"AWB_ROUTE","field":"destination",
                       "message":"AWB origin and destination are the same airport"})
    if not data.get("flights"):
        issues.append({"level":"Error","code":"NO_FLIGHTS","field":"flights",
                       "message":"FFA message contains no flight detail lines"})
    for i, flt in enumerate(data.get("flights") or []):
        code = (flt.get("space_allocation_code") or "").upper()
        if code not in _VALID_ALLOC:
            issues.append({"level":"Error","code":"ALLOC_CODE","field":f"flights.{i}.space_allocation_code",
                           "message":f"Unknown space allocation code '{code}'"})
        if flt.get("departure_airport") == flt.get("arrival_airport"):
            issues.append({"level":"Warning","code":"FLIGHT_ROUTE","field":f"flights.{i}.arrival_airport",
                           "message":"Flight departure and arrival airports are identical"})
    ref = data.get("booking_reference") or {}
    if not (ref.get("office_address") or ref.get("participant_id") or ref.get("file_reference")):
        issues.append({"level":"Error","code":"REF_MISSING","field":"booking_reference",
                       "message":"REF line is mandatory in an FFA message"})
    return issues
```

---

## 7. `process()`

### 7.1 Strategy — amend, don't replace

FFA is an answer to an FFR; it carries the airline's reply about *previously requested* flights. The Shipment already exists (created by FWB or by FFR processing). `process()` must:

1. Look up the Shipment by AWB number — raise if not found.
2. For each flight in `data["flights"]`, find the matching row in `flight_bookings` and update it; create a new row if no match exists.
3. Merge SSR/OSI additions (append, not replace — FFA SSR is a reply to FFR SSR, spec note FFA23).
4. Write sender reference from REF into Shipment header fields.
5. Merge SRI rows.
6. `doc.save()`.

### 7.2 Flight-row matching

Match on **carrier code + flight number + day + month** (same semantics as the original FFR request). Do not match on departure/arrival airports because those come *from* the FFA — the FFR may not have had them.

```python
def _find_flight_row(self, booking_rows, flt):
    """Return the matching flight_bookings row, or None."""
    for row in booking_rows:
        if (
            (row.carrier_code or "").upper() == flt["carrier"].upper()
            and (row.flight_number or "") == flt["flight_number"]
            and str(row.flight_day or "") == str(flt["day"])
            and (row.flight_month or "").upper() == flt["month"].upper()
        ):
            return row
    return None
```

### 7.3 `process()` full outline

```python
def process(self, data, message_in) -> str:
    awb = data["awb"]
    name = awb["awb_number"]

    if not frappe.db.exists("Shipment", name):
        frappe.throw(f"FFA received for unknown AWB {name}; process the FWB first")

    doc = frappe.get_doc("Shipment", name)

    self._ensure("Airport", {"iata_code": awb["origin"]}, awb["origin"])
    self._ensure("Airport", {"iata_code": awb["destination"]}, awb["destination"])

    for flt in data.get("flights") or []:
        self._ensure("Airport", {"iata_code": flt["departure_airport"]}, flt["departure_airport"])
        self._ensure("Airport", {"iata_code": flt["arrival_airport"]}, flt["arrival_airport"])
        carrier = self._ensure_airline_by_code(flt["carrier"])
        row = self._find_flight_row(doc.flight_bookings, flt)
        if row:
            row.space_allocation_code = flt["space_allocation_code"]
            if not row.departure_airport:
                row.departure_airport = flt["departure_airport"]
            if not row.arrival_airport:
                row.arrival_airport = flt["arrival_airport"]
        else:
            doc.append("flight_bookings", {
                "carrier": carrier,
                "flight_number": flt["flight_number"][:5],
                "flight_day": str(flt["day"]).zfill(2),
                "flight_month": flt["month"],
                "departure_airport": flt["departure_airport"],
                "arrival_airport": flt["arrival_airport"],
                "space_allocation_code": flt["space_allocation_code"],
            })

    # SSR — append new texts; don't duplicate (FFA23: reply to FFR SSR)
    existing_ssr = {r.special_service_request for r in doc.special_service_requests}
    for text in data.get("ssr") or []:
        if text[:65] not in existing_ssr:
            doc.append("special_service_requests", {"special_service_request": text[:65]})

    # OSI — same append logic
    existing_osi = {r.other_service_information for r in doc.other_service_info}
    for text in data.get("osi") or []:
        if text[:65] not in existing_osi:
            doc.append("other_service_info", {"other_service_information": text[:65]})

    # REF → sender reference fields
    ref = data.get("booking_reference") or {}
    if ref.get("office_address"):
        doc.sender_office_address = ref["office_address"][:8]
    if ref.get("file_reference"):
        doc.sender_file_reference = ref["file_reference"][:15]
    if ref.get("participant_id"):
        doc.sender_participant_id = ref["participant_id"][:3]
    if ref.get("participant_code"):
        doc.sender_participant_code = ref["participant_code"][:17]

    # SRI → references child table (merge)
    for r in data.get("references") or []:
        ref_num = (r.get("reference_number") or "").strip()
        if ref_num:
            doc.append("references", {
                "reference_number": ref_num[:14],
                "supplementary_1": (r.get("supplementary_1") or "")[:12],
                "supplementary_2": (r.get("supplementary_2") or "")[:12],
            })

    doc.flags.ignore_permissions = True
    doc.save()
    return doc.name
```

### 7.4 Helper methods (shared pattern from FWB16Parser)

```python
def _ensure(self, doctype, values, name):
    if name and not frappe.db.exists(doctype, name):
        d = frappe.new_doc(doctype)
        d.update(values)
        d.flags.ignore_permissions = True
        d.insert()

def _ensure_airline_by_code(self, carrier_code):
    code = (carrier_code or "").strip().upper()
    if not code:
        return None
    existing = frappe.db.get_value("Airline", {"carrier_code": code}, "name")
    if existing:
        return existing
    if frappe.db.exists("Airline", code):
        return code
    d = frappe.new_doc("Airline")
    d.airline_prefix = code
    d.carrier_code = code
    d.flags.ignore_permissions = True
    d.insert()
    return code
```

---

## 8. Registry Wire-Up

### 8.1 `EDX Message Definition` row

Create via Frappe Desk or migration fixture:

| Field | Value |
|---|---|
| `name` | `FFA-6` |
| `message_type` | `FFA` |
| `version` | `6` |
| `detection_pattern` | `^FFA/[0-9]` |
| `parser_class` | `awbix.edx.handlers.ffa.ffa_parser.FFAParser` |
| `composer_class` | `awbix.edx.handlers.ffa.ffa_composer.FFAComposer` |
| `target_doctype` | `Shipment` |
| `is_parser_enabled` | `1` |
| `is_composer_enabled` | `1` |
| `auto_promote` | `1` (promote on ingest) |
| `auto_process` | `0` (require manual verify first) |

> **Note on `detection_pattern`:** The classifier (engine/classifier.py) matches against the beginning of the raw message using `re.search(..., re.IGNORECASE|re.MULTILINE)`. The pattern `^FFA/[0-9]` correctly matches `FFA/4`, `FFA/6`, etc. and will not false-match `FFA` appearing elsewhere in the body.

### 8.2 Pipeline flow for an inbound FFA

```
ingest_raw()
  → content-hash dedup
  → classify() → "FFA", "6"
  → auto_promote = True → promote_stage()
  → EDX Message In created (parse_status = "Pending")

[Manual or scheduled trigger]
  → verify_message_in()
      → FFAParser.parse() → parsed_json stored
      → FFAParser.validate() → issues stored
      → parse_status = "Verified" | "Issues"

[Manual "Process" button, after human review if issues]
  → process_message_in()
      → amendment guards (stale / lock)
      → FFAParser.process() → Shipment.flight_bookings updated
      → process_status = "Processed"
```

---

## 9. Test Plan

File: `awbix/edx/handlers/ffa/test_ffa_parser.py`

### 9.1 parse() unit tests (no DB, pure)

| Test | Input | Expected output |
|---|---|---|
| `test_parse_example_61` | Example 6.1 FFA/4 | awb_number=`125-1234565`, flights=[{carrier=BA, flt=171, alloc=KK, dep=LHR, arr=JFK}] |
| `test_parse_example_68_multi_flight` | Example 6.8 | Two flight rows with KK and UU respectively |
| `test_parse_example_69_ssr_osi_sri` | Example 6.9 | ssr, osi, booking_reference, and references populated |
| `test_parse_example_610_sri_time` | Example 6.10 | SRI with reference `LH8520` and supplementary datetime values |
| `test_parse_ref_format_a` | `REF/FRAFCBA` | office_address=`FRAFCBA`, file_reference=`` |
| `test_parse_ref_format_a_with_fileref` | `REF/BHXFRBA/1234` | office_address=`BHXFRBA`, file_reference=`1234` |
| `test_parse_ref_format_b_participant` | `REF//MYREF/XXX/CODEABC/JFK` | file_reference=`MYREF`, participant_id=`XXX` |
| `test_parse_sph_codes_in_awb` | AWB line with `/BOOKS /VAL` tokens | special_handling_codes=[`VAL`], goods_description=`BOOKS` |
| `test_parse_ssr_continuation` | SSR with `/` continuation line | ssr has two entries |
| `test_parse_unknown_segment_ignored` | Unknown 3-char code between flights and REF | does not raise |

### 9.2 validate() unit tests

| Test | Setup | Expected |
|---|---|---|
| `test_validate_clean` | Example 6.2 parsed | no issues |
| `test_validate_missing_awb` | Empty AWB line | Error AWB_LINE |
| `test_validate_bad_checkdigit` | Serial `12345678` (wrong check digit) | Warning AWB_CHECKDIGIT |
| `test_validate_short_serial` | 7-digit serial | Error AWB_SERIAL_LENGTH |
| `test_validate_no_flights` | No flight lines | Error NO_FLIGHTS |
| `test_validate_bad_alloc_code` | Space code `ZZ` | Error ALLOC_CODE |
| `test_validate_missing_ref` | No REF line | Error REF_MISSING |
| `test_validate_zero_pieces_info` | pieces=0 | Info ZERO_PIECES |

### 9.3 business_key() tests

| Test | Expected |
|---|---|
| `test_business_key_normal` | `"057-12345675"` |
| `test_business_key_no_awb` | `None` |

### 9.4 process() integration tests (require Frappe DB)

These tests use `FrappeTestCase` and insert a minimal `Shipment` first:

| Test | Setup | Assert |
|---|---|---|
| `test_process_updates_existing_flight_row` | Shipment with BA171/19MAR; FFA says KK | Row `space_allocation_code` becomes `KK` |
| `test_process_appends_new_flight_row` | Shipment with no BA171; FFA says KK | New row appended |
| `test_process_fills_dep_arr_airports` | Existing row with no dep/arr; FFA gives LHR/JFK | Fields populated |
| `test_process_does_not_overwrite_dep_arr` | Row already has dep=LHR; FFA gives different | dep=LHR unchanged |
| `test_process_missing_shipment_raises` | No Shipment for AWB | `frappe.ValidationError` or throw |
| `test_process_ssr_appended_not_duplicated` | Existing SSR text; FFA repeats same text | Only one row |
| `test_process_multi_flight` | Example 6.8 (2 flights) | Two rows updated independently |
| `test_process_ref_written_to_header` | REF/FRAFCBA | `shipment.sender_office_address == "FRAFCBA"` |
| `test_process_creates_airport_stubs` | Airport LHR not in DB | Airport LHR created |

---

## 10. Open Questions / Design Decisions

| # | Question | Recommended resolution |
|---|---|---|
| 1 | Should `process()` fail if the Shipment is submitted (docstatus=1)? | Yes — throw a clear message; the pipeline's lock-guard should catch it first, but the parser should defend too. |
| 2 | Should FFA amend SSR/OSI by replacing or appending? | Append (FFA23 note says "reply to SSR received in FFR"). Dedup by text content. |
| 3 | Flight match logic: should month be required for matching? | Yes — same flight number operates on multiple days; month disambiguates. |
| 4 | `auto_process` flag on the definition: auto or manual? | Manual (`0`) for initial deployment so ops can inspect before the flight bookings flip. Can enable later. |
| 5 | What if an FFA arrives for an AWB not in the system yet? | Throw and surface as `Error` in EDX Message Log. Ops reprocess after FWB is ingested. |
| 6 | Should the `departure_airport` / `arrival_airport` fields on `Shipment Flight Booking` be auto-resolved (via `_ensure`) even if the Shipment already has routing? | Yes — ensure Airport stub exists; resolution is idempotent. |
| 7 | Do we need a separate validator class (`FFAValidator`) like FWB has `fwb16_validator.py`? | Not for v1 — embed validation in `FFAParser.validate()`. Promote to a separate module if ABNF-level validation is added later. |

---

## 11. Implementation Checklist

- [ ] Create `awbix/edx/handlers/ffa/__init__.py` (empty, if not already present)
- [ ] Create `awbix/edx/handlers/ffa/ffa_parser.py` with `FFAParser` class
  - [ ] `parse()` + all `_parse_*` helpers
  - [ ] `business_key()`
  - [ ] `validate()`
  - [ ] `process()` + `_find_flight_row()` + `_ensure*` helpers
- [ ] Create `awbix/edx/handlers/ffa/test_ffa_parser.py` with all test cases above
- [ ] Insert `EDX Message Definition` row `FFA-6` (via fixture JSON or Desk)
- [ ] Smoke test: ingest one of the FFA/6 examples from FFA.md through the full pipeline
- [ ] Run `bench run-tests awbix.edx.handlers.ffa.test_ffa_parser`
- [ ] Run `ruff check awbix/edx/handlers/ffa/ffa_parser.py` — zero issues
