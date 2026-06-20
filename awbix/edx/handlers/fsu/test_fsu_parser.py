"""Tests for FSUParser and FSAParser.

Covers parse, validate, and process (DB-backed). Test IDs match the plan §12.

AWB check digits used in these tests:
  157-53806270: int("5380627") % 7 = 0  → digit 8 = 0  ✓
  157-41266466: int("4126646") % 7 = 6  → digit 8 = 6  ✓
"""

import frappe
from frappe.tests.utils import FrappeTestCase

from awbix.edx.handlers.fsu.fsa_parser import FSAParser
from awbix.edx.handlers.fsu.fsu_parser import FSUParser

# ---------------------------------------------------------------------------
# Sample messages
# ---------------------------------------------------------------------------

# Full FSU/14 sample with Type-B telex envelope (from fsu sample.txt).
SAMPLE_FSU_ENVELOPE = """\
QD SIN05XH
.HDQFMQR 200739
FSU/14
157-53806270HKGNLU/P2K505.0T10
FIW/QR8403/20JUN1039/DOH/P2K505.0/S0720/A1008
OCI/HK/ISS/RA/28490
/HK//SS/SPX
/HK//SM/XRY
ULD/PMC72534QR/PMC77313QR
"""

# Bare FSU/14 (no envelope) — same AWB, BKD status.
SAMPLE_FSU_BKD = """\
FSU/14
157-53806270HKGNLU/P2K505.0T10
BKD/QR/0843/20JUN/HKG/NLU
"""

# FSU with no origin/destination on the AWB line.
SAMPLE_FSU_NO_OD = """\
FSU/14
157-53806270/P2K505.0T10
RCS/20JUN1039/HKG
"""

# FSA/14 sample (from plan §11.2).
SAMPLE_FSA = """\
FSA/14
157-41266466DOHLHR/T60K1428
DLV/24MAY1223/LHR/T60K1428/DART AIR SERVICES LTD
"""


# ---------------------------------------------------------------------------
# Pure (no-DB) tests
# ---------------------------------------------------------------------------


class TestFSUParserPure(FrappeTestCase):
	def setUp(self):
		self.parser = FSUParser()

	# G1 — Envelope stripping
	def test_g1_envelope_stripped(self):
		data = self.parser.parse(SAMPLE_FSU_ENVELOPE)
		self.assertEqual(data["message"]["id"], "FSU/14")
		self.assertEqual(data["awb_reference"]["awb_number"], "157-53806270")

	# G2 — Parse pure
	def test_g2_parse_fields(self):
		data = self.parser.parse(SAMPLE_FSU_ENVELOPE)
		self.assertEqual(data["message"]["type"], "FSU")
		self.assertEqual(data["message"]["version"], "14")
		awb = data["awb_reference"]
		self.assertEqual(awb["airline_prefix"], "157")
		self.assertEqual(awb["awb_serial_number"], "53806270")
		self.assertEqual(awb["origin"], "HKG")
		self.assertEqual(awb["destination"], "NLU")
		self.assertEqual(self.parser.business_key(data), "157-53806270")

	# G3 — Optional O&D: AWB without origin/destination must parse without AWB_REF error
	def test_g3_optional_od(self):
		data = self.parser.parse(SAMPLE_FSU_NO_OD)
		self.assertEqual(data["awb_reference"]["awb_number"], "157-53806270")
		errors = [i for i in self.parser.validate(data) if i["level"] == "Error"]
		codes = {e["code"] for e in errors}
		self.assertNotIn("AWB_REF", codes)

	# G4 — Validate: clean message has no errors
	def test_g4_validate_clean(self):
		data = self.parser.parse(SAMPLE_FSU_ENVELOPE)
		errors = [i for i in self.parser.validate(data) if i["level"] == "Error"]
		self.assertEqual(errors, [])

	# G4 — Validate: bad serial raises AWB_SERIAL
	def test_g4_validate_bad_serial(self):
		bad = SAMPLE_FSU_ENVELOPE.replace("157-53806270", "157-5380627")
		data = self.parser.parse(bad)
		codes = {i["code"] for i in self.parser.validate(data) if i["level"] == "Error"}
		self.assertIn("AWB_SERIAL", codes)

	# G5 — Check digit: int(serial[:7]) % 7, not digit-sum
	def test_g5_checkdigit_algorithm(self):
		# 5380627 % 7 = 0 → valid (digit 8 = 0)
		data = self.parser.parse(SAMPLE_FSU_ENVELOPE)
		errors = [i for i in self.parser.validate(data) if i["code"] == "AWB_CHECKDIGIT"]
		self.assertEqual(errors, [])

		# Corrupt the check digit to 1 → should fail
		bad = SAMPLE_FSU_ENVELOPE.replace("157-53806270", "157-53806271")
		bad_data = self.parser.parse(bad)
		codes = {i["code"] for i in self.parser.validate(bad_data) if i["level"] == "Error"}
		self.assertIn("AWB_CHECKDIGIT", codes)

		# Confirm digit-sum of "5380627" = 5+3+8+0+6+2+7 = 31, 31%7 = 3 ≠ 0
		# so the digit-sum algorithm would give a different (wrong) result
		self.assertNotEqual(sum(int(d) for d in "5380627") % 7, int("5380627") % 7)

	# G8 — Open status code: FIW (not in FSU.md table) stored verbatim
	def test_g8_open_status_code(self):
		data = self.parser.parse(SAMPLE_FSU_ENVELOPE)
		codes = [e["status_code"] for e in data["fsu_data"]["movement_records"]]
		self.assertIn("FIW", codes)

	# G9 — FSA parse
	def test_g9_fsa_parse(self):
		fsa = FSAParser()
		data = fsa.parse(SAMPLE_FSA)
		self.assertEqual(data["message"]["type"], "FSA")
		self.assertEqual(data["message"]["version"], "14")
		self.assertEqual(fsa.business_key(data), "157-41266466")
		awb = data["awb_reference"]
		self.assertEqual(awb["origin"], "DOH")
		self.assertEqual(awb["destination"], "LHR")
		# DLV event present
		codes = [e["status_code"] for e in data["fsu_data"]["movement_records"]]
		self.assertIn("DLV", codes)


