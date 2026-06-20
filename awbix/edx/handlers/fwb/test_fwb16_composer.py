import frappe
from frappe.tests.utils import FrappeTestCase

from awbix.edx.engine import registry
from awbix.edx.engine.pipeline import dispatch_message_out, queue_outbound
from awbix.edx.handlers.fwb.fwb16_composer import FWB16Composer
from awbix.edx.handlers.fwb.fwb16_parser import FWB16Parser

# A complete Shipment-like source (the composer only reads via ``.get()``). It carries every
# element the ABNF marks as mandatory - prefix/serial/origin/destination, quantity, routing,
# shipper + consignee (name/address/place/country), currency, a rate line with a nature-of-goods
# (NG) line, a charge summary total (CT), issue date/place and a sender reference - so that the
# composer (which now refuses to emit a structurally-incomplete message) succeeds.
SHIPMENT = {
	"name": "157-68076960",
	"airline_prefix": "157",
	"awb_serial_number": "68076960",
	"origin": "BSL",
	"destination": "DOH",
	"currency": "CHF",
	"number_of_pieces": 1,
	"weight": 40.0,
	"weight_code": "K",
	"routing": [
		{"sequence": 1, "airport": "ZRH", "carrier_code": "QR"},
		{"sequence": 2, "airport": "DOH", "carrier_code": "QR"},
	],
	"shipper_name": "HOFFMANN - LA ROCHE LTD",
	"shipper_address": "GRENZACHERSTRASSE 124",
	"shipper_place": "BASEL",
	"shipper_country": "Switzerland",
	"consignee_name": "M S EBN SINA MEDICAL",
	"consignee_address": "MEDICAL STREET 1",
	"consignee_place": "DOHA",
	"consignee_country": "Qatar",
	"agent_name": "DSV AIR SEA AG",
	"agent_iata_code": "8147158",
	"agent_place": "BASEL",
	"rate_lines": [
		{"line_number": 1, "number_of_pieces": 1, "gross_weight_code": "K", "gross_weight": 40.0,
		 "rate_class_code": "Q", "chargeable_weight": 40.0, "rate_charge": 5.0, "total": 200.0},
	],
	"goods_details": [
		{"rate_line_number": 1, "goods_data_identifier": "G", "description": "PHARMACEUTICALS"},
	],
	"charge_summary": [
		{"settlement": "Prepaid", "charge_identifier": "WT", "amount": 200.0},
		{"settlement": "Prepaid", "charge_identifier": "CT", "amount": 200.0},
	],
	"issue_date": "2026-06-15",
	"issue_place": "BSL",
	"sender_office_address": "BSLFFQR",
}


class TestFWB16Composer(FrappeTestCase):
	def setUp(self):
		self.composer = FWB16Composer()
		self.raw = self.composer.compose(dict(SHIPMENT))

	def test_round_trip(self):
		data = FWB16Parser().parse(self.raw)
		awb = data["awb"]
		self.assertEqual(awb["airline_prefix"], "157")
		self.assertEqual(awb["awb_serial_number"], "68076960")
		self.assertEqual(awb["origin"], "BSL")
		self.assertEqual(awb["destination"], "DOH")
		self.assertEqual(
			data["routing"],
			[
				{"sequence": 1, "airport": "ZRH", "carrier": "QR"},
				{"sequence": 2, "airport": "DOH", "carrier": "QR"},
			],
		)
		self.assertEqual(data["shipper"]["name"], "HOFFMANN - LA ROCHE LTD")
		self.assertEqual(data["consignee"]["name"], "M S EBN SINA MEDICAL")
		self.assertEqual(data["agent"]["name"], "DSV AIR SEA AG")
		self.assertEqual(data["charge_declarations"]["currency"], "CHF")

	def test_verify_clean(self):
		self.assertFalse([i for i in self.composer.verify(self.raw) if i["level"] == "Error"])

	def test_verify_flags_bad_check_digit(self):
		bad = dict(SHIPMENT, awb_serial_number="68076961")
		issues = self.composer.verify(self.composer.compose(bad))
		self.assertTrue(any(i["code"] == "AWB_CHECKDIGIT" for i in issues))

	def test_compose_raises_on_missing_mandatory(self):
		"""A source lacking mandatory data (routing, parties, RTD, summary, ISU, REF) is refused."""
		incomplete = {
			"airline_prefix": "157",
			"awb_serial_number": "68076960",
			"origin": "BSL",
			"destination": "DOH",
			"number_of_pieces": 1,
			"weight": 40.0,
		}
		with self.assertRaises(frappe.ValidationError):
			FWB16Composer().compose(incomplete)


