# Copyright (c) 2026, Shofiq and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


def _get_master_shipment():
	"""Return a valid draft Shipment to use as test master, creating one if needed."""
	existing = frappe.db.get_value("Shipment", {"docstatus": 0}, "name")
	if existing:
		return frappe.get_doc("Shipment", existing)

	airline = frappe.db.get_value("Airline", {}, "name")
	airports = frappe.db.get_all("Airport", fields=["name"], limit=2)
	currency = frappe.db.get_value("Currency", {}, "name") or "USD"
	if not airline or len(airports) < 2:
		frappe.throw("HWB tests require at least 1 Airline and 2 Airport fixtures.")

	doc = frappe.new_doc("Shipment")
	doc.airline_prefix = airline
	# 0000000 % 7 = 0 → last digit 0 → valid serial per IATA CSC Resolution 600a
	doc.awb_serial_number = "00000000"
	doc.origin = airports[0].name
	doc.destination = airports[1].name
	doc.currency = currency
	doc.insert(ignore_permissions=True)
	return doc


def _get_second_master():
	"""Return a second distinct master Shipment for cross-master uniqueness tests."""
	airline = frappe.db.get_value("Airline", {}, "name")
	airports = frappe.db.get_all("Airport", fields=["name"], limit=2)
	currency = frappe.db.get_value("Currency", {}, "name") or "USD"
	if not airline or len(airports) < 2:
		frappe.throw("HWB tests require at least 1 Airline and 2 Airport fixtures.")

	# Use serial 00000010 → 0000001 % 7 = 1 → last digit 1 → valid
	existing = frappe.db.get_value(
		"Shipment", {"awb_serial_number": "00000011"}, "name"
	)
	if existing:
		return frappe.get_doc("Shipment", existing)

	doc = frappe.new_doc("Shipment")
	doc.airline_prefix = airline
	doc.awb_serial_number = "00000011"
	doc.origin = airports[0].name
	doc.destination = airports[1].name
	doc.currency = currency
	doc.insert(ignore_permissions=True)
	return doc


