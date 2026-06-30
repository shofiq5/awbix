import json

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


# ── Shipment / AWB endpoints ───────────────────────────────────────────────────


@frappe.whitelist(allow_guest=False)
def get_shipments(page=0, page_size=20, search=None):
	page = int(page)
	page_size = min(int(page_size), 100)

	filters = []
	if search:
		filters.append(['awb_number', 'like', f'%{search}%'])

	total = frappe.db.count('Shipment', filters)
	rows = frappe.get_all(
		'Shipment',
		filters=filters,
		fields=[
			'name',
			'awb_number',
			'airline_prefix',
			'awb_serial_number',
			'origin',
			'destination',
			'weight',
			'weight_code',
			'chargeable_weight',
			'number_of_pieces',
			'shipper_name',
			'consignee_name',
			'currency',
			'docstatus',
			'modified',
		],
		order_by='modified desc',
		limit_start=page * page_size,
		limit_page_length=page_size,
	)
	return {'total': total, 'rows': rows}


@frappe.whitelist(allow_guest=False)
def get_shipment(name):
	doc = frappe.get_doc('Shipment', name)
	return {
		# Identity
		'name': doc.name,
		'awb_number': doc.awb_number,
		'airline_prefix': doc.airline_prefix,
		'awb_serial_number': doc.awb_serial_number,
		'origin': doc.origin,
		'destination': doc.destination,
		'e_awb': doc.e_awb,
		'console': doc.console,
		'docstatus': doc.docstatus,
		'modified': doc.modified,
		# Mandatory weights & measures
		'number_of_pieces': doc.number_of_pieces,
		'weight': doc.weight,
		'weight_code': doc.weight_code,
		'volume_amount': doc.volume_amount,
		'volume_weight': doc.volume_weight,
		'chargeable_weight': doc.chargeable_weight,
		'volume_weight_factor': doc.volume_weight_factor,
		'volume_code': doc.volume_code,
		'currency': doc.currency,
		# Rating header
		'iata_rate': doc.iata_rate,
		'rate_class': doc.rate_class,
		'charge_code': doc.charge_code,
		'nature_of_goods': doc.nature_of_goods,
		'commodity_item_no': doc.commodity_item_no,
		'wt_val_prepaid_collect': doc.wt_val_prepaid_collect,
		'other_charges_prepaid_collect': doc.other_charges_prepaid_collect,
		'declared_value_carriage_type': doc.declared_value_carriage_type,
		'declared_value_carriage_amount': doc.declared_value_carriage_amount,
		'declared_value_customs_type': doc.declared_value_customs_type,
		'declared_value_customs_amount': doc.declared_value_customs_amount,
		'insurance_type': doc.insurance_type,
		'insurance_amount': doc.insurance_amount,
		# Shipper
		'shipper_name': doc.shipper_name,
		'shipper_account': doc.shipper_account,
		'shipper_address': doc.shipper_address,
		'shipper_place': doc.shipper_place,
		'shipper_state': doc.shipper_state,
		'shipper_country': doc.shipper_country,
		'shipper_post_code': doc.shipper_post_code,
		# Consignee
		'consignee_name': doc.consignee_name,
		'consignee_account': doc.consignee_account,
		'consignee_address': doc.consignee_address,
		'consignee_place': doc.consignee_place,
		'consignee_state': doc.consignee_state,
		'consignee_country': doc.consignee_country,
		'consignee_post_code': doc.consignee_post_code,
		# Agent (read-only fetched fields — returned for display only)
		'agent': doc.agent,
		'agent_name': doc.agent_name,
		'agent_place': doc.agent_place,
		'agent_account': doc.agent_account,
		'agent_iata_code': doc.agent_iata_code,
		'agent_cass_address': doc.agent_cass_address,
		'agent_participant_id': doc.agent_participant_id,
		# Certification & fine-print
		'shippers_certification_signature': doc.shippers_certification_signature,
		'issue_date': str(doc.issue_date) if doc.issue_date else '',
		'issue_place': doc.issue_place,
		'carrier_execution_signature': doc.carrier_execution_signature,
		'no_commission_indicator': doc.no_commission_indicator,
		'commission_amount': doc.commission_amount,
		'commission_percentage': doc.commission_percentage,
		'sales_incentive_amount': doc.sales_incentive_amount,
		'sales_incentive_indicator': doc.sales_incentive_indicator,
		'agent_reference': doc.agent_reference,
		# Sender
		'sender_file_reference': doc.sender_file_reference,
		'sender_office_address': doc.sender_office_address,
		'sender_participant_id': doc.sender_participant_id,
		'sender_participant_code': doc.sender_participant_code,
		# EDX ack (read-only system)
		'edx_ack_status': doc.edx_ack_status,
		'edx_ack_detail': doc.edx_ack_detail,
		'edx_ack_at': str(doc.edx_ack_at) if doc.edx_ack_at else '',
		# CDC
		'cc_dest_currency': doc.cc_dest_currency,
		'rate_of_exchange': doc.rate_of_exchange,
		'cc_charges_dest': doc.cc_charges_dest,
		'charges_at_dest': doc.charges_at_dest,
		'total_collect_charges': doc.total_collect_charges,
		# Customs
		'customs_origin_code': doc.customs_origin_code,
		# Nominated handling
		'nominated_handling_name': doc.nominated_handling_name,
		'nominated_handling_place': doc.nominated_handling_place,
		# Internal
		'customer': doc.customer,
		'supplier': doc.supplier,
		# Hidden dimensions child table (raw rows only — server computes volume/volume_weight)
		'dimensions': [
			{
				'line_number': r.line_number,
				'pieces': r.pieces,
				'length': r.length,
				'width': r.width,
				'height': r.height,
				'dim_unit': r.dim_unit,
				'remarks': r.remarks,
			}
			for r in (doc.dimensions or [])
		],
		# Child tables
		'also_notify': [
			{
				'party': r.party,
				'notify_name': r.notify_name,
				'street_address': r.street_address,
				'place': r.place,
				'state_province': r.state_province,
				'country': r.country,
				'post_code': r.post_code,
				'telephone': r.telephone,
				'fax': r.fax,
			}
			for r in (doc.also_notify or [])
		],
		'other_participants': [
			{
				'participant_name': r.participant_name,
				'office_file_reference': r.office_file_reference,
				'participant_id': r.participant_id,
				'participant_code': r.participant_code,
				'airport': r.airport,
			}
			for r in (doc.other_participants or [])
		],
		'flight_bookings': [
			{
				'carrier': r.carrier,
				'carrier_code': r.carrier_code,
				'flight_number': r.flight_number,
				'flight_day': r.flight_day,
				'flight_month': r.flight_month,
				'departure_airport': r.departure_airport,
				'arrival_airport': r.arrival_airport,
				'space_allocation_code': r.space_allocation_code,
				'allotment_id': r.allotment_id,
			}
			for r in (doc.flight_bookings or [])
		],
		'routing': [
			{
				'sequence': r.sequence,
				'airport': r.airport,
				'carrier': r.carrier,
				'carrier_code': r.carrier_code,
			}
			for r in (doc.routing or [])
		],
		'rate_lines': [
			{
				'line_number': r.line_number,
				'number_of_pieces': r.number_of_pieces,
				'rate_class_code': r.rate_class_code,
				'gross_weight': r.gross_weight,
				'gross_weight_code': r.gross_weight_code,
				'chargeable_weight': r.chargeable_weight,
				'rate_charge': r.rate_charge,
				'total': r.total,
				'goods_data_identifier': r.goods_data_identifier,
				'description': r.description,
				'rate_combination_point': r.rate_combination_point,
				'commodity_item_number': r.commodity_item_number,
				'uld_rate_class_type': r.uld_rate_class_type,
				'rate_class_percentage': r.rate_class_percentage,
			}
			for r in (doc.rate_lines or [])
		],
		'goods_details': [
			{
				'rate_line_number': r.rate_line_number,
				'goods_data_identifier': r.goods_data_identifier,
				'description': r.description,
				'hs_code': r.hs_code,
				'country_of_origin': r.country_of_origin,
				'slac': r.slac,
				'volume_code': r.volume_code,
				'volume_amount': r.volume_amount,
				'uld_type': r.uld_type,
				'uld_serial': r.uld_serial,
				'uld_owner': r.uld_owner,
				'measurement_unit': r.measurement_unit,
				'dim_weight_code': r.dim_weight_code,
				'dim_weight': r.dim_weight,
				'dim_length': r.dim_length,
				'dim_width': r.dim_width,
				'dim_height': r.dim_height,
				'dim_pieces': r.dim_pieces,
				'service_code': r.service_code,
			}
			for r in (doc.goods_details or [])
		],
		'other_charges': [
			{
				'prepaid_collect': r.prepaid_collect,
				'other_charge_code': r.other_charge_code,
				'amount': r.amount,
			}
			for r in (doc.other_charges or [])
		],
		'special_service_requests': [
			{'special_service_request': r.special_service_request}
			for r in (doc.special_service_requests or [])
		],
		'special_handling': [
			{
				'special_handling_code': r.special_handling_code,
				'description': r.description,
			}
			for r in (doc.special_handling or [])
		],
		'other_service_info': [
			{'other_service_information': r.other_service_information}
			for r in (doc.other_service_info or [])
		],
		'oci_customs': [
			{
				'country': r.country,
				'information_identifier': r.information_identifier,
				'customs_info_identifier': r.customs_info_identifier,
				'supplementary': r.supplementary,
			}
			for r in (doc.oci_customs or [])
		],
		'accounting_information': [
			{
				'identifier': r.identifier,
				'information': r.information,
			}
			for r in (doc.accounting_information or [])
		],
		'references': [
			{
				'reference_number': r.reference_number,
				'supplementary_1': r.supplementary_1,
				'supplementary_2': r.supplementary_2,
			}
			for r in (doc.references or [])
		],
		# Charge summary — display-only (server-computed; never submitted from FE)
		'charge_summary': [
			{
				'settlement': r.settlement,
				'charge_identifier': r.charge_identifier,
				'amount': r.amount,
			}
			for r in (doc.charge_summary or [])
		],
	}


