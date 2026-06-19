# House Airway Bill (HWB) — Strategic Implementation Plan

> **Status:** Design / not yet implemented
> **Author baseline:** expands the original scope stub into a phased, enterprise-grade delivery plan.
> **Canonical field spec:** `FHL_RULE_BY_SEQ.csv` (sequence + M/O + data format + data element code + fixed constants). The CIMP manual (`fhl_cimp_manuel.md`), the Data Element / Code List grids (`data_grid_masters.md`), and the five `fhl sample message*.txt` files are the supporting references.

---

## 0. Scope (locked)

| Dimension | Decision |
|---|---|
| Framework | Frappe Framework v15 |
| Scope **include** | Frappe **DocType / model creation only** (schema + Python `Document` business logic + tests) |
| Scope **exclude** | Frontend beyond standard Desk; **messaging / FHL serialization & parsing** (that is the EDX module's job) |
| Module | `Shipment` (HWB lives alongside `Shipment`, under `awbix/shipment/doctype/`) |
| Workspace | Surface `House Airway Bill` under the **Shipment** workspace (Phase 7) |
| New feature | House Airway Bill |
| Base rule | CIMP **FHL** (Consolidation List) message |
| Relationship | HWB is an **independent document** that **references** a Shipment (Master AWB). **One Shipment → many House Airway Bills.** |
| Data elements | As per the FHL CIMP manual / IATA Data Element Grid |

**What "as per FHL rule" means for a model-only build:** the FHL message is a *consolidation list* = one **MBI** (Master AWB) header + many **HBS** (House Waybill) blocks, each with optional **TXT / HTS / OCI / SHP / CNE / CVD** sub-groups. Because messaging is out of scope, we are **not** generating or parsing FHL text. We are building the **persistent data model** that one such HBS block (plus its sub-groups) represents — i.e. the House Airway Bill document — and relating it to the Shipment that plays the MBI/Master role. EDX (future) will read this model to emit/consume FHL.

---

## 1. Architecture & Strategy (the "best enterprise strategy")

### 1.1 Guiding principles
1. **Mirror the proven Shipment model.** The existing `Shipment` DocType already implements the AWB/Master side of CIMP with a clean, repeatable pattern (tabs → section/column breaks, `Link` to masters, `fetch_from` denormalization, `DExxx` field descriptions, `length` matching IATA formats, submittable + `amended_from`, EDX-ack section). HWB must be **structurally consistent** with it so the two read as one system.
2. **CSV is the source of truth for *requiredness & format*.** Every HWB field maps to a row in `FHL_RULE_BY_SEQ.csv`; the `Condition Code` (M/O) drives `reqd`, the `Data Format` drives `fieldtype`/`length`, the `Data Element Code` becomes the field `description` (`DE###`), and `Fixed Value Constant` values (FHL, MBI, HBS, TXT, HTS, OCI, NAM, ADR, LOC, SHP, CNE, CVD, NVD, NCV, XXX) are **structure markers** we model as DocType/section identity — not as stored fields.
3. **Reuse reference masters; own the transactional children.** Pure lookup masters are shared verbatim. Repeating sub-blocks get **dedicated `House Airway Bill *` child tables** (see 1.3) to honor the "independent document" requirement and keep the bounded context clean.
4. **Incremental, migratable slices.** Every phase ends in a state that `bench migrate && bench build` cleanly and has passing tests. No phase leaves the schema half-defined.
5. **Independence with a typed link.** HWB does **not** become a child table of Shipment. It is a standalone submittable DocType with a  `Link` to `Shipment`. The one-to-many is surfaced on the Shipment via the **Connections/`links`** dashboard (Phase 6), not via embedding.

### 1.2 Relationship model (decision)

```
Shipment (Master AWB / MBI role)  1 ────────< many  House Airway Bill (HBS + sub-groups)
        ▲                                              │
        └──────────────  master_shipment (Link, reqd) ─┘
```

- **Rejected:** modeling HWBs as a child table on `Shipment`. Child rows are not independently submittable, addressable, permissioned, or amendable — all of which an HWB legally requires. ✗
- **Chosen:** standalone **submittable** `House Airway Bill` DocType + `master_shipment` Link + Shipment-side Connections panel. ✓

### 1.3 Reuse vs. create (decision matrix)

**Reuse as-is (reference masters — pure IATA code lists, stable):**

| Concern | DE | Existing master to reuse |
|---|---|---|
| Airport/City code (origin/dest) | 313 | `Airport` |
| ISO Country code | 304 | `Country` (Frappe core) |
| ISO Currency code | 606 | `Currency` (Frappe core) |
| Special Handling code | 705 | `Special Handling Code` |
| OCI Information Identifier (line id) | 103 | `OCI Information Identifier` |
| Customs/Security/Reg. Info Identifier | 941 | `Customs Information Identifier` |
| Party (shipper/consignee) | 300/301/302… | `Party` (+ `Party Contact`) |

**Create new — one parent + four dedicated child tables** (own the transactional/repeating data so HWB stays independent of Shipment's children):

| New DocType | Role | FHL ref | Repeats |
|---|---|---|---|
| `House Airway Bill` | Parent (submittable) — MBI link + HBS summary + SHP + CNE + CVD | 2,3,7,8,9 | — |
| `House Airway Bill Free Text` | TXT — free-text goods description | 3.1.2 | ≤ 9 |
| `House Airway Bill HS Code` | HTS — harmonised tariff codes | 3.1.3 | ≤ 9 |
| `House Airway Bill Customs Info` | OCI — customs/security/regulatory lines | 3.1.4 | repeatable |
| `House Airway Bill Special Handling` | SPH — special handling codes | 3.1.1.10 | ≤ 9 |

> **Why dedicate the children instead of reusing `Shipment Customs Info` / `Shipment Special Handling`?** They are structurally identical *today*, so reuse is technically possible (Frappe child tables can serve multiple parents). But the user requirement is explicit — HWB is an *independent* document. Dedicated children (a) avoid a `Shipment Customs Info` row type surfacing inside an HWB (confusing ownership), (b) let HWB-specific rules evolve (e.g. OCI continuation-qualifier ordering, HWB SLAC) without risk to live Shipment data, and (c) cost only ~4 tiny JSON files. **Recommendation: dedicate.** If the team prefers minimal surface area, reusing the two identical Shipment children is an acceptable fallback — note it and move on.

### 1.4 FHL message → model map (one consolidation list)

| FHL line | Constant | Lives in | Notes |
|---|---|---|---|
| Ref 1 SMI/version | `FHL/5` | *(EDX, out of scope)* | message envelope |
| Ref 2 MBI | `MBI` | **Shipment** (master) + denormalized onto HWB for context | airline prefix, AWB serial, O&D, T-pieces, weight |
| Ref 3 HBS | `HBS` | **House Airway Bill** core (HBS summary) | the spine of the HWB |
| Ref 3.10 SPH | `aaa` (705) | `House Airway Bill Special Handling` | ≤ 9 |
| Ref 4 TXT | `TXT` | `House Airway Bill Free Text` | ≤ 9 |
| Ref 5 HTS | `HTS` | `House Airway Bill HS Code` | ≤ 9 |
| Ref 6 OCI | `OCI` | `House Airway Bill Customs Info` | composition rules (FHL2/FHL30) |
| Ref 7 SHP | `SHP` | HWB Shipper section (Link `Party` + denormalized) | |
| Ref 8 CNE | `CNE` | HWB Consignee section (Link `Party` + denormalized) | |
| Ref 9 CVD | `CVD` | HWB Charge Declarations section | currency, P/C, NVD/NCV/XXX |

The "consolidation list" as a whole = **a Shipment plus the set of House Airway Bills that link to it.**

---

## 2. Target file layout

Standard Frappe 3-file pattern per DocType, under the existing module:

```
awbix/shipment/doctype/
├── house_airway_bill/
│   ├── __init__.py
│   ├── house_airway_bill.json          # schema
│   ├── house_airway_bill.py            # Document subclass (validation)
│   ├── house_airway_bill.js            # client (minimal; standard Desk only)
│   └── test_house_airway_bill.py       # FrappeTestCase
├── house_airway_bill_free_text/        # istable child  (TXT)
├── house_airway_bill_hs_code/          # istable child  (HTS)
├── house_airway_bill_customs_info/     # istable child  (OCI)
└── house_airway_bill_special_handling/ # istable child  (SPH)
```

Conventions to copy verbatim from existing DocTypes: tabs (`Tab Break`) → `Section Break` (`sb_*`) → `Column Break` (`cb_*`); `description: "DE###"` on every IATA field; `length` = IATA max; `fetch_from` for party denormalization; `editable_grid: 1`, `in_list_view: 1`, `grid_page_length: 50` on children; `engine: InnoDB`; `module: Shipment`.

---

## 3. Data model blueprint

### 3.1 `House Airway Bill` (parent, `is_submittable: 1`, `track_changes: 1`)

**Tab: Consignment**

*Section — Master AWB (MBI context)*
| Field | Type | DE | Len | Req | Notes |
|---|---|---|---|---|---|
| `master_shipment` | Link → `Shipment` | — | — | **M** | the consolidation parent |
| `master_awb_number` | Data (RO, `fetch_from` master) | — | — | | display |
| `airline_prefix` | Data/Link (RO fetch) | 112 | | | from master |
| `origin` *(master)* | Link → `Airport` (RO fetch) | 313 | | | MBI O |
| `destination` *(master)* | Link → `Airport` (RO fetch) | 313 | | | MBI D |

*Section — House Waybill Summary (HBS)*
| Field | Type | DE | Len | Req | Notes |
|---|---|---|---|---|---|
| `hwb_serial_number` | Data | 119 | 12 | **M** | `m[1...12]` alphanumeric |
| `hwb_number` | Data (RO, computed) | — | | | display key, see §5 |
| `hwb_origin` | Link → `Airport` | 313 | | **M** | house O&D (may differ from master) |
| `hwb_destination` | Link → `Airport` | 313 | | **M** | |
| `number_of_pieces` | Int | 701 | 4 | **M** | |
| `weight_code` | Select `K\nL` | 601 | | **M** | default `K` |
| `weight` | Float | 600 | | **M** | `n[...7]p` |
| `slac` | Int | 714 | 5 | O | Shipper's Load & Count |
| `manifest_description` | Data | 708 | 15 | **M** | `t[...15]` |

*Section — Special Handling (SPH)*: `special_handling` Table → `House Airway Bill Special Handling`

*Section — Free Text (TXT)*: `free_text` Table → `House Airway Bill Free Text`

*Section — Harmonised Tariff (HTS)*: `hs_codes` Table → `House Airway Bill HS Code`

**Tab: Parties**

*Section — Shipper (SHP)* — mirror Shipment's shipper block exactly:
`shipper` Link→`Party`; `shipper_name`(35) `shipper_account`(14) `shipper_address`(SmallText) `shipper_place`(17) `shipper_state`(9) `shipper_country`(Link Country) `shipper_post_code`(9) — all `read_only` + `fetch_from`; plus `shipper_contact_id`(DE122,3) `shipper_contact_number`(DE123,25).

*Section — Consignee (CNE)* — same shape with `consignee_*`.

**Tab: Customs & Charges**

*Section — Other Customs/Security/Reg. Info (OCI)*: `oci_customs` Table → `House Airway Bill Customs Info`

*Section — Charge Declarations (CVD)* — mirror Shipment:
`currency` Link→`Currency` (DE606, M); `wt_val_prepaid_collect` Select `P\nC` (DE403); `other_charges_prepaid_collect` Select `P\nC` (DE403); `declared_value_carriage_type` Select `NVD\nValue` + `declared_value_carriage_amount` Float (DE510); `declared_value_customs_type` Select `NCV\nValue` + `declared_value_customs_amount` Float (DE509); `insurance_type` Select `XXX\nValue` + `insurance_amount` Float (DE508).

**Tab: System** — `amended_from` (Link→`House Airway Bill`, RO, `no_copy`); optional collapsible **EDX Acknowledgement** section (`edx_ack_status` / `edx_ack_detail` / `edx_ack_at`, all RO) mirroring Shipment for forward-compatibility with the future FHL EDX flow. *(Fields only; no messaging logic.)*

Parent meta: `autoname` per §5; `title_field: "hwb_number"`; `sort_field: modified`; permissions cloned from `Shipment` (System Manager full incl. submit/cancel/amend).

### 3.2 Child tables

**`House Airway Bill Special Handling`** (`istable`)
| Field | Type | DE | Req |
|---|---|---|---|
| `special_handling_code` | Link → `Special Handling Code` | 705 | M |
| `description` | Data (RO, `fetch_from` code.description) | — | |

**`House Airway Bill Free Text`** (`istable`)
| Field | Type | DE | Len |
|---|---|---|---|
| `free_text` | Small Text | 127 | 65 |

**`House Airway Bill HS Code`** (`istable`)
| Field | Type | DE | Len |
|---|---|---|---|
| `hs_code` | Data | 900 | 18 |

**`House Airway Bill Customs Info`** (`istable`) — same four columns as `Shipment Customs Info`
| Field | Type | DE | Len |
|---|---|---|---|
| `country` | Link → `Country` | 304 | |
| `information_identifier` | Link → `OCI Information Identifier` | 103 | |
| `customs_info_identifier` | Link → `Customs Information Identifier` | 941 | 2 |
| `supplementary` | Data | 940 | 35 |

> OCI **continuation/qualifier** lines from the samples (`///ED/1026`, `///SM/EDD`, `///SN/PMT`, `///SD/…`, `///ST/…`) map to **additional rows** where `country`/`information_identifier` are blank and only `customs_info_identifier` + `supplementary` are filled. Frappe preserves grid `idx` order, so sequence is retained without an extra field.

---

## 4. Phased delivery plan

Each phase: **Objective → Build → Validate (Python) → Tests → Exit criteria.** Exit always includes `ruff check/format`, `bench migrate`, `bench build`, and green `bench run-tests --doctype "House Airway Bill"`.

### Phase 0 — Foundation & sign-off  *(no code)*
- **Objective:** lock the decisions in §1 (relationship, reuse-vs-create, naming/uniqueness, OCI strategy).
- **Build:** confirm masters from §1.3 all exist and are populated as fixtures (they are — see `hooks.py fixtures`). Confirm no *new* master is required (TXT is free text; HTS is a raw HS-code Data field; SPH/OCI/Country/Currency masters already exist).
- **Exit:** this plan reviewed; field-by-field map (Appendix A) accepted as the build checklist.

### Phase 1 — Reference-data gap analysis  *(verify only)*
- **Objective:** prove every `Link` target resolves before building dependents.
- **Build:** verify `Airport`, `Country`, `Currency`, `Special Handling Code`, `OCI Information Identifier`, `Customs Information Identifier`, `Party` are migratable and seeded. No schema change expected.
- **Exit:** documented confirmation; if any list is empty in CI, add seed fixtures. **No new masters created.**

### Phase 2 — Core `House Airway Bill` parent (MBI + HBS)
- **Objective:** the spine — a standalone, submittable HWB linked to its master, carrying the HBS summary.
- **Build:** parent JSON with the **Master AWB** and **House Waybill Summary** sections only (tables/parties/charges added later). `house_airway_bill.py`, `.js` (standard), `test_*.py`.
- **Validate (Python `validate()`):**
  - `set_hwb_number()` — compose display key (mirrors `Shipment.set_awb_number`).
  - `hwb_serial_number` format — 1–12 chars, `m[1...12]` (alphanumeric), per DE119.
  - `(master_shipment, hwb_serial_number)` **uniqueness** — reject duplicate house serial under the same master (§5).
  - `number_of_pieces > 0`, `weight > 0`, `manifest_description` present.
  - `hwb_origin != hwb_destination`.
- **Tests:** insert valid HWB; reject blank/over-12 serial; reject duplicate serial per master; reject same O&D; auto-name/`hwb_number` correctness.
- **Exit:** create/submit/amend a House Airway Bill in Desk; tests green.

### Phase 3 — Goods narrative children (SPH + TXT + HTS)
- **Objective:** repeating goods/handling detail.
- **Build:** `House Airway Bill Special Handling`, `House Airway Bill Free Text`, `House Airway Bill HS Code`; wire as `Table` fields on parent.
- **Validate:** each table capped at **9 rows** (FHL: SPH/TXT/HTS "max nine times"); SPH code required per row; HTS `m[6...18]` length; TXT `t[...65]` length.
- **Tests:** add rows; 10th row rejected per table; SPH description fetch; length guards.
- **Exit:** tables editable in grid; tests green.

### Phase 4 — Parties (SHP + CNE)
- **Objective:** shipper & consignee, identical UX to Shipment.
- **Build:** Parties tab with `shipper`/`consignee` `Link → Party` + `fetch_from` denormalized address fields + contact id/number.
- **Validate:** **FHL24** — if SHP present, CNE must be present (and vice-versa for a fully-expanded HWB); contact identifier ∈ {`FX`,`TE`,`TL`} (DE122); coded-location + contact combined length ≤ 69 (FHL22/FHL26) — implement as a soft length guard.
- **Tests:** party fetch populates name/address; SHP-without-CNE rejected; contact-id domain.
- **Exit:** parties round-trip; tests green.

### Phase 5 — Customs/Security (OCI) + Charge Declarations (CVD)
- **Objective:** the compliance + money block; highest validation density.
- **Build:** `House Airway Bill Customs Info` table + CVD section.
- **Validate:**
  - **OCI composition (FHL2 + FHL30 + OCI rules table):** per row, **at least one** of `country` / `information_identifier` / `customs_info_identifier` present; enforce the high-value identifier rules from the manual incrementally — e.g. `ED`/`SM`/`SN`/`SD`/`SS` rows must follow an `RA`/`KC` issuer row; `SS` only one per HWB; screening **method/exemption/status** codes belong in `supplementary` (DE940), **not** in the identifier. Start with the "≥1 of three" rule (hard) + issuer-ordering (warn), harden over time.
  - **CVD:** if type = `NVD`/`NCV`/`XXX` then the matching amount must be empty; if type = `Value` the amount is required and must be in range (DE510/509/508). `currency` required.
- **Tests:** empty OCI row rejected; NVD-with-amount rejected; Value-without-amount rejected; currency required; ordering/`idx` preserved for continuation rows.
- **Exit:** full HWB (all sub-groups) saves & submits; tests green.

### Phase 6 — Shipment integration & consolidation consistency
- **Objective:** make the one-to-many first-class and reconcile house↔master totals.
- **Build:**
  - Add a **Connections** entry on `Shipment` (`links` array / dashboard) → `House Airway Bill` via `master_shipment`, so a Shipment shows "House Airway Bills (n)".
  - Optional helper: server method returning consolidation rollups (Σ house pieces, Σ house weight).
- **Validate (on HWB, against master):**
  - house `weight` and `number_of_pieces` consistent with the master consignment (e.g. Σ houses ≤ master totals) — implement as a **warning/`msgprint`** first (consolidations legitimately build up over time), promote to hard check only if the business demands.
  - currency/O&D sanity vs master where business rules require.
- **Tests:** Shipment shows linked HWBs; rollup math; over-allocation warns.
- **Exit:** navigable Shipment↔HWB; tests green.

### Phase 7 — Hardening, permissions, workspace, fixtures, docs
- **Objective:** production-readiness.
- **Build:**
  - Permissions/roles cloned from `Shipment` (consider a dedicated `Cargo User` role split if required).
  - **Workspace:** add a `House Airway Bill` shortcut/link card to the **Shipment** workspace (per the scope note) so it is reachable next to `Shipment`.
  - Add new DocTypes to **`fixtures`** in `hooks.py` only if any carries seed/reference rows (the four children and the parent are transactional → typically **not** fixtures; double-check before adding).
  - Update `awbix/shipment/CLAUDE.md` DocType hierarchy + the root `CLAUDE.md` child-table table.
  - Full `test_house_airway_bill.py` suite; run `pre-commit run --all-files`.
- **Validate:** end-to-end create→submit→amend→cancel lifecycle; `bench run-tests --module shipment` green.
- **Exit:** merged; CI (`ci.yml` + `linter.yml`) green.

---

## 5. Naming & uniqueness (decision)

- **HWB serial numbers are agent-assigned** and only unique *within a forwarder/master* — two different masters can legitimately reuse a serial. So **do not** globally unique-name by serial.
- **Chosen:** `autoname` = **naming series** `HWB-.#####`, plus a computed read-only **`hwb_number`** display field = `"{master_awb_number} / {hwb_serial_number}"` (mirrors how `Shipment` computes `awb_number`), and a **Python uniqueness guard** on the pair `(master_shipment, hwb_serial_number)`. `title_field: "hwb_number"`.
- **Rejected:** `autoname: format:{hwb_serial_number}` (collides across masters) and `field:hwb_serial_number` (global-unique constraint is wrong for HWB).

---

## 6. Validation catalog (consolidated)

| Rule | Source | Phase | Severity |
|---|---|---|---|
| HWB serial `m[1...12]`, non-blank | DE119 / CSV 3.1.1.3 | 2 | error |
| `(master, serial)` unique | enterprise integrity | 2 | error |
| pieces > 0, weight > 0, manifest desc present | CSV M flags | 2 | error |
| `hwb_origin != hwb_destination` | mirrors Shipment | 2 | error |
| SPH / TXT / HTS ≤ 9 rows | FHL §3.10, §4, §5 | 3 | error |
| HTS `m[6...18]`, TXT `t[...65]` lengths | DE900 / DE127 | 3 | error |
| CNE required if SHP present | FHL24 | 4 | error |
| Contact id ∈ {FX,TE,TL} | DE122 / 1.39 | 4 | error |
| Coded-loc + contact ≤ 69 chars | FHL22/FHL26 | 4 | warn |
| OCI row: ≥1 of country/info-id/customs-id | FHL30 | 5 | error |
| OCI identifier ordering (ED/SM/SN/SD after RA/KC; SS once) | FHL2 + rules table | 5 | warn→error |
| CVD NVD/NCV/XXX ⇒ no amount; Value ⇒ amount in range | DE510/509/508 | 5 | error |
| Σ house pieces/weight vs master | consolidation logic | 6 | warn |

---

## 7. Testing strategy

- `FrappeTestCase`; `frappe.new_doc("House Airway Bill")` → set fields → `.insert()` triggers `validate()`; assert `frappe.ValidationError` for negative cases (same pattern noted in `shipment/CLAUDE.md`).
- Build a `make_hwb(**overrides)` helper that depends on a seeded master `Shipment` + masters.
- Per-phase tests land **with** that phase (no deferred testing).
- Commands: `bench run-tests --doctype "House Airway Bill"`, `bench run-tests --module shipment`.

---

## 8. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Over-coupling HWB to Shipment's children | Dedicated `House Airway Bill *` children (§1.3) |
| OCI composition complexity | Phase it: hard-enforce "≥1 of three" first, layer identifier-specific rules as warnings, promote later |
| Serial uniqueness wrong globally | Scope uniqueness to `(master, serial)` (§5) |
| Consolidation totals block legitimate partial build-up | Start as warnings, not hard errors (Phase 6) |
| Master fixtures empty in CI → Link failures | Phase 1 gate verifies/seeds before dependents |
| Scope creep into messaging | EDX-ack fields are placeholders only; **no** FHL serialize/parse in this plan |

---

## 9. Explicitly out of scope

FHL message generation/parsing & all EDX transport; non-standard frontend (portal/custom UI); reporting/print formats beyond Frappe defaults; cross-app integrations. These consume the model later; they are not built here.

---

## Appendix A — Field map (build checklist, keyed to `FHL_RULE_BY_SEQ.csv`)

| CSV seq | FHL element | Constant | M/O | DE | Format | HWB field | Type/Len |
|---|---|---|---|---|---|---|---|
| 2.3.x | Master AWB id | MBI | M | 112/113 | nnn / n[8] | `master_shipment` (+fetch) | Link |
| 2.4.x | Master O&D | — | M | 313 | aaa | fetched from master | Link Airport |
| 3.1.1.3 | HWB serial | HBS | M | 119 | m[1...12] | `hwb_serial_number` | Data/12 |
| 3.1.1.5.x | House O&D | — | M | 313 | aaa | `hwb_origin`/`hwb_destination` | Link Airport |
| 3.1.1.7.1 | Pieces | — | M | 701 | n[...4] | `number_of_pieces` | Int |
| 3.1.1.7.3 | Weight code | — | M | 601 | a | `weight_code` | Select K/L |
| 3.1.1.7.4 | Weight | — | M | 600 | n[...7]p | `weight` | Float |
| 3.1.1.7.6 | SLAC | — | O | 714 | n[...5] | `slac` | Int |
| 3.1.1.8.2 | Manifest desc | — | M | 708 | t[...15] | `manifest_description` | Data/15 |
| 3.1.1.10.2 | Special handling | — | M* | 705 | aaa | `House Airway Bill Special Handling` | child ≤9 |
| 3.1.2.3 | Free text | TXT | M* | 127 | t[...65] | `House Airway Bill Free Text` | child ≤9 |
| 3.1.3.3 | HS code | HTS | M* | 900 | m[6...18] | `House Airway Bill HS Code` | child ≤9 |
| 3.1.4.3 | ISO country | OCI | O | 304 | aa | `…Customs Info.country` | Link |
| 3.1.4.5 | Info identifier | — | O | 103 | aaa | `…Customs Info.information_identifier` | Link |
| 3.1.4.7 | Customs info id | — | M | 941 | a[...2] | `…Customs Info.customs_info_identifier` | Link/2 |
| 3.1.4.9 | Supplementary | — | M | 940 | t[...35] | `…Customs Info.supplementary` | Data/35 |
| 3.1.5.3.3 | Shipper name | SHP/NAM | M | 300 | t[...35] | `shipper_name` (fetch) | Data/35 |
| 3.1.5.4.3 | Shipper address | ADR | M | 301 | t[...35] | `shipper_address` (fetch) | Small Text |
| 3.1.5.5.3/.5 | Shipper place/state | LOC | M/O | 302/303 | t[...17]/t[...9] | `shipper_place`/`shipper_state` | Data |
| 3.1.5.6.x | Shipper country/post | — | M/O | 304/305 | aa/t[...9] | `shipper_country`/`shipper_post_code` | Link/Data |
| 3.1.5.7.x | Shipper contact | — | O | 122/123 | m[...3]/m[...25] | `shipper_contact_id`/`_number` | Data |
| 3.1.6.x | Consignee (NAM/ADR/LOC/contact) | CNE | M* | 300/301/302/303/304/305/122/123 | — | `consignee_*` | mirror shipper |
| 3.1.7.3 | Currency | CVD | M | 606 | aaa | `currency` | Link |
| 3.1.7.5.x | P/C indicators | — | M | 403 | a | `wt_val_prepaid_collect`/`other_charges_prepaid_collect` | Select P/C |
| 3.1.7.6.x | Value carriage / NVD | — | M | 510 | n[...12]p\|NVD | `declared_value_carriage_type`+`_amount` | Select+Float |
| 3.1.7.7.x | Value customs / NCV | — | M | 509 | n[...12]p\|NCV | `declared_value_customs_type`+`_amount` | Select+Float |
| 3.1.7.8.x | Value insurance / XXX | — | M | 508 | n[...11]p\|XXX | `insurance_type`+`_amount` | Select+Float |

\* "M*" = the **sub-group is optional**, but **when present** these fields are mandatory (per CSV nesting/condition codes).

---

## Appendix B — Worked reference (from `fhl sample message.txt`)

```
MBI/157-69081003AMSYUL/T1K610      → master = Shipment 157-69081003, AMS→YUL, 1pc 610K
HBS/SAMSA0009420/AMSYUL/1/K610.0// → HWB serial SAMSA0009420, AMS→YUL, 1pc, 610.0K, (no SLAC), manifest desc
/SPX/EAW                           → SPH rows: SPX, EAW
TXT/GROUND FLIGHT TRAINING EQUIP…  → Free Text rows (continuation /…)
HTS/880529                         → HS Code row 880529
OCI/NL/EXP/M/26NL4O34OG29FTZDA3    → OCI row: country NL, id EXP, customs-id M, supplementary …
//HWB/I/SAMSA0009420               → OCI continuation row (country/id blank)
SHP NAM/SIMZATION BV …             → Shipper party block
CNE NAM/CAE INC. …                 → Consignee party block
CVD/EUR/CC/NVD/NCV/XXX             → currency EUR, P/C=C/C, NVD, NCV, XXX
```
This single block ↔ **one `House Airway Bill`** document linked to the `Shipment` named `157-69081003`.
