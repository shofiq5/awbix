"""FFA/6 (AWB Space Allocation Answer, Cargo-IMP) inbound parser.

Handles all FFA versions (detection_pattern covers FFA/2 through FFA/6). ``parse()``
is pure (no DB) and returns a normalised dict; ``process()`` updates the matching
Shipment's flight_bookings child table with the airline's space allocation answer.

Segments handled: message id, AWB consignment detail (pieces/weight/goods/SHC),
flight detail lines (carrier/flight/day/month/dep/arr/space_code), SSR, OSI,
REF booking reference, SRI shipment reference information.
"""

import re

import frappe

from awbix.edx.engine.base_parser import BaseParser
from awbix.edx.handlers.fwb import cargoimp

# prefix-serial + origin + dest, optional rest after /
_AWB_RE = re.compile(r"^(\d{1,3})-(\d{7,8})([A-Z]{3})([A-Z]{3})(?:/(.*))?$")

# quantity detail: T|P + pieces + K|L + weight, optional total pieces for P-type (section 2.4)
_CONSIGNMENT_RE = re.compile(
	r"^(?P<desc>[TP])(?P<pieces>\d{1,4})(?P<wt_code>[KL])(?P<weight>\d+(?:\.\d+)?)"
	r"(?:(?P<total_desc>T)(?P<total_pieces>\d{1,4}))?"
)

# bare flight lines (no leading segment code): CC999X/01JAN/DEPAAR/KK
_FLIGHT_RE = re.compile(
	r"^([A-Z0-9]{2})(\d{3,4}[A-Z]?)/(\d{2})([A-Z]{3})/([A-Z]{3})([A-Z]{3})/([A-Z]{2})$"
)

# exactly 3 uppercase alpha — distinguishes SHC codes from goods descriptions
_SHC_RE = re.compile(r"^[A-Z]{3}$")

_VALID_ALLOC = {"NN", "NA", "SS", "CA", "XX", "HK", "HL", "HN", "KK", "UU", "UN", "LL"}


