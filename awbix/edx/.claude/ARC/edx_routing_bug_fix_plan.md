# EDX Message Dispatch — Revamp

## Symptom
Clicking **Dispatch** on an EDX Message Out hung the browser and eventually failed with:
`pymysql ... (1205, 'Lock wait timeout exceeded; try restarting transaction')`

## Root Causes
1. **Double row-lock deadlock.** The Desk button called `frappe.call({ doc, method: "dispatch" })`.
   Frappe's `run_doc_method` first runs `doc.check_if_latest()` → `load_doc_before_save()` →
   `get_doc(for_update=True)`, taking a `FOR UPDATE` lock on the row **in the web request**.
   `dispatch_message_out()` then ran *inline in that same request* and took the lock again
   (plus `mo.save()` re-triggers `check_if_latest`), tangling the transaction → lock-wait timeout.

2. **Synchronous transport I/O in the web request.** `send()` opens an SMTP/SFTP/MQ socket.
   Running it inline froze the button on every dispatch and made the request long-lived,
   widening the lock window.

## Revamp (conventional Frappe pattern)
**Trigger now enqueues; the worker does the work.**

- `EDXMessageOut.dispatch()` (controller): validates status, flips the row to **Sending** via
  `db_set` (committed, no save/lock), then `frappe.enqueue(dispatch_message_out, enqueue_after_commit, job_id=…)`
  and returns `{queued: True}` immediately. No transport I/O, no second lock in the web request.

- `dispatch_message_out(name)` (worker, no longer `@whitelist`): one `get_doc(for_update=True)`
  for the whole transaction, skips terminal states, runs compose → verify → route → send, and
  persists once per outcome through `_save_out()` (which sets `ignore_version` so `check_if_latest`
  never takes a second lock on the already-locked row).

- New **Sending** delivery status (added to the doctype Select) marks in-flight messages so the
  button can't double-fire; the JS shows a headline + "Refresh Status" button instead.

- `dispatch_outbound_queue()` recovers **orphaned Sending rows** (worker died) after
  `_SENDING_STALE_MIN` minutes, and both trigger + scheduler enqueue with the same
  `job_id=edx-dispatch-{name}` so concurrent ticks can't double-send.

- Removed debug `frappe.logger().info(...)` spam from `routing.resolve_route`.

## Files Changed
- `awbix/edx/doctype/edx_message_out/edx_message_out.py` — `dispatch()` enqueues.
- `awbix/edx/doctype/edx_message_out/edx_message_out.js` — async UX (queued toast, Sending state).
- `awbix/edx/doctype/edx_message_out/edx_message_out.json` — add `Sending` status.
- `awbix/edx/engine/pipeline.py` — worker lock/save cleanup, `_save_out`, queue/recovery, dedup.
- `awbix/edx/engine/routing.py` — drop debug logging.

## Verification
- All three Python files byte-compile; `pipeline.py` + controller pass `ruff` clean.
- FHL dispatch tests (`test_fhl_composer.py`) currently error in `setUp` (`Airline` autoname needs
  `Carrier Code`, but the fixture seeds only `airline_prefix`) — **pre-existing fixture bug,
  unrelated to dispatch**; no dispatch code is reached. Fixing that fixture is out of scope here.
