import os
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase


class TestProjectAISettings(FrappeTestCase):
	def _settings(self, **kwargs):
		s = frappe.get_single("Project AI Settings")
		for k, v in kwargs.items():
			setattr(s, k, v)
		return s

	def test_custom_requires_base_url(self):
		s = self._settings(provider="Custom", api_base_url="")
		with self.assertRaises(frappe.ValidationError):
			s.save()

	def test_defaults_fill_in_when_blank(self):
		s = self._settings(provider="Claude (Anthropic)", model="", api_base_url="")
		self.assertEqual(s.resolved_model(), "claude-opus-4-8")
		self.assertEqual(s.resolved_base_url(), "https://api.anthropic.com")

	def test_explicit_values_win(self):
		s = self._settings(
			provider="ChatGPT (OpenAI)", model="gpt-4o-mini", api_base_url="https://proxy.local/v1"
		)
		self.assertEqual(s.resolved_model(), "gpt-4o-mini")
		self.assertEqual(s.resolved_base_url(), "https://proxy.local/v1")

	def test_api_key_precedence_env_fallback(self):
		s = self._settings(provider="Claude (Anthropic)", api_key="")
		s.save()
		# No field value, no site_config key -> env var is used.
		with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "from-env"}):
			with patch.dict(frappe.conf, {"anthropic_api_key": None}):
				self.assertEqual(s.resolved_api_key(), "from-env")

	def test_api_key_field_wins_over_env(self):
		s = self._settings(provider="Claude (Anthropic)", api_key="from-field")
		s.save()
		with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "from-env"}):
			self.assertEqual(s.resolved_api_key(), "from-field")

	def test_test_connection_reports_disabled(self):
		from awbix.project.doctype.project_ai_settings.project_ai_settings import test_connection

		self._settings(enabled=0).save()
		result = test_connection()
		self.assertFalse(result["ok"])
