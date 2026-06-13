import frappe
from frappe import _

# ── Icon SVG map (keyed by Portal Menu Item icon field value) ─────────────────
_ICON_SVG = {
	"dashboard":  '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/>',
	"shipments":  '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/>',
	"track":      '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
	"reports":    '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
	"doctype":    '<path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/>',
	"link":       '<path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/>',
	"cog":        '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/>',
	"user":       '<path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/>',
	"chart":      '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
	"calendar":   '<rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',
	"bell":       '<path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/>',
	"folder":     '<path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>',
	"star":       '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
	"heart":      '<path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/>',
	"check":      '<polyline points="20 6 9 17 4 12"/>',
}

_DEFAULT_MENU = [
	{"label": "Dashboard",     "type": "Page",  "route": "/portal",            "icon": "dashboard", "group_label": "Main",    "order": 1},
	{"label": "Shipments",     "type": "Page",  "route": "/portal/shipments",  "icon": "shipments", "group_label": "Main",    "order": 2},
	{"label": "New AWB",       "type": "Page",  "route": "/portal/shipment",   "icon": "doctype",   "group_label": "Main",    "order": 3, "parent_item": "Shipments"},
	{"label": "Draft AWBs",    "type": "Page",  "route": "/portal/shipments?docstatus=0", "icon": "doctype", "group_label": "Main", "order": 4, "parent_item": "Shipments"},
	{"label": "Track AWB",     "type": "Page",  "route": "/portal/track",      "icon": "track",     "group_label": "Main",    "order": 5},
	{"label": "Reports",       "type": "Page",  "route": "/portal/reports/summary", "icon": "reports", "group_label": "Reports", "order": 10},
]

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


# ── Portal Menu ───────────────────────────────────────────────────────────────

@frappe.whitelist(allow_guest=False)
def get_portal_menu():
	"""Return menu items visible to the current user, enriched with icon SVG paths."""
	if not frappe.db.table_exists("tabPortal Menu Item"):
		return {"items": _build_default_menu(), "is_default": True}

	rows = frappe.get_all(
		"Portal Menu Item",
		filters={"enabled": 1},
		fields=["name", "label", "type", "route", "icon", "group_label", "parent_item", "order", "open_in_new_tab"],
		order_by="order asc, label asc",
	)

	if not rows:
		return {"items": _build_default_menu(), "is_default": True}

	for row in rows:
		row["icon_svg"] = _ICON_SVG.get(row.get("icon") or "link", _ICON_SVG["link"])

	return {"items": rows, "is_default": False}


@frappe.whitelist(allow_guest=False)
def save_menu_item(data):
	"""Create or update a Portal Menu Item. Admins only."""
	if "System Manager" not in frappe.get_roles(frappe.session.user):
		frappe.throw(_("Only System Managers can configure the portal menu."), frappe.PermissionError)

	import json
	if isinstance(data, str):
		data = json.loads(data)

	name = data.get("name")
	if name and frappe.db.exists("Portal Menu Item", name):
		doc = frappe.get_doc("Portal Menu Item", name)
	else:
		doc = frappe.new_doc("Portal Menu Item")

	for field in ("label", "type", "route", "icon", "group_label", "parent_item", "order", "enabled", "open_in_new_tab"):
		if field in data:
			doc.set(field, data[field])

	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"name": doc.name, "label": doc.label}


@frappe.whitelist(allow_guest=False)
def delete_menu_item(name):
	"""Delete a Portal Menu Item. Admins only."""
	if "System Manager" not in frappe.get_roles(frappe.session.user):
		frappe.throw(_("Only System Managers can configure the portal menu."), frappe.PermissionError)
	frappe.delete_doc("Portal Menu Item", name, ignore_permissions=True)
	frappe.db.commit()
	return {"deleted": name}


@frappe.whitelist(allow_guest=False)
def seed_default_menu():
	"""Seed the default menu items into Portal Menu Item. Admins only."""
	if "System Manager" not in frappe.get_roles(frappe.session.user):
		frappe.throw(_("Only System Managers can configure the portal menu."), frappe.PermissionError)

	for item in _DEFAULT_MENU:
		if not frappe.db.exists("Portal Menu Item", item["label"]):
			doc = frappe.new_doc("Portal Menu Item")
			for k, v in item.items():
				doc.set(k, v)
			doc.enabled = 1
			doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {"seeded": len(_DEFAULT_MENU)}


def _build_default_menu():
	"""Return default menu list with icon SVGs (no DB required)."""
	items = []
	for item in _DEFAULT_MENU:
		row = dict(item)
		row["icon_svg"] = _ICON_SVG.get(item.get("icon", "link"), _ICON_SVG["link"])
		row["open_in_new_tab"] = 0
		items.append(row)
	return items
