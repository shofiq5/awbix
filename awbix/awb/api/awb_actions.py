# Copyright (c) 2026, CargoXY and contributors
# AWB Bulk Status Update API — Workbench Edition
# Supports: preview/dry-run, per-item results, conflict detection,
#           background enqueue, audit logging, CSV export, and undo.

import csv
import io
import json

import frappe
from frappe import _
from frappe.utils import cint, now_datetime, today

# ------------------------------------------------------------------ #
#  Transition rules                                                    #
# ------------------------------------------------------------------ #
_ALLOWED_TRANSITIONS = {
    "Available":   ["Assigned", "Hold", "Void", "Blacklisted"],
    "Assigned":    ["Withdrawn", "Hold", "Void", "Blacklisted"],
    "Withdrawn":   ["Available", "Assigned", "Hold", "Void", "Blacklisted"],
    "Hold":        ["Available", "Assigned", "Void", "Blacklisted"],
    "Void":        [],          # Terminal – no further transitions
    "Blacklisted": [],          # Terminal – no further transitions
}

_VALID_STATUSES       = ["Assigned", "Withdrawn", "Void", "Hold", "Blacklisted", "Available"]
_REASON_REQUIRED_FOR  = ["Withdrawn", "Void", "Blacklisted"]
_BULK_ASYNC_THRESHOLD = 200     # override via System Settings: awb_bulk_async_threshold


# ====================================================================== #
#  Phase 1 — Preview / Dry-Run                                           #
# ====================================================================== #

@frappe.whitelist()
def preview_awb_operation(
    mode,
    new_status,
    awb_prefix=None,
    serial_start=None,
    serial_end=None,
    full_awb_number=None,
    names=None,
    customer=None,
    force=False,
    reason=None,
):
    """
    Dry-run preview — returns per-item allow/block reasons without saving.
    """
    _check_permission()
    names = _parse_names(names)
    _validate_params(mode, new_status, awb_prefix, serial_start, serial_end,
                     full_awb_number, names, customer, reason)

    target_names = _resolve_targets(
        mode, awb_prefix, serial_start, serial_end, full_awb_number, names
    )
    force = frappe.utils.sbool(force)
    items = []

    for name in target_names:
        doc        = frappe.get_doc("AWB Inventory", name)
        is_allowed = new_status in _ALLOWED_TRANSITIONS.get(doc.status, [])
        reason     = ""

        if not is_allowed:
            if force and _can_force_transition(frappe.session.user):
                is_allowed = True
                reason     = _("[FORCED] Override permitted by administrator.")
            else:
                reason = _("Cannot transition from '{0}' to '{1}'.").format(
                    doc.status, new_status
                )

        items.append({
            "name":            name,
            "full_awb_number": doc.full_awb_number,
            "current_status":  doc.status,
            "assigned_to":     doc.assigned_to,
            "allowed":         is_allowed,
            "reason":          reason,
        })

    will_update = sum(1 for i in items if i["allowed"])
    return {
        "items":      items,
        "counts":     {
            "will_update": will_update,
            "blocked":     len(items) - will_update,
            "total":       len(items),
        },
        "mode":       mode,
        "new_status": new_status,
    }


# ====================================================================== #
#  Phase 1+2 — Extended Bulk Update (backward-compatible)               #
# ====================================================================== #

