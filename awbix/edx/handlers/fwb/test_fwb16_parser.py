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


# A message exercising every FWB/16 segment group, used to prove full coverage.
FULL_SAMPLE = """FWB/16
157-68076960BSLDOH/T2K500MC1.5
FLT/QR0205/15/QR0608/16
RTG/ZRHQR/DOHQR
SHP
/HOFFMANN LA ROCHE LTD
/GRENZACHERSTRASSE 124
/BASEL/BS
/CH/4070
/TE/41611234567
CNE
/EBN SINA MEDICAL
/MEDICAL STREET 1
/DOHA
/QA/00000
AGT/12345/8147158/4003/AB
/DSV AIR SEA AG
/BASEL
SSR
/HANDLE WITH CARE
NFY
/NOTIFY PARTY LTD
/NOTIFY STREET
/DOHA
/QA/12345
/TE/97412345
ACC
/GEN/PAYMENT BY CASH
CVD/CHF/CC/PP/NVD/NCV/XXX
RTD
/1/P2/K500/CQ/W500/R5.50/T2750
/1/NG/ELECTRONIC EQUIPMENT
/1/ND/K500/CMT120-80-100/2
/1/NV/MC1.5
/1/NH/847130
/1/NO/CH/E
OTH
/P/MYA50.00
PPD
/WT2750/VC10
/CT2760
CER/JOHN SHIPPER
ISU/15JUN26/BSL/QR AGENT
OSI
/GENERAL INFO
CDC/USD1.085/2500/100/2600
REF/BSLFFQR/MYFILE123
COR/US
COI///5
SII/100/CI
ARD/AGENTREF99
SPH/PER/EAW
NOM/HANDLING CO/DOHA
SRI/REF12345/SUPP1/SUPP2
OPI/OTHER PARTICIPANT
//FILEREF/AB/PARTCODE/BSL
OCI/CH/CT/T/EORI12345
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

	def test_awb_consignment_detail(self):
		awb = self.data["awb"]
		self.assertEqual(awb["shipment_description_code"], "T")
		self.assertEqual(awb["number_of_pieces"], 1)
		self.assertEqual(awb["weight_code"], "K")
		self.assertEqual(awb["weight"], 40.0)

	def test_awb_volume_is_captured(self):
		# Regression: the volume suffix (MC0.36) used to be silently dropped.
		awb = self.data["awb"]
		self.assertEqual(awb["volume_code"], "MC")
		self.assertEqual(awb["volume_amount"], 0.36)

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
		self.assertEqual(self.data["shipper"]["address"], "GRENZACHERSTRASSE 124")
		self.assertEqual(self.data["consignee"]["name"], "M S  EBN SINA MEDICAL")
		self.assertEqual(self.data["agent"]["name"], "DSV AIR  SEA AG")
		self.assertEqual(self.data["agent"]["iata_code"], "8147158")
		self.assertEqual(self.data["agent"]["cass_address"], "4003")
		self.assertEqual(self.data["charge_declarations"]["currency"], "CHF")

	def test_cvd_prepaid_collect_and_declared_values(self):
		cvd = self.data["charge_declarations"]
		self.assertEqual(cvd["wt_val_prepaid_collect"], "P")
		self.assertEqual(cvd["other_charges_prepaid_collect"], "P")
		self.assertEqual(cvd["declared_value_carriage_type"], "NVD")
		self.assertEqual(cvd["declared_value_customs_type"], "NCV")
		self.assertEqual(cvd["insurance_type"], "XXX")

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


class TestFWB16ParserFullCoverage(FrappeTestCase):
	"""Parse a message that uses every segment group and assert each is captured."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.data = FWB16Parser().parse(FULL_SAMPLE)

	def test_awb_quantity_and_volume(self):
		awb = self.data["awb"]
		self.assertEqual(awb["number_of_pieces"], 2)
		self.assertEqual(awb["weight"], 500.0)
		self.assertEqual(awb["volume_code"], "MC")
		self.assertEqual(awb["volume_amount"], 1.5)

	def test_flight_bookings(self):
		self.assertEqual(
			self.data["flights"],
			[
				{"carrier": "QR", "flight_number": "0205", "day": 15},
				{"carrier": "QR", "flight_number": "0608", "day": 16},
			],
		)

	def test_shipper_full_address_and_contact(self):
		shp = self.data["shipper"]
		self.assertEqual(shp["name"], "HOFFMANN LA ROCHE LTD")
		self.assertEqual(shp["address"], "GRENZACHERSTRASSE 124")
		self.assertEqual(shp["place"], "BASEL")
		self.assertEqual(shp["state"], "BS")
		self.assertEqual(shp["country"], "CH")
		self.assertEqual(shp["post_code"], "4070")
		self.assertEqual(shp["contacts"], [{"identifier": "TE", "number": "41611234567"}])

	def test_agent_participant(self):
		agt = self.data["agent"]
		self.assertEqual(agt["account"], "12345")
		self.assertEqual(agt["iata_code"], "8147158")
		self.assertEqual(agt["cass_address"], "4003")
		self.assertEqual(agt["participant_id"], "AB")
		self.assertEqual(agt["place"], "BASEL")

	def test_notify_and_ssr_and_accounting(self):
		self.assertEqual(self.data["also_notify"][0]["name"], "NOTIFY PARTY LTD")
		self.assertEqual(self.data["also_notify"][0]["contacts"][0]["number"], "97412345")
		self.assertEqual(self.data["ssr"], ["HANDLE WITH CARE"])
		self.assertEqual(self.data["accounting"], [{"identifier": "GEN", "information": "PAYMENT BY CASH"}])

	def test_cvd_charge_code(self):
		self.assertEqual(self.data["charge_declarations"]["charge_code"], "CC")

	def test_rate_line(self):
		rl = self.data["rate_lines"][0]
		self.assertEqual(rl["line_number"], 1)
		self.assertEqual(rl["number_of_pieces"], 2)
		self.assertEqual(rl["gross_weight"], 500.0)
		self.assertEqual(rl["rate_class_code"], "Q")
		self.assertEqual(rl["chargeable_weight"], 500.0)
		self.assertEqual(rl["rate_charge"], 5.5)
		self.assertEqual(rl["total"], 2750.0)

	def test_goods_details(self):
		goods = {g["goods_data_identifier"]: g for g in self.data["goods"]}
		self.assertEqual(goods["G"]["description"], "ELECTRONIC EQUIPMENT")
		self.assertEqual(goods["D"]["measurement_unit"], "CMT")
		self.assertEqual(goods["D"]["dim_length"], 120.0)
		self.assertEqual(goods["D"]["dim_width"], 80.0)
		self.assertEqual(goods["D"]["dim_height"], 100.0)
		self.assertEqual(goods["D"]["dim_pieces"], 2)
		self.assertEqual(goods["V"]["volume_code"], "MC")
		self.assertEqual(goods["V"]["volume_amount"], 1.5)
		self.assertEqual(goods["H"]["hs_code"], "847130")
		self.assertEqual(goods["O"]["country_of_origin"], "CH")
		self.assertEqual(goods["O"]["service_code"], "E")  # trailing DE505 service code

	def test_other_charges(self):
		self.assertEqual(
			self.data["other_charges"],
			[{"prepaid_collect": "P", "other_charge_code": "MY", "entitlement_code": "A", "amount": 50.0}],
		)

	def test_charge_summary(self):
		summary = {(r["settlement"], r["charge_identifier"]): r["amount"] for r in self.data["charge_summary"]}
		self.assertEqual(summary[("Prepaid", "WT")], 2750.0)
		self.assertEqual(summary[("Prepaid", "VC")], 10.0)
		self.assertEqual(summary[("Prepaid", "CT")], 2760.0)

	def test_certification_and_execution(self):
		self.assertEqual(self.data["certification"]["signature"], "JOHN SHIPPER")
		self.assertEqual(self.data["execution"]["issue_date"], "2026-06-15")
		self.assertEqual(self.data["execution"]["issue_place"], "BSL")
		self.assertEqual(self.data["execution"]["signature"], "QR AGENT")

	def test_osi_and_cdc(self):
		self.assertEqual(self.data["osi"], ["GENERAL INFO"])
		cdc = self.data["cdc"]
		self.assertEqual(cdc["dest_currency"], "USD")
		self.assertEqual(cdc["rate_of_exchange"], 1.085)
		self.assertEqual(cdc["cc_charges_dest"], 2500.0)
		self.assertEqual(cdc["total_collect_charges"], 2600.0)

	def test_references_and_customs(self):
		ref = self.data["sender_reference"]
		self.assertEqual(ref["office_address"], "BSLFFQR")
		self.assertEqual(ref["file_reference"], "MYFILE123")
		self.assertEqual(self.data["customs_origin"]["code"], "US")
		self.assertEqual(self.data["nominated_handling"], {"name": "HANDLING CO", "place": "DOHA"})

	def test_commission_incentive_agent_ref(self):
		self.assertEqual(self.data["commission"]["percentage"], 5.0)
		self.assertEqual(self.data["sales_incentive"]["amount"], 100.0)
		self.assertEqual(self.data["sales_incentive"]["indicator"], "CI")
		self.assertEqual(self.data["agent_reference"]["reference"], "AGENTREF99")

	def test_special_handling(self):
		self.assertEqual(self.data["special_handling"], ["PER", "EAW"])

	def test_references_table(self):
		self.assertEqual(
			self.data["references"],
			[{"reference_number": "REF12345", "supplementary_1": "SUPP1", "supplementary_2": "SUPP2"}],
		)

	def test_other_participants(self):
		opi = self.data["other_participants"][0]
		self.assertEqual(opi["name"], "OTHER PARTICIPANT")
		self.assertEqual(opi["office_file_reference"], "FILEREF")
		self.assertEqual(opi["participant_id"], "AB")
		self.assertEqual(opi["participant_code"], "PARTCODE")
		self.assertEqual(opi["airport"], "BSL")

	def test_oci(self):
		self.assertEqual(
			self.data["oci"],
			[{
				"country": "CH",
				"information_identifier": "CT",
				"customs_info_identifier": "T",
				"supplementary": "EORI12345",
			}],
		)


