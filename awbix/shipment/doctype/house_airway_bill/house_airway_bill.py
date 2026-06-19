import re

import frappe
from frappe.model.document import Document

_SERIAL_RE = re.compile(r"^[A-Za-z0-9]{1,12}$")
_CONTACT_ID_VALID = {"FX", "TE", "TL"}

# OCI identifiers that must immediately follow an RA or KC issuer row.
_OCI_REQUIRES_ISSUER = {"ED", "SM", "SN", "SD"}
# Only one SS row is permitted per HWB (FHL2 / OCI rules table).
_OCI_SS_MAX_ONE = "SS"


class HouseAirwayBill(Document):
	def validate(self):
		self.validate_hwb_serial_number()
		self.validate_hwb_route()
		self.validate_pieces_and_weight()
		self.validate_unique_serial_per_master()
		self.validate_goods_row_limits()
		self.validate_hs_code_lengths()
		self.validate_parties()
		self.validate_contact_identifiers()
		self.validate_oci_rows()
		self.validate_charge_declarations()
		self.set_hwb_number()

	# ------------------------------------------------------------------
	# Phase 2 — core HBS
	# ------------------------------------------------------------------

	def set_hwb_number(self):
		master_awb = self.master_awb_number
		if not master_awb and self.master_shipment:
			master_awb = frappe.db.get_value("Shipment", self.master_shipment, "awb_number")
		if master_awb and self.hwb_serial_number:
			self.hwb_number = f"{master_awb} / {self.hwb_serial_number}"

	def validate_hwb_serial_number(self):
		serial = (self.hwb_serial_number or "").strip()
		if not serial:
			frappe.throw("HWB Serial Number (DE119) is required.")
		if not _SERIAL_RE.match(serial):
			frappe.throw(
				f"HWB Serial Number (DE119) must be 1–12 alphanumeric characters (A-Z, 0-9). "
				f"Got: {serial!r}"
			)

	def validate_hwb_route(self):
		if self.hwb_origin and self.hwb_destination and self.hwb_origin == self.hwb_destination:
			frappe.throw("HWB Origin and Destination cannot be the same airport.")

	def validate_pieces_and_weight(self):
		if (self.number_of_pieces or 0) <= 0:
			frappe.throw("Number of Pieces (DE701) must be greater than zero.")
		if (self.weight or 0.0) <= 0.0:
			frappe.throw("Weight (DE600) must be greater than zero.")

	def validate_unique_serial_per_master(self):
		if not self.master_shipment or not self.hwb_serial_number:
			return
		duplicate = frappe.db.get_value(
			"House Airway Bill",
			{
				"master_shipment": self.master_shipment,
				"hwb_serial_number": self.hwb_serial_number,
				"name": ("!=", self.name or ""),
				"docstatus": ("!=", 2),
			},
			"name",
		)
		if duplicate:
			frappe.throw(
				f"HWB Serial Number {self.hwb_serial_number!r} already exists under "
				f"Master Shipment {self.master_shipment} ({duplicate})."
			)

	# ------------------------------------------------------------------
	# Phase 3 — goods children (SPH / TXT / HTS)
	# ------------------------------------------------------------------

	def validate_goods_row_limits(self):
		limits = {
			"special_handling": ("Special Handling (SPH)", 9),
			"free_text": ("Free Text (TXT)", 9),
			"hs_codes": ("Harmonised Tariff (HTS)", 9),
		}
		for fieldname, (label, max_rows) in limits.items():
			rows = self.get(fieldname) or []
			if len(rows) > max_rows:
				frappe.throw(
					f"{label} may not exceed {max_rows} rows (FHL rule). "
					f"Found {len(rows)} rows."
				)

	def validate_hs_code_lengths(self):
		for row in self.get("hs_codes") or []:
			code = (row.hs_code or "").strip()
			if not code:
				frappe.throw(f"HS Code row #{row.idx}: HS Code is required.")
			if len(code) < 6 or len(code) > 18:
				frappe.throw(
					f"HS Code row #{row.idx}: code must be 6–18 characters (DE900). Got {len(code)}."
				)

	# ------------------------------------------------------------------
	# Phase 4 — parties (SHP / CNE) — FHL24, FHL22/26
	# ------------------------------------------------------------------

	def validate_parties(self):
		has_shipper = bool(self.shipper)
		has_consignee = bool(self.consignee)
		if has_shipper and not has_consignee:
			frappe.throw("Consignee (CNE) is required when Shipper (SHP) is present (FHL24).")
		if has_consignee and not has_shipper:
			frappe.throw("Shipper (SHP) is required when Consignee (CNE) is present (FHL24).")

	def validate_contact_identifiers(self):
		for role, id_field, num_field in [
			("Shipper", "shipper_contact_id", "shipper_contact_number"),
			("Consignee", "consignee_contact_id", "consignee_contact_number"),
		]:
			cid = (getattr(self, id_field) or "").strip().upper()
			cnum = (getattr(self, num_field) or "").strip()
			if cid and cid not in _CONTACT_ID_VALID:
				frappe.throw(
					f"{role} Contact Identifier (DE122) must be one of "
					f"{', '.join(sorted(_CONTACT_ID_VALID))}. Got: {cid!r}"
				)
			if cnum and not cid:
				frappe.throw(
					f"{role} Contact Number (DE123) is set but Contact Identifier (DE122) is missing."
				)

	# ------------------------------------------------------------------
	# Phase 5 — OCI composition (FHL2/FHL30) + CVD amounts
	# ------------------------------------------------------------------

	def validate_oci_rows(self):
		rows = self.get("oci_customs") or []
		ss_count = 0
		last_was_issuer = False

		for row in rows:
			country = row.country
			info_id = row.information_identifier
			cust_id = (row.customs_info_identifier or "").strip().upper()

			# FHL30: at least one of the three qualifier fields must be present.
			if not country and not info_id and not cust_id:
				frappe.throw(
					f"OCI row #{row.idx}: at least one of Country, Info Identifier, or "
					f"Customs Info Identifier is required (FHL30)."
				)

			if cust_id == _OCI_SS_MAX_ONE:
				ss_count += 1
				if ss_count > 1:
					frappe.throw(
						"OCI: only one SS (Security Status) row is permitted per HWB (FHL2)."
					)

			if cust_id in _OCI_REQUIRES_ISSUER and not last_was_issuer:
				frappe.msgprint(
					f"OCI row #{row.idx}: identifier {cust_id!r} should follow an RA or KC "
					f"issuer row (FHL2). Please verify the OCI row order.",
					indicator="orange",
					title="OCI Row Order Warning",
				)

			last_was_issuer = cust_id in ("RA", "KC")

	def validate_charge_declarations(self):
		pairs = [
			("declared_value_carriage_type", "declared_value_carriage_amount", "NVD", "DE510"),
			("declared_value_customs_type", "declared_value_customs_amount", "NCV", "DE509"),
			("insurance_type", "insurance_amount", "XXX", "DE508"),
		]
		for type_field, amount_field, nil_code, de in pairs:
			vtype = (getattr(self, type_field) or nil_code).strip()
			amount = getattr(self, amount_field) or 0.0
			if vtype == nil_code and amount:
				label = type_field.replace("_", " ").title()
				frappe.throw(
					f"{label} ({de}): amount must be empty when declaration type is {nil_code!r}."
				)
			if vtype == "Value" and not amount:
				label = type_field.replace("_", " ").title()
				frappe.throw(
					f"{label} ({de}): amount is required when declaration type is 'Value'."
				)
