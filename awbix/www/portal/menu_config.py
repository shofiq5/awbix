import frappe
from .portal import set_portal_context


def get_context(context):
	set_portal_context(context)

	if context.get("_is_guest"):
		frappe.local.flags.redirect_location = "/login"
		raise frappe.Redirect

	if "System Manager" not in frappe.get_roles(frappe.session.user):
		frappe.throw("Access denied — System Manager role required.", frappe.PermissionError)

	context.update({
		"page_title": "Configure Portal Menu",
		"no_cache": 1,
	})
