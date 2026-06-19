"""FWB/16 (Air Waybill, Cargo-IMP) inbound parser.

First-pass coverage: message id, AWB consignment detail, routing, shipper/consignee/
agent names, and charge-declaration currency — enough to create/update a Shipment
end-to-end. Remaining segments (RTD/OTH/charge summaries/SPH/OCI/…) are recognised in
``segments_seen`` and will be mapped per the full FWB rule manual (see strategy §9).
"""

import re

import frappe

from awbix.edx.engine.base_parser import BaseParser
from awbix.edx.handlers.fwb import cargoimp

# <prefix>-<8-digit serial><origin><dest>[/additional info]
_AWB_RE = re.compile(r"^(\d{1,3})-(\d{8})([A-Z]{3})([A-Z]{3})(?:/(.*))?$")


class FWB16Parser(BaseParser):
	message_type = "FWB"
	version = "16"

	# ------------------------------------------------------------------ parse
	def parse(self, raw: str) -> dict:
		t = cargoimp.tokenize(raw)
		return {
			"message": {"type": self.message_type, "version": self.version, "id": t.get("message_id")},
			"awb": self._parse_awb(t.get("awb_line")),
			"routing": self._parse_routing(t),
			"shipper": self._parse_party(t, "SHP"),
			"consignee": self._parse_party(t, "CNE"),
			"agent": self._parse_party(t, "AGT"),
			"charge_declarations": self._parse_cvd(t),
			"segments_seen": [s["code"] for s in t["segments"] if s["code"]],
		}

	def _parse_awb(self, line):
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

	def _parse_routing(self, t):
		seg = cargoimp.first(t, "RTG")
		if not seg:
			return []
		parts = [p for p in seg["lines"][0].split("/")[1:] if p]
		rows = []
		for i, tok in enumerate(parts, start=1):
			rows.append({"sequence": i, "airport": tok[:3], "carrier": tok[3:5] if len(tok) >= 5 else ""})
		return rows

	def _parse_party(self, t, code):
		seg = cargoimp.first(t, code)
		if not seg:
			return {}
		lines = cargoimp.continuation_text(seg)
		return {"name": (lines[0] if lines else "")[:140], "lines": lines}

	def _parse_cvd(self, t):
		seg = cargoimp.first(t, "CVD")
		if not seg:
			return {}
		parts = seg["lines"][0].split("/")
		return {"currency": parts[1] if len(parts) > 1 else "", "raw": seg["lines"][0]}

	# ------------------------------------------------------------ business key
	def business_key(self, data):
		return (data.get("awb") or {}).get("awb_number")

	# --------------------------------------------------------------- validate
	def validate(self, data):
		issues = []
		awb = data.get("awb") or {}
		if not awb.get("awb_number"):
			return [
				{
					"level": "Error",
					"code": "AWB",
					"field": "awb",
					"message": "Could not parse the AWB consignment detail line",
				}
			]
		serial = (awb.get("awb_serial_number") or "").strip()
		if not (serial.isdigit() and len(serial) == 8):
			issues.append(
				{
					"level": "Error",
					"code": "AWB_SERIAL",
					"field": "awb_serial_number",
					"message": "AWB serial number must be exactly 8 digits",
				}
			)
		elif int(serial[:7]) % 7 != int(serial[7]):
			issues.append(
				{
					"level": "Error",
					"code": "AWB_CHECKDIGIT",
					"field": "awb_serial_number",
					"message": f"Invalid AWB check digit (expected {int(serial[:7]) % 7})",
				}
			)
		if awb.get("origin") and awb.get("origin") == awb.get("destination"):
			issues.append(
				{
					"level": "Error",
					"code": "ROUTE",
					"field": "destination",
					"message": "Origin and destination are the same airport",
				}
			)
		if not (data.get("charge_declarations") or {}).get("currency"):
			issues.append(
				{
					"level": "Warning",
					"code": "CURRENCY",
					"field": "currency",
					"message": "No currency found in CVD; a default will be used on process",
				}
			)
		return issues

	# ---------------------------------------------------------------- process
	def process(self, data, message_in) -> str:
		awb = data["awb"]
		name = awb["awb_number"]

		self._ensure("Airline", {"airline_prefix": awb["airline_prefix"]}, awb["airline_prefix"])
		self._ensure("Airport", {"iata_code": awb["origin"]}, awb["origin"])
		self._ensure("Airport", {"iata_code": awb["destination"]}, awb["destination"])
		currency = (data.get("charge_declarations") or {}).get("currency") or "USD"
		self._ensure_currency(currency)

		if frappe.db.exists("Shipment", name):
			doc = frappe.get_doc("Shipment", name)  # amendment: update in place
		else:
			doc = frappe.new_doc("Shipment")

		doc.airline_prefix = awb["airline_prefix"]
		doc.awb_serial_number = awb["awb_serial_number"]
		doc.origin = awb["origin"]
		doc.destination = awb["destination"]
		doc.currency = currency
		doc.shipper_name = (data.get("shipper") or {}).get("name") or doc.shipper_name
		doc.consignee_name = (data.get("consignee") or {}).get("name") or doc.consignee_name
		doc.agent_name = (data.get("agent") or {}).get("name") or doc.agent_name

		doc.set("routing", [])
		routing_rows = data.get("routing", [])
		for r in routing_rows:
			self._ensure("Airport", {"iata_code": r["airport"]}, r["airport"])
			if r.get("carrier"):
				self._ensure("Airline", {"airline_prefix": r["carrier"]}, r["carrier"])
			doc.append("routing", {"sequence": r["sequence"], "airport": r["airport"], "carrier_code": r.get("carrier") or ""})

		if routing_rows:
			r0 = routing_rows[0]
			doc.to_airport1 = r0["airport"]
			doc.by_carrier1 = r0.get("carrier") or ""
		if len(routing_rows) >= 2:
			r1 = routing_rows[1]
			doc.to_airport2 = r1["airport"]
			doc.by_carrier2 = r1.get("carrier") or ""

		doc.flags.ignore_permissions = True
		doc.save()
		return doc.name

	# ----------------------------------------------------------------- helpers
	def _ensure(self, doctype, values, name):
		if name and not frappe.db.exists(doctype, name):
			d = frappe.new_doc(doctype)
			d.update(values)
			d.flags.ignore_permissions = True
			d.insert()

	def _ensure_currency(self, code):
		if code and not frappe.db.exists("Currency", code):
			d = frappe.new_doc("Currency")
			d.currency_name = code
			d.enabled = 1
			d.flags.ignore_permissions = True
			d.insert()
