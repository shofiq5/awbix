import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

DEFAULT_VOLUME_FACTOR = 6000  # cm³ per kg (IATA)
_UNIT_TO_CM = {"cm": 1.0, "in": 2.54, "m": 100.0}

# Volume Code names that represent cubic metres (MC is the IATA standard code).
_M3_VOLUME_CODES = {"MC", "M3", "CBM"}


def _row_volume_cm3(row):
	"""Return total volume in cm³ for a single dimension row."""
	pieces = row.get("pieces") if isinstance(row, dict) else (row.pieces or 1)
	if not pieces:
		pieces = 1
	unit = (row.get("dim_unit") if isinstance(row, dict) else row.dim_unit) or "cm"
	f = _UNIT_TO_CM.get(unit, 1.0)
	length = (row.get("length") if isinstance(row, dict) else row.length) or 0
	width = (row.get("width") if isinstance(row, dict) else row.width) or 0
	height = (row.get("height") if isinstance(row, dict) else row.height) or 0
	return (length * f) * (width * f) * (height * f) * pieces


class Shipment(Document):
	def validate(self):
		self.validate_awb_serial_number()
		self.set_awb_number()
		self.compute_dimensions()
		self.populate_charge_summary()
		if self.origin and self.destination and self.origin == self.destination:
			frappe.throw("Origin and Destination cannot be the same airport.")

	def set_awb_number(self):
		if self.airline_prefix and self.awb_serial_number:
			self.awb_number = f"{self.airline_prefix}-{self.awb_serial_number}"

	def validate_awb_serial_number(self):
		serial = (self.awb_serial_number or "").strip()
		if not serial:
			return
		if not serial.isdigit() or len(serial) != 8:
			frappe.throw("AWB Serial Number (DE113) must be exactly 8 digits.")
		# DE113: the last digit is the unweighted modulus-7 check digit of the
		# first seven digits (IATA CSC Resolution 600a).
		expected = int(serial[:7]) % 7
		if expected != int(serial[7]):
			frappe.throw(
				f"Invalid AWB check digit: serial ends in {serial[7]} but the "
				f"modulus-7 check digit of {serial[:7]} is {expected}."
			)

	def populate_charge_summary(self):
		if not self.rate_lines:
			frappe.throw(_("Rate Lines are required. Please add at least one rate line before saving."))

		if not self.other_charges:
			frappe.msgprint(
				_("No Other Charges entered. Charge summary will include weight charges only."),
				indicator="orange",
				alert=True,
			)

		self.charge_summary = []

		# WT — one row per settlement group (sum of all rate line totals)
		wt_settlement = "PPD" if self.wt_val_prepaid_collect == "P" else "COL"
		wt_amount = sum(flt(r.total) for r in self.rate_lines)
		self.append("charge_summary", {"settlement": wt_settlement, "charge_identifier": "WT", "amount": wt_amount})

		# OC — sum all other charges per settlement group into a single row each
		oc_totals = {"PPD": 0.0, "COL": 0.0}
		for row in self.other_charges:
			pc = row.prepaid_collect or self.other_charges_prepaid_collect or "P"
			group = "PPD" if pc == "P" else "COL"
			oc_totals[group] += flt(row.amount)

		for group in ("PPD", "COL"):
			if oc_totals[group]:
				self.append("charge_summary", {"settlement": group, "charge_identifier": "OC", "amount": oc_totals[group]})

		# CT — grand total per settlement group (WT + OC for that group)
		for group in ("PPD", "COL"):
			group_rows = [r for r in self.charge_summary if r.settlement == group]
			if group_rows:
				self.append("charge_summary", {
					"settlement": group,
					"charge_identifier": "CT",
					"amount": sum(flt(r.amount) for r in group_rows),
				})

	def compute_dimensions(self):
		"""Compute per-row volume/volume_weight and roll up totals onto the parent."""
		if not self.dimensions:
			# No dimension rows — derive volume_weight from volume_amount if m³, then update chargeable_weight.
			vol_code = (self.volume_code or "").strip().upper()
			if not vol_code or vol_code in _M3_VOLUME_CODES:
				vol_m3 = float(self.volume_amount or 0)
				if vol_m3 > 0:
					factor = int(self.volume_weight_factor or 0) or DEFAULT_VOLUME_FACTOR
					self.volume_weight = round(vol_m3 * 1_000_000 / factor, 2)
					self.chargeable_weight = round(max(float(self.weight or 0), self.volume_weight), 2)
			return

		factor = int(self.volume_weight_factor or 0) or DEFAULT_VOLUME_FACTOR
		total_cm3 = 0.0
		has_valid_row = False

		for idx, row in enumerate(self.dimensions, start=1):
			# Auto-fill line_number if blank.
			if not row.line_number:
				row.line_number = idx

			vol_cm3 = _row_volume_cm3(row)
			if vol_cm3 <= 0:
				# Skip degenerate rows — don't zero computed fields, just leave them.
				continue

			has_valid_row = True
			total_cm3 += vol_cm3
			row.volume = round(vol_cm3 / 1_000_000, 4)
			row.volume_weight = round(vol_cm3 / factor, 2)

		if not has_valid_row:
			return

		calc_vw = round(total_cm3 / factor, 2)
		calc_m3 = total_cm3 / 1_000_000

		vol_code = (self.volume_code or "").strip().upper()
		if not vol_code or vol_code in _M3_VOLUME_CODES:
			# Auto-raise volume_amount to at least the dimension-calculated m³.
			if not self.volume_amount or self.volume_amount < calc_m3:
				self.volume_amount = round(calc_m3, 4)
			# volume_weight is the larger of dimension VW and volume_amount-derived VW.
			manual_vw = round(float(self.volume_amount) * 1_000_000 / factor, 2)
			self.volume_weight = max(calc_vw, manual_vw)
		else:
			frappe.msgprint(
				f"Dimensions calculated {calc_m3:.4f} m³ but volume_code is '{self.volume_code}' "
				"(not m³). volume_amount was not updated automatically — please set it manually.",
				alert=True,
			)
			self.volume_weight = calc_vw

		self.chargeable_weight = round(max(float(self.weight or 0), self.volume_weight or 0), 2)


