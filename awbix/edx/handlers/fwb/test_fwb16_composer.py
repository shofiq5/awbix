import frappe
from frappe.tests.utils import FrappeTestCase

from awbix.edx.engine import registry
from awbix.edx.engine.pipeline import dispatch_message_out, queue_outbound
from awbix.edx.handlers.fwb.fwb16_composer import FWB16Composer
from awbix.edx.handlers.fwb.fwb16_parser import FWB16Parser

# A minimal Shipment-like source: the composer only reads via ``.get()``.
SHIPMENT = {
	"name": "157-68076960",
	"airline_prefix": "157",
	"awb_serial_number": "68076960",
	"origin": "BSL",
	"destination": "DOH",
	"currency": "CHF",
	"shipper_name": "HOFFMANN - LA ROCHE LTD",
	"consignee_name": "M S EBN SINA MEDICAL",
	"agent_name": "DSV AIR SEA AG",
	"number_of_pieces": 1,
	"weight": 40.0,
	"weight_code": "K",
	"routing": [
		{"sequence": 1, "airport": "ZRH", "carrier_code": "QR"},
		{"sequence": 2, "airport": "DOH", "carrier_code": "QR"},
	],
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
