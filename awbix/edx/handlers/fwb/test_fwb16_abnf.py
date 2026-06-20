"""Tests for the FWB/16 ABNF validator.

Fixtures use the ABNF-conformant AWB consignment-detail encoding where the 8-digit
serial, 3-letter origin and 3-letter destination are concatenated (e.g.
``001-12345675JFKLAX``) and only the quantity detail is slant-delimited — exactly as
the grammar in ``awbix/edx/.claude/fwb_abnf.txt`` defines it.
"""

from frappe.tests.utils import FrappeTestCase

from awbix.edx.handlers.fwb.fwb16_validator import _SAMPLE, FWBABNFValidator


class TestFWB16ABNFValidator(FrappeTestCase):
	"""Test FWB/16 ABNF validator."""

	def test_empty_message(self):
		"""Empty message should produce a single MSG_EMPTY violation."""
		issues = FWBABNFValidator().validate("")
		self.assertTrue(any(i["code"] == "MSG_EMPTY" for i in issues))

	def test_valid_message_has_no_violations(self):
		"""The reference valid FWB/16 message must validate cleanly."""
		issues = FWBABNFValidator().validate(_SAMPLE)
		self.assertEqual(issues, [], f"Unexpected violations: {issues}")

	def test_checks_are_numbered(self):
		"""Every check carries a hierarchical 'section.item' reference (1.1, 2.1, …)."""
		validator = FWBABNFValidator()
		validator.validate_report(_SAMPLE)
		self.assertTrue(validator.checks)
		self.assertEqual(validator.checks[0]["ref"], "1.1")
		for check in validator.checks:
			self.assertRegex(check["ref"], r"^\d+\.\d+$")

	def test_bad_awb_checkdigit(self):
		"""Invalid mod-7 check digit should be reported."""
		msg = "FWB/16\n001-12345671JFKLAX/T100K1000"
		issues = FWBABNFValidator().validate(msg)
		self.assertTrue(any("Check digit" in i["message"] for i in issues))

	def test_missing_required_segments(self):
		"""Missing mandatory segments should be reported."""
		msg = "FWB/16\n001-12345675JFKLAX/T100K1000"
		issues = FWBABNFValidator().validate(msg)
		self.assertTrue(any("missing" in i["message"].lower() for i in issues))

	def test_bad_currency_code(self):
		"""Invalid currency code should be detected."""
		msg = "FWB/16\n001-12345675JFKLAX/T100K1000\nCVD/XX"
		issues = FWBABNFValidator().validate(msg)
		self.assertTrue(any("currency" in i["field"].lower() for i in issues))

	def test_only_errors_returned(self):
		"""Every returned issue is a fully-formed Error with a reference."""
		msg = "FWB/16\n001-12345675JFKLAX/T100K1000\nRTG//AA"
		issues = FWBABNFValidator().validate(msg)
		for issue in issues:
			self.assertIn("field", issue)
			self.assertIn("message", issue)
			self.assertIn("ref", issue)
			self.assertEqual(issue["level"], "Error")

	def test_same_origin_destination(self):
		"""Identical origin and destination should be flagged."""
		msg = "FWB/16\n001-12345675JFKJFK/T100K1000"
		issues = FWBABNFValidator().validate(msg)
		self.assertTrue(any("identical" in i["message"].lower() for i in issues))

	def test_invalid_date_format_in_isu(self):
		"""Invalid date format in ISU should be detected."""
		msg = "FWB/16\n001-12345675JFKLAX/T100K1000\nISU/20250115/JFK"
		issues = FWBABNFValidator().validate(msg)
		self.assertTrue(
			any("date" in i["field"].lower() or "DDMMMYY" in i["message"] for i in issues)
		)

	def test_airline_prefix_format(self):
		"""Airline prefix must be 3 numeric digits (DE112)."""
		msg = "FWB/16\n12-12345675JFKLAX/T100K1000"
		issues = FWBABNFValidator().validate(msg)
		prefix_errors = [i for i in issues if "DE112" in i["field"]]
		self.assertTrue(prefix_errors)
		for error in prefix_errors:
			self.assertIn("Airline prefix", error["message"])

	def test_weight_code_validation(self):
		"""Weight code must be K or L."""
		msg = "FWB/16\n001-12345675JFKLAX/T100X1000"
		issues = FWBABNFValidator().validate(msg)
		self.assertTrue(any("weight" in i["field"].lower() for i in issues))

	def test_charge_summary_requirement(self):
		"""PPD or COL must be present."""
		msg = (
			"FWB/16\n"
			"001-12345675JFKLAX/T100K1000\n"
			"RTG/LAXAA\n"
			"SHP\n/ACME EXPORTS\n/1 MAIN STREET\n/NEW YORK\n/US/10001\n"
			"CNE\n/WIDGET IMPORTS\n/2 HIGH STREET\n/LONDON\n/GB/EC1A\n"
			"CVD/USD//PP/NVD/NCV/XXX\n"
			"RTD/1/P100/K1000/CQ/W1000/R1.00/T1000.00\n"
			"ISU/01JAN26/NEW YORK\n"
			"REF/JFKAAAA"
		)
		issues = FWBABNFValidator().validate(msg)
		self.assertTrue(any("PPD" in i["field"] or "COL" in i["field"] for i in issues))
