"""EDX Message Routing — outbound delivery rules (strategy R9).

Maps (message type, carrier, origin, destination) to a destination address + the
``EDX Connection`` that delivers it. Resolution lives in ``awbix.edx.engine.routing``;
this controller only enforces row-level consistency.
"""

import frappe
from frappe import _
from frappe.model.document import Document


class EDXMessageRouting(Document):
	def validate(self):
		# Every address type requires a Connection so the dispatcher knows which
		# transport adapter (SMTP, SFTP, MQ) to use for delivery.
		if not self.connection:
			frappe.throw(_("{0} routes require a Connection.").format(self.address_type))
