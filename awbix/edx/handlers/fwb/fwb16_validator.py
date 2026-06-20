"""FWB/16 enterprise message validator (ABNF-driven).

Validates an FWB/16 Cargo-IMP message data-element by data-element against the ABNF
grammar in ``awbix/edx/.claude/fwb_abnf.txt``. Every element is checked in message
order and assigned a hierarchical reference: section ``1`` is the Standard Message
Identification, section ``2`` the AWB Consignment Detail, then one section per segment
(``3.1``, ``3.2`` …). ``validate()`` returns the failing checks (errors only) so it
plugs into the existing pipeline ``issues`` contract; ``validate_report()`` /
``format_report()`` expose the full numbered enumeration (PASS and FAIL) for an
enterprise-style validation report.

The grammar treats slants (``/``) as field separators and concatenates fixed-width
elements (e.g. ``157-42781966DACHAM`` = prefix-serial+origin+destination), so the
validator splits on slants where the grammar does and parses concatenated runs with
explicit character rules where it does not.
"""

import re

from awbix.edx.handlers.fwb import cargoimp

_MONTHS = {
	"JAN", "FEB", "MAR", "APR", "MAY", "JUN",
	"JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
}

# ABNF data-element type specifications -> (full-match regex, human description).
# Decimal specs ("1*NDecimal") are handled separately by ``_is_decimal``.
_SPEC = {
	"1Alpha": (r"[A-Z]", "1 letter"),
	"2Alpha": (r"[A-Z]{2}", "2 letters"),
	"3Alpha": (r"[A-Z]{3}", "3 letters"),
	"1*2Alpha": (r"[A-Z]{1,2}", "1-2 letters"),
	"2Numeric": (r"[0-9]{2}", "2 numeric digits"),
	"3Numeric": (r"[0-9]{3}", "3 numeric digits"),
	"4Numeric": (r"[0-9]{4}", "4 numeric digits"),
	"7Numeric": (r"[0-9]{7}", "7 numeric digits"),
	"8Numeric": (r"[0-9]{8}", "8 numeric digits"),
	"1*2Numeric": (r"[0-9]{1,2}", "1-2 numeric digits"),
	"1*3Numeric": (r"[0-9]{1,3}", "1-3 numeric digits"),
	"1*4Numeric": (r"[0-9]{1,4}", "1-4 numeric digits"),
	"1*5Numeric": (r"[0-9]{1,5}", "1-5 numeric digits"),
	"4*7Numeric": (r"[0-9]{4,7}", "4-7 numeric digits"),
	"2Mixed": (r"[A-Z0-9]{2}", "2 alphanumeric characters"),
	"1*2Mixed": (r"[A-Z0-9]{1,2}", "1-2 alphanumeric characters"),
	"1*3Mixed": (r"[A-Z0-9]{1,3}", "1-3 alphanumeric characters"),
	"1*17Mixed": (r"[A-Z0-9]{1,17}", "1-17 alphanumeric characters"),
	"1*25Mixed": (r"[A-Z0-9]{1,25}", "1-25 alphanumeric characters"),
	"6*18Mixed": (r"[A-Z0-9]{6,18}", "6-18 alphanumeric characters"),
	"1*9Text": (r"[A-Z0-9 .\-]{1,9}", "1-9 text characters"),
	"1*12Text": (r"[A-Z0-9 .\-]{1,12}", "1-12 text characters"),
	"1*14Text": (r"[A-Z0-9 .\-]{1,14}", "1-14 text characters"),
	"1*15Text": (r"[A-Z0-9 .\-]{1,15}", "1-15 text characters"),
	"1*17Text": (r"[A-Z0-9 .\-]{1,17}", "1-17 text characters"),
	"1*20Text": (r"[A-Z0-9 .\-]{1,20}", "1-20 text characters"),
	"1*34Text": (r"[A-Z0-9 .\-]{1,34}", "1-34 text characters"),
	"1*35Text": (r"[A-Z0-9 .\-]{1,35}", "1-35 text characters"),
	"1*65Text": (r"[A-Z0-9 .\-]{1,65}", "1-65 text characters"),
}


