"""Generic inbound/outbound orchestration.

Engine-side only: it knows the lifecycle (stage → in → verify → process) and the
amendment policy, but nothing about any specific message format — that lives in the
parser/composer handlers resolved from the registry.

Lifecycle entry points (all whitelisted so the Desk buttons / API can call them):
    ingest_raw → promote_stage → verify_message_in → process_message_in
Scheduler entry points: poll_inbound_connections, dispatch_outbound_queue, retry_failed
"""

import hashlib

import frappe
from frappe import _
from frappe.utils import add_to_date, get_datetime, now_datetime

from awbix.edx.engine.classifier import classify
from awbix.edx.engine.registry import get_definition, get_parser

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def log_event(reference_doctype, reference_name, event, level="Info", message="", traceback=""):
	"""Append one row to EDX Message Log. Logging must never break the flow."""
	try:
		frappe.get_doc(
			{
				"doctype": "EDX Message Log",
				"reference_doctype": reference_doctype,
				"reference_name": reference_name,
				"event": event,
				"level": level,
				"message": (message or "")[:2000],
				"traceback": traceback or "",
				"timestamp": now_datetime(),
			}
		).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "EDX log_event failed")


def _hash(raw: str) -> str:
	return hashlib.sha256((raw or "").encode("utf-8", "replace")).hexdigest()


def _flatten(data, prefix=""):
	"""Flatten nested dict/list into [{field, value}] rows for the verify grid."""
	rows = []
	if isinstance(data, dict):
		for k, v in data.items():
			rows += _flatten(v, f"{prefix}{k}.")
	elif isinstance(data, list):
		for i, v in enumerate(data):
			rows += _flatten(v, f"{prefix}{i}.")
	else:
		rows.append({"field": prefix.rstrip("."), "value": "" if data is None else str(data)})
	return rows


# ---------------------------------------------------------------------------
# Ingest → EDX Message Stage  (no filtering; dedup only)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def ingest_raw(raw, connection=None, sender=None, subject=None, external_id=None):
	"""Capture a raw inbound payload into EDX Message Stage.

	Safe for both transport polls and manual upload. Deduplicates on content hash and
	on (connection, external_id). Returns the (possibly pre-existing) stage docname.
	"""
	content_hash = _hash(raw)

	existing = frappe.db.exists("EDX Message Stage", {"content_hash": content_hash})
	if existing:
		log_event("EDX Message Stage", existing, "Ingested", "Info", "Duplicate payload ignored")
		return existing

	if connection and external_id:
		dup = frappe.db.exists("EDX Message Stage", {"connection": connection, "external_id": external_id})
		if dup:
			return dup

	stage = frappe.get_doc(
		{
			"doctype": "EDX Message Stage",
			"connection": connection,
			"received_at": now_datetime(),
			"raw_message": raw,
			"content_hash": content_hash,
			"external_id": external_id,
			"sender": sender,
			"subject": subject,
			"status": "Staged",
		}
	).insert(ignore_permissions=True)
	log_event("EDX Message Stage", stage.name, "Ingested", "Info", "Staged")

	_classify_stage(stage)
	return stage.name


def _classify_stage(stage):
	mtype, mver = classify(stage.raw_message)
	if not mtype:
		stage.db_set("status", "Unrecognized")
		log_event("EDX Message Stage", stage.name, "Classified", "Warning", "No matching definition")
		return
	stage.db_set("detected_type", mtype)
	stage.db_set("detected_version", mver)
	log_event("EDX Message Stage", stage.name, "Classified", "Info", f"{mtype}/{mver}")

	if get_definition(mtype, mver).auto_promote:
		promote_stage(stage.name)


# ---------------------------------------------------------------------------
# Promote: Stage → EDX Message In
# ---------------------------------------------------------------------------


