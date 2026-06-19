"""Tests for FHLParser — pure parse/validate (no DB) and DB-backed process."""

import frappe
from frappe.tests.utils import FrappeTestCase

from awbix.edx.handlers.fhl.fhl_parser import FHLParser

# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

# Single-house expanded message (mirrors fhl sample message 1.txt)
SAMPLE_SINGLE = """FHL/5
MBI/157-67661882BLRCDG/T3K99.0
HBS/530510258554/BLRCDG/2/K64.0//HOSE ASSEMBLY
TXT/INVOICE NOS E-IN 26-27 0193
HTS/88079000
OCI//CNE/T/FR42091691800063
SHP
NAM/STS TITEFLEX INDIA PVT LTD
ADR/38KIADB INDUSTRIAL AREA
LOC/BANGALORE/KA
/IN/561203
CNE
NAM/AIRBUS OPERATIONS S.A.
ADR/AD34301385 TSA 5008
LOC/TOULOUSE
/FR/31060
CVD/INR/PP/NVD/NCV/XXX
"""

# Bare check-list: three HBS blocks, no sub-groups (CIMP manual §6.1)
SAMPLE_CHECKLIST = """FHL/5
MBI/220-12345675FRAJFK/T1234K10000
HBS/11AA11111111/FRABOS/1000/K8000//NUTS
HBS/22AA12121212/FRAJFK/200/K1800//BOLTS
HBS/33AA13131313/FRAORD/34/K200//SCREWS
"""

# Multi-line OCI with continuation qualifiers (mirrors fhl sample message 2.txt)
SAMPLE_OCI = """FHL/5
MBI/157-43426040AMSORD/T7K837.2
HBS/AMS00004138/AMSORD/7/K837.2/7/ELECTROSTATIC P
TXT/ELECTROSTATIC POWDER COATING EQUIPMENT
HTS/842489
OCI/US/CNE/CT/00140434565678
/NL/ISS/RA/00324-00
///ED/1026
///SM/EDD
///SN/PMT
SHP
NAM/GEMA SWITZERLAND GMBH
ADR/MOVENSTRASSE 17
LOC/ST GALLEN
/CH/9015
CNE
NAM/GEMA USA
ADR/4141 WEST 54TH STREET
LOC/INDIANAPOLIS/IN
/US/46254/TE/00140434565678
CVD/EUR/PP/NVD/NCV/XXX
"""

# HBS with SPH continuation codes
SAMPLE_SPH = """FHL/5
MBI/157-43426040AMSORD/T1K50.0
HBS/SAMSA0009420/AMSORD/1/K50.0//DANGEROUS GOOD
/SPX/EAW
CVD/EUR/PP/NVD/NCV/XXX
"""