@frappe.whitelist()
def calculate_dimension_totals(rows, weight=0, volume_weight_factor=None, volume_amount=0, volume_code=None):
	"""
	Preview endpoint: accepts a JSON list of dimension rows, returns per-row
	computed fields plus header totals.  Reuses the same math as compute_dimensions()
	so FE and BE never diverge.

	rows: JSON-encoded list of {pieces, length, width, height, dim_unit}
	Returns: {rows: [{volume, volume_weight}, ...], total_volume_m3, volume_weight,
	          chargeable_weight, suggested_volume_amount}
	"""
	if isinstance(rows, str):
		rows = json.loads(rows)
	weight = float(weight or 0)
	factor = int(volume_weight_factor or 0) or DEFAULT_VOLUME_FACTOR

	out_rows = []
	total_cm3 = 0.0

	for row in rows:
		vol_cm3 = _row_volume_cm3(row)
		if vol_cm3 <= 0:
			out_rows.append({"volume": 0, "volume_weight": 0})
			continue
		total_cm3 += vol_cm3
		out_rows.append({
			"volume": round(vol_cm3 / 1_000_000, 4),
			"volume_weight": round(vol_cm3 / factor, 2),
		})

	vol_code = (volume_code or "").strip().upper()

	if not total_cm3:
		# No valid dimension rows — derive volume_weight from volume_amount when m³.
		existing = float(volume_amount or 0)
		if (not vol_code or vol_code in _M3_VOLUME_CODES) and existing > 0:
			vw = round(existing * 1_000_000 / factor, 2)
		else:
			vw = 0.0
		return {
			"rows": out_rows,
			"total_volume_m3": 0.0,
			"volume_weight": vw,
			"chargeable_weight": round(max(weight, vw), 2),
			"suggested_volume_amount": None,
		}

	total_m3 = total_cm3 / 1_000_000
	calc_vw = round(total_cm3 / factor, 2)

	suggested_volume_amount = None
	if not vol_code or vol_code in _M3_VOLUME_CODES:
		existing = float(volume_amount or 0)
		if not existing or existing < total_m3:
			suggested_volume_amount = round(total_m3, 4)
		# volume_weight = max of dimension VW and volume_amount-derived VW.
		effective_m3 = suggested_volume_amount if suggested_volume_amount is not None else existing
		manual_vw = round(effective_m3 * 1_000_000 / factor, 2) if effective_m3 else 0.0
		vw = max(calc_vw, manual_vw)
	else:
		vw = calc_vw

	chargeable = round(max(weight, vw), 2)

	return {
		"rows": out_rows,
		"total_volume_m3": round(total_m3, 4),
		"volume_weight": vw,
		"chargeable_weight": chargeable,
		"suggested_volume_amount": suggested_volume_amount,
	}


