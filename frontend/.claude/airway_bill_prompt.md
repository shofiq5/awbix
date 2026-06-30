# Prompt: Build the Air Waybill List + Form in the Vue.js Frontend

> This is the engineering brief to hand to Claude (or any implementer) to build the feature described in `airway_bill_plan.md`. It is self-contained: backend contracts, field inventory, UX layout, and acceptance criteria are all specified below so no further discovery is needed before coding starts.

## 1. Objective

Build an **Air Waybill (AWB) list page and a multi-tab AWB form page** in the existing `frontend/` Vue 3 SPA, backed by the `Shipment` DocType and its child tables. This is the primary operational screen of AWBix — it must feel like a purpose-built cargo desk tool, not a generic CRUD form.

Scope is **data entry only**. The Charge Summary section (`charge_summary` / `shipment_charge_summary`) is entirely out of scope — it is server-computed from other data elements (`Shipment.populate_charge_summary()` in `shipment.py`) and must never be rendered or edited on this screen.

## 2. Where this fits in the codebase

- **Backend DocType:** `awbix/shipment/doctype/shipment/shipment.py` / `.json` — read this file before writing any code; it is the source of truth for field names, validation, and computed behavior (uppercase enforcement, AWB check-digit validation, dimension/volume-weight computation, Shipment Settings defaults).
- **Frontend app:** `frontend/` — Vue 3 + `vue-router` + Tailwind, using `frappe-ui`'s design language but with hand-rolled components (no heavy component library dependency observed yet — confirm current `frappe-ui` usage before adding new dependencies).
- **Existing precedent to copy conventions from:** `frontend/src/pages/PartyList.vue` and `frontend/src/pages/PartyForm.vue`. These establish the house style:
  - CSS custom properties for theme (`var(--color-surface)`, `var(--color-border)`, `var(--color-primary)`, etc.) — **reuse these tokens, do not hardcode colors.**
  - The local `<Icon name="..." :size="N" />` wrapper (`src/components/ui/Icon.vue`). **IMPORTANT: this does NOT wrap the `feather-icons` npm package at runtime** — it renders SVG inner-paths from a *hardcoded dictionary* in `src/utils/icons.js` (`getSvgPath(name)` returns `iconSvgs[name] ?? null`). Only ~40 names exist there; **any name not in that dict renders nothing.** Before building the right-side rail (which needs icons like `truck`, `box`, `dollar-sign`, `globe`, `clipboard`, `printer`, `upload`, `more-horizontal`, `map-pin` — none of which exist yet), you MUST first add those SVG paths to `icons.js` (copy the inner-path markup from feather-icons). Existing usable names to prefer where they fit: `file-text, users, package, list, alert-triangle, settings, search, plus, save, trash-2, x, filter, phone, briefcase`.
  - Manual `fetch()` wrapped in local `apiGet`/`apiPost` helpers with CSRF header (`X-Frappe-CSRF-Token`) and a `parseErr()` helper that unpacks Frappe's `_server_messages` error envelope — replicate this pattern, don't introduce axios or a different HTTP client.
  - Toast notifications via a local `reactive` toast object + `<Transition>`, not a toast library.
  - `reactive(form)` for flat fields, `ref([])` for child table arrays.
  - Tab bar pattern (`activeTab` ref + `v-show`) for sectioned forms.
- **Routing:** `frontend/src/router.js` already has a **stub route** at `path: 'awb', name: 'AWBList'` pointing at `Placeholder.vue` — replace this with the real `AWBList.vue`, and add two new routes `awb/new` (`AWBNew`) and `awb/:name` (`AWBEdit`) pointing at `AWBForm.vue`, following the exact pattern used for `parties` / `parties/new` / `parties/:name`.
- **Navigation:** `frontend/src/config/navigation.js` already lists `{ id: 'awb', label: 'Air Waybills', icon: 'file-text', route: '/awb' }` under the "Shipments" group — no change needed there, but verify the icon/label still make sense once built.
- **Backend API to extend:** `awbix/frontend_api.py` — currently only has Party endpoints (`get_parties`, `get_party`, `save_party`, `delete_party`) plus `get_session_info`. You will add the AWB equivalents here, following the exact same function signatures, whitelisting (`@frappe.whitelist(allow_guest=False)`), and JSON-shape conventions.