class TestFHLParserPure(FrappeTestCase):
	"""Pure parse/validate tests — no DB required."""

	def setUp(self):
		self.parser = FHLParser()

	# ---------------------------------------------------------------- master

	def test_master_fields_single(self):
		data = self.parser.parse(SAMPLE_SINGLE)
		master = data["master"]
		self.assertEqual(master["airline_prefix"], "157")
		self.assertEqual(master["awb_serial_number"], "67661882")
		self.assertEqual(master["awb_number"], "157-67661882")
		self.assertEqual(master["origin"], "BLR")
		self.assertEqual(master["destination"], "CDG")
		self.assertEqual(master["pieces"], 3)
		self.assertEqual(master["weight_code"], "K")
		self.assertAlmostEqual(master["weight"], 99.0)

	def test_business_key(self):
		data = self.parser.parse(SAMPLE_SINGLE)
		self.assertEqual(self.parser.business_key(data), "157-67661882")

	# ---------------------------------------------------------------- houses

	def test_single_house_fields(self):
		data = self.parser.parse(SAMPLE_SINGLE)
		self.assertEqual(len(data["houses"]), 1)
		h = data["houses"][0]
		self.assertEqual(h["hwb_serial_number"], "530510258554")
		self.assertEqual(h["hwb_origin"], "BLR")
		self.assertEqual(h["hwb_destination"], "CDG")
		self.assertEqual(h["number_of_pieces"], 2)
		self.assertEqual(h["weight_code"], "K")
		self.assertAlmostEqual(h["weight"], 64.0)
		self.assertIsNone(h["slac"])
		self.assertEqual(h["manifest_description"], "HOSE ASSEMBLY")

	def test_single_house_txt_hts(self):
		data = self.parser.parse(SAMPLE_SINGLE)
		h = data["houses"][0]
		self.assertEqual(len(h["free_text"]), 1)
		self.assertIn("INVOICE", h["free_text"][0]["free_text"])
		self.assertEqual(len(h["hs_codes"]), 1)
		self.assertEqual(h["hs_codes"][0]["hs_code"], "88079000")

	def test_single_house_oci(self):
		data = self.parser.parse(SAMPLE_SINGLE)
		oci = data["houses"][0]["oci"]
		self.assertEqual(len(oci), 1)
		self.assertEqual(oci[0]["information_identifier"], "CNE")
		self.assertEqual(oci[0]["customs_info_identifier"], "T")
		self.assertEqual(oci[0]["supplementary"], "FR42091691800063")

	def test_single_house_parties(self):
		data = self.parser.parse(SAMPLE_SINGLE)
		h = data["houses"][0]
		self.assertEqual(h["shipper"]["name"], "STS TITEFLEX INDIA PVT LTD")
		self.assertEqual(h["shipper"]["address"], "38KIADB INDUSTRIAL AREA")
		self.assertEqual(h["shipper"]["place"], "BANGALORE")
		self.assertEqual(h["shipper"]["state"], "KA")
		self.assertEqual(h["shipper"]["country"], "IN")
		self.assertEqual(h["shipper"]["post_code"], "561203")

		self.assertEqual(h["consignee"]["name"], "AIRBUS OPERATIONS S.A.")
		self.assertEqual(h["consignee"]["place"], "TOULOUSE")
		self.assertEqual(h["consignee"]["country"], "FR")
		self.assertEqual(h["consignee"]["post_code"], "31060")

	def test_single_house_cvd(self):
		data = self.parser.parse(SAMPLE_SINGLE)
		cvd = data["houses"][0]["charge_declarations"]
		self.assertEqual(cvd["currency"], "INR")
		self.assertEqual(cvd["wt_val_prepaid_collect"], "P")
		self.assertEqual(cvd["other_charges_prepaid_collect"], "P")
		self.assertEqual(cvd["declared_value_carriage_type"], "NVD")
		self.assertIsNone(cvd["declared_value_carriage_amount"])
		self.assertEqual(cvd["declared_value_customs_type"], "NCV")
		self.assertEqual(cvd["insurance_type"], "XXX")

	# ---------------------------------------------------------------- checklist

	def test_checklist_three_houses(self):
		data = self.parser.parse(SAMPLE_CHECKLIST)
		self.assertEqual(data["master"]["awb_number"], "220-12345675")
		self.assertEqual(len(data["houses"]), 3)
		serials = [h["hwb_serial_number"] for h in data["houses"]]
		self.assertEqual(serials, ["11AA11111111", "22AA12121212", "33AA13131313"])

	def test_checklist_no_parties(self):
		data = self.parser.parse(SAMPLE_CHECKLIST)
		for h in data["houses"]:
			self.assertEqual(h["shipper"], {})
			self.assertEqual(h["consignee"], {})

	def test_checklist_piece_weights(self):
		data = self.parser.parse(SAMPLE_CHECKLIST)
		self.assertEqual(data["houses"][0]["number_of_pieces"], 1000)
		self.assertAlmostEqual(data["houses"][0]["weight"], 8000.0)
		self.assertEqual(data["houses"][1]["number_of_pieces"], 200)
		self.assertAlmostEqual(data["houses"][1]["weight"], 1800.0)

	# ---------------------------------------------------------------- OCI multi-line

	def test_oci_continuations_preserved(self):
		data = self.parser.parse(SAMPLE_OCI)
		oci = data["houses"][0]["oci"]
		# First row: OCI/US/CNE/CT/00140434565678
		self.assertEqual(oci[0]["information_identifier"], "CNE")
		self.assertEqual(oci[0]["customs_info_identifier"], "CT")
		self.assertEqual(oci[0]["supplementary"], "00140434565678")
		# Second row continuation: /NL/ISS/RA/00324-00
		self.assertEqual(oci[1]["information_identifier"], "ISS")
		self.assertEqual(oci[1]["customs_info_identifier"], "RA")
		# Third row: ///ED/1026 → country="", info_id="", customs_id="ED"
		self.assertEqual(oci[2]["country"], "")
		self.assertEqual(oci[2]["information_identifier"], "")
		self.assertEqual(oci[2]["customs_info_identifier"], "ED")
		self.assertEqual(oci[2]["supplementary"], "1026")

	def test_oci_contact_in_loc(self):
		data = self.parser.parse(SAMPLE_OCI)
		cne = data["houses"][0]["consignee"]
		self.assertEqual(cne["contact_id"], "TE")
		self.assertEqual(cne["contact_number"], "00140434565678")

	# ---------------------------------------------------------------- SPH

	def test_sph_codes_parsed(self):
		data = self.parser.parse(SAMPLE_SPH)
		sph = data["houses"][0]["special_handling"]
		codes = [r["code"] for r in sph]
		self.assertIn("SPX", codes)
		self.assertIn("EAW", codes)

	def test_slac_parsed(self):
		data = self.parser.parse(SAMPLE_OCI)
		self.assertEqual(data["houses"][0]["slac"], 7)

	# ---------------------------------------------------------------- validate (positive)

	def test_valid_message_no_errors(self):
		data = self.parser.parse(SAMPLE_SINGLE)
		errors = [i for i in self.parser.validate(data) if i["level"] == "Error"]
		self.assertEqual(errors, [])

	def test_checklist_currency_warning(self):
		data = self.parser.parse(SAMPLE_CHECKLIST)
		# Bare checklist has no CVD → CURRENCY warnings
		codes = {i["code"] for i in self.parser.validate(data) if i["level"] == "Warning"}
		self.assertIn("CURRENCY", codes)

	# ---------------------------------------------------------------- validate (negative)

	def test_bad_master_check_digit(self):
		bad = SAMPLE_SINGLE.replace("MBI/157-67661882", "MBI/157-67661889")
		data = self.parser.parse(bad)
		codes = {i["code"] for i in self.parser.validate(data) if i["level"] == "Error"}
		self.assertIn("AWB_CHECKDIGIT", codes)

	def test_no_house_block_flagged(self):
		no_house = "FHL/5\nMBI/157-67661882BLRCDG/T3K99.0\n"
		data = self.parser.parse(no_house)
		codes = {i["code"] for i in self.parser.validate(data) if i["level"] == "Error"}
		self.assertIn("NO_HOUSE", codes)

	def test_duplicate_house_serial_flagged(self):
		dup = """FHL/5
MBI/220-12345675FRAJFK/T2K100.0
HBS/DUPE0001/FRAJFK/1/K50.0//GOODS A
HBS/DUPE0001/FRAJFK/1/K50.0//GOODS B
"""
		data = self.parser.parse(dup)
		codes = {i["code"] for i in self.parser.validate(data) if i["level"] == "Error"}
		self.assertIn("HWB_DUP", codes)

	def test_same_origin_destination_flagged(self):
		bad = SAMPLE_SINGLE.replace("HBS/530510258554/BLRCDG", "HBS/530510258554/BLRBLR")
		data = self.parser.parse(bad)
		codes = {i["code"] for i in self.parser.validate(data) if i["level"] == "Error"}
		self.assertIn("HWB_ROUTE", codes)

	def test_unparseable_mbi_flagged(self):
		data = self.parser.parse("FHL/5\nNOTAVALIDMBI\n")
		codes = {i["code"] for i in self.parser.validate(data) if i["level"] == "Error"}
		self.assertIn("MBI", codes)


