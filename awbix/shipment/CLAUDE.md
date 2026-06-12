# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Module Overview

The **Shipment** module is the core logistics management component of the AWBix cargo system. It handles the complete lifecycle of air shipments, from initial Air Waybill (AWB) creation through goods tracking and charge calculations. The module implements IATA standards for shipment documentation and follows the Frappe framework conventions.

**Key Responsibility:** Managing shipment data structures, validation, and operational workflows that comply with international cargo standards.

## Core Concepts

### Air Waybill (AWB)
- **Identifier Format:** `{airline_prefix}-{awb_serial_number}` (e.g., "AA-12345678")
- **Serial Number:** 8-digit code with modulus-7 check digit validation (IATA CSC Resolution 600a)
- **Check Digit:** The 8th digit is calculated as `first_seven_digits % 7`
- **Validation:** Performed in `Shipment.validate_awb_serial_number()`

### Shipment Structure
- **Core Fields:** Origin airport, destination airport, weight, volume, currency, charges
- **Parties Involved:** Shipper, consignee, agent, also-notify
- **Flight Routing:** Multiple flight segments with routing details
- **Goods Details:** Item-level descriptions and measurements
- **Charges:** Rate lines, other charges, charge summaries with prepaid/collect accounting
- **Special Services:** Service requests, special handling, customs information, accounting details

## DocType Hierarchy

**Main DocType (Parent):**
- `Shipment` — Core shipment document with validation and AWB management

**Child DocTypes (Embedded):**
- **Routing & Logistics:** `shipment_flight_booking`, `shipment_routing`, `shipment_goods_detail`
- **Financial:** `shipment_rate_line`, `shipment_other_charge`, `shipment_charge_summary`, `shipment_accounting_info`
- **Parties:** `shipment_notify_party`, `shipment_other_participant`
- **Special Services:** `shipment_special_handling`, `shipment_special_service_request`, `shipment_other_service_info`
- **Compliance:** `shipment_customs_info`

**Reference DocTypes (Standalone Masters):**
- `party`, `airline`, `airport`, `service_code`, `charge_code`, `rate_class_code`
- `special_handling_code`, `measurement_unit_code`, `volume_code`, `uld_type`
- Various identifier types: `participant_identifier`, `accounting_information_identifier`, `customs_information_identifier`, `oci_information_identifier`

## Development Commands

### Frappe Bench Commands

**Run Tests for Shipment Module:**
```bash
bench run-tests --module shipment
```

**Run Tests for Specific DocType:**
```bash
bench run-tests --doctype Shipment
```

**Run a Single Test File:**
```bash
bench run-tests awbix.shipment.doctype.shipment.test_shipment
```

**Start Development Server:**
```bash
bench start
```

**Access Frappe Desk:**
Navigate to `http://localhost:8000` and use the "Shipment" list to view/create shipment documents.

### Code Quality

**Check Code with Ruff (Linter):**
```bash
ruff check shipment/
```

**Format Code with Ruff:**
```bash
ruff format shipment/
```

**Configuration:** Ruff settings are in `pyproject.toml` with:
- Line length: 110 characters
- Quote style: Double quotes
- Indent style: Tabs
- Python target: 3.10+

## Key Patterns & Conventions

### Validation in DocType Classes
- Override `validate()` method in the Document class
- Use `frappe.throw(message)` to raise validation errors with user-friendly messages
- Examples:
  ```python
  def validate(self):
      self.validate_awb_serial_number()
      self.set_awb_number()
      if self.origin == self.destination:
          frappe.throw("Origin and Destination cannot be the same airport.")
  ```

### AWB Validation
- Always validate the 8-digit serial number structure and check digit
- Error messages should specify the expected vs. actual check digit
- Referenced in: `Shipment.validate_awb_serial_number()` (shipment/doctype/shipment/shipment.py:16-29)

### DocType Structure
- **JSON Definition:** `doctype/{doctype_name}/{doctype_name}.json` — schema, fields, properties
- **Python Class:** `doctype/{doctype_name}/{doctype_name}.py` — business logic, validations
- **`__init__.py`:** Present but empty (Frappe framework convention)

### Field Organization
- DocTypes use section headers (fields starting with `sb_` or `cb_`) to organize related fields
- Child table rows contain specific data (e.g., `flight_bookings` table has `shipment_flight_booking` rows)
- Reference fields link to master data (e.g., `origin` -> `airport` doctype)

## Data Flow

1. **Shipment Creation:** User creates a Shipment document via Frappe Desk
2. **Validation:** `Shipment.validate()` checks AWB format and business rules
3. **Name Assignment:** Auto-named based on `{airline_prefix}-{awb_serial_number}` pattern
4. **Child Table Population:** Users add routing, goods, charges, and special services
5. **Storage:** Document saved to MariaDB via Frappe ORM
6. **Queries:** Data retrieved via Frappe's query interface or REST API

## Important Notes

- **IATA Compliance:** Shipment structure follows international air cargo standards (AWB, charge codes, special handling codes)
- **Multi-party System:** Shipments track multiple stakeholders (shipper, consignee, agent, notify parties)
- **Modular Charges:** Charges are broken down into rate lines and other charges, then summarized
- **Child Tables:** All detail data (routing, goods, charges) are stored as child table rows linked to the main Shipment
- **Master Data Dependencies:** Many fields reference master data (airlines, airports, service codes) to ensure consistency

## Testing Notes

- Tests follow Frappe conventions with test modules named `test_{doctype_name}.py`
- Use `frappe.new_doc()` to create test documents
- Use `.insert()` to save and trigger validation
- Use `.save()` for updates without auto-assignment
- Error assertions should check for `frappe.ValidationError` exceptions