@frappe.whitelist()
def promote_stage(stage_name):
	stage = frappe.get_doc("EDX Message Stage", stage_name)
	if stage.message_in:
		return stage.message_in
	if not stage.detected_type:
		frappe.throw(_("Stage {0} is not classified; cannot promote").format(stage_name))

	mi = frappe.get_doc(
		{
			"doctype": "EDX Message In",
			"stage": stage.name,
			"message_type": stage.detected_type,
			"message_version": stage.detected_version,
			"received_at": stage.received_at,
			"raw_message": stage.raw_message,
			"parse_status": "Pending",
			"process_status": "Not Processed",
		}
	).insert(ignore_permissions=True)
	stage.db_set("message_in", mi.name)
	stage.db_set("status", "Promoted")
	log_event("EDX Message In", mi.name, "Promoted", "Info", f"from {stage.name}")

	if get_definition(stage.detected_type, stage.detected_version).auto_process:
		frappe.enqueue("awbix.edx.engine.pipeline.process_message_in", queue="long", name=mi.name)
	return mi.name


# ---------------------------------------------------------------------------
# Verify: parse + validate  (NO business writes)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def verify_message_in(name):
	mi = frappe.get_doc("EDX Message In", name)
	parser = get_parser(mi.message_type, mi.message_version)

	try:
		data = parser.parse(mi.raw_message)
	except Exception as e:
		mi.parse_status = "Verification Failed"
		mi.set("issues", [{"level": "Error", "code": "PARSE", "message": str(e)}])
		mi.save(ignore_permissions=True)
		log_event("EDX Message In", name, "Parsed", "Error", str(e), frappe.get_traceback())
		return {"ok": False, "issues": [i.as_dict() for i in mi.issues]}

	issues = parser.validate(data) or []
	has_error = any(i.get("level") == "Error" for i in issues)

	mi.business_key = parser.business_key(data)
	mi.parsed_json = frappe.as_json(data, indent=2)
	mi.set("issues", issues)
	mi.set("verify_rows", _flatten(data))
	mi.parse_status = "Verification Failed" if has_error else "Verified"
	mi.save(ignore_permissions=True)

	log_event(
		"EDX Message In", name, "Verified", "Warning" if has_error else "Info", f"{len(issues)} issue(s)"
	)
	return {"ok": not has_error, "issues": issues}


# ---------------------------------------------------------------------------
# Process: amendment-aware persist into business DocTypes
# ---------------------------------------------------------------------------


@frappe.whitelist()
def process_message_in(name):
	mi = frappe.get_doc("EDX Message In", name)

	if mi.parse_status != "Verified":
		res = verify_message_in(name)
		mi.reload()
		if not res.get("ok"):
			mi.db_set("process_status", "Failed")
			return {"ok": False, "status": "Verification Failed"}

	definition = get_definition(mi.message_type, mi.message_version)
	parser = get_parser(mi.message_type, mi.message_version)
	data = frappe.parse_json(mi.parsed_json or "{}")
	key = mi.business_key or parser.business_key(data)
	target_doctype = definition.target_doctype

	mi.db_set("process_status", "Processing")

	# Status/annotation messages (FNA/FMA): no amendment guards, no EDX Delivery ledger —
	# process() only annotates an existing target, and must reach even a submitted one.
	if definition.bypass_amendment:
		return _process_annotation(mi, parser, data, target_doctype)

	decision = _amendment_decision(definition, target_doctype, key, mi.received_at)
	if decision != "apply":
		status = "Superseded" if decision == "stale" else "Needs Review"
		mi.db_set("process_status", status)
		log_event("EDX Message In", name, "Superseded" if decision == "stale" else "Processed",
			"Warning", f"Not applied: {decision}")
		return {"ok": True, "applied": False, "reason": decision}

	try:
		target_name = parser.process(data, mi)
	except frappe.ValidationError as e:
		frappe.db.rollback()
		mi.reload()
		mi.db_set("process_status", "Failed")
		mi.append("issues", {"level": "Error", "code": "PROCESS", "message": str(e)})
		mi.save(ignore_permissions=True)
		log_event("EDX Message In", name, "Failed", "Error", str(e), frappe.get_traceback())
		return {"ok": False, "status": "Failed", "error": str(e)}

	rev = _upsert_delivery(target_doctype, key, target_name, mi.name, mi.received_at)
	mi.db_set("process_status", "Processed")
	mi.db_set("applied", 1)
	mi.db_set("target_doctype", target_doctype)
	mi.db_set("target_name", target_name)
	mi.db_set("delivery_status", "Delivered")
	log_event("EDX Message In", name, "Processed", "Info", f"{target_doctype} {target_name} (rev {rev})")
	return {"ok": True, "applied": True, "target": target_name, "revision": rev}