@frappe.whitelist()
def bulk_update_awb_status(
    mode,
    new_status,
    awb_prefix=None,
    serial_start=None,
    serial_end=None,
    full_awb_number=None,
    names=None,
    customer=None,
    # ── New params (all optional; safe defaults preserve old behaviour) ──
    dry_run=False,
    enqueue=False,
    force=False,
    reason=None,
    operation_id=None,
):
    """
    Unified AWB status update endpoint.

    New parameters (all optional, backward-compatible):
        dry_run (bool):     Return per-item validation without saving.
        enqueue (bool):     Force background job regardless of batch size.
        force (bool):       Allow Cargo Admin to override transition rules.
        reason (str):       Notes stored in audit log; required for
                            Withdraw / Void / Blacklist actions (UI-enforced).
        operation_id (str): Links sync results to an AWB Bulk Operation doc.

    Returns (sync):  {"items": [...], "counts": {...}, "dry_run": bool}
    Returns (async): {"enqueued": True, "operation_id": str, "message": str}
    """
    _check_permission()
    names = _parse_names(names)
    
    # Normalize customer parameter - ensure it's never None/empty string for Assigned
    customer = (customer or "").strip() if isinstance(customer, str) else ""
    
    _validate_params(mode, new_status, awb_prefix, serial_start, serial_end,
                     full_awb_number, names, customer, reason)

    dry_run  = frappe.utils.sbool(dry_run)
    enqueue  = frappe.utils.sbool(enqueue)
    force    = frappe.utils.sbool(force)

    target_names = _resolve_targets(
        mode, awb_prefix, serial_start, serial_end, full_awb_number, names
    )
    if not target_names:
        frappe.throw(_("No AWB records found matching the specified criteria."))

    # Dry-run always runs inline — no DB writes
    if dry_run:
        return _execute_sync(
            target_names, new_status, customer, force, reason,
            dry_run=True, operation_id=None,
        )

    # Determine whether to enqueue
    try:
        threshold = cint(
            frappe.db.get_single_value("AWB Settings", "awb_bulk_async_threshold")
        ) or _BULK_ASYNC_THRESHOLD
    except Exception:
        # Field may not exist; fall back to default threshold
        threshold = _BULK_ASYNC_THRESHOLD
    
    should_async = enqueue or len(target_names) > threshold

    if should_async:
        # Guard: AWB Bulk Operation doctype must be installed (Phase 4)
        if not frappe.db.table_exists("AWB Bulk Operation"):
            frappe.msgprint(
                _("Background job doctype not yet installed — running synchronously."),
                indicator="orange",
            )
            return _execute_sync(
                target_names, new_status, customer, force, reason,
                dry_run=False, operation_id=None,
            )

        op_doc = frappe.get_doc({
            "doctype":          "AWB Bulk Operation",
            "status":           "Queued",
            "total":            len(target_names),
            "operation_params": json.dumps({
                "mode":       mode,
                "new_status": new_status,
                "names":      target_names,
                "customer":   customer,
                "force":      force,
                "reason":     reason,
            }),
        })
        op_doc.insert(ignore_permissions=True)
        frappe.db.commit()

        frappe.enqueue(
            "cargoxy.awb.api.awb_actions._execute_background_operation",
            queue="long",
            job_name=f"awb_bulk_{op_doc.name}",
            is_async=True,
            operation_id=op_doc.name,
            target_names=target_names,
            new_status=new_status,
            customer=customer,
            force=force,
            reason=reason,
            owner=frappe.session.user,
        )

        return {
            "enqueued":     True,
            "operation_id": op_doc.name,
            "message":      _(
                "Batch of {0} AWBs enqueued as operation {1}. "
                "You will be notified on completion."
            ).format(len(target_names), op_doc.name),
        }

    # Synchronous for small batches or when enqueue is not available
    return _execute_sync(
        target_names, new_status, customer, force, reason,
        dry_run=False, operation_id=operation_id,
    )


# ====================================================================== #
#  Phase 2 — Internal sync executor (per-item results + conflict check) #
# ====================================================================== #

