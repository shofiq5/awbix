"""FFR/6 (AWB Space Allocation Request, Cargo-IMP) outbound composer.

Builds an FFR message from a Shipment document:

    FFR/6
    {prefix}-{serial}{origin}{dest}/{desc}{pieces}{wt_code}{weight}[{vol}|DG{dg}][T{total}]/{goods}[/{sph}...]
    {carrier_code}{flight_number}/{day}{month}/{dep}{arr}/{space_allocation_code}[/{allotment_id}]
    [ULD/{total_uld}/{uld_type}{uld_serial}{uld_owner}/{wt_code}{weight}...]
    [SSR/{ssr_1}[/{ssr_2}]]
    [OSI/{osi_1}[/{osi_2}]]
    REF/{office_addr}[/{file_ref}]
    [DIM/{wt_code}{weight}/{meas_unit}{L}-{W}-{H}/{pieces}...]
    [SRI/{ref}[/{supp1}[/{supp2}]]]

Nature of goods (section 2.7) is mandatory in FFR. Flight details (section 3) repeat once
per row in the flight_bookings child table that carries the full set of required fields.
ULD (section 4) and DIM (section 8) are built from goods_details rows of type 'U' and 'D'.
"""

import frappe

from awbix.edx.engine.base_composer import BaseComposer
from awbix.edx.handlers.fwb import cargoimp

_num = cargoimp.num


class FFRComposer(BaseComposer):
	message_type = "FFR"
	version = "6"

	# ------------------------------------------------------------------ compose

	def compose(self, source_doc) -> str:
		d = source_doc
		self._assert_mandatory(d)
		lines = ["FFR/6", self._consignment_line(d)]
		lines += self._flight_lines(d)
		lines += self._uld_lines(d)
		lines += self._text_segment(d, "SSR", "special_service_requests", "special_service_request")
		lines += self._text_segment(d, "OSI", "other_service_info", "other_service_information")
		ref = self._ref_line(d)
		if ref:
			lines.append(ref)
		lines += self._dim_lines(d)
		lines += self._sri_lines(d)
		return cargoimp.join(lines)

	# ------------------------------------------------ mandatory-data enforcement

	def _assert_mandatory(self, d) -> None:
		missing = self._missing_mandatory(d)
		if missing:
			frappe.throw(
				"Cannot compose FFR/6 for {0}: missing mandatory data - {1}".format(
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
		if not self._goods_description(d):
			m.append("nature of goods / manifest description (DE708)")
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
		"""Section 2 — consignment detail line."""
		prefix = (d.get("airline_prefix") or "").strip()
		serial = (d.get("awb_serial_number") or "").strip()
		origin = (d.get("origin") or "").strip().upper()
		dest = (d.get("destination") or "").strip().upper()
		line = f"{prefix}-{serial}{origin}{dest}"

		pieces = d.get("number_of_pieces")
		weight = d.get("weight")
		desc = (d.get("shipment_description_code") or "T").strip() or "T"
		wt_code = (d.get("weight_code") or "K").strip()
		line += f"/{desc}{int(pieces)}{wt_code}{_num(weight)}"

		# Volume (2.4) or density group (2.5) — mutually exclusive
		if d.get("density_indicator") and d.get("density_group"):
			line += f"DG{int(d.get('density_group'))}"
		elif d.get("volume_code") and d.get("volume_amount"):
			line += f"{d.get('volume_code')}{_num(d.get('volume_amount'))}"

		# Total consignment pieces for P-type ULD shipments (2.6)
		if desc == "P" and pieces:
			line += f"T{int(pieces)}"

		# Nature of goods — mandatory in FFR (2.7)
		line += f"/{self._goods_description(d)}"

		# Special handling codes — up to 9 (2.9)
		for row in (d.get("special_handling") or [])[:9]:
			code = (row.get("special_handling_code") or "").strip()
			if code:
				line += f"/{code}"

		return line

	def _goods_description(self, d) -> str:
		"""First G or C goods_details row description, or empty string."""
		for g in d.get("goods_details") or []:
			if (g.get("goods_data_identifier") or "") in ("G", "C"):
				desc = (g.get("description") or "").strip()
				if desc:
					return desc[:15]
		return ""

	def _flight_lines(self, d) -> list[str]:
		"""Section 3 — one line per flight booking that has the full set of FFR fields."""
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
			flight_line = f"{code}{number}/{day_str}{month}/{dep}{arr}/{alloc}"
			# Allotment ID (3.6) — mandatory when code is CA
			allotment = (row.get("allotment_id") or "").strip()
			if allotment:
				flight_line += f"/{allotment}"
			lines.append(flight_line)
		return lines

	def _uld_lines(self, d) -> list[str]:
		"""Section 4 — ULD description from goods_details rows with type 'U'."""
		uld_rows = [g for g in (d.get("goods_details") or []) if (g.get("goods_data_identifier") or "") == "U"]
		if not uld_rows:
			return []
		total = len(uld_rows)
		parts = []
		for g in uld_rows:
			uld_type = (g.get("uld_type") or "").strip().upper()
			uld_serial = (g.get("uld_serial") or "").strip().upper()
			uld_owner = (g.get("uld_owner") or "").strip().upper()
			wt_code = (g.get("dim_weight_code") or "K").strip()
			weight = g.get("dim_weight")
			if not (uld_type and weight):
				continue
			uld_id = f"{uld_type}{uld_serial}{uld_owner}"
			parts.append(f"/{uld_id}/{wt_code}{_num(weight)}")
		if not parts:
			return []
		# First line: ULD/{total} + first ULD; subsequent ULDs are continuation lines
		first_line = f"ULD/{total}{parts[0]}"
		return [first_line] + parts[1:]

	def _text_segment(self, d, code, table, field) -> list[str]:
		"""Build SSR or OSI segment — up to 2 continuation lines per FFR spec."""
		values = [(r.get(field) or "").strip() for r in (d.get(table) or [])]
		values = [v for v in values if v][:2]
		if not values:
			return []
		return [f"{code}/{values[0]}"] + ["/" + v for v in values[1:]]

	def _ref_line(self, d) -> str:
		"""Section 7 — booking reference (mandatory)."""
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

	def _dim_lines(self, d) -> list[str]:
		"""Section 8 — dimension information from goods_details rows with type 'D'."""
		dim_rows = [g for g in (d.get("goods_details") or []) if (g.get("goods_data_identifier") or "") == "D"]
		if not dim_rows:
			return []
		parts = []
		for g in dim_rows:
			wt_code = (g.get("dim_weight_code") or "K").strip()
			weight = g.get("dim_weight")
			meas = (g.get("measurement_unit") or "").strip().upper()
			length = g.get("dim_length")
			width = g.get("dim_width")
			height = g.get("dim_height")
			pieces = g.get("dim_pieces")
			if not (weight and meas and length and width and height and pieces):
				continue
			parts.append(f"/{wt_code}{_num(weight)}/{meas}{int(length)}-{int(width)}-{int(height)}/{int(pieces)}")
		if not parts:
			return []
		return [f"DIM{parts[0]}"] + parts[1:]

	def _sri_lines(self, d) -> list[str]:
		"""Section 13 — shipment reference information (optional, at most one)."""
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
