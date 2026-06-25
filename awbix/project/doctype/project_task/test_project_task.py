import frappe
from frappe.tests.utils import FrappeTestCase


class TestProjectTask(FrappeTestCase):
	def test_create_and_autoname(self):
		task = frappe.new_doc("Project Task")
		task.title = "Write the parser"
		task.insert()
		self.assertTrue(task.name.startswith("TASK-"))
		self.assertEqual(task.status, "Open")

	def test_ai_confidence_must_be_in_range(self):
		task = frappe.new_doc("Project Task")
		task.title = "Bad confidence"
		task.ai_confidence = 1.5
		with self.assertRaises(frappe.ValidationError):
			task.insert()

	def test_primary_reference(self):
		task = frappe.new_doc("Project Task")
		task.title = "Has a reference"
		task.append("code_references", {"file_path": "a/b.py", "line_number": 10, "marker": "TODO"})
		task.insert()
		ref = task.primary_reference()
		self.assertEqual(ref.file_path, "a/b.py")
		self.assertEqual(ref.line_number, 10)