## 3. Required new backend endpoints (`awbix/frontend_api.py`)

Add three whitelisted methods, mirroring the Party endpoints' shape and error-handling conventions exactly:

```python
@frappe.whitelist(allow_guest=False)
def get_shipments(page=0, page_size=20, search=None, origin=None, destination=None, docstatus=None):
    # list view: search by awb_number (LIKE), filter by origin/destination/docstatus
    # return {'total': int, 'rows': [...]}
    # rows fields: name, awb_number, origin, destination, weight, chargeable_weight,
    #              currency, docstatus, modified, shipper_name, consignee_name

@frappe.whitelist(allow_guest=False)
def get_shipment(name):
    # full doc fetch — every field needed by the form (see field inventory below),
    # PLUS all child tables fully expanded as lists of dicts.
    # Build the dict with an EXPLICIT field allowlist (mirror get_party), one key
    # per flat field + a list-comp per child table emitting only its real columns.
    # Do NOT use doc.as_dict()-and-strip: as_dict() leaks charge_summary,
    # shipment_fsu, docstatus, owner, child rowids, etc., and re-leaks every time
    # the doctype grows. The allowlist documents the FE contract in one place.
    # MUST include the hidden `dimensions` child table (needed to re-seed the
    # dimensions modal on reload — see §4.3), plus the computed read-only scalars
    # (awb_number, volume_weight, chargeable_weight) and agent_* fetch fields for
    # display. Optionally include charge_summary (display-only) and edx_ack_*.

@frappe.whitelist(allow_guest=False)
def save_shipment(data):
    # mirrors save_party: parse JSON if string, new_doc vs get_doc by `name` presence,
    # assign every flat field, rebuild every child table from scratch (doc.<table> = []
    # then doc.append(...) per row), doc.save(), frappe.db.commit().
    # CHILD-TABLE KEYS MUST MATCH THE DOCTYPE EXACTLY — doc.append() silently drops
    # unknown keys (= silent data loss). Use the verified fieldnames in §4 (note
    # notify_name / participant_name / other_service_information).
    # IMPORTANT: do NOT let the frontend send charge_summary rows — ignore that key
    # entirely if present (it's server-derived). Likewise NEVER assign the hidden
    # shipment_fsu table or the read-only awb_number / volume_weight /
    # chargeable_weight / agent_* / edx_ack_* fields (all server-set/fetched).
    # DO send the raw `dimensions` rows (see §4.3) — the server recomputes volume
    # weights from them on every save.
    # Let frappe's own validate() raise — catch frappe.ValidationError and let it
    # propagate so parseErr() on the frontend surfaces the real message
    # (e.g. AWB check-digit errors, origin==destination, etc.)

@frappe.whitelist(allow_guest=False)
def delete_shipment(name):
    # only allowed when docstatus == 0 (draft) — frappe.delete_doc will already
    # refuse submitted docs, just let that error surface naturally.
```

