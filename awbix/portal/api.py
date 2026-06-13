import frappe
from frappe import _

_SHIPMENT_FIELDS = [
	"name", "awb_number", "airline_prefix", "awb_serial_number",
	"origin", "destination", "shipment_description_code",
	"number_of_pieces", "weight_code", "weight", "volume_code", "volume_amount",
	"currency", "charge_code",
	"wt_val_prepaid_collect", "other_charges_prepaid_collect",
	"declared_value_carriage_type", "declared_value_carriage_amount",
	"declared_value_customs_type", "declared_value_customs_amount",
	"insurance_type", "insurance_amount",
	"shipper", "shipper_name", "shipper_account", "shipper_address",
	"shipper_place", "shipper_state", "shipper_country", "shipper_post_code",
	"consignee", "consignee_name", "consignee_account", "consignee_address",
	"consignee_place", "consignee_state", "consignee_country", "consignee_post_code",
	"agent", "agent_name", "agent_account", "agent_place",
	"agent_iata_code", "agent_cass_address", "agent_participant_id",
	"docstatus", "creation", "modified",
]

_EDITABLE_FIELDS = [f for f in _SHIPMENT_FIELDS if f not in ("name", "awb_number", "docstatus", "creation", "modified")]


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


@frappe.whitelist(allow_guest=False)
def get_shipment(name):
	doc = frappe.get_doc("Shipment", name)
	if doc.owner != frappe.session.user and not frappe.has_permission("Shipment", "read", doc):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return {f: doc.get(f) for f in _SHIPMENT_FIELDS}


@frappe.whitelist(allow_guest=False)
def save_shipment(data):
	import json

	if isinstance(data, str):
		data = json.loads(data)

	name = data.get("name")
	is_new = not name or name == "new"

	if is_new:
		doc = frappe.new_doc("Shipment")
	else:
		doc = frappe.get_doc("Shipment", name)
		if doc.owner != frappe.session.user and not frappe.has_permission("Shipment", "write", doc):
			frappe.throw(_("Not permitted"), frappe.PermissionError)
		if doc.docstatus == 1:
			frappe.throw(_("Submitted AWBs cannot be edited. Amend first."))

	for field in _EDITABLE_FIELDS:
		val = data.get(field)
		if val is not None and val != "":
			doc.set(field, val)
		elif field not in ("awb_number",) and val == "":
			doc.set(field, None)

	doc.save(ignore_permissions=False)
	frappe.db.commit()

	return {
		"name": doc.name,
		"awb_number": doc.awb_number,
		"docstatus": doc.docstatus,
		"is_new": is_new,
	}


@frappe.whitelist(allow_guest=False)
def submit_shipment(name):
	doc = frappe.get_doc("Shipment", name)
	if doc.owner != frappe.session.user and not frappe.has_permission("Shipment", "submit", doc):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	doc.submit()
	frappe.db.commit()
	return {"name": doc.name, "awb_number": doc.awb_number, "docstatus": doc.docstatus}


@frappe.whitelist(allow_guest=False)
def cancel_shipment(name):
	doc = frappe.get_doc("Shipment", name)
	if doc.owner != frappe.session.user and not frappe.has_permission("Shipment", "cancel", doc):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	doc.cancel()
	frappe.db.commit()
	return {"name": doc.name, "docstatus": doc.docstatus}
