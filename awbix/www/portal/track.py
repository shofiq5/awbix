import frappe
from awbix.www.portal.portal import set_portal_context


def get_context(context):
	set_portal_context(context)
