import frappe
from frappe.model.document import Document


class EDXMessageDefinition(Document):
	def validate(self):
		# Sanity-check that configured handler paths import, so a typo is caught at
		# save time rather than at the first message.
		for field in ("parser_class", "composer_class"):
			path = self.get(field)
			if not path:
				continue
			try:
				frappe.get_attr(path)
			except Exception:
				frappe.throw(frappe._("{0} '{1}' could not be imported").format(field, path))
