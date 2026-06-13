import frappe


def set_portal_context(context):
	"""Set common context variables for all portal pages."""
	user = frappe.session.user
	is_guest = user == "Guest"
	is_admin = (not is_guest) and ("System Manager" in frappe.get_roles(user))

	context.update({
		"_user": user,
		"_is_guest": is_guest,
		"_user_short": user.split("@")[0] if not is_guest else "Guest",
		"_is_admin": is_admin,
	})


def get_context(context):
	set_portal_context(context)
