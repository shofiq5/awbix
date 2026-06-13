import frappe


def get_context(context):
	context.no_cache = 1
	name = frappe.form_dict.get("name", "new")
	context.is_new = name == "new"
	context.shipment_name = None if context.is_new else name

	if context.is_new:
		context.page_title = "New AWB"
		context.awb_display = "New AWB"
	else:
		awb = frappe.db.get_value("Shipment", name, "awb_number") or name
		context.page_title = f"AWB: {awb}"
		context.awb_display = awb

	# Collect Link field options for quick dropdowns
	context.airlines = frappe.get_all("Airline", fields=["name", "airline_name"], order_by="name")
	context.airports = frappe.get_all("Airport", fields=["name", "airport_name"], order_by="name")
	context.currencies = frappe.get_all("Currency", fields=["name"], filters={"enabled": 1}, order_by="name")
	context.countries = frappe.get_all("Country", fields=["name"], order_by="name")
