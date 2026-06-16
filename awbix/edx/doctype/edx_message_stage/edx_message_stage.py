import frappe
from frappe.model.document import Document


class EDXMessageStage(Document):
	@frappe.whitelist()
	def promote(self):
		from awbix.edx.engine.pipeline import promote_stage

		return promote_stage(self.name)
