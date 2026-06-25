import os
import tempfile

import frappe
from frappe.tests.utils import FrappeTestCase

from awbix.project import completion, todo_scanner


class TestCompletion(FrappeTestCase):
	def setUp(self):
		# Ensure AI is disabled so completion uses the deterministic path only.
		settings = frappe.get_single("Project AI Settings")
		settings.enabled = 0
		settings.save()

	def _task_with_ref(self, root, rel, line, marker):
		task = frappe.new_doc("Project Task")
		task.title = f"track {marker}"
		task.status = "Open"
		task.source = "TODO Scan"
		task.append("code_references", {"file_path": rel, "line_number": line, "marker": marker})
		task.insert()
		return task

	def test_marker_present_means_not_done(self):
		with tempfile.TemporaryDirectory() as root:
			os.makedirs(os.path.join(root, "pkg"))
			with open(os.path.join(root, "pkg", "m.py"), "w", encoding="utf-8") as fh:
				fh.write("# TODO: still here\n")

			original = todo_scanner.app_root
			todo_scanner.app_root = lambda: root
			try:
				task = self._task_with_ref(root, "pkg/m.py", 1, "TODO")
				verdict = completion.deterministic_verdict(task)
			finally:
				todo_scanner.app_root = original

			self.assertFalse(verdict.done)
			frappe.delete_doc("Project Task", task.name, force=True)

	def test_marker_gone_moves_to_review(self):
		with tempfile.TemporaryDirectory() as root:
			os.makedirs(os.path.join(root, "pkg"))
			with open(os.path.join(root, "pkg", "m.py"), "w", encoding="utf-8") as fh:
				fh.write("# resolved, nothing here\n")

			original = todo_scanner.app_root
			todo_scanner.app_root = lambda: root
			try:
				task = self._task_with_ref(root, "pkg/m.py", 1, "TODO")
				summary = completion.detect_completed_tasks()
			finally:
				todo_scanner.app_root = original

			refreshed = frappe.get_doc("Project Task", task.name)
			self.assertEqual(refreshed.status, "Needs Review")
			self.assertIn(task.name, summary["moved_to_review"])
			frappe.delete_doc("Project Task", task.name, force=True)
