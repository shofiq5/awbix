from frappe.model.document import Document


class EDXDelivery(Document):
	def validate(self):
		self.status = "Locked" if self.locked else (self.status or "Active")