class FWBABNFValidator:
	"""Validate an FWB/16 message data-element by data-element against the ABNF grammar."""

	# code, display name, mandatory?, validator method name. Excludes the message id
	# (section 1) and AWB consignment detail (section 2), which are always validated.
	# PPD/COL are individually optional here; the "at least one" rule is enforced
	# separately after the sweep.
	_ORDER = [
		("FLT", "Flight Bookings", False, "_v_flt"),
		("RTG", "Routing", True, "_v_rtg"),
		("SHP", "Shipper", True, "_v_shp"),
		("CNE", "Consignee", True, "_v_cne"),
		("AGT", "Agent", False, "_v_agt"),
		("SSR", "Special Service Request", False, "_v_ssr"),
		("NFY", "Also Notify", False, "_v_nfy"),
		("ACC", "Accounting Information", False, "_v_acc"),
		("CVD", "Charge Declarations", True, "_v_cvd"),
		("RTD", "Rate Description", True, "_v_rtd"),
		("OTH", "Other Charges", False, "_v_oth"),
		("PPD", "Prepaid Charge Summary", False, "_v_ppd"),
		("COL", "Collect Charge Summary", False, "_v_col"),
		("CER", "Shipper's Certification", False, "_v_cer"),
		("ISU", "Carrier's Execution", True, "_v_isu"),
		("OSI", "Other Service Information", False, "_v_osi"),
		("CDC", "CC Charges in Destination Currency", False, "_v_cdc"),
		("REF", "Sender Reference", True, "_v_ref"),
		("COR", "Customs Origin", False, "_v_cor"),
		("COI", "Commission Information", False, "_v_coi"),
		("SII", "Sales Incentive Information", False, "_v_sii"),
		("ARD", "Agent Reference Data", False, "_v_ard"),
		("SPH", "Special Handling Details", False, "_v_sph"),
		("NOM", "Nominated Handling Party", False, "_v_nom"),
		("SRI", "Shipment Reference Information", False, "_v_sri"),
		("OPI", "Other Participant Information", False, "_v_opi"),
		("OCI", "Other Customs Information", False, "_v_oci"),
	]

	def __init__(self):
		self.checks: list[dict] = []
		self.tok: dict = {}
		self._sec = 0
		self._item = 0
		self._cur = ""
		self._rtd_goods_desc = False

	# ------------------------------------------------------------------ public API

	def validate(self, raw: str) -> list[dict]:
		"""Run every check and return the failing ones (errors only)."""
		self.validate_report(raw)
		return [self._violation(c) for c in self.checks if not c["ok"]]

	def validate_report(self, raw: str) -> list[dict]:
		"""Run every check and return the full numbered enumeration (PASS and FAIL)."""
		self.checks = []
		self._sec = 0
		self._item = 0

		if not raw or not raw.strip():
			self._section("Standard Message Identification")
			self._record(
				"StandardMessageIdentification", "", False, "Message is empty",
				field="StandardMessageIdentification", code="MSG_EMPTY",
			)
			return self.checks

		self.tok = cargoimp.tokenize(raw)
		self._run_all()
		return self.checks

	def format_report(self, raw: str | None = None) -> str:
		"""Human-readable numbered report. Re-validates when ``raw`` is given."""
		if raw is not None:
			self.validate_report(raw)
		lines: list[str] = []
		current_section = None
		for c in self.checks:
			section_no = c["ref"].split(".")[0]
			if section_no != current_section:
				current_section = section_no
				lines.append(f"\n{section_no}. {c['segment']}")
			status = "PASS" if c["ok"] else "FAIL"
			text = f"  {c['ref']:<6} [{status}] {c['element']} = {c['value']!r}"
			if not c["ok"]:
				text += f"\n          -> {c['message']}"
			lines.append(text)
		fails = sum(1 for c in self.checks if not c["ok"])
		lines.append(f"\n{len(self.checks)} element(s) checked, {fails} violation(s).")
		return "\n".join(lines).lstrip("\n")

	# ------------------------------------------------------------------ orchestration

	def _run_all(self) -> None:
		self._section("Standard Message Identification")
		self._v_msgid()

		self._section("AWB Consignment Detail")
		self._v_awb()

		for code, name, mandatory, method in self._ORDER:
			segs = cargoimp.by_code(self.tok, code)
			if not segs:
				if mandatory:
					self._section(name)
					self._record(
						code, "", False,
						f"Mandatory segment '{code}' ({name}) is missing",
						field=code, code=f"{code}_MISSING",
					)
				continue
			fn = getattr(self, method)
			for seg in segs:
				self._section(name)
				try:
					fn(seg)
				except Exception as exc:  # never let one bad segment abort the whole report
					self._record(code, "", False, f"{name} could not be validated: {exc}", field=code)

		if not cargoimp.by_code(self.tok, "PPD") and not cargoimp.by_code(self.tok, "COL"):
			self._section("Charge Summary (PPD/COL)")
			self._record(
				"PPD/COL", "", False,
				"At least one of PPD or COL charge summary is mandatory but both are missing",
				field="PPD/COL", code="CHARGE_SUMMARY_MISSING",
			)

		self._check_order()

	def _check_order(self) -> None:
		canon = {code: i for i, (code, _n, _m, _f) in enumerate(self._ORDER)}
		seen_max = -1
		flagged = False
		for seg in self.tok.get("segments", []):
			code = seg.get("code")
			if code not in canon:
				continue
			idx = canon[code]
			if idx < seen_max:
				if not flagged:
					self._section("Segment Sequence")
					flagged = True
				self._record(
					code, code, False,
					f"Segment '{code}' appears out of the FWB/16 canonical order",
					field=code, code="ORDER",
				)
			else:
				seen_max = idx

	# ------------------------------------------------------------------ section 1 / 2

	def _v_msgid(self) -> None:
		mid = self.tok.get("message_id") or ""
		self._record(
			"DE101_StandardMessageIdentifier", mid, mid == "FWB/16",
			f"First line must be exactly 'FWB/16', got '{mid}'",
			field="StandardMessageIdentification", code="MSGID",
		)

	def _v_awb(self) -> None:
		line = self.tok.get("awb_line") or ""
		if not line:
			self._record(
				"AWBConsignmentDetail", "", False, "AWB consignment detail line is missing",
				field="AWBConsignmentDetail",
			)
			return
		if "-" not in line:
			self._record(
				"AWBIdentification", line, False,
				"AWB identification must contain a hyphen between airline prefix and serial number",
				field="AWBIdentification",
			)
			return

		id_part, _, after = line.partition("-")
		self._record(
			"DE112_AirlinePrefix", id_part, bool(re.fullmatch(r"\d{3}", id_part)),
			f"Airline prefix (DE112) must be 3 numeric digits, got '{id_part}'",
			field="DE112_AirlinePrefix",
		)

		head, slant, qty = after.partition("/")
		serial, origin, dest, extra = head[:8], head[8:11], head[11:14], head[14:]

		serial_ok = bool(re.fullmatch(r"\d{8}", serial))
		self._record(
			"DE113_AWBSerialNumber", serial, serial_ok,
			f"AWB serial number (DE113) must be 8 numeric digits, got '{serial}'",
			field="DE113_AWBSerialNumber",
		)
		if serial_ok:
			expected = int(serial[:7]) % 7
			self._record(
				"DE113_AWBSerialNumber", serial, expected == int(serial[7]),
				f"Check digit invalid: expected {expected} (serial digits 1-7 modulus 7), got {serial[7]}",
				field="DE113_AWBSerialNumber", code="AWB_CHECKDIGIT",
			)

		self._de("DE313_AirportCityCode", origin, "3Alpha", "Origin airport/city code", field="AWBOrigin")
		self._de(
			"DE313_AirportCityCode", dest, "3Alpha", "Destination airport/city code", field="AWBDestination"
		)
		if origin and dest:
			self._record(
				"AWBOriginAndDestination", f"{origin}{dest}", origin != dest,
				"Origin and destination airports are identical",
				field="AWBOriginAndDestination", code="ROUTE",
			)
		if extra:
			self._record(
				"AWBOriginAndDestination", extra, False,
				f"Unexpected characters after origin/destination: '{extra}'",
				field="AWBOriginAndDestination",
			)

		if not slant:
			self._record(
				"QuantityDetail", "", False, "Quantity detail (/T...) is missing", field="QuantityDetail"
			)
			return
		self._v_quantity(qty)

	def _v_quantity(self, qty: str) -> None:
		if not qty:
			self._record("QuantityDetail", "", False, "Quantity detail is empty", field="QuantityDetail")
			return

		code = qty[:1]
		self._record(
			"DE703_ShipmentDescriptionCode", code, code in ("T", "P"),
			f"Shipment description code (DE703) must be 'T' or 'P', got '{code}'",
			field="DE703_ShipmentDescriptionCode",
		)
		rest = qty[1:]

		m = re.match(r"\d{1,4}", rest)
		pieces = m.group(0) if m else ""
		self._record(
			"DE701_NumberOfPieces", pieces, bool(pieces),
			f"Number of pieces (DE701) must be 1-4 numeric digits, got '{pieces}'",
			field="DE701_NumberOfPieces",
		)
		rest = rest[len(pieces):]

		wc = rest[:1]
		self._record(
			"DE601_WeightCode", wc, wc in ("K", "L"),
			f"Weight code (DE601) must be 'K' or 'L', got '{wc}'",
			field="DE601_WeightCode",
		)
		rest = rest[1:]

		m = re.match(r"[0-9.]+", rest)
		weight = m.group(0) if m else ""
		self._record(
			"DE600_Weight", weight, self._is_decimal(weight, 7),
			f"Weight (DE600) must be a decimal of up to 7 characters, got '{weight}'",
			field="DE600_Weight",
		)
		rest = rest[len(weight):]

		if not rest:
			return
		if rest.startswith("DG"):
			dg = rest[2:]
			self._record(
				"DE602_DensityGroup", dg, bool(re.fullmatch(r"\d{1,2}", dg)),
				f"Density group (DE602) must be 1-2 numeric digits, got '{dg}'",
				field="DE602_DensityGroup",
			)
		else:
			m = re.fullmatch(r"([A-Z]{2})([0-9.]+)", rest)
			if m:
				self._de("DE604_VolumeCode", m.group(1), "2Alpha", "Volume code")
				self._record(
					"DE500_VolumeAmount", m.group(2), self._is_decimal(m.group(2), 9),
					f"Volume amount (DE500) must be a decimal of up to 9 characters, got '{m.group(2)}'",
					field="DE500_VolumeAmount",
				)
			else:
				self._record(
					"VolumeDetail", rest, False,
					f"Volume detail must be a 2-letter code + amount (or DGnn), got '{rest}'",
					field="VolumeDetail",
				)

	# ------------------------------------------------------------------ FLT / RTG

	def _v_flt(self, seg: dict) -> None:
		fields = seg["lines"][0].split("/")[1:]
		i = 0
		while i < len(fields):
			fid = fields[i]
			day = fields[i + 1] if i + 1 < len(fields) else ""
			self._de("DE312_CarrierCode", fid[:2], "2Mixed", "Carrier code")
			number = fid[2:]
			self._record(
				"DE800_FlightNumber", number, bool(re.fullmatch(r"\d{3,4}[A-Z]?", number)),
				f"Flight number (DE800) must be 3-4 digits with optional trailing letter, got '{number}'",
				field="DE800_FlightNumber",
			)
			self._de("DE202_Day", day, "2Numeric", "Flight day")
			i += 2

	def _v_rtg(self, seg: dict) -> None:
		fields = seg["lines"][0].split("/")[1:]
		first = fields[0] if fields else ""
		if len(first) >= 4:
			self._de("DE313_AirportCityCode", first[:3], "3Alpha", "First destination airport")
			self._de("DE312_CarrierCode", first[3:], "2Mixed", "First destination carrier")
		else:
			self._record(
				"DE312_CarrierCode", first, bool(re.fullmatch(r"[A-Z0-9]{2}", first)),
				f"First destination carrier (DE312) must be 2 alphanumeric characters, got '{first}'",
				field="DE312_CarrierCode",
			)
		onward = fields[1:]
		if len(onward) > 2:
			self._record(
				"Routing", "/".join(onward), False,
				"At most 2 onward destination/carrier entries are allowed (RTG_OnwardDestinationCarrier *2)",
				field="Routing",
			)
		for tok in onward:
			self._de("DE313_AirportCode", tok[:3], "3Alpha", "Onward destination airport")
			if tok[3:]:
				self._de("DE312_CarrierCode", tok[3:], "2Mixed", "Onward destination carrier")

	# ------------------------------------------------------------------ parties

	def _v_shp(self, seg: dict) -> None:
		self._v_party(seg, name_on_header=False)

	def _v_cne(self, seg: dict) -> None:
		self._v_party(seg, name_on_header=False)

	def _v_nfy(self, seg: dict) -> None:
		self._v_party(seg, name_on_header=True)

	def _v_party(self, seg: dict, name_on_header: bool) -> None:
		hparts = seg["lines"][0].split("/")
		bodies = cargoimp.continuation_text(seg)
		idx = 0

		if name_on_header:
			name = hparts[1] if len(hparts) > 1 else ""
			self._de("DE300_Name", name, "1*35Text", "Name")
		else:
			account = hparts[1] if len(hparts) > 1 else ""
			if account:
				self._de("DE108_AccountNumber", account, "1*14Text", "Account number")
			name = bodies[idx] if idx < len(bodies) else ""
			self._de("DE300_Name", name, "1*35Text", "Name")
			idx += 1

		street = bodies[idx] if idx < len(bodies) else ""
		idx += 1
		self._de("DE301_StreetAddress", street, "1*35Text", "Street address")

		loc = bodies[idx] if idx < len(bodies) else ""
		idx += 1
		lp = loc.split("/")
		self._de("DE302_Place", lp[0] if lp else "", "1*17Text", "Place")
		if len(lp) > 1 and lp[1]:
			self._de("DE303_StateProvince", lp[1], "1*9Text", "State/Province")

		coded = bodies[idx] if idx < len(bodies) else ""
		idx += 1
		cp = coded.split("/")
		self._de("DE304_ISOCountryCode", cp[0] if cp else "", "2Alpha", "ISO country code")
		if len(cp) > 1 and cp[1]:
			self._de("DE305_PostCode", cp[1], "1*9Text", "Post code")
		contacts = cp[2:]
		j = 0
		while j < len(contacts):
			ident = contacts[j]
			number = contacts[j + 1] if j + 1 < len(contacts) else ""
			if ident:
				self._de("DE122_ContactIdentifier", ident, "1*3Mixed", "Contact identifier")
				self._de("DE123_ContactNumber", number, "1*25Mixed", "Contact number")
			j += 2

	def _v_agt(self, seg: dict) -> None:
		h = seg["lines"][0].split("/")
		account = h[1] if len(h) > 1 else ""
		if account:
			self._de("DE108_AccountNumber", account, "1*14Text", "Account number")
		iata = h[2] if len(h) > 2 else ""
		self._de("DE311_IATACargoAgentNumericCode", iata, "7Numeric", "IATA cargo agent numeric code")
		f3 = h[3] if len(h) > 3 else ""
		if f3:
			if re.fullmatch(r"\d{4}", f3):
				self._de("DE309_IATACargoAgentCASSAddress", f3, "4Numeric", "IATA cargo agent CASS address")
			else:
				self._de("DE319_ParticipantIdentifier", f3, "1*3Mixed", "Participant identifier")
		f4 = h[4] if len(h) > 4 else ""
		if f4:
			self._de("DE319_ParticipantIdentifier", f4, "1*3Mixed", "Participant identifier")

		bodies = cargoimp.continuation_text(seg)
		self._de("DE300_Name", bodies[0] if bodies else "", "1*35Text", "Name")
		self._de("DE302_Place", bodies[1] if len(bodies) > 1 else "", "1*17Text", "Place")

	# ------------------------------------------------------------------ text segments

	def _v_ssr(self, seg: dict) -> None:
		self._v_text(seg, "SSR", "DE404_SpecialServiceRequest", "Special service request")

	def _v_osi(self, seg: dict) -> None:
		self._v_text(seg, "OSI", "DE405_OtherServiceInformation", "Other service information")

	def _v_text(self, seg: dict, code: str, element: str, label: str) -> None:
		values = self._seg_values(seg, code)
		if len(values) > 3:
			self._record(code, str(len(values)), False, f"{label}: at most 3 lines allowed (1*3)", field=code)
		for v in values:
			self._de(element, v, "1*65Text", label)

	def _v_acc(self, seg: dict) -> None:
		values = self._seg_values(seg, "ACC")
		if len(values) > 6:
			self._record(
				"ACC", str(len(values)), False, "Accounting information: at most 6 lines (1*6)", field="ACC"
			)
		for v in values:
			p = v.split("/")
			self._de(
				"DE411_AccountingInformationIdentifier", p[0] if p else "", "3Alpha",
				"Accounting information identifier",
			)
			if len(p) > 1:
				self._de("DE410_AccountingInformation", p[1], "1*34Text", "Accounting information")

	def _v_sph(self, seg: dict) -> None:
		codes: list[str] = []
		for v in self._seg_values(seg, "SPH"):
			codes += [c for c in v.split("/") if c != ""]
		if len(codes) > 9:
			self._record(
				"SPH", str(len(codes)), False, "Special handling: at most 9 codes (1*9)", field="SPH"
			)
		for c in codes:
			self._de("DE705_SpecialHandlingCode", c, "3Alpha", "Special handling code")

	# ------------------------------------------------------------------ CVD

	def _v_cvd(self, seg: dict) -> None:
		f = seg["lines"][0].split("/")

		def at(i):
			return f[i] if i < len(f) else ""

		self._de("DE606_ISOCurrencyCode", at(1), "3Alpha", "Currency code", field="DE606_ISOCurrencyCode")
		if at(2):
			self._de("DE503_ChargeCode", at(2), "2Alpha", "Charge code")
		pc = at(3)
		if pc:
			self._record(
				"DE403_PCInd", pc, bool(re.fullmatch(r"[A-Z]{2}", pc)),
				f"Prepaid/collect charge declaration (2x DE403) must be 2 letters, got '{pc}'",
				field="DE403_PCInd",
			)
		self._declared_value("DE510_DeclaredValueOfCarriage", at(4), "NVD", 12, "Declared value for carriage")
		self._declared_value("DE509_DeclaredValueOfCustoms", at(5), "NCV", 12, "Declared value for customs")
		self._declared_value("DE508_AmountOfInsurance", at(6), "XXX", 11, "Amount of insurance")

	def _declared_value(self, element, value, no_value_code, maxlen, label) -> None:
		ok = value == no_value_code or self._is_decimal(value, maxlen)
		self._record(
			element, value, ok,
			f"{label} must be '{no_value_code}' or a decimal up to {maxlen} chars, got '{value}'",
			field=element,
		)

	# ------------------------------------------------------------------ RTD

	def _v_rtd(self, seg: dict) -> None:
		lines = list(seg["lines"])
		if lines and lines[0].startswith("RTD"):
			lines[0] = lines[0][3:]

		self._rtd_goods_desc = False
		for raw in lines:
			toks = raw.split("/")
			if toks and toks[0] == "":
				toks = toks[1:]
			self._rtd_line(toks)

		# DE709 (nature and quantity of goods) is mandatory in an FWB; it is only carried
		# on an NG (goods description) or NC (consolidation) line. The ABNF permits a rate
		# line with no such second line, so this conditional rule is enforced explicitly.
		self._record(
			"DE709_NatureAndQuantityOfGoods", "G/C" if self._rtd_goods_desc else "",
			self._rtd_goods_desc,
			"Rate description must include a nature and quantity of goods line "
			"(NG goods description or NC consolidation) carrying DE709",
			field="DE709_NatureAndQuantityOfGoods", code="RTD_GOODS_MISSING",
		)

	def _rtd_line(self, toks: list[str]) -> None:
		k, n = 0, len(toks)
		while k < n:
			tok = toks[k]
			if tok == "":
				k += 1
				continue
			if tok.isdigit():
				self._de("DE106_AWBRateLineNumber", tok, "1*2Numeric", "Rate line number")
				k += 1
				continue
			ind = tok[0]
			if ind == "N" and len(tok) >= 2:
				k = self._rtd_goods(tok[1], toks, k)
				continue
			if ind == "P":
				val = tok[1:]
				ok = bool(re.fullmatch(r"\d{1,4}", val) or re.fullmatch(r"[A-Z]{3}", val))
				self._record(
					"DE701_NumberOfPieces", tok, ok,
					f"P column must be 1-4 digits (pieces) or a 3-letter rate combination point, got '{val}'",
					field="DE701_NumberOfPieces",
				)
			elif ind in ("K", "L"):
				self._rtd_decimal("DE600_Weight", tok[1:], 7, "Gross weight")
			elif ind == "C":
				self._de("DE507_RateClassCode", tok[1:], "1Alpha", "Rate class code")
			elif ind == "S":
				val = tok[1:]
				self._record(
					"DE_Commodity_S", tok, bool(re.fullmatch(r"[A-Z0-9]+", val)),
					f"S column (commodity item / ULD rate class / rate class+percentage) is invalid: '{val}'",
					field="DE_Commodity_S",
				)
			elif ind == "W":
				self._rtd_decimal("DE600_Weight", tok[1:], 7, "Chargeable weight")
			elif ind == "R":
				self._rtd_decimal("DE506_RateChargeDiscount", tok[1:], 8, "Rate / charge")
			elif ind == "T":
				self._rtd_decimal("DE501_ChargeDiscountAmount", tok[1:], 12, "Charge / total")
			elif len(tok) == 1 and tok.isalpha():
				self._de("DE505_ServiceCode", tok, "1Alpha", "Service code")
			else:
				self._record("RTD_Token", tok, False, f"Unrecognised RTD token '{tok}'", field="RTD")
			k += 1

	def _rtd_goods(self, sub: str, toks: list[str], k: int) -> int:
		"""Validate one N-prefixed goods line element; return the next token index."""
		n = len(toks)

		def nxt(offset):
			return toks[k + offset] if k + offset < n else ""

		if sub in ("G", "C"):
			self._rtd_goods_desc = True
			self._de("DE709_NatureAndQuantityOfGoods", nxt(1), "1*20Text", "Nature and quantity of goods")
			return k + 2
		if sub == "H":
			self._de("DE900_HarmonisedCommodityCode", nxt(1), "6*18Mixed", "Harmonised commodity code")
			return k + 2
		if sub == "O":
			self._de("DE304_ISOCountryCode", nxt(1), "2Alpha", "Country of origin of goods")
			return k + 2
		if sub == "S":
			self._de("DE714_SLAC", nxt(1), "1*5Numeric", "Shipper's load and count")
			return k + 2
		if sub == "V":
			val = nxt(1)
			m = re.fullmatch(r"([A-Z]{2})([0-9.]+)", val)
			if m:
				self._de("DE604_VolumeCode", m.group(1), "2Alpha", "Volume code")
				self._rtd_decimal("DE500_VolumeAmount", m.group(2), 9, "Volume amount")
			else:
				self._record(
					"DE604_VolumeCode", val, False,
					f"Volume must be a 2-letter code + amount, got '{val}'", field="DE604_VolumeCode",
				)
			return k + 2
		if sub == "U":
			val = nxt(1)
			ok = bool(re.fullmatch(r"[A-Z][A-Z0-9]{2}[A-Z0-9]+\d{3,4}[A-Z0-9]{2}", val))
			self._record(
				"DE802_ULDIdentification", val, ok,
				f"ULD identification (type+serial+owner) is invalid: '{val}'",
				field="DE802_ULDIdentification",
			)
			return k + 2
		if sub == "D":
			return self._rtd_dimensions(toks, k)
		self._record(
			"RTD_GoodsData", "N" + sub, False, f"Unknown goods data identifier 'N{sub}'", field="RTD"
		)
		return k + 1

	def _rtd_dimensions(self, toks: list[str], k: int) -> int:
		n = len(toks)
		wt = toks[k + 1] if k + 1 < n else ""
		dims = toks[k + 2] if k + 2 < n else ""
		pieces = toks[k + 3] if k + 3 < n else ""
		if wt:
			m = re.fullmatch(r"([KL])([0-9.]+)", wt)
			if m:
				self._rtd_decimal("DE600_Weight", m.group(2), 7, "Dimension weight")
			else:
				self._record(
					"DE601_WeightCode", wt, False,
					f"Dimension weight must be K/L + amount, got '{wt}'", field="DE601_WeightCode",
				)
		if dims == "NDA":
			self._record("DE611_NoDimensionsAvailable", dims, True, "")
			return k + 3
		m = re.fullmatch(r"([A-Z0-9]{1,3})(\d{1,5})-(\d{1,5})-(\d{1,5})", dims)
		if m:
			self._de("DE611_MeasurementUnitCode", m.group(1), "1*3Mixed", "Measurement unit code")
			self._record("DE608_LengthDimension", m.group(2), True, "")
			self._record("DE609_WidthDimension", m.group(3), True, "")
			self._record("DE610_HeightDimension", m.group(4), True, "")
			self._de("DE701_NumberOfPieces", pieces, "1*4Numeric", "Number of pieces")
			return k + 4
		self._record(
			"RTD_Dimensions", dims, False,
			f"Dimensions must be unit+L-W-H, got '{dims}'", field="RTD_Dimensions",
		)
		return k + 3

	def _rtd_decimal(self, element, value, maxlen, label) -> None:
		self._record(
			element, value, self._is_decimal(value, maxlen),
			f"{label} ({element}) must be a decimal of up to {maxlen} characters, got '{value}'",
			field=element,
		)

	# ------------------------------------------------------------------ OTH

	def _v_oth(self, seg: dict) -> None:
		groups: list[str] = []
		header = seg["lines"][0]
		if header.startswith("OTH/"):
			groups.append(header[4:])
		groups += cargoimp.continuation_text(seg)
		for g in groups:
			parts = g.split("/")
			pc = parts[0] if parts else ""
			self._record(
				"DE403_PCInd", pc, bool(re.fullmatch(r"[A-Z]", pc)),
				f"Other-charge prepaid/collect indicator (DE403) must be a single letter, got '{pc}'",
				field="DE403_PCInd",
			)
			body = "".join(parts[1:])
			items = re.findall(r"([A-Z]{2})([A-Z])([0-9.]+)", body)
			if not 1 <= len(items) <= 3:
				self._record(
					"OTH_OtherChargeItems", body, False,
					"Each OTH line must carry 1-3 other-charge items", field="OTH",
				)
			consumed = "".join(c + e + a for c, e, a in items)
			if consumed != body:
				self._record(
					"OTH_OtherChargeItems", body, False,
					f"Could not parse all other-charge items in '{body}'", field="OTH",
				)
			for ccode, ent, amt in items:
				self._de("DE504_OtherChargeCode", ccode, "2Alpha", "Other charge code")
				self._de("DE315_EntitlementCode", ent, "1Alpha", "Entitlement code")
				self._rtd_decimal("DE501_ChargeAmount", amt, 12, "Charge amount")

	# ------------------------------------------------------------------ PPD / COL

	def _v_ppd(self, seg: dict) -> None:
		self._v_charge_summary(seg, "PPD")

	def _v_col(self, seg: dict) -> None:
		self._v_charge_summary(seg, "COL")

	def _v_charge_summary(self, seg: dict, code: str) -> None:
		toks: list[str] = []
		header = seg["lines"][0]
		if header.startswith(code + "/"):
			toks += [t for t in header[len(code) + 1:].split("/") if t != ""]
		for body in cargoimp.continuation_text(seg):
			toks += [t for t in body.split("/") if t != ""]

		has_total = False
		for tok in toks:
			m = re.fullmatch(r"(WT|VC|TX|OA|OC|CT)([0-9.]+)", tok)
			if m:
				has_total = has_total or m.group(1) == "CT"
				self._rtd_decimal("DE501_ChargeAmount", m.group(2), 12, f"{m.group(1)} charge amount")
			else:
				self._record(
					"DE502_ChargeIdentifier", tok, False,
					f"Charge token must be WT/VC/TX/OA/OC/CT + amount, got '{tok}'",
					field="DE502_ChargeIdentifier",
				)
		self._record(
			"DE502_ChargeIdentifier_CT", "CT", has_total,
			f"{code} charge summary must include the CT (summary total) charge",
			field="DE502_ChargeIdentifier_CT",
		)

	# ------------------------------------------------------------------ CER / ISU

	def _v_cer(self, seg: dict) -> None:
		parts = seg["lines"][0].split("/", 1)
		sig = parts[1] if len(parts) > 1 else ""
		self._de("DE414_Signature", sig, "1*20Text", "Shipper's certification signature")

	def _v_isu(self, seg: dict) -> None:
		f = seg["lines"][0].split("/")
		date = f[1] if len(f) > 1 else ""
		m = re.fullmatch(r"(\d{2})([A-Z]{3})(\d{2})", date)
		if m:
			self._de("DE202_Day", m.group(1), "2Numeric", "Issue day")
			self._record(
				"DE201_Month", m.group(2), m.group(2) in _MONTHS,
				f"Issue month (DE201) must be a 3-letter month (JAN-DEC), got '{m.group(2)}'",
				field="DE201_Month",
			)
			self._de("DE200_Year", m.group(3), "2Numeric", "Issue year")
		else:
			self._record(
				"ISU_IssueDate", date, False,
				f"Issue date must be DDMMMYY format (DE202/DE201/DE200), got '{date}'",
				field="ISU_IssueDate",
			)
		place = f[2] if len(f) > 2 else ""
		self._de("DE302_Place", place, "1*17Text", "Place of issue")
		if len(f) > 3 and f[3]:
			self._de("DE414_Signature", f[3], "1*20Text", "Carrier's execution signature")

	# ------------------------------------------------------------------ CDC / REF

	def _v_cdc(self, seg: dict) -> None:
		f = seg["lines"][0].split("/")
		cur_rate = f[1] if len(f) > 1 else ""
		m = re.fullmatch(r"([A-Z]{3})([0-9.]+)", cur_rate)
		if m:
			self._de("DE606_ISOCurrencyCode", m.group(1), "3Alpha", "Destination currency")
			self._rtd_decimal("DE607_RateOfExchange", m.group(2), 11, "Currency conversion rate")
		else:
			self._record(
				"CDC_DestinationCurrency", cur_rate, False,
				f"Destination currency + rate invalid: '{cur_rate}'", field="DE606_ISOCurrencyCode",
			)
		amounts = (
			(2, "CC charges in destination currency"),
			(3, "Charges at destination"),
			(4, "Total collect charges"),
		)
		for i, label in amounts:
			if i < len(f):
				self._rtd_decimal("DE501_ChargeAmount", f[i], 12, label)

	def _v_ref(self, seg: dict) -> None:
		f = seg["lines"][0].split("/")
		a = f[1] if len(f) > 1 else ""
		if a == "":
			# participant identification form: REF// [fileref] / pid / code / airport
			if len(f) > 2 and f[2]:
				self._de("DE117_FileReference", f[2], "1*15Text", "Sender office file reference")
			if len(f) > 3 and f[3]:
				self._de("DE319_ParticipantIdentifier", f[3], "1*3Mixed", "Sender participant identifier")
			if len(f) > 4 and f[4]:
				self._de("DE320_ParticipantCode", f[4], "1*17Mixed", "Sender participant code")
			if len(f) > 5 and f[5]:
				self._de("DE313_AirportCityCode", f[5], "3Alpha", "Sender airport/city code")
		else:
			# office message address form: airport(3) + office function(2) + company(2)
			self._de("DE313_AirportCityCode", a[:3], "3Alpha", "Sender airport/city code")
			self._de("DE107_OfficeFunctionDesignator", a[3:5], "2Mixed", "Office function designator")
			self._de("DE308_CompanyDesignator", a[5:7], "2Mixed", "Company designator")
			if len(a) > 7:
				self._record(
					"REF_SenderOfficeMessageAddress", a, False,
					f"Office message address has trailing characters: '{a[7:]}'", field="REF",
				)
			if len(f) > 2 and f[2]:
				self._de("DE117_FileReference", f[2], "1*15Text", "Sender office file reference")

	# ------------------------------------------------------------------ COR / COI / SII / ARD / NOM / SRI

	def _v_cor(self, seg: dict) -> None:
		f = seg["lines"][0].split("/")
		self._de("DE906_CustomsOriginCode", f[1] if len(f) > 1 else "", "1*2Mixed", "Customs origin code")

	def _v_coi(self, seg: dict) -> None:
		f = seg["lines"][0].split("/")
		a = f[1] if len(f) > 1 else ""
		b = f[2] if len(f) > 2 else ""
		c = f[3] if len(f) > 3 else ""
		if a:
			self._de("DE614_CASSIndicator", a, "1*2Alpha", "No-commission indication")
		elif b:
			self._rtd_decimal("DE613_CASSSettlementFactor", b, 12, "Commission amount")
		elif c:
			self._rtd_decimal("DE613_CASSSettlementFactor", c, 12, "Commission percentage")
		else:
			self._record(
				"CommissionInformation", "", False,
				"Commission information requires an indicator, amount or percentage", field="COI",
			)

	def _v_sii(self, seg: dict) -> None:
		f = seg["lines"][0].split("/")
		self._rtd_decimal("DE501_ChargeAmount", f[1] if len(f) > 1 else "", 12, "Sales incentive amount")
		if len(f) > 2 and f[2]:
			self._de("DE614_CASSIndicator", f[2], "1*2Alpha", "Sales incentive indication")

	def _v_ard(self, seg: dict) -> None:
		f = seg["lines"][0].split("/")
		self._de("DE117_FileReference", f[1] if len(f) > 1 else "", "1*15Text", "Agent reference")

	def _v_nom(self, seg: dict) -> None:
		f = seg["lines"][0].split("/")
		self._de("DE300_Name", f[1] if len(f) > 1 else "", "1*35Text", "Nominated handling party name")
		self._de("DE302_Place", f[2] if len(f) > 2 else "", "1*17Text", "Nominated handling party place")

	def _v_sri(self, seg: dict) -> None:
		f = seg["lines"][0].split("/")
		ref = f[1] if len(f) > 1 else ""
		if ref:
			self._de("DE132_ReferenceNumber", ref, "1*14Text", "Reference number")
		if len(f) > 2 and f[2]:
			self._de(
				"DE133_SupplementaryShipmentInformation", f[2], "1*12Text", "Supplementary shipment info"
			)
		if len(f) > 3 and f[3]:
			self._de(
				"DE133_SupplementaryShipmentInformation", f[3], "1*12Text", "Supplementary shipment info"
			)

	def _v_opi(self, seg: dict) -> None:
		h = seg["lines"][0].split("/")
		self._de("DE300_Name", h[1] if len(h) > 1 else "", "1*35Text", "Other participant name")
		bodies = cargoimp.continuation_text(seg)
		if not bodies:
			return
		p = bodies[-1].split("/")
		if p and p[0] == "":
			if len(p) > 2 and p[2]:
				self._de("DE319_ParticipantIdentifier", p[2], "1*3Mixed", "Other participant identifier")
			if len(p) > 3 and p[3]:
				self._de("DE320_ParticipantCode", p[3], "1*17Mixed", "Other participant code")
			if len(p) > 4 and p[4]:
				self._de("DE313_AirportCityCode", p[4], "3Alpha", "Other participant airport/city code")
		elif p and p[0]:
			addr = p[0]
			self._de("DE313_AirportCityCode", addr[:3], "3Alpha", "Other participant airport/city code")
			self._de("DE107_OfficeFunctionDesignator", addr[3:5], "2Mixed", "Office function designator")
			self._de("DE308_CompanyDesignator", addr[5:7], "2Mixed", "Company designator")

	# ------------------------------------------------------------------ OCI

	def _v_oci(self, seg: dict) -> None:
		lines = list(seg["lines"])
		if lines and lines[0].startswith("OCI"):
			lines[0] = lines[0][3:]
		for raw in lines:
			fields = raw.split("/")
			if fields and fields[0] == "":
				fields = fields[1:]
			country = fields[0] if len(fields) > 0 else ""
			info_id = fields[1] if len(fields) > 1 else ""
			customs_id = fields[2] if len(fields) > 2 else ""
			supp = fields[3] if len(fields) > 3 else ""
			if country:
				self._de("DE304_ISOCountryCode", country, "2Alpha", "Country code")
			if info_id:
				self._de("DE103_InformationIdentifier", info_id, "3Alpha", "Information identifier")
			if customs_id:
				self._de(
					"DE941_CustomsInformationIdentifier", customs_id, "1*2Alpha",
					"Customs information identifier",
				)
			self._de(
				"DE940_SupplementaryCustomsInformation", supp, "1*35Text",
				"Supplementary customs information",
			)

	# ------------------------------------------------------------------ primitives

	def _seg_values(self, seg: dict, code: str) -> list[str]:
		"""Slash-delimited body values: header remainder + continuation bodies."""
		out = []
		header = seg["lines"][0]
		if header.startswith(code + "/"):
			out.append(header[len(code) + 1:])
		out += cargoimp.continuation_text(seg)
		return [v for v in out if v != ""]

	def _section(self, name: str) -> None:
		self._sec += 1
		self._item = 0
		self._cur = name

	def _record(self, element, value, ok, message, field=None, code=None) -> bool:
		self._item += 1
		self.checks.append({
			"ref": f"{self._sec}.{self._item}",
			"segment": self._cur,
			"element": element,
			"value": "" if value is None else str(value),
			"ok": bool(ok),
			"message": "" if ok else message,
			"field": field or element,
			"code": code or element,
		})
		return bool(ok)

	def _de(self, element, value, spec, label, field=None, required=True) -> bool:
		v = "" if value is None else str(value)
		if v == "" and not required:
			return True
		ok = self._match(spec, v)
		return self._record(
			element, v, ok,
			f"{label} ({element}) is invalid: expected {self._desc(spec)}, got '{v}'",
			field=field,
		)

	@staticmethod
	def _match(spec: str, value: str) -> bool:
		if spec.endswith("Decimal"):
			maxlen = int(spec[spec.find("*") + 1: -len("Decimal")])
			return FWBABNFValidator._is_decimal(value, maxlen)
		entry = _SPEC.get(spec)
		if not entry:
			return True
		return bool(re.fullmatch(entry[0], value))

	@staticmethod
	def _desc(spec: str) -> str:
		if spec.endswith("Decimal"):
			maxlen = spec[spec.find("*") + 1: -len("Decimal")]
			return f"a decimal of up to {maxlen} characters"
		entry = _SPEC.get(spec)
		return entry[1] if entry else spec

	@staticmethod
	def _is_decimal(value: str, maxlen: int) -> bool:
		if not value or len(value) > maxlen:
			return False
		if not re.fullmatch(r"[0-9.]+", value):
			return False
		if value.count(".") > 1:
			return False
		return any(ch.isdigit() for ch in value)

	@staticmethod
	def _violation(check: dict) -> dict:
		return {
			"level": "Error",
			"code": check["code"],
			"field": check["field"],
			"message": check["message"],
			"ref": check["ref"],
			"segment": check["segment"],
		}


