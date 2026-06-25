import os
import tempfile

import frappe
from frappe.tests.utils import FrappeTestCase

from awbix.project import todo_scanner


class TestTodoScanner(FrappeTestCase):
	def _write(self, root, rel, content):
		path = os.path.join(root, rel)
		os.makedirs(os.path.dirname(path), exist_ok=True)
		with open(path, "w", encoding="utf-8") as fh:
			fh.write(content)

	def test_scan_finds_markers_and_skips_dirs(self):
		with tempfile.TemporaryDirectory() as root:
			self._write(root, "pkg/mod.py", "x = 1  # TODO: handle edge case\nok = 2\n")
			self._write(root, "pkg/other.py", "# FIXME broken\n")
			self._write(root, "node_modules/lib.js", "// TODO ignore me\n")
			self._write(root, "notes.txt", "TODO not a scanned extension\n")

			hits = todo_scanner.scan(root=root)
			signatures = {h.signature() for h in hits}

			self.assertIn("pkg/mod.py:1:TODO", signatures)
			self.assertIn("pkg/other.py:1:FIXME", signatures)
			# Skipped dir and unscanned extension must not appear.
			self.assertFalse(any("node_modules" in s for s in signatures))
			self.assertFalse(any("notes.txt" in s for s in signatures))

	def test_title_strips_comment_and_marker(self):
		hit = todo_scanner.TodoHit("a.py", 1, "TODO", "# TODO: refactor this")
		self.assertEqual(todo_scanner._title_for(hit), "[TODO] refactor this")

	def test_sync_tasks_is_idempotent(self):
		with tempfile.TemporaryDirectory() as root:
			self._write(root, "pkg/mod.py", "# TODO: one thing\n")

			# Sanity-check the scan, then drive sync_tasks against a patched app_root.
			hits = todo_scanner.scan(root=root)
			self.assertEqual(len(hits), 1)

			# Drive sync_tasks against a patched app_root.
			original = todo_scanner.app_root
			todo_scanner.app_root = lambda: root
			try:
				r1 = todo_scanner.sync_tasks()
				r2 = todo_scanner.sync_tasks()
			finally:
				todo_scanner.app_root = original

			self.assertEqual(len(r1.created_task_names), 1)
			self.assertEqual(len(r2.created_task_names), 0)
			self.assertGreaterEqual(r2.skipped_existing, 1)

			frappe.delete_doc("Project Task", r1.created_task_names[0], force=True)
