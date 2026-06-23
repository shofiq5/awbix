"""Tests for FFAParser — pure parse/validate (no DB) and DB-backed process."""

import frappe
from frappe.tests.utils import FrappeTestCase

from awbix.edx.handlers.ffa.ffa_parser import FFAParser

# ---------------------------------------------------------------------------
# Test fixtures — examples taken verbatim from FFA.md §6
# ---------------------------------------------------------------------------

# §6.1 — KK (confirmed), goods description + SHC, 7-digit serial (FFA/4 era)
SAMPLE_61 = """FFA/4
125-1234565FRAPHL/T12K950/BOOKS/VAL
BA171/19MAR/LHRJFK/KK
REF/FRAFCBA
"""

# §6.2 — UU (rejected), file reference on REF, valid 8-digit serial
SAMPLE_62 = """FFA/4
057-12345675BHXJFK/T5K400
AF077/19MAY/CDGJFK/UU
REF/BHXFRBA/1234
"""

# §6.3 — UN (flight doesn't operate)
SAMPLE_63 = """FFA/4
125-12345675LHRLAX/T12K900
SR3309/11JUL/ZRHLAX/UN
REF/LHRFWBA
"""

# §6.4 — LL (wait-listed)
SAMPLE_64 = """FFA/4
085-12345675ZRHLAX/T10K250
AA123/10MAY/JFKLAX/LL
REF/ZRHFRSR
"""

# §6.5 — HK (holding confirmation)
SAMPLE_65 = """FFA/4
125-21210000EDIYMX/T7K95
BA073/16MAR/LHRYMX/HK
REF/GLAFRBA
"""

# §6.8 — two flights: KK then UU
SAMPLE_68 = """FFA/4
160-76543213HKGYSB/T4K160
AC857/19MAR/LHRYYZ/KK
AC363/20MAR/YYZYSB/UU
REF/HKGFQCX
"""

# §6.9 — SSR + OSI (continuation lines) + SRI, P-type with total pieces
SAMPLE_69 = """FFA/4
021-77777770MSPLHR/P5K5750T9
AA001/19MAR/JFKLHR/KK
SSR/TEMP RESTRICTION OK
/SPL CARE OK
OSI/NEED TO RCV CGO BY 1800 19MAR
/AND TO MEET THE AGENT
REF/MSPFCNW/4923ACA
SRI/ABCD-12345
"""

# §6.10 — SRI with time-definite service reference
SAMPLE_610 = """FFA/4
020-12345675FRAJFK/T20K800
LH404/02JUN/FRAJFK/KK
SSR/SPECIAL SERVICE INFORMATION
OSI/OTHER SERVICE INFORMATION
REF/FRAGDLH
SRI/LH8520/YNZ01JUN1800/03JUN0700
"""

# FFA/6 message used for process() integration tests
SAMPLE_PROCESS = """FFA/6
057-12345675BHXJFK/T5K400
AF077/19MAY/CDGJFK/KK
REF/BHXFRBA
"""

# Multi-flight FFA/6 for process() multi-flight test
SAMPLE_MULTI_PROCESS = """FFA/6
160-76543213HKGYSB/T4K160
AC857/19MAR/LHRYYZ/KK
AC363/20MAR/YYZYSB/UU
REF/HKGFQCX
"""


# ---------------------------------------------------------------------------
# Pure parse/validate tests — no DB required
# ---------------------------------------------------------------------------