def _execute_sync(target_names, new_status, customer, force, reason,
                  dry_run, operation_id):
    """
    Core update loop used by both sync execution and dry-run preview.
    Returns per-item {name, full_awb_number, previous_status,
                      attempted_status, success, message}.
    """
    results    = []
    today_date = today()

    for name in target_names:
        try:
            doc              = frappe.get_doc("AWB Inventory", name)
            prev_status      = doc.status
            prev_assigned_to = doc.assigned_to

            # ── Transition validation ──────────────────────────────── #
            is_allowed = new_status in _ALLOWED_TRANSITIONS.get(prev_status, [])

            if not is_allowed:
                if force and _can_force_transition(frappe.session.user):
                    is_allowed = True
                else:
                    results.append(_item_result(
                        doc, new_status, prev_status,
                        success=False,
                        message=_("Cannot transition from '{0}' to '{1}'.").format(
                            prev_status, new_status
                        ),
                    ))
                    continue

            if not is_allowed:       # force denied
                results.append(_item_result(
                    doc, new_status, prev_status,
                    success=False,
                    message=_("Force permission denied — Cargo Admin role required."),
                ))
                continue

            if dry_run:
                # Preview only — no writes
                results.append(_item_result(
                    doc, new_status, prev_status, success=True, message=""
                ))
                continue

            # ── Optimistic conflict detection ─────────────────────── #
            doc.reload()
            if doc.status != prev_status:
                results.append(_item_result(
                    doc, new_status, prev_status,
                    success=False,
                    message=_("Conflict: AWB status was changed since preview."),
                ))
                continue

            # ── Apply field changes ───────────────────────────────── #
            doc.status = new_status
            if new_status == "Assigned":
                if not customer:
                    frappe.throw(_("Internal error: customer required for Assigned status but not provided"))
                doc.assigned_to    = customer
                doc.assigned_date  = today_date
                doc.withdrawn_date = None
            elif new_status == "Withdrawn":
                doc.withdrawn_date = today_date
                doc.assigned_date  = None
                # Keep assigned_to for audit trail; clearing happens only when explicitly moving to unclaimed status
            else:   # Available / Hold / Void / Blacklisted
                doc.assigned_to    = None
                doc.assigned_date  = None
                doc.withdrawn_date = None

            doc.save(ignore_permissions=True)

            # ── Audit log ─────────────────────────────────────────── #
            _try_write_audit_log(
                awb_inventory    = doc.name,
                operation_type   = _status_to_op_type(new_status),
                prev_status      = prev_status,
                new_status       = new_status,
                prev_assigned_to = prev_assigned_to,
                new_assigned_to  = doc.assigned_to,
                reason           = reason,
                operation_id     = operation_id,
            )

            results.append(_item_result(
                doc, new_status, prev_status, success=True, message=""
            ))

        except Exception as exc:
            results.append({
                "name":             name,
                "full_awb_number":  "?",
                "previous_status":  "?",
                "attempted_status": new_status,
                "success":          False,
                "message":          str(exc),
            })

    if not dry_run:
        frappe.db.commit()

    succeeded = sum(1 for r in results if r["success"])
    return {
        "items":   results,
        "counts":  {"updated": succeeded, "failed": len(results) - succeeded,
                    "total": len(results)},
        "dry_run": dry_run,
    }


# ====================================================================== #
#  Phase 4 — Background worker                                           #
# ====================================================================== #

def _execute_background_operation(
    operation_id, target_names, new_status, customer, force, reason, owner
):
    """
    Background job entry point — called by frappe.enqueue, not directly.
    Updates AWB Bulk Operation doc with progress; attaches CSV on completion.
    """
    try:
        op            = frappe.get_doc("AWB Bulk Operation", operation_id)
        op.status     = "Running"
        op.started_at = now_datetime()
        op.save(ignore_permissions=True)
        frappe.db.commit()

        _publish_progress(operation_id, 0, len(target_names), _("Starting…"), owner)

        result = _execute_sync(
            target_names, new_status, customer, force, reason,
            dry_run=False, operation_id=operation_id,
        )

        csv_file_name = _create_result_csv(operation_id, result["items"])

        op.reload()
        op.status      = "Completed"
        op.processed   = result["counts"]["updated"]
        op.errors      = result["counts"]["failed"]
        op.result_file = csv_file_name
        op.finished_at = now_datetime()
        op.save(ignore_permissions=True)
        frappe.db.commit()

        _publish_progress(
            operation_id, len(target_names), len(target_names), _("Completed"), owner
        )
        frappe.publish_realtime(
            "awb_bulk_finished",
            {"operation_id": operation_id, "counts": result["counts"]},
            user=owner,
        )

    except Exception:
        frappe.log_error(
            frappe.get_traceback(), f"AWB Bulk Operation {operation_id} failed"
        )
        if frappe.db.exists("AWB Bulk Operation", operation_id):
            frappe.db.set_value("AWB Bulk Operation", operation_id, {
                "status":      "Failed",
                "finished_at": now_datetime(),
            })
        frappe.publish_realtime(
            "awb_bulk_finished",
            {"operation_id": operation_id, "error": "Operation failed — see error log."},
            user=owner,
        )


