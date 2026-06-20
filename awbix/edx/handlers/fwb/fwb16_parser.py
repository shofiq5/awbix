"""FWB/16 (Air Waybill, Cargo-IMP) inbound parser.

Full coverage of the FWB/16 grammar in ``.claude/fwb_abnf.txt``. ``parse()`` is pure
(no DB) and returns one normalized dict per segment group; ``process()`` persists every
available data element into a ``Shipment`` and its child tables.

Segments handled: message id, AWB consignment detail (pieces/weight/volume/density),
FLT flight bookings, RTG routing, SHP/CNE/AGT/NFY parties (linked ``Party`` records),
SSR, ACC accounting, CVD charge declarations (types *and* amounts), RTD rate lines +
goods detail sub-lines, OTH other charges, PPD/COL charge summaries, CER certification,
ISU carrier execution, OSI, CDC destination-currency charges, REF sender reference,
COR customs origin, COI commission, SII sales incentive, ARD agent reference,
SPH special handling, NOM nominated handling party, SRI shipment references,
OPI other participants, and OCI other customs information.
"""

import re

import frappe

from awbix.edx.engine.base_parser import BaseParser
from awbix.edx.handlers.fwb import cargoimp

# <prefix>-<8-digit serial><origin><dest>[/additional info]
_AWB_RE = re.compile(r"^(\d{1,3})-(\d{8})([A-Z]{3})([A-Z]{3})(?:/(.*))?$")

# AWB consignment detail suffix: "T1K40", "T12K500.5" (volume/density handled separately)
_AWB_DETAIL_RE = re.compile(
	r"^(?P<desc>[TP])"
	r"(?P<pieces>\d+)"
	r"(?P<wt_code>[KL])"
	r"(?P<weight>\d+(?:\.\d+)?)"
)

