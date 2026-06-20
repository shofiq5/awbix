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
		# RTD SecondLine (NG) belongs to the rate-line row, not a separate goods row
		self.assertEqual(rl["goods_data_identifier"], "G")
		self.assertEqual(rl["description"], "ELECTRONIC EQUIPMENT")

	def test_goods_details(self):
		goods = {g["goods_data_identifier"]: g for g in self.data["goods"]}
		# NG (G) is stored in the rate-line row — not present in goods
		self.assertNotIn("G", goods)
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


# Real-world FWB: compact RTD encoding where the NC SecondLine has no line-count
# prefix, and subsequent goods groups carry sequential RTD line counts (2, 3, …).
# Source: AWB 157-42781966, DAC→HAM via DOH.
SEQUENTIAL_RTD_SAMPLE = """FWB/16
157-42781966DACHAM/T40K574MC4.785
RTG/DOHQR/HAMQR
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
"""


class TestFWB16ParserSequentialRTD(FrappeTestCase):
	"""RTD compact encoding: NC SecondLine on rate-line 1 (no line-count prefix);
	subsequent goods groups carry sequential RTD line counts (/2/, /3/, …)."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.data = FWB16Parser().parse(SEQUENTIAL_RTD_SAMPLE)

	def test_rate_line_data(self):
		rl = self.data["rate_lines"][0]
		self.assertEqual(rl["line_number"], 1)
		self.assertEqual(rl["number_of_pieces"], 40)
		self.assertEqual(rl["gross_weight"], 574.0)
		self.assertEqual(rl["rate_class_code"], "Q")
		self.assertEqual(rl["chargeable_weight"], 798.0)
		self.assertEqual(rl["rate_charge"], 4.25)
		self.assertEqual(rl["total"], 3391.5)

	def test_nc_description_stored_in_rate_line(self):
		# ABNF RTD_SecondLine for group 1: NC belongs to the rate-line row, not goods.
		rl = self.data["rate_lines"][0]
		self.assertEqual(rl["goods_data_identifier"], "C")
		self.assertEqual(rl["description"], "CONSOL OF GARMENTS")

	def test_nc_not_in_goods_list(self):
		ids = {g["goods_data_identifier"] for g in self.data["goods"]}
		self.assertNotIn("C", ids)

	def test_goods_carry_sequential_rtd_line_counts(self):
		# /2/NH→2, /3/ND→3, /4/ND→4, /5/ND→5 — sequential RTD counts preserved.
		nos = sorted(g["rate_line_number"] for g in self.data["goods"])
		self.assertEqual(nos, [2, 3, 4, 5])

	def test_hs_code_line_2(self):
		h = next(g for g in self.data["goods"] if g.get("goods_data_identifier") == "H")
		self.assertEqual(h["hs_code"], "61102000")
		self.assertEqual(h["rate_line_number"], 2)

	def test_dimension_lines(self):
		dims = sorted(
			[g for g in self.data["goods"] if g.get("goods_data_identifier") == "D"],
			key=lambda g: g["rate_line_number"],
		)
		self.assertEqual(len(dims), 3)
		self.assertEqual(dims[0]["rate_line_number"], 3)
		self.assertEqual(dims[0]["measurement_unit"], "CMT")
		self.assertEqual(dims[0]["dim_length"], 60.0)
		self.assertEqual(dims[0]["dim_width"], 41.0)
		self.assertEqual(dims[0]["dim_height"], 45.0)
		self.assertEqual(dims[0]["dim_pieces"], 21)
		self.assertEqual(dims[1]["rate_line_number"], 4)
		self.assertEqual(dims[1]["dim_pieces"], 4)
		self.assertEqual(dims[2]["rate_line_number"], 5)
		self.assertEqual(dims[2]["dim_pieces"], 15)