# RTD sample using real-world sequential line numbering: the NC description for
# rate line 1 has no explicit line-number prefix, and subsequent goods lines carry
# sequential RTD counters (/2/, /3/, …) rather than the rate-line number.
SEQUENTIAL_RTD_SAMPLE = """FWB/16
157-41510976DACFRA/T108K1599MC7.957
FLT/QR639/04
RTG/DOHQR/FRAQR
SHP
/CONTAINER TRANSPORTATION SERVICES L
/NAFI TOWER  LEVEL-12  53  GULSHAN A
/DHAKA
/BD/1212
CNE
/HELLMANN WORLDWIDE LOGISTICS GERMAN
/ADMIRAL-ROSENDAHL-STRASSE 11
/FRANKFURT
/DE/63263/TE/49696952160
AGT/4273595/0000000
/CONTAINER TRANSPORTATION SERVICES L
/DHAKA
CVD/USD//PP/NVD/NCV/XXX
RTD/1/P108/K1599/CQ/S2199/W1599/R4.2/T6715.8
/NC/CONSOL OF GARMENTS
/2/NH/620711
/3/NH/61082100
/4/NH/620333
/5/NV/MC7.957
/6/ND//CMT58-40-38/52
/7/ND//CMT58-40-30/5
OTH/P/AHC31.98FEC127.92SCC127.92
PPD/WT6715.8
/CT7028.89
ISU/03JUN26/DHAKA/CONTAINER TRANSPORTA
"""