# A Shipment-like source exercising every composable segment, for a full round-trip.
SHIPMENT_FULL = {
	"name": "157-68076960",
	"airline_prefix": "157",
	"awb_serial_number": "68076960",
	"origin": "BSL",
	"destination": "DOH",
	"shipment_description_code": "T",
	"number_of_pieces": 2,
	"weight": 500.0,
	"weight_code": "K",
	"volume_code": "MC",
	"volume_amount": 1.5,
	"currency": "CHF",
	"charge_code": "CC",
	"wt_val_prepaid_collect": "P",
	"other_charges_prepaid_collect": "P",
	"declared_value_carriage_type": "NVD",
	"declared_value_customs_type": "NCV",
	"insurance_type": "XXX",
	"shipper_name": "HOFFMANN LA ROCHE LTD",
	"shipper_address": "GRENZACHERSTRASSE 124",
	"shipper_place": "BASEL",
	"shipper_state": "BS",
	"shipper_post_code": "4070",
	"shipper_country": "Switzerland",
	"consignee_name": "EBN SINA MEDICAL",
	"consignee_address": "MEDICAL STREET 1",
	"consignee_place": "DOHA",
	"consignee_country": "Qatar",
	"agent_name": "DSV AIR SEA AG",
	"agent_account": "12345",
	"agent_iata_code": "8147158",
	"agent_cass_address": "4003",
	"agent_participant_id": "AB",
	"agent_place": "BASEL",
	"flight_bookings": [
		{"carrier_code": "QR", "flight_number": "0205", "flight_day": 15},
		{"carrier_code": "QR", "flight_number": "0608", "flight_day": 16},
	],
	"routing": [
		{"sequence": 1, "airport": "ZRH", "carrier_code": "QR"},
		{"sequence": 2, "airport": "DOH", "carrier_code": "QR"},
	],
	"also_notify": [
		{"notify_name": "NOTIFY PARTY LTD", "street_address": "NOTIFY STREET",
		 "place": "DOHA", "country": "Qatar", "post_code": "12345", "telephone": "97412345"},
	],
	"special_service_requests": [{"special_service_request": "HANDLE WITH CARE"}],
	"other_service_info": [{"other_service_information": "GENERAL INFO"}],
	"accounting_information": [{"identifier": "GEN", "information": "PAYMENT BY CASH"}],
	"rate_lines": [
		{"line_number": 1, "number_of_pieces": 2, "gross_weight_code": "K", "gross_weight": 500.0,
		 "rate_class_code": "Q", "chargeable_weight": 500.0, "rate_charge": 5.5, "total": 2750.0},
	],
	"goods_details": [
		{"rate_line_number": 1, "goods_data_identifier": "G", "description": "ELECTRONIC EQUIPMENT"},
		{"rate_line_number": 1, "goods_data_identifier": "D", "dim_weight_code": "K", "dim_weight": 500.0,
		 "measurement_unit": "CMT", "dim_length": 120.0, "dim_width": 80.0, "dim_height": 100.0, "dim_pieces": 2},
		{"rate_line_number": 1, "goods_data_identifier": "V", "volume_code": "MC", "volume_amount": 1.5},
		{"rate_line_number": 1, "goods_data_identifier": "H", "hs_code": "847130", "service_code": "E"},
	],
	"other_charges": [
		{"prepaid_collect": "P", "other_charge_code": "MYA", "amount": 50.0},
	],
	"charge_summary": [
		{"settlement": "Prepaid", "charge_identifier": "WT", "amount": 2750.0},
		{"settlement": "Prepaid", "charge_identifier": "VC", "amount": 10.0},
		{"settlement": "Prepaid", "charge_identifier": "CT", "amount": 2760.0},
	],
	"shippers_certification_signature": "JOHN SHIPPER",
	"issue_date": "2026-06-15",
	"issue_place": "BSL",
	"carrier_execution_signature": "QR AGENT",
	"cc_dest_currency": "USD",
	"rate_of_exchange": 1.085,
	"cc_charges_dest": 2500.0,
	"charges_at_dest": 100.0,
	"total_collect_charges": 2600.0,
	"sender_office_address": "BSLFFQR",
	"sender_file_reference": "MYFILE123",
	"customs_origin_code": "US",
	"nominated_handling_name": "HANDLING CO",
	"nominated_handling_place": "DOHA",
	"commission_percentage": 5.0,
	"sales_incentive_amount": 100.0,
	"sales_incentive_indicator": "CI",
	"agent_reference": "AGENTREF99",
	"references": [{"reference_number": "REF12345", "supplementary_1": "SUPP1", "supplementary_2": "SUPP2"}],
	"other_participants": [
		{"participant_name": "OTHER PARTICIPANT", "office_file_reference": "FILEREF",
		 "participant_id": "AB", "participant_code": "PARTCODE", "airport": "BSL"},
	],
	"oci_customs": [
		{"country": "Bangladesh", "information_identifier": "ISS",
		 "customs_info_identifier": "RA", "supplementary": "EORI12345"},
	],
	"special_handling": [{"special_handling_code": "PER"}, {"special_handling_code": "EAW"}],
}


