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
from frappe.utils import get_datetime, now_datetime

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


def dispatch_outbound_queue():
	"""Compose + send queued outbound messages — implemented in M5."""
	pass


def retry_failed():
	"""Re-enqueue failed messages past their next_retry_at — implemented in M6."""
	pass
