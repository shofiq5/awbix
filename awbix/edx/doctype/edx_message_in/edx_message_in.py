import frappe
from frappe.model.document import Document


class EDXMessageIn(Document):
	@frappe.whitelist()
	def verify(self):
		"""Parse + validate only — populates parsed_json / issues, no business writes."""
		from awbix.edx.engine.pipeline import verify_message_in

		return verify_message_in(self.name)

	@frappe.whitelist()
	def process(self):
		"""Persist into the target DocType (amendment-aware)."""
		from awbix.edx.engine.pipeline import process_message_in

		return process_message_in(self.name)
