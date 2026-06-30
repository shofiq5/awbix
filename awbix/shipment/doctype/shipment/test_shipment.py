# Copyright (c) 2026, Shofiq and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


def _valid_serial(first_seven="1234560"):
	"""Return an 8-digit AWB serial with a valid mod-7 check digit."""
	check = int(first_seven) % 7
	return f"{first_seven}{check}"


def _make_shipment(**kwargs):
	doc = frappe.new_doc("Shipment")
	doc.airline_prefix = kwargs.get("airline_prefix", "020")
	doc.awb_serial_number = kwargs.get("awb_serial_number", _valid_serial())
	doc.origin = kwargs.get("origin", "DXB")
	doc.destination = kwargs.get("destination", "JFK")
	doc.weight = kwargs.get("weight", 100.0)
	doc.weight_code = kwargs.get("weight_code", "K")
	doc.currency = kwargs.get("currency", "USD")
	for k, v in kwargs.items():
		if k not in ("airline_prefix", "awb_serial_number", "origin", "destination", "weight", "weight_code", "currency"):
			setattr(doc, k, v)
	return doc


class TestShipment(FrappeTestCase):

	# ── 1. Happy-path round-trip ────────────────────────────────────────────
	def test_full_round_trip(self):
		"""awb_number, flat fields, and child table rows all persist correctly."""
		doc = _make_shipment(
			airline_prefix="125",
			awb_serial_number=_valid_serial("1234567"),
			shipper_name="Test Shipper",
		)
		doc.append("also_notify", {
			"notify_name": "Notify Co",
			"street_address": "123 Street",
			"place": "Dubai",
		})
		doc.append("other_participants", {
			"participant_name": "Handler",
			"participant_id": "ABC",
		})
		doc.append("other_service_info", {
			"other_service_information": "Handle with care",
		})
		doc.insert()
		self.addCleanup(doc.delete)

		expected_serial = _valid_serial("1234567")
		self.assertEqual(doc.awb_number, f"125-{expected_serial}")
		self.assertEqual(doc.shipper_name, "TEST SHIPPER")  # uppercase-enforced

		# Reload from DB and verify child rows
		loaded = frappe.get_doc("Shipment", doc.name)
		self.assertEqual(len(loaded.also_notify), 1)
		self.assertEqual(loaded.also_notify[0].notify_name, "NOTIFY CO")
		self.assertEqual(len(loaded.other_participants), 1)
		self.assertEqual(loaded.other_participants[0].participant_name, "HANDLER")
		self.assertEqual(len(loaded.other_service_info), 1)
		self.assertEqual(loaded.other_service_info[0].other_service_information, "Handle with care")

	# ── 2. Bad check digit → ValidationError ───────────────────────────────
	def test_bad_check_digit_raises(self):
		"""A serial whose 8th digit does not match mod-7 must raise ValidationError."""
		# Build a serial with a deliberately wrong check digit
		first_seven = "1234567"
		correct_check = int(first_seven) % 7
		wrong_check = (correct_check + 1) % 7
		bad_serial = f"{first_seven}{wrong_check}"

		doc = _make_shipment(awb_serial_number=bad_serial)
		with self.assertRaises(frappe.exceptions.ValidationError):
			doc.insert()

	# ── 3. Origin == destination → ValidationError ─────────────────────────
	def test_origin_equals_destination_raises(self):
		doc = _make_shipment(origin="DXB", destination="DXB")
		with self.assertRaises(frappe.exceptions.ValidationError):
			doc.insert()

	# ── 4. charge_summary in payload is ignored; server recomputes it ──────
	def test_charge_summary_ignored_on_save(self):
		"""
		Even if a client somehow sends charge_summary, the saved doc's
		charge_summary must reflect populate_charge_summary(), not the payload.
		"""
		from awbix.frontend_api import save_shipment

		serial = _valid_serial("9876543")
		payload = {
			"airline_prefix": "020",
			"awb_serial_number": serial,
			"origin": "DXB",
			"destination": "JFK",
			"weight": 50.0,
			"weight_code": "K",
			"currency": "USD",
			"wt_val_prepaid_collect": "P",
			"rate_lines": [{
				"line_number": 1,
				"number_of_pieces": 1,
				"gross_weight": 50.0,
				"gross_weight_code": "K",
				"chargeable_weight": 50.0,
				"rate_charge": 2.0,
				"total": 100.0,
				"goods_data_identifier": "G",
				"description": "GOODS",
			}],
			# Client tries to inject a bogus charge_summary row
			"charge_summary": [{"settlement": "BOGUS", "charge_identifier": "XX", "amount": 9999}],
		}
		result = save_shipment(payload)
		name = result["name"]
		self.addCleanup(lambda: frappe.delete_doc("Shipment", name))

		doc = frappe.get_doc("Shipment", name)
		settlements = {r.settlement for r in doc.charge_summary}
		self.assertNotIn("BOGUS", settlements)
		# populate_charge_summary should have produced real rows
		identifiers = {r.charge_identifier for r in doc.charge_summary}
		self.assertIn("WT", identifiers)

	# ── 5. dimensions rows persist and volume_weight recomputes correctly ───
	def test_dimension_round_trip_and_recompute(self):
		"""
		Dimension rows must survive save/reload, and volume_weight must match
		what calculate_dimension_totals() returns for the same input.
		"""
		from awbix.shipment.doctype.shipment.shipment import calculate_dimension_totals

		doc = _make_shipment(weight=10.0, volume_weight_factor=6000)
		doc.append("dimensions", {
			"line_number": 1,
			"pieces": 1,
			"length": 100.0,
			"width": 40.0,
			"height": 30.0,
			"dim_unit": "cm",
		})
		doc.insert()
		self.addCleanup(doc.delete)

		# compare with the preview endpoint
		preview = calculate_dimension_totals(
			rows=[{"pieces": 1, "length": 100.0, "width": 40.0, "height": 30.0, "dim_unit": "cm"}],
			weight=10.0,
			volume_weight_factor=6000,
		)

		doc.reload()
		self.assertEqual(len(doc.dimensions), 1)
		self.assertAlmostEqual(doc.volume_weight, preview["volume_weight"], places=2)
		self.assertAlmostEqual(doc.chargeable_weight, preview["chargeable_weight"], places=2)

	# ── 6. get_shipment returns dimension rows ──────────────────────────────
	def test_get_shipment_returns_dimension_rows(self):
		from awbix.frontend_api import get_shipment

		doc = _make_shipment(weight=5.0)
		doc.append("dimensions", {
			"line_number": 1,
			"pieces": 2,
			"length": 50.0,
			"width": 30.0,
			"height": 20.0,
			"dim_unit": "cm",
		})
		doc.insert()
		self.addCleanup(doc.delete)

		data = get_shipment(doc.name)
		self.assertIn("dimensions", data)
		self.assertEqual(len(data["dimensions"]), 1)
		row = data["dimensions"][0]
		# Only raw fields — not server-computed volume/volume_weight
		self.assertIn("pieces", row)
		self.assertNotIn("volume", row)
		self.assertNotIn("volume_weight", row)

	# ── 7. Corrected child-table fieldnames round-trip non-empty values ─────
	def test_corrected_fieldnames_round_trip(self):
		"""
		Guards against silent key-drop by doc.append() for the three fieldnames
		that are easily confused: notify_name, participant_name,
		other_service_information.
		"""
		doc = _make_shipment()
		doc.append("also_notify", {"notify_name": "Alert Party"})
		doc.append("other_participants", {"participant_name": "Ground Handler"})
		doc.append("other_service_info", {"other_service_information": "Fragile"})
		doc.insert()
		self.addCleanup(doc.delete)

		loaded = frappe.get_doc("Shipment", doc.name)
		self.assertTrue(loaded.also_notify[0].notify_name)
		self.assertTrue(loaded.other_participants[0].participant_name)
		self.assertTrue(loaded.other_service_info[0].other_service_information)

	# ── 8. search_link allows/blocks doctypes correctly ────────────────────
	def test_search_link_allowed_doctype(self):
		from awbix.frontend_api import search_link

		# An allowed doctype should return a list (may be empty in test DB)
		result = search_link("Airport", txt="")
		self.assertIsInstance(result, list)

	def test_search_link_blocked_doctype(self):
		from awbix.frontend_api import search_link

		with self.assertRaises(frappe.exceptions.ValidationError):
			search_link("User", txt="")