@frappe.whitelist()
def get_bulk_operation_status(operation_id):
    """Return progress snapshot of a bulk operation."""
    if not frappe.db.exists("AWB Bulk Operation", operation_id):
        frappe.throw(_("Operation {0} not found.").format(operation_id))

    op       = frappe.get_doc("AWB Bulk Operation", operation_id)
    progress = int(op.processed / op.total * 100) if op.total else 0

    return {
        "operation_id": op.name,
        "status":       op.status,
        "total":        op.total,
        "processed":    op.processed,
        "errors":       op.errors,
        "progress":     progress,
        "result_file":  op.result_file,
        "started_at":   str(op.started_at  or ""),
        "finished_at":  str(op.finished_at or ""),
    }


@frappe.whitelist()
def cancel_bulk_operation(operation_id):
    """Request graceful cancellation of a running bulk operation."""
    _check_permission()
    if not frappe.db.exists("AWB Bulk Operation", operation_id):
        frappe.throw(_("Operation {0} not found.").format(operation_id))
    frappe.db.set_value("AWB Bulk Operation", operation_id, "cancel_requested", 1)
    return {"success": True}


# ====================================================================== #
#  Phase 5 — Undo bulk operation                                         #
# ====================================================================== #

@frappe.whitelist()
def undo_bulk_operation(operation_id):
    """
    Revert all AWBs changed in a bulk operation back to their prior states.
    Restricted to Cargo Admin; time-window controlled by system setting
    awb_undo_time_window_hours (default 24).
    """
    if not _can_force_transition(frappe.session.user):
        frappe.throw(
            _("Only Cargo Admin users can undo bulk operations."),
            frappe.PermissionError,
        )

    if not frappe.db.table_exists("AWB Audit Log"):
        frappe.throw(_("Audit Log doctype not installed — cannot undo."))

    audit_entries = frappe.get_all(
        "AWB Audit Log",
        filters={"operation_id": operation_id},
        fields=["name", "awb_inventory", "prev_status", "prev_assigned_to"],
    )
    if not audit_entries:
        frappe.throw(_("No audit entries found for operation {0}.").format(operation_id))

    # Time-window check
    undo_hours = cint(
        frappe.db.get_single_value("System Settings", "awb_undo_time_window_hours") or 24
    )
    if frappe.db.exists("AWB Bulk Operation", operation_id):
        finished_at = frappe.db.get_value("AWB Bulk Operation", operation_id, "finished_at")
        if finished_at:
            elapsed_hrs = (now_datetime() - finished_at).total_seconds() / 3600
            if elapsed_hrs > undo_hours:
                frappe.throw(
                    _("Undo window expired ({0} h). Operation finished {1:.1f} h ago.").format(
                        undo_hours, elapsed_hrs
                    )
                )

    reverted = 0
    for entry in audit_entries:
        try:
            doc            = frappe.get_doc("AWB Inventory", entry["awb_inventory"])
            prev_s         = entry["prev_status"]
            prev_cust      = entry["prev_assigned_to"]

            doc.status     = prev_s
            doc.assigned_to    = prev_cust
            doc.assigned_date  = today() if prev_s == "Assigned"  else None
            doc.withdrawn_date = today() if prev_s == "Withdrawn" else None
            doc.save(ignore_permissions=True)

            _try_write_audit_log(
                awb_inventory    = entry["awb_inventory"],
                operation_type   = "Undo",
                prev_status      = doc.status,
                new_status       = prev_s,
                prev_assigned_to = doc.assigned_to,
                new_assigned_to  = prev_cust,
                reason           = f"Undo of operation {operation_id}",
                operation_id     = None,
            )
            reverted += 1

        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"AWB Undo failed for {entry['awb_inventory']}"
            )

    frappe.db.commit()
    return {
        "success":  True,
        "reverted": reverted,
        "message":  _("{0} AWB(s) reverted successfully.").format(reverted),
    }


# ====================================================================== #
#  Private helpers                                                        #
# ====================================================================== #

