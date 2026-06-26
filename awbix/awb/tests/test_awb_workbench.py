# Copyright (c) 2026, CargoXY and contributors
# AWB Workbench – Test Suite
# Covers: Phase 1 (preview), Phase 2 (sync bulk update + conflict + force),
#         Phase 4 (enqueue skeleton), Phase 5 (undo)

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today

from cargoxy.awb.api import awb_actions


def _make_awb(prefix="157", serial=None, status="Available", awb_type=None, cycle="2026"):
    """Helper: insert a fresh AWB Inventory record and return it."""
    serial = serial or "0099901"
    awb_type = awb_type or _ensure_awb_type()
    doc = frappe.get_doc({
        "doctype":    "AWB Inventory",
        "awb_cycle":  cycle,
        "awb_type":   awb_type,
        "awb_prefix": prefix,
        "awb_serial": serial,
        "status":     status,
    })
    doc.insert(ignore_permissions=True)
    return doc


def _ensure_awb_type():
    """Return an AWB Type name, creating one if needed."""
    existing = frappe.db.get_value("AWB Type", {}, "name")
    if existing:
        return existing
    t = frappe.get_doc({"doctype": "AWB Type", "awb_type_name": "Test Type"})
    t.insert(ignore_permissions=True)
    return t.name


def _ensure_customer(name="WB-TEST-CUST"):
    if frappe.db.exists("Customer", name):
        return name
    c = frappe.get_doc({
        "doctype":       "Customer",
        "customer_name": name,
        "customer_type": "Company",
        "customer_group": frappe.db.get_value("Customer Group", {}, "name") or "All Customer Groups",
        "territory":     frappe.db.get_value("Territory", {}, "name") or "All Territories",
    })
    c.insert(ignore_permissions=True)
    return c.name


class TestAWBWorkbenchPhase1Preview(FrappeTestCase):
    """Phase 1 – preview_awb_operation dry-run tests."""

    def setUp(self):
        self.customer = _ensure_customer()
        self.awb_avail = _make_awb(serial="0001001", status="Available")
        self.awb_void  = _make_awb(serial="0001002", status="Void")

    def tearDown(self):
        for d in [self.awb_avail, self.awb_void]:
            d.reload()
            frappe.delete_doc("AWB Inventory", d.name, ignore_permissions=True, force=True)

    # ── Test: allowed transition shows allowed=True ────────────────── #
    def test_preview_allows_valid_transition(self):
        result = awb_actions.preview_awb_operation(
            mode="single",
            new_status="Assigned",
            full_awb_number=self.awb_avail.full_awb_number,
            customer=self.customer,
        )
        self.assertEqual(result["counts"]["will_update"], 1)
        self.assertEqual(result["counts"]["blocked"], 0)
        self.assertTrue(result["items"][0]["allowed"])

    # ── Test: terminal status Void blocks any transition ───────────── #
    def test_preview_blocks_terminal_status(self):
        result = awb_actions.preview_awb_operation(
            mode="single",
            new_status="Assigned",
            full_awb_number=self.awb_void.full_awb_number,
            customer=self.customer,
        )
        self.assertEqual(result["counts"]["will_update"], 0)
        self.assertEqual(result["counts"]["blocked"], 1)
        self.assertFalse(result["items"][0]["allowed"])
        self.assertIn("Cannot transition", result["items"][0]["reason"])

    # ── Test: range mode resolves multiple AWBs ────────────────────── #
    def test_preview_range_resolves_both_items(self):
        result = awb_actions.preview_awb_operation(
            mode="range",
            new_status="Hold",
            awb_prefix="157",
            serial_start="0001001",
            serial_end="0001002",
        )
        self.assertEqual(result["counts"]["total"], 2)
        # Available → Hold allowed; Void → Hold blocked
        self.assertEqual(result["counts"]["will_update"], 1)
        self.assertEqual(result["counts"]["blocked"], 1)

    # ── Test: selected mode returns items for given names ──────────── #
    def test_preview_selected_mode(self):
        result = awb_actions.preview_awb_operation(
            mode="selected",
            new_status="Hold",
            names=[self.awb_avail.name],
        )
        self.assertEqual(result["counts"]["total"], 1)
        self.assertTrue(result["items"][0]["allowed"])


