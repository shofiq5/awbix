# Copyright (c) 2026, CargoXY and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class AWBSeriesGenerator(Document):
    # ------------------------------------------------------------------ #
    #  Frappe lifecycle hooks
    # ------------------------------------------------------------------ #

    def validate(self):
        self._validate_prefix()
        self._validate_cycle()
        self._validate_serial_range()
        self._calculate_total_count()

    def before_save(self):
        # Prevent editing after generation (skip for new documents or fixture import)
        if not self.is_new() and self.generation_status == "Generated":
            # Check if any significant fields have changed
            if self.has_value_changed("generation_status") or self.has_value_changed("awb_prefix") or \
               self.has_value_changed("awb_cycle") or self.has_value_changed("serial_start") or \
               self.has_value_changed("serial_end") or self.has_value_changed("awb_type"):
                frappe.throw(
                    _("Cannot modify an AWB Series that has already been Generated. "
                      "Create a new series instead.")
                )

    # ------------------------------------------------------------------ #
    #  Private validation helpers
    # ------------------------------------------------------------------ #

    def _validate_prefix(self):
        prefix = (self.awb_prefix or "").strip()
        if not prefix.isdigit() or len(prefix) != 3:
            frappe.throw(_("AWB Prefix must be exactly 3 numeric digits (e.g. 157)."))
        self.awb_prefix = prefix

    def _validate_cycle(self):
        cycle = (self.awb_cycle or "").strip()
        if not cycle.isdigit() or len(cycle) != 4:
            frappe.throw(_("AWB Cycle must be a 4-digit year (e.g. 2026)."))
        self.awb_cycle = cycle

    def _validate_serial_range(self):
        start = (self.serial_start or "").strip()
        end = (self.serial_end or "").strip()

        if not start.isdigit() or len(start) != 7:
            frappe.throw(_("Serial Start must be exactly 7 numeric digits."))
        if not end.isdigit() or len(end) != 7:
            frappe.throw(_("Serial End must be exactly 7 numeric digits."))
        if int(start) > int(end):
            frappe.throw(_("Serial Start ({0}) cannot be greater than Serial End ({1}).").format(start, end))

        self.serial_start = start
        self.serial_end = end

    def _calculate_total_count(self):
        if self.serial_start and self.serial_end:
            self.total_count = int(self.serial_end) - int(self.serial_start) + 1

    # ------------------------------------------------------------------ #
    #  Core generation method (called from JS button)
    # ------------------------------------------------------------------ #

    @frappe.whitelist()
    def generate_awb_inventory(self):
        """
        Bulk-create AWB Inventory records for the defined serial range.
        Uses batch inserts for performance. Check digit = serial_int % 7.
        """
        if self.generation_status == "Generated":
            frappe.throw(_("AWB Inventory has already been generated for this series."))

        start_int = int(self.serial_start)
        end_int = int(self.serial_end)

        # Collect all full AWB numbers to detect duplicates in one query
        existing = set(
            frappe.get_all(
                "AWB Inventory",
                filters={"awb_prefix": self.awb_prefix},
                pluck="awb_serial",
            )
        )

        records = []
        skipped = 0
        today = frappe.utils.today()

        for serial_int in range(start_int, end_int + 1):
            serial_str = str(serial_int).zfill(7)

            if serial_str in existing:
                skipped += 1
                continue

            check_digit = serial_int % 7
            full_awb = f"{self.awb_prefix}-{serial_str}{check_digit}"

            records.append({
                "doctype": "AWB Inventory",
                "awb_cycle": self.awb_cycle,
                "awb_type": self.awb_type,
                "awb_prefix": self.awb_prefix,
                "awb_serial": serial_str,
                "awb_check_digit": check_digit,
                "full_awb_number": full_awb,
                "status": "Available",
                "generated_by": self.name,
                "generated_date": today,
            })

        if not records:
            frappe.throw(
                _("No new AWB records to generate — all serials in this range already exist.")
            )

        # Batch insert using frappe.db.bulk_insert for efficiency
        created = 0
        BATCH_SIZE = 500
        for i in range(0, len(records), BATCH_SIZE):
            batch = records[i: i + BATCH_SIZE]
            for rec in batch:
                doc = frappe.get_doc(rec)
                doc.insert(ignore_permissions=True)
            frappe.db.commit()
            created += len(batch)

        # Update generator status
        self.db_set("generation_status", "Generated")
        self.db_set("generated_count", created)
        self.db_set("generated_date", now_datetime())

        msg = _("{0} AWB records generated successfully.").format(created)
        if skipped:
            msg += _(" {0} serial(s) skipped (already exist).").format(skipped)

        frappe.msgprint(msg, title=_("AWB Generation Complete"), indicator="green")
        return {"created": created, "skipped": skipped}
