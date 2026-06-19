"""FHL/5 (Consolidation List, Cargo-IMP) outbound composer.

The inverse of FHLParser: given a master Shipment document, it queries all linked
House Airway Bills and emits a Cargo-IMP FHL/5 message — one MBI line followed by
one HBS block per house. verify() re-parses the output through the parser as a
self-check so a data error is caught before sending.
"""

import frappe

from awbix.edx.engine.base_composer import BaseComposer
from awbix.edx.handlers.fwb import cargoimp
from awbix.edx.handlers.fhl.fhl_parser import FHLParser


def _num(value) -> str:
	"""Render a numeric value without a trailing .0 (40.0 → '40', 0.36 → '0.36')."""
	f = float(value)
	return str(int(f)) if f.is_integer() else ("%g" % f)


class FHLComposer(BaseComposer):
	message_type = "FHL"
	version = "5"

	# ------------------------------------------------------------------ compose

	def compose(self, source_doc) -> str:
		lines = ["FHL/5", self._mbi_line(source_doc)]
		for hwb in self._houses_for(source_doc):
			lines += self._house_lines(hwb)
		return cargoimp.join(lines)

	def _mbi_line(self, doc) -> str:
		prefix = (doc.get("airline_prefix") or "").strip()
		serial = (doc.get("awb_serial_number") or "").strip()
		origin = (doc.get("origin") or "").strip().upper()
		dest = (doc.get("destination") or "").strip().upper()
		line = f"MBI/{prefix}-{serial}{origin}{dest}"
		pieces = doc.get("number_of_pieces")
		weight = doc.get("weight")
		if pieces and weight:
			wt_code = (doc.get("weight_code") or "K").strip()
			line += f"/T{int(pieces)}{wt_code}{_num(weight)}"
		return line

	def _houses_for(self, source_doc) -> list:
		name = source_doc.get("name") if isinstance(source_doc, dict) else source_doc.name
		if not name:
			return []
		names = frappe.get_all(
			"House Airway Bill",
			filters={"master_shipment": name, "docstatus": ["!=", 2]},
			pluck="name",
			order_by="creation asc",
		)
		return [frappe.get_doc("House Airway Bill", n) for n in names]

	def _house_lines(self, hwb) -> list[str]:
		lines = []
		lines.append(self._hbs_line(hwb))

		sph = self._sph_continuation(hwb)
		if sph:
			lines.append(sph)

		lines += self._txt_lines(hwb)
		lines += self._hts_lines(hwb)
		lines += self._oci_lines(hwb)

		shp = self._party_block(hwb, "shipper")
		if shp:
			lines += shp

		cne = self._party_block(hwb, "consignee")
		if cne:
			lines += cne

		cvd = self._cvd_line(hwb)
		if cvd:
			lines.append(cvd)

		return lines

	def _hbs_line(self, hwb) -> str:
		serial = (hwb.get("hwb_serial_number") or "").strip()
		origin = (hwb.get("hwb_origin") or "").strip().upper()
		dest = (hwb.get("hwb_destination") or "").strip().upper()
		pieces = hwb.get("number_of_pieces") or 0
		wt_code = (hwb.get("weight_code") or "K").strip()
		weight = hwb.get("weight") or 0
		slac = hwb.get("slac") or ""
		manifest = (hwb.get("manifest_description") or "").strip()[:15]
		return f"HBS/{serial}/{origin}{dest}/{int(pieces)}/{wt_code}{_num(weight)}/{slac}/{manifest}"

	def _sph_continuation(self, hwb) -> str:
		rows = hwb.get("special_handling") or []
		codes = []
		for row in rows:
			code = (row.get("special_handling_code") or "").strip()
			if code:
				codes.append(code)
		if not codes:
			return ""
		return "/" + "/".join(codes)

	def _txt_lines(self, hwb) -> list[str]:
		lines = []
		for row in (hwb.get("free_text") or []):
			text = (row.get("free_text") or "").strip()[:65]
			if text:
				lines.append(f"TXT/{text}")
		return lines

	def _hts_lines(self, hwb) -> list[str]:
		lines = []
		for row in (hwb.get("hs_codes") or []):
			code = (row.get("hs_code") or "").strip()
			if code:
				lines.append(f"HTS/{code}")
		return lines

	def _oci_lines(self, hwb) -> list[str]:
		rows = hwb.get("oci_customs") or []
		if not rows:
			return []

		def _oci_row(country_name, info_id, customs_id, supp):
			iso = self._resolve_country_code(country_name)
			return f"{iso}/{info_id or ''}/{customs_id or ''}/{supp or ''}"

		first = rows[0]
		header = "OCI/" + _oci_row(
			first.get("country"), first.get("information_identifier"),
			first.get("customs_info_identifier"), first.get("supplementary"),
		)
		lines = [header]
		for row in rows[1:]:
			cont = "/" + _oci_row(
				row.get("country"), row.get("information_identifier"),
				row.get("customs_info_identifier"), row.get("supplementary"),
			)
			lines.append(cont)
		return lines

	def _party_block(self, hwb, role: str) -> list[str]:
		"""role is 'shipper' or 'consignee'; emits SHP/CNE + NAM/ADR/LOC block."""
		prefix = role  # field prefix (shipper_name, consignee_name, …)
		name = (hwb.get(f"{prefix}_name") or "").strip()
		if not name:
			return []

		header = "SHP" if role == "shipper" else "CNE"
		lines = [header, f"NAM/{name}"]

		address = (hwb.get(f"{prefix}_address") or "").strip()
		if address:
			lines.append(f"ADR/{address}")

		place = (hwb.get(f"{prefix}_place") or "").strip()
		state = (hwb.get(f"{prefix}_state") or "").strip()
		country_name = hwb.get(f"{prefix}_country") or ""
		post_code = (hwb.get(f"{prefix}_post_code") or "").strip()
		contact_id = (hwb.get(f"{prefix}_contact_id") or "").strip()
		contact_number = (hwb.get(f"{prefix}_contact_number") or "").strip()

		if place:
			loc_line = f"LOC/{place}"
			if state:
				loc_line += f"/{state}"
			lines.append(loc_line)
			if country_name or post_code or contact_id:
				iso = self._resolve_country_code(country_name)
				cont = f"/{iso}/{post_code}"
				if contact_id:
					cont += f"/{contact_id}"
					if contact_number:
						cont += f"/{contact_number}"
				lines.append(cont)

		return lines

	def _cvd_line(self, hwb) -> str:
		currency = (hwb.get("currency") or "").strip()
		if not currency:
			return ""
		wt_pc = (hwb.get("wt_val_prepaid_collect") or "P").strip()
		oth_pc = (hwb.get("other_charges_prepaid_collect") or "P").strip()
		pc = wt_pc + oth_pc

		def _val(type_field, amount_field, nil_code):
			t = (hwb.get(type_field) or nil_code).strip()
			if t == "Value":
				return _num(hwb.get(amount_field) or 0)
			return nil_code

		carriage = _val("declared_value_carriage_type", "declared_value_carriage_amount", "NVD")
		customs = _val("declared_value_customs_type", "declared_value_customs_amount", "NCV")
		insurance = _val("insurance_type", "insurance_amount", "XXX")
		return f"CVD/{currency}/{pc}/{carriage}/{customs}/{insurance}"

	# ------------------------------------------------------------------- verify

	def verify(self, raw: str) -> list[dict]:
		parser = FHLParser()
		return parser.validate(parser.parse(raw))

	# ----------------------------------------------------------------- helpers

	def _resolve_country_code(self, country_name) -> str:
		"""Map Frappe Country name back to uppercase 2-letter ISO code."""
		if not country_name:
			return ""
		try:
			code = frappe.db.get_value("Country", country_name, "country_code")
			return (code or "").upper()[:2]
		except Exception:
			return ""
