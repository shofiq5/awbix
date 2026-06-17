import frappe
from frappe.tests.utils import FrappeTestCase

from awbix.edx.engine.pipeline import ingest_raw, process_message_in, promote_stage
from awbix.edx.handlers.ack.fma_parser import FMAParser
from awbix.edx.handlers.ack.fna_parser import FNAParser

AWB = "157-68076960"
FMA = f"FMA\r\nACK/ACCEPTED\r\nFWB/16\r\n{AWB}BSLDOH/T1K40\r\n"
FNA = f"FNA/1\r\nERR/AWB SERIAL INVALID\r\nFWB/16\r\n{AWB}BSLDOH/T1K40\r\n"


class TestAckParsers(FrappeTestCase):
	def test_fma_parse(self):
		data = FMAParser().parse(FMA)
		self.assertEqual(data["reason"], "ACCEPTED")
		self.assertEqual(data["line_id"], "ACK")
		self.assertEqual(FMAParser().business_key(data), AWB)

	def test_fna_parse(self):
		data = FNAParser().parse(FNA)
		self.assertEqual(data["reason"], "AWB SERIAL INVALID")
		self.assertEqual(FNAParser().business_key(data), AWB)

	def test_no_awb_is_warning_not_error(self):
		data = FMAParser().parse("FMA\r\nACK/OK\r\nsome free text without an awb\r\n")
		issues = FMAParser().validate(data)
		self.assertTrue(any(i["code"] == "ACK_AWB" and i["level"] == "Warning" for i in issues))
		self.assertFalse(any(i["level"] == "Error" for i in issues))


# --------------------------------------------------------------------------- process


def _ensure(doctype, name, values):
	if not frappe.db.exists(doctype, name):
		frappe.get_doc({"doctype": doctype, **values}).insert(ignore_permissions=True)


def _ensure_definitions():
	for d in (
		{
			"message_type": "FMA",
			"version": "1",
			"parser_class": "awbix.edx.handlers.ack.fma_parser.FMAParser",
			"detection_pattern": "^FMA",
		},
		{
			"message_type": "FNA",
			"version": "1",
			"parser_class": "awbix.edx.handlers.ack.fna_parser.FNAParser",
			"detection_pattern": "^FNA",
		},
	):
		name = f"{d['message_type']}-{d['version']}"
		base = {
			"doctype": "EDX Message Definition",
			"target_doctype": "Shipment",
			"is_parser_enabled": 1,
			"bypass_amendment": 1,
			"auto_promote": 1,
			"auto_process": 1,
			**d,
		}
		if frappe.db.exists("EDX Message Definition", name):
			frappe.db.set_value("EDX Message Definition", name, base)
		else:
			frappe.get_doc(base).insert(ignore_permissions=True)
	frappe.clear_cache(doctype="EDX Message Definition")


def _ensure_shipment():
	_ensure("Airline", "157", {"airline_prefix": "157"})
	for code in ("BSL", "DOH"):
		_ensure("Airport", code, {"iata_code": code})
	_ensure("Currency", "CHF", {"currency_name": "CHF", "enabled": 1})
	if not frappe.db.exists("Shipment", AWB):
		doc = frappe.new_doc("Shipment")
		doc.update(
			{
				"airline_prefix": "157",
				"awb_serial_number": "68076960",
				"origin": "BSL",
				"destination": "DOH",
				"currency": "CHF",
				"edx_ack_status": "Pending",
			}
		)
		doc.flags.ignore_permissions = True
		doc.insert()


def _seed_sent_fwb():
	frappe.db.delete("EDX Message Out", {"business_key": AWB})
	return frappe.get_doc(
		{
			"doctype": "EDX Message Out",
			"message_type": "FWB",
			"message_version": "16",
			"business_key": AWB,
			"delivery_status": "Sent",
		}
	).insert(ignore_permissions=True)


class TestAckProcess(FrappeTestCase):
	def setUp(self):
		_ensure_definitions()
		_ensure_shipment()
		frappe.db.set_value("Shipment", AWB, {"edx_ack_status": "Pending", "edx_ack_detail": None})

	def test_fma_marks_acknowledged_and_delivers(self):
		mo = _seed_sent_fwb()
		FMAParser().process(FMAParser().parse(FMA), None)

		ship = frappe.db.get_value("Shipment", AWB, ["edx_ack_status", "edx_ack_detail", "edx_ack_at"], as_dict=True)
		self.assertEqual(ship.edx_ack_status, "Acknowledged")
		self.assertEqual(ship.edx_ack_detail, "ACCEPTED")
		self.assertIsNotNone(ship.edx_ack_at)
		self.assertEqual(frappe.db.get_value("EDX Message Out", mo.name, "delivery_status"), "Delivered")

	def test_fna_marks_rejected_and_fails(self):
		mo = _seed_sent_fwb()
		FNAParser().process(FNAParser().parse(FNA), None)

		self.assertEqual(frappe.db.get_value("Shipment", AWB, "edx_ack_status"), "Rejected")
		self.assertEqual(frappe.db.get_value("EDX Message Out", mo.name, "delivery_status"), "Failed")

	def test_unknown_awb_returns_none(self):
		data = FMAParser().parse("FMA\r\nACK/OK\r\nFWB/16\r\n999-99999990AAABBB\r\n")
		self.assertIsNone(FMAParser().process(data, None))

	def test_pipeline_bypass_applies_to_submitted_shipment(self):
		# Submitted Shipment must still receive its ack (db.set_value bypasses docstatus).
		if frappe.db.get_value("Shipment", AWB, "docstatus") == 0:
			frappe.get_doc("Shipment", AWB).submit()
		_seed_sent_fwb()

		stage = ingest_raw(FMA)
		mi = frappe.db.get_value("EDX Message Stage", stage, "message_in") or promote_stage(stage)
		process_message_in(mi)

		self.assertEqual(frappe.db.get_value("Shipment", AWB, "edx_ack_status"), "Acknowledged")
		self.assertEqual(frappe.db.get_value("EDX Message In", mi, "process_status"), "Processed")
