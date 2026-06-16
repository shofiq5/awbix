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