@frappe.whitelist(allow_guest=False)
def save_shipment(data):
	if isinstance(data, str):
		data = json.loads(data)

	name = data.get('name')
	is_new = not name or name == 'new'

	if is_new:
		doc = frappe.new_doc('Shipment')
	else:
		doc = frappe.get_doc('Shipment', name)

	# Flat fields — assign all; server validate() is authoritative for uppercase/computed
	doc.airline_prefix = data.get('airline_prefix') or ''
	doc.awb_serial_number = data.get('awb_serial_number') or ''
	doc.origin = data.get('origin') or ''
	doc.destination = data.get('destination') or ''
	doc.e_awb = 1 if data.get('e_awb') else 0
	doc.console = 1 if data.get('console') else 0
	doc.number_of_pieces = data.get('number_of_pieces') or None
	doc.weight = data.get('weight') or None
	doc.weight_code = data.get('weight_code') or 'K'
	doc.volume_amount = data.get('volume_amount') or None
	doc.volume_weight_factor = data.get('volume_weight_factor') or 6000
	doc.volume_code = data.get('volume_code') or ''
	doc.currency = data.get('currency') or ''
	doc.iata_rate = data.get('iata_rate') or None
	doc.rate_class = data.get('rate_class') or ''
	doc.charge_code = data.get('charge_code') or ''
	doc.nature_of_goods = data.get('nature_of_goods') or ''
	doc.commodity_item_no = data.get('commodity_item_no') or ''
	doc.wt_val_prepaid_collect = data.get('wt_val_prepaid_collect') or ''
	doc.other_charges_prepaid_collect = data.get('other_charges_prepaid_collect') or ''
	doc.declared_value_carriage_type = data.get('declared_value_carriage_type') or ''
	doc.declared_value_carriage_amount = data.get('declared_value_carriage_amount') or None
	doc.declared_value_customs_type = data.get('declared_value_customs_type') or ''
	doc.declared_value_customs_amount = data.get('declared_value_customs_amount') or None
	doc.insurance_type = data.get('insurance_type') or ''
	doc.insurance_amount = data.get('insurance_amount') or None
	# Shipper
	doc.shipper_name = data.get('shipper_name') or ''
	doc.shipper_account = data.get('shipper_account') or ''
	doc.shipper_address = data.get('shipper_address') or ''
	doc.shipper_place = data.get('shipper_place') or ''
	doc.shipper_state = data.get('shipper_state') or ''
	doc.shipper_country = data.get('shipper_country') or ''
	doc.shipper_post_code = data.get('shipper_post_code') or ''
	# Consignee
	doc.consignee_name = data.get('consignee_name') or ''
	doc.consignee_account = data.get('consignee_account') or ''
	doc.consignee_address = data.get('consignee_address') or ''
	doc.consignee_place = data.get('consignee_place') or ''
	doc.consignee_state = data.get('consignee_state') or ''
	doc.consignee_country = data.get('consignee_country') or ''
	doc.consignee_post_code = data.get('consignee_post_code') or ''
	# Agent (link only; fetched fields are server-set)
	doc.agent = data.get('agent') or ''
	# Certification
	doc.shippers_certification_signature = data.get('shippers_certification_signature') or ''
	doc.issue_date = data.get('issue_date') or None
	doc.issue_place = data.get('issue_place') or ''
	doc.carrier_execution_signature = data.get('carrier_execution_signature') or ''
	doc.no_commission_indicator = 1 if data.get('no_commission_indicator') else 0
	doc.commission_amount = data.get('commission_amount') or None
	doc.commission_percentage = data.get('commission_percentage') or None
	doc.sales_incentive_amount = data.get('sales_incentive_amount') or None
	doc.sales_incentive_indicator = data.get('sales_incentive_indicator') or ''
	doc.agent_reference = data.get('agent_reference') or ''
	# Sender
	doc.sender_file_reference = data.get('sender_file_reference') or ''
	doc.sender_office_address = data.get('sender_office_address') or ''
	doc.sender_participant_id = data.get('sender_participant_id') or ''
	doc.sender_participant_code = data.get('sender_participant_code') or ''
	# CDC
	doc.cc_dest_currency = data.get('cc_dest_currency') or ''
	doc.rate_of_exchange = data.get('rate_of_exchange') or None
	doc.cc_charges_dest = data.get('cc_charges_dest') or None
	doc.charges_at_dest = data.get('charges_at_dest') or None
	doc.total_collect_charges = data.get('total_collect_charges') or None
	# Customs
	doc.customs_origin_code = data.get('customs_origin_code') or ''
	# Nominated handling
	doc.nominated_handling_name = data.get('nominated_handling_name') or ''
	doc.nominated_handling_place = data.get('nominated_handling_place') or ''
	# Internal
	doc.customer = data.get('customer') or ''
	doc.supplier = data.get('supplier') or ''

	# Child tables — clear and rebuild (never send charge_summary / shipment_fsu)
	doc.dimensions = []
	for r in data.get('dimensions', []):
		doc.append('dimensions', {
			'line_number': r.get('line_number') or None,
			'pieces': r.get('pieces') or 1,
			'length': r.get('length') or None,
			'width': r.get('width') or None,
			'height': r.get('height') or None,
			'dim_unit': r.get('dim_unit') or 'cm',
			'remarks': r.get('remarks') or '',
		})

	doc.also_notify = []
	for r in data.get('also_notify', []):
		if r.get('notify_name', '').strip():
			doc.append('also_notify', {
				'party': r.get('party') or '',
				'notify_name': r.get('notify_name') or '',
				'street_address': r.get('street_address') or '',
				'place': r.get('place') or '',
				'state_province': r.get('state_province') or '',
				'country': r.get('country') or '',
				'post_code': r.get('post_code') or '',
				'telephone': r.get('telephone') or '',
				'fax': r.get('fax') or '',
			})

	doc.other_participants = []
	for r in data.get('other_participants', []):
		doc.append('other_participants', {
			'participant_name': r.get('participant_name') or '',
			'office_file_reference': r.get('office_file_reference') or '',
			'participant_id': r.get('participant_id') or '',
			'participant_code': r.get('participant_code') or '',
			'airport': r.get('airport') or '',
		})

	doc.flight_bookings = []
	for r in data.get('flight_bookings', []):
		if r.get('carrier'):
			doc.append('flight_bookings', {
				'carrier': r.get('carrier') or '',
				'flight_number': r.get('flight_number') or '',
				'flight_day': r.get('flight_day') or '',
				'flight_month': r.get('flight_month') or '',
				'departure_airport': r.get('departure_airport') or '',
				'arrival_airport': r.get('arrival_airport') or '',
				'space_allocation_code': r.get('space_allocation_code') or '',
				'allotment_id': r.get('allotment_id') or '',
			})

	doc.routing = []
	for r in data.get('routing', []):
		doc.append('routing', {
			'sequence': r.get('sequence') or None,
			'airport': r.get('airport') or '',
			'carrier': r.get('carrier') or '',
		})

	doc.rate_lines = []
	for r in data.get('rate_lines', []):
		doc.append('rate_lines', {
			'line_number': r.get('line_number') or None,
			'number_of_pieces': r.get('number_of_pieces') or None,
			'rate_class_code': r.get('rate_class_code') or '',
			'gross_weight': r.get('gross_weight') or None,
			'gross_weight_code': r.get('gross_weight_code') or 'K',
			'chargeable_weight': r.get('chargeable_weight') or None,
			'rate_charge': r.get('rate_charge') or None,
			'total': r.get('total') or None,
			'goods_data_identifier': r.get('goods_data_identifier') or '',
			'description': r.get('description') or '',
			'rate_combination_point': r.get('rate_combination_point') or '',
			'commodity_item_number': r.get('commodity_item_number') or '',
			'uld_rate_class_type': r.get('uld_rate_class_type') or '',
			'rate_class_percentage': r.get('rate_class_percentage') or None,
		})

	doc.goods_details = []
	for r in data.get('goods_details', []):
		doc.append('goods_details', {
			'rate_line_number': r.get('rate_line_number') or None,
			'goods_data_identifier': r.get('goods_data_identifier') or '',
			'description': r.get('description') or '',
			'hs_code': r.get('hs_code') or '',
			'country_of_origin': r.get('country_of_origin') or '',
			'slac': r.get('slac') or None,
			'volume_code': r.get('volume_code') or '',
			'volume_amount': r.get('volume_amount') or None,
			'uld_type': r.get('uld_type') or '',
			'uld_serial': r.get('uld_serial') or '',
			'uld_owner': r.get('uld_owner') or '',
			'measurement_unit': r.get('measurement_unit') or '',
			'dim_weight_code': r.get('dim_weight_code') or '',
			'dim_weight': r.get('dim_weight') or None,
			'dim_length': r.get('dim_length') or None,
			'dim_width': r.get('dim_width') or None,
			'dim_height': r.get('dim_height') or None,
			'dim_pieces': r.get('dim_pieces') or None,
			'service_code': r.get('service_code') or '',
		})

	doc.other_charges = []
	for r in data.get('other_charges', []):
		if r.get('other_charge_code'):
			doc.append('other_charges', {
				'prepaid_collect': r.get('prepaid_collect') or 'P',
				'other_charge_code': r.get('other_charge_code') or '',
				'amount': r.get('amount') or None,
			})

	doc.special_service_requests = []
	for r in data.get('special_service_requests', []):
		if r.get('special_service_request', '').strip():
			doc.append('special_service_requests', {
				'special_service_request': r.get('special_service_request') or '',
			})

	doc.special_handling = []
	for r in data.get('special_handling', []):
		if r.get('special_handling_code'):
			doc.append('special_handling', {
				'special_handling_code': r.get('special_handling_code') or '',
			})

	doc.other_service_info = []
	for r in data.get('other_service_info', []):
		if r.get('other_service_information', '').strip():
			doc.append('other_service_info', {
				'other_service_information': r.get('other_service_information') or '',
			})

	doc.oci_customs = []
	for r in data.get('oci_customs', []):
		doc.append('oci_customs', {
			'country': r.get('country') or '',
			'information_identifier': r.get('information_identifier') or '',
			'customs_info_identifier': r.get('customs_info_identifier') or '',
			'supplementary': r.get('supplementary') or '',
		})

	doc.accounting_information = []
	for r in data.get('accounting_information', []):
		if r.get('identifier'):
			doc.append('accounting_information', {
				'identifier': r.get('identifier') or '',
				'information': r.get('information') or '',
			})

	doc.references = []
	for r in data.get('references', []):
		doc.append('references', {
			'reference_number': r.get('reference_number') or '',
			'supplementary_1': r.get('supplementary_1') or '',
			'supplementary_2': r.get('supplementary_2') or '',
		})

	# Let validate() throw naturally — parseErr() on the FE surfaces the message
	doc.save()
	frappe.db.commit()

	return {
		'name': doc.name,
		'awb_number': doc.awb_number,
		'modified': doc.modified,
	}


