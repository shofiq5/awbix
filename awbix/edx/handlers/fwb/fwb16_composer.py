"""FWB/16 (Air Waybill, Cargo-IMP) outbound composer.

The inverse of ``FWB16Parser``: it reads a ``Shipment`` and emits Cargo-IMP text for every
segment the parser understands, so ``parse(compose(shipment))`` round-trips the full set of
data elements (AWB consignment line, FLT, RTG, SHP/CNE/AGT/NFY, SSR, ACC, CVD, RTD rate +
goods, OTH, PPD/COL, CER, ISU, OSI, CDC, REF, COR, COI, SII, ARD, SPH, NOM, SRI, OPI, OCI).
``verify`` re-parses the output through the parser as a genuine self-check.
"""

import frappe
from frappe.utils import getdate

from awbix.edx.engine.base_composer import BaseComposer
from awbix.edx.handlers.fwb import cargoimp
from awbix.edx.handlers.fwb.fwb16_parser import FWB16Parser

_num = cargoimp.num

_MONTHS = ["", "JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


class FWB16Composer(BaseComposer):
	message_type = "FWB"
	version = "16"

	# ------------------------------------------------------------------ compose

	def compose(self, source_doc) -> str:
		d = source_doc
		self._assert_mandatory(d)
		lines = ["FWB/16", self._awb_line(d)]

		lines += _opt(self._flt_line(d))
		lines += _opt(self._routing_line(d))
		lines += self._party_block(d, "SHP", "shipper")
		lines += self._party_block(d, "CNE", "consignee")
		lines += self._agent_block(d)
		lines += self._text_segment(d, "SSR", "special_service_requests", "special_service_request")
		lines += self._notify_blocks(d)
		lines += self._accounting_lines(d)
		lines += _opt(self._cvd_line(d))
		lines += self._rtd_lines(d)
		lines += self._other_charge_lines(d)
		lines += self._charge_summary_lines(d)
		lines += _opt(self._cer_line(d))
		lines += _opt(self._isu_line(d))
		lines += self._text_segment(d, "OSI", "other_service_info", "other_service_information")
		lines += _opt(self._cdc_line(d))
		lines += _opt(self._ref_line(d))
		lines += _opt(self._cor_line(d))
		lines += _opt(self._coi_line(d))
		lines += _opt(self._sii_line(d))
		lines += _opt(self._ard_line(d))
		lines += _opt(self._sph_line(d))
		lines += _opt(self._nom_line(d))
		lines += self._sri_lines(d)
		lines += self._opi_blocks(d)
		lines += self._oci_lines(d)

		return cargoimp.join(lines)

	# ------------------------------------------------ mandatory-data enforcement
	# The FWB/16 ABNF marks each segment/element as mandatory (bare), optional ([X]) or
	# repeatable (*X / n*mX). Mandatory data that is absent cannot be invented, so the
	# composer refuses to emit a structurally-incomplete message and reports exactly what
	# is missing. Optional segments are emitted only when present; once present, their own
	# mandatory ("conditional") elements are required too.

	def _assert_mandatory(self, d) -> None:
		missing = self._missing_mandatory(d)
		if missing:
			frappe.throw(
				"Cannot compose FWB/16 for {0}: missing mandatory data - {1}".format(
					d.get("name") or "shipment", "; ".join(missing)
				)
			)

	def _missing_mandatory(self, d) -> list[str]:
		m = []
		# AWB consignment detail (incl. mandatory quantity detail)
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
		# Routing - first destination carrier is mandatory
		if not self._first_carrier(d):
			m.append("routing first-destination carrier (RTG)")
		# Shipper / Consignee
		m += self._missing_party(d, "shipper", "shipper (SHP)")
		m += self._missing_party(d, "consignee", "consignee (CNE)")
		# Charge declarations
		if not (d.get("currency") or "").strip():
			m.append("currency (CVD/DE606)")
		# Rate description - at least one line plus nature/quantity of goods (NG/NC)
		if not (d.get("rate_lines") or d.get("goods_details")):
			m.append("rate description lines (RTD)")
		elif not self._has_goods_description(d):
			m.append("nature and quantity of goods (RTD NG/NC, DE709)")
		# Charge summary - at least one of PPD/COL, each carrying the CT total
		if not self._has_charge_total(d):
			m.append("a PPD or COL charge summary total (CT)")
		# Carrier's execution
		if not d.get("issue_date"):
			m.append("issue date (ISU)")
		if not (d.get("issue_place") or "").strip():
			m.append("issue place (ISU)")
		# Sender reference - office message address or participant identification
		if not ((d.get("sender_office_address") or "").strip() or (d.get("sender_participant_id") or "").strip()):
			m.append("sender reference office address or participant id (REF)")
		m += self._missing_conditional(d)
		return m

	def _first_carrier(self, d) -> bool:
		rows = sorted(d.get("routing") or [], key=lambda r: r.get("sequence") or 0)
		if rows:
			return bool((rows[0].get("carrier_code") or rows[0].get("carrier") or "").strip())
		return bool((d.get("by_carrier1") or "").strip())

	def _missing_party(self, d, prefix, label) -> list[str]:
		if not (d.get(f"{prefix}_name") or "").strip():
			return [f"{label} name (DE300)"]
		out = []
		if not (d.get(f"{prefix}_address") or "").strip():
			out.append(f"{label} street address (DE301)")
		if not (d.get(f"{prefix}_place") or "").strip():
			out.append(f"{label} place (DE302)")
		if not cargoimp.resolve_country_code(d.get(f"{prefix}_country")):
			out.append(f"{label} country (DE304)")
		return out

	def _has_goods_description(self, d) -> bool:
		return any(
			(r.get("goods_data_identifier") or "").strip() in ("G", "C")
			for r in d.get("rate_lines") or []
		) or any(
			(g.get("goods_data_identifier") or "").strip() in ("G", "C")
			for g in d.get("goods_details") or []
		)

	def _has_charge_total(self, d) -> bool:
		return any(
			(r.get("charge_identifier") or "").strip() == "CT" and r.get("settlement") in ("Prepaid", "Collect")
			for r in d.get("charge_summary") or []
		)

	def _missing_conditional(self, d) -> list[str]:
		"""Mandatory elements of optional segments that are present in the source."""
		out = []
		# Agent (optional): IATA code (DE311) and place (DE302) are mandatory once present
		if (d.get("agent_name") or "").strip():
			if not (d.get("agent_iata_code") or "").strip():
				out.append("agent IATA code (AGT/DE311)")
			if not (d.get("agent_place") or "").strip():
				out.append("agent place (AGT/DE302)")
		# Also-Notify (optional): street, place and country mandatory per row
		for row in d.get("also_notify") or []:
			if not (row.get("notify_name") or "").strip():
				continue
			if not (row.get("street_address") or "").strip():
				out.append("also-notify street address (NFY/DE301)")
			if not (row.get("place") or "").strip():
				out.append("also-notify place (NFY/DE302)")
			if not cargoimp.resolve_country_code(row.get("country")):
				out.append("also-notify country (NFY/DE304)")
		# CDC (optional): rate of exchange mandatory once a destination currency is given
		if (d.get("cc_dest_currency") or "").strip() and not d.get("rate_of_exchange"):
			out.append("CDC rate of exchange (DE607)")
		# NOM (optional): place mandatory once a name is given
		if (d.get("nominated_handling_name") or "").strip() and not (d.get("nominated_handling_place") or "").strip():
			out.append("nominated handling party place (NOM/DE302)")
		# OPI (optional, repeatable): participant identifier mandatory per row
		for p in d.get("other_participants") or []:
			if (p.get("participant_name") or "").strip() and not (p.get("participant_id") or "").strip():
				out.append("other-participant identifier (OPI/DE319)")
		return out

	# ------------------------------------------------------------ AWB / FLT / RTG

	def _awb_line(self, doc) -> str:
		prefix = (doc.get("airline_prefix") or "").strip()
		serial = (doc.get("awb_serial_number") or "").strip()
		origin = (doc.get("origin") or "").strip().upper()
		dest = (doc.get("destination") or "").strip().upper()
		line = f"{prefix}-{serial}{origin}{dest}"

		pieces = doc.get("number_of_pieces")
		weight = doc.get("weight")
		if pieces and weight:
			desc = (doc.get("shipment_description_code") or "T").strip() or "T"
			weight_code = (doc.get("weight_code") or "K").strip()
			line += f"/{desc}{int(pieces)}{weight_code}{_num(weight)}"
			if doc.get("density_indicator") and doc.get("density_group"):
				line += f"DG{int(doc.get('density_group'))}"
			elif doc.get("volume_code") and doc.get("volume_amount"):
				line += f"{doc.get('volume_code')}{_num(doc.get('volume_amount'))}"
		return line

	def _flt_line(self, doc) -> str:
		tokens = []
		for row in (doc.get("flight_bookings") or [])[:2]:
			code = (row.get("carrier_code") or row.get("carrier") or "").strip().upper()
			number = (row.get("flight_number") or "").strip()
			day = row.get("flight_day")
			if code and number:
				tokens.append(f"{code}{number}")
				tokens.append(f"{int(day):02d}" if day else "")
		return "FLT/" + "/".join(tokens) if tokens else ""

	def _routing_line(self, doc) -> str:
		rows = sorted(doc.get("routing") or [], key=lambda r: r.get("sequence") or 0)
		tokens = []
		for r in rows:
			airport = (r.get("airport") or "").strip().upper()
			if airport:
				tokens.append(airport + (r.get("carrier_code") or "").strip().upper())
		if not tokens:
			a1 = (doc.get("to_airport1") or "").strip().upper()
			if a1:
				tokens.append(a1 + (doc.get("by_carrier1") or "").strip().upper())
			a2 = (doc.get("to_airport2") or "").strip().upper()
			if a2:
				tokens.append(a2 + (doc.get("by_carrier2") or "").strip().upper())
		# ABNF: RTG_FirstDestinationCarrier *2RTG_OnwardDestinationCarrier -> at most 3 entries.
		tokens = tokens[:3]
		return "RTG/" + "/".join(tokens) if tokens else ""

	# ------------------------------------------------------------ parties

	def _party_block(self, doc, code, prefix) -> list[str]:
		name = (doc.get(f"{prefix}_name") or "").strip()
		if not name:
			return []
		account = (doc.get(f"{prefix}_account") or "").strip()
		header = f"{code}/{account}" if account else code
		lines = [header, "/" + name]

		address = (doc.get(f"{prefix}_address") or "").strip()
		place = (doc.get(f"{prefix}_place") or "").strip()
		state = (doc.get(f"{prefix}_state") or "").strip()
		iso = cargoimp.resolve_country_code(doc.get(f"{prefix}_country"))
		post_code = (doc.get(f"{prefix}_post_code") or "").strip()
		contacts = self._party_contacts(doc, prefix)

		# Positional continuation lines (ABNF): name / street / place[/state] / country[/post]
		if address or place or iso or contacts:
			lines.append("/" + address)
		if place or iso or contacts:
			lines.append("/" + place + (f"/{state}" if state else ""))
		if iso or contacts:
			lines.append("/" + iso + (f"/{post_code}" if post_code else ""))
		for ident, number in contacts:
			lines.append(f"/{ident}/{number}")
		return lines

	def _party_contacts(self, doc, prefix) -> list:
		"""Contact (identifier, number) pairs from the linked Party, when available."""
		link = doc.get(prefix)
		if not link:
			return []
		try:
			party = frappe.get_doc("Party", link)
		except Exception:
			return []
		out = []
		for c in party.get("contacts") or []:
			ident = (c.get("contact_identifier") or "").strip()
			number = (c.get("contact_number") or "").strip()
			if ident and number:
				out.append((ident, number))
		return out

	def _agent_block(self, doc) -> list[str]:
		name = (doc.get("agent_name") or "").strip()
		if not name:
			return []
		account = (doc.get("agent_account") or "").strip()
		iata = (doc.get("agent_iata_code") or "").strip()
		cass = (doc.get("agent_cass_address") or "").strip()
		participant = (doc.get("agent_participant_id") or "").strip()

		header = f"AGT/{account}/{iata}"
		if participant:
			header += f"/{cass}/{participant}"
		elif cass:
			header += f"/{cass}"
		lines = [header, "/" + name]
		place = (doc.get("agent_place") or "").strip()
		if place:
			lines.append("/" + place)
		return lines

	def _notify_blocks(self, doc) -> list[str]:
		lines = []
		# ABNF: [AlsoNotify] is optional and single - emit at most one NFY.
		for row in (doc.get("also_notify") or [])[:1]:
			name = (row.get("notify_name") or "").strip()
			if not name:
				continue
			# ABNF: NFY identifier and name share the first physical line (no CRLF between them).
			block = [f"NFY/{name}"]
			address = (row.get("street_address") or "").strip()
			place = (row.get("place") or "").strip()
			state = (row.get("state_province") or "").strip()
			iso = cargoimp.resolve_country_code(row.get("country"))
			post_code = (row.get("post_code") or "").strip()
			contacts = []
			if (row.get("telephone") or "").strip():
				contacts.append(("TE", row["telephone"].strip()))
			if (row.get("fax") or "").strip():
				contacts.append(("FX", row["fax"].strip()))

			if address or place or iso or contacts:
				block.append("/" + address)
			if place or iso or contacts:
				block.append("/" + place + (f"/{state}" if state else ""))
			if iso or contacts:
				block.append("/" + iso + (f"/{post_code}" if post_code else ""))
			for ident, number in contacts:
				block.append(f"/{ident}/{number}")
			lines += block
		return lines

	# ------------------------------------------------------------ SSR / OSI / ACC / SPH

	def _text_segment(self, doc, code, table, field) -> list[str]:
		values = [(r.get(field) or "").strip() for r in (doc.get(table) or [])]
		values = [v for v in values if v][:3]
		if not values:
			return []
		# ABNF: identifier immediately followed by /value CRLF (no line-break between them).
		return [f"{code}/{values[0]}"] + ["/" + v for v in values[1:]]

	def _accounting_lines(self, doc) -> list[str]:
		rows = doc.get("accounting_information") or []
		out = []
		for r in rows[:6]:
			ident = (r.get("identifier") or "").strip()
			if not ident:
				continue
			out.append(f"/{ident}/{(r.get('information') or '').strip()}")
		if not out:
			return []
		# ABNF: ACC immediately followed by /identifier/info CRLF (no line-break before first detail).
		return ["ACC" + out[0]] + out[1:]

	def _sph_line(self, doc) -> str:
		codes = [(r.get("special_handling_code") or "").strip() for r in (doc.get("special_handling") or [])]
		codes = [c for c in codes if c][:9]
		return "SPH/" + "/".join(codes) if codes else ""

	# ------------------------------------------------------------ CVD

	def _cvd_line(self, doc) -> str:
		currency = (doc.get("currency") or "").strip()
		if not currency:
			return ""
		charge_code = (doc.get("charge_code") or "").strip()
		wt_pc = (doc.get("wt_val_prepaid_collect") or "P").strip()
		oth_pc = (doc.get("other_charges_prepaid_collect") or "P").strip()
		carriage = self._dv(doc, "declared_value_carriage_type", "declared_value_carriage_amount", "NVD")
		customs = self._dv(doc, "declared_value_customs_type", "declared_value_customs_amount", "NCV")
		insurance = self._dv(doc, "insurance_type", "insurance_amount", "XXX")
		return f"CVD/{currency}/{charge_code}/{wt_pc}{oth_pc}/{carriage}/{customs}/{insurance}"

	def _dv(self, doc, type_field, amount_field, nil_code) -> str:
		t = (doc.get(type_field) or nil_code).strip()
		if t == "Value":
			return _num(doc.get(amount_field) or 0)
		return t if t in ("NVD", "NCV", "XXX") else nil_code

	# ------------------------------------------------------------ RTD

	def _rtd_lines(self, doc) -> list[str]:
		# ABNF: RateDescription = RTD 1*11(...) -> at most 11 charge lines.
		rate_lines = sorted(doc.get("rate_lines") or [], key=lambda r: r.get("line_number") or 0)[:11]
		goods = doc.get("goods_details") or []
		if not rate_lines and not goods:
			return []

		goods_by_line = {}
		for g in goods:
			goods_by_line.setdefault(g.get("rate_line_number") or 0, []).append(g)

		lines = []
		for i, r in enumerate(rate_lines):
			ln = r.get("line_number") or 0
			rate_line_str = self._rate_line(ln, r)
			if i == 0:
				# First rate line: concatenate with RTD identifier (ABNF: RTD and first ChargeLineCount on same line)
				lines.append("RTD" + rate_line_str)
			else:
				# Subsequent rate lines: add as separate lines
				lines.append(rate_line_str)
			# Emit NG/NC line from the rate line row itself (goods_data_identifier + description).
			inline = self._goods_line_from_rate(ln, r)
			if inline:
				lines.append(inline)
				# If rate_line has goods description, skip goods_by_line for this line to avoid duplicates
				goods_by_line.pop(ln, None)
			else:
				lines += _opt_many(self._goods_line(ln, g) for g in goods_by_line.pop(ln, []))
		# goods whose rate line wasn't emitted (orphans) still get included
		for ln, rows in goods_by_line.items():
			lines += _opt_many(self._goods_line(ln, g) for g in rows)
		return lines

	def _goods_line_from_rate(self, ln, r) -> str:
		"""Emit the /NG or /NC line stored directly on a Shipment Rate Line row.

		This is a SecondLine for a rate line, so per ABNF it does not include the line number.
		"""
		ident = (r.get("goods_data_identifier") or "").strip()
		if ident not in ("G", "C"):
			return ""
		desc = (r.get("description") or "").strip()
		return f"/N{ident}/{desc}"

	def _rate_line(self, ln, r) -> str:
		out = f"/{ln}"
		if r.get("number_of_pieces"):
			out += f"/P{int(r.get('number_of_pieces'))}"
		elif r.get("rate_combination_point"):
			out += f"/P{r.get('rate_combination_point')}"
		if r.get("gross_weight"):
			out += f"/{(r.get('gross_weight_code') or 'K').strip()}{_num(r.get('gross_weight'))}"
		if r.get("rate_class_code"):
			out += f"/C{r.get('rate_class_code')}"
		if r.get("commodity_item_number"):
			out += f"/S{r.get('commodity_item_number')}"
		elif r.get("uld_rate_class_type"):
			out += f"/S{r.get('uld_rate_class_type')}"
		elif r.get("rate_class_percentage") and r.get("rate_class_code"):
			out += f"/S{r.get('rate_class_code')}{int(r.get('rate_class_percentage'))}"
		if r.get("chargeable_weight"):
			out += f"/W{_num(r.get('chargeable_weight'))}"
		if r.get("rate_charge"):
			out += f"/R{_num(r.get('rate_charge'))}"
		if r.get("total"):
			out += f"/T{_num(r.get('total'))}"
		return out

	def _goods_line(self, ln, g) -> str:
		ident = (g.get("goods_data_identifier") or "").strip()
		service = (g.get("service_code") or "").strip()
		if not ident:
			# A second-line carrying only a service code (DE505).
			return f"/{ln}/{service}" if service else ""
		head = f"/{ln}/N{ident}"
		line = self._goods_body(head, ident, g)
		if service:
			line += f"/{service}"
		return line

	def _goods_body(self, head, ident, g) -> str:
		if ident in ("G", "C"):
			return f"{head}/{(g.get('description') or '').strip()}"
		if ident == "D":
			weight = ""
			if g.get("dim_weight"):
				weight = f"{(g.get('dim_weight_code') or 'K').strip()}{_num(g.get('dim_weight'))}"
			if g.get("dim_length") and g.get("dim_width") and g.get("dim_height"):
				unit = (g.get("measurement_unit") or "CMT").strip()
				dims = f"{unit}{_num(g.get('dim_length'))}-{_num(g.get('dim_width'))}-{_num(g.get('dim_height'))}"
				pieces = int(g.get("dim_pieces")) if g.get("dim_pieces") else ""
				return f"{head}/{weight}/{dims}/{pieces}"
			return f"{head}/{weight}/NDA"
		if ident == "V":
			return f"{head}/{(g.get('volume_code') or '').strip()}{_num(g.get('volume_amount') or 0)}"
		if ident == "U":
			uld = (g.get("uld_type") or "").strip() + (g.get("uld_serial") or "").strip()
			uld += (g.get("uld_owner") or "").strip()
			return f"{head}/{uld}"
		if ident == "S":
			return f"{head}/{int(g.get('slac')) if g.get('slac') else ''}"
		if ident == "H":
			return f"{head}/{(g.get('hs_code') or '').strip()}"
		if ident == "O":
			return f"{head}/{cargoimp.resolve_country_code(g.get('country_of_origin'))}"
		return f"{head}/"

	# ------------------------------------------------------------ OTH / PPD / COL

	def _other_charge_lines(self, doc) -> list[str]:
		rows = doc.get("other_charges") or []
		if not rows:
			return []
		lines = []
		current_pc = None
		current_charges = []
		for r in rows:
			code = (r.get("other_charge_code") or "").strip()
			if len(code) < 3:
				continue
			pc = (r.get("prepaid_collect") or "P").strip()
			amount = _num(r.get("amount") or 0)
			# If PC changed or we have 3 charges, finalize current line
			if (pc != current_pc or len(current_charges) >= 3) and current_charges:
				line = f"/{current_pc}/" + "".join(current_charges)
				if not lines:
					line = "OTH" + line
				lines.append(line)
				current_charges = []
			current_pc = pc
			current_charges.append(f"{code}{amount}")
		# Add final line
		if current_charges:
			line = f"/{current_pc}/" + "".join(current_charges)
			if not lines:
				line = "OTH" + line
			lines.append(line)
		return lines

	def _charge_summary_lines(self, doc) -> list[str]:
		rows = doc.get("charge_summary") or []
		groups = {"Prepaid": ("PPD", []), "Collect": ("COL", [])}
		order = ["WT", "VC", "TX", "OA", "OC", "CT"]
		for r in rows:
			settlement = r.get("settlement")
			ident = (r.get("charge_identifier") or "").strip()
			if settlement in groups and ident:
				groups[settlement][1].append((ident, r.get("amount")))

		lines = []
		for settlement in ("Prepaid", "Collect"):
			code, items = groups[settlement]
			if not items:
				continue
			items.sort(key=lambda x: order.index(x[0]) if x[0] in order else 99)
			first = [i for i in items if i[0] in ("WT", "VC", "TX")]
			second = [i for i in items if i[0] in ("OA", "OC", "CT")]
			# ABNF: PPD/COL identifier on same line as WT/VC/TX (line 1); OA/OC/CT on line 2.
			first_line = code + "".join(f"/{i}{_num(a)}" for i, a in first)
			block = [first_line]
			if second:
				block.append("".join(f"/{i}{_num(a)}" for i, a in second))
			lines += block
		return lines

	# ------------------------------------------------------------ CER / ISU / CDC

	def _cer_line(self, doc) -> str:
		sig = (doc.get("shippers_certification_signature") or "").strip()
		return f"CER/{sig}" if sig else ""

	def _isu_line(self, doc) -> str:
		date = doc.get("issue_date")
		place = (doc.get("issue_place") or "").strip()
		if not date or not place:
			return ""
		dt = getdate(date)
		date_token = f"{dt.day:02d}{_MONTHS[dt.month]}{dt.year % 100:02d}"
		line = f"ISU/{date_token}/{place}"
		sig = (doc.get("carrier_execution_signature") or "").strip()
		if sig:
			line += f"/{sig}"
		return line

	def _cdc_line(self, doc) -> str:
		currency = (doc.get("cc_dest_currency") or "").strip()
		rate = doc.get("rate_of_exchange")
		if not currency or not rate:
			return ""
		return (
			f"CDC/{currency}{_num(rate)}"
			f"/{_num(doc.get('cc_charges_dest') or 0)}"
			f"/{_num(doc.get('charges_at_dest') or 0)}"
			f"/{_num(doc.get('total_collect_charges') or 0)}"
		)

	# ------------------------------------------------------------ REF / COR / NOM

	def _ref_line(self, doc) -> str:
		office = (doc.get("sender_office_address") or "").strip()
		file_ref = (doc.get("sender_file_reference") or "").strip()
		pid = (doc.get("sender_participant_id") or "").strip()
		pcode = (doc.get("sender_participant_code") or "").strip()
		airport = (doc.get("sender_airport") or "").strip()
		if office:
			return f"REF/{office}" + (f"/{file_ref}" if file_ref else "")
		if pid or pcode or file_ref:
			line = f"REF//{file_ref}"
			if pid or pcode:
				line += f"/{pid}/{pcode}"
				# ABNF: airport is mandatory in participant form; fallback to origin if not set
				if not airport:
					airport = (doc.get("origin") or "").strip()
				if airport:
					line += f"/{airport}"
			elif airport:
				line += f"/{airport}"
			return line
		return ""

	def _cor_line(self, doc) -> str:
		code = (doc.get("customs_origin_code") or "").strip()
		return f"COR/{code}" if code else ""

	def _nom_line(self, doc) -> str:
		name = (doc.get("nominated_handling_name") or "").strip()
		if not name:
			return ""
		place = (doc.get("nominated_handling_place") or "").strip()
		return f"NOM/{name}/{place}"

	# ------------------------------------------------------------ COI / SII / ARD

	def _coi_line(self, doc) -> str:
		if doc.get("commission_percentage"):
			return f"COI///{_num(doc.get('commission_percentage'))}"
		if doc.get("commission_amount"):
			return f"COI//{_num(doc.get('commission_amount'))}"
		indicator = (doc.get("no_commission_indicator") or "").strip()
		return f"COI/{indicator}" if indicator else ""

	def _sii_line(self, doc) -> str:
		if not doc.get("sales_incentive_amount"):
			return ""
		line = f"SII/{_num(doc.get('sales_incentive_amount'))}"
		indicator = (doc.get("sales_incentive_indicator") or "").strip()
		if indicator:
			line += f"/{indicator}"
		return line

	def _ard_line(self, doc) -> str:
		ref = (doc.get("agent_reference") or "").strip()
		return f"ARD/{ref}" if ref else ""

	# ------------------------------------------------------------ SRI / OPI / OCI

	def _sri_lines(self, doc) -> list[str]:
		lines = []
		# ABNF: [ShipmentReferenceInformation] is optional and single - emit at most one SRI.
		for r in (doc.get("references") or [])[:1]:
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
			lines.append(line)
		return lines

	def _opi_blocks(self, doc) -> list[str]:
		lines = []
		for p in doc.get("other_participants") or []:
			name = (p.get("participant_name") or "").strip()
			if not name:
				continue
			file_ref = (p.get("office_file_reference") or "").strip()
			pid = (p.get("participant_id") or "").strip()
			pcode = (p.get("participant_code") or "").strip()
			airport = (p.get("airport") or "").strip()
			lines.append(f"OPI/{name}")
			lines.append(f"//{file_ref}/{pid}/{pcode}/{airport}")
		return lines

	def _oci_lines(self, doc) -> list[str]:
		rows = doc.get("oci_customs") or []
		out = []
		for r in rows:
			iso = cargoimp.resolve_country_code(r.get("country"))
			info_id = (r.get("information_identifier") or "").strip()
			customs_id = (r.get("customs_info_identifier") or "").strip()
			supp = (r.get("supplementary") or "").strip()
			out.append(f"/{iso}/{info_id}/{customs_id}/{supp}")
		if not out:
			return []
		return ["OCI" + out[0]] + out[1:]

	# ------------------------------------------------------------------- verify

	def verify(self, raw: str) -> list[dict]:
		from awbix.edx.handlers.fwb.fwb16_validator import FWBABNFValidator

		parser = FWB16Parser()
		parser_issues = parser.validate(parser.parse(raw))
		validator = FWBABNFValidator()
		structural_issues = validator.validate(raw)
		existing_codes = {i["code"] for i in parser_issues}
		return parser_issues + [i for i in structural_issues if i["code"] not in existing_codes]


def _opt(line: str) -> list[str]:
	"""Wrap an optional single-line segment: ``[line]`` when non-empty, else ``[]``."""
	return [line] if line else []


def _opt_many(lines) -> list[str]:
	"""Keep only the non-empty lines from an iterable."""
	return [ln for ln in lines if ln]