def _process_annotation(mi, parser, data, target_doctype):
	"""Process a bypass-amendment message: annotate the target, no ledger, no guards.

	``process()`` returns the target docname when it found and updated one, or a falsy
	value when the referenced business document doesn't exist (→ Needs Review).
	"""
	name = mi.name
	try:
		target_name = parser.process(data, mi)
	except frappe.ValidationError as e:
		frappe.db.rollback()
		mi.reload()
		mi.db_set("process_status", "Failed")
		mi.append("issues", {"level": "Error", "code": "PROCESS", "message": str(e)})
		mi.save(ignore_permissions=True)
		log_event("EDX Message In", name, "Failed", "Error", str(e), frappe.get_traceback())
		return {"ok": False, "status": "Failed", "error": str(e)}

	if not target_name:
		mi.db_set("process_status", "Needs Review")
		log_event("EDX Message In", name, "Processed", "Warning", "No matching target document")
		return {"ok": True, "applied": False, "reason": "target not found"}

	mi.db_set("process_status", "Processed")
	mi.db_set("applied", 1)
	mi.db_set("target_doctype", target_doctype)
	mi.db_set("target_name", target_name)
	mi.db_set("delivery_status", "Delivered")
	log_event("EDX Message In", name, "Processed", "Info", f"Annotated {target_doctype} {target_name}")
	return {"ok": True, "applied": True, "target": target_name}


def _amendment_decision(definition, target_doctype, key, received_at):
	"""Decide how a (possibly re-received) message should be applied.

	Returns 'apply', 'stale', or 'review'. See strategy §6.
	"""
	if not key:
		return "apply"

	delivery = _get_delivery(target_doctype, key)  # row-locks if present
	if not delivery:
		return "apply"  # first time we've seen this business key

	# lock-guard: never auto-overwrite a manually locked or submitted target
	if delivery.locked:
		return "review"
	if delivery.target_name and frappe.get_meta(target_doctype).is_submittable:
		if frappe.db.get_value(target_doctype, delivery.target_name, "docstatus") == 1:
			return "review"

	# stale-guard: an older message must not clobber newer data
	if received_at and delivery.last_source_received_at:
		if get_datetime(received_at) < get_datetime(delivery.last_source_received_at):
			return "stale"

	if (definition.amendment_mode or "Auto Apply") == "Manual Review":
		return "review"
	return "apply"


def _get_delivery(target_doctype, key):
	name = frappe.db.exists("EDX Delivery", {"business_key": key, "target_doctype": target_doctype})
	if not name:
		return None
	# row-lock to serialise concurrent workers processing the same business key
	frappe.db.get_value("EDX Delivery", name, "name", for_update=True)
	return frappe.get_doc("EDX Delivery", name)


def _upsert_delivery(target_doctype, key, target_name, message_in, received_at):
	if not key:
		return 1
	name = frappe.db.exists("EDX Delivery", {"business_key": key, "target_doctype": target_doctype})
	if name:
		d = frappe.get_doc("EDX Delivery", name)
		d.revision = (d.revision or 1) + 1
		d.current_message_in = message_in
		d.target_name = target_name
		d.last_source_received_at = received_at or now_datetime()
		d.save(ignore_permissions=True)
		return d.revision
	frappe.get_doc(
		{
			"doctype": "EDX Delivery",
			"business_key": key,
			"target_doctype": target_doctype,
			"target_name": target_name,
			"current_message_in": message_in,
			"revision": 1,
			"last_source_received_at": received_at or now_datetime(),
			"status": "Active",
		}
	).insert(ignore_permissions=True)
	return 1


