"""Tests for FHLComposer — round-trip and outbound pipeline."""

import frappe
from frappe.tests.utils import FrappeTestCase

from awbix.edx.engine import registry
from awbix.edx.engine.pipeline import dispatch_message_out, queue_outbound
from awbix.edx.handlers.fhl.fhl_composer import FHLComposer
from awbix.edx.handlers.fhl.fhl_parser import FHLParser

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MASTER_AWB = "157-68076960"
MASTER_PREFIX = "157"
MASTER_SERIAL = "68076960"


def _ensure(doctype, name, values):
	if not frappe.db.exists(doctype, name):
		frappe.get_doc({"doctype": doctype, **values}).insert(ignore_permissions=True)


def _ensure_definition():
	if not frappe.db.exists("EDX Message Definition", "FHL-5"):
		frappe.get_doc({
			"doctype": "EDX Message Definition",
			"message_type": "FHL",
			"version": "5",
			"title": "FHL/5 — Consolidation List / House Waybills (Cargo-IMP)",
			"standard": "Cargo-IMP",
			"parser_class": "awbix.edx.handlers.fhl.fhl_parser.FHLParser",
			"composer_class": "awbix.edx.handlers.fhl.fhl_composer.FHLComposer",
			"target_doctype": "House Airway Bill",
			"is_parser_enabled": 1,
			"is_composer_enabled": 1,
			"auto_promote": 1,
			"auto_process": 1,
			"detection_pattern": "^FHL/5",
			"amendment_mode": "Auto Apply",
		}).insert(ignore_permissions=True)
	else:
		frappe.db.set_value(
			"EDX Message Definition",
			"FHL-5",
			{
				"composer_class": "awbix.edx.handlers.fhl.fhl_composer.FHLComposer",
				"is_composer_enabled": 1,
			},
		)


def _seed():
	_ensure("Airline", MASTER_PREFIX, {"airline_prefix": MASTER_PREFIX})
	for code in ("BSL", "DOH"):
		_ensure("Airport", code, {"iata_code": code})
	if not frappe.db.exists("Currency", "CHF"):
		frappe.get_doc({"doctype": "Currency", "currency_name": "CHF", "enabled": 1}).insert(
			ignore_permissions=True
		)

	if not frappe.db.exists("Shipment", MASTER_AWB):
		doc = frappe.new_doc("Shipment")
		doc.airline_prefix = MASTER_PREFIX
		doc.awb_serial_number = MASTER_SERIAL
		doc.origin = "BSL"
		doc.destination = "DOH"
		doc.currency = "CHF"
		doc.flags.ignore_permissions = True
		doc.save()

	# Create one House Airway Bill linked to the master
	existing = frappe.db.get_value(
		"House Airway Bill",
		{"master_shipment": MASTER_AWB, "hwb_serial_number": "HWB001"},
		"name",
	)
	if not existing:
		hwb = frappe.new_doc("House Airway Bill")
		hwb.master_shipment = MASTER_AWB
		hwb.hwb_serial_number = "HWB001"
		hwb.hwb_origin = "BSL"
		hwb.hwb_destination = "DOH"
		hwb.number_of_pieces = 3
		hwb.weight_code = "K"
		hwb.weight = 45.5
		hwb.manifest_description = "ELECTRONIC PARTS"
		hwb.currency = "CHF"
		hwb.wt_val_prepaid_collect = "P"
		hwb.other_charges_prepaid_collect = "P"
		hwb.declared_value_carriage_type = "NVD"
		hwb.declared_value_customs_type = "NCV"
		hwb.insurance_type = "XXX"
		hwb.flags.ignore_permissions = True
		hwb.save()
		frappe.db.set_value("House Airway Bill", hwb.name, {
			"shipper_name": "ACME CORP",
			"consignee_name": "GLOBAL TRADING LLC",
		})
	return MASTER_AWB


# ---------------------------------------------------------------------------
# Pure compose / verify tests (no DB queries in compose itself — uses _seed data)
# ---------------------------------------------------------------------------


