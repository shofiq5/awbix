# Copyright (c) 2026, CargoXY and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today


class AWBInventory(Document):
    # ------------------------------------------------------------------ #
    #  Frappe lifecycle hooks
    # ------------------------------------------------------------------ #

    def validate(self):
        self._validate_serial()
        self._calculate_check_digit()
        self._build_full_awb_number()
        self._validate_assignment_fields()

    # ------------------------------------------------------------------ #
    #  Private helpers
    # ------------------------------------------------------------------ #

    def _validate_serial(self):
        serial = (self.awb_serial or "").strip().zfill(7)
        if not serial.isdigit() or len(serial) != 7:
            frappe.throw(_("AWB Serial must be exactly 7 numeric digits."))
        self.awb_serial = serial

    def _calculate_check_digit(self):
        self.awb_check_digit = int(self.awb_serial) % 7

    def _build_full_awb_number(self):
        self.full_awb_number = (
            f"{self.awb_prefix}-{self.awb_serial}{self.awb_check_digit}"
        )

    def _validate_assignment_fields(self):
        if self.status == "Assigned" and not self.assigned_to:
            frappe.throw(_("Please set 'Assigned To (Customer)' when status is Assigned."))
        if self.status != "Assigned":
            # Clear customer if not assigned
            if self.status in ("Available", "Void", "Hold", "Blacklisted"):
                self.assigned_to = None
                self.assigned_date = None
        if self.status == "Withdrawn" and not self.assigned_to:
            # Keep last customer reference but clear assign date
            self.assigned_date = None
            if not self.withdrawn_date:
                self.withdrawn_date = today()
