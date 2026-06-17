import frappe
from frappe.tests.utils import FrappeTestCase

from awbix.edx.engine.routing import resolve_route
from awbix.edx.transports.manual_transport import ManualTransport


def _make_connection(name, channel="Manual", direction="Both"):
	if frappe.db.exists("EDX Connection", name):
		frappe.delete_doc("EDX Connection", name, force=True)
	doc = frappe.get_doc(
		{
			"doctype": "EDX Connection",
			"connection_name": name,
			"channel": channel,
			"direction": direction,
			"enabled": 1,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc


class TestManualTransport(FrappeTestCase):
	def test_manual_poll_and_test(self):
		conn = _make_connection("Test Manual Conn")
		transport = ManualTransport(conn)
		self.assertEqual(transport.poll(), [])
		self.assertTrue(transport.test("Inbound")["ok"])
		self.assertFalse(transport.send("x", {})["ok"])


class TestConnectionTestButtons(FrappeTestCase):
	def test_manual_connection_test_stamps_status(self):
		conn = _make_connection("Test Manual Status")
		res = conn.test_incoming()
		self.assertTrue(res["ok"])
		conn.reload()
		self.assertEqual(conn.last_test_status, "OK")
		self.assertIsNotNone(conn.last_test_at)

	def test_direction_guard(self):
		conn = _make_connection("Test Inbound Only", direction="Inbound")
		with self.assertRaises(frappe.ValidationError):
			conn.test_outgoing()


class TestRouting(FrappeTestCase):
	def setUp(self):
		frappe.db.delete("EDX Message Routing")
		self.conn = _make_connection("Test Route Conn")

	def _route(self, **kwargs):
		row = {
			"doctype": "EDX Message Routing",
			"enabled": 1,
			"address_type": "Email",
			"address": "ops@example.com",
			"connection": self.conn.name,
		}
		row.update(kwargs)
		return frappe.get_doc(row).insert(ignore_permissions=True)

	def test_most_specific_wins(self):
		self._route(carrier_code="157", address="generic@example.com")
		self._route(carrier_code="157", origin="DAC", destination="DXB", address="specific@example.com")
		hit = resolve_route("FWB", "157", "DAC", "DXB")
		self.assertEqual(hit["address"], "specific@example.com")

	def test_wildcard_fallback(self):
		self._route(address="default@example.com")  # all-wildcard catch-all
		hit = resolve_route("FWB", "999", "AAA", "BBB")
		self.assertEqual(hit["address"], "default@example.com")

	def test_priority_tiebreak(self):
		self._route(carrier_code="157", priority=1, address="low@example.com")
		self._route(carrier_code="157", priority=5, address="high@example.com")
		hit = resolve_route("FWB", "157", "DAC", "DXB")
		self.assertEqual(hit["address"], "high@example.com")

	def test_no_match_returns_none(self):
		self._route(carrier_code="157", address="x@example.com")
		self.assertIsNone(resolve_route("FWB", "176", "DAC", "DXB"))

	def test_disabled_ignored(self):
		self._route(carrier_code="157", enabled=0, address="off@example.com")
		self.assertIsNone(resolve_route("FWB", "157", "DAC", "DXB"))