def _check_permission():
    if not frappe.has_permission("AWB Inventory", ptype="write"):
        frappe.throw(
            _("You do not have permission to update AWB Inventory."),
            frappe.PermissionError,
        )


def _parse_names(names):
    """
    frappe.call JSON-stringifies array arguments before sending them as form
    data, so `names` arrives as the string '["AWB-001", ...]' instead of a
    list.  Deserialise it here before any validation touches it.
    """
    if isinstance(names, str):
        try:
            names = json.loads(names)
        except (ValueError, TypeError):
            pass
    return names


def _extract_serial_number(serial_input):
    """
    Extract numeric serial number from input.
    Handles both formats:
      - "0000003" (numeric part only)
      - "215-0000003" (full AWB format with prefix)
    Returns: numeric string suitable for int() conversion (e.g., "0000003")
    """
    if not serial_input:
        return "0"
    
    serial_str = str(serial_input).strip()
    
    # If contains hyphen, extract part after it (full AWB format)
    if "-" in serial_str:
        parts = serial_str.split("-")
        return parts[-1]  # Return last part (the serial number)
    
    # Otherwise return as-is (already numeric)
    return serial_str


def _can_force_transition(user):
    """True if user holds Cargo Admin or Administrator role."""
    return bool(frappe.db.get_value(
        "Has Role",
        {"parent": user, "role": ["in", ["Cargo Admin", "Administrator"]]},
        "role",
    ))


def _validate_params(mode, new_status, awb_prefix, serial_start, serial_end,
                     full_awb_number, names, customer, reason=None):
    if new_status not in _VALID_STATUSES:
        frappe.throw(_("Invalid status: {0}").format(new_status))

    # Validate reason is provided for actions that require it
    if new_status in _REASON_REQUIRED_FOR:
        reason_normalized = (reason or "").strip() if isinstance(reason, str) else ""
        if not reason_normalized:
            frappe.throw(
                _("Reason/Notes is required for {0} action. Please provide a reason.").format(new_status),
                title=_("Missing Reason")
            )

    # Normalize customer parameter - strip whitespace and handle empty strings
    customer_normalized = (customer or "").strip() if isinstance(customer, str) else ""
    
    if new_status == "Assigned":
        if not customer_normalized:
            frappe.throw(
                _("Customer is required when assigning AWBs. Please select a customer from the dropdown."),
                title=_("Missing Customer Assignment")
            )

    if mode == "range":
        if not awb_prefix or not serial_start or not serial_end:
            frappe.throw(
                _("awb_prefix, serial_start and serial_end are required for range mode.")
            )
        # Extract numeric serial part if full format (e.g., "215-0000003" → "0000003")
        serial_start_num = _extract_serial_number(serial_start)
        serial_end_num = _extract_serial_number(serial_end)
        if int(serial_start_num) > int(serial_end_num):
            frappe.throw(_("serial_start cannot be greater than serial_end."))

    elif mode == "single":
        if not full_awb_number:
            frappe.throw(_("full_awb_number is required for single mode."))

    elif mode == "selected":
        if not names or not isinstance(names, (list, tuple)):
            frappe.throw(_("names (list) is required for selected mode."))
    else:
        frappe.throw(
            _("Invalid mode: {0}. Must be range, single, or selected.").format(mode)
        )


def _resolve_targets(mode, awb_prefix, serial_start, serial_end, full_awb_number, names):
    if mode == "range":
        # Extract numeric serial part if full format (e.g., "215-0000003" → "0000003")
        serial_start_num = _extract_serial_number(serial_start)
        serial_end_num = _extract_serial_number(serial_end)
        serials = [
            str(s).zfill(7) for s in range(int(serial_start_num), int(serial_end_num) + 1)
        ]
        return frappe.get_all(
            "AWB Inventory",
            filters={"awb_prefix": awb_prefix, "awb_serial": ["in", serials]},
            pluck="name",
        )

    elif mode == "single":
        result = frappe.db.get_value(
            "AWB Inventory", {"full_awb_number": full_awb_number}, "name"
        )
        return [result] if result else []

    elif mode == "selected":
        return frappe.get_all(
            "AWB Inventory",
            filters={"name": ["in", list(names)]},
            pluck="name",
        )

    return []


