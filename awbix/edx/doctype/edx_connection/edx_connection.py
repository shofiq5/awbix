"""EDX Connection — one transport endpoint (self-managed; strategy D2/§7).

The controller stays thin: it owns config + the Test Connection actions, and delegates
all I/O to the channel's transport adapter (resolved via the registry). Polling and
sending are driven by the pipeline / scheduler, not from here.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class EDXConnection(Document):
	def _run_test(self, direction):
		"""Resolve the transport, run its self-test, and stamp the result. Never raises."""
		from awbix.edx.engine.registry import get_transport

		try:
			result = get_transport(self).test(direction) or {}
			ok = bool(result.get("ok"))
			message = result.get("message", "")
		except Exception as e:
			ok, message = False, str(e)
			frappe.log_error(frappe.get_traceback(), f"EDX Connection test failed: {self.name}")

		self.db_set(
			{
				"last_test_status": "OK" if ok else "Failed",
				"last_test_at": now_datetime(),
				"last_test_message": (message or "")[:500],
			}
		)
		return {"ok": ok, "message": message}

	@frappe.whitelist()
	def test_incoming(self):
		if self.direction == "Outbound":
			frappe.throw(_("This connection is Outbound only."))
		return self._run_test("Inbound")

	@frappe.whitelist()
	def test_outgoing(self):
		if self.direction == "Inbound":
			frappe.throw(_("This connection is Inbound only."))
		return self._run_test("Outbound")