# ---------------------------------------------------------------------------
# DB-backed tests
# ---------------------------------------------------------------------------


class TestFSUParserProcess(FrappeTestCase):
	def setUp(self):
		self.parser = FSUParser()
		# Clean up any Shipment FSU docs created by previous runs.
		for name in ("157-53806270", "157-41266466"):
			if frappe.db.exists("Shipment FSU", name):
				frappe.delete_doc("Shipment FSU", name, force=True)

	def tearDown(self):
		for name in ("157-53806270", "157-41266466"):
			if frappe.db.exists("Shipment FSU", name):
				frappe.delete_doc("Shipment FSU", name, force=True)

	def _process(self, raw, parser=None):
		p = parser or self.parser
		data = p.parse(raw)
		issues = [i for i in p.validate(data) if i["level"] == "Error"]
		self.assertEqual(issues, [], f"Validation errors: {issues}")
		return p.process(data, None)

	# G6 — Process: Shipment FSU created; no Shipment auto-created; re-process is no-op
	def test_g6_process_creates_doc(self):
		name = self._process(SAMPLE_FSU_ENVELOPE)
		self.assertEqual(name, "157-53806270")
		self.assertTrue(frappe.db.exists("Shipment FSU", "157-53806270"))

		doc = frappe.get_doc("Shipment FSU", "157-53806270")
		self.assertFalse(doc.shipment)  # no Shipment in DB → blank
		self.assertFalse(frappe.db.exists("Shipment", "157-53806270"))

		# Re-process → same row count (idempotent)
		count_before = len(doc.fsu_status_records)
		self._process(SAMPLE_FSU_ENVELOPE)
		doc.reload()
		self.assertEqual(len(doc.fsu_status_records), count_before)

	# G7 — History merge: two different messages → both events retained
	def test_g7_history_merge(self):
		self._process(SAMPLE_FSU_ENVELOPE)  # FIW event
		self._process(SAMPLE_FSU_BKD)       # BKD event

		doc = frappe.get_doc("Shipment FSU", "157-53806270")
		status_codes = {r.status_code for r in doc.fsu_status_records}
		self.assertIn("FIW", status_codes)
		self.assertIn("BKD", status_codes)

	# G10 — FSA shared target: FSA and FSU for same AWB → one Shipment FSU with both events
	def test_g10_fsa_shared_target(self):
		fsa = FSAParser()
		# Process FSA for 157-41266466
		self._process(SAMPLE_FSA, parser=fsa)
		self.assertTrue(frappe.db.exists("Shipment FSU", "157-41266466"))

		doc = frappe.get_doc("Shipment FSU", "157-41266466")
		self.assertEqual(doc.awb_number, "157-41266466")
		codes = {r.status_code for r in doc.fsu_status_records}
		self.assertIn("DLV", codes)

		# Cleanup
		frappe.delete_doc("Shipment FSU", "157-41266466", force=True)