def _item_result(doc, new_status, prev_status, success, message):
    return {
        "name":             doc.name,
        "full_awb_number":  doc.full_awb_number,
        "previous_status":  prev_status,
        "attempted_status": new_status,
        "success":          success,
        "message":          message,
    }


def _status_to_op_type(status):
    return {
        "Assigned":    "Assign",
        "Withdrawn":   "Withdraw",
        "Hold":        "Hold",
        "Void":        "Void",
        "Blacklisted": "Blacklist",
        "Available":   "MakeAvailable",
    }.get(status, status)


def _try_write_audit_log(awb_inventory, operation_type, prev_status, new_status,
                         prev_assigned_to, new_assigned_to, reason, operation_id):
    """Write audit log entry — silently skips if doctype not yet installed."""
    if not frappe.db.table_exists("AWB Audit Log"):
        return
    try:
        frappe.get_doc({
            "doctype":          "AWB Audit Log",
            "awb_inventory":    awb_inventory,
            "operation_id":     operation_id,
            "operation_type":   operation_type,
            "prev_status":      prev_status,
            "new_status":       new_status,
            "prev_assigned_to": prev_assigned_to,
            "new_assigned_to":  new_assigned_to,
            "reason":           reason or "",
            "performed_by":     frappe.session.user,
            "performed_at":     now_datetime(),
        }).insert(ignore_permissions=True)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "AWB Audit Log write failed")


def _publish_progress(operation_id, processed, total, message, user):
    frappe.publish_realtime(
        "awb_bulk_progress",
        {
            "operation_id": operation_id,
            "processed":    processed,
            "total":        total,
            "progress":     int(processed / total * 100) if total else 0,
            "message":      message,
        },
        user=user,
    )


# ====================================================================== #
#  Workbench Data APIs                                                   #
# ====================================================================== #

@frappe.whitelist()
def get_workbench_series():
    """Return all generated AWB series for the workbench series selector."""
    _check_permission()
    series = frappe.get_all(
        "AWB Series Generator",
        filters={"generation_status": "Generated"},
        fields=["name", "awb_prefix", "awb_cycle", "awb_type",
                "serial_start", "serial_end", "generated_count"],
        order_by="modified desc",
        limit=500,
    )
    return {"series": series}


def _build_workbench_filters(series, awb_prefix, status, customer, search,
                              date_from, date_to, awb_range_start, awb_range_end):
    filters = []

    if series:
        sg = frappe.db.get_value(
            "AWB Series Generator", series, ["awb_prefix", "awb_cycle"], as_dict=True
        )
        if sg:
            filters += [["awb_prefix", "=", sg.awb_prefix], ["awb_cycle", "=", sg.awb_cycle]]
    elif awb_prefix:
        filters.append(["awb_prefix", "=", awb_prefix])

    if status:
        sl = json.loads(status) if isinstance(status, str) else list(status)
        if sl:
            filters.append(["status", "in", sl])

    if customer:
        filters.append(["assigned_to", "=", customer])

    if search:
        filters.append(["full_awb_number", "like", f"%{search}%"])

    if date_from and date_to:
        filters.append(["creation", "between", [date_from, date_to]])
    elif date_from:
        filters.append(["creation", ">=", date_from])
    elif date_to:
        filters.append(["creation", "<=", date_to])

    if awb_range_start and awb_range_end:
        s = str(awb_range_start).strip().zfill(7)
        e = str(awb_range_end).strip().zfill(7)
        filters.append(["awb_serial", "between", [s, e]])

    return filters