class TestFFAParserPure(FrappeTestCase):
	"""Pure parse/validate tests — no DB required."""

	def setUp(self):
		self.parser = FFAParser()

	# ----------------------------------------------------------------- parse: AWB

	def test_parse_61_awb_fields(self):
		data = self.parser.parse(SAMPLE_61)
		awb = data["awb"]
		self.assertEqual(awb["airline_prefix"], "125")
		self.assertEqual(awb["awb_serial_number"], "1234565")
		self.assertEqual(awb["awb_number"], "125-1234565")
		self.assertEqual(awb["origin"], "FRA")
		self.assertEqual(awb["destination"], "PHL")
		self.assertEqual(awb["shipment_description_code"], "T")
		self.assertEqual(awb["number_of_pieces"], 12)
		self.assertEqual(awb["weight_code"], "K")
		self.assertAlmostEqual(awb["weight"], 950.0)

	def test_parse_61_goods_and_shc(self):
		data = self.parser.parse(SAMPLE_61)
		awb = data["awb"]
		self.assertEqual(awb.get("goods_description"), "BOOKS")
		self.assertIn("VAL", awb.get("special_handling_codes", []))

	def test_parse_62_awb_8digit_serial(self):
		data = self.parser.parse(SAMPLE_62)
		self.assertEqual(data["awb"]["awb_serial_number"], "12345675")
		self.assertEqual(data["awb"]["awb_number"], "057-12345675")

	def test_parse_69_p_type_total_pieces(self):
		data = self.parser.parse(SAMPLE_69)
		awb = data["awb"]
		self.assertEqual(awb["shipment_description_code"], "P")
		self.assertEqual(awb["number_of_pieces"], 5)
		self.assertEqual(awb.get("total_pieces"), 9)

	def test_parse_awb_no_quantity_detail(self):
		# AWB line without quantity suffix is accepted; fields simply absent
		raw = "FFA/6\n057-12345675BHXJFK\nAF077/19MAY/CDGJFK/UU\nREF/BHXFRBA\n"
		data = self.parser.parse(raw)
		awb = data["awb"]
		self.assertEqual(awb["awb_number"], "057-12345675")
		self.assertNotIn("number_of_pieces", awb)

	# ----------------------------------------------------------------- parse: flights

	def test_parse_61_single_flight(self):
		data = self.parser.parse(SAMPLE_61)
		self.assertEqual(len(data["flights"]), 1)
		flt = data["flights"][0]
		self.assertEqual(flt["carrier"], "BA")
		self.assertEqual(flt["flight_number"], "171")
		self.assertEqual(flt["day"], 19)
		self.assertEqual(flt["month"], "MAR")
		self.assertEqual(flt["departure_airport"], "LHR")
		self.assertEqual(flt["arrival_airport"], "JFK")
		self.assertEqual(flt["space_allocation_code"], "KK")

	def test_parse_63_un_flight(self):
		data = self.parser.parse(SAMPLE_63)
		flt = data["flights"][0]
		self.assertEqual(flt["carrier"], "SR")
		self.assertEqual(flt["flight_number"], "3309")
		self.assertEqual(flt["space_allocation_code"], "UN")

	def test_parse_68_multi_flight(self):
		data = self.parser.parse(SAMPLE_68)
		self.assertEqual(len(data["flights"]), 2)
		self.assertEqual(data["flights"][0]["space_allocation_code"], "KK")
		self.assertEqual(data["flights"][0]["carrier"], "AC")
		self.assertEqual(data["flights"][0]["flight_number"], "857")
		self.assertEqual(data["flights"][1]["space_allocation_code"], "UU")
		self.assertEqual(data["flights"][1]["carrier"], "AC")
		self.assertEqual(data["flights"][1]["flight_number"], "363")
		self.assertEqual(data["flights"][1]["month"], "MAR")

	def test_parse_64_ll_wait_listed(self):
		data = self.parser.parse(SAMPLE_64)
		self.assertEqual(data["flights"][0]["space_allocation_code"], "LL")

	def test_parse_65_hk_holding_confirm(self):
		data = self.parser.parse(SAMPLE_65)
		self.assertEqual(data["flights"][0]["space_allocation_code"], "HK")

	# ----------------------------------------------------------------- parse: SSR/OSI

	def test_parse_69_ssr_continuation(self):
		data = self.parser.parse(SAMPLE_69)
		self.assertEqual(len(data["ssr"]), 2)
		self.assertIn("TEMP RESTRICTION OK", data["ssr"][0])
		self.assertIn("SPL CARE OK", data["ssr"][1])

	def test_parse_69_osi_continuation(self):
		data = self.parser.parse(SAMPLE_69)
		self.assertEqual(len(data["osi"]), 2)
		self.assertIn("1800 19MAR", data["osi"][0])
		self.assertIn("MEET THE AGENT", data["osi"][1])

	def test_parse_610_single_ssr_osi(self):
		data = self.parser.parse(SAMPLE_610)
		self.assertEqual(len(data["ssr"]), 1)
		self.assertEqual(data["ssr"][0], "SPECIAL SERVICE INFORMATION")
		self.assertEqual(len(data["osi"]), 1)
		self.assertEqual(data["osi"][0], "OTHER SERVICE INFORMATION")

	def test_parse_no_ssr_osi(self):
		data = self.parser.parse(SAMPLE_62)
		self.assertEqual(data["ssr"], [])
		self.assertEqual(data["osi"], [])

	# ----------------------------------------------------------------- parse: REF

	def test_parse_ref_format_a_no_fileref(self):
		data = self.parser.parse(SAMPLE_61)
		ref = data["booking_reference"]
		self.assertEqual(ref["office_address"], "FRAFCBA")
		self.assertEqual(ref.get("file_reference", ""), "")

	def test_parse_ref_format_a_with_fileref(self):
		data = self.parser.parse(SAMPLE_62)
		ref = data["booking_reference"]
		self.assertEqual(ref["office_address"], "BHXFRBA")
		self.assertEqual(ref["file_reference"], "1234")

	def test_parse_ref_format_b_participant(self):
		raw = "FFA/6\n057-12345675BHXJFK/T5K400\nAF077/19MAY/CDGJFK/UU\nREF//MYREF/XXX/CODEABC/JFK\n"
		data = self.parser.parse(raw)
		ref = data["booking_reference"]
		self.assertEqual(ref["file_reference"], "MYREF")
		self.assertEqual(ref["participant_id"], "XXX")
		self.assertEqual(ref["participant_code"], "CODEABC")
		self.assertEqual(ref["airport"], "JFK")

	def test_parse_69_ref_with_fileref(self):
		data = self.parser.parse(SAMPLE_69)
		ref = data["booking_reference"]
		self.assertEqual(ref["office_address"], "MSPFCNW")
		self.assertEqual(ref["file_reference"], "4923ACA")

	# ----------------------------------------------------------------- parse: SRI

	def test_parse_69_sri(self):
		data = self.parser.parse(SAMPLE_69)
		self.assertEqual(len(data["references"]), 1)
		r = data["references"][0]
		self.assertEqual(r["reference_number"], "ABCD-12345")
		self.assertEqual(r["supplementary_1"], "")
		self.assertEqual(r["supplementary_2"], "")

	def test_parse_610_sri_time_definite(self):
		data = self.parser.parse(SAMPLE_610)
		r = data["references"][0]
		self.assertEqual(r["reference_number"], "LH8520")
		self.assertEqual(r["supplementary_1"], "YNZ01JUN1800")
		self.assertEqual(r["supplementary_2"], "03JUN0700")

	def test_parse_no_sri(self):
		data = self.parser.parse(SAMPLE_62)
		self.assertEqual(data["references"], [])

	# ----------------------------------------------------------------- parse: misc

	def test_parse_message_version_captured(self):
		data = self.parser.parse(SAMPLE_61)
		self.assertEqual(data["message"]["version"], "4")

	def test_parse_unknown_segment_between_flights_ignored(self):
		raw = "FFA/6\n057-12345675BHXJFK/T5K400\nAF077/19MAY/CDGJFK/UU\nXYZ/IGNORE THIS\nREF/BHXFRBA\n"
		data = self.parser.parse(raw)
		self.assertEqual(len(data["flights"]), 1)
		self.assertIsNotNone(data["booking_reference"].get("office_address"))

	# ----------------------------------------------------------------- business_key

	def test_business_key_normal(self):
		data = self.parser.parse(SAMPLE_62)
		self.assertEqual(self.parser.business_key(data), "057-12345675")

	def test_business_key_7digit_serial(self):
		data = self.parser.parse(SAMPLE_61)
		self.assertEqual(self.parser.business_key(data), "125-1234565")

	def test_business_key_no_awb(self):
		self.assertIsNone(self.parser.business_key({"awb": {}}))

	# ----------------------------------------------------------------- validate: clean

	def test_validate_clean_62(self):
		data = self.parser.parse(SAMPLE_62)
		errors = [i for i in self.parser.validate(data) if i["level"] == "Error"]
		self.assertEqual(errors, [])

	def test_validate_clean_68(self):
		data = self.parser.parse(SAMPLE_68)
		errors = [i for i in self.parser.validate(data) if i["level"] == "Error"]
		self.assertEqual(errors, [])

	# ----------------------------------------------------------------- validate: AWB errors

	def test_validate_unparseable_awb(self):
		data = self.parser.parse("FFA/6\nNOTVALID\nAF077/19MAY/CDGJFK/UU\nREF/BHXFRBA\n")
		codes = {i["code"] for i in self.parser.validate(data) if i["level"] == "Error"}
		self.assertIn("AWB_LINE", codes)

	def test_validate_7digit_serial_flagged(self):
		data = self.parser.parse(SAMPLE_61)  # 7-digit serial
		codes = {i["code"] for i in self.parser.validate(data) if i["level"] == "Error"}
		self.assertIn("AWB_SERIAL_LENGTH", codes)

	def test_validate_bad_checkdigit(self):
		# 12345676 — check digit should be 5, not 6
		bad = SAMPLE_62.replace("057-12345675", "057-12345676")
		data = self.parser.parse(bad)
		codes = {i["code"] for i in self.parser.validate(data) if i["level"] == "Warning"}
		self.assertIn("AWB_CHECKDIGIT", codes)

	def test_validate_good_checkdigit_no_warning(self):
		data = self.parser.parse(SAMPLE_62)
		codes = {i["code"] for i in self.parser.validate(data) if i["level"] == "Warning"}
		self.assertNotIn("AWB_CHECKDIGIT", codes)

	def test_validate_same_origin_dest_warning(self):
		bad = SAMPLE_62.replace("057-12345675BHXJFK", "057-12345675JFKJFK")
		data = self.parser.parse(bad)
		codes = {i["code"] for i in self.parser.validate(data) if i["level"] == "Warning"}
		self.assertIn("AWB_ROUTE", codes)

	# ----------------------------------------------------------------- validate: flight errors

	def test_validate_no_flights(self):
		data = self.parser.parse("FFA/6\n057-12345675BHXJFK/T5K400\nREF/BHXFRBA\n")
		codes = {i["code"] for i in self.parser.validate(data) if i["level"] == "Error"}
		self.assertIn("NO_FLIGHTS", codes)

	def test_validate_bad_alloc_code(self):
		raw = "FFA/6\n057-12345675BHXJFK/T5K400\nAF077/19MAY/CDGJFK/ZZ\nREF/BHXFRBA\n"
		data = self.parser.parse(raw)
		codes = {i["code"] for i in self.parser.validate(data) if i["level"] == "Error"}
		self.assertIn("ALLOC_CODE", codes)

	def test_validate_all_valid_alloc_codes(self):
		for code in ("NN", "NA", "SS", "CA", "XX", "HK", "HL", "HN", "KK", "UU", "UN", "LL"):
			raw = f"FFA/6\n057-12345675BHXJFK/T5K400\nAF077/19MAY/CDGJFK/{code}\nREF/BHXFRBA\n"
			data = self.parser.parse(raw)
			alloc_errors = [
				i for i in self.parser.validate(data)
				if i["level"] == "Error" and i["code"] == "ALLOC_CODE"
			]
			self.assertEqual(alloc_errors, [], f"Code {code} should be valid")

	def test_validate_same_dep_arr_warning(self):
		raw = "FFA/6\n057-12345675BHXJFK/T5K400\nAF077/19MAY/JFKJFK/UU\nREF/BHXFRBA\n"
		data = self.parser.parse(raw)
		codes = {i["code"] for i in self.parser.validate(data) if i["level"] == "Warning"}
		self.assertIn("FLIGHT_ROUTE", codes)

	# ----------------------------------------------------------------- validate: REF

	def test_validate_missing_ref(self):
		data = self.parser.parse("FFA/6\n057-12345675BHXJFK/T5K400\nAF077/19MAY/CDGJFK/UU\n")
		codes = {i["code"] for i in self.parser.validate(data) if i["level"] == "Error"}
		self.assertIn("REF_MISSING", codes)

	# ----------------------------------------------------------------- validate: zero pieces

	def test_validate_zero_pieces_info(self):
		raw = "FFA/6\n057-12345675BHXJFK/T0K400\nAF077/19MAY/CDGJFK/UU\nREF/BHXFRBA\n"
		data = self.parser.parse(raw)
		codes = {i["code"] for i in self.parser.validate(data) if i["level"] == "Info"}
		self.assertIn("ZERO_PIECES", codes)

	def test_validate_nonzero_pieces_no_info(self):
		data = self.parser.parse(SAMPLE_62)
		codes = {i["code"] for i in self.parser.validate(data) if i["level"] == "Info"}
		self.assertNotIn("ZERO_PIECES", codes)