Also expose two small lookup endpoints the form will need for autocomplete/typeahead (Link fields with potentially large tables — don't dump full lists):

```python
@frappe.whitelist(allow_guest=False)
def search_link(doctype, txt="", limit=20):
    # generic Link-field search, restricted to an allow-list of doctypes used on
    # this form: Airport, Airline, Party, Currency, Country, Rate Class Code,
    # Charge Code, Other Charge Code, Special Handling Code, Service Code,
    # Volume Code, Measurement Unit Code, ULD Type, Accounting Information Identifier,
    # Customs Information Identifier, OCI Information Identifier.
    # frappe.throw if doctype not in the allow-list — this prevents arbitrary
    # doctype enumeration through this endpoint.
```

Reuse the existing dimension-calculation endpoints already in `shipment.py` from the Python side directly — do not duplicate that math in JS:
- `awbix.shipment.doctype.shipment.shipment.calculate_dimension_totals` — call this from the frontend whenever the dimensions popup changes, to preview volume/volume-weight/chargeable-weight before save.
- `awbix.shipment.doctype.shipment.shipment.parse_dimension_file` — wire this to the dimensions popup's CSV/XLSX upload button.

## 4. Field inventory (what the form must cover)

Everything below is sourced directly from `shipment.json` and its child DocTypes. **Exclude `charge_summary` entirely.**

### 4.1 Header / AWB identity (always visible, top of form — paper-AWB style)
| Field | Type | Notes |
|---|---|---|
| `airline_prefix` | Data(3), reqd, uppercase | DE112 |
| `awb_serial_number` | Data(8), reqd | DE113 — 8 digits, mod-7 check digit on last digit |
| `awb_number` | Data, read-only | auto = `{airline_prefix}-{awb_serial_number}` |
| `origin` | Link→Airport, reqd-by-business-rule | defaults from Shipment Settings |
| `destination` | Link→Airport, reqd-by-business-rule | defaults from Shipment Settings; must differ from origin |
| `e_awb` | Check | "Electronic AWB" toggle |
| `console` | Check | consolidation flag |

### 4.2 Mandatory minimum section (render first, above the fold)
Per the plan's instruction "First All Mandatory minimum section": airline_prefix, awb_serial_number, origin, destination, number_of_pieces, weight, weight_code, shipper (name/address/place), consignee (name/address/place), currency, at least one rate line. Everything else is optional/secondary.

| Field | Type | Notes |
|---|---|---|
| `number_of_pieces` | Int | DE701 |
| `weight` | Float | DE600 |
| `weight_code` | Select (K/L), default K | DE601 |
| `volume_amount` | Float | DE500 — can be auto-derived from dimensions popup |
| `volume_weight` | Float, read-only | computed server-side |
| `chargeable_weight` | Float, read-only | computed server-side (`max(weight, volume_weight)`) |
| `volume_weight_factor` | Int, default 6000 | cm³/kg divisor — **NOTE: there is NO Shipment Settings default for this**; initialize it to `6000` client-side on new forms (the brief elsewhere implies it is settings-driven; it is not). |
| `currency` | Link→Currency, reqd | defaults from Shipment Settings |

### 4.3 Dimensions popup (modal, triggered from the mandatory section)
Backing table: `dimensions` → `shipment_dimension` rows.

| Field | Type | Notes |
|---|---|---|
| `line_number` | Int | auto-assigned |
| `pieces` | Int, default 1 | |
| `length`, `width`, `height` | Float, precision 2 | |
| `dim_unit` | Select (cm/in/m), default cm | |
| `volume` (m³), `volume_weight` (kg) | Float, read-only | computed per-row server-side |
| `remarks` | Small Text | |

Modal behavior:
- Editable grid (add/remove row), with a CSV/XLSX **upload button** wired to `parse_dimension_file` — show per-row import errors inline (the endpoint returns `{rows, errors: [{row, message}]}`).
- "Recalculate" or live-recalculate-on-change calling `calculate_dimension_totals`, showing a live preview footer: total m³, volume weight, suggested chargeable weight — before the user commits by closing the modal (commit = copy results back into the parent form's `volume_amount`/`volume_weight`/`chargeable_weight` fields, mirroring exactly what `compute_dimensions()` does server-side so there's no drift between preview and what save() will compute).
- This is the plan's explicit ask: *"Use pop-up window where require like dimension."*

> **⚠️ Dimensions round-trip — read carefully, this is the subtlest correctness issue on the form.**
> `dimensions` is a **hidden** child table, and on every save `validate()` → `compute_dimensions()` **recomputes** `volume_weight` and `chargeable_weight` from the *raw dimension rows*. Therefore:
> - The form's source of truth is the **raw rows** (`pieces, length, width, height, dim_unit, line_number, remarks`) — **NOT** the per-row `volume`/`volume_weight` (those are server-computed; never send them).
> - `save_shipment` **must send the raw rows**, and `get_shipment` **must return them**, so reopening a saved AWB re-seeds the modal and the scalars don't reset.
> - If you send only the computed scalars (`volume_weight`/`chargeable_weight`) without the rows, the server recomputes from empty rows and **zeroes them** → values visibly "jump" after save. Don't.
> - To guarantee preview == server result (no jump): the modal's `calculate_dimension_totals` call MUST pass the *same* `weight`, `volume_weight_factor`, `volume_amount`, and `volume_code` that will be saved (bind them to the same `form` object). Committing the modal copies the previewed `volume_weight`/`chargeable_weight`/suggested `volume_amount` into the parent purely for instant display — the authoritative values still come from the server on reload.

### 4.4 Right-side vertical tab rail — Parties (Shipper + Consignee + Agent + Notify + Other Participants)

Per the plan: *"Right Side vertical tab to select section like Party (Shipper+Consignee+Agent)."* Implement this as a **vertical icon+label tab rail** docked to the right edge of the form card (not the horizontal pill-tab pattern used in `PartyForm.vue` — this is a deliberate UX difference requested by the plan). Each rail item switches the visible panel; the rail itself stays pinned so users can jump between AWB sections without scrolling.

**Shipper** (flat fields, no child table):
`shipper_name`(35), `shipper_account`(uppercase), `shipper_address`(35), `shipper_place`(17), `shipper_state`(9), `shipper_country`(Link→Country), `shipper_post_code`(9) — all uppercase-enforced server-side, mirror with `text-transform:uppercase` styling client-side for visual parity, but still send raw text (server is authoritative).

**Consignee**: identical shape to Shipper, fields prefixed `consignee_*`.

**Agent**: `agent`(Link→Party, triggers fetch), `agent_name`, `agent_place`, `agent_account`, `agent_iata_code`(7), `agent_cass_address`(4), `agent_participant_id`(3) — note several of these are `read_only` / `fetch_from` in the doctype (fetched from the linked Party) — render them read-only/greyed-out in the UI to match, don't make them independently editable.

**Also Notify** — child table `also_notify` → `shipment_notify_party`. **Exact fieldnames (verified):** `party`(Link→Party), `notify_name`(**REQUIRED**, fetched from `party.party_name` — note the field is `notify_name`, NOT `name`), `street_address`, `place`, `state_province`, `country`(Link→Country), `post_code` (all fetched from the party), `telephone`, `fax` (entered). Render as a repeatable card list (not a dense grid — these are full addresses), max expect 0-2 rows typically.

**Other Participants** — child table `other_participants` → `shipment_other_participant`. **Exact fieldnames (verified):** `participant_name`(35) (NOT `name`), `office_file_reference`(15), `participant_id`(3), `participant_code`(17), `airport`(Link). Render as a simple add/remove table — this is a rare/advanced field, keep it visually de-emphasized (e.g. collapsed by default).

### 4.5 Vertical tab rail — Routing & Flights

**Flight Bookings** — child table `flight_bookings` → `shipment_flight_booking`: carrier(Link→Airline, reqd), carrier_code(read-only fetch), flight_number(5), flight_day(2)+flight_month(Select JAN-DEC) as a combined date-ish picker, departure_airport/arrival_airport(Link→Airport), space_allocation_code(Select: NN/NA/SS/CA/XX/HK/HL/HN/KK/UU/UN/LL — render as a labeled dropdown, these are IATA allotment codes, add tooltips), allotment_id(14).

**Routing** — child table `routing` → `shipment_routing`: sequence(Int, drag-to-reorder if feasible, else numeric input), airport(Link), carrier(Link→Airline), carrier_code(read-only fetch). This models the RTG IATA segment — first destination + up to 2 onward — keep the UI capped visually at a sensible row count matching that constraint, but don't hard-block extra rows client-side (server doesn't enforce a cap here per the explored code).