_MONTHS = {
	"JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
	"JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}

_DV_CODES = ("NVD", "NCV", "XXX")


def _to_float(value):
	return cargoimp.to_decimal(value)


def _to_int(value):
	try:
		return int(str(value).strip())
	except (TypeError, ValueError):
		return None


class FWB16Parser(BaseParser):
	message_type = "FWB"
	version = "16"

	# ------------------------------------------------------------------ parse

	def parse(self, raw: str) -> dict:
		t = cargoimp.tokenize(raw)
		rate_lines, goods = self._parse_rtd(t)
		return {
			"message": {"type": self.message_type, "version": self.version, "id": t.get("message_id")},
			"awb": self._parse_awb(t.get("awb_line")),
			"flights": self._parse_flights(t),
			"routing": self._parse_routing(t),
			"shipper": self._parse_party(t, "SHP"),
			"consignee": self._parse_party(t, "CNE"),
			"agent": self._parse_agent(t),
			"also_notify": self._parse_notify(t),
			"ssr": self._parse_text_segment(t, "SSR"),
			"osi": self._parse_text_segment(t, "OSI"),
			"accounting": self._parse_accounting(t),
			"charge_declarations": self._parse_cvd(t),
			"rate_lines": rate_lines,
			"goods": goods,
			"other_charges": self._parse_other_charges(t),
			"charge_summary": self._parse_charge_summary(t),
			"certification": self._parse_certification(t),
			"execution": self._parse_execution(t),
			"cdc": self._parse_cdc(t),
			"sender_reference": self._parse_ref(t),
			"customs_origin": self._parse_cor(t),
			"commission": self._parse_coi(t),
			"sales_incentive": self._parse_sii(t),
			"agent_reference": self._parse_ard(t),
			"special_handling": self._parse_sph(t),
			"nominated_handling": self._parse_nom(t),
			"references": self._parse_sri(t),
			"other_participants": self._parse_opi(t),
			"oci": self._parse_oci(t),
			"segments_seen": [s["code"] for s in t["segments"] if s["code"]],
		}

	# ------------------------------------------------------------ AWB / FLT / RTG

	def _parse_awb(self, line):
		if not line:
			return {}
		m = _AWB_RE.match(line.strip())
		if not m:
			return {"raw_detail": line}
		prefix, serial, origin, dest, rest = m.groups()
		result = {
			"airline_prefix": prefix,
			"awb_serial_number": serial,
			"awb_number": f"{prefix}-{serial}",
			"origin": origin,
			"destination": dest,
			"raw_detail": rest or "",
		}
		if rest:
			dm = _AWB_DETAIL_RE.match(rest)
			if dm:
				result["shipment_description_code"] = dm.group("desc")
				result["number_of_pieces"] = int(dm.group("pieces"))
				result["weight_code"] = dm.group("wt_code")
				result["weight"] = float(dm.group("weight"))
				tail = rest[dm.end():].strip()
				if tail.startswith("DG"):
					dg = re.match(r"^DG(\d{1,2})$", tail)
					if dg:
						result["density_indicator"] = "DG"
						result["density_group"] = int(dg.group(1))
				elif tail:
					vol = re.match(r"^([A-Z]{2})([\d.]+)$", tail)
					if vol:
						result["volume_code"] = vol.group(1)
						result["volume_amount"] = float(vol.group(2))
		return result

	def _parse_flights(self, t):
		seg = cargoimp.first(t, "FLT")
		if not seg:
			return []
		parts = [p.strip() for p in seg["lines"][0].split("/")][1:]
		flights = []
		i = 0
		while i < len(parts):
			flt = parts[i]
			day = parts[i + 1] if i + 1 < len(parts) else ""
			if flt:
				flights.append({
					"carrier": flt[:2],
					"flight_number": flt[2:],
					"day": _to_int(day),
				})
			i += 2
		return flights

	def _parse_routing(self, t):
		seg = cargoimp.first(t, "RTG")
		if not seg:
			return []
		parts = [p for p in seg["lines"][0].split("/")[1:] if p]
		rows = []
		for i, tok in enumerate(parts, start=1):
			rows.append({"sequence": i, "airport": tok[:3], "carrier": tok[3:5] if len(tok) >= 5 else ""})
		return rows

	# ------------------------------------------------------------ parties

	def _parse_party(self, t, code):
		"""SHP/CNE: optional account on the header, then name / street / place[/state] /
		country[/postcode] / contacts on the continuation lines (ABNF positional)."""
		seg = cargoimp.first(t, code)
		if not seg:
			return {}
		hparts = seg["lines"][0].split("/")
		account = hparts[1].strip() if len(hparts) > 1 else ""
		return self._assemble_party(cargoimp.continuation_text(seg), account=account)

	def _parse_notify(self, t):
		"""All NFY segments → one party each (no account line per ABNF)."""
		rows = []
		for seg in cargoimp.by_code(t, "NFY"):
			party = self._assemble_party(cargoimp.continuation_text(seg))
			if party.get("name"):
				rows.append(party)
		return rows

	def _assemble_party(self, lines, account=""):
		res = {"account": account, "contacts": [], "lines": lines}
		if len(lines) > 0:
			res["name"] = lines[0]
		if len(lines) > 1:
			res["address"] = lines[1]
		if len(lines) > 2:
			place = lines[2].split("/")
			res["place"] = place[0].strip()
			if len(place) > 1:
				res["state"] = place[1].strip()
		if len(lines) > 3:
			loc = lines[3].split("/")
			res["country"] = loc[0].strip()
			if len(loc) > 1:
				res["post_code"] = loc[1].strip()
		for extra in lines[4:]:
			cparts = extra.split("/")
			if cparts and cparts[0].strip():
				res["contacts"].append({
					"identifier": cparts[0].strip(),
					"number": cparts[1].strip() if len(cparts) > 1 else "",
				})
		return res

	def _parse_agent(self, t):
		"""AGT: header is AGT/[account]/iata[/cass[/participant]]; continuation name / place."""
		seg = cargoimp.first(t, "AGT")
		if not seg:
			return {}
		hparts = seg["lines"][0].split("/")
		lines = cargoimp.continuation_text(seg)
		return {
			"name": lines[0] if len(lines) > 0 else "",
			"account": (hparts[1].strip() if len(hparts) > 1 else "")[:14],
			"iata_code": (hparts[2].strip() if len(hparts) > 2 else "")[:7],
			"cass_address": (hparts[3].strip() if len(hparts) > 3 else "")[:4],
			"participant_id": (hparts[4].strip() if len(hparts) > 4 else "")[:3],
			"place": lines[1] if len(lines) > 1 else "",
			"lines": lines,
		}

	# ------------------------------------------------------------ SSR / OSI / ACC / SPH

	def _segment_values(self, seg, code):
		"""All slash-delimited values of a segment: header remainder + continuation bodies."""
		out = []
		header = seg["lines"][0]
		if header.startswith(code + "/"):
			out.append(header[len(code) + 1:].strip())
		out += cargoimp.continuation_text(seg)
		return [v for v in out if v]

	def _parse_text_segment(self, t, code):
		"""SSR / OSI: 1*3 free-text lines."""
		seg = cargoimp.first(t, code)
		return self._segment_values(seg, code) if seg else []

	def _parse_sph(self, t):
		"""SPH: 1*9 special-handling codes, slash-delimited on the header line."""
		seg = cargoimp.first(t, "SPH")
		if not seg:
			return []
		codes = []
		for v in self._segment_values(seg, "SPH"):
			codes += [c.strip() for c in v.split("/") if c.strip()]
		return codes

	def _parse_accounting(self, t):
		"""ACC: 1*6 /identifier/information pairs."""
		seg = cargoimp.first(t, "ACC")
		if not seg:
			return []
		rows = []
		for body in self._segment_values(seg, "ACC"):
			parts = body.split("/")
			ident = parts[0].strip() if parts else ""
			info = parts[1].strip() if len(parts) > 1 else ""
			if ident or info:
				rows.append({"identifier": ident, "information": info})
		return rows

	# ------------------------------------------------------------ CVD

	def _parse_cvd(self, t):
		seg = cargoimp.first(t, "CVD")
		if not seg:
			return {}
		parts = seg["lines"][0].split("/")
		currency = parts[1].strip() if len(parts) > 1 else ""
		charge_code = parts[2].strip() if len(parts) > 2 else ""
		pp = parts[3].strip() if len(parts) > 3 else ""
		wt_val_pc = pp[0] if pp else "P"
		other_chg_pc = pp[1] if len(pp) > 1 else "P"

		carriage_type, carriage_amt = self._dv_value(parts[4] if len(parts) > 4 else "", "NVD")
		customs_type, customs_amt = self._dv_value(parts[5] if len(parts) > 5 else "", "NCV")
		insurance_type, insurance_amt = self._dv_value(parts[6] if len(parts) > 6 else "", "XXX")

		return {
			"currency": currency,
			"charge_code": charge_code,
			"wt_val_prepaid_collect": wt_val_pc if wt_val_pc in ("P", "C") else "P",
			"other_charges_prepaid_collect": other_chg_pc if other_chg_pc in ("P", "C") else "P",
			"declared_value_carriage_type": carriage_type,
			"declared_value_carriage_amount": carriage_amt,
			"declared_value_customs_type": customs_type,
			"declared_value_customs_amount": customs_amt,
			"insurance_type": insurance_type,
			"insurance_amount": insurance_amt,
			"raw": seg["lines"][0],
		}

	def _dv_value(self, raw, default_code):
		"""A declared-value field is either a no-value code (NVD/NCV/XXX) or an amount."""
		r = (raw or "").strip().upper()
		if not r:
			return default_code, None
		if r in _DV_CODES:
			return r, None
		amount = cargoimp.to_decimal(r)
		if amount is not None:
			return "Value", amount
		return default_code, None

	# ------------------------------------------------------------ RTD (rate + goods)

	def _parse_rtd(self, t):
		"""Return (rate_lines, goods). Each RTD continuation line is keyed by its line
		number; a line whose first token is ``N<id>`` is a goods sub-line, otherwise it is
		a rate line with column-tagged tokens (P/K/L/C/S/W/R/T)."""
		seg = cargoimp.first(t, "RTD")
		rate_lines, goods = [], []
		if not seg:
			return rate_lines, goods

		raw_lines = list(seg["lines"])
		if raw_lines and raw_lines[0].startswith("RTD"):
			raw_lines[0] = raw_lines[0][3:]

		for raw in raw_lines:
			tokens = raw.split("/")
			if tokens and tokens[0] == "":
				tokens = tokens[1:]
			if not tokens:
				continue
			line_no = tokens[0].strip()
			rest = tokens[1:]
			if not line_no.isdigit() or not rest:
				continue
			line_no = int(line_no)
			if rest[0][:1] == "N":
				goods.append(self._parse_goods_line(line_no, rest))
			elif len(rest) == 1 and len(rest[0]) == 1 and rest[0].isalpha():
				# A second-line carrying only a service code (DE505).
				goods.append({"rate_line_number": line_no, "service_code": rest[0]})
			else:
				row = self._parse_rate_line(line_no, rest)
				if len(row) > 1:  # more than just line_number → real rate data
					rate_lines.append(row)
		return rate_lines, goods

	def _parse_rate_line(self, line_no, tokens):
		row = {"line_number": line_no}
		for tok in tokens:
			if not tok:
				continue
			tag, val = tok[0], tok[1:]
			if tag == "P":
				if val.isdigit():
					row["number_of_pieces"] = int(val)
				else:
					row["rate_combination_point"] = val
			elif tag in ("K", "L"):
				row["gross_weight_code"] = tag
				row["gross_weight"] = _to_float(val)
			elif tag == "C":
				row["rate_class_code"] = val
			elif tag == "S":
				self._parse_commodity(row, val)
			elif tag == "W":
				row["chargeable_weight"] = _to_float(val)
			elif tag == "R":
				row["rate_charge"] = _to_float(val)
			elif tag == "T":
				row["total"] = _to_float(val)
		return row

	def _parse_commodity(self, row, val):
		"""S column: rate class + percentage / commodity item number / ULD rate-class type."""
		if re.match(r"^[A-Za-z]\d{1,3}$", val):
			row["rate_class_code"] = val[0]
			row["rate_class_percentage"] = int(val[1:])
		elif re.match(r"^\d{4,7}$", val):
			row["commodity_item_number"] = val
		elif val:
			row["uld_rate_class_type"] = val

	def _parse_goods_line(self, line_no, tokens):
		identifier = tokens[0][1:2]
		data = tokens[1:]
		row = {"rate_line_number": line_no, "goods_data_identifier": identifier}
		# A trailing single-alpha token is the optional service code (DE505).
		if len(data) >= 2 and len(data[-1]) == 1 and data[-1].isalpha():
			row["service_code"] = data[-1]
			data = data[:-1]
		if identifier in ("G", "C"):
			row["description"] = ("/".join(data)).strip()[:20]
		elif identifier == "D":
			self._parse_dimensions(row, data)
		elif identifier == "V":
			m = re.match(r"^([A-Za-z]{2})([\d.]+)$", data[0]) if data else None
			if m:
				row["volume_code"] = m.group(1)
				row["volume_amount"] = _to_float(m.group(2))
		elif identifier == "U":
			val = data[0] if data else ""
			if len(val) >= 5:
				row["uld_type"] = val[:3]
				row["uld_owner"] = val[-2:]
				row["uld_serial"] = val[3:-2]
		elif identifier == "S":
			row["slac"] = _to_int(data[0]) if data else None
		elif identifier == "H":
			row["hs_code"] = data[0].strip()[:18] if data else ""
		elif identifier == "O":
			row["country_of_origin"] = data[0].strip() if data else ""
		return row

	def _parse_dimensions(self, row, data):
		if data and data[0]:
			wc = data[0][0]
			if wc in ("K", "L"):
				row["dim_weight_code"] = wc
				row["dim_weight"] = _to_float(data[0][1:])
		dims = data[1] if len(data) > 1 else ""
		if dims and dims.upper() != "NDA":
			m = re.match(r"^([A-Za-z]{1,3})(\d+)-(\d+)-(\d+)$", dims)
			if m:
				row["measurement_unit"] = m.group(1)
				row["dim_length"] = float(m.group(2))
				row["dim_width"] = float(m.group(3))
				row["dim_height"] = float(m.group(4))
		if len(data) > 2 and data[2].strip().isdigit():
			row["dim_pieces"] = int(data[2].strip())

	# ------------------------------------------------------------ OTH / PPD / COL

	def _parse_other_charges(self, t):
		seg = cargoimp.first(t, "OTH")
		if not seg:
			return []
		raw_lines = list(seg["lines"])
		if raw_lines and raw_lines[0].startswith("OTH"):
			raw_lines[0] = raw_lines[0][3:]
		rows = []
		for raw in raw_lines:
			parts = raw.split("/")
			if parts and parts[0] == "":
				parts = parts[1:]
			if not parts:
				continue
			pc = parts[0].strip()
			pc = pc if pc in ("P", "C") else ""
			body = "".join(parts[1:])
			for code, ent, amt in re.findall(r"([A-Z]{2})([A-Z])([\d.]+)", body):
				rows.append({
					"prepaid_collect": pc or "P",
					"other_charge_code": code,
					"entitlement_code": ent,
					"amount": _to_float(amt),
				})
		return rows

	def _parse_charge_summary(self, t):
		rows = []
		for code, settlement in (("PPD", "Prepaid"), ("COL", "Collect")):
			seg = cargoimp.first(t, code)
			if not seg:
				continue
			raw_lines = list(seg["lines"])
			if raw_lines and raw_lines[0].startswith(code):
				raw_lines[0] = raw_lines[0][3:]
			for raw in raw_lines:
				for tok in raw.split("/"):
					tok = tok.strip()
					m = re.match(r"^(WT|VC|TX|OA|OC|CT)([\d.]+)$", tok)
					if m:
						rows.append({
							"settlement": settlement,
							"charge_identifier": m.group(1),
							"amount": _to_float(m.group(2)),
						})
		return rows

	# ------------------------------------------------------------ CER / ISU / CDC

	def _parse_certification(self, t):
		seg = cargoimp.first(t, "CER")
		if not seg:
			return {}
		parts = seg["lines"][0].split("/", 1)
		return {"signature": parts[1].strip()[:20]} if len(parts) > 1 else {}

	def _parse_execution(self, t):
		seg = cargoimp.first(t, "ISU")
		if not seg:
			return {}
		parts = seg["lines"][0].split("/")
		res = {}
		date_token = parts[1].strip() if len(parts) > 1 else ""
		dm = re.match(r"^(\d{2})([A-Z]{3})(\d{2})$", date_token)
		if dm:
			day, mon, yr = int(dm.group(1)), _MONTHS.get(dm.group(2)), int(dm.group(3))
			if mon:
				res["issue_date"] = f"20{yr:02d}-{mon:02d}-{day:02d}"
		if len(parts) > 2:
			res["issue_place"] = parts[2].strip()[:17]
		if len(parts) > 3:
			res["signature"] = parts[3].strip()[:20]
		return res

	def _parse_cdc(self, t):
		seg = cargoimp.first(t, "CDC")
		if not seg:
			return {}
		parts = seg["lines"][0].split("/")
		res = {}
		cur_rate = parts[1].strip() if len(parts) > 1 else ""
		m = re.match(r"^([A-Z]{3})([\d.]+)$", cur_rate)
		if m:
			res["dest_currency"] = m.group(1)
			res["rate_of_exchange"] = _to_float(m.group(2))
		if len(parts) > 2:
			res["cc_charges_dest"] = _to_float(parts[2])
		if len(parts) > 3:
			res["charges_at_dest"] = _to_float(parts[3])
		if len(parts) > 4:
			res["total_collect_charges"] = _to_float(parts[4])
		return res

	# ------------------------------------------------------------ REF / COR / NOM

	def _parse_ref(self, t):
		seg = cargoimp.first(t, "REF")
		if not seg:
			return {}
		parts = seg["lines"][0].split("/")
		res = {}
		# parts[0] == "REF"; parts[1] empty → participant form, else office-address form
		if len(parts) > 1 and parts[1].strip() == "":
			if len(parts) > 2 and parts[2].strip():
				res["file_reference"] = parts[2].strip()[:15]
			if len(parts) > 3 and parts[3].strip():
				res["participant_id"] = parts[3].strip()[:3]
			if len(parts) > 4 and parts[4].strip():
				res["participant_code"] = parts[4].strip()[:17]
		else:
			if len(parts) > 1 and parts[1].strip():
				res["office_address"] = parts[1].strip()[:8]
			if len(parts) > 2 and parts[2].strip():
				res["file_reference"] = parts[2].strip()[:15]
		return res

	def _parse_cor(self, t):
		seg = cargoimp.first(t, "COR")
		if not seg:
			return {}
		parts = seg["lines"][0].split("/", 1)
		return {"code": parts[1].strip()[:2]} if len(parts) > 1 and parts[1].strip() else {}

	def _parse_nom(self, t):
		seg = cargoimp.first(t, "NOM")
		if not seg:
			return {}
		parts = seg["lines"][0].split("/")
		res = {}
		if len(parts) > 1 and parts[1].strip():
			res["name"] = parts[1].strip()[:35]
		if len(parts) > 2 and parts[2].strip():
			res["place"] = parts[2].strip()[:17]
		return res

	# ------------------------------------------------------------ COI / SII / ARD

	def _parse_coi(self, t):
		seg = cargoimp.first(t, "COI")
		if not seg:
			return {}
		parts = seg["lines"][0].split("/")
		res = {}
		# COI///pct  |  COI//amount  |  COI/indicator
		if len(parts) >= 4 and parts[1].strip() == "" and parts[2].strip() == "":
			res["percentage"] = _to_float(parts[3])
		elif len(parts) >= 3 and parts[1].strip() == "":
			res["amount"] = _to_float(parts[2])
		elif len(parts) >= 2 and parts[1].strip():
			res["no_commission_indicator"] = parts[1].strip()[:2]
		return res

	def _parse_sii(self, t):
		seg = cargoimp.first(t, "SII")
		if not seg:
			return {}
		parts = seg["lines"][0].split("/")
		res = {}
		if len(parts) > 1:
			res["amount"] = _to_float(parts[1])
		if len(parts) > 2 and parts[2].strip():
			res["indicator"] = parts[2].strip()[:2]
		return res

	def _parse_ard(self, t):
		seg = cargoimp.first(t, "ARD")
		if not seg:
			return {}
		parts = seg["lines"][0].split("/", 1)
		return {"reference": parts[1].strip()[:15]} if len(parts) > 1 and parts[1].strip() else {}

	# ------------------------------------------------------------ SRI / OPI / OCI

	def _parse_sri(self, t):
		rows = []
		for seg in cargoimp.by_code(t, "SRI"):
			parts = seg["lines"][0].split("/")
			ref = parts[1].strip() if len(parts) > 1 else ""
			supp1 = parts[2].strip() if len(parts) > 2 else ""
			supp2 = parts[3].strip() if len(parts) > 3 else ""
			if ref or supp1 or supp2:
				rows.append({
					"reference_number": ref[:14],
					"supplementary_1": supp1[:12],
					"supplementary_2": supp2[:12],
				})
		return rows

	def _parse_opi(self, t):
		rows = []
		for seg in cargoimp.by_code(t, "OPI"):
			header = seg["lines"][0].split("/")
			name = header[1].strip() if len(header) > 1 else ""
			row = {"name": name[:35]}
			cont = cargoimp.continuation_text(seg)
			if cont:
				parts = cont[0].split("/")
				# leading empty (//…) → participant form; else office-address form
				if parts and parts[0].strip() == "":
					if len(parts) > 1 and parts[1].strip():
						row["office_file_reference"] = parts[1].strip()[:15]
					if len(parts) > 2 and parts[2].strip():
						row["participant_id"] = parts[2].strip()[:3]
					if len(parts) > 3 and parts[3].strip():
						row["participant_code"] = parts[3].strip()[:17]
					if len(parts) > 4 and parts[4].strip():
						row["airport"] = parts[4].strip()[:3]
				else:
					if parts and parts[0].strip():
						row["office_file_reference"] = parts[0].strip()[:15]
					if len(parts) > 1 and parts[1].strip():
						row["participant_id"] = parts[1].strip()[:3]
			if name:
				rows.append(row)
		return rows

	def _parse_oci(self, t):
		seg = cargoimp.first(t, "OCI")
		if not seg:
			return []
		raw_lines = list(seg["lines"])
		if raw_lines and raw_lines[0].startswith("OCI"):
			raw_lines[0] = raw_lines[0][3:]
		rows = []
		for raw in raw_lines:
			parts = raw.split("/")
			if parts and parts[0] == "":
				parts = parts[1:]
			country = parts[0].strip() if len(parts) > 0 else ""
			info_id = parts[1].strip() if len(parts) > 1 else ""
			customs_id = parts[2].strip() if len(parts) > 2 else ""
			supp = parts[3].strip() if len(parts) > 3 else ""
			if country or info_id or customs_id or supp:
				rows.append({
					"country": country,
					"information_identifier": info_id,
					"customs_info_identifier": customs_id,
					"supplementary": supp[:35],
				})
		return rows

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
			doc = frappe.get_doc("Shipment", name)
		else:
			doc = frappe.new_doc("Shipment")

		self._apply_awb(doc, awb, currency)
		self._apply_cvd(doc, data.get("charge_declarations") or {})
		self._apply_parties(doc, data)
		self._apply_flights(doc, data.get("flights") or [])
		self._apply_routing(doc, data.get("routing") or [])
		self._apply_rate_description(doc, data.get("rate_lines") or [], data.get("goods") or [])
		self._apply_other_charges(doc, data.get("other_charges") or [])
		self._apply_charge_summary(doc, data.get("charge_summary") or [])
		self._apply_cdc(doc, data.get("cdc") or {})
		self._apply_simple_tables(doc, data)
		self._apply_certification_execution(doc, data)
		self._apply_references(doc, data)
		self._apply_commission_incentive(doc, data)

		doc.flags.ignore_permissions = True
		doc.save()
		return doc.name

	# ---- apply: AWB / CVD ----

	def _apply_awb(self, doc, awb, currency):
		doc.airline_prefix = awb["airline_prefix"]
		doc.awb_serial_number = awb["awb_serial_number"]
		doc.origin = awb["origin"]
		doc.destination = awb["destination"]
		doc.currency = currency
		if awb.get("shipment_description_code"):
			doc.shipment_description_code = awb["shipment_description_code"]
		if awb.get("number_of_pieces"):
			doc.number_of_pieces = int(awb["number_of_pieces"])
		if awb.get("weight_code"):
			doc.weight_code = awb["weight_code"]
		if awb.get("weight") and float(awb["weight"]) > 0:
			doc.weight = float(awb["weight"])
		if awb.get("volume_code"):
			self._ensure_code("Volume Code", awb["volume_code"])
			doc.volume_code = awb["volume_code"]
		if awb.get("volume_amount") is not None:
			doc.volume_amount = float(awb["volume_amount"])
		if awb.get("density_indicator"):
			doc.density_indicator = awb["density_indicator"]
		if awb.get("density_group") is not None:
			doc.density_group = int(awb["density_group"])

	def _apply_cvd(self, doc, cvd):
		if cvd.get("charge_code"):
			self._ensure_code("Charge Code", cvd["charge_code"])
			doc.charge_code = cvd["charge_code"]
		if cvd.get("wt_val_prepaid_collect"):
			doc.wt_val_prepaid_collect = cvd["wt_val_prepaid_collect"]
		if cvd.get("other_charges_prepaid_collect"):
			doc.other_charges_prepaid_collect = cvd["other_charges_prepaid_collect"]
		if cvd.get("declared_value_carriage_type"):
			doc.declared_value_carriage_type = cvd["declared_value_carriage_type"]
		if cvd.get("declared_value_carriage_amount") is not None:
			doc.declared_value_carriage_amount = cvd["declared_value_carriage_amount"]
		if cvd.get("declared_value_customs_type"):
			doc.declared_value_customs_type = cvd["declared_value_customs_type"]
		if cvd.get("declared_value_customs_amount") is not None:
			doc.declared_value_customs_amount = cvd["declared_value_customs_amount"]
		if cvd.get("insurance_type"):
			doc.insurance_type = cvd["insurance_type"]
		if cvd.get("insurance_amount") is not None:
			doc.insurance_amount = cvd["insurance_amount"]

	# ---- apply: parties ----

	def _apply_parties(self, doc, data):
		shp = data.get("shipper") or {}
		if shp.get("name"):
			doc.shipper = self._ensure_party(shp, "is_shipper")
		cne = data.get("consignee") or {}
		if cne.get("name"):
			doc.consignee = self._ensure_party(cne, "is_consignee")
		agt = data.get("agent") or {}
		if agt.get("name"):
			doc.agent = self._ensure_party(agt, "is_agent")

		doc.set("also_notify", [])
		for nfy in data.get("also_notify") or []:
			party = self._ensure_party(nfy, "is_notify")
			if not party:
				continue
			row = {"party": party}
			for c in nfy.get("contacts") or []:
				ident = (c.get("identifier") or "").upper()
				if ident == "TE":
					row["telephone"] = (c.get("number") or "")[:25]
				elif ident == "FX":
					row["fax"] = (c.get("number") or "")[:25]
			doc.append("also_notify", row)

	def _ensure_party(self, info, role_field):
		pname = (info.get("name") or "").strip()
		if not pname:
			return None
		existing = frappe.db.get_value("Party", {"party_name": pname, role_field: 1}, "name")
		party = frappe.get_doc("Party", existing) if existing else frappe.new_doc("Party")
		party.party_name = pname[:35]
		setattr(party, role_field, 1)
		if info.get("account"):
			party.account_number = info["account"][:14]
		if info.get("address"):
			party.street_address = info["address"]
		if info.get("place"):
			party.place = info["place"][:17]
		if info.get("state"):
			party.state_province = info["state"][:9]
		if info.get("post_code"):
			party.post_code = info["post_code"][:9]
		country = cargoimp.resolve_country_name(info.get("country"))
		if country:
			party.country = country
		if info.get("iata_code"):
			party.iata_cargo_agent_code = info["iata_code"][:7]
		if info.get("cass_address"):
			party.cass_address = info["cass_address"][:4]
		if info.get("participant_id"):
			party.participant_id = info["participant_id"][:3]
		contacts = [
			c for c in (info.get("contacts") or [])
			if (c.get("identifier") or "").upper() in ("TE", "FX", "TL")
		]
		if contacts:
			party.set("contacts", [])
			for c in contacts:
				party.append("contacts", {
					"contact_identifier": c["identifier"].upper(),
					"contact_number": (c.get("number") or "")[:25],
				})
		party.flags.ignore_permissions = True
		party.save()
		return party.name

	# ---- apply: flights / routing ----

	def _apply_flights(self, doc, flights):
		doc.set("flight_bookings", [])
		for f in flights:
			carrier = self._ensure_airline_by_code(f.get("carrier"))
			if not carrier:
				continue
			doc.append("flight_bookings", {
				"carrier": carrier,
				"flight_number": (f.get("flight_number") or "")[:5],
				"flight_day": f.get("day"),
			})

	def _apply_routing(self, doc, routing_rows):
		doc.set("routing", [])
		for r in routing_rows:
			self._ensure("Airport", {"iata_code": r["airport"]}, r["airport"])
			carrier = self._ensure_airline_by_code(r.get("carrier"))
			doc.append("routing", {
				"sequence": r["sequence"],
				"airport": r["airport"],
				"carrier": carrier,
			})
		if routing_rows:
			r0 = routing_rows[0]
			doc.to_airport1 = r0["airport"]
			doc.by_carrier1 = self._ensure_airline_by_code(r0.get("carrier"))
		if len(routing_rows) >= 2:
			r1 = routing_rows[1]
			doc.to_airport2 = r1["airport"]
			doc.by_carrier2 = self._ensure_airline_by_code(r1.get("carrier"))

	# ---- apply: RTD ----

	def _apply_rate_description(self, doc, rate_lines, goods):
		doc.set("rate_lines", [])
		for r in rate_lines:
			if r.get("rate_class_code"):
				self._ensure_code("Rate Class Code", r["rate_class_code"])
			doc.append("rate_lines", {
				"line_number": r.get("line_number"),
				"number_of_pieces": r.get("number_of_pieces"),
				"rate_combination_point": r.get("rate_combination_point"),
				"gross_weight_code": r.get("gross_weight_code") or "K",
				"gross_weight": r.get("gross_weight"),
				"rate_class_code": r.get("rate_class_code"),
				"commodity_item_number": r.get("commodity_item_number"),
				"uld_rate_class_type": r.get("uld_rate_class_type"),
				"rate_class_percentage": r.get("rate_class_percentage"),
				"chargeable_weight": r.get("chargeable_weight"),
				"rate_charge": r.get("rate_charge"),
				"total": r.get("total"),
			})

		doc.set("goods_details", [])
		for g in goods:
			if g.get("volume_code"):
				self._ensure_code("Volume Code", g["volume_code"])
			if g.get("uld_type"):
				self._ensure_code("ULD Type", g["uld_type"])
			if g.get("measurement_unit"):
				self._ensure_code("Measurement Unit Code", g["measurement_unit"])
			if g.get("service_code"):
				self._ensure_code("Service Code", g["service_code"])
			doc.append("goods_details", {
				"rate_line_number": g.get("rate_line_number"),
				"goods_data_identifier": g.get("goods_data_identifier"),
				"description": g.get("description"),
				"hs_code": g.get("hs_code"),
				"country_of_origin": cargoimp.resolve_country_name(g.get("country_of_origin")),
				"slac": g.get("slac"),
				"volume_code": g.get("volume_code"),
				"volume_amount": g.get("volume_amount"),
				"uld_type": g.get("uld_type"),
				"uld_serial": g.get("uld_serial"),
				"uld_owner": g.get("uld_owner"),
				"measurement_unit": g.get("measurement_unit"),
				"dim_weight_code": g.get("dim_weight_code"),
				"dim_weight": g.get("dim_weight"),
				"dim_length": g.get("dim_length"),
				"dim_width": g.get("dim_width"),
				"dim_height": g.get("dim_height"),
				"dim_pieces": g.get("dim_pieces"),
				"service_code": g.get("service_code"),
			})

	# ---- apply: charges ----

	def _apply_other_charges(self, doc, other_charges):
		doc.set("other_charges", [])
		for o in other_charges:
			code = (o.get("other_charge_code") or "").strip()
			if not code:
				continue
			self._ensure_code("Other Charge Code", code)
			entitlement = (o.get("entitlement_code") or "").strip().upper()
			doc.append("other_charges", {
				"prepaid_collect": o.get("prepaid_collect") or "P",
				"other_charge_code": code,
				"entitlement_code": entitlement if entitlement in ("C", "A") else None,
				"amount": o.get("amount"),
			})

	def _apply_charge_summary(self, doc, charge_summary):
		doc.set("charge_summary", [])
		for c in charge_summary:
			if not c.get("charge_identifier"):
				continue
			doc.append("charge_summary", {
				"settlement": c.get("settlement"),
				"charge_identifier": c["charge_identifier"],
				"amount": c.get("amount"),
			})

	def _apply_cdc(self, doc, cdc):
		if cdc.get("dest_currency"):
			self._ensure_currency(cdc["dest_currency"])
			doc.cc_dest_currency = cdc["dest_currency"]
		if cdc.get("rate_of_exchange") is not None:
			doc.rate_of_exchange = cdc["rate_of_exchange"]
		if cdc.get("cc_charges_dest") is not None:
			doc.cc_charges_dest = cdc["cc_charges_dest"]
		if cdc.get("charges_at_dest") is not None:
			doc.charges_at_dest = cdc["charges_at_dest"]
		if cdc.get("total_collect_charges") is not None:
			doc.total_collect_charges = cdc["total_collect_charges"]

	# ---- apply: SSR / OSI / SPH / ACC ----

	def _apply_simple_tables(self, doc, data):
		doc.set("special_service_requests", [])
		for text in data.get("ssr") or []:
			doc.append("special_service_requests", {"special_service_request": text[:65]})

		doc.set("other_service_info", [])
		for text in data.get("osi") or []:
			doc.append("other_service_info", {"other_service_information": text[:65]})

		doc.set("special_handling", [])
		for code in data.get("special_handling") or []:
			self._ensure_code("Special Handling Code", code)
			doc.append("special_handling", {"special_handling_code": code})

		doc.set("accounting_information", [])
		for row in data.get("accounting") or []:
			ident = (row.get("identifier") or "").strip()
			if not ident:
				continue
			self._ensure_code("Accounting Information Identifier", ident)
			doc.append("accounting_information", {
				"identifier": ident,
				"information": (row.get("information") or "")[:34],
			})

	# ---- apply: certification / execution ----

	def _apply_certification_execution(self, doc, data):
		cer = data.get("certification") or {}
		if cer.get("signature"):
			doc.shippers_certification_signature = cer["signature"][:20]
		isu = data.get("execution") or {}
		if isu.get("issue_date"):
			doc.issue_date = isu["issue_date"]
		if isu.get("issue_place"):
			doc.issue_place = isu["issue_place"][:17]
		if isu.get("signature"):
			doc.carrier_execution_signature = isu["signature"][:20]

	# ---- apply: references / customs / participants ----

	def _apply_references(self, doc, data):
		ref = data.get("sender_reference") or {}
		if ref.get("file_reference"):
			doc.sender_file_reference = ref["file_reference"][:15]
		if ref.get("office_address"):
			doc.sender_office_address = ref["office_address"][:8]
		if ref.get("participant_id"):
			doc.sender_participant_id = ref["participant_id"][:3]
		if ref.get("participant_code"):
			doc.sender_participant_code = ref["participant_code"][:17]

		cor = data.get("customs_origin") or {}
		if cor.get("code"):
			doc.customs_origin_code = cor["code"][:2]

		nom = data.get("nominated_handling") or {}
		if nom.get("name"):
			doc.nominated_handling_name = nom["name"][:35]
		if nom.get("place"):
			doc.nominated_handling_place = nom["place"][:17]

		doc.set("references", [])
		for r in data.get("references") or []:
			doc.append("references", {
				"reference_number": (r.get("reference_number") or "")[:14],
				"supplementary_1": (r.get("supplementary_1") or "")[:12],
				"supplementary_2": (r.get("supplementary_2") or "")[:12],
			})

		doc.set("other_participants", [])
		for p in data.get("other_participants") or []:
			if not p.get("name"):
				continue
			if p.get("airport"):
				self._ensure("Airport", {"iata_code": p["airport"]}, p["airport"])
			doc.append("other_participants", {
				"participant_name": p["name"][:35],
				"office_file_reference": (p.get("office_file_reference") or "")[:15],
				"participant_id": (p.get("participant_id") or "")[:3],
				"participant_code": (p.get("participant_code") or "")[:17],
				"airport": p.get("airport") or None,
			})

		doc.set("oci_customs", [])
		for o in data.get("oci") or []:
			info_id = (o.get("information_identifier") or "").strip()
			customs_id = (o.get("customs_info_identifier") or "").strip()
			country = cargoimp.resolve_country_name(o.get("country"))
			if not (info_id or customs_id or country or o.get("supplementary")):
				continue
			if info_id:
				self._ensure_code("OCI Information Identifier", info_id)
			if customs_id:
				self._ensure_code("Customs Information Identifier", customs_id)
			doc.append("oci_customs", {
				"country": country,
				"information_identifier": info_id or None,
				"customs_info_identifier": customs_id or None,
				"supplementary": (o.get("supplementary") or "")[:35],
			})

	# ---- apply: commission / incentive / agent reference ----

	def _apply_commission_incentive(self, doc, data):
		coi = data.get("commission") or {}
		if coi.get("no_commission_indicator"):
			doc.no_commission_indicator = coi["no_commission_indicator"][:2]
		if coi.get("amount") is not None:
			doc.commission_amount = coi["amount"]
		if coi.get("percentage") is not None:
			doc.commission_percentage = coi["percentage"]

		sii = data.get("sales_incentive") or {}
		if sii.get("amount") is not None:
			doc.sales_incentive_amount = sii["amount"]
		if sii.get("indicator"):
			doc.sales_incentive_indicator = sii["indicator"][:2]

		ard = data.get("agent_reference") or {}
		if ard.get("reference"):
			doc.agent_reference = ard["reference"][:15]

	# ----------------------------------------------------------------- helpers

	def _ensure(self, doctype, values, name):
		if name and not frappe.db.exists(doctype, name):
			d = frappe.new_doc(doctype)
			d.update(values)
			d.flags.ignore_permissions = True
			d.insert()

	def _ensure_code(self, doctype, code):
		"""Ensure a ``field:code`` master row exists (Charge Code, Volume Code, …)."""
		code = (code or "").strip()
		if code and not frappe.db.exists(doctype, code):
			frappe.get_doc({"doctype": doctype, "code": code}).insert(ignore_permissions=True)

	def _ensure_currency(self, code):
		if code and not frappe.db.exists("Currency", code):
			d = frappe.new_doc("Currency")
			d.currency_name = code
			d.enabled = 1
			d.flags.ignore_permissions = True
			d.insert()

	def _ensure_airline_by_code(self, carrier_code):
		"""Resolve an Airline docname from a 2-char carrier code, creating a stub if needed.

		Returns the Airline name (its ``airline_prefix``) so the caller can set a proper
		Link; ``carrier_code`` is then populated naturally by the child table's fetch_from.
		"""
		code = (carrier_code or "").strip().upper()
		if not code:
			return None
		existing = frappe.db.get_value("Airline", {"carrier_code": code}, "name")
		if existing:
			return existing
		if frappe.db.exists("Airline", code):
			if not frappe.db.get_value("Airline", code, "carrier_code"):
				frappe.db.set_value("Airline", code, "carrier_code", code, update_modified=False)
			return code
		d = frappe.new_doc("Airline")
		d.airline_prefix = code
		d.carrier_code = code
		d.flags.ignore_permissions = True
		d.insert()
		return code