# ---------------------------------------------------------------------------
# DB-backed process tests
# ---------------------------------------------------------------------------


def _ensure(doctype, name, values):
	if not frappe.db.exists(doctype, name):
		frappe.get_doc({"doctype": doctype, **values}).insert(ignore_permissions=True)


def _seed_masters():
	_ensure("Airline", "157", {"airline_prefix": "157"})
	for code in ("BLR", "CDG"):
		_ensure("Airport", code, {"iata_code": code})
	if not frappe.db.exists("Currency", "INR"):
		frappe.get_doc({"doctype": "Currency", "currency_name": "INR", "enabled": 1}).insert(
			ignore_permissions=True
		)


class TestFHLParserProcess(FrappeTestCase):
	def setUp(self):
		self.parser = FHLParser()
		_seed_masters()

	def test_process_creates_hwb(self):
		data = self.parser.parse(SAMPLE_SINGLE)
		self.parser.process(data, None)

		name = frappe.db.get_value(
			"House Airway Bill",
			{"master_shipment": "157-67661882", "hwb_serial_number": "530510258554"},
			"name",
		)
		self.assertIsNotNone(name)
		doc = frappe.get_doc("House Airway Bill", name)
		self.assertEqual(doc.hwb_origin, "BLR")
		self.assertEqual(doc.hwb_destination, "CDG")
		self.assertEqual(doc.number_of_pieces, 2)
		self.assertAlmostEqual(doc.weight, 64.0)
		self.assertEqual(doc.manifest_description, "HOSE ASSEMBLY")
		self.assertEqual(doc.currency, "INR")

	def test_process_creates_master_shipment_if_missing(self):
		# Remove the master if it exists, then process
		if frappe.db.exists("Shipment", "157-67661882"):
			frappe.delete_doc("Shipment", "157-67661882", force=True, ignore_permissions=True)
		data = self.parser.parse(SAMPLE_SINGLE)
		self.parser.process(data, None)
		self.assertTrue(frappe.db.exists("Shipment", "157-67661882"))

	def test_process_is_idempotent(self):
		data = self.parser.parse(SAMPLE_SINGLE)
		self.parser.process(data, None)
		self.parser.process(data, None)
		count = frappe.db.count(
			"House Airway Bill",
			{"master_shipment": "157-67661882", "hwb_serial_number": "530510258554", "docstatus": ("!=", 2)},
		)
		self.assertEqual(count, 1)

	def test_process_checklist_creates_three_hwbs(self):
		_ensure("Airline", "220", {"airline_prefix": "220"})
		for code in ("FRA", "JFK", "BOS", "ORD"):
			_ensure("Airport", code, {"iata_code": code})
		data = self.parser.parse(SAMPLE_CHECKLIST)
		self.parser.process(data, None)
		count = frappe.db.count(
			"House Airway Bill",
			{"master_shipment": "220-12345675", "docstatus": ("!=", 2)},
		)
		self.assertEqual(count, 3)

	def test_process_stamps_party_fields(self):
		data = self.parser.parse(SAMPLE_SINGLE)
		self.parser.process(data, None)
		name = frappe.db.get_value(
			"House Airway Bill",
			{"master_shipment": "157-67661882", "hwb_serial_number": "530510258554"},
			"name",
		)
		shipper_name = frappe.db.get_value("House Airway Bill", name, "shipper_name")
		self.assertEqual(shipper_name, "STS TITEFLEX INDIA PVT LTD")