**Legacy single-route fields** (`to_airport1`/`by_carrier1`/`to_airport2`/`by_carrier2`) exist on the parent — confirm with backend owner whether these are superseded by the `routing` child table before deciding whether to surface them; default to showing them only if non-empty on load (legacy/back-compat display), not as a primary input path.

### 4.6 Vertical tab rail — Goods & Rate Lines

**Rate Lines** — child table `rate_lines` → `shipment_rate_line` (**mandatory: at least one row** — though the hard validation throw was removed server-side, the UI should still nudge/require this since it drives chargeable totals):
line_number, number_of_pieces, rate_class_code(Link), gross_weight + gross_weight_code(K/L), chargeable_weight, rate_charge, total, goods_data_identifier(Select G/C), description(20, "Nature of Goods"), rate_combination_point(3), commodity_item_number(7), rate_class_percentage, uld_rate_class_type(4).
This is the densest table on the form — use a true spreadsheet-style editable grid (tab-to-next-cell, numeric inputs right-aligned) rather than stacked form fields.

There's an `auto_rate_line` **Button** field on the parent. **⚠️ There is NO server-side handler to "wire up" — the logic lives ONLY in `shipment.js` (desk client script, ~lines 34-53), which the SPA cannot reach.** Reimplement it as a Vue method that mirrors `shipment.js` exactly: clear `rate_lines`, then append one row from the header — `line_number=1`, `number_of_pieces`←header pieces, `gross_weight_code`←`weight_code`, `gross_weight`←`weight`, `chargeable_weight`←header `chargeable_weight`, `rate_class_code="Q"`, `description`←`nature_of_goods`, `goods_data_identifier = console ? 'C' : 'G'`, `commodity_item_number`←`commodity_item_no`, `rate_charge`←`iata_rate`, `total = iata_rate * chargeable_weight` (for "Q"; flat `iata_rate` for "M"). **Add a `// MIRRORS shipment.js auto_rate_line — keep in sync` comment.** This duplicates logic across desk JS and the SPA; see Open Question #1 about promoting it to a shared whitelisted method.

