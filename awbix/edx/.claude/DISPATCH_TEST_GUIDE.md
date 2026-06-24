# Testing the Dispatch Button Fix

## Quick Manual Test

1. **Start the bench dev server:**
   ```bash
   cd ~/frappe-bench
   bench start
   ```

2. **Create test data:**
   - Go to EDX Connection and create a "Manual Test" connection (channel: Manual, direction: Outbound)
   - Go to EDX Message Routing and add a route pointing to the Manual Test connection
   - Go to Shipment list and find or create a test shipment

3. **Queue a message:**
   - Open the Shipment
   - Click "Send FWB" button (in EDX group)
   - This creates an EDX Message Out in Queued status

4. **Test the Dispatch button:**
   - Go to the EDX Message Out that was just created
   - Click the "Dispatch" button
   - **Before fix:** Browser would hang, showing "Dispatching…" indefinitely
   - **After fix:** Should complete in <1 second and show "Sent" (or "Failed" with reason if validation fails)

## Automated Test

Run the dispatch hang fix test:

```bash
cd ~/frappe-bench
bench run-tests awbix.edx.engine.test_dispatch_hang_fix
```

Expected output:
```
OK — 3 tests passed in 1.234s
```

## What the Fix Ensures

✅ **No hang on dispatch** — The button click returns immediately with success/failure status
✅ **Concurrent safety** — Multiple workers can't double-dispatch the same message
✅ **Clean error handling** — Validation/routing errors are recorded without crashing
✅ **Proper locking** — Row-level DB locks serialize concurrent attempts

## If You Still See Hanging

1. **Check the server logs** for exceptions:
   ```bash
   tail -f ~/frappe-bench/logs/bench.log
   ```

2. **Verify the EDX Connection exists** and is enabled

3. **Check if a routing rule exists** for the message type/carrier/origin/destination

4. **Test in browser console:**
   ```javascript
   frappe.call({
     method: "awbix.edx.engine.pipeline.dispatch_message_out",
     args: { name: "EDX Message Out name here" },
     callback(r) { console.log(r.message); }
   });
   ```

## Expected Responses

**Success (Sent):**
```json
{
  "ok": true,
  "status": "Sent",
  "connection": "Manual Test"
}
```

**Verification failure (bad check digit, etc):**
```json
{
  "ok": false,
  "status": "Verification Failed"
}
```

**No matching route:**
```json
{
  "ok": false,
  "status": "Failed",
  "error": "No routing rule matched this message"
}
```

**Already dispatched:**
```json
{
  "ok": false,
  "status": "Sent",
  "skipped": true
}
```