class TestFWB16ParserSequentialRTD(FrappeTestCase):
	"""RTD with implicit NC description and sequential goods-line counters."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.data = FWB16Parser().parse(SEQUENTIAL_RTD_SAMPLE)

	def test_rate_line(self):
		rl = self.data["rate_lines"][0]
		self.assertEqual(rl["line_number"], 1)
		self.assertEqual(rl["number_of_pieces"], 108)
		self.assertEqual(rl["gross_weight"], 1599.0)
		self.assertEqual(rl["rate_class_code"], "Q")
		self.assertEqual(rl["commodity_item_number"], "2199")
		self.assertEqual(rl["chargeable_weight"], 1599.0)
		self.assertEqual(rl["rate_charge"], 4.2)
		self.assertEqual(rl["total"], 6715.8)

	def test_nc_description_captured_for_rate_line_1(self):
		# /NC/CONSOL OF GARMENTS has no line-number prefix; must be associated with
		# rate line 1 and stored with goods_data_identifier='C'.
		goods = {g["goods_data_identifier"]: g for g in self.data["goods"]}
		self.assertIn("C", goods)
		self.assertEqual(goods["C"]["description"], "CONSOL OF GARMENTS")
		self.assertEqual(goods["C"]["rate_line_number"], 1)

	def test_sequential_goods_lines_associated_with_rate_line_1(self):
		# /2/NH/... through /7/ND/... carry sequential RTD counters, not rate-line
		# refs; all must be linked to rate line 1.
		for g in self.data["goods"]:
			self.assertEqual(g["rate_line_number"], 1)

	def test_hs_codes(self):
		hs_codes = {g["hs_code"] for g in self.data["goods"] if g.get("hs_code")}
		self.assertEqual(hs_codes, {"620711", "61082100", "620333"})

	def test_volume(self):
		goods = {g["goods_data_identifier"]: g for g in self.data["goods"]}
		self.assertEqual(goods["V"]["volume_code"], "MC")
		self.assertEqual(goods["V"]["volume_amount"], 7.957)

	def test_dimensions(self):
		dim_rows = [g for g in self.data["goods"] if g.get("goods_data_identifier") == "D"]
		self.assertEqual(len(dim_rows), 2)
		first = dim_rows[0]
		self.assertEqual(first["measurement_unit"], "CMT")
		self.assertEqual(first["dim_length"], 58.0)
		self.assertEqual(first["dim_width"], 40.0)
		self.assertEqual(first["dim_height"], 38.0)
		self.assertEqual(first["dim_pieces"], 52)