class TestFWB16ComposerFullCoverage(FrappeTestCase):
	"""Compose a fully-populated Shipment, parse it back, and assert each segment survives."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.raw = FWB16Composer().compose(dict(SHIPMENT_FULL))
		cls.data = FWB16Parser().parse(cls.raw)

	def test_awb_quantity_volume(self):
		awb = self.data["awb"]
		self.assertEqual(awb["number_of_pieces"], 2)
		self.assertEqual(awb["weight"], 500.0)
		self.assertEqual(awb["volume_code"], "MC")
		self.assertEqual(awb["volume_amount"], 1.5)

	def test_flights_and_routing(self):
		self.assertEqual(self.data["flights"][0], {"carrier": "QR", "flight_number": "0205", "day": 15})
		self.assertEqual(self.data["routing"][0], {"sequence": 1, "airport": "ZRH", "carrier": "QR"})

	def test_parties(self):
		self.assertEqual(self.data["shipper"]["place"], "BASEL")
		self.assertEqual(self.data["shipper"]["state"], "BS")
		self.assertEqual(self.data["consignee"]["address"], "MEDICAL STREET 1")
		self.assertEqual(self.data["agent"]["participant_id"], "AB")
		self.assertEqual(self.data["also_notify"][0]["name"], "NOTIFY PARTY LTD")
		self.assertEqual(self.data["also_notify"][0]["contacts"][0]["number"], "97412345")

	def test_charges_and_cvd(self):
		self.assertEqual(self.data["charge_declarations"]["charge_code"], "CC")
		self.assertEqual(self.data["other_charges"][0]["other_charge_code"], "MYA")
		summary = {(r["settlement"], r["charge_identifier"]): r["amount"] for r in self.data["charge_summary"]}
		self.assertEqual(summary[("Prepaid", "WT")], 2750.0)
		self.assertEqual(summary[("Prepaid", "CT")], 2760.0)

	def test_rate_and_goods(self):
		rl = self.data["rate_lines"][0]
		self.assertEqual(rl["rate_charge"], 5.5)
		self.assertEqual(rl["total"], 2750.0)
		goods = {g["goods_data_identifier"]: g for g in self.data["goods"]}
		self.assertEqual(goods["G"]["description"], "ELECTRONIC EQUIPMENT")
		self.assertEqual(goods["D"]["dim_length"], 120.0)
		self.assertEqual(goods["V"]["volume_amount"], 1.5)
		self.assertEqual(goods["H"]["hs_code"], "847130")
		self.assertEqual(goods["H"]["service_code"], "E")  # DE505 service code round-trips

	def test_execution_and_cdc(self):
		self.assertEqual(self.data["execution"]["issue_date"], "2026-06-15")
		self.assertEqual(self.data["execution"]["issue_place"], "BSL")
		self.assertEqual(self.data["cdc"]["dest_currency"], "USD")
		self.assertEqual(self.data["cdc"]["rate_of_exchange"], 1.085)

	def test_references_handling_commission(self):
		self.assertEqual(self.data["sender_reference"]["file_reference"], "MYFILE123")
		self.assertEqual(self.data["customs_origin"]["code"], "US")
		self.assertEqual(self.data["nominated_handling"]["name"], "HANDLING CO")
		self.assertEqual(self.data["commission"]["percentage"], 5.0)
		self.assertEqual(self.data["sales_incentive"]["amount"], 100.0)
		self.assertEqual(self.data["agent_reference"]["reference"], "AGENTREF99")
		self.assertEqual(self.data["special_handling"], ["PER", "EAW"])
		self.assertEqual(self.data["references"][0]["reference_number"], "REF12345")
		self.assertEqual(self.data["other_participants"][0]["participant_code"], "PARTCODE")
		self.assertEqual(self.data["oci"][0]["customs_info_identifier"], "RA")

	def test_verify_clean(self):
		self.assertFalse([i for i in FWB16Composer().verify(self.raw) if i["level"] == "Error"])


# --------------------------------------------------------------------------- outbound


def _ensure(doctype, name, values):
	if not frappe.db.exists(doctype, name):
		frappe.get_doc({"doctype": doctype, **values}).insert(ignore_permissions=True)


def _ensure_definition():
	if frappe.db.exists("EDX Message Definition", "FWB-16"):
		frappe.db.set_value(
			"EDX Message Definition",
			"FWB-16",
			{
				"composer_class": "awbix.edx.handlers.fwb.fwb16_composer.FWB16Composer",
				"is_composer_enabled": 1,
			},
		)


def _ensure_shipment():
	_ensure("Airline", "157", {"airline_prefix": "157"})
	for code in ("BSL", "DOH", "ZRH"):
		_ensure("Airport", code, {"iata_code": code})
	_ensure("Currency", "CHF", {"currency_name": "CHF", "enabled": 1})
	if not frappe.db.exists("Shipment", "157-68076960"):
		doc = frappe.new_doc("Shipment")
		doc.update(
			{
				"airline_prefix": "157",
				"awb_serial_number": "68076960",
				"origin": "BSL",
				"destination": "DOH",
				"currency": "CHF",
				"shipper_name": "HOFFMANN - LA ROCHE LTD",
			}
		)
		doc.append("routing", {"sequence": 1, "airport": "ZRH", "carrier_code": "QR"})
		doc.flags.ignore_permissions = True
		doc.insert()
	return "157-68076960"


class _FakeTransport:
	last = {}

	def __init__(self, connection):
		self.connection = connection

	def send(self, raw, meta):
		_FakeTransport.last = {"raw": raw, "meta": meta}
		return {"ok": True, "external_id": "EXT-1", "response": "accepted"}


class TestOutboundPipeline(FrappeTestCase):
	def setUp(self):
		_ensure_definition()
		self.shipment = _ensure_shipment()
		frappe.db.delete("EDX Message Routing")
		_ensure(
			"EDX Connection",
			"Out Test Conn",
			{"connection_name": "Out Test Conn", "channel": "Manual", "direction": "Outbound", "enabled": 1},
		)
		self._orig_transport = registry.get_transport

	def tearDown(self):
		registry.get_transport = self._orig_transport

	def _add_route(self, **kwargs):
		row = {
			"doctype": "EDX Message Routing",
			"enabled": 1,
			"address_type": "Email",
			"address": "ops@example.com",
			"connection": "Out Test Conn",
		}
		row.update(kwargs)
		frappe.get_doc(row).insert(ignore_permissions=True)

	def test_dispatch_sends_via_routed_transport(self):
		self._add_route(carrier_code="157", origin="BSL", destination="DOH")
		registry.get_transport = lambda c: _FakeTransport(c)

		out = queue_outbound("Shipment", self.shipment, "FWB", "16")
		dispatch_message_out(out)

		mo = frappe.get_doc("EDX Message Out", out)
		self.assertEqual(mo.delivery_status, "Sent")
		self.assertEqual(mo.verify_status, "Verified")
		self.assertEqual(mo.external_id, "EXT-1")
		self.assertEqual(mo.connection, "Out Test Conn")
		self.assertIn("FWB/16", _FakeTransport.last["raw"])

	def test_no_route_fails_cleanly(self):
		registry.get_transport = lambda c: _FakeTransport(c)
		out = queue_outbound("Shipment", self.shipment, "FWB", "16")
		dispatch_message_out(out)

		mo = frappe.get_doc("EDX Message Out", out)
		self.assertEqual(mo.delivery_status, "Failed")
		self.assertTrue(any(i.code == "ROUTE" for i in mo.issues))

	def test_manual_send_is_graceful(self):
		# Routing to a Manual (non-deliverable) connection records an issue, never crashes.
		self._add_route()
		out = queue_outbound("Shipment", self.shipment, "FWB", "16")
		dispatch_message_out(out)

		mo = frappe.get_doc("EDX Message Out", out)
		self.assertIn(mo.delivery_status, ("Queued", "Failed"))
		self.assertTrue(any(i.code == "SEND" for i in mo.issues))
