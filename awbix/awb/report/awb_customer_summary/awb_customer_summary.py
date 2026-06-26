# Copyright (c) 2026, CargoXY and contributors
# AWB Customer Summary Report – Script Report (Python)

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
            "width": 220
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
            "fieldname": "total",
            "label": _("Total AWBs"),
            "fieldtype": "Int",
            "width": 100
        },
        {
            "fieldname": "used",
            "label": _("Used"),
            "fieldtype": "Int",
            "width": 80
        },
        {
            "fieldname": "void_count",
            "label": _("Void"),
            "fieldtype": "Int",
            "width": 80
        },
        {
            "fieldname": "blacklisted",
            "label": _("Blacklisted"),
            "fieldtype": "Int",
            "width": 90
        },
        {
            "fieldname": "balance",
            "label": _("Balance"),
            "fieldtype": "Int",
            "width": 100
        }
    ]


def get_data(filters):
    conditions = ["1=1"]
    values = {}

    if filters.get("customer"):
        conditions.append("assigned_to = %(customer)s")
        values["customer"] = filters["customer"]

    if filters.get("awb_cycle"):
        conditions.append("awb_cycle = %(awb_cycle)s")
        values["awb_cycle"] = filters["awb_cycle"]

    if filters.get("awb_type"):
        conditions.append("awb_type = %(awb_type)s")
        values["awb_type"] = filters["awb_type"]

    where = " AND ".join(conditions)

    data = frappe.db.sql(
        f"""
        SELECT
            COALESCE(ai.assigned_to, '— Unassigned —') AS customer_name,
            ai.awb_cycle,
            ai.awb_type,
            COUNT(DISTINCT ai.name)                    AS total,
            COUNT(DISTINCT CASE WHEN EXISTS (
                    SELECT 1 FROM `tabShp Mst` sm
                    WHERE sm.prefix = ai.awb_prefix
                    AND sm.serial_number = CONCAT(ai.awb_serial, ai.awb_check_digit)
                    AND sm.docstatus IN (0, 1)
                ) THEN CONCAT(ai.awb_prefix, ai.awb_serial, ai.awb_check_digit) ELSE NULL END) AS used,
            SUM(CASE WHEN ai.status = 'Void'        THEN 1 ELSE 0 END) AS void_count,
            SUM(CASE WHEN ai.status = 'Blacklisted' THEN 1 ELSE 0 END) AS blacklisted
        FROM
            `tabAWB Inventory` ai
        WHERE
            {where}
        GROUP BY
            COALESCE(ai.assigned_to, '— Unassigned —'),
            ai.awb_cycle,
            ai.awb_type
        ORDER BY
            customer_name ASC,
            awb_cycle     ASC
        """,
        values=values,
        as_dict=True
    )

    for row in data:
        row["balance"] = row["total"] - row.get("used", 0) - row.get("void_count", 0) - row.get("blacklisted", 0)

    return data


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
            "fieldname": "awb_type",
            "label": _("AWB Type"),
            "fieldtype": "Link",
            "options": "AWB Type"
        }
    ]
