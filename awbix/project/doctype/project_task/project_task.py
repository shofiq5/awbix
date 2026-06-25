import frappe
from frappe.model.document import Document


class ProjectTask(Document):
	def validate(self):
		self.clamp_ai_confidence()

	def clamp_ai_confidence(self):
		if self.ai_confidence is None:
			return
		if self.ai_confidence < 0 or self.ai_confidence > 1:
			frappe.throw("AI Confidence must be between 0 and 1.")

	def primary_reference(self):
		"""Return the first code reference row, or None.

		Used by completion-detection to locate the source TODO this task tracks.
		"""
		return self.code_references[0] if self.code_references else None
