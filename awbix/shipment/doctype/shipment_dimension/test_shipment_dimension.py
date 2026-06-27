import json

import frappe
from frappe.tests.utils import FrappeTestCase

from awbix.shipment.doctype.shipment.shipment import (
	_row_volume_cm3,
	calculate_dimension_totals,
)

# ---------------------------------------------------------------------------
# Helper to make a minimal dict-like namespace for _row_volume_cm3
# ---------------------------------------------------------------------------

class _Row(dict):
	def __getattr__(self, k):
		return self.get(k)


def _make_row(length, width, height, pieces=1, dim_unit="cm"):
	return _Row(length=length, width=width, height=height, pieces=pieces, dim_unit=dim_unit)


class TestShipmentDimensionCalc(FrappeTestCase):
	# ------------------------------------------------------------------
	# _row_volume_cm3
	# ------------------------------------------------------------------

	def test_basic_cm(self):
		"""100×40×30 cm, 1 pc → 120 000 cm³"""
		self.assertAlmostEqual(_row_volume_cm3(_make_row(100, 40, 30)), 120_000)

	def test_pieces_multiplier(self):
		"""3 pieces → 360 000 cm³"""
		self.assertAlmostEqual(_row_volume_cm3(_make_row(100, 40, 30, pieces=3)), 360_000)

	def test_unit_inches(self):
		"""Same dims in inches should equal the cm result (2.54 conversion)."""
		cm_vol = _row_volume_cm3(_make_row(100, 40, 30))
		in_vol = _row_volume_cm3(_make_row(100 / 2.54, 40 / 2.54, 30 / 2.54, dim_unit="in"))
		self.assertAlmostEqual(cm_vol, in_vol, places=2)

	def test_unit_metres(self):
		"""1×0.4×0.3 m = same 120 000 cm³."""
		self.assertAlmostEqual(_row_volume_cm3(_make_row(1, 0.4, 0.3, dim_unit="m")), 120_000)

	def test_zero_dimension_returns_zero(self):
		self.assertEqual(_row_volume_cm3(_make_row(0, 40, 30)), 0)

	# ------------------------------------------------------------------
	# calculate_dimension_totals (endpoint parity)
	# ------------------------------------------------------------------

	def test_single_row_totals(self):
		rows = [{"pieces": 1, "length": 100, "width": 40, "height": 30, "dim_unit": "cm"}]
		result = calculate_dimension_totals(json.dumps(rows), weight=10, volume_weight_factor=6000)
		self.assertAlmostEqual(result["total_volume_m3"], 0.12, places=4)
		self.assertAlmostEqual(result["volume_weight"], 20.0, places=2)
		# chargeable = max(10, 20) = 20
		self.assertAlmostEqual(result["chargeable_weight"], 20.0, places=2)

	def test_chargeable_weight_governed_by_actual_weight(self):
		rows = [{"pieces": 1, "length": 10, "width": 10, "height": 10, "dim_unit": "cm"}]
		# vol_cm3=1000, vw=1000/6000≈0.17, weight=50 → chargeable=50
		result = calculate_dimension_totals(json.dumps(rows), weight=50)
		self.assertAlmostEqual(result["chargeable_weight"], 50.0, places=2)

	def test_multiple_rows_sum(self):
		rows = [
			{"pieces": 2, "length": 100, "width": 40, "height": 30, "dim_unit": "cm"},
			{"pieces": 1, "length": 50, "width": 50, "height": 50, "dim_unit": "cm"},
		]
		# row1: 120000*2=240000; row2: 125000; total=365000
		result = calculate_dimension_totals(json.dumps(rows), volume_weight_factor=6000)
		self.assertAlmostEqual(result["total_volume_m3"], 365_000 / 1_000_000, places=4)
		self.assertAlmostEqual(result["volume_weight"], round(365_000 / 6000, 2), places=2)

	def test_custom_factor(self):
		rows = [{"pieces": 1, "length": 100, "width": 40, "height": 30, "dim_unit": "cm"}]
		result = calculate_dimension_totals(json.dumps(rows), volume_weight_factor=5000)
		self.assertAlmostEqual(result["volume_weight"], round(120_000 / 5000, 2), places=2)

	def test_factor_zero_defaults_to_6000(self):
		rows = [{"pieces": 1, "length": 100, "width": 40, "height": 30, "dim_unit": "cm"}]
		result_zero = calculate_dimension_totals(json.dumps(rows), volume_weight_factor=0)
		result_6000 = calculate_dimension_totals(json.dumps(rows), volume_weight_factor=6000)
		self.assertAlmostEqual(result_zero["volume_weight"], result_6000["volume_weight"], places=4)

	def test_suggested_volume_amount_when_blank(self):
		rows = [{"pieces": 1, "length": 100, "width": 40, "height": 30, "dim_unit": "cm"}]
		result = calculate_dimension_totals(json.dumps(rows), volume_amount=0)
		self.assertIsNotNone(result["suggested_volume_amount"])
		self.assertAlmostEqual(result["suggested_volume_amount"], 0.12, places=4)

	def test_suggested_volume_amount_not_overwritten_when_higher(self):
		rows = [{"pieces": 1, "length": 100, "width": 40, "height": 30, "dim_unit": "cm"}]
		# existing volume_amount (0.5) > calculated (0.12) → no suggestion
		result = calculate_dimension_totals(json.dumps(rows), volume_amount=0.5)
		self.assertIsNone(result["suggested_volume_amount"])

	def test_row_per_results_returned(self):
		rows = [{"pieces": 1, "length": 100, "width": 40, "height": 30, "dim_unit": "cm"}]
		result = calculate_dimension_totals(json.dumps(rows))
		self.assertEqual(len(result["rows"]), 1)
		self.assertAlmostEqual(result["rows"][0]["volume"], 0.12, places=4)
		self.assertAlmostEqual(result["rows"][0]["volume_weight"], 20.0, places=2)

	# ------------------------------------------------------------------
	# CSV parse helper (unit test without file system)
	# ------------------------------------------------------------------

	def test_map_rows_basic(self):
		from awbix.shipment.doctype.shipment.shipment import _map_rows

		raw = [
			["pieces", "length", "width", "height", "unit"],
			["2", "100", "40", "30", "cm"],
		]
		out = _map_rows(raw)
		self.assertEqual(len(out["rows"]), 1)
		self.assertEqual(out["rows"][0]["pieces"], 2)
		self.assertEqual(out["rows"][0]["dim_unit"], "cm")
		self.assertEqual(out["errors"], [])

	def test_map_rows_aliases(self):
		from awbix.shipment.doctype.shipment.shipment import _map_rows

		raw = [
			["qty", "l", "w", "h", "unit"],
			["3", "50", "20", "10", "in"],
		]
		out = _map_rows(raw)
		self.assertEqual(out["rows"][0]["pieces"], 3)
		self.assertEqual(out["rows"][0]["length"], 50)
		self.assertEqual(out["rows"][0]["dim_unit"], "in")

	def test_map_rows_bad_value_produces_error(self):
		from awbix.shipment.doctype.shipment.shipment import _map_rows

		raw = [
			["pieces", "length", "width", "height", "unit"],
			["abc", "notanumber", "40", "30", "cm"],
		]
		out = _map_rows(raw)
		self.assertEqual(len(out["errors"]), 1)
		self.assertIn("Length", out["errors"][0]["message"])
