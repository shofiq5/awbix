# FWB/16 ABNF Validator Demo

## Overview
The new `FWBABNFValidator` validates FWB/16 messages against ABNF grammar rules. It validates **each data element** according to the rules and returns **only violations** (no noise).

## What Changed
- **Old validator**: Generic segment checking with many false positives
- **New validator**: Strict ABNF-based validation with data element format checking

## How It Works

### 1. Validates Data Elements by Format
Each data element has a specific format defined in the ABNF grammar:

```
DE112_AirlinePrefix = 3Numeric       # Must be exactly 3 digits
DE113_AWBSerialNumber = 8Numeric     # Must be exactly 8 digits
DE313_AirportCityCode = 3Alpha       # Must be exactly 3 letters
DE606_ISOCurrencyCode = 3Alpha       # Must be exactly 3 letters
DE600_Weight = 1*7Decimal            # 1-7 decimal digits
```

### 2. Returns Only Violations
When you call `validator.validate(message)`, you get **only** violations:

```python
from awbix.edx.handlers.fwb.fwb16_validator import FWBABNFValidator

validator = FWBABNFValidator()
violations = validator.validate(fwb_message)

# Returns:
[
    {
        "level": "Error",
        "code": "DE113_AWBSerialNumber",
        "field": "DE113_AWBSerialNumber",
        "message": "Check digit validation failed (mod-7)"
    },
    {
        "level": "Error",
        "code": "RTG",
        "field": "RTG",
        "message": "Required segment 'RTG' is missing"
    }
]
```

## Example Violations

### Example 1: Bad AWB Check Digit
```
Message line: 001-12345671/JFK/LAX/T100K1000
Violation:   DE113_AWBSerialNumber: Check digit validation failed (mod-7)
Expected:    Check digit (8th digit) must match mod-7 of first 7 digits
```

### Example 2: Invalid Currency Code
```
Message line: CVD/XX/...
Violation:   DE606_ISOCurrencyCode: Currency must be 3 alpha, got 'XX'
Expected:    3-letter ISO currency code (e.g., USD, EUR)
```

### Example 3: Bad Weight Code
```
Message line: 001-12345670/JFK/LAX/T100X1000
Violation:   DE601_WeightCode: Expected K or L, got 'X'
Expected:    K=kilogrammes or L=pounds
```

### Example 4: Missing Required Segment
```
Message missing: RTG segment
Violation:   RTG: Required segment 'RTG' is missing
Expected:    Routing segment is mandatory
```

### Example 5: Same Origin and Destination
```
Message line: 001-12345670/JFK/JFK/T100K1000
Violation:   AWBOriginAndDestination: Origin and destination cannot be identical
Expected:    Origin and destination must be different airports
```

## Integration with UI

The validator is integrated into the "Verify Message" button on the EDX Message Out form:

1. User clicks "Verify Message" button
2. Validator runs: `FWBABNFValidator().validate(composed_raw)`
3. Returns list of violations
4. UI displays:
   - Pass/Fail indicator (green/red)
   - Table with columns: Field | Message
   - "Copy as JSON" button

## Data Element Format Rules

The validator knows these formats:

| Format | Meaning | Example |
|--------|---------|---------|
| `3Alpha` | Exactly 3 uppercase letters | `JFK`, `USD` |
| `3Numeric` | Exactly 3 digits | `001`, `100` |
| `8Numeric` | Exactly 8 digits | `12345670` |
| `2Mixed` | 2 alphanumeric chars | `AA`, `1A` |
| `1*35Text` | 1-35 text chars (letters/digits/dash/dot/space) | `SHIPPER LTD`, `123 MAIN ST` |
| `1*7Decimal` | 1-7 decimal (with optional dot) | `1000`, `100.5` |
| `1*12Decimal` | 1-12 decimal | `10000.99` |

## Testing

Run the unit tests:
```bash
cd ~/frappe-bench
bench run-tests awbix.edx.handlers.fwb.test_fwb16_abnf
```

## Files

- `awbix/edx/handlers/fwb/fwb16_validator.py` — The validator class
- `awbix/edx/handlers/fwb/fwb16_composer.py` — Updated to call validator
- `awbix/edx/engine/pipeline.py` — Endpoint `verify_message_out()`
- `awbix/edx/doctype/edx_message_out/edx_message_out.js` — UI button and modal