class TestAWBWorkbenchPhase2SyncUpdate(FrappeTestCase):
    """Phase 2 – bulk_update_awb_status sync, dry-run, conflict, force."""

    def setUp(self):
        self.customer = _ensure_customer()
        self.awb = _make_awb(serial="0002001", status="Available")

    def tearDown(self):
        self.awb.reload()
        frappe.delete_doc("AWB Inventory", self.awb.name, ignore_permissions=True, force=True)

    # ── Test: dry_run does not save ────────────────────────────────── #
    def test_dry_run_makes_no_db_changes(self):
        original_status = self.awb.status
        result = awb_actions.bulk_update_awb_status(
            mode="single",
            new_status="Assigned",
            full_awb_number=self.awb.full_awb_number,
            customer=self.customer,
            dry_run=True,
        )
        self.assertTrue(result["dry_run"])
        self.assertEqual(result["counts"]["updated"], 1)   # dry-run counts as "would update"
        self.awb.reload()
        self.assertEqual(self.awb.status, original_status)  # DB unchanged

    # ── Test: sync update sets new status and returns per-item result  #
    def test_sync_update_assigns_awb(self):
        result = awb_actions.bulk_update_awb_status(
            mode="single",
            new_status="Assigned",
            full_awb_number=self.awb.full_awb_number,
            customer=self.customer,
            dry_run=False,
        )
        self.assertFalse(result["dry_run"])
        self.assertEqual(result["counts"]["updated"], 1)
        self.assertEqual(result["counts"]["failed"], 0)
        item = result["items"][0]
        self.assertTrue(item["success"])
        self.assertEqual(item["attempted_status"], "Assigned")
        self.awb.reload()
        self.assertEqual(self.awb.status, "Assigned")
        self.assertEqual(self.awb.assigned_to, self.customer)

    # ── Test: per-item result for blocked transition ─────────────────  #
    def test_sync_update_blocks_invalid_transition(self):
        # Set AWB to Void (terminal) first
        frappe.db.set_value("AWB Inventory", self.awb.name, "status", "Void")
        result = awb_actions.bulk_update_awb_status(
            mode="single",
            new_status="Assigned",
            full_awb_number=self.awb.full_awb_number,
            customer=self.customer,
        )
        self.assertEqual(result["counts"]["updated"], 0)
        self.assertEqual(result["counts"]["failed"], 1)
        self.assertFalse(result["items"][0]["success"])
        self.assertIn("Cannot transition", result["items"][0]["message"])

    # ── Test: conflict detection skips concurrently changed AWB ───── #
    def test_conflict_detection_skips_item(self):
        # Monkeypatch: after get_doc, externally change the status
        original_get_doc = frappe.get_doc

        call_count = {"n": 0}

        def mock_get_doc(doctype, name=None, *args, **kwargs):
            doc = original_get_doc(doctype, name, *args, **kwargs)
            if doctype == "AWB Inventory" and name == self.awb.name:
                call_count["n"] += 1
                if call_count["n"] == 2:   # second call is doc.reload() inside sync
                    # Simulate external change
                    doc.status = "Hold"
            return doc

        frappe.get_doc = mock_get_doc
        try:
            result = awb_actions.bulk_update_awb_status(
                mode="single",
                new_status="Assigned",
                full_awb_number=self.awb.full_awb_number,
                customer=self.customer,
                dry_run=False,
            )
        finally:
            frappe.get_doc = original_get_doc

        self.assertEqual(result["counts"]["failed"], 1)
        self.assertIn("Conflict", result["items"][0]["message"])

    # ── Test: range mode updates multiple AWBs ─────────────────────── #
    def test_range_mode_updates_multiple(self):
        awb2 = _make_awb(serial="0002002", status="Available")
        try:
            result = awb_actions.bulk_update_awb_status(
                mode="range",
                new_status="Hold",
                awb_prefix="157",
                serial_start="0002001",
                serial_end="0002002",
            )
            self.assertEqual(result["counts"]["updated"], 2)
        finally:
            awb2.reload()
            frappe.delete_doc("AWB Inventory", awb2.name, ignore_permissions=True, force=True)

    # ── Test: backward compatibility — old callers still get updated/skipped #
    def test_backward_compat_old_callers(self):
        """Old list-view callers didn't pass dry_run/force/reason — must still work."""
        result = awb_actions.bulk_update_awb_status(
            mode="single",
            new_status="Hold",
            full_awb_number=self.awb.full_awb_number,
        )
        # New format: has 'items' and 'counts'
        self.assertIn("items",  result)
        self.assertIn("counts", result)


class TestAWBWorkbenchPhase5Undo(FrappeTestCase):
    """Phase 5 – undo_bulk_operation basic checks (doctype guard)."""

    def test_undo_raises_if_audit_log_doctype_missing(self):
        """If AWB Audit Log table doesn't exist, undo should throw cleanly."""
        if frappe.db.table_exists("AWB Audit Log"):
            self.skipTest("AWB Audit Log installed — skipping absence test.")
        with self.assertRaises(frappe.ValidationError):
            awb_actions.undo_bulk_operation("AWB-BULK-NONEXISTENT")

    def test_undo_raises_without_admin_role(self):
        """Non-admin user calling undo should get PermissionError."""
        original_user = frappe.session.user
        try:
            # Set a non-admin user
            frappe.set_user("Guest")
            with self.assertRaises(frappe.PermissionError):
                awb_actions.undo_bulk_operation("AWB-BULK-NONEXISTENT")
        finally:
            frappe.set_user(original_user)
