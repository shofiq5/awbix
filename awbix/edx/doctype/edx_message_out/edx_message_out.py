"""EDX Message Out — the composed outbound copy + delivery ledger (strategy §4.3).

One row per outbound attempt. The controller exposes a single ``dispatch()`` action that
re-runs the full compose → verify → send cycle through the shared engine function, so the
Desk button and the scheduler use exactly the same path.
"""

import frappe
from frappe.model.document import Document


class EDXMessageOut(Document):
	@frappe.whitelist()
	def dispatch(self):
		from awbix.edx.engine.pipeline import dispatch_message_out

		return dispatch_message_out(self.name)