**Goods Details** — child table `goods_details` → `shipment_goods_detail`: this is the IATA RTD "second line" data (goods description, dimensions-in-rate-line, volume, ULD number, SLAC, HS code, country of origin, service code) keyed by `goods_data_identifier` (G/C/D/V/U/S/H/O). **Each row also carries a `rate_line_number` (Int) linking it back to a rate line** — round-trip it (a dropdown of existing rate-line numbers is ideal; no FK is enforced server-side). Render as an editable table where the visible input fields change based on the selected identifier (e.g. selecting "D" shows dim_length/width/height/pieces/dim_weight_code, selecting "H" shows just hs_code). This mirrors the ABNF grammar's `RTD_SecondLine` alternation — don't try to show all 19 columns at once, it'll be unusable.

**Other Charges** — child table `other_charges` → `shipment_other_charge`: prepaid_collect(P/C), other_charge_code(Link→Other Charge Code, reqd), amount. Simple 3-column table.

**Top-level rate/value fields** (render in a compact strip above the Rate Lines grid): `iata_rate`, `rate_class`, `charge_code`(Link), `wt_val_prepaid_collect`(P/C), `other_charges_prepaid_collect`(P/C), `declared_value_carriage_type`(NVD/Value)+`declared_value_carriage_amount`, `declared_value_customs_type`(NCV/Value)+`declared_value_customs_amount`, `insurance_type`(XXX/Value)+`insurance_amount`. The `*_type` Select fields toggle whether the paired `*_amount` input is shown/enabled — when type is the "no value" sentinel (NVD/NCV/XXX) grey out and zero the amount field.

### 4.7 Vertical tab rail — Special Services & Compliance

**Special Service Requests** — child table `special_service_requests` → `shipment_special_service_request`: single field `special_service_request`(65 chars free text), max ~3 rows per the ABNF grammar (`1*3`). Simple repeatable text-line list, soft-cap the UI at 3 with a friendly message rather than a hard block.

**Special Handling** — child table `special_handling` → `shipment_special_handling`: special_handling_code(Link, reqd) + description(read-only fetch). Render as a multi-select-style tag picker if feasible (these are short IATA codes like "PER", "VAL"), falling back to a simple add-row table.

**Other Service Information** — child table `other_service_info` → `shipment_other_service_info`: single field `other_service_information`(65 chars), max 3 rows (ABNF `1*3`).

**Customs / OCI** — child table `oci_customs` → `shipment_customs_info`: country(Link), information_identifier(Link→OCI Information Identifier), customs_info_identifier(Link→Customs Information Identifier), supplementary(35). Plus parent-level `customs_origin_code`. Group these together under one "Customs" rail item.

**Accounting Information** — child table `accounting_information` → `shipment_accounting_info`: identifier(Link→Accounting Information Identifier, reqd), information(34). Simple 2-column table.

**Nominated Handling** — parent fields `nominated_handling_name`(35), `nominated_handling_place`(17). Two plain inputs.

**References** — child table `references` → `shipment_reference`: reference_number(14), supplementary_1(12), supplementary_2(12). Simple 3-column table.

