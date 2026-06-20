# EDX FHL Handler — Implementation Plan (parse · process · compose)

> **Goal:** add a new EDX message handler for **FHL** (Consolidation List, Cargo-IMP), built the
> same way as the existing **FWB** handler — a parser (inbound), a composer (outbound), and one
> `EDX Message Definition` registration. Implemented entirely inside the existing EDX framework;
> **no engine/core changes** beyond one documented amendment-ledger nuance (§6).
>
> **Data model is already done.** The `House Airway Bill` (HWB) DocType and its four children
> (`…Special Handling`, `…Free Text`, `…HS Code`, `…Customs Info`) already exist under
> `awbix/shipment/doctype/` (see `house_airway_bill_plan.md`). This plan only wires FHL messaging
> to that model — it does **not** touch the DocTypes.
>
> **Canonical references:** `FHL_RULE_BY_SEQ.csv` (field spec: seq · M/O · format · DE# · constant),
> `fhl_cimp_manuel.md` (CIMP manual), and `fhl sample message*.txt` (5 real messages). FWB is the
> structural template: `awbix/edx/handlers/fwb/{fwb16_parser,fwb16_composer,cargoimp}.py`.

---

## 1. What FHL is, and how it differs from FWB

| | FWB | FHL |
|---|---|---|
| Meaning | One Air Waybill (Master) | A **consolidation list**: one Master AWB + **many** House Waybills |
| Target DocType | `Shipment` (1 message → 1 doc) | `House Airway Bill` (1 message → **N** docs, all linked to one master `Shipment`) |
| Top line | `FWB/16` | `FHL/5` |
| Consignment line | AWB line (`157-68076960BSLDOH/…`) | **MBI** line (`MBI/157-69081003AMSYUL/T1K610`) — the master |
| Repeating spine | — | **HBS** block per house, each optionally carrying SPH / TXT / HTS / OCI / SHP / CNE / CVD |

The single most important structural fact: **FHL is one master header (`MBI`) followed by a
repeating list of house blocks (`HBS …`)**. Everything in the parser/composer is organized around
slicing/emitting that repeating list. This is the only meaningful departure from FWB.

### FHL message anatomy (from `fhl sample message 1.txt`)

```
FHL/5                                           ← Ref 1  message id + version
MBI/157-67661882BLRCDG/T3K99.0                  ← Ref 2  MASTER AWB (prefix-serial, O&D, T pieces/wt)
HBS/530510258554/BLRCDG/2/K64.0//HOSE ASSEMBLY  ← Ref 3  HOUSE summary (serial/O&D/pcs/wt/slac/desc)
  /SPX/EAW                                       ← Ref 3.10 SPH (continuation of HBS, may be absent)
TXT/NVOICE NOS E-IN 26-27 …                      ← Ref 4  free-text goods (≤9, repeatable)
HTS/88079000                                     ← Ref 5  HS code (≤9, repeatable)
OCI//CNE/T/FR42091691800063                      ← Ref 6  customs/security lines (repeatable, + ///… continuations)
SHP                                              ← Ref 7  shipper block …
  NAM/STS TITEFLEX INDIA PVT LTD                 ←        name
  ADR/38KIADB INDUSTRIAL AREA                    ←        street
  LOC/BANGALORE/KA                               ←        place / state
  /IN/561203                                     ←        country / post (LOC continuation)
CNE                                              ← Ref 8  consignee block (same shape)
  …
CVD/INR/PP/NVD/NCV/XXX                           ← Ref 9  charge declarations (currency, P/C, NVD/NCV/XXX)
```

In the bare "check-list" form (manual §6.1) there are several `HBS` lines back-to-back with **no**
TXT/OCI/SHP/CNE/CVD. In the "expanded" form (samples) each house carries its own sub-groups. The
parser must handle both: **a new house begins at each `HBS` line and owns every segment until the
next `HBS` (or end of message).**

---

## 2. File layout (mirror `handlers/fwb/`)

```
awbix/edx/handlers/fhl/
├── __init__.py                  # empty (package marker)
├── fhl_parser.py                # FHLParser(BaseParser)        — inbound
├── fhl_composer.py              # FHLComposer(BaseComposer)    — outbound
├── test_fhl_parser.py           # FrappeTestCase (parse + validate, pure)
└── test_fhl_composer.py         # FrappeTestCase (round-trip + outbound pipeline)
```

**Reuse `awbix/edx/handlers/fwb/cargoimp.py` as-is** — the line tokenizer (`normalize`, `tokenize`,
`by_code`, `first`, `continuation_text`, `segment`, `join`) is message-agnostic and already shared
by FWB/FNA/FMA. FHL-specific **grouping** (slicing segments into per-house blocks) lives in
`fhl_parser.py`, not in `cargoimp` (keep the shared module dumb). If FHL grouping helpers grow,
extract them to `handlers/fhl/cimp_fhl.py`; start inline.

> Note: `cargoimp.tokenize` already treats line[0] as `message_id`, line[1] as `awb_line`, and the
> rest as `/`-grouped segments. For FHL, line[1] is the `MBI` line and `HBS`/`TXT`/`OCI`/`SHP`/`NAM`/
> `ADR`/`LOC`/`CNE`/`CVD`/`HTS` each tokenize as their own segment (SPH and LOC country/post arrive as
> `/`-continuation lines on their owning segment). No tokenizer change needed.

---

## 3. Parser — `fhl_parser.py` (`FHLParser(BaseParser)`, `message_type="FHL"`, `version="5"`)

Implements the four `BaseParser` hooks (`parse`, `business_key`, `validate`, `process`). `parse`,
`business_key`, `validate` are **pure** (no DB/network) per the base contract; only `process` writes.

### 3.1 `parse(raw) -> dict`

```python
{
  "message": {"type": "FHL", "version": "5", "id": <line 0>},
  "master": { airline_prefix, awb_serial_number, awb_number, origin, destination,
              pieces, weight_code, weight, raw_detail },          # from MBI
  "houses": [ { house dict }, … ],                                # one per HBS block
  "segments_seen": [codes…],
}
```

Steps:
1. `t = cargoimp.tokenize(raw)`.
2. `self._parse_master(t["awb_line"])` — parse the `MBI` line. Regex mirrors FWB's `_AWB_RE` but the
   token is prefixed `MBI/`: `^MBI/(\d{1,3})-(\d{8})([A-Z]{3})([A-Z]{3})(?:/T(\d+)([A-Z])([0-9.]+))?`.
3. `self._group_houses(t["segments"])` — walk segments, **start a new group at every `HBS` segment**,
   appending subsequent non-`HBS` segments (TXT/HTS/OCI/SHP/NAM/ADR/LOC/CNE/CVD) to the current group
   until the next `HBS`. Returns `list[list[segment]]`.
4. For each group, `self._parse_house(group)`:
   - **HBS header** (`group[0]["lines"][0]`): `HBS/{serial}/{orig}{dest}/{pieces}/{wtcode}{weight}/{slac}/{manifest_desc}`.
     Split on `/`; positions are: serial, O&D (6 chars → `[:3]`/`[3:]`), pieces, weight (code+number),
     slac (may be empty), manifest description. Map to
     `hwb_serial_number, hwb_origin, hwb_destination, number_of_pieces, weight_code, weight, slac, manifest_description`.
   - **SPH**: `cargoimp.continuation_text(hbs_segment)` → each `/SPX/EAW` continuation splits on `/`
     into special-handling codes → `special_handling: [{code}, …]` (cap awareness handled in `validate`).
   - **TXT**: every `TXT` segment → `free_text: [{text}, …]`.
   - **HTS**: every `HTS` segment → `hs_codes: [{code}, …]`.
   - **OCI**: every `OCI` segment **plus its `/`-continuation lines** → `oci: [{country, information_identifier,
     customs_info_identifier, supplementary}, …]`. Each line splits on `/`; blank leading fields
     (e.g. `///ED/0213`, `//HWB/I/…`) become rows with empty country/info-id — order preserved
     (matches the HWB model note: continuation rows keep `idx`).
   - **SHP / CNE**: `self._parse_party(group, "SHP")` / `"CNE"` — find the `SHP`/`CNE` header, then read
     the following `NAM` / `ADR` / `LOC` segments until the next party/`CVD`. Extract
     `name (NAM), address (ADR), place+state (LOC line), country+post (LOC continuation),
     contact_id+contact_number (trailing /FX|TE|TL/number)`.
   - **CVD**: `CVD/{currency}/{wt_pc}{oth_pc}/{carriage}/{customs}/{insurance}` →
     `{currency, wt_val_prepaid_collect, other_charges_prepaid_collect, declared_value_carriage,
       declared_value_customs, insurance}` (NVD/NCV/XXX = the "nil" tokens).

Keep per-field parsing defensive (`raw_*` fallbacks like FWB's `_parse_awb`) so a malformed line
surfaces as a `validate` issue rather than a parse exception.

### 3.2 `business_key(data) -> str`

Return the **master AWB number** (`data["master"]["awb_number"]`, e.g. `157-67661882`). The whole
consolidation shares one key; per-house identity is `(master, hwb_serial)` and is enforced by
`House Airway Bill.validate_unique_serial_per_master`. (See §6 for the amendment-ledger implication.)

### 3.3 `validate(data) -> list[dict]`

Light, pure pre-checks (the deep field rules already live in `HouseAirwayBill.validate()` and run on
`process`). Mirror FWB's issue shape `{level, code, field, message}`:

| Check | Level | Code |
|---|---|---|
| MBI parsed / master `awb_number` present | Error | `MBI` |
| Master serial 8 digits + mod-7 check digit (reuse FWB logic) | Error | `AWB_SERIAL` / `AWB_CHECKDIGIT` |
| At least one `HBS` house present | Error | `NO_HOUSE` |
| Per house: serial present & `m[1...12]` | Error | `HWB_SERIAL` |
| Per house: pieces > 0, weight > 0, manifest desc present | Error | `HWB_QTY` |
| Per house: `hwb_origin != hwb_destination` | Error | `HWB_ROUTE` |
| Duplicate house serial within the message | Error | `HWB_DUP` |
| SPH / TXT / HTS > 9 rows in a house | Warning | `ROW_LIMIT` |
| CVD currency missing on a house | Warning | `CURRENCY` |

### 3.4 `process(data, message_in) -> str`

Idempotent, create-or-update — mirrors `FWB16Parser.process` but fans out to N houses:

1. **Ensure the master `Shipment` exists** (the MBI). If `frappe.db.exists("Shipment", awb_number)`
   use it; else create a minimal one from the MBI (prefix/serial/origin/destination/currency), reusing
   FWB's `_ensure("Airline"/"Airport")` + `_ensure_currency` helpers (copy them, or lift the shared
   ones into a small `handlers/_masters.py` — optional refactor, not required).
2. **For each house** in `data["houses"]`:
   - Ensure `Airport` rows for `hwb_origin`/`hwb_destination`, `Currency`, `Special Handling Code`,
     `Country`, `OCI Information Identifier`, `Customs Information Identifier` referenced — using the
     same `_ensure` guard (create-if-missing) so a `Link` never fails on process.
   - Find existing HWB by `{master_shipment, hwb_serial_number}` (the model's uniqueness pair); if
     found `frappe.get_doc` (amendment in place), else `frappe.new_doc("House Airway Bill")`.
   - Set scalar fields (`master_shipment`, `hwb_serial_number`, `hwb_origin`, `hwb_destination`,
     `number_of_pieces`, `weight_code`, `weight`, `slac`, `manifest_description`).
   - **Parties:** FHL carries inline name/address, not `Party` links. Leave `shipper`/`consignee`
     (the `Link → Party` fields) empty and write the denormalized `shipper_*`/`consignee_*` fields
     directly — they are `read_only` + `fetch_from`, but `fetch_from` only overwrites when the link
     field changes, so directly-set values persist when the link is blank. (Optional later: resolve/
     create a `Party` and link it.)
   - Rebuild children with `doc.set("special_handling", [])` etc. then `doc.append(...)` per row
     (cap at 9 to satisfy the model rule), and `oci_customs` rows in parsed order.
   - Set CVD fields. For NVD/NCV/XXX map the nil tokens to the model's Select types
     (`NVD`/`Value`, `NCV`/`Value`, `XXX`/`Value`) and amounts.
   - `doc.flags.ignore_permissions = True; doc.save()`.
3. Return the **master AWB number** (the business key) as the representative target name.

> The model's own `validate()` (serial format, route, qty, row caps, OCI ≥1-of-3, party FHL24, CVD
> amount rules) runs on each `save()` — so `process` stays thin and the heavy validation is not
> duplicated. A `frappe.ValidationError` from any house propagates to the pipeline, which rolls back
> and records a `PROCESS` issue (see `pipeline.process_message_in`).

---

## 4. Composer — `fhl_composer.py` (`FHLComposer(BaseComposer)`, `FHL`/`5`)

The inverse, mirroring `FWB16Composer`. **Compose source = the master `Shipment`**; the composer
gathers all linked houses.

### 4.1 `compose(source_doc) -> str`

```python
lines = ["FHL/5", self._mbi_line(source_doc)]
for hwb in self._houses_for(source_doc):     # frappe.get_all("House Airway Bill",
    lines += self._house_lines(hwb)          #   {"master_shipment": source_doc.name}, ordered)
return cargoimp.join(lines)
```

- `_mbi_line`: `MBI/{prefix}-{serial}{ORIG}{DEST}` + `/T{pieces}{wtcode}{weight}` (reuse FWB's
  `_awb_line` numeric helper `_num`).
- `_house_lines(hwb)` emits, per house, in FHL order:
  - `HBS/{serial}/{O}{D}/{pieces}/{wtcode}{weight}/{slac or ''}/{manifest_description}`
  - SPH as an `/CODE/CODE` continuation line if any `special_handling` rows.
  - one `TXT/<text>` per `free_text` row; one `HTS/<code>` per `hs_codes` row.
  - `OCI/...` per `oci_customs` row (blank fields rendered as empty between slashes).
  - `SHP` + `NAM/ ADR/ LOC/…` when shipper present; same for `CNE`.
  - `CVD/{currency}/{wtpc}{othpc}/{NVD|amt}/{NCV|amt}/{XXX|amt}`.
- The composer reads only via `.get()` so tests can pass plain dicts (see FWB composer test).

### 4.2 `verify(raw) -> list[dict]`

Re-parse through the parser as a genuine self-check (identical pattern to FWB):

```python
def verify(self, raw):
    p = FHLParser()
    return p.validate(p.parse(raw))
```

`pipeline.dispatch_message_out` blocks sending if `verify` returns any `Error`.

---

## 5. Registration — `EDX Message Definition` (`install.py`)

Add one dict to `_DEFINITIONS` in `awbix/edx/install.py` (seeded idempotently by `after_migrate`;
`_backfill_definition` activates the composer on re-migrate):

```python
{
    "message_type": "FHL",
    "version": "5",
    "title": "FHL/5 — Consolidation List / House Waybills (Cargo-IMP)",
    "standard": "Cargo-IMP",
    "parser_class": "awbix.edx.handlers.fhl.fhl_parser.FHLParser",
    "composer_class": "awbix.edx.handlers.fhl.fhl_composer.FHLComposer",
    "target_doctype": "House Airway Bill",
    "is_parser_enabled": 1,
    "is_composer_enabled": 1,
    "auto_promote": 1,
    "auto_process": 1,
    "detection_pattern": "^FHL/5",     # classifier matches the SMI; mirrors "^FWB/16"
    "amendment_mode": "Auto Apply",
},
```

`classifier.classify` is data-driven (regex from the definition), so **no code change** is needed to
recognize inbound FHL once this row exists. Verify ordering: definitions are tried `message_type asc,
version desc`; `^FHL/5` is unambiguous against `^FWB/16` / `^FMA` / `^FNA`.

---

## 6. The one framework nuance — amendment ledger for 1-message→N-docs

`pipeline._upsert_delivery` records **one** `EDX Delivery` per `(business_key, target_doctype)` with a
single `target_name`. FHL's business key is the master AWB while it produces many HWBs, so the
Delivery's `target_name` can only hold a representative (we return the master AWB number). This is
acceptable and requires **no engine change**:

- Amendment/stale guards key on the master AWB — correct granularity for "re-received consolidation".
- Idempotency of individual houses is guaranteed by the model's `(master_shipment, hwb_serial_number)`
  uniqueness + create-or-update in `process` (re-processing updates the same HWBs, never duplicates).
- `target_doctype = "House Airway Bill"` keeps the Delivery distinct from any FWB Delivery on the same
  AWB (FWB Delivery's `target_doctype` is `Shipment`).

Document this explicitly in `process`'s docstring so the representative-`target_name` choice is not
mistaken for a bug. (If per-house delivery tracking is ever required, that's a future engine feature,
out of scope here.)

---

## 7. Tests (mirror `test_fwb16_parser.py` / `test_fwb16_composer.py`)

**`test_fhl_parser.py`** — pure parse + validate, no DB:
- Single-house expanded message (sample 1): assert master prefix/serial/O&D, `business_key` ==
  `157-67661882`, one house with serial/O&D/pieces/weight/manifest, OCI row, shipper/consignee names,
  CVD currency `INR`.
- Multi-house check-list (manual §6.1 three `HBS`): assert 3 houses, no parties, distinct serials.
- Multi-line OCI with `///ED`, `///SM`, `///SN`, `///ST` continuations (sample 2): rows preserved in order.
- Negative: bad master check digit → `AWB_CHECKDIGIT`; no HBS → `NO_HOUSE`; duplicate house serial →
  `HWB_DUP`; same house O&D → `HWB_ROUTE`.

**`test_fhl_composer.py`**:
- **Round-trip**: build a master dict + house dict(s), `compose`, re-`parse`, assert master + each
  house's serial/O&D/qty/parties/CVD survive.
- `verify` clean on good data; flags bad master check digit.
- **Outbound pipeline** (like `TestOutboundPipeline`): seed a `Shipment` + ≥1 `House Airway Bill`,
  `queue_outbound("Shipment", master, "FHL", "5")` → `dispatch_message_out`, assert `Sent`/`Verified`
  via a fake transport and `"FHL/5"` in the raw payload (add a routing row + Manual connection).

**Process test** (in parser test file, DB-backed): feed sample 1 through
`parser.process(parser.parse(raw), mi_stub)`, assert a `House Airway Bill` exists with the parsed
serial linked to the master `Shipment`, and re-processing updates rather than duplicates.

Commands (from bench root):
```bash
bench run-tests awbix.edx.handlers.fhl.test_fhl_parser
bench run-tests awbix.edx.handlers.fhl.test_fhl_composer
bench migrate          # seeds the FHL definition
```

---

## 8. Build order (each step migrates clean + tests green)

1. **Scaffold** `handlers/fhl/__init__.py` + skeleton parser/composer classes (NotImplemented bodies).
2. **Parser `parse` + house grouping** + `business_key`; `test_fhl_parser` parse cases (samples 1–2,
   manual check-list). Pure, no DB.
3. **Parser `validate`**; negative-case tests.
4. **Register definition** in `install.py`; `bench migrate`; confirm `classify` detects `^FHL/5` and
   `verify_message_in` runs end-to-end on a staged sample.
5. **Parser `process`** (master ensure + per-house create/update + children + parties + CVD);
   DB-backed process + re-process idempotency test.
6. **Composer `compose` + `verify`**; round-trip + outbound-pipeline tests.
7. **Docs:** note FHL in `edx_implemented.md` and the EDX strategy doc; update root `CLAUDE.md` EDX
   handler list if it enumerates message types. Run `ruff check . && ruff format .` and
   `pre-commit run --all-files`.

---

## 9. Explicitly out of scope

- Any change to the `House Airway Bill` DocTypes (already built; see `house_airway_bill_plan.md`).
- Multi-part FHL reassembly across physical messages (FHL1 continuation rule) — single-message only
  for v1; note as a future enhancement.
- Per-house `EDX Delivery` ledger rows (single representative key per consolidation — §6).
- Resolving/creating `Party` masters from inline SHP/CNE (denormalized fields only for v1).
- New transports/routing logic — reuse the existing engine, registry, and routing unchanged.