# ---------------------------------------------------------------------------
# Scheduler entry points (transports land in M4; guarded until then)
# ---------------------------------------------------------------------------


def poll_inbound_connections():
	if not frappe.db.exists("DocType", "EDX Connection"):
		return
	for name in frappe.get_all(
		"EDX Connection",
		filters={"enabled": 1, "direction": ["in", ["Inbound", "Both"]], "channel": ["!=", "Manual"]},
		pluck="name",
	):
		frappe.enqueue("awbix.edx.engine.pipeline.poll_connection", queue="long", connection=name)


def poll_connection(connection):
	from awbix.edx.engine.registry import get_transport

	conn = frappe.get_doc("EDX Connection", connection)
	transport = get_transport(conn)
	for msg in transport.poll():
		ingest_raw(
			msg.get("raw"),
			connection=conn.name,
			sender=msg.get("sender"),
			subject=msg.get("subject"),
			external_id=msg.get("external_id"),
		)
	conn.db_set("last_polled_at", now_datetime())


# ---------------------------------------------------------------------------
# Outbound: compose → verify → route → send  (Composer engine, M5)
# ---------------------------------------------------------------------------

_RETRY_BACKOFF_MIN = 10
_MAX_RETRIES = 5


@frappe.whitelist()
def queue_outbound(source_doctype, source_name, message_type, version):
	"""Create a Queued EDX Message Out for a source document and enqueue dispatch.

	Trigger surface for the Desk button / API. Composition and sending happen
	asynchronously in ``dispatch_message_out`` so the caller returns immediately.
	"""
	get_definition(message_type, version)  # fail fast if the type/version is unknown
	source = frappe.get_doc(source_doctype, source_name)

	mo = frappe.get_doc(
		{
			"doctype": "EDX Message Out",
			"message_type": message_type,
			"message_version": version,
			"source_doctype": source_doctype,
			"source_name": source_name,
			"business_key": source.get("awb_number") or source.name,
			"compose_status": "Pending",
			"verify_status": "Pending",
			"delivery_status": "Queued",
		}
	).insert(ignore_permissions=True)
	log_event("EDX Message Out", mo.name, "Ingested", "Info", f"Queued from {source_doctype} {source_name}")

	frappe.enqueue("awbix.edx.engine.pipeline.dispatch_message_out", queue="long", name=mo.name)
	return mo.name