### 4.8 Vertical tab rail — Certification, Commission & Sender Info (the "fine print" tab — lowest priority, render last)

Certification: `shippers_certification_signature`(20), `issue_date`(Date), `issue_place`(17), `carrier_execution_signature`(20).
Commission: `no_commission_indicator`, `commission_amount`, `commission_percentage`.
Sales incentive: `sales_incentive_amount`, `sales_incentive_indicator`, `agent_reference`.
Sender / EDX: `sender_file_reference`(15), `sender_office_address`(defaults from Shipment Settings), `sender_participant_id`(3), `sender_participant_code`(17). `edx_ack_status`/`edx_ack_detail`/`edx_ack_at` are **read-only system fields** — display them but never make them editable.
CDC (collect charges in destination currency): `cc_dest_currency`, `rate_of_exchange`, `cc_charges_dest`, `charges_at_dest`, `total_collect_charges` — only show this block if `wt_val_prepaid_collect == 'C'` or any other-charge row is marked Collect; otherwise hide it (it's meaningless for an all-prepaid AWB).

### 4.9 Accounting tab (internal, not IATA-standard)
`customer`(Link), `supplier`(Link) — internal cross-references, keep these visually separated (e.g. an "Internal" badge) since they're not part of the IATA AWB data model.

## 5. Layout & visual direction (the plan's explicit asks)

> *"Best Way / Conventional way / Beautiful / Attractive / International standard clean form / compact / not messy / very user friendly / mandatory-first then optional / layout sequence follows the AWB paper layout / right side vertical tab for parties / popup for dimensions"*

Concretely:

1. **Header band** mimics the top-left box of a paper AWB: airline prefix + serial in large monospace type forming the AWB number, with origin/destination as a route chip (`DXB ✈ JFK` style), right next to it the e-AWB/Console toggles as small pills.
2. **Two-column shell below the header**: a wide main column (mandatory fields + the active rail panel) and a **fixed-width vertical rail on the right** (icons + short labels: Parties, Routing, Goods/Rates, Services, Fine Print, Internal) — clicking a rail item swaps the main panel content, the mandatory section always stays pinned above it.
3. **Progressive disclosure**: collapse genuinely rare sections (Other Participants, CDC block, Internal tab) behind a "Show more" / collapsed-by-default card so a simple domestic AWB doesn't visually overwhelm the user with 80 fields at once.
4. **Density**: use the same compact `text-sm`, `px-3 py-2` input sizing already established in `PartyForm.vue` — this is already a good "compact but not cramped" baseline, carry it through unchanged rather than inventing new spacing.
5. **Uppercase fields**: visually indicate which fields are server-uppercased (small `Aa→AA` icon or just rely on `text-transform:uppercase` CSS on the input — cheap and effective, matches the `"uppercase": 1` JSON flags already on the DocType).
6. **Validation surfacing**: AWB check-digit errors, origin==destination, and any other `frappe.throw()` from `validate()` arrive as a single string via `parseErr()` — show these as the existing toast pattern, AND additionally highlight the specific offending field (e.g. flash the `awb_serial_number` input red) where the error message can be pattern-matched to a known field.
7. **Empty/loading/error states**: replicate the exact patterns from `PartyList.vue` (spinner + label, empty-state icon + CTA, fixed-bottom-right error toast) for consistency across the app.
8. **Link fields**: there is **no existing typeahead component** (`PartyForm.vue` uses a preloaded `<select>` for Country only). Build one reusable `LinkField.vue` (see §6) backed by the `search_link` endpoint for the large masters (Airport, Party, Airline, Currency, etc.); keep a plain `<select>` only for static enums (`dim_unit`, month, P/C, K/L, G/C, the literal `Q`).
9. **Rail icons**: the rail/section icons (`truck`, `box`, `dollar-sign`, `globe`, `clipboard`, etc.) do **not** exist in `icons.js` yet — add them there first (see §2), or they render blank.

## 6. Files to create

```
frontend/src/pages/AWBList.vue
frontend/src/pages/AWBForm.vue
frontend/src/components/ui/LinkField.vue              (NEW — reusable debounced typeahead over search_link; none exists today)
frontend/src/components/awb/DimensionsModal.vue
frontend/src/components/awb/PartyRailPanel.vue        (Shipper/Consignee/Agent/Notify/Other Participants)
frontend/src/components/awb/RoutingRailPanel.vue      (Flight Bookings + Routing)
frontend/src/components/awb/RateLinesRailPanel.vue    (Rate Lines + Goods Details + Other Charges)
frontend/src/components/awb/ServicesRailPanel.vue     (SSR + Special Handling + OSI + Customs/OCI + Accounting Info + References)
frontend/src/components/awb/FinePrintRailPanel.vue    (Certification + Commission + Sender + CDC)
frontend/src/components/awb/EditableTable.vue         (generic add/remove-row child-table grid — extract since 6+ panels need this)
```

`LinkField.vue` contract: props `modelValue` (linked doc `name`), `doctype` (must be in the `search_link` allow-list), `placeholder`, optional `filters`, `disabled`; emits `update:modelValue`. Debounce input ~300ms → `apiGet('/api/method/awbix.frontend_api.search_link', {doctype, txt, ...})`; on mount with a non-empty value, fetch its label once so edit-mode shows the human label, not the raw id. Reuse the PartyForm input classes + CSS tokens; use the existing `search` icon.

Modify:
```
frontend/src/utils/icons.js     — add rail/section icons BEFORE building the rail (see §2)
frontend/src/router.js          — replace AWBList Placeholder, add AWBNew/AWBEdit
awbix/frontend_api.py           — add the 5 endpoints from §3
```

Do **not** modify `shipment.py`/`shipment.js`/`shipment.json` unless you find the dimension-math or `auto_rate_line` button handler needs a small whitelisted wrapper exposed — prefer calling existing whitelisted methods over duplicating logic.

## 7. Acceptance criteria

- [ ] `/awb` lists shipments with search (by AWB number) + origin/destination/docstatus filters + pagination, matching `PartyList.vue`'s visual and code conventions.
- [ ] `/awb/new` and `/awb/:name` render the same `AWBForm.vue`, mirroring `PartyForm.vue`'s `isNew` pattern.
- [ ] Mandatory-minimum fields are visible without any tab/rail navigation; everything else requires selecting a rail item.
- [ ] Dimensions popup: add/edit/remove rows, CSV/XLSX upload via `parse_dimension_file`, live recalculation via `calculate_dimension_totals`, and committing the modal updates the parent's volume/volume-weight/chargeable-weight fields identically to what the server will compute on save (no visible "jump" after save).
- [ ] Charge Summary is **never** fetched, rendered, or submitted by this UI.
- [ ] Saving a new AWB with a bad check-digit serial number shows the exact server validation message in a toast.
- [ ] Saving with `origin == destination` is rejected with the server's message surfaced.
- [ ] All fields flagged `"uppercase": 1` in `shipment.json` visually uppercase as the user types (CSS), and whatever casing is sent, the saved record reflects the server's authoritative uppercased value after reload.
- [ ] Read-only/fetched fields (agent_name, agent_place, etc.) are rendered disabled/greyed, never independently editable.
- [ ] The right-side vertical rail stays visible and pinned while scrolling the active panel's content.
- [ ] Deleting only works for draft (`docstatus == 0`) AWBs; attempting on a submitted one surfaces Frappe's own rejection message.
- [ ] No new npm dependencies added without first checking whether `frappe-ui` or the existing local component set already covers the need.

## 8. Delivery phases (build in this order — each phase ends shippable)

This feature is large (8+ components, 5 endpoints, ~80 fields, 15 child tables). Do **not** land it as one PR. Each phase below should checkout-build-run cleanly even if incomplete.

- **P0 — Skeleton / plumbing.** Extend `icons.js` (§2); add `get_shipments` + `search_link` endpoints (§3); replace the `awb` Placeholder route with `AWBList`/`AWBNew`/`AWBEdit` (mirror the Party route trio); build `AWBList.vue` (clone `PartyList.vue`); build the `AWBForm.vue` shell (header band, right rail, toast, Ctrl+S) and `LinkField.vue`, proven on `origin`/`destination`. *End: `/awb` lists, "New" shows the shell with working typeahead, nothing saves yet.*
- **P1 — Mandatory slice (can save a valid AWB).** Add `get_shipment`/`save_shipment`/`delete_shipment` covering the header + `dimensions` only, plus the Dimensions modal (§4.3). *End: create → save (server sets `awb_number`, validates the mod-7 check digit) → reload with full parity (incl. dim rows) → delete.*
- **P2 — Parties.** Shipper/Consignee flat fields, Agent (read-only fetched), `also_notify`, `other_participants`.
- **P3 — Routing & Flights.** `routing` + `flight_bookings`.
- **P4 — Rating.** `rate_lines` + the client-side Auto Rate Line (§4.6) + `other_charges` + a **read-only** charge-summary card (the only place `populate_charge_summary` output is shown; never editable/submitted).
- **P5 — Goods Details.** `goods_details` (identifier-driven columns + `rate_line_number`).
- **P6 — Customs / Accounting / References.** `oci_customs`, `accounting_information`, `references`.
- **P7 — Special Services.** `special_handling`, `special_service_requests`, `other_service_info`, plus the Fine-Print/CDC and Internal tabs; `edx_ack_*` shown read-only.
- **P8 — Polish.** CSV/XLSX dimension import via `parse_dimension_file`; field-level error focus; progressive-disclosure collapses.
- **P9 — Hardening & tests** (§9).

Each phase owns exactly one set of child tables; extract each table into its own grid component rather than inlining all ~15 into one file.

## 9. Testing & verification

**Backend (FrappeTestCase — `test_shipment.py` is currently an empty `pass`):** add tests for (1) a full round-trip happy path where `awb_number == f"{airline_prefix}-{awb_serial_number}"` and every flat field + child row matches; (2) bad check-digit serial → `ValidationError` propagates through the endpoint; (3) `origin == destination` → `ValidationError`; (4) a bogus `charge_summary` in the payload is **ignored** and the persisted summary reflects `populate_charge_summary`; (5) a pre-existing `shipment_fsu` row **survives** a save that omits the fsu key; (6) `dimensions` rows persist and `volume_weight`/`chargeable_weight` recompute to the same values `calculate_dimension_totals` returns, and `get_shipment` returns the rows; (7) the three corrected fieldnames (`notify_name`, `participant_name`, `other_service_information`) round-trip non-empty (guards against silent drop); (8) `search_link` returns rows for an allowed doctype and `frappe.throw`s for a non-whitelisted one. Run: `bench run-tests --doctype Shipment`.

**Frontend manual E2E:** `bench start` → log in → `/awb` lists → click New. Use a **valid** serial (8th digit = `int(first7) % 7`; e.g. first 7 `1234567` then append `1234567 % 7`). Set `origin` ≠ `destination` via `LinkField` (proves typeahead + the rule), fill weight/pieces/code/currency, open Dimensions, add a row (e.g. 1 pc 100×40×30 cm), Apply → scalars populate. **Save** → success toast, URL becomes `/awb/<name>`, `awb_number` shows `<prefix>-<serial>`. **Reload** → assert full parity including dimension rows and scalars (proves the §4.3 round-trip). **Negatives:** a wrong check digit and `origin == destination` each surface the server message in a toast. **Delete** → routes back to `/awb`. Repeat the round-trip-then-reload check per phase as each child table is added.

## 10. Open questions for the backend owner

1. **Promote `auto_rate_line` to a shared whitelisted method?** It would let desk and SPA call one implementation and kill the §4.6 duplication. (Recommended.)
2. **Confirm `shipment.json` autoname** — is `name == awb_number`, or is `name` a separate series? The FE routes on `name`, so this affects `/awb/:name`.
3. **Are `iata_rate` and `volume_code` real parent fields?** Both the Auto Rate Line logic and the dimension m³ auto-raise read them (`frm.doc.iata_rate` / `frm.doc.volume_code` in `shipment.js`). Verify they exist in `shipment.json` and include them in the get/save allow-list and the header UI (`volume_code` as a `LinkField`→Volume Code).
4. **Legacy `to_airport1`/`by_carrier1`/`to_airport2`/`by_carrier2`** — superseded by the `routing` child table? Safe to omit from primary input (show only if non-empty on load)?
5. **Permissions** — confirm the SPA user's role has create/write/delete on `Shipment`.
