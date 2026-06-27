# EDX Module — Strategy & Backend Implementation Plan

> **Scope:** Backend only, **Frappe Framework v15**, AWBix app. No frontend/Desk work beyond what DocType JSON generates. Phase 1 delivers an extensible EDI messaging engine with **FWB/16** as the first message type. Phase 2 (dashboard) is sketched, not built.

## Locked Decisions (from review)

| # | Decision |
|---|---|
| D1 | **FNA / FMA are inbound-only.** We *receive* acknowledgement/error messages; we **never send** them. The inbound pipeline emits **no acknowledgement** message. |
| D2 | **Email is fully self-managed** inside `EDX Connection` (own POP3/IMAP + SMTP). We do **not** reuse Frappe's `Email Account`. |
| D3 | **Successful inbound processing does NOT create a Message Out record.** It only flags delivery (`delivery_status = Delivered`, plus the `EDX Delivery` ledger). Message Out exists solely for the (future) outbound composer engine. |
| D4 | **Re-received messages** are handled by the amendment model in §6 — exact replays are no-ops; same-AWB-different-content is a controlled, audited update with stale- and lock-guards. |

---

## 1. Goal

Build **EDX (Electronic Data Exchange)** — an EDI messaging engine inside AWBix that can:

1. **Ingest** messages over multiple transports (Email POP3/IMAP, SFTP, MQ, Manual).
2. **Parse** inbound messages into normalized data and **process** them into business DocTypes (e.g. `Shipment`).
3. **Compose** outbound messages from business documents, verify, and deliver them, keeping a copy with delivery status.
4. Do all of this through a **plugin architecture keyed by `(message_type, version)`** so new message kinds (FWB/16, FHL/5, FNA, FMA …) are added and activated **without changing core code**.

It must handle **high message volume** (decoupled ingest/parse/process via background jobs, deduplication, batching).

**The single most important constraint** (from the brief): *"I should be able to develop and add different message types and versions in the same framework."* Every decision below is subordinate to it — the core is a thin, generic pipeline; everything message-specific lives in pluggable handlers selected from a DB registry.

---

## 2. Existing Codebase Anchors

| Asset | Location | Role |
|---|---|---|
| `EDX` module | `awbix/modules.txt` (registered) | Host module for EDX DocTypes |
| `Shipment` (+ child tables) | `awbix/shipment/doctype/` | **Target** of inbound FWB / **source** of outbound FWB |
| FWB/16 ABNF | `awbix/shipment/Supporting_doc/fwb16.abnf` | Authoritative message grammar |
| FWB rule table | `awbix/shipment/Supporting_doc/FWB.csv` | Element-level spec → seeds `EDX Element Rule` |
| FWB samples 1–3 | `awbix/shipment/Supporting_doc/` | Parser/round-trip test fixtures |
| FWB rules PDF | `awbix/shipment/Supporting_doc/fwb_rule.pdf` | Validation rules reference |

**Critical properties of `Shipment` that shape EDX** (verified from `shipment.json`):
- `is_submittable = 1` → a submitted Shipment **cannot be edited in place**; amendments must respect docstatus (see §6 lock-guard).
- `track_changes = 1` → Frappe auto-records a field-level version history; EDX gets amendment audit **for free** via `tabVersion`.
- `airline_prefix` → **Link → Airline**, `origin`/`destination` → **Link → Airport**, `shipper`/`consignee`/`agent` → **Link → Party**. Inbound processing must therefore **resolve or create master records** for Airline/Airport (simple keys) and is conservative about Party (complex key — set the `*_name` text fields, leave the Link for a later matching step). Writing a Link to a non-existent master fails validation.
- `Shipment.validate_awb_serial_number()` throws on a bad modulus-7 check digit — EDX **reuses** this but must treat it as a recordable *issue*, not an uncaught crash (see Red Flag R1).

---

## 3. Architecture Overview

Three engines plus a shared plugin core. Deliberate symmetry: **transports, parsers, and composers are all plugins resolved from the DB registry through one mechanism.**

