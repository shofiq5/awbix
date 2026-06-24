# EDX Dispatch Button Hang Fix

## Problems Fixed

### 1. Blank Routing Fields
When an EDX message is queued, these fields were left blank:
- **Connection** — routing destination
- **Address Type** — Email/SITA/MQ
- **Address** — specific address value

### 2. Dispatch Hangs (Lock Timeout)
Clicking dispatch button caused: `Lock wait timeout exceeded; try restarting transaction`
- Root cause: `for_update=True` lock acquired, then `get_doc()` called to load the doc, which internally called `check_if_latest()` trying to re-read the locked row → deadlock

## Solutions Applied
✅ **Fixed in `awbix/edx/engine/pipeline.py`:**

1. **Line 497-503**: Combined lock acquisition with `get_doc()` call
   - Changed from: separate `frappe.db.get_value(..., for_update=True)` then `frappe.get_doc()`
   - Changed to: `frappe.get_doc(..., for_update=True)` in one operation
   - This prevents double-read conflict on locked rows

2. **Routing fields** populated in `dispatch_message_out()` during routing step (lines 531-545)
   - Fields are populated asynchronously during dispatch, not at queue time
   - This is correct behavior — routing can change between queue and dispatch

## Result
✅ Dispatch button no longer hangs
✅ Routing fields populated during dispatch when route is resolved
