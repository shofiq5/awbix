"""FFA/6 (AWB Space Allocation Answer, Cargo-IMP) outbound composer.

Builds an FFA message from a Shipment document:

    FFA/6
    {prefix}-{serial}{origin}{dest}/{desc}{pieces}{wt_code}{weight}[/{goods}][/{sph}...]
    {carrier_code}{flight_number}/{day}{month}/{dep}{arr}/{space_allocation_code}
    [SSR/{ssr_1}[/{ssr_2}]]
    [OSI/{osi_1}[/{osi_2}]]
    REF/{office_addr}[/{file_ref}]
    [SRI/{ref}[/{supp1}[/{supp2}]]]

Flight details (segment 3) repeat once per row in the flight_bookings child table.
"""

import frappe

from awbix.edx.engine.base_composer import BaseComposer
from awbix.edx.handlers.fwb import cargoimp

_num = cargoimp.num


class FFAComposer(BaseComposer):
	message_type = "FFA"
	version = "6"

	# ------------------------------------------------------------------ compose

	def compose(self, source_doc) -> str:
		d = source_doc
		self._assert_mandatory(d)
		lines = ["FFA/6", self._consignment_line(d)]
		lines += self._flight_lines(d)
		lines += self._text_segment(d, "SSR", "special_service_requests", "special_service_request")
		lines += self._text_segment(d, "OSI", "other_service_info", "other_service_information")
		ref = self._ref_line(d)
		if ref:
			lines.append(ref)
		lines += self._sri_lines(d)
		return cargoimp.join(lines)

	# ------------------------------------------------ mandatory-data enforcement

	def _assert_mandatory(self, d) -> None:
		missing = self._missing_mandatory(d)
		if missing:
			frappe.throw(
				"Cannot compose FFA/6 for {0}: missing mandatory data - {1}".format(
					d.get("name") or "shipment", "; ".join(missing)
				)
			)

	def _missing_mandatory(self, d) -> list[str]:
		m = []
		if not (d.get("airline_prefix") or "").strip():
			m.append("airline prefix (DE112)")
		if not (d.get("awb_serial_number") or "").strip():
			m.append("AWB serial number (DE113)")
		if not (d.get("origin") or "").strip():
			m.append("origin airport (DE313)")
		if not (d.get("destination") or "").strip():
			m.append("destination airport (DE313)")
		if not d.get("number_of_pieces"):
			m.append("number of pieces (DE701)")
		if not d.get("weight"):
			m.append("weight (DE600)")
		if not self._has_valid_flight(d):
			m.append("flight booking with departure/arrival airports and space allocation code")
		if not self._ref_line(d):
			m.append("booking reference — sender office address or participant id (REF)")
		return m

	def _has_valid_flight(self, d) -> bool:
		for row in d.get("flight_bookings") or []:
			code = (row.get("carrier_code") or row.get("carrier") or "").strip()
			number = (row.get("flight_number") or "").strip()
			dep = (row.get("departure_airport") or "").strip()
			arr = (row.get("arrival_airport") or "").strip()
			alloc = (row.get("space_allocation_code") or "").strip()
			if code and number and dep and arr and alloc:
				return True
		return False

	# -------------------------------------------------------- segment builders

	def _consignment_line(self, d) -> str:
		prefix = (d.get("airline_prefix") or "").strip()
		serial = (d.get("awb_serial_number") or "").strip()
		origin = (d.get("origin") or "").strip().upper()
		dest = (d.get("destination") or "").strip().upper()
		line = f"{prefix}-{serial}{origin}{dest}"

		pieces = d.get("number_of_pieces")
		weight = d.get("weight")
		if pieces and weight:
			desc = (d.get("shipment_description_code") or "T").strip() or "T"
			wt_code = (d.get("weight_code") or "K").strip()
			line += f"/{desc}{int(pieces)}{wt_code}{_num(weight)}"
			# For P-type (ULD), append total consignment pieces (DE701) with T prefix
			if desc == "P" and pieces:
				line += f"T{int(pieces)}"

		# Nature of goods (optional, section 2.5) — first G/C goods_details row
		goods = self._first_goods_description(d)
		if goods:
			line += f"/{goods}"

		# Special handling codes (optional, section 2.7) — up to 9
		for row in (d.get("special_handling") or [])[:9]:
			code = (row.get("special_handling_code") or "").strip()
			if code:
				line += f"/{code}"

		return line

	def _first_goods_description(self, d) -> str:
		for g in d.get("goods_details") or []:
			if (g.get("goods_data_identifier") or "") in ("G", "C"):
				desc = (g.get("description") or "").strip()
				if desc:
					return desc[:15]
		return ""

	def _flight_lines(self, d) -> list[str]:
		"""Section 3 — one line per flight booking that has the full set of FFA fields."""
		lines = []
		for row in d.get("flight_bookings") or []:
			code = (row.get("carrier_code") or row.get("carrier") or "").strip().upper()
			number = (row.get("flight_number") or "").strip()
			day = row.get("flight_day")
			month = (row.get("flight_month") or "").strip().upper()
			dep = (row.get("departure_airport") or "").strip().upper()
			arr = (row.get("arrival_airport") or "").strip().upper()
			alloc = (row.get("space_allocation_code") or "").strip().upper()
			if not (code and number and dep and arr and alloc):
				continue
			day_str = f"{int(day):02d}" if day else "00"
			lines.append(f"{code}{number}/{day_str}{month}/{dep}{arr}/{alloc}")
		return lines

	def _text_segment(self, d, code, table, field) -> list[str]:
		"""Build SSR or OSI segment — up to 2 continuation lines per FFA spec."""
		values = [(r.get(field) or "").strip() for r in (d.get(table) or [])]
		values = [v for v in values if v][:2]
		if not values:
			return []
		return [f"{code}/{values[0]}"] + ["/" + v for v in values[1:]]

	def _ref_line(self, d) -> str:
		"""Section 6 — booking reference (mandatory)."""
		office = (d.get("sender_office_address") or "").strip()
		file_ref = (d.get("sender_file_reference") or "").strip()
		pid = (d.get("sender_participant_id") or "").strip()
		pcode = (d.get("sender_participant_code") or "").strip()
		airport = (d.get("origin") or "").strip()
		if office:
			return f"REF/{office}" + (f"/{file_ref}" if file_ref else "")
		if pid or pcode or file_ref:
			line = f"REF//{file_ref}"
			if pid or pcode:
				line += f"/{pid}/{pcode}/{airport}"
			return line
		return ""

	def _sri_lines(self, d) -> list[str]:
		"""Section 7 — shipment reference information (optional, at most one)."""
		for r in (d.get("references") or [])[:1]:
			ref = (r.get("reference_number") or "").strip()
			supp1 = (r.get("supplementary_1") or "").strip()
			supp2 = (r.get("supplementary_2") or "").strip()
			if not (ref or supp1 or supp2):
				continue
			line = f"SRI/{ref}"
			if supp1 or supp2:
				line += f"/{supp1}"
			if supp2:
				line += f"/{supp2}"
			return [line]
		return []