# Column aliases accepted in CSV/Excel uploads (lowercase).
_COL_ALIASES = {
	"pieces": "pieces",
	"qty": "pieces",
	"quantity": "pieces",
	"pcs": "pieces",
	"length": "length",
	"len": "length",
	"l": "length",
	"width": "width",
	"wid": "width",
	"w": "width",
	"height": "height",
	"hgt": "height",
	"h": "height",
	"unit": "dim_unit",
	"dim_unit": "dim_unit",
	"units": "dim_unit",
}

_MAX_ROWS = 1000


@frappe.whitelist()
def parse_dimension_file(file_url):
	"""
	Parse a CSV or xlsx file attached to the server and return a list of
	dimension rows suitable for the dimensions child table.

	file_url: the URL of a file previously uploaded to Frappe's File DocType.
	Returns: {rows: [...], errors: [{row, message}, ...]}
	"""
	from frappe.utils.file_manager import get_file

	file_name, file_content = get_file(file_url)
	file_name_lower = (file_name or "").lower()

	if file_name_lower.endswith(".csv"):
		raw_rows = _parse_csv(file_content)
	elif file_name_lower.endswith((".xlsx", ".xls")):
		raw_rows = _parse_xlsx(file_url, file_name_lower)
	else:
		frappe.throw("Unsupported file type. Please upload a .csv, .xlsx, or .xls file.")

	return _map_rows(raw_rows)


def _parse_csv(content):
	from frappe.utils.csvutils import read_csv_content

	if isinstance(content, bytes):
		content = content.decode("utf-8-sig", errors="replace")
	return read_csv_content(content)


def _parse_xlsx(file_url, file_name_lower):
	if file_name_lower.endswith(".xlsx"):
		from frappe.utils.xlsxutils import read_xlsx_file_from_attached_file

		return read_xlsx_file_from_attached_file(file_url=file_url)
	else:
		# .xls — use xlrd via Frappe helper if available, otherwise error out.
		try:
			from frappe.utils.xlsxutils import read_xls_file_from_attached_file

			return read_xls_file_from_attached_file(file_url=file_url)
		except ImportError:
			frappe.throw("XLS files require the xlrd package. Please upload .xlsx or .csv instead.")


def _map_rows(raw_rows):
	errors = []
	rows = []

	if not raw_rows:
		return {"rows": rows, "errors": errors}

	# First row is the header.
	header = [str(h).strip().lower() for h in raw_rows[0]]
	col_map = {}
	for idx, h in enumerate(header):
		canonical = _COL_ALIASES.get(h)
		if canonical:
			col_map[canonical] = idx

	data_rows = raw_rows[1:]
	if len(data_rows) > _MAX_ROWS:
		frappe.msgprint(
			f"File contains {len(data_rows)} rows; only the first {_MAX_ROWS} will be imported.",
			alert=True,
		)
		data_rows = data_rows[:_MAX_ROWS]

	for i, raw in enumerate(data_rows, start=2):  # 1-indexed, row 1 is header
		def _get(field):
			idx = col_map.get(field)
			if idx is None or idx >= len(raw):
				return None
			val = raw[idx]
			return str(val).strip() if val is not None else None

		row_errors = []
		try:
			pieces = int(float(_get("pieces") or 1))
		except (ValueError, TypeError):
			pieces = 1
			row_errors.append("Invalid pieces value; defaulted to 1.")

		def _float(field, label):
			val = _get(field)
			if not val:
				return 0.0, f"{label} is missing."
			try:
				return float(val), None
			except ValueError:
				return 0.0, f"{label} '{val}' is not a number."

		length, e1 = _float("length", "Length")
		width, e2 = _float("width", "Width")
		height, e3 = _float("height", "Height")
		row_errors += [e for e in [e1, e2, e3] if e]

		dim_unit = (_get("dim_unit") or "cm").lower()
		if dim_unit not in _UNIT_TO_CM:
			row_errors.append(f"Unknown unit '{dim_unit}'; defaulted to cm.")
			dim_unit = "cm"

		if row_errors:
			errors.append({"row": i, "message": "; ".join(row_errors)})

		rows.append({
			"pieces": pieces,
			"length": length,
			"width": width,
			"height": height,
			"dim_unit": dim_unit,
		})

	return {"rows": rows, "errors": errors}
