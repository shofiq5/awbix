import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def get_session_info():
	"""Return current user, full name, and CSRF token for SPA bootstrap."""
	user = frappe.session.user
	if not user or user == "Guest":
		return {"user": "Guest", "user_fullname": "Guest", "csrf_token": ""}
	full_name = frappe.db.get_value("User", user, "full_name") or user
	return {
		"user": user,
		"user_fullname": full_name,
		"csrf_token": frappe.local.session.data.csrf_token,
	}


@frappe.whitelist(allow_guest=False)
def get_parties(page=0, page_size=20, search=None, role_filter=None):
	page = int(page)
	page_size = min(int(page_size), 100)

	filters = []
	if search:
		filters.append(['party_name', 'like', f'%{search}%'])
	if role_filter:
		filters.append([role_filter, '=', 1])

	total = frappe.db.count('Party', filters)
	rows = frappe.get_all(
		'Party',
		filters=filters,
		fields=[
			'name',
			'party_name',
			'account_number',
			'country',
			'is_shipper',
			'is_consignee',
			'is_notify',
			'is_agent',
		],
		order_by='party_name asc',
		limit_start=page * page_size,
		limit_page_length=page_size,
	)
	return {'total': total, 'rows': rows}


@frappe.whitelist(allow_guest=False)
def get_party(name):
	doc = frappe.get_doc('Party', name)
	return {
		'name': doc.name,
		'party_name': doc.party_name,
		'account_number': doc.account_number,
		'street_address': doc.street_address,
		'place': doc.place,
		'state_province': doc.state_province,
		'country': doc.country,
		'post_code': doc.post_code,
		'is_shipper': doc.is_shipper,
		'is_consignee': doc.is_consignee,
		'is_notify': doc.is_notify,
		'is_agent': doc.is_agent,
		'iata_cargo_agent_code': doc.iata_cargo_agent_code,
		'cass_address': doc.cass_address,
		'participant_id': doc.participant_id,
		'participant_code': doc.participant_code,
		'contacts': [
			{'contact_identifier': c.contact_identifier, 'contact_number': c.contact_number}
			for c in (doc.contacts or [])
		],
		'modified': doc.modified,
	}


@frappe.whitelist(allow_guest=False)
def save_party(data):
	import json

	if isinstance(data, str):
		data = json.loads(data)

	name = data.get('name')
	is_new = not name or name == 'new'

	if is_new:
		doc = frappe.new_doc('Party')
	else:
		doc = frappe.get_doc('Party', name)

	# Map form fields to doc fields
	doc.party_name = data.get('party_name')
	doc.account_number = data.get('account_number') or ''
	doc.street_address = data.get('street_address') or ''
	doc.place = data.get('place') or ''
	doc.state_province = data.get('state_province') or ''
	doc.country = data.get('country') or ''
	doc.post_code = data.get('post_code') or ''
	doc.is_shipper = 1 if data.get('is_shipper') else 0
	doc.is_consignee = 1 if data.get('is_consignee') else 0
	doc.is_notify = 1 if data.get('is_notify') else 0
	doc.is_agent = 1 if data.get('is_agent') else 0
	doc.iata_cargo_agent_code = data.get('iata_cargo_agent_code') or ''
	doc.cass_address = data.get('cass_address') or ''
	doc.participant_id = data.get('participant_id') or ''
	doc.participant_code = data.get('participant_code') or ''

	# Clear and rebuild contacts
	doc.contacts = []
	for c in data.get('contacts', []):
		if c.get('contact_number', '').strip():
			doc.append('contacts', {
				'contact_identifier': c.get('contact_identifier', 'TE'),
				'contact_number': c.get('contact_number'),
			})

	doc.save()
	frappe.db.commit()

	return {
		'name': doc.name,
		'party_name': doc.party_name,
		'modified': doc.modified,
	}


@frappe.whitelist(allow_guest=False)
def delete_party(name):
	frappe.delete_doc('Party', name)
	frappe.db.commit()
	return {'deleted': name}