@frappe.whitelist(allow_guest=False)
def delete_shipment(name):
	frappe.delete_doc('Shipment', name)
	frappe.db.commit()
	return {'deleted': name}


@frappe.whitelist(allow_guest=False)
def search_link(doctype, txt=None, page_length=20, filters=None):
	_ALLOWED = {
		'Airport', 'Airline', 'Party', 'Currency', 'Country',
		'Charge Code', 'Rate Class Code', 'Volume Code', 'ULD Type',
		'Measurement Unit Code', 'Service Code', 'Special Handling Code',
		'Other Charge Code', 'OCI Information Identifier',
		'Customs Information Identifier', 'Accounting Information Identifier',
		'Participant Identifier',
	}
	if doctype not in _ALLOWED:
		frappe.throw(_(f'Search not allowed for doctype: {doctype}'))

	page_length = min(int(page_length or 20), 50)
	txt = (txt or '').strip()

	meta = frappe.get_meta(doctype)
	title_field = meta.title_field or 'name'

	or_filters = [['name', 'like', f'%{txt}%']]
	if title_field != 'name':
		or_filters.append([title_field, 'like', f'%{txt}%'])

	extra_filters = []
	if filters:
		if isinstance(filters, str):
			filters = json.loads(filters)
		if isinstance(filters, dict):
			extra_filters = [[k, '=', v] for k, v in filters.items()]

	fields = ['name']
	if title_field != 'name':
		fields.append(title_field)

	rows = frappe.get_all(
		doctype,
		filters=extra_filters,
		or_filters=or_filters,
		fields=fields,
		order_by='name asc',
		limit_page_length=page_length,
	)

	return [
		{
			'value': r['name'],
			'label': r.get(title_field) or r['name'],
		}
		for r in rows
	]