class TestFHLComposer(FrappeTestCase):
	def setUp(self):
		self.composer = FHLComposer()
		self.master_name = _seed()
		master_doc = frappe.get_doc("Shipment", self.master_name)
		self.raw = self.composer.compose(master_doc)

	def test_fhl_header_present(self):
		self.assertIn("FHL/5", self.raw)

	def test_mbi_line_present(self):
		self.assertIn(f"MBI/{MASTER_PREFIX}-{MASTER_SERIAL}BSLDOH", self.raw)

	def test_hbs_line_present(self):
		self.assertIn("HBS/HWB001/BSLDOH/3/K45.5//ELECTRONIC PARTS", self.raw)

	def test_cvd_line_present(self):
		self.assertIn("CVD/CHF/PP/NVD/NCV/XXX", self.raw)

	def test_round_trip(self):
		parser = FHLParser()
		data = parser.parse(self.raw)
		self.assertEqual(data["master"]["awb_number"], MASTER_AWB)
		self.assertEqual(len(data["houses"]), 1)
		h = data["houses"][0]
		self.assertEqual(h["hwb_serial_number"], "HWB001")
		self.assertEqual(h["hwb_origin"], "BSL")
		self.assertEqual(h["hwb_destination"], "DOH")
		self.assertEqual(h["number_of_pieces"], 3)
		self.assertAlmostEqual(h["weight"], 45.5)
		self.assertEqual(h["manifest_description"], "ELECTRONIC PARTS")
		self.assertEqual(h["charge_declarations"]["currency"], "CHF")

	def test_verify_clean(self):
		errors = [i for i in self.composer.verify(self.raw) if i["level"] == "Error"]
		self.assertEqual(errors, [])

	def test_verify_flags_bad_check_digit(self):
		bad_raw = self.raw.replace(
			f"MBI/{MASTER_PREFIX}-{MASTER_SERIAL}", f"MBI/{MASTER_PREFIX}-{MASTER_SERIAL[:-1]}9"
		)
		issues = self.composer.verify(bad_raw)
		codes = {i["code"] for i in issues if i["level"] == "Error"}
		self.assertIn("AWB_CHECKDIGIT", codes)


# ---------------------------------------------------------------------------
# Outbound pipeline tests
# ---------------------------------------------------------------------------


class _FakeTransport:
	last = {}

	def __init__(self, connection):
		pass

	def send(self, raw, meta):
		_FakeTransport.last = {"raw": raw, "meta": meta}
		return {"ok": True, "external_id": "FHL-EXT-1", "response": "accepted"}


class TestFHLOutboundPipeline(FrappeTestCase):
	def setUp(self):
		_ensure_definition()
		self.master = _seed()
		frappe.db.delete("EDX Message Routing")
		_ensure(
			"EDX Connection",
			"FHL Out Conn",
			{
				"connection_name": "FHL Out Conn",
				"channel": "Manual",
				"direction": "Outbound",
				"enabled": 1,
			},
		)
		self._orig_transport = registry.get_transport

	def tearDown(self):
		registry.get_transport = self._orig_transport

	def _add_route(self, **kwargs):
		row = {
			"doctype": "EDX Message Routing",
			"enabled": 1,
			"address_type": "Email",
			"address": "cargo@example.com",
			"connection": "FHL Out Conn",
		}
		row.update(kwargs)
		frappe.get_doc(row).insert(ignore_permissions=True)

	def test_dispatch_sends_fhl_payload(self):
		self._add_route(carrier_code=MASTER_PREFIX, origin="BSL", destination="DOH")
		registry.get_transport = lambda c: _FakeTransport(c)

		out = queue_outbound("Shipment", self.master, "FHL", "5")
		dispatch_message_out(out)

		mo = frappe.get_doc("EDX Message Out", out)
		self.assertEqual(mo.delivery_status, "Sent")
		self.assertEqual(mo.verify_status, "Verified")
		self.assertIn("FHL/5", _FakeTransport.last["raw"])
		self.assertIn("HBS/HWB001", _FakeTransport.last["raw"])

	def test_no_route_fails_cleanly(self):
		registry.get_transport = lambda c: _FakeTransport(c)
		out = queue_outbound("Shipment", self.master, "FHL", "5")
		dispatch_message_out(out)

		mo = frappe.get_doc("EDX Message Out", out)
		self.assertEqual(mo.delivery_status, "Failed")
		self.assertTrue(any(i.code == "ROUTE" for i in mo.issues))
