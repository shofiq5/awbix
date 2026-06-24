# EDX Routing Bug Fix

## Problem
When an EDX message is queued (Message Out record created), the following fields were left blank:
- **Composed Raw** — raw message content (populated during compose)
- **Connection** — routing destination
- **Address Type** — Email/SITA/MQ
- **Address** — specific address value

Status was set to `Queued` but routing information was missing until async dispatch.

## Root Cause
`queue_outbound()` in `pipeline.py` was creating Message Out records without resolving routing. Routing only happened later in `dispatch_message_out()`, leaving fields blank at creation time.

## Solution
✅ **Fixed in `awbix/edx/engine/pipeline.py`:**

1. **`queue_outbound()` (line 441-473)**: Now calls `resolve_route()` upfront and populates `connection`, `address_type`, `address` at queue time
2. **`dispatch_message_out()` (line 531-545)**: Skips redundant routing if fields already populated

## Result
- Message Out records now have routing information populated immediately when queued
- `Composed Raw` remains populated during dispatch (correct — must compose to raw first)
- Dispatch can skip routing resolution if already done at queue time