class FFAParser(BaseParser):
	message_type = "FFA"
	version = "6"

	# ------------------------------------------------------------------ parse

	def parse(self, raw: str) -> dict:
		lines = cargoimp.normalize(raw)
		message_id = lines[0] if lines else None
		awb_line = lines[1] if len(lines) > 1 else None

		flights, ssr_lines, osi_lines, ref_raw, sri_raw = [], [], [], None, None
		last_block = None  # tracks "ssr" | "osi" for continuation lines

		for ln in lines[2:]:
			if _FLIGHT_RE.match(ln):
				flights.append(ln)
				last_block = None
			elif ln.upper().startswith("SSR/"):
				ssr_lines.append(ln[4:])
				last_block = "ssr"
			elif ln.upper().startswith("OSI/"):
				osi_lines.append(ln[4:])
				last_block = "osi"
			elif ln.upper().startswith("REF/"):
				ref_raw = ln[4:]
				last_block = None
			elif ln.upper().startswith("SRI/"):
				sri_raw = ln[4:]
				last_block = None
			elif ln.startswith("/") and last_block == "ssr":
				ssr_lines.append(ln[1:])
			elif ln.startswith("/") and last_block == "osi":
				osi_lines.append(ln[1:])

		version_str = message_id.split("/", 1)[1].strip() if message_id and "/" in message_id else None

		return {
			"message": {
				"type": self.message_type,
				"version": version_str or self.version,
				"id": message_id,
			},
			"awb": self._parse_awb(awb_line),
			"flights": [self._parse_flight(f) for f in flights],
			"ssr": [s.strip() for s in ssr_lines if s.strip()],
			"osi": [o.strip() for o in osi_lines if o.strip()],
			"booking_reference": self._parse_ref(ref_raw),
			"references": self._parse_sri(sri_raw),
		}

	# ----------------------------------------------------------- segment parsers

	def _parse_awb(self, line):
		if not line:
			return {}
		m = _AWB_RE.match(line.strip())
		if not m:
			return {"raw": line}
		prefix, serial, origin, dest, rest = m.groups()
		result = {
			"airline_prefix": prefix,
			"awb_serial_number": serial,
			"awb_number": f"{prefix}-{serial}",
			"origin": origin,
			"destination": dest,
		}
		if rest:
			cm = _CONSIGNMENT_RE.match(rest)
			if cm:
				result["shipment_description_code"] = cm.group("desc")
				result["number_of_pieces"] = int(cm.group("pieces"))
				result["weight_code"] = cm.group("wt_code")
				result["weight"] = float(cm.group("weight"))
				if cm.group("total_pieces"):
					result["total_pieces"] = int(cm.group("total_pieces"))
				sph, goods_set = [], False
				for tok in rest[cm.end():].split("/"):
					tok = tok.strip()
					if not tok:
						continue
					if _SHC_RE.match(tok):
						sph.append(tok)
					elif not goods_set:
						result["goods_description"] = tok[:15]
						goods_set = True
				result["special_handling_codes"] = sph[:9]
		return result

	def _parse_flight(self, line):
		m = _FLIGHT_RE.match(line.strip())
		if not m:
			return {"raw": line}
		carrier, flt_num, day, month, dep, arr, code = m.groups()
		return {
			"carrier": carrier,
			"flight_number": flt_num,
			"day": int(day),
			"month": month,
			"departure_airport": dep,
			"arrival_airport": arr,
			"space_allocation_code": code,
		}

	def _parse_ref(self, raw):
		"""Section 6 — two formats: office address (6.3) or participant id (6.6)."""
		if not raw:
			return {}
		if raw.startswith("/"):
			# Format B: REF//{file_ref}[/{pid}/{pcode}/{airport}]
			parts = raw[1:].split("/")
			return {
				"file_reference": parts[0].strip()[:15] if parts else "",
				"participant_id": parts[1].strip()[:3] if len(parts) > 1 else "",
				"participant_code": parts[2].strip()[:17] if len(parts) > 2 else "",
				"airport": parts[3].strip()[:3] if len(parts) > 3 else "",
			}
		# Format A: REF/{office_addr}[/{file_ref}]
		parts = raw.split("/", 1)
		return {
			"office_address": parts[0].strip()[:8],
			"file_reference": parts[1].strip()[:15] if len(parts) > 1 else "",
		}

	def _parse_sri(self, raw):
		"""Section 7 — shipment reference information."""
		if not raw:
			return []
		parts = raw.split("/")
		return [
			{
				"reference_number": parts[0].strip()[:14] if parts else "",
				"supplementary_1": parts[1].strip()[:12] if len(parts) > 1 else "",
				"supplementary_2": parts[2].strip()[:12] if len(parts) > 2 else "",
			}
		]

	# ---------------------------------------------------------------- business key

	def business_key(self, data):
		return (data.get("awb") or {}).get("awb_number")

	# ------------------------------------------------------------------ validate

	def validate(self, data):
		issues = []
		awb = data.get("awb") or {}

		if not awb.get("awb_number"):
			return [
				{
					"level": "Error",
					"code": "AWB_LINE",
					"field": "awb",
					"message": "Could not parse the AWB consignment detail line",
				}
			]

		serial = (awb.get("awb_serial_number") or "").strip()
		if not (serial.isdigit() and len(serial) == 8):
			issues.append(
				{
					"level": "Error",
					"code": "AWB_SERIAL_LENGTH",
					"field": "awb_serial_number",
					"message": "AWB serial number must be exactly 8 digits",
				}
			)
		elif int(serial[:7]) % 7 != int(serial[7]):
			issues.append(
				{
					"level": "Warning",
					"code": "AWB_CHECKDIGIT",
					"field": "awb_serial_number",
					"message": f"Invalid AWB check digit (expected {int(serial[:7]) % 7})",
				}
			)

		if awb.get("origin") and awb.get("origin") == awb.get("destination"):
			issues.append(
				{
					"level": "Warning",
					"code": "AWB_ROUTE",
					"field": "destination",
					"message": "AWB origin and destination are the same airport",
				}
			)

		pieces = awb.get("number_of_pieces")
		if pieces is not None and pieces == 0:
			issues.append(
				{
					"level": "Info",
					"code": "ZERO_PIECES",
					"field": "number_of_pieces",
					"message": "Number of pieces is zero (FFA21 permits this)",
				}
			)

		if not data.get("flights"):
			issues.append(
				{
					"level": "Error",
					"code": "NO_FLIGHTS",
					"field": "flights",
					"message": "FFA message contains no flight detail lines",
				}
			)

		for i, flt in enumerate(data.get("flights") or []):
			alloc = (flt.get("space_allocation_code") or "").upper()
			if alloc not in _VALID_ALLOC:
				issues.append(
					{
						"level": "Error",
						"code": "ALLOC_CODE",
						"field": f"flights.{i}.space_allocation_code",
						"message": f"Unknown space allocation code '{alloc}'",
					}
				)
			dep = flt.get("departure_airport")
			if dep and dep == flt.get("arrival_airport"):
				issues.append(
					{
						"level": "Warning",
						"code": "FLIGHT_ROUTE",
						"field": f"flights.{i}.arrival_airport",
						"message": "Flight departure and arrival airports are identical",
					}
				)

		ref = data.get("booking_reference") or {}
		if not (ref.get("office_address") or ref.get("participant_id") or ref.get("file_reference")):
			issues.append(
				{
					"level": "Error",
					"code": "REF_MISSING",
					"field": "booking_reference",
					"message": "REF line is mandatory in an FFA message",
				}
			)

		return issues

	# ------------------------------------------------------------------ process

	def process(self, data, message_in) -> str:
		"""Update an existing Shipment's flight_bookings with the space allocation answers.

		Creates airport/airline stubs on the fly. Does not replace existing flight rows —
		matches by carrier + flight number + day (+ month if present on the existing row)
		then patches space_allocation_code and fills dep/arr airports if absent.
		"""
		awb = data["awb"]
		name = awb["awb_number"]

		if not frappe.db.exists("Shipment", name):
			frappe.throw(f"FFA received for unknown AWB {name}; ensure the FWB is processed first")

		doc = frappe.get_doc("Shipment", name)

		if awb.get("origin"):
			self._ensure("Airport", {"iata_code": awb["origin"]}, awb["origin"])
		if awb.get("destination"):
			self._ensure("Airport", {"iata_code": awb["destination"]}, awb["destination"])

		for flt in data.get("flights") or []:
			dep, arr = flt.get("departure_airport"), flt.get("arrival_airport")
			if dep:
				self._ensure("Airport", {"iata_code": dep}, dep)
			if arr:
				self._ensure("Airport", {"iata_code": arr}, arr)
			carrier = self._ensure_airline_by_code(flt["carrier"])
			row = self._find_flight_row(doc.flight_bookings, flt)
			if row:
				row.space_allocation_code = flt["space_allocation_code"]
				if not row.departure_airport and dep:
					row.departure_airport = dep
				if not row.arrival_airport and arr:
					row.arrival_airport = arr
			else:
				doc.append(
					"flight_bookings",
					{
						"carrier": carrier,
						"flight_number": flt["flight_number"][:5],
						"flight_day": str(flt["day"]).zfill(2),
						"flight_month": flt["month"],
						"departure_airport": dep or None,
						"arrival_airport": arr or None,
						"space_allocation_code": flt["space_allocation_code"],
					},
				)

		# SSR — append new entries; don't duplicate (FFA23: reply to FFR SSR)
		existing_ssr = {r.special_service_request for r in doc.special_service_requests}
		for text in data.get("ssr") or []:
			if text[:65] not in existing_ssr:
				doc.append("special_service_requests", {"special_service_request": text[:65]})

		# OSI — same append-not-replace logic
		existing_osi = {r.other_service_information for r in doc.other_service_info}
		for text in data.get("osi") or []:
			if text[:65] not in existing_osi:
				doc.append("other_service_info", {"other_service_information": text[:65]})

		# REF → sender reference header fields
		ref = data.get("booking_reference") or {}
		if ref.get("office_address"):
			doc.sender_office_address = ref["office_address"][:8]
		if ref.get("file_reference"):
			doc.sender_file_reference = ref["file_reference"][:15]
		if ref.get("participant_id"):
			doc.sender_participant_id = ref["participant_id"][:3]
		if ref.get("participant_code"):
			doc.sender_participant_code = ref["participant_code"][:17]

		# SRI → references child table (merge, not replace)
		for r in data.get("references") or []:
			ref_num = (r.get("reference_number") or "").strip()
			if ref_num:
				doc.append(
					"references",
					{
						"reference_number": ref_num[:14],
						"supplementary_1": (r.get("supplementary_1") or "")[:12],
						"supplementary_2": (r.get("supplementary_2") or "")[:12],
					},
				)

		doc.flags.ignore_permissions = True
		doc.save()
		return doc.name

	# ------------------------------------------------------------------- helpers

	def _find_flight_row(self, booking_rows, flt):
		"""Return the matching flight_bookings child row or None.

		Matches on carrier_code + flight_number + day. Month is also checked when the
		existing row has one — rows created by FWB (which omits month) are matched on
		carrier + flight + day alone so FFA can still update them.
		"""
		for row in booking_rows:
			try:
				stored_day = int(row.flight_day or 0)
			except (TypeError, ValueError):
				stored_day = -1
			stored_month = (row.flight_month or "").upper()
			month_ok = not stored_month or stored_month == flt["month"].upper()
			if (
				(row.carrier_code or "").upper() == flt["carrier"].upper()
				and (row.flight_number or "") == flt["flight_number"]
				and stored_day == flt["day"]
				and month_ok
			):
				return row
		return None

	def _ensure(self, doctype, values, name):
		if name and not frappe.db.exists(doctype, name):
			d = frappe.new_doc(doctype)
			d.update(values)
			d.flags.ignore_permissions = True
			d.insert()

	def _ensure_airline_by_code(self, carrier_code):
		"""Resolve Airline docname from 2-char code, creating a stub if needed."""
		code = (carrier_code or "").strip().upper()
		if not code:
			return None
		existing = frappe.db.get_value("Airline", {"carrier_code": code}, "name")
		if existing:
			return existing
		if frappe.db.exists("Airline", code):
			return code
		d = frappe.new_doc("Airline")
		d.airline_prefix = code
		d.carrier_code = code
		d.flags.ignore_permissions = True
		d.insert()
		return code
