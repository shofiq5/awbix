"""FHL/5 (Consolidation List, Cargo-IMP) inbound parser.

One FHL message = one MBI (master AWB) header + N HBS (house waybill) blocks, each
block optionally carrying SPH / TXT / HTS / OCI / SHP / CNE / CVD sub-groups.

parse() is pure (no DB). process() fans out: it ensures the master Shipment exists,
then creates or updates one House Airway Bill per HBS block, all linked to that master.

The EDX Delivery ledger records the master AWB number as the representative target_name
(1-message→N-docs fan-out; per-house idempotency is keyed on
(master_shipment, hwb_serial_number) — see plan §6).
"""

import re

import frappe

from awbix.edx.engine.base_parser import BaseParser
from awbix.edx.handlers.fwb import cargoimp

# MBI/prefix-serial ORIGDEST [/T pieces WTCODE weight]
_MBI_RE = re.compile(
	r"^MBI/(\d{1,3})-(\d{8})([A-Z]{3})([A-Z]{3})(?:/T(\d+)([A-Z])([0-9.]+))?$"
)

# HBS/serial/ORIGDEST/pieces/WTCODEweight/slac/manifest_desc
_HBS_RE = re.compile(
	r"^HBS/([^/]+)/([A-Z]{3})([A-Z]{3})/(\d+)/([A-Z])([0-9.]+)/(\d*)/(.*)$"
)

_SERIAL_RE = re.compile(r"^[A-Za-z0-9]{1,12}$")