def validate(raw: str) -> list[dict]:
	"""Convenience: return the list of violations for ``raw``."""
	return FWBABNFValidator().validate(raw)


_SAMPLE = """FWB/16
157-42781966DACHAM/T40K574MC4.785
RTG/DOHQR/FRAQR/HAMQR
SHP
/CONVEYOR SHIPPING LINES.
/57 KEMAL ATATURK AVENUE    BANANI
/DHAKA
/BD/1213/TE/01799929458
CNE
/HBH LOGISTICS GMBH  CO. KG.
/EDISONSTR. 9 28816 STUHR  GERMANY.
/HAMBURG
/DE/28816/TE/4942148993927
AGT//4230437/0006
/CONVEYOR LOGISTICS LTD
/DHAKA
CVD/USD//PP/NVD/NCV/XXX
RTD/1/P40/K574/CQ/W798/R4.25/T3391.5
/NC/CONSOL OF GARMENTS
/2/NH/61102000
/3/ND//CMT60-41-45/21
/4/ND//CMT60-41-55/4
/5/ND//CMT60-41-52/15
OTH/P/AHC15.96CGC9BFC30
/P/FEC63.84AWC6.62SCC45.92
PPD/WT3391.5
/OA0/OC171.34/CT3562.84
COL
/CT0
CER/CONVEYOR LOGISTICS L
ISU/03JUN26/DHAKA/CONVEYOR LOGISTICS L
REF/DACCDQR
SPH/EAP/GCR/SRA
OCI/BD/ISS/RA/00001-01
/BD//ED/1027
/BD//SS/SHR
/BD//SM/EDS
/BD//SN/ZAHIRULISLAM
/BD//SD/03-JUN-2026 1958
/IE/OSS/RC/ACC3-BDDAC-QR
"""


if __name__ == "__main__":
	import sys

	data = sys.stdin.read() if not sys.stdin.isatty() else _SAMPLE
	print(FWBABNFValidator().format_report(data))
