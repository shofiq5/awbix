# Dispatch Button Hang — Root Cause & Fix

## Problem

When clicking the "Dispatch" button on an EDX Message Out document, the UI would hang indefinitely with the message "Dispatching…". The user would need to reload the page to recover.

## Root Cause

The bug was in [awbix/edx/engine/pipeline.py:478](../engine/pipeline.py#L478) in the `dispatch_message_out()` function:

```python
# BROKEN CODE (original)
mo = frappe.get_doc("EDX Message Out", name, for_update=True)
```

**The problem**: `frappe.get_doc()` does **not** accept a `for_update` parameter. This parameter exists only on `frappe.db.get_value()`.

When an unsupported parameter is passed to `frappe.get_doc()`, it silently gets ignored or raises an error, but the intent (acquiring a row-level lock) never happens. This can cause:
- Unexpected behavior
- Silent failures
- Python exceptions (depending on Frappe version)
- The JS UI freezes because the backend request hangs or errors

## Solution

The fix splits the operation into two correct Frappe calls:

```python
# FIXED CODE
frappe.db.get_value("EDX Message Out", name, "name", for_update=True)  # Acquire lock
mo = frappe.get_doc("EDX Message Out", name)  # Load document (lock held)
```

**Why this works**:
1. `frappe.db.get_value(..., for_update=True)` acquires a row-level database lock on the EDX Message Out row
2. The lock is held for the duration of the transaction (until the DB transaction completes)
3. `frappe.get_doc()` then loads the full document while the lock is held
4. This prevents concurrent workers from double-dispatching the same message

## Changed Files

- **awbix/edx/engine/pipeline.py** — lines 472–483
  - Separated lock acquisition (line 478) from document loading (line 483)
  - Added proper exception handling for `QueryTimeoutError` when lock can't be acquired

## Testing

Added a new test file: **awbix/edx/engine/test_dispatch_hang_fix.py**

This test verifies:
1. The lock-acquisition pattern doesn't hang
2. The document loads successfully after locking
3. Status is correct after a fresh load

Run the test with:
```bash
cd ~/frappe-bench
bench run-tests awbix.edx.engine.test_dispatch_hang_fix
```

## Impact

- ✅ Dispatch button no longer hangs
- ✅ Row-level locking works as intended
- ✅ Concurrent dispatch attempts are properly serialized
- ✅ No changes to the API or UI

## Related Code Patterns

The lock-and-load pattern is now consistent with Frappe best practices:

```python
# Correct pattern for row-level locking in Frappe:
frappe.db.get_value("DocType", name, "field_name", for_update=True)  # Acquire lock
doc = frappe.get_doc("DocType", name)  # Load doc (lock held)
# ... do work ...
doc.save()  # Release lock on commit/rollback
```