# ---------------------------------------------------------------------------
# DB-backed process tests
# ---------------------------------------------------------------------------


def _ensure(doctype, name, values):
	if not frappe.db.exists(doctype, name):
		frappe.get_doc({"doctype": doctype, **values}).insert(ignore_permissions=True)


def _seed_airline(code):
	_ensure("Airline", code, {"airline_prefix": code, "carrier_code": code})


def _seed_airport(code):
	_ensure("Airport", code, {"iata_code": code})


def _make_shipment(prefix, serial, origin, dest, flight_rows=None):
	name = f"{prefix}-{serial}"
	if frappe.db.exists("Shipment", name):
		return frappe.get_doc("Shipment", name)
	doc = frappe.new_doc("Shipment")
	doc.airline_prefix = prefix
	doc.awb_serial_number = serial
	doc.origin = origin
	doc.destination = dest
	for row in flight_rows or []:
		doc.append("flight_bookings", row)
	doc.flags.ignore_permissions = True
	doc.save()
	return doc


class TestFFAParserProcess(FrappeTestCase):
	def setUp(self):
		self.parser = FFAParser()
		for code in ("AF", "AC"):
			_seed_airline(code)
		for code in ("BHX", "JFK", "CDG", "LHR", "YYZ", "HKG", "YSB"):
			_seed_airport(code)

	# ----------------------------------------------------------------- process: basic

	def test_process_updates_existing_flight_row(self):
		_seed_airline("AF")
		_seed_airport("BHX")
		_seed_airport("JFK")
		_seed_airport("CDG")
		doc = _make_shipment(
			"057", "12345675", "BHX", "JFK",
			[{"carrier": "AF", "flight_number": "077", "flight_day": "19", "flight_month": "MAY"}],
		)
		data = self.parser.parse(SAMPLE_PROCESS)
		self.parser.process(data, None)

		doc = frappe.get_doc("Shipment", "057-12345675")
		self.assertEqual(len(doc.flight_bookings), 1)
		row = doc.flight_bookings[0]
		self.assertEqual(row.space_allocation_code, "KK")

	def test_process_fills_dep_arr_airports_on_existing_row(self):
		_seed_airline("AF")
		_seed_airport("CDG")
		doc = _make_shipment(
			"057", "12345675", "BHX", "JFK",
			[{"carrier": "AF", "flight_number": "077", "flight_day": "19", "flight_month": "MAY"}],
		)
		data = self.parser.parse(SAMPLE_PROCESS)
		self.parser.process(data, None)

		doc = frappe.get_doc("Shipment", "057-12345675")
		row = doc.flight_bookings[0]
		self.assertEqual(row.departure_airport, "CDG")
		self.assertEqual(row.arrival_airport, "JFK")

	def test_process_does_not_overwrite_existing_dep_arr(self):
		_seed_airline("AF")
		_seed_airport("CDG")
		doc = _make_shipment(
			"057", "12345675", "BHX", "JFK",
			[{
				"carrier": "AF",
				"flight_number": "077",
				"flight_day": "19",
				"flight_month": "MAY",
				"departure_airport": "CDG",
				"arrival_airport": "JFK",
			}],
		)
		# Change what the FFA says about dep/arr — existing values must not be overwritten
		raw = SAMPLE_PROCESS.replace("AF077/19MAY/CDGJFK/KK", "AF077/19MAY/LHRJFK/KK")
		_seed_airport("LHR")
		data = self.parser.parse(raw)
		self.parser.process(data, None)

		doc = frappe.get_doc("Shipment", "057-12345675")
		row = doc.flight_bookings[0]
		self.assertEqual(row.departure_airport, "CDG")  # unchanged

	def test_process_appends_new_flight_row_when_no_match(self):
		_make_shipment("057", "12345675", "BHX", "JFK")
		data = self.parser.parse(SAMPLE_PROCESS)
		self.parser.process(data, None)

		doc = frappe.get_doc("Shipment", "057-12345675")
		self.assertEqual(len(doc.flight_bookings), 1)
		row = doc.flight_bookings[0]
		self.assertEqual(row.flight_number, "077")
		self.assertEqual(row.space_allocation_code, "KK")

	def test_process_missing_shipment_raises(self):
		# Ensure the AWB doesn't exist
		if frappe.db.exists("Shipment", "999-99999995"):
			frappe.delete_doc("Shipment", "999-99999995", force=True, ignore_permissions=True)
		raw = "FFA/6\n999-99999995JFKLHR/T1K10\nBA001/01JAN/JFKLHR/KK\nREF/JFKFRBA\n"
		data = self.parser.parse(raw)
		with self.assertRaises(Exception):
			self.parser.process(data, None)

	def test_process_multi_flight(self):
		_seed_airline("AC")
		_seed_airport("LHR")
		_seed_airport("YYZ")
		_seed_airport("YSB")
		_make_shipment(
			"160", "76543213", "HKG", "YSB",
			[
				{"carrier": "AC", "flight_number": "857", "flight_day": "19", "flight_month": "MAR"},
				{"carrier": "AC", "flight_number": "363", "flight_day": "20", "flight_month": "MAR"},
			],
		)
		data = self.parser.parse(SAMPLE_MULTI_PROCESS)
		self.parser.process(data, None)

		doc = frappe.get_doc("Shipment", "160-76543213")
		codes = {row.flight_number: row.space_allocation_code for row in doc.flight_bookings}
		self.assertEqual(codes.get("857"), "KK")
		self.assertEqual(codes.get("363"), "UU")

	# ----------------------------------------------------------------- process: idempotent

	def test_process_is_idempotent(self):
		_make_shipment("057", "12345675", "BHX", "JFK")
		data = self.parser.parse(SAMPLE_PROCESS)
		self.parser.process(data, None)
		self.parser.process(data, None)

		doc = frappe.get_doc("Shipment", "057-12345675")
		self.assertEqual(len(doc.flight_bookings), 1)

	# ----------------------------------------------------------------- process: SSR / OSI

	def test_process_ssr_appended(self):
		_make_shipment("057", "12345675", "BHX", "JFK")
		raw = (
			"FFA/6\n057-12345675BHXJFK/T5K400\nAF077/19MAY/CDGJFK/KK\n"
			"SSR/HANDLE WITH CARE\nREF/BHXFRBA\n"
		)
		data = self.parser.parse(raw)
		self.parser.process(data, None)

		doc = frappe.get_doc("Shipment", "057-12345675")
		ssr_texts = [r.special_service_request for r in doc.special_service_requests]
		self.assertIn("HANDLE WITH CARE", ssr_texts)

	def test_process_ssr_not_duplicated(self):
		# Insert a Shipment that already has the SSR text
		doc = _make_shipment("057", "12345675", "BHX", "JFK")
		doc.append("special_service_requests", {"special_service_request": "HANDLE WITH CARE"})
		doc.flags.ignore_permissions = True
		doc.save()

		raw = (
			"FFA/6\n057-12345675BHXJFK/T5K400\nAF077/19MAY/CDGJFK/KK\n"
			"SSR/HANDLE WITH CARE\nREF/BHXFRBA\n"
		)
		data = self.parser.parse(raw)
		self.parser.process(data, None)

		doc = frappe.get_doc("Shipment", "057-12345675")
		count = sum(
			1 for r in doc.special_service_requests if r.special_service_request == "HANDLE WITH CARE"
		)
		self.assertEqual(count, 1)

	# ----------------------------------------------------------------- process: REF → header

	def test_process_ref_written_to_header(self):
		_make_shipment("057", "12345675", "BHX", "JFK")
		data = self.parser.parse(SAMPLE_PROCESS)
		self.parser.process(data, None)

		doc = frappe.get_doc("Shipment", "057-12345675")
		self.assertEqual(doc.sender_office_address, "BHXFRBA")

	def test_process_ref_file_reference_written(self):
		_make_shipment("057", "12345675", "BHX", "JFK")
		data = self.parser.parse(SAMPLE_62)
		self.parser.process(data, None)

		doc = frappe.get_doc("Shipment", "057-12345675")
		self.assertEqual(doc.sender_file_reference, "1234")

	# ----------------------------------------------------------------- process: airport stubs

	def test_process_creates_airport_stubs(self):
		stub_code = "ZZZ"
		if frappe.db.exists("Airport", stub_code):
			frappe.delete_doc("Airport", stub_code, force=True, ignore_permissions=True)
		_make_shipment("057", "12345675", "BHX", "JFK")
		raw = f"FFA/6\n057-12345675BHXJFK/T5K400\nAF077/19MAY/{stub_code}JFK/KK\nREF/BHXFRBA\n"
		data = self.parser.parse(raw)
		self.parser.process(data, None)

		self.assertTrue(frappe.db.exists("Airport", stub_code))

	def test_process_creates_airline_stub(self):
		stub_code = "ZQ"
		if frappe.db.exists("Airline", stub_code):
			frappe.delete_doc("Airline", stub_code, force=True, ignore_permissions=True)
		_ensure("Airport", "LAX", {"iata_code": "LAX"})
		_make_shipment("085", "12345675", "ZRH", "LAX")
		raw = f"FFA/6\n085-12345675ZRHLAX/T1K10\n{stub_code}123/10MAY/JFKLAX/LL\nREF/ZRHFRSR\n"
		_seed_airport("ZRH")
		data = self.parser.parse(raw)
		self.parser.process(data, None)

		self.assertTrue(frappe.db.get_value("Airline", {"carrier_code": stub_code}, "name"))

	# ----------------------------------------------------------------- process: month matching

	def test_process_matches_row_without_month(self):
		"""Flight row created without a month (e.g. by FWB) is matched by FFA on carrier+flight+day."""
		_seed_airline("AF")
		doc = _make_shipment(
			"057", "12345675", "BHX", "JFK",
			[{"carrier": "AF", "flight_number": "077", "flight_day": "19"}],
		)
		data = self.parser.parse(SAMPLE_PROCESS)
		self.parser.process(data, None)

		doc = frappe.get_doc("Shipment", "057-12345675")
		self.assertEqual(doc.flight_bookings[0].space_allocation_code, "KK")