```
                         ┌─────────────────────────────────────────────┐
                         │              EDX Registry (DB)                │
                         │  EDX Message Definition  (type+version → ▼)   │
                         │  EDX Connection          (transport config)   │
                         └───────────────┬───────────────────────────────┘
                                         │ frappe.get_attr(dotted_path)
        ┌────────────────────────────────┼────────────────────────────────┐
        ▼                                ▼                                ▼
  Transport plugins              Parser plugins                  Composer plugins
  (BaseTransport)                (BaseParser)                    (BaseComposer)
  email / sftp / mq / manual     FWB16Parser, FNAParser…         FWB16Composer…

  ── CONNECTIVITY ENGINE ──    ── PARSER ENGINE (IN) ──        ── COMPOSER ENGINE (OUT) ──
  poll() / send() / test()     stage→in→verify→process          compose→verify→send→deliver

                  ┌──────────────── INBOUND PIPELINE ─────────────────┐
   transport.poll → EDX Message Stage → (classify) → EDX Message In
                    → verify(parse-only) → process → Shipment + EDX Delivery
                      (NO acknowledgement, NO Message Out — D1, D3)

                  ┌──────────────── OUTBOUND PIPELINE (later) ────────┐
   Shipment/API → EDX Message Out (compose → verify → transport.send → delivery status)

   Cross-cutting: EDX Message Log (every state transition, error, retry)
```

### 3.1 Plugin core (`awbix/edx/engine/`)

```
awbix/edx/
├── doctype/                     # Frappe DocTypes (schema + controllers)
├── engine/
│   ├── __init__.py
│   ├── registry.py              # (type,version) → handler class via EDX Message Definition
│   ├── base_parser.py           # BaseParser
│   ├── base_composer.py         # BaseComposer
│   ├── base_transport.py        # BaseTransport
│   ├── pipeline.py              # generic inbound/outbound orchestration + amendment logic
│   ├── classifier.py            # detect (type,version) from raw payload
│   └── exceptions.py            # EDXError, EDXParseError, EDXProcessError, …
├── handlers/
│   └── fwb/
│       ├── cargoimp.py          # shared Cargo-IMP tokenizer
│       ├── fwb16_parser.py      # FWB16Parser(BaseParser)
│       └── fwb16_composer.py    # FWB16Composer(BaseComposer)  (later)
├── transports/                  # email / sftp / mq / manual adapters (later)
└── utils/
```

### 3.2 Base interfaces

```python
class BaseParser:
    message_type: str = None
    version: str = None
    def parse(self, raw: str) -> dict: ...          # raw → normalized dict, NO DB writes
    def business_key(self, data: dict) -> str | None: ...  # e.g. AWB number → amendment key
    def validate(self, data: dict) -> list[dict]: ...      # [{level, code, message, field}]
    def process(self, data: dict, message_in) -> str: ...  # persist; idempotent; returns target name

class BaseComposer:
    message_type: str = None
    version: str = None
    def compose(self, source_doc) -> str: ...
    def verify(self, raw: str) -> list[dict]: ...

class BaseTransport:
    def test(self, direction) -> dict: ...          # {ok, message}
    def poll(self) -> list[dict]: ...               # [{raw, sender, subject, external_id, attachments}]
    def send(self, raw, meta) -> dict: ...          # {ok, external_id, response}
```

### 3.3 Registry resolution

`EDX Message Definition` autonames as `{message_type}-{version}` (e.g. `FWB-16`), so lookups are a deterministic `get_cached_doc`. Adding a message kind = (1) write a handler class, (2) create one definition row pointing at it, (3) toggle enabled. **Zero core edits.**

---

## 4. Data Model (DocTypes)

All under module **EDX**; three-file pattern (`.json`/`.py`/`__init__.py`), tabs, double quotes, 110-char lines.

### 4.1 Registry & configuration

**`EDX Message Definition`** — activation registry. Autoname `format:{message_type}-{version}`.

