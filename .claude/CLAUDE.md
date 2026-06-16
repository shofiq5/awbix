# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Framework & Runtime

AWBix is a **Frappe Framework v15** custom app. It runs inside a `frappe-bench` environment — all `bench` commands must be run from the bench root (e.g., `~/frappe-bench`), not from this app directory. The `--site` flag was removed in Frappe 15; use the site name directly where required.

Modules defined in `awbix/modules.txt`: **AWBix**, **Shipment** (with EDX and Pricing planned).

## Common Commands

All bench commands run from the bench root:

```bash
# Start development server
bench start

# Run all tests for this app
bench run-tests --app awbix

# Run tests for a specific module
bench run-tests --module Shipment

# Run tests for a specific DocType
bench run-tests --doctype Shipment

# Run a single test file
bench run-tests awbix.shipment.doctype.shipment.test_shipment

# After adding/modifying DocType JSON, migrate and rebuild
bench migrate
bench build
```

Lint and format (run from `apps/awbix`):

```bash
# Lint
ruff check .

# Format
ruff format .

# Run all pre-commit hooks
pre-commit run --all-files
```

Pre-commit runs ruff (lint + format), eslint, prettier, and standard file checks. Install once with `pre-commit install` inside `apps/awbix`.

## Architecture

### DocType Pattern

Every DocType lives under `awbix/<module>/doctype/<doctype_name>/` with three files:
- `<doctype_name>.json` — schema definition (fields, permissions, properties)
- `<doctype_name>.py` — business logic as a `Document` subclass
- `__init__.py` — empty, required by Frappe

Business logic goes in the Python class. Validation errors use `frappe.throw(message)`. The `validate()` method is the main hook for field-level and cross-field checks.

### Shipment Module

The `Shipment` DocType is the core document representing an Air Waybill (AWB). Key details:

- **AWB identifier:** `{airline_prefix}-{awb_serial_number}` (e.g., `AA-12345678`)
- **AWB serial number:** 8 digits; digit 8 is the modulus-7 check digit of digits 1–7 (IATA CSC Resolution 600a). Validated in `Shipment.validate_awb_serial_number()`.
- **Name auto-assignment:** `set_awb_number()` builds `awb_number` from prefix + serial on save.

Child tables attached to `Shipment` (embedded rows stored in separate DB tables linked by `parent`):

| Category | Child DocTypes |
|---|---|
| Routing & Logistics | `shipment_flight_booking`, `shipment_routing`, `shipment_goods_detail` |
| Financial | `shipment_rate_line`, `shipment_other_charge`, `shipment_charge_summary`, `shipment_accounting_info` |
| Parties | `shipment_notify_party`, `shipment_other_participant` |
| Special Services | `shipment_special_handling`, `shipment_special_service_request`, `shipment_other_service_info` |
| Compliance | `shipment_customs_info` |

Master/reference DocTypes (standalone lookup tables): `party`, `party_contact`, `airline`, `airport`, `service_code`, `charge_code`, `other_charge_code`, `rate_class_code`, `special_handling_code`, `measurement_unit_code`, `volume_code`, `uld_type`, `participant_identifier`, `accounting_information_identifier`, `customs_information_identifier`, `oci_information_identifier`, `shipment_reference`.

### Code Style

- Python 3.10+, tabs for indentation, double quotes, 110-char line length (configured in `pyproject.toml`)
- Ruff rule set: standard flake8/pyflakes subset plus `UP` (pyupgrade), `B` (bugbear), `RUF`
- JS/SCSS formatted with prettier, linted with eslint (config in `.eslintrc`)

## Testing

Tests follow Frappe conventions. Typical pattern:

```python
import frappe
from frappe.tests.utils import FrappeTestCase

class TestShipment(FrappeTestCase):
    def test_something(self):
        doc = frappe.new_doc("Shipment")
        doc.field = "value"
        doc.insert()  # triggers validate()
```

Use `frappe.new_doc()` + `.insert()` to trigger validation. Assert `frappe.ValidationError` for expected failures.

## CI

- **CI workflow** (`ci.yml`): runs the full test suite on `develop` branch pushes and PRs (MariaDB + Redis required).
- **Linter workflow** (`linter.yml`): runs Frappe semgrep rules and `pip-audit` on PRs.
