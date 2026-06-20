"""FSU/14 (Functional Status Update, Cargo-IMP) inbound parser.

One AWB = one Shipment FSU document. Each FSU message adds status events to that document's
child table (additive stream); history is never erased. bypass_amendment is set in the
EDX Message Definition so every message reaches process() regardless of arrival order.
"""

import re
from datetime import datetime

import frappe

from awbix.edx.engine.base_parser import BaseParser
from awbix.edx.handlers.fwb import cargoimp

# Matches the SMI line for both FSU and FSA so the FSA subclass reuses this unchanged.
_SMI_RE = re.compile(r"^(?:FSU|FSA)/\d", re.MULTILINE)

# Origin and destination are optional per FSU.md §2.2.
_AWB_RE = re.compile(r"^(\d{1,3})-(\d{8})(?:([A-Z]{3})([A-Z]{3}))?(?:/(.*))?$")

# DDMMMHHMM (e.g. 20JUN1039) or DDMMM (e.g. 20JUN) — combined Cargo-IMP date/time token.
_DATE_RE = re.compile(r"^(\d{1,2})([A-Z]{3})(\d{4})?$")

_MONTH_MAP = {
	"JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
	"JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}


def _strip_preamble(raw: str) -> str:
	"""Drop the Type-B telex envelope (QD / .HDQFMQR lines) before the SMI."""
	m = _SMI_RE.search(raw or "")
	return raw[m.start():] if m else (raw or "")


def _build_timestamp(day_str, month_str, time_str=None) -> str | None:
	"""Convert Cargo-IMP day/month/time fields to a Frappe datetime string."""
	try:
		day = int(day_str)
		month = _MONTH_MAP.get((month_str or "").upper())
		if not month:
			return None
		year = datetime.now().year
		hour = int(time_str[:2]) if time_str and len(time_str) >= 4 else 0
		minute = int(time_str[2:4]) if time_str and len(time_str) >= 4 else 0
		return f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:00"
	except (ValueError, TypeError):
		return None


def _parse_status_event(seg: dict) -> dict | None:
	"""Extract a status event from a segment dict; returns None if unparseable."""
	if not seg or not seg.get("lines"):
		return None

	header = seg["lines"][0]
	parts = [p.strip() for p in header.split("/")]
	status_code = parts[0] if parts else None
	if not status_code:
		return None

	fields = parts[1:]
	event = {
		"status_code": status_code,
		"status_timestamp": None,
		"location": None,
		"carrier_code": None,
		"flight_number": None,
		"description": None,
	}

	# Best-effort field extraction: scan tokens by recognisable pattern.
	# Order matters — carrier (2-char alpha) before airport (3-char alpha).
	for field in fields:
		if not field:
			continue

		# Combined date+time token: DDMMMHHMM or DDMMM
		dm = _DATE_RE.match(field)
		if dm and not event["status_timestamp"]:
			day, month, time = dm.groups()
			event["status_timestamp"] = _build_timestamp(day, month, time)
			continue

		# 2-char alpha = carrier code
		if re.match(r"^[A-Z]{2}$", field) and not event["carrier_code"]:
			event["carrier_code"] = field
			continue

		# 3-char alpha = airport code — use the first one as location
		if re.match(r"^[A-Z]{3}$", field) and not event["location"]:
			event["location"] = field
			continue

		# 3-5 char alphanumeric starting with digits = flight number
		if re.match(r"^\d{3,5}[A-Z]?$", field) and not event["flight_number"]:
			event["flight_number"] = field
			continue

	# Continuation lines (/…) become the description
	cont = cargoimp.continuation_text(seg)
	if cont:
		event["description"] = " | ".join(cont)

	# If we have no timestamp (many status types omit it), use a sentinel so the
	# upsert key is still unique per status_code + location combination.
	if not event["status_timestamp"]:
		event["status_timestamp"] = frappe.utils.now()

	return event


class FSUParser(BaseParser):
	message_type = "FSU"
	version = "14"

	# ------------------------------------------------------------------ parse

	def parse(self, raw: str) -> dict:
		t = cargoimp.tokenize(_strip_preamble(raw))

		message = {
			"type": self.message_type,
			"version": self.version,
			"id": t.get("message_id"),
		}

		awb_ref = self._parse_awb_line(t.get("awb_line"))

		events = []
		segments_seen = []
		for seg in t["segments"]:
			code = seg.get("code")
			if code:
				segments_seen.append(code)
				event = _parse_status_event(seg)
				if event:
					events.append(event)

		return {
			"message": message,
			"awb_reference": awb_ref,
			"fsu_data": {
				"status_code": events[-1]["status_code"] if events else None,
				"movement_records": events,
			},
			"raw_detail": raw or "",
			"segments_seen": segments_seen,
		}

	def _parse_awb_line(self, line: str | None) -> dict:
		if not line:
			return {}
		m = _AWB_RE.match(line.strip())
		if not m:
			return {"raw_detail": line}
		prefix, serial, origin, dest, rest = m.groups()
		return {
			"airline_prefix": prefix,
			"awb_serial_number": serial,
			"awb_number": f"{prefix}-{serial}",
			"origin": origin,
			"destination": dest,
			"raw_detail": rest or "",
		}

	# ------------------------------------------------------------ business key

	def business_key(self, data: dict) -> str | None:
		return (data.get("awb_reference") or {}).get("awb_number")

	# --------------------------------------------------------------- validate

	def validate(self, data: dict) -> list[dict]:
		issues = []
		awb = data.get("awb_reference") or {}

		if not awb.get("awb_number"):
			return [{"level": "Error", "code": "AWB_REF", "field": "awb_reference",
					 "message": "Could not parse the AWB consignment detail line"}]

		serial = (awb.get("awb_serial_number") or "").strip()
		if not (serial.isdigit() and len(serial) == 8):
			issues.append({"level": "Error", "code": "AWB_SERIAL", "field": "awb_serial_number",
						   "message": "AWB serial must be exactly 8 digits"})
		elif int(serial[:7]) % 7 != int(serial[7]):
			# IATA CSC Res. 600a: check digit = int(first 7 digits) % 7, NOT a digit-sum.
			expected = int(serial[:7]) % 7
			issues.append({"level": "Error", "code": "AWB_CHECKDIGIT", "field": "awb_serial_number",
						   "message": f"Invalid AWB check digit (expected {expected})"})

		if not data.get("fsu_data", {}).get("movement_records"):
			issues.append({"level": "Warning", "code": "NO_DATA", "field": "segments_seen",
						   "message": "No FSU status segments found in message"})

		origin = awb.get("origin")
		dest = awb.get("destination")
		if origin and dest and origin == dest:
			issues.append({"level": "Warning", "code": "ROUTE", "field": "destination",
						   "message": "Origin and destination are the same airport"})

		return issues

	# ---------------------------------------------------------------- process

	def process(self, data: dict, message_in) -> str:
		awb = data["awb_reference"]
		awb_number = awb["awb_number"]
		origin = awb.get("origin")
		destination = awb.get("destination")

		# Ensure Airport master records exist for any airports present.
		if origin:
			self._ensure("Airport", {"iata_code": origin}, origin)
		if destination:
			self._ensure("Airport", {"iata_code": destination}, destination)
		for event in data["fsu_data"]["movement_records"]:
			loc = event.get("location")
			if loc:
				self._ensure("Airport", {"iata_code": loc}, loc)

		# Find or create the Shipment FSU document for this AWB.
		if frappe.db.exists("Shipment FSU", awb_number):
			doc = frappe.get_doc("Shipment FSU", awb_number)
		else:
			doc = frappe.new_doc("Shipment FSU")
			doc.awb_number = awb_number

		# Refresh scalar fields.
		if origin:
			doc.origin = origin
		if destination:
			doc.destination = destination
		if data["fsu_data"].get("status_code"):
			doc.status_code = data["fsu_data"]["status_code"]
		doc.raw_message = data.get("raw_detail") or ""

		# Link the reference Shipment only if it already exists — never create it.
		if not doc.shipment and frappe.db.exists("Shipment", awb_number):
			doc.shipment = awb_number

		# Upsert status events by natural key (status_code, status_timestamp, location).
		# Append a row only when that triple is not already present so re-processing
		# the same message is a no-op and history accumulates across messages.
		existing_keys = {
			(r.status_code, str(r.status_timestamp or ""), r.location or "")
			for r in doc.fsu_status_records
		}
		for event in data["fsu_data"]["movement_records"]:
			key = (
				event["status_code"],
				str(event.get("status_timestamp") or ""),
				event.get("location") or "",
			)
			if key not in existing_keys:
				doc.append("fsu_status_records", {
					"status_code": event["status_code"],
					"status_timestamp": event.get("status_timestamp"),
					"location": event.get("location"),
					"carrier_code": event.get("carrier_code"),
					"flight_number": event.get("flight_number"),
					"description": event.get("description"),
				})
				existing_keys.add(key)

		doc.flags.ignore_permissions = True
		doc.save()
		return awb_number

	# ----------------------------------------------------------------- helpers

	def _ensure(self, doctype: str, values: dict, name: str) -> None:
		if name and not frappe.db.exists(doctype, name):
			d = frappe.new_doc(doctype)
			d.update(values)
			d.flags.ignore_permissions = True
			d.insert()