| Field | Type | Notes |
|---|---|---|
| `message_type` / `version` | Data | e.g. `FWB` / `16` |
| `title` | Data | `FWB/16 — Air Waybill (Cargo-IMP)` |
| `standard` | Select | `Cargo-IMP`, `Cargo-XML`, `EDIFACT`, `Custom` |
| `parser_class` / `composer_class` | Data | dotted path to handler class |
| `is_parser_enabled` / `is_composer_enabled` | Check | |
| `detection_pattern` | Small Text | regex matched by the classifier (e.g. `^FWB/16`) |
| `target_doctype` | Link → DocType | e.g. `Shipment` |
| `auto_promote` / `auto_process` | Check | automation per type |
| `amendment_mode` | Select | `Auto Apply` (last-valid-wins) / `Manual Review` |

**`EDX Connection`** — one transport endpoint (self-managed; D2).

| Field | Type | Notes |
|---|---|---|
| `connection_name` | Data | autoname |
| `channel` | Select | `Email`, `SFTP`, `MQ`, `Manual` |
| `direction` | Select | `Inbound`, `Outbound`, `Both` |
| `enabled` | Check | |
| Email | | `incoming_protocol`(POP3/IMAP), `email_host/port/user/password`(Password), `use_ssl`, `mailbox`; outgoing `smtp_host/port/user/password`(Password), `smtp_tls` |
| SFTP | | host/port/username/`private_key`or password(Password), `remote_inbound_path`, `remote_outbound_path`, `archive_after_fetch` |
| MQ | | `mq_type`, host/port, `queue_in`, `queue_out`, credentials |
| `max_messages_per_poll` | Int | volume guard |
| `last_polled_at`, `last_test_status`, `last_test_at`, `last_test_message` | | populated by Test Connection |

Buttons: **Test Incoming**, **Test Outgoing** → `connection.test(direction)` → store result.

**`EDX Element Rule`** — data-driven spec, seeded from `FWB.csv` (see Red Flag R2): `message_definition`(Link), `ref_no`, `element_name`, `condition`(M/C/O), `data_format`, `fixed_value`, `sort_seq`.

### 4.2 Inbound (Parser engine)

**`EDX Message Stage`** — raw capture, **no filtering**.

| Field | Type | Notes |
|---|---|---|
| `connection` | Link → EDX Connection | source (blank = Manual) |
| `received_at` | Datetime | |
| `raw_message` | Long Text | (large payloads → File attachment) |
| `content_hash` | Data, **indexed** | sha256 → dedup |
| `external_id` | Data | provider id (email Message-ID / filename) |
| `sender`, `subject` | Data | |
| `detected_type`, `detected_version` | Data | from classifier |
| `status` | Select | `Staged`, `Promoted`, `Unrecognized`, `Duplicate`, `Error` |
| `message_in` | Link → EDX Message In | set on promotion |

Unique index on `(connection, external_id)` and on `content_hash` to stop duplicate staging under concurrent polls.

**`EDX Message In`** — promoted, processable messages.

| Field | Type | Notes |
|---|---|---|
| `stage` | Link → EDX Message Stage | provenance |
| `message_type`, `message_version` | Data | |
| `business_key` | Data, indexed | e.g. AWB number — drives amendment matching |
| `raw_message` | Long Text | |
| `parsed_json` | Code (JSON) | **human-readable verify output** |
| `verify_rows` | Table → EDX Verify Row | flat field/value/condition view |
| `parse_status` | Select | `Pending`, `Verified`, `Verification Failed` |
| `issues` | Table → EDX Message Issue | from `validate()` |
| `process_status` | Select | `Not Processed`, `Processing`, `Processed`, `Failed`, `Superseded`, `Needs Review` |
| `target_doctype`, `target_name` | Data | created/updated `Shipment` |
| `delivery_status` | Select | blank → `Delivered` (flag only; D3) |
| `applied` | Check | did this message actually modify the target? |
| `diff_json` | Code (JSON) | field-level changes applied (amendment audit) |
| `retry_count`, `next_retry_at` | Int / Datetime | |

