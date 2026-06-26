# Copyright (c) 2026, CargoXY and contributors
# AWB Customer Detail Report – Script Report (Python)

import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "fieldname": "customer_name",
            "label": _("Customer"),
            "fieldtype": "Link",
            "options": "Customer",
            "width": 200
        },
        {
            "fieldname": "awb_cycle",
            "label": _("Cycle (Year)"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "awb_type",
            "label": _("AWB Type"),
            "fieldtype": "Data",
            "width": 110
        },
        {
            "fieldname": "awb_prefix",
            "label": _("Prefix"),
            "fieldtype": "Data",
            "width": 80
        },
        {
            "fieldname": "full_awb_number",
            "label": _("Full AWB Number"),
            "fieldtype": "Data",
            "width": 160
        },
        {
            "fieldname": "awb_serial",
            "label": _("Serial"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "awb_check_digit",
            "label": _("Check Digit"),
            "fieldtype": "Int",
            "width": 90
        },
        {
            "fieldname": "status",
            "label": _("Status"),
            "fieldtype": "Data",
            "width": 110
        },
        {
            "fieldname": "assigned_date",
            "label": _("Assigned Date"),
            "fieldtype": "Date",
            "width": 120
        },
        {
            "fieldname": "withdrawn_date",
            "label": _("Withdrawn Date"),
            "fieldtype": "Date",
            "width": 120
        },
        {
            "fieldname": "remarks",
            "label": _("Remarks"),
            "fieldtype": "Data",
            "width": 200
        }
    ]


def get_data(filters):
    conditions = ["1=1"]
    values = {}

    if filters.get("customer"):
        conditions.append("ai.assigned_to = %(customer)s")
        values["customer"] = filters["customer"]

    if filters.get("awb_cycle"):
        conditions.append("ai.awb_cycle = %(awb_cycle)s")
        values["awb_cycle"] = filters["awb_cycle"]

    if filters.get("awb_prefix"):
        conditions.append("ai.awb_prefix = %(awb_prefix)s")
        values["awb_prefix"] = filters["awb_prefix"]

    if filters.get("awb_type"):
        conditions.append("ai.awb_type = %(awb_type)s")
        values["awb_type"] = filters["awb_type"]

    if filters.get("status"):
        conditions.append("ai.status = %(status)s")
        values["status"] = filters["status"]

    where = " AND ".join(conditions)

    return frappe.db.sql(
        f"""
        SELECT
            ai.assigned_to   AS customer_name,
            ai.awb_cycle,
            ai.awb_type,
            ai.awb_prefix,
            ai.full_awb_number,
            ai.awb_serial,
            ai.awb_check_digit,
            ai.status,
            ai.assigned_date,
            ai.withdrawn_date,
            ai.remarks
        FROM
            `tabAWB Inventory` AS ai
        WHERE
            {where}
        ORDER BY
            ai.assigned_to ASC,
            ai.awb_prefix  ASC,
            ai.awb_serial  ASC
        """,
        values=values,
        as_dict=True
    )


def get_filters():
    return [
        {
            "fieldname": "customer",
            "label": _("Customer"),
            "fieldtype": "Link",
            "options": "Customer"
        },
        {
            "fieldname": "awb_cycle",
            "label": _("AWB Cycle (Year)"),
            "fieldtype": "Data"
        },
        {
            "fieldname": "awb_prefix",
            "label": _("AWB Prefix"),
            "fieldtype": "Data"
        },
        {
            "fieldname": "awb_type",
            "label": _("AWB Type"),
            "fieldtype": "Link",
            "options": "AWB Type"
        },
        {
            "fieldname": "status",
            "label": _("Status"),
            "fieldtype": "Select",
            "options": "\nAvailable\nAssigned\nWithdrawn\nVoid\nHold\nBlacklisted"
        }
    ]
