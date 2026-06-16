from frappe.tests.utils import FrappeTestCase

from awbix.edx.handlers.fwb.fwb16_parser import FWB16Parser

SAMPLE = """FWB/16
157-68076960BSLDOH/T1K40MC0.36
RTG/ZRHQR/DOHQR
SHP
/F  HOFFMANN - LA ROCHE LTD
/GRENZACHERSTRASSE 124
CNE
/M S  EBN SINA MEDICAL
AGT//8147158/4003
/DSV AIR  SEA AG
CVD/CHF//PP/NVD/NCV/XXX
"""


class TestFWB16Parser(FrappeTestCase):
	def setUp(self):
		self.parser = FWB16Parser()
		self.data = self.parser.parse(SAMPLE)

	def test_awb_and_business_key(self):
		awb = self.data["awb"]
		self.assertEqual(awb["airline_prefix"], "157")
		self.assertEqual(awb["awb_serial_number"], "68076960")
		self.assertEqual(awb["origin"], "BSL")
		self.assertEqual(awb["destination"], "DOH")
		self.assertEqual(self.parser.business_key(self.data), "157-68076960")

	def test_routing(self):
		self.assertEqual(
			self.data["routing"],
			[
				{"sequence": 1, "airport": "ZRH", "carrier": "QR"},
				{"sequence": 2, "airport": "DOH", "carrier": "QR"},
			],
		)

	def test_parties_and_currency(self):
		self.assertEqual(self.data["shipper"]["name"], "F  HOFFMANN - LA ROCHE LTD")
		self.assertEqual(self.data["consignee"]["name"], "M S  EBN SINA MEDICAL")
		self.assertEqual(self.data["agent"]["name"], "DSV AIR  SEA AG")
		self.assertEqual(self.data["charge_declarations"]["currency"], "CHF")

	def test_valid_message_has_no_errors(self):
		errors = [i for i in self.parser.validate(self.data) if i["level"] == "Error"]
		self.assertEqual(errors, [])

	def test_bad_check_digit_flagged(self):
		bad = self.parser.parse(SAMPLE.replace("157-68076960", "157-68076961"))
		codes = {i["code"] for i in self.parser.validate(bad) if i["level"] == "Error"}
		self.assertIn("AWB_CHECKDIGIT", codes)

	def test_same_origin_destination_flagged(self):
		bad = self.parser.parse(SAMPLE.replace("BSLDOH", "DOHDOH"))
		codes = {i["code"] for i in self.parser.validate(bad) if i["level"] == "Error"}
		self.assertIn("ROUTE", codes)
