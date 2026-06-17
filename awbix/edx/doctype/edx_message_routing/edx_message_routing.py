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
		# An MQ/SITA route addresses a queue/teletype endpoint and needs a connection to
		# carry it; Email may deliver via a dedicated SMTP connection too, so require one
		# for the non-Email transports where the address alone is not deliverable.
		if self.address_type in ("MQ", "SITA") and not self.connection:
			frappe.throw(_("{0} routes require a Connection.").format(self.address_type))
