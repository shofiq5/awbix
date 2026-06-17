"""Shared logic for the acknowledgement family (FMA accept / FNA reject).

Both messages echo back (part of) the original message we sent and carry a short reason on
their second line. They never create a Shipment — they annotate an existing one and close
the loop on the ``EDX Message Out`` we dispatched. Correlation is by the AWB recovered from
the echoed body (these messages have no key of their own).
"""

import re

import frappe
from frappe.utils import now_datetime

from awbix.edx.handlers.fwb import cargoimp

# AWB consignment line inside the echoed message, e.g. "157-68076960BSLDOH/…".
_AWB_RE = re.compile(r"^(\d{1,3})-(\d{8})([A-Z]{3})([A-Z]{3})", re.MULTILINE)


def parse_ack(raw: str, kind: str) -> dict:
	"""Split an FMA/FNA message into id, reason, and the echoed received message.

	Line 1 is the message identifier (``FMA`` / ``FNA/1``); line 2 is the reason line
	(``ACK/<reason>`` for FMA, ``<id>/<error>`` for FNA); the remainder is the echoed body.
	"""
	lines = cargoimp.normalize(raw)
	message_id = lines[0] if lines else ""
	line_id, reason = "", ""
	received = []

	if len(lines) > 1:
		head = lines[1]
		if "/" in head:
			line_id, reason = head.split("/", 1)
		else:
			line_id = head
		received = lines[2:]

	return {
		"message": {"type": kind, "version": "1", "id": message_id},
		"line_id": line_id.strip(),
		"reason": reason.strip(),
		"received_message": "\n".join(received).strip(),
	}


def extract_awb(received_message: str) -> str | None:
	"""Return the AWB number ``{prefix}-{serial}`` found in the echoed body, or None."""
	m = _AWB_RE.search(received_message or "")
	if not m:
		return None
	return f"{m.group(1)}-{m.group(2)}"


def validate_ack(data: dict) -> list[dict]:
	issues = []
	if not data.get("reason"):
		issues.append({"level": "Info", "code": "ACK_REASON", "field": "reason", "message": "No reason text"})
	if not extract_awb(data.get("received_message", "")):
		issues.append(
			{
				"level": "Warning",
				"code": "ACK_AWB",
				"field": "received_message",
				"message": "No AWB found in the echoed message; cannot correlate to a Shipment",
			}
		)
	return issues


def apply_ack(business_key: str, status: str, reason: str) -> str | None:
	"""Stamp the Shipment ack fields (via db.set_value so a submitted doc is fine — R3).

	Returns the Shipment name when found and updated, else None (→ Needs Review upstream).
	"""
	if not business_key or not frappe.db.exists("Shipment", business_key):
		return None
	frappe.db.set_value(
		"Shipment",
		business_key,
		{
			"edx_ack_status": status,
			"edx_ack_detail": (reason or "")[:140],
			"edx_ack_at": now_datetime(),
		},
	)
	return business_key


def reconcile_message_out(business_key: str, outcome: str, reason: str) -> None:
	"""Close the loop on the FWB we sent: mark its EDX Message Out Delivered/Failed.

	``outcome`` is ``"ack"`` (FMA) or ``"nak"`` (FNA). Matches the most recent outbound FWB
	for the business key; a no-op if none was sent from here.
	"""
	if not business_key:
		return
	names = frappe.get_all(
		"EDX Message Out",
		filters={"business_key": business_key, "message_type": "FWB"},
		order_by="creation desc",
		pluck="name",
		limit=1,
	)
	if not names:
		return
	frappe.db.set_value(
		"EDX Message Out",
		names[0],
		{
			"delivery_status": "Delivered" if outcome == "ack" else "Failed",
			"response": (f"{outcome.upper()}: {reason}" or "")[:140],
		},
	)
