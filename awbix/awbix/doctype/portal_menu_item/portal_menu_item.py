import frappe
from frappe.model.document import Document


class PortalMenuItem(Document):
	def validate(self):
		if self.type == "DocType" and self.route:
			if not frappe.db.exists("DocType", self.route):
				frappe.throw(f"DocType '{self.route}' does not exist")

		if self.parent_item and self.parent_item == self.name:
			frappe.throw("A menu item cannot be its own parent")