Buttons: **Verify** (`parse()`+`validate()` → `parsed_json`/`issues`, **no business writes**) and **Process**.

**`EDX Delivery`** — authoritative *current-state ledger*, one row per `(target_doctype, business_key)`. Decouples amendment logic from `Shipment` (no Shipment pollution).

| Field | Type | Notes |
|---|---|---|
| `business_key` | Data, **unique** | e.g. `157-68076960` |
| `target_doctype`, `target_name` | Data | |
| `current_message_in` | Link → EDX Message In | last applied |
| `revision` | Int | bumped on each applied amendment |
| `last_source_received_at` | Datetime | **stale-guard** reference |
| `locked` | Check | **lock-guard**: when set, no auto-overwrite |
| `status` | Select | `Active`, `Locked`, `Conflict` |

**`EDX Message Issue`** *(child)*: `level`(Info/Warning/Error), `code`, `message`, `field`.
**`EDX Verify Row`** *(child)*: `ref_no`, `field`, `value`, `condition`.

### 4.3 Outbound (Composer engine — built later)

**`EDX Message Out`** — composed copy + delivery status: `message_type/version`, `source_doctype/name`, `connection`, `composed_raw`, `compose_status`, `verify_status`, `delivery_status`(Queued/Sent/Delivered/Failed), `sent_at`, `external_id`, `response`, `issues`, `retry_count/next_retry_at`. Used **only** for true outbound composition — never for inbound delivery (D3).

### 4.4 Logging

**`EDX Message Log`** — append-only trail, Dynamic-linked to Stage/In/Out/Delivery: `reference_doctype`, `reference_name`, `event`(Ingested/Classified/Promoted/Parsed/Verified/Processed/Amended/Superseded/Failed/Retry), `level`, `message`, `traceback`, `timestamp`.

---

## 5. Inbound Lifecycle

```
[Transport.poll / Manual upload]
        │  store raw + content_hash; dedup (hash & external_id)
        ▼
EDX Message Stage  ── Staged
        │  classify(raw): match detection_pattern of enabled definitions
        ├─ no match / disabled → Unrecognized   (kept for review)
        ├─ duplicate hash      → Duplicate       (no-op)
        ▼ recognized & enabled
   promote (manual, or auto_promote)
        ▼
EDX Message In  ── Pending
        │  VERIFY: parse() + validate() → parsed_json + issues   (NO business writes)
        ├─ Error issues → Verification Failed
        ▼ clean
   Verified
        │  PROCESS (manual, or auto_process) → §6 amendment logic, in a transaction + AWB lock
        ▼
   Shipment created/updated  +  EDX Delivery upserted
   process_status=Processed, delivery_status=Delivered          (NO Message Out — D3)
        ▼
   EDX Message Log entries throughout
```

---

## 6. Re-received Messages & Amendments  *(answer to "same message comes again with different values")*

The same AWB legitimately arrives more than once — exact re-transmissions and genuine corrections both happen in air cargo. EDX distinguishes them and **never silently loses data**.

**Two cases:**

1. **Exact replay** (byte-identical → same `content_hash`): idempotent **no-op**. Stage → `Duplicate`, nothing reprocessed.
2. **Amendment** (same `business_key`, different content): a controlled, audited update.