def dispatch_message_out(name):
	"""Run one outbound message through compose → verify → route → send.

	Never raises: every failure is recorded on the row (status + issue + retry schedule)
	so a bad message can't crash the dispatch worker (strategy R1 style).
	"""
	from awbix.edx.engine.registry import get_composer, get_transport
	from awbix.edx.engine.routing import resolve_route

	mo = frappe.get_doc("EDX Message Out", name)
	source = frappe.get_doc(mo.source_doctype, mo.source_name)

	# --- compose ---
	try:
		composer = get_composer(mo.message_type, mo.message_version)
		raw = composer.compose(source)
		mo.composed_raw = raw
		mo.compose_status = "Composed"
	except Exception as e:
		return _fail_out(mo, "COMPOSE", e, retry=False, compose=True)

	# --- verify (self-check; a data error must not be sent) ---
	issues = composer.verify(raw) or []
	mo.set("issues", issues)
	if any(i.get("level") == "Error" for i in issues):
		mo.verify_status = "Verification Failed"
		mo.delivery_status = "Failed"
		mo.save(ignore_permissions=True)
		log_event("EDX Message Out", name, "Verified", "Error", f"{len(issues)} issue(s); not sent")
		return {"ok": False, "status": "Verification Failed"}
	mo.verify_status = "Verified"

	# --- route ---
	route = resolve_route(
		mo.message_type,
		source.get("airline_prefix"),
		source.get("origin"),
		source.get("destination"),
	)
	if not route or not route.get("connection"):
		mo.save(ignore_permissions=True)
		return _fail_out(mo, "ROUTE", _("No routing rule matched this message"), retry=False)
	mo.connection = route["connection"]
	mo.address_type = route.get("address_type")
	mo.address = route.get("address")

	# --- send ---
	try:
		transport = get_transport(mo.connection)
		meta = {
			"to": mo.address,
			"subject": f"{mo.message_type}/{mo.message_version} {mo.business_key or ''}".strip(),
			"routing_key": mo.address,
			"external_id": mo.business_key,
		}
		result = transport.send(raw, meta) or {}
	except Exception as e:
		mo.save(ignore_permissions=True)
		return _fail_out(mo, "SEND", e, retry=True)

	if not result.get("ok"):
		mo.save(ignore_permissions=True)
		return _fail_out(mo, "SEND", result.get("response") or "Transport reported failure", retry=True)

	mo.delivery_status = "Sent"
	mo.sent_at = now_datetime()
	mo.external_id = result.get("external_id")
	mo.response = (result.get("response") or "")[:140]
	mo.save(ignore_permissions=True)
	log_event("EDX Message Out", name, "Sent", "Info", f"Sent via {mo.connection}")
	return {"ok": True, "status": "Sent", "connection": mo.connection}


def _fail_out(mo, code, error, retry=True, compose=False):
	"""Record an outbound failure on the row; schedule a retry when retryable."""
	message = str(error)
	if compose:
		mo.compose_status = "Compose Failed"
	mo.append("issues", {"level": "Error", "code": code, "message": message[:500]})

	if retry and (mo.retry_count or 0) < _MAX_RETRIES:
		mo.retry_count = (mo.retry_count or 0) + 1
		mo.next_retry_at = add_to_date(now_datetime(), minutes=_RETRY_BACKOFF_MIN * mo.retry_count)
		mo.delivery_status = "Queued"
	else:
		mo.delivery_status = "Failed"
	mo.save(ignore_permissions=True)
	log_event("EDX Message Out", mo.name, "Failed", "Error", f"{code}: {message}", frappe.get_traceback())
	return {"ok": False, "status": mo.delivery_status, "error": message}


def dispatch_outbound_queue():
	"""Scheduler tick: enqueue dispatch for all Queued outbound messages that are due."""
	if not frappe.db.exists("DocType", "EDX Message Out"):
		return
	now = now_datetime()
	for name in frappe.get_all(
		"EDX Message Out",
		filters={"delivery_status": "Queued"},
		pluck="name",
	):
		row = frappe.db.get_value("EDX Message Out", name, "next_retry_at")
		if row and get_datetime(row) > get_datetime(now):
			continue  # a retry that isn't due yet
		frappe.enqueue("awbix.edx.engine.pipeline.dispatch_message_out", queue="long", name=name)


def retry_failed():
	"""Re-enqueue messages whose retry window has elapsed (inbound + outbound).

	Only rows with a due ``next_retry_at`` are retried — failures aren't auto-scheduled, so
	a permanent data error stays terminal until an operator (or a future dead-letter policy)
	sets a retry time. The full dead-letter queue / perf pass is still open.
	"""
	if frappe.db.exists("DocType", "EDX Message Out"):
		dispatch_outbound_queue()
	_retry_inbound()


def _retry_inbound():
	if not frappe.db.exists("DocType", "EDX Message In"):
		return
	now = now_datetime()
	for name in frappe.get_all(
		"EDX Message In",
		filters={"process_status": "Failed", "next_retry_at": ["<=", now]},
		pluck="name",
	):
		frappe.enqueue("awbix.edx.engine.pipeline.process_message_in", queue="long", name=name)