class TestHouseAirwayBill(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.master = _get_master_shipment()
		cls.origin = cls.master.origin
		cls.destination = cls.master.destination

	def _make_hwb(self, **overrides):
		defaults = {
			"master_shipment": self.master.name,
			"hwb_serial_number": "TEST000001",
			"hwb_origin": self.origin,
			"hwb_destination": self.destination,
			"number_of_pieces": 2,
			"weight_code": "K",
			"weight": 64.0,
			"manifest_description": "PARTS",
			"currency": self.master.currency,
		}
		defaults.update(overrides)
		doc = frappe.new_doc("House Airway Bill")
		for k, v in defaults.items():
			setattr(doc, k, v)
		return doc

	def _cleanup(self, *names):
		for name in names:
			if name and frappe.db.exists("House Airway Bill", name):
				frappe.delete_doc("House Airway Bill", name, force=True, ignore_permissions=True)

	# ---- Phase 2: core HBS -----------------------------------------------

	def test_valid_insert_and_hwb_number(self):
		doc = self._make_hwb(hwb_serial_number="VALID0001")
		doc.insert(ignore_permissions=True)
		self.assertIn("VALID0001", doc.hwb_number)
		self._cleanup(doc.name)

	def test_serial_blank_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self._make_hwb(hwb_serial_number="").insert()

	def test_serial_too_long_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self._make_hwb(hwb_serial_number="A" * 13).insert()

	def test_serial_special_chars_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self._make_hwb(hwb_serial_number="ABC-123!").insert()

	def test_serial_12_chars_accepted(self):
		doc = self._make_hwb(hwb_serial_number="A" * 12)
		doc.insert(ignore_permissions=True)
		self._cleanup(doc.name)

	def test_same_origin_destination_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self._make_hwb(hwb_destination=self.origin).insert()

	def test_zero_pieces_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self._make_hwb(number_of_pieces=0).insert()

	def test_negative_pieces_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self._make_hwb(number_of_pieces=-1).insert()

	def test_zero_weight_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self._make_hwb(weight=0).insert()

	def test_duplicate_serial_same_master_rejected(self):
		doc1 = self._make_hwb(hwb_serial_number="DUPTEST01")
		doc1.insert(ignore_permissions=True)
		try:
			with self.assertRaises(frappe.ValidationError):
				self._make_hwb(hwb_serial_number="DUPTEST01").insert()
		finally:
			self._cleanup(doc1.name)

	def test_same_serial_different_masters_allowed(self):
		master2 = _get_second_master()
		doc1 = self._make_hwb(hwb_serial_number="CROSSSER1")
		doc1.insert(ignore_permissions=True)
		doc2 = self._make_hwb(
			master_shipment=master2.name,
			hwb_serial_number="CROSSSER1",
			hwb_origin=master2.origin,
			hwb_destination=master2.destination,
		)
		doc2.insert(ignore_permissions=True)
		self._cleanup(doc1.name, doc2.name)

	# ---- Phase 3: goods children -----------------------------------------

	def test_sph_over_9_rows_rejected(self):
		shc = frappe.db.get_value("Special Handling Code", {}, "name")
		if not shc:
			self.skipTest("No Special Handling Code fixtures available")
		doc = self._make_hwb(hwb_serial_number="SPHTEST01")
		for _ in range(10):
			doc.append("special_handling", {"special_handling_code": shc})
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_txt_over_9_rows_rejected(self):
		doc = self._make_hwb(hwb_serial_number="TXTTEST01")
		for i in range(10):
			doc.append("free_text", {"free_text": f"Line {i}"})
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_hts_over_9_rows_rejected(self):
		doc = self._make_hwb(hwb_serial_number="HTSTEST01")
		for _ in range(10):
			doc.append("hs_codes", {"hs_code": "880529"})
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_hs_code_too_short_rejected(self):
		doc = self._make_hwb(hwb_serial_number="HTSLEN001")
		doc.append("hs_codes", {"hs_code": "12345"})  # only 5 chars
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_hs_code_19_chars_rejected(self):
		doc = self._make_hwb(hwb_serial_number="HTSLEN002")
		doc.append("hs_codes", {"hs_code": "1" * 19})
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_hs_code_6_chars_accepted(self):
		doc = self._make_hwb(hwb_serial_number="HTSLEN003")
		doc.append("hs_codes", {"hs_code": "880529"})
		doc.insert(ignore_permissions=True)
		self._cleanup(doc.name)

	def test_hs_code_18_chars_accepted(self):
		doc = self._make_hwb(hwb_serial_number="HTSLEN004")
		doc.append("hs_codes", {"hs_code": "1" * 18})
		doc.insert(ignore_permissions=True)
		self._cleanup(doc.name)

	# ---- Phase 4: parties ------------------------------------------------

	def test_shipper_without_consignee_rejected(self):
		party = frappe.db.get_value("Party", {}, "name")
		if not party:
			self.skipTest("No Party fixtures available")
		with self.assertRaises(frappe.ValidationError):
			self._make_hwb(hwb_serial_number="SHPONLY01", shipper=party).insert()

	def test_consignee_without_shipper_rejected(self):
		party = frappe.db.get_value("Party", {}, "name")
		if not party:
			self.skipTest("No Party fixtures available")
		with self.assertRaises(frappe.ValidationError):
			self._make_hwb(hwb_serial_number="CNEONLY01", consignee=party).insert()

	def test_invalid_shipper_contact_id_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self._make_hwb(
				hwb_serial_number="CIDTEST01",
				shipper_contact_id="XX",  # invalid — only FX/TE/TL allowed
				shipper_contact_number="12345678",
			).insert()

	def test_valid_shipper_contact_id_accepted(self):
		doc = self._make_hwb(
			hwb_serial_number="CIDTEST02",
			shipper_contact_id="TE",
			shipper_contact_number="5148446311",
		)
		doc.insert(ignore_permissions=True)
		self._cleanup(doc.name)

	def test_contact_number_without_id_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self._make_hwb(
				hwb_serial_number="CIDTEST03",
				shipper_contact_number="5148446311",
			).insert()

	# ---- Phase 5: OCI + CVD ----------------------------------------------

	def test_oci_empty_row_rejected(self):
		doc = self._make_hwb(hwb_serial_number="OCITEST01")
		doc.append("oci_customs", {
			"country": None,
			"information_identifier": None,
			"customs_info_identifier": None,
			"supplementary": None,
		})
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_oci_country_only_accepted(self):
		doc = self._make_hwb(hwb_serial_number="OCITEST02")
		doc.append("oci_customs", {"country": "Netherlands", "supplementary": "TEST"})
		doc.insert(ignore_permissions=True)
		self._cleanup(doc.name)

	def test_oci_duplicate_ss_rejected(self):
		cid = frappe.db.get_value("Customs Information Identifier", {"name": "SS"}, "name")
		if not cid:
			self.skipTest("No 'SS' Customs Information Identifier fixture available")
		doc = self._make_hwb(hwb_serial_number="SSTEST001")
		for _ in range(2):
			doc.append("oci_customs", {
				"customs_info_identifier": "SS",
				"supplementary": "SPX",
			})
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_cvd_nvd_with_amount_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self._make_hwb(
				hwb_serial_number="CVDTEST01",
				declared_value_carriage_type="NVD",
				declared_value_carriage_amount=100.0,
			).insert()

	def test_cvd_value_without_amount_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self._make_hwb(
				hwb_serial_number="CVDTEST02",
				declared_value_carriage_type="Value",
				declared_value_carriage_amount=0.0,
			).insert()

	def test_cvd_value_with_amount_accepted(self):
		doc = self._make_hwb(
			hwb_serial_number="CVDTEST03",
			declared_value_carriage_type="Value",
			declared_value_carriage_amount=500.0,
		)
		doc.insert(ignore_permissions=True)
		self._cleanup(doc.name)

	def test_cvd_ncv_with_amount_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self._make_hwb(
				hwb_serial_number="CVDTEST04",
				declared_value_customs_type="NCV",
				declared_value_customs_amount=200.0,
			).insert()

	def test_cvd_xxx_with_amount_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self._make_hwb(
				hwb_serial_number="CVDTEST05",
				insurance_type="XXX",
				insurance_amount=50.0,
			).insert()

	def test_currency_required(self):
		with self.assertRaises(frappe.ValidationError):
			self._make_hwb(hwb_serial_number="CURTEST01", currency=None).insert()

	# ---- Lifecycle -------------------------------------------------------

	def test_submit_and_amend_cycle(self):
		doc = self._make_hwb(hwb_serial_number="LIFECYCLE1")
		doc.insert(ignore_permissions=True)
		doc.submit()
		amended = doc.copy()
		amended.hwb_serial_number = "LIFECYCLE2"
		amended.amended_from = doc.name
		amended.docstatus = 0
		amended.insert(ignore_permissions=True)
		self.assertEqual(amended.amended_from, doc.name)
		self._cleanup(amended.name)
		# cancel original
		doc.cancel()
		self._cleanup(doc.name)
