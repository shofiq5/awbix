Your question: what happens when the same message arrives again with different values
I designed and built this as the core of the inbound pipeline. Two cases, never any silent data loss:

Exact replay (byte-identical) → deduplicated on content_hash at the stage, marked Duplicate, no-op.
Amendment (same AWB, different content) → a controlled, audited update governed by an EDX Delivery ledger (one row per business key) with three guards in pipeline.py _amendment_decision:
Stale-guard — an older message can't overwrite newer data → marked Superseded.
Lock-guard — if the Shipment is submitted (it's a submittable DocType) or the ledger row is locked, EDX won't auto-overwrite → marked Needs Review for manual apply.
Otherwise apply, bump revision, keep the full history (every EDX Message In is immutable; Frappe track_changes gives the field-level diff for free).
Mode is per-definition: Auto Apply (default) or Manual Review.
I deliberately put provenance in EDX Delivery rather than polluting Shipment, so EDX stays decoupled.

Gaps & red flags I found (full table in §14 of the strategy)
The ones that actually change the design: R1 Shipment.validate() throws on bad AWB data — so I made validation produce recordable issues and the pipeline catches ValidationError instead of crashing the worker. R2 FWB.csv carries both "16" and "FWB Message 17" markers — confirm the version before seeding rules. R3 Shipment is submittable → drove the lock-guard. R5 Party has no natural key → I create Airline/Airport stubs but only set Party name text. Plus R6 email idempotency (UIDL), R7 multi-message payloads, R8 encoding/line-wrap, R12 parser_class is an importable path so write access is admin-only.

What I built (M0–M3 inbound vertical slice, all decisions locked in)
Engine core (engine/): base parser/composer/transport, DB-driven registry, classifier, and the full inbound pipeline with amendment logic.
7 DocTypes: Message Definition, Message Log, Message Stage, Message In, Delivery, + two child tables.
FWB/16 handler (fwb16_parser.py, cargoimp.py) — parse → business_key → validate → process into Shipment.
Wiring: scheduler_events + idempotent after_migrate seed in hooks.py/install.py, and a test module.
Verified: all JSON valid, all Python compiles, and the parser runs correctly on all three real FWB samples (correct AWB/routing/parties/currency) with the validator flagging a tampered check digit. I could not run bench migrate/run-tests from here — that needs the WSL bench. Please run:


bench migrate && bench build && bench run-tests --app awbix
Then the FWB-16 definition auto-seeds and you can test the flow end-to-end:


from awbix.edx.engine.pipeline import ingest_raw, process_message_in
stage = ingest_raw(open('/path/to/fwb sample1.txt').read())  # → auto-classifies
# promote (or set auto_promote on the definition), then process_message_in(<EDX Message In name>)
Decisions applied to the doc
FNA/FMA inbound-only (no sending); self-managed email; no Message Out on inbound (delivery is a flag + ledger only).

Still need from you (§15): FNA/FMA manuals + the Shipment status/field they should update, the FWB.csv version question, MQ broker choice, and outbound routing rules. Next milestones: M4 connectivity (Email/SFTP + Test Connection), M5 composer, M6 FNA/FMA. Want me to continue with M4, or pause for you to migrate and review first?

Still need from you (§15): FNA/FMA manuals + the Shipment status/field they should update, the FWB.
answer Manual attached create best swited status field in the shipment table

MQ broker choice: Rabit MQ, or any other good open source broker.
Outbound Routing : Please create new table Message Routing, By Carrier code, Origin, Destination
address type email SITA, MQ

What I added
EDX Connection — edx_connection.json, .py, .js
One transport endpoint, self-managed (no Frappe Email Account). Channel-specific sections (Email / SFTP / MQ) shown via depends_on; all credentials are encrypted Password fields. Test Incoming / Test Outgoing buttons call thin whitelisted methods that delegate to the adapter's test() and stamp last_test_status/at/message. Permissions: EDX Manager + System Manager.

Transport adapters — awbix/edx/transports/, one class per channel, paths matching registry._DEFAULT_TRANSPORTS exactly:

ManualTransport — never polls, not deliverable, always tests OK.
EmailTransport — POP3/IMAP in (UIDL/UID as external_id so the pipeline's existing dedup handles re-polls, R6), SMTP out.
SFTPTransport — paramiko, list/download/archive in, upload out (lazy import).
MQTransport — RabbitMQ via pika, basic_get in / basic_publish out, broker-agnostic base preserved (R10 resolved).
EDX Message Routing — edx_message_routing.json + resolver
Keyed by message type / carrier / origin / destination (blank = wildcard), with address_type ∈ Email / SITA / MQ and the delivering connection. resolve_route() picks the most-specific enabled rule, priority as tiebreak (R9 resolved). SITA is a routing classification now; its concrete transport is deferred as agreed.

Supporting: pika + paramiko added to pyproject.toml; seed_roles() in install.py creates the three EDX roles on migrate; tests cover Manual transport, the Test buttons, and all routing-resolution cases.

Verified here
All new Python compiles, both DocType JSONs parse, indentation is tabs (matches project), and db_set(dict) is supported in your Frappe build.

You need to run (on the WSL bench root)

bench setup requirements          # pulls pika + paramiko
bench migrate && bench build      # creates the 2 DocTypes + seeds roles; poll_inbound_connections goes live
ruff check . && ruff format --check .   # from apps/awbix (ruff isn't on the Windows side)
bench run-tests --module EDX
Left for later milestones (as scoped): outbound compose/dispatch + EDX Message Out (M5, needs the FWB16Composer — dispatch_outbound_queue stays a no-op); the concrete SITA adapter; and FNA/FMA parsers + the Shipment status field (M6 — that's your separate earlier answer, not this phase). Want me to take M5 (composer + wiring the routing resolver into a real send path) next, or pause here for you to migrate and test?

EDX Phase M5 — Composer Engine (Outbound FWB/16)
Context
M0–M4 are built: the inbound engine (stage→in→verify→process), FWB/16 parser, and the connectivity layer (EDX Connection, four transports incl. RabbitMQ, EDX Message Routing

resolve_route). The outbound side is still stubbed — pipeline.dispatch_outbound_queue() is a pass, BaseComposer has no concrete handler, and there is no EDX Message Out DocType. So a Shipment can be created from an inbound FWB but cannot yet be sent as one.
This phase delivers the Composer engine (strategy §3/§4.3, milestone M5): compose a Shipment into FWB/16 Cargo-IMP, verify it, resolve a route, transmit via the matching EDX Connection, and record a copy with delivery status. It closes the loop with the M4 routing/transport work — resolve_route and transport.send() finally get a caller.

Confirmed scope decisions (from user):

Trigger = manual button + whitelisted API → queue. A "Send FWB" button on Shipment and an API create an EDX Message Out (Queued); the scheduler dispatches it. Auto-on-submit deferred.
Full send path. dispatch_outbound_queue composes → verifies → resolve_route → EDX Connection → transport.send(), recording delivery_status/external_id/retries. Manual-channel send is a no-op; Email/MQ exercised via mocks in tests.
Composer coverage: symmetric with the current parser (message id, AWB consignment line, RTG routing, SHP/CNE/AGT party names, CVD currency) so compose(parse(sample)) round-trips the covered fields. Built to extend as the parser grows (strategy §9 remaining segments).

Deliverables
1. EDX Message Out DocType (awbix/edx/doctype/edx_message_out/)
Three-file pattern. Autoname hash. The composed copy + delivery ledger for outbound (strategy §4.3). Fields:

message_type, message_version (Data)
source_doctype (Link → DocType), source_name (Dynamic Link → source_doctype)
business_key (Data, indexed — e.g. AWB number, for traceability)
connection (Link → EDX Connection — resolved at dispatch; may be blank until then)
address_type (Select Email/SITA/MQ), address (Data) — captured from the route
composed_raw (Long Text — the FWB/16 text)
compose_status (Select: Pending/Composed/Compose Failed)
verify_status (Select: Pending/Verified/Verification Failed)
delivery_status (Select: Queued/Sent/Delivered/Failed)
sent_at (Datetime), external_id (Data), response (Small Text)
issues (Table → EDX Message Issue — reuse existing child)
retry_count (Int), next_retry_at (Datetime)
Permissions: EDX Manager + System Manager. Controller (edx_message_out.py): a whitelisted dispatch() method that runs one message through compose→verify→send (so the Desk can re-send a single row); the scheduler reuses the same engine function.

2. FWB16Composer (awbix/edx/handlers/fwb/fwb16_composer.py)
BaseComposer subclass, message_type="FWB", version="16". Mirror of FWB16Parser (reuse its field knowledge — same Shipment fields used in FWB16Parser.process):

compose(source_doc) -> str: read a Shipment doc and emit Cargo-IMP lines:
FWB/16
AWB consignment line {prefix}-{serial}{ORIGIN}{DEST} (+ pieces/weight when available)
RTG/ from the routing child table
SHP / CNE / AGT from shipper_name / consignee_name / agent_name
CVD/{currency}//PP/... from currency
join with CRLF (Cargo-IMP convention; cargoimp.normalize is CRLF-tolerant on the way back)
verify(raw) -> list[dict]: parse the composed text back with FWB16Parser().parse + .validate and return the issues — a genuine self-check (round-trip) reusing existing code.
Add a small cargoimp.build_segment(code, lines) / join helper to the existing cargoimp.py so composition shares the tokenizer module (keeps format knowledge in one place).

3. Outbound engine (awbix/edx/engine/pipeline.py — extend)
New whitelisted + scheduler functions, mirroring the inbound section's style (log_event, structured returns):

queue_outbound(source_doctype, source_name, message_type, version) -> str (whitelisted): resolve definition, compute business_key (via the parser's business_key is inbound-only — instead derive from the source doc: AWB number), create an EDX Message Out (Queued), enqueue dispatch_message_out. Returns the Message Out name.
dispatch_message_out(name): the core. compose (via registry.get_composer) → set composed_raw/compose_status → verify → on clean, resolve route (routing.resolve_route(message_type, carrier=airline_prefix, origin, destination)) → load its connection → get_transport(conn).send(raw, meta) → stamp delivery_status=Sent, external_id, sent_at. Catch failures into issues + delivery_status=Failed + schedule next_retry_at (never crash the worker — strategy R1 style).
dispatch_outbound_queue() (replace the pass): pick EDX Message Out rows where delivery_status=Queued, enqueue dispatch_message_out for each (batched).
Extend retry_failed() to also re-enqueue delivery_status=Failed outbound rows past next_retry_at (currently a pass; keep inbound TODO note).
Reuse: registry.get_composer (already exists), registry.get_transport, routing.resolve_route, log_event.

4. Registry/definition enablement
FWB16Composer needs composer_class + is_composer_enabled on the FWB-16 definition. Update the seed in awbix/edx/install.py _DEFINITIONS to include composer_class and is_composer_enabled: 1. Idempotency caveat: seed_definitions skips existing rows, so on an already-migrated site the FWB-16 row won't pick up the new fields. Add a tiny one-time backfill in seed_definitions (if row exists and composer_class empty → set it) so bench migrate activates the composer without manual edits. Keep it minimal and idempotent.
5. Shipment "Send FWB" button (awbix/shipment/doctype/shipment/shipment.js)
Add (or create) the client script: a Send FWB button (under an "EDX" group, shown when the doc is saved/submitted) calling queue_outbound via frappe.call with source_doctype="Shipment", the docname, FWB/16; toast the resulting Message Out name. Check whether shipment.js exists first; if not, create the three-file JS hook minimally.

6. Tests (awbix/edx/handlers/fwb/test_fwb16_composer.py + outbound pipeline test)
FrappeTestCase:

Round-trip: parse(sample) → build a transient dict/Shipment-like object → compose → parse again → assert AWB, routing, parties, currency survive (compose(parse(sample)) ≈ sample on covered fields).
verify(): composed output verifies clean; a tampered Shipment (bad check digit) surfaces an Error issue.
Outbound pipeline (Manual connection + route): queue_outbound creates a Queued Message Out; dispatch_message_out composes, resolves the route to a Manual connection, marks delivery (Manual send → records the no-op response without crashing); failed route (no matching rule) → Failed + issue, not an exception.
Email/MQ send() monkeypatched to assert the routed transport is called with the raw.
Files
New:

awbix/edx/doctype/edx_message_out/{__init__.py, edx_message_out.json, edx_message_out.py}
awbix/edx/handlers/fwb/fwb16_composer.py
awbix/edx/handlers/fwb/test_fwb16_composer.py
Modified:

awbix/edx/engine/pipeline.py — add queue_outbound, dispatch_message_out, implement dispatch_outbound_queue, extend retry_failed.
awbix/edx/handlers/fwb/cargoimp.py — add a build_segment/join helper.
awbix/edx/install.py — seed composer_class + enable; backfill existing FWB-16 row.
awbix/shipment/doctype/shipment/shipment.js — Send FWB button (create if absent).
Reused (no change):

awbix/edx/engine/base_composer.py — BaseComposer interface.
awbix/edx/engine/registry.py — get_composer, get_transport.
awbix/edx/engine/routing.py — resolve_route (M4).
awbix/edx/doctype/edx_message_issue/ — reused child table for issues.
awbix/edx/handlers/fwb/fwb16_parser.py — field mapping + verify() re-parse.
Out of scope (later)
Fuller FWB/16 segment coverage (RTD/OTH/charge summaries/SPH/OCI) — grows with the parser.
Concrete SITA transport (gateway TBD); SITA routes compose+queue but send() is deferred.
FNA/FMA (M6) and auto-on-submit triggering.
Verification
On the WSL bench root (~/frappe-bench):

bench migrate && bench build     # creates EDX Message Out; enables FWB-16 composer
ruff check . && ruff format --check .   # from apps/awbix
bench run-tests --module EDX
End-to-end smoke (Manual connection, no external services):

import frappe
# 1. a Manual connection + a catch-all route to it
c = frappe.get_doc({"doctype":"EDX Connection","connection_name":"Out Manual",
    "channel":"Manual","direction":"Outbound","enabled":1}).insert()
frappe.get_doc({"doctype":"EDX Message Routing","address_type":"Email",
    "address":"ops@example.com","connection":c.name,"enabled":1}).insert()

# 2. queue + dispatch an existing Shipment's FWB
from awbix.edx.engine.pipeline import queue_outbound, dispatch_message_out
out = queue_outbound("Shipment", "157-68076960", "FWB", "16")
dispatch_message_out(out)
mo = frappe.get_doc("EDX Message Out", out)
print(mo.compose_status, mo.verify_status, mo.delivery_status, mo.composed_raw[:40])
Then verify the Send FWB button on a Shipment creates a Message Out and the round-trip test passes (compose(parse(sample)) preserves AWB/routing/parties/currency).

What I added
EDX Message Out — json / py
The composed copy + delivery ledger: source link, business key, resolved connection/address, composed_raw, and three independent statuses (compose_status / verify_status / delivery_status), retries, and an issues table (reuses the existing EDX Message Issue child). A whitelisted dispatch() re-runs one row through the same engine the scheduler uses.

FWB16Composer — fwb16_composer.py
The inverse of the parser: reads a Shipment and emits FWB/16, the AWB consignment line (+ pieces/weight), RTG, SHP/CNE/AGT, and CVD. verify() re-parses its own output through FWB16Parser — a genuine round-trip self-check. Composition primitives (segment, join) live in cargoimp.py so format knowledge stays in one module.

Outbound engine — pipeline.py

queue_outbound(...) (whitelisted) — creates a Queued EDX Message Out and enqueues dispatch.
dispatch_message_out(name) — compose → verify → resolve_route(type, airline_prefix, origin, destination) → get_transport(connection).send(). Never raises: compose/verify/route/send failures land as issues + status + a backoff next_retry_at (strategy R1 style). Verification errors and missing routes are non-retryable Failed; transport errors retry up to 5×.
dispatch_outbound_queue() / retry_failed() — now real: enqueue due Queued rows. (The existing every-minute cron hook picks these up; no hooks change needed.)
Activation + UI

install.py: FWB-16 seed now sets composer_class + is_composer_enabled, with an idempotent backfill so an already-migrated site activates the composer on the next bench migrate without manual edits.
shipment.js: a Send FWB/16 button under an "EDX" group calling queue_outbound.
Tests — test_fwb16_composer.py: round-trip (parse(compose(shipment)) preserves AWB/routing/parties/currency), verify clean + bad-check-digit, and the outbound pipeline (routed send via a faked transport → Sent; no-route → Failed+ROUTE issue; Manual channel → graceful, no crash).

Verified here
All Python compiles, the new JSON is valid, indentation is tabs, log events use valid event options (Sent/Failed/Verified), and the composer↔parser segments line up by construction.

You need to run (WSL bench root)

bench migrate && bench build      # creates EDX Message Out; backfills/enables FWB-16 composer
ruff check . && ruff format --check .   # from apps/awbix (ruff isn't on the Windows side)
bench run-tests --module EDX
The plan file has a copy-paste smoke test (Manual connection + catch-all route → queue_outbound → dispatch_message_out).

Remaining milestones: M6 — FNA/FMA parsers + the Shipment status field they update (your earlier answer, manuals are in .claude/), plus retry/dead-letter hardening; and the concrete SITA transport once the gateway is chosen. Want M6 next?

What I added
Generic engine hook — bypass_amendment (definition JSON + pipeline.py)
FNA/FMA aren't amendments to a Shipment — they annotate it. A new bypass_amendment flag makes process_message_in skip the amendment/lock guards and the EDX Delivery ledger and run a dedicated _process_annotation path. This is why an ack reaches even a submitted Shipment (the write uses db.set_value, sidestepping docstatus — R3), with no FNA/FMA special-casing in the engine. A target it can't find → Needs Review, never a crash.

FNA/FMA parsers — awbix/edx/handlers/ack/
ack_common.py holds the shared logic: split id/reason/echoed-body, recover the AWB by scanning the echoed message for the FWB consignment line, stamp the Shipment, and reconcile the matching EDX Message Out (FMA → Delivered, FNA → Failed + reason). fma_parser.py / fna_parser.py are thin BaseParser subclasses. Verified the parse + AWB-extraction logic standalone.

Shipment ack fields — shipment.json
New collapsible "EDX Acknowledgement" section: edx_ack_status (Pending/Acknowledged/Rejected, filterable), edx_ack_detail, edx_ack_at — all read-only, set by EDX.

Seed + retry — install.py: FMA-1 and FNA-1 definitions (parser-enabled, bypass_amendment, auto-promote + auto-process, ^FMA/^FNA detection). retry_failed now also re-enqueues inbound Failed Message In rows with a due next_retry_at.

Manual Ingest button — edx_connection.js: a prompt to paste a raw message that calls the existing whitelisted ingest_raw against the connection — reusing the entire ingest→classify→promote→process path, no new server code.

Tests — test_ack.py: FMA/FNA parse + AWB key, no-AWB→Warning (not Error), FMA→Acknowledged+Delivered, FNA→Rejected+Failed, unknown AWB→None, and the end-to-end pipeline bypass on a submitted Shipment.

How the flow answers your question
Recapping with M6 in place: ingest_raw stages and classifies (FMA/FNA matched by ^FMA/^FNA); because their definitions have auto_promote+auto_process, they promote to Message In and process automatically — verify parses with no writes, then process (via the bypass path) stamps the Shipment ack status and closes the loop on the sent FWB. For FWB inbound the same stages run but through the amendment-guarded path into a Shipment.

Verified here
All Python compiles, both edited JSONs are valid, tabs throughout (the lone "space" line in pipeline.py is the pre-existing docstring), and the FMA/FNA parse/extract logic runs correctly on samples.

You run (WSL bench root)

bench migrate && bench build      # adds bypass_amendment + Shipment ack fields; seeds FMA-1/FNA-1
ruff check . && ruff format --check .   # ruff isn't on the Windows side
bench run-tests --module EDX
That closes out the strategy's milestones (M0–M6). Still genuinely open: the concrete SITA transport (awaiting the gateway choice) and the full retry dead-letter/perf pass — plus the Phase 2 dashboard sketch (§13) if you want to start that next.


Phase 2 — EDX Dashboard is built. No new data model (per §13) — it reuses the existing awbix/dashboard/ convention (module-scoped is_standard JSON that bench migrate imports), so it appears for everyone without fixtures or a build step.

What I added
Workspace "EDX" — edx.json
A single screen laid out as Overview (8 number cards) → Inbound charts → Outbound charts → Quick Access shortcuts → a Pipeline & Configuration link section. Shortcuts jump to Stage / In / Out / Connection / Routing lists; the link cards group Inbound (Stage, In, Delivery), Outbound (Message Out), Configuration (Connection, Definition, Routing), and Monitoring (Message Log).

8 Number Cards — awbix/edx/number_card/
Live status counts: Staged, Unrecognized, Needs Review, Inbound Failed, Inbound Processed, Outbound Queued, Outbound Failed, Delivered — the operator's at-a-glance health of both legs.

3 Dashboard Charts — awbix/edx/dashboard_chart/
EDX Inbound by Status (Message In process_status, donut), EDX Outbound by Status (Message Out delivery_status, donut), and EDX Inbound Volume (daily time-series on received_at).

Form action buttons (the §13 re-verify / re-process / re-send actions), all calling existing whitelisted methods — no new server code:

edx_message_stage.js — Promote (when classified but not yet promoted)
edx_message_in.js — Verify / Process
edx_message_out.js — Dispatch / Re-send (when Queued or Failed)
Verified here
All 12 JSON files parse, the workspace content blocks round-trip, and every card/chart filter, group_by_based_on, and based_on field was cross-checked to exist on its target DocType (process_status, delivery_status, status, received_at). Drill-through (raw → parsed_json → issues → EDX Message Log) is already inherent in the existing DocType forms.

You run (WSL bench root)

bench migrate && bench build      # imports the EDX workspace, cards, charts
bench clear-cache
Then open EDX in the Desk sidebar; the cards/charts populate as messages flow.

That completes the full strategy roadmap (M0–M6 + Phase 2). The only items still deliberately open are the concrete SITA transport (awaiting the gateway choice) and the retry dead-letter/perf hardening pass — both noted in earlier phases. Want me to tackle either of those, or is this a good place to pause and migrate/review the whole EDX module end to end?