class FHLParser(BaseParser):
	message_type = "FHL"
	version = "5"

	# ------------------------------------------------------------------ parse

	def parse(self, raw: str) -> dict:
		t = cargoimp.tokenize(raw)
		return {
			"message": {"type": self.message_type, "version": self.version, "id": t.get("message_id")},
			"master": self._parse_master(t.get("awb_line")),
			"houses": [self._parse_house(g) for g in self._group_houses(t["segments"])],
			"segments_seen": [s["code"] for s in t["segments"] if s["code"]],
		}

	def _parse_master(self, line):
		if not line:
			return {}
		m = _MBI_RE.match((line or "").strip())
		if not m:
			return {"raw_detail": line}
		prefix, serial, origin, destination, pieces, weight_code, weight = m.groups()
		return {
			"airline_prefix": prefix,
			"awb_serial_number": serial,
			"awb_number": f"{prefix}-{serial}",
			"origin": origin,
			"destination": destination,
			"pieces": int(pieces) if pieces else None,
			"weight_code": weight_code,
			"weight": float(weight) if weight else None,
			"raw_detail": line,
		}

	def _group_houses(self, segments):
		"""Split the segment list into per-house groups; each HBS line starts a new group."""
		groups = []
		current = None
		for seg in segments:
			if seg["code"] == "HBS":
				current = [seg]
				groups.append(current)
			elif current is not None:
				current.append(seg)
		return groups

	def _parse_house(self, group):
		hbs = group[0]
		summary = self._parse_hbs(hbs)
		summary["special_handling"] = self._parse_sph(hbs)
		summary["free_text"] = self._parse_txt(group)
		summary["hs_codes"] = self._parse_hts(group)
		summary["oci"] = self._parse_oci(group)
		summary["shipper"] = self._parse_party(group, "SHP")
		summary["consignee"] = self._parse_party(group, "CNE")
		summary["charge_declarations"] = self._parse_cvd(group)
		return summary

	def _parse_hbs(self, seg):
		line = seg["lines"][0] if seg["lines"] else ""
		m = _HBS_RE.match(line.strip())
		if not m:
			return {"raw_detail": line}
		serial, origin, destination, pieces, weight_code, weight, slac, manifest = m.groups()
		return {
			"hwb_serial_number": serial,
			"hwb_origin": origin,
			"hwb_destination": destination,
			"number_of_pieces": int(pieces),
			"weight_code": weight_code,
			"weight": float(weight),
			"slac": int(slac) if slac else None,
			"manifest_description": manifest[:15],
		}

	def _parse_sph(self, hbs_seg):
		"""SPH codes appear as /CODE/CODE continuation lines on the HBS segment."""
		codes = []
		for text in cargoimp.continuation_text(hbs_seg):
			for code in text.split("/"):
				code = code.strip()
				if code:
					codes.append({"code": code})
		return codes

	def _parse_txt(self, group):
		rows = []
		for seg in group:
			if seg["code"] == "TXT":
				line = seg["lines"][0]
				text = line[4:] if line.startswith("TXT/") else ""
				rows.append({"free_text": text[:65]})
		return rows

	def _parse_hts(self, group):
		rows = []
		for seg in group:
			if seg["code"] == "HTS":
				line = seg["lines"][0]
				code = line[4:].strip() if line.startswith("HTS/") else ""
				if code:
					rows.append({"hs_code": code})
		return rows

	def _parse_oci(self, group):
		"""Parse OCI segment: header row + all /continuation lines become individual rows."""
		rows = []
		for seg in group:
			if seg["code"] != "OCI":
				continue
			# Header line: OCI/country/info_id/customs_id/supplementary
			header = seg["lines"][0]
			parts = header.split("/")
			rows.append({
				"country": parts[1].strip() if len(parts) > 1 else "",
				"information_identifier": parts[2].strip() if len(parts) > 2 else "",
				"customs_info_identifier": parts[3].strip() if len(parts) > 3 else "",
				"supplementary": parts[4].strip() if len(parts) > 4 else "",
			})
			# Continuation lines: /country/info_id/customs_id/supplementary
			for ln in seg["lines"][1:]:
				if not ln.startswith("/"):
					continue
				content = ln[1:]  # strip leading /
				cparts = content.split("/")
				rows.append({
					"country": cparts[0].strip() if len(cparts) > 0 else "",
					"information_identifier": cparts[1].strip() if len(cparts) > 1 else "",
					"customs_info_identifier": cparts[2].strip() if len(cparts) > 2 else "",
					"supplementary": cparts[3].strip() if len(cparts) > 3 else "",
				})
		return rows

	def _parse_party(self, group, code):
		"""Parse SHP or CNE block: find the header then collect NAM/ADR/LOC until the next party or CVD."""
		start = None
		for i, seg in enumerate(group):
			if seg["code"] == code:
				start = i
				break
		if start is None:
			return {}

		party_segs = []
		for seg in group[start + 1:]:
			if seg["code"] in ("SHP", "CNE", "CVD", "HBS"):
				break
			if seg["code"] in ("NAM", "ADR", "LOC"):
				party_segs.append(seg)

		result = {}
		for seg in party_segs:
			if seg["code"] == "NAM":
				line = seg["lines"][0]
				result["name"] = line[4:].strip() if line.startswith("NAM/") else ""
			elif seg["code"] == "ADR":
				line = seg["lines"][0]
				result["address"] = line[4:].strip() if line.startswith("ADR/") else ""
			elif seg["code"] == "LOC":
				line = seg["lines"][0]
				# LOC/place[/state]
				loc_content = line[4:] if line.startswith("LOC/") else ""
				loc_parts = loc_content.split("/")
				result["place"] = loc_parts[0].strip() if loc_parts else ""
				result["state"] = loc_parts[1].strip() if len(loc_parts) > 1 else ""
				# Continuation: /country/post_code[/contact_id/contact_number]
				for cont in cargoimp.continuation_text(seg):
					cparts = cont.split("/")
					result["country"] = cparts[0].strip() if len(cparts) > 0 else ""
					result["post_code"] = cparts[1].strip() if len(cparts) > 1 else ""
					if len(cparts) > 2:
						result["contact_id"] = cparts[2].strip()
					if len(cparts) > 3:
						result["contact_number"] = cparts[3].strip()
		return result

	def _parse_cvd(self, group):
		seg = next((s for s in group if s["code"] == "CVD"), None)
		if not seg:
			return {}
		line = seg["lines"][0]
		parts = line.split("/")
		# CVD/currency/wt_pc+oth_pc/carriage/customs/insurance
		currency = parts[1].strip() if len(parts) > 1 else ""
		pc = parts[2].strip() if len(parts) > 2 else "PP"
		wt_val_pc = pc[0] if pc else "P"
		other_pc = pc[1] if len(pc) > 1 else "P"

		def _parse_value(raw):
			r = (raw or "").strip()
			if r in ("NVD", "NCV", "XXX"):
				return r, None
			try:
				return "Value", float(r)
			except (ValueError, TypeError):
				return r, None

		carriage_type, carriage_amt = _parse_value(parts[3] if len(parts) > 3 else "NVD")
		customs_type, customs_amt = _parse_value(parts[4] if len(parts) > 4 else "NCV")
		insurance_type, insurance_amt = _parse_value(parts[5] if len(parts) > 5 else "XXX")

		return {
			"currency": currency,
			"wt_val_prepaid_collect": wt_val_pc,
			"other_charges_prepaid_collect": other_pc,
			"declared_value_carriage_type": carriage_type,
			"declared_value_carriage_amount": carriage_amt,
			"declared_value_customs_type": customs_type,
			"declared_value_customs_amount": customs_amt,
			"insurance_type": insurance_type,
			"insurance_amount": insurance_amt,
		}

	# ---------------------------------------------------------- business_key

	def business_key(self, data):
		return (data.get("master") or {}).get("awb_number")

	# ---------------------------------------------------------------- validate

	def validate(self, data):
		issues = []
		master = data.get("master") or {}

		if not master.get("awb_number"):
			return [{
				"level": "Error", "code": "MBI", "field": "master",
				"message": "Could not parse the MBI (master AWB) line",
			}]

		serial = (master.get("awb_serial_number") or "").strip()
		if not (serial.isdigit() and len(serial) == 8):
			issues.append({
				"level": "Error", "code": "AWB_SERIAL", "field": "awb_serial_number",
				"message": "Master AWB serial number must be exactly 8 digits",
			})
		elif int(serial[:7]) % 7 != int(serial[7]):
			issues.append({
				"level": "Error", "code": "AWB_CHECKDIGIT", "field": "awb_serial_number",
				"message": f"Invalid master AWB check digit (expected {int(serial[:7]) % 7})",
			})

		houses = data.get("houses") or []
		if not houses:
			issues.append({
				"level": "Error", "code": "NO_HOUSE", "field": "houses",
				"message": "FHL message must contain at least one HBS (house waybill) block",
			})
			return issues

		serials_seen: set[str] = set()
		for i, house in enumerate(houses, start=1):
			hserial = (house.get("hwb_serial_number") or "").strip()
			if not hserial:
				issues.append({
					"level": "Error", "code": "HWB_SERIAL",
					"field": f"houses.{i}.hwb_serial_number",
					"message": f"House #{i}: HWB serial number is missing",
				})
			elif not _SERIAL_RE.match(hserial):
				issues.append({
					"level": "Error", "code": "HWB_SERIAL",
					"field": f"houses.{i}.hwb_serial_number",
					"message": f"House #{i}: serial must be 1–12 alphanumeric characters (DE119)",
				})
			elif hserial in serials_seen:
				issues.append({
					"level": "Error", "code": "HWB_DUP",
					"field": f"houses.{i}.hwb_serial_number",
					"message": f"House #{i}: duplicate serial {hserial!r} in this message",
				})
			else:
				serials_seen.add(hserial)

			if (house.get("number_of_pieces") or 0) <= 0 or (house.get("weight") or 0) <= 0:
				issues.append({
					"level": "Error", "code": "HWB_QTY", "field": f"houses.{i}",
					"message": f"House #{i}: pieces and weight must be greater than zero",
				})

			if not house.get("manifest_description"):
				issues.append({
					"level": "Error", "code": "HWB_QTY",
					"field": f"houses.{i}.manifest_description",
					"message": f"House #{i}: manifest description (DE708) is required",
				})

			if house.get("hwb_origin") and house.get("hwb_destination"):
				if house["hwb_origin"] == house["hwb_destination"]:
					issues.append({
						"level": "Error", "code": "HWB_ROUTE", "field": f"houses.{i}",
						"message": f"House #{i}: origin and destination cannot be the same airport",
					})

			for table, label in (("special_handling", "SPH"), ("free_text", "TXT"), ("hs_codes", "HTS")):
				if len(house.get(table) or []) > 9:
					issues.append({
						"level": "Warning", "code": "ROW_LIMIT",
						"field": f"houses.{i}.{table}",
						"message": f"House #{i}: {label} has more than 9 rows (FHL §3–5 limit)",
					})

			if not (house.get("charge_declarations") or {}).get("currency"):
				issues.append({
					"level": "Warning", "code": "CURRENCY",
					"field": f"houses.{i}.charge_declarations",
					"message": f"House #{i}: no CVD currency found; USD will be used as default",
				})

		return issues

	# ---------------------------------------------------------------- process

	def process(self, data, message_in) -> str:
		"""Create/update one House Airway Bill per HBS block, linked to the master Shipment
		when it exists. When the master Shipment is not yet in the system, HAWBs are saved
		with awb_assignment_status='Unassigned AWB' and pending_awb_number set so they can
		be linked later via the 'Assign AWB' list action.

		Returns the master AWB number as the representative target_name.
		"""
		master = data["master"]
		awb_number = master["awb_number"]

		self._ensure("Airline", {"airline_prefix": master["airline_prefix"]}, master["airline_prefix"])
		self._ensure("Airport", {"iata_code": master["origin"]}, master["origin"])
		self._ensure("Airport", {"iata_code": master["destination"]}, master["destination"])

		master_shipment = awb_number if frappe.db.exists("Shipment", awb_number) else None

		for house in data.get("houses") or []:
			self._process_house(awb_number, master_shipment, house)

		return awb_number

	def _process_house(self, awb_number, master_shipment, house):
		serial = house.get("hwb_serial_number", "")
		cvd = house.get("charge_declarations") or {}
		currency = cvd.get("currency") or "USD"

		for airport_code in (house.get("hwb_origin"), house.get("hwb_destination")):
			if airport_code:
				self._ensure("Airport", {"iata_code": airport_code}, airport_code)
		self._ensure_currency(currency)

		# Idempotency: check by master_shipment first, then by pending_awb_number so that
		# a previously-unassigned HAWB is updated (rather than duplicated) when the master
		# Shipment arrives and the FHL is reprocessed.
		existing = None
		if master_shipment:
			existing = frappe.db.get_value(
				"House Airway Bill",
				{"master_shipment": master_shipment, "hwb_serial_number": serial, "docstatus": ("!=", 2)},
				"name",
			)
		if not existing:
			existing = frappe.db.get_value(
				"House Airway Bill",
				{"pending_awb_number": awb_number, "hwb_serial_number": serial, "docstatus": ("!=", 2)},
				"name",
			)

		if existing:
			doc = frappe.get_doc("House Airway Bill", existing)
		else:
			doc = frappe.new_doc("House Airway Bill")

		doc.master_shipment = master_shipment
		doc.awb_assignment_status = "Assigned" if master_shipment else "Unassigned AWB"
		doc.pending_awb_number = None if master_shipment else awb_number
		doc.hwb_serial_number = serial
		doc.hwb_origin = house.get("hwb_origin") or doc.hwb_origin
		doc.hwb_destination = house.get("hwb_destination") or doc.hwb_destination
		doc.number_of_pieces = house.get("number_of_pieces") or doc.number_of_pieces
		doc.weight_code = house.get("weight_code") or doc.weight_code or "K"
		doc.weight = house.get("weight") or doc.weight
		doc.slac = house.get("slac") if house.get("slac") is not None else doc.slac
		doc.manifest_description = (house.get("manifest_description") or doc.manifest_description or "")[:15]

		doc.set("special_handling", [])
		for row in (house.get("special_handling") or [])[:9]:
			code = (row.get("code") or "").strip()
			if code:
				self._ensure_sph(code)
				doc.append("special_handling", {"special_handling_code": code})

		doc.set("free_text", [])
		for row in (house.get("free_text") or [])[:9]:
			text = (row.get("free_text") or "").strip()
			if text:
				doc.append("free_text", {"free_text": text[:65]})

		doc.set("hs_codes", [])
		for row in (house.get("hs_codes") or [])[:9]:
			code = (row.get("hs_code") or "").strip()
			if code:
				doc.append("hs_codes", {"hs_code": code})

		doc.set("oci_customs", [])
		for row in (house.get("oci") or []):
			info_id = (row.get("information_identifier") or "").strip()
			customs_id = (row.get("customs_info_identifier") or "").strip()
			supp = (row.get("supplementary") or "").strip()
			iso_code = (row.get("country") or "").strip()
			country_name = self._resolve_country(iso_code)
			if country_name or info_id or customs_id:
				self._ensure_oci_info_id(info_id)
				self._ensure_customs_info_id(customs_id)
				doc.append("oci_customs", {
					"country": country_name or None,
					"information_identifier": info_id or None,
					"customs_info_identifier": customs_id or None,
					"supplementary": supp[:35],
				})

		# CVD fields
		doc.currency = currency
		doc.wt_val_prepaid_collect = cvd.get("wt_val_prepaid_collect") or "P"
		doc.other_charges_prepaid_collect = cvd.get("other_charges_prepaid_collect") or "P"
		doc.declared_value_carriage_type = cvd.get("declared_value_carriage_type") or "NVD"
		doc.declared_value_carriage_amount = cvd.get("declared_value_carriage_amount") or 0.0
		doc.declared_value_customs_type = cvd.get("declared_value_customs_type") or "NCV"
		doc.declared_value_customs_amount = cvd.get("declared_value_customs_amount") or 0.0
		doc.insurance_type = cvd.get("insurance_type") or "XXX"
		doc.insurance_amount = cvd.get("insurance_amount") or 0.0

		doc.flags.ignore_permissions = True
		if not master_shipment:
			doc.flags.ignore_mandatory = True
		doc.save()

		# Stamp denormalized party fields via db_set — bypasses fetch_from
		# (shipper/consignee Link fields are left empty; directly-set values must persist).
		shipper = house.get("shipper") or {}
		if shipper.get("name"):
			frappe.db.set_value("House Airway Bill", doc.name, {
				"shipper_name": shipper["name"][:35],
				"shipper_address": (shipper.get("address") or ""),
				"shipper_place": (shipper.get("place") or "")[:17],
				"shipper_state": (shipper.get("state") or "")[:9],
				"shipper_post_code": (shipper.get("post_code") or "")[:9],
				"shipper_contact_id": (shipper.get("contact_id") or "")[:3],
				"shipper_contact_number": (shipper.get("contact_number") or "")[:25],
			})

		consignee = house.get("consignee") or {}
		if consignee.get("name"):
			frappe.db.set_value("House Airway Bill", doc.name, {
				"consignee_name": consignee["name"][:35],
				"consignee_address": (consignee.get("address") or ""),
				"consignee_place": (consignee.get("place") or "")[:17],
				"consignee_state": (consignee.get("state") or "")[:9],
				"consignee_post_code": (consignee.get("post_code") or "")[:9],
				"consignee_contact_id": (consignee.get("contact_id") or "")[:3],
				"consignee_contact_number": (consignee.get("contact_number") or "")[:25],
			})

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

	def _ensure_sph(self, code):
		if code and not frappe.db.exists("Special Handling Code", code):
			frappe.get_doc({"doctype": "Special Handling Code", "code": code}).insert(ignore_permissions=True)

	def _ensure_oci_info_id(self, code):
		if code and not frappe.db.exists("OCI Information Identifier", code):
			frappe.get_doc({"doctype": "OCI Information Identifier", "code": code}).insert(
				ignore_permissions=True
			)

	def _ensure_customs_info_id(self, code):
		if code and not frappe.db.exists("Customs Information Identifier", code):
			frappe.get_doc({"doctype": "Customs Information Identifier", "code": code}).insert(
				ignore_permissions=True
			)

	def _resolve_country(self, iso_code: str) -> str | None:
		"""Map a 2-letter ISO code to the Frappe Country name, or return None if not found."""
		if not iso_code:
			return None
		try:
			return frappe.db.get_value("Country", {"country_code": iso_code.lower()}, "name")
		except Exception:
			return None
