import frappe
from frappe import _


@frappe.whitelist(allow_guest=False)
def get_dashboard_data():
	user = frappe.session.user
	base = {"owner": user}

	from frappe.utils import get_first_day
	from datetime import date

	total = frappe.db.count("Shipment", base)
	submitted = frappe.db.count("Shipment", {**base, "docstatus": 1})
	draft = frappe.db.count("Shipment", {**base, "docstatus": 0})
	this_month = frappe.db.count(
		"Shipment", {**base, "creation": [">=", get_first_day(date.today())]}
	)

	recent = frappe.get_all(
		"Shipment",
		filters=base,
		fields=[
			"name",
			"awb_number",
			"origin",
			"destination",
			"number_of_pieces",
			"weight",
			"shipper_name",
			"docstatus",
			"creation",
		],
		order_by="creation desc",
		limit=10,
	)

	return {
		"total": total,
		"submitted": submitted,
		"draft": draft,
		"this_month": this_month,
		"recent": recent,
	}


@frappe.whitelist(allow_guest=False)
def get_shipments(page=0, page_size=20, search=None, docstatus=None):
	page = int(page)
	page_size = min(int(page_size), 100)
	user = frappe.session.user

	filters = {"owner": user}
	if docstatus not in (None, ""):
		filters["docstatus"] = int(docstatus)
	if search:
		filters["awb_number"] = ["like", f"%{search}%"]

	total = frappe.db.count("Shipment", filters)
	rows = frappe.get_all(
		"Shipment",
		filters=filters,
		fields=[
			"name",
			"awb_number",
			"shipper_name",
			"origin",
			"destination",
			"number_of_pieces",
			"weight",
			"docstatus",
			"creation",
		],
		order_by="creation desc",
		limit_start=page * page_size,
		limit_page_length=page_size,
	)
	return {"total": total, "rows": rows}


@frappe.whitelist(allow_guest=True)
def track_shipment(awb):
	if not awb:
		return {"error": _("AWB number is required.")}

	awb = awb.strip().upper()
	_fields = [
		"name",
		"awb_number",
		"origin",
		"destination",
		"number_of_pieces",
		"weight",
		"docstatus",
		"creation",
	]

	doc = frappe.db.get_value("Shipment", {"awb_number": awb}, _fields, as_dict=True)
	if not doc:
		doc = frappe.db.get_value("Shipment", {"name": awb}, _fields, as_dict=True)
	if not doc:
		return {"error": _("AWB not found. Please check the number and try again.")}

	status_map = {0: "Draft", 1: "Active", 2: "Cancelled"}
	status_class_map = {0: "draft", 1: "active", 2: "cancelled"}

	events = [{"title": "Shipment Record Created", "location": doc.get("origin") or "", "time": ""}]
	if doc.get("docstatus") == 1:
		events.insert(0, {"title": "AWB Submitted", "location": doc.get("origin") or "", "time": ""})

	return {
		"awb_number": doc.get("awb_number") or doc.get("name"),
		"status": status_map.get(doc.get("docstatus"), "Unknown"),
		"status_class": status_class_map.get(doc.get("docstatus"), "draft"),
		"origin": doc.get("origin"),
		"destination": doc.get("destination"),
		"pieces": doc.get("number_of_pieces"),
		"weight": doc.get("weight"),
		"events": events,
	}