@frappe.whitelist()
def get_workbench_data(
    series=None,
    awb_prefix=None,
    status=None,
    customer=None,
    search=None,
    date_from=None,
    date_to=None,
    awb_range_start=None,
    awb_range_end=None,
    page=1,
    page_size=50,
    sort_by="full_awb_number",
    sort_order="asc",
):
    """Paginated, filtered AWB list for the workbench grid."""
    _check_permission()

    filters = _build_workbench_filters(
        series, awb_prefix, status, customer, search,
        date_from, date_to, awb_range_start, awb_range_end,
    )

    _ALLOWED_SORT = {
        "full_awb_number", "status", "assigned_to", "creation",
        "modified", "awb_prefix", "awb_serial", "awb_cycle",
    }
    if sort_by not in _ALLOWED_SORT:
        sort_by = "full_awb_number"
    sort_order = "asc" if sort_order not in ("asc", "desc") else sort_order

    page      = max(1, cint(page))
    page_size = min(max(1, cint(page_size) or 50), 500)
    start     = (page - 1) * page_size

    total = frappe.db.count("AWB Inventory", filters)
    items = frappe.get_all(
        "AWB Inventory",
        filters=filters,
        fields=[
            "name", "full_awb_number", "awb_prefix", "awb_serial",
            "awb_cycle", "awb_type", "status", "assigned_to",
            "assigned_date", "withdrawn_date", "creation", "modified",
            "generated_by", "remarks",
        ],
        order_by=f"{sort_by} {sort_order}",
        start=start,
        page_length=page_size,
    )

    return {
        "items":       items,
        "total":       total,
        "page":        page,
        "page_size":   page_size,
        "total_pages": max(1, -(-total // page_size)),
    }


@frappe.whitelist()
def get_status_dashboard(series=None, awb_prefix=None):
    """Return AWB counts grouped by status for the dashboard strip."""
    _check_permission()

    conditions, values = [], {}

    if series:
        sg = frappe.db.get_value(
            "AWB Series Generator", series, ["awb_prefix", "awb_cycle"], as_dict=True
        )
        if sg:
            conditions.append("awb_prefix = %(pfx)s AND awb_cycle = %(cyc)s")
            values["pfx"] = sg.awb_prefix
            values["cyc"] = sg.awb_cycle
    elif awb_prefix:
        conditions.append("awb_prefix = %(pfx)s")
        values["pfx"] = awb_prefix

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    rows  = frappe.db.sql(
        f"SELECT status, COUNT(*) AS cnt FROM `tabAWB Inventory` {where} GROUP BY status",
        values, as_dict=True,
    )
    counts = {r["status"]: r["cnt"] for r in rows}
    return {
        "Available":   counts.get("Available",   0),
        "Assigned":    counts.get("Assigned",    0),
        "Withdrawn":   counts.get("Withdrawn",   0),
        "Hold":        counts.get("Hold",        0),
        "Void":        counts.get("Void",        0),
        "Blacklisted": counts.get("Blacklisted", 0),
        "Total":       sum(counts.values()),
    }


@frappe.whitelist()
def get_awb_audit_history(awb_name):
    """Return audit log entries for a single AWB."""
    if not frappe.has_permission("AWB Inventory", ptype="read", doc=awb_name):
        frappe.throw(_("Permission denied."), frappe.PermissionError)
    if not frappe.db.table_exists("AWB Audit Log"):
        return []
    return frappe.get_all(
        "AWB Audit Log",
        filters={"awb_inventory": awb_name},
        fields=[
            "operation_type", "prev_status", "new_status",
            "prev_assigned_to", "new_assigned_to", "reason",
            "performed_by", "performed_at", "operation_id",
        ],
        order_by="performed_at desc",
        limit=100,
    )


def _create_result_csv(operation_id, items):
    """Build CSV result file and attach it as a private Frappe File doc."""
    buf    = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=[
        "AWB Name", "Full AWB Number", "Previous Status",
        "Attempted Status", "Success", "Message",
    ])
    writer.writeheader()
    for item in items:
        writer.writerow({
            "AWB Name":         item.get("name", ""),
            "Full AWB Number":  item.get("full_awb_number", ""),
            "Previous Status":  item.get("previous_status", ""),
            "Attempted Status": item.get("attempted_status", ""),
            "Success":          "Yes" if item.get("success") else "No",
            "Message":          item.get("message", ""),
        })
    file_doc = frappe.get_doc({
        "doctype":   "File",
        "file_name": f"AWB_Operation_{operation_id}_{today()}.csv",
        "content":   buf.getvalue(),
        "is_private": 1,
    })
    file_doc.insert(ignore_permissions=True)
    return file_doc.name