**Mechanism**
- `business_key` is computed by the parser (`parser.business_key(data)`; for FWB = `{prefix}-{serial}`).
- `EDX Delivery` is the single source of truth for "what is currently applied" for each business key (current message, `revision`, `last_source_received_at`, `locked`). Every received message stays as its own **immutable** `EDX Message In` — full history is preserved regardless of apply outcome.
- On process of an amendment:
  1. **Lock the key** (named/row lock on `business_key`) so concurrent workers serialize — prevents duplicate-Shipment and lost-update races.
  2. **Stale-guard:** if the incoming message's timestamp (message date, else `received_at`) is **older** than `EDX Delivery.last_source_received_at` → mark Message In `Superseded`, do **not** overwrite, log. (defends against out-of-order delivery)
  3. **Lock-guard:** if `EDX Delivery.locked` **or** the target Shipment is **submitted** (`docstatus=1`) → do **not** auto-overwrite; mark Message In `Needs Review` and require a manual apply. (protects human corrections and submitted documents — see Red Flag R3)
  4. **Otherwise apply:** update the target, compute a **field-level diff** (stored in `diff_json`, also captured by Frappe's `track_changes`), bump `revision`, update `current_message_in` / `last_source_received_at`, log `Amended`.
- **Mode** per definition: `Auto Apply` (default, last-valid-wins with audit) or `Manual Review` (every amendment → `Needs Review`).

This gives: replays are free; real amendments update with full diff + history; stale messages can't clobber newer data; manual/submitted records are never silently overwritten.

---

## 7. Connectivity Engine

Transports are plugins resolved per `EDX Connection.channel`. **Heavy-load principle:** `poll()` only fetches and stages raw bytes; all parse/process is enqueued.

| Channel | Inbound | Outbound | Library | Test |
|---|---|---|---|---|
| **Email** (self-managed, D2) | POP3 `poplib` / IMAP `imaplib`, SSL/TLS, fetch unseen, body+attachments; **track UIDL/UID** to avoid re-fetch | SMTP `smtplib` | stdlib | login (+IMAP select / SMTP `noop`) |
| **SFTP** | list `remote_inbound_path`, download new, archive after fetch | upload to `remote_outbound_path` | `paramiko` | open session + `listdir` |
| **MQ** | consume `queue_in` | publish `queue_out` | broker adapter | connect + peek |
| **Manual** | no poll; ingest via API/upload | — | — | always ok |

**Test Connection** runs `adapter.test(direction)` and stores `last_test_status`/`message`/`at`.

---

## 8. Scheduling & Heavy-Volume Handling

`hooks.py`:
```python
scheduler_events = {
    "cron": {
        "*/2 * * * *": ["awbix.edx.engine.pipeline.poll_inbound_connections"],
        "*/1 * * * *": ["awbix.edx.engine.pipeline.dispatch_outbound_queue"],
    },
    "all": ["awbix.edx.engine.pipeline.retry_failed"],
}
```
- **Decouple** ingest from parse/process; each fetched message staged immediately, then processing `frappe.enqueue`'d on a dedicated **`edx` long queue**.
- **Dedup** by `content_hash` (+ `external_id`) before any work.
- **Batch** with `max_messages_per_poll`.
- **Indexes** on `content_hash`, `business_key`, `status`, `message_type`, `received_at`.
- **Idempotent** processing; **AWB lock** during apply.
- No long work in the scheduler tick; concurrency via worker count.

---

## 9. FWB/16 — First Implementation

Cargo-IMP, line-oriented (slash / CRLF separated). `cargoimp.py` tokenizes into segments; `FWB16Parser` maps segments → normalized dict → `Shipment`; the `EDX Element Rule` set (from `FWB.csv`) drives M/C/O + format validation.

**Segment → Shipment mapping** (from `fwb16.abnf` + sample):

| Line id | ABNF element | Shipment target |
|---|---|---|
| `FWB/16` | StandardMessageIdentification | version detection |
| `nnn-nnnnnnnnOOODDD/…` | AWBConsignmentDetail | `airline_prefix`, `awb_serial_number`, `origin`, `destination`, pieces/weight/volume |
| `RTG` | Routing | `routing` |
| `SHP` / `CNE` / `AGT` | Shipper / Consignee / Agent | `shipper_*` / `consignee_*` / `agent_*` |
| `SSR` / `NFY` / `ACC` | SSR / AlsoNotify / Accounting | `special_service_requests` / `also_notify` / `accounting_information` |
| `CVD` | ChargeDeclarations | currency, charge_code, prepaid/collect, declared values |
| `RTD` | RateDescription | `rate_lines` + `goods_details` |
| `OTH` / `PPD`/`CCD` | OtherCharges / Charge Summary | `other_charges` / `charge_summary` |
| `CER` / `ISU` / `OSI` | Certification / Carrier Exec / OSI | `cdc_section_note` / carrier exec / `other_service_info` |
| `REF` / `COR` / `SPH` / `OCI` | Sender Ref / Customs Origin / Special Handling / Customs Info | `shipment_reference` / customs / `special_handling` / `customs_info` |
| `*` Participant | OtherParticipantInformation | `shipment_other_participant` |

**Master resolution:** `airline_prefix`→get-or-create `Airline`(field `airline_prefix`), `origin`/`destination`→get-or-create `Airport`(field `iata_code`). Parties set `*_name` text only (Party link deferred to a matching step). AWB check digit validated via `Shipment.validate_awb_serial_number` but surfaced as an *issue*, not a crash (R1).

**FNA / FMA (inbound, D1):** separate parsers, registered later. Their `process()` is **not** a Shipment-create — they reference an existing AWB and update a status / append a notification / log. Their target semantics need the FNA/FMA manuals (see R4).

---

## 10. Security & Permissions

Roles **EDX Manager** / **EDX Operator** / **EDX Viewer**. Credentials use `Password` fields (encrypted); `EDX Connection` read restricted to EDX Manager. All ingest/process/send via whitelisted methods with permission checks; raw payloads contain PII (shipper/consignee) → field-level perms where needed.

---

## 11. Testing

`FrappeTestCase`, `bench run-tests --module EDX`.
- **Parser units:** each sample → normalized dict + Shipment fields/children; malformed AWB → recorded Error issue.
- **Amendment:** replay = no-op; amendment = update + revision bump + diff; stale = Superseded; locked/submitted = Needs Review; concurrent process of same AWB → one Shipment.
- **Composer (later):** round-trip `compose(parse(sample)) ≈ sample`.
- **Registry/classifier:** unknown/disabled raises cleanly; pattern detection picks right (type,version).
- **Transports:** mocked; `test()` structured ok/fail; dedup via hash.

---

## 12. Implementation Plan (Milestones)

| # | Milestone | Deliverables |
|---|---|---|
| **M0** | Engine + registry | `engine/` package; `EDX Message Definition`, `EDX Message Log`; roles |
| **M1** | Inbound data model + capture | `EDX Message Stage`, `EDX Message In`, `EDX Delivery`, child tables; classifier; Manual ingest API |
| **M2** | FWB/16 parse + verify | `cargoimp.py`, `FWB16Parser` (parse/validate); `parsed_json`/issues; FWB.csv → `EDX Element Rule` |
| **M3** | Process + amendments | `process()` → Shipment + EDX Delivery; §6 amendment logic (stale/lock/diff); idempotency + AWB lock |
| **M4** | Connectivity + scheduler | `EDX Connection`; Email/SFTP/Manual adapters (+ MQ iface); Test Incoming/Outgoing; polling |
| **M5** | Composer engine | `EDX Message Out`; `FWB16Composer` + verify; round-trip tests |
| **M6** | FNA/FMA + hardening | FNA/FMA parsers (status-update semantics); retries/backoff, dead-letter, perf pass |
| **P2** | Dashboard | §13 |

After DocType changes: `bench migrate && bench build`. Lint: `ruff check . && ruff format .`; `pre-commit run --all-files`.

---

## 13. Phase 2 — Dashboard (sketch)

Frappe Workspace + Number Cards + Charts + filtered list views: counts by status across Stage/In/Out; filter by type/version/connection/date/AWB/status; drill into raw → `parsed_json` → issues → `EDX Message Log`; inbound vs outbound screens with re-verify / re-process / re-send actions. No new data model.

---

## 14. Gaps & Red Flags

| # | Risk | Impact | Mitigation |
|---|---|---|---|
| **R1** | `Shipment.validate()` **throws** on bad AWB check digit / `origin==destination`. Real-world partner messages contain such errors. | A hard `frappe.throw` during `process()` aborts the job with a stack trace instead of a clean failure. | Run business validation as **issues** during `verify()`; in `process()` catch `ValidationError`, set Message In `Failed` with the issue, never crash the worker. Optional `strict`/`lenient` mode per definition. |
| **R2** | `FWB.csv` carries **both** `16` and `17` / `"FWB Message 17"` markers, while the brief/ABNF say **FWB/16**. | Seeding the wrong rule version silently mis-validates every message. | **Confirm the target version before seeding** `EDX Element Rule`; tag each rule row with its `message_definition`. |
| **R3** | `Shipment` is **submittable** (`docstatus`). A submitted shipment can't be edited; an amendment for it can't be auto-applied. | Auto-apply would crash or be silently dropped. | Lock-guard in §6: submitted/`locked` → `Needs Review`, manual apply (amend/cancel is a business decision). |
| **R4** | We will **receive FNA/FMA** but their target semantics (which Shipment field/status they update) are undefined, and FWB-out composition isn't built yet — so *why* we receive FMA/FNA needs confirming. | Can't implement FNA/FMA `process()` without the manuals and a target field. | Scaffold FNA/FMA parsers disabled; define a Shipment status/notification target with their manuals. |
| **R5** | **Master auto-creation**: inbound creates `Airline`/`Airport` stubs from codes; `Party` has a `naming_series` key (no natural unique code) → can't safely get-or-create. | Junk/duplicate Party records, or link-validation failures. | Create Airline/Airport stubs (simple keys); for Party set `*_name` text only, defer link matching to an explicit step/rule. |
| **R6** | **Email idempotency**: POP3 has no "seen" state; re-polling re-downloads. | Repeated staging / load. | Track UIDL (POP3) / UID+folder (IMAP); plus `content_hash`/`external_id` dedup at stage. |
| **R7** | **Multi-message payloads**: one email/file may carry several concatenated Cargo-IMP messages or a batch. | A single Stage row mixes messages; parser sees garbage. | Split on message boundaries (`FWB/`, `FHL/` …) at ingest; one Stage row per message. |
| **R8** | **Encoding / line endings / Type-B wrapping**: Cargo-IMP charset, CRLF vs LF, teletype line wraps. | Tokenizer mis-splits segments. | Normalize encoding + newlines and rejoin wrapped continuation lines before tokenizing. |
| **R9** | **Outbound partner routing** undefined — which `EDX Connection` sends which message to whom. | Composer engine (M5) can't route. | Add a routing rule (per airline/destination → connection) when building M5. |
| **R10** | **MQ broker unspecified.** | Can't build a concrete MQ adapter. | Ship broker-agnostic `BaseTransport`; implement one concrete adapter (RabbitMQ/`pika` suggested) once chosen. MQ deferred to M4/M6. |
| **R11** | **Large raw payloads in Long Text** bloat the DB under volume. | Table/row size, backup cost. | Store oversized raw as File attachment, keep a hash/pointer in the row. |
| **R12** | **`get_attr` on a DB-stored dotted path** executes arbitrary import paths. | If a non-admin could edit `parser_class`, it's code execution. | `EDX Message Definition` write restricted to EDX Manager / System Manager only. |

---

## 15. Open Items (need input)

1. **FNA/FMA manuals** + the target Shipment status/field they update (R4). Confirm why we receive them if we don't send FWB.
2. **FWB version** of `FWB.csv` — 16 or 17 (R2).
3. **MQ broker** choice (R10).
4. **Outbound routing** rules for the composer engine (R9).

---

## Appendix A — Original Brief (verbatim)

> Backend FRAPPE 15, no frontend for now. EDX (Electronic Data Exchange) — International Enterprise EDI Messaging Engine. Connectivity (Email POP/IMAP, SFTP, MQ, Manual; test incoming/outgoing). Composer (Message Out): compose, verify, store copy with delivery status. Parser (Message In): stage (no filter) → message in (verify, human-readable JSON/table) → parse (independent by type & version; add/activate parsers like FWB-16, FHL-5) → process (feed tables; on success record delivery to module like Shipment) → message log. Composer & parser keyed by type+version; initially FWB/16; framework must allow adding new types/versions without rework. Phase 2: filterable message dashboard (in/out).
