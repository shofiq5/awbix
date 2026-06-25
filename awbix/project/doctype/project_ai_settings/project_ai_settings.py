import os

import frappe
from frappe.model.document import Document

# Per-provider defaults. Used when the user leaves Model / API Base URL blank.
PROVIDER_DEFAULTS = {
	"Claude (Anthropic)": {
		"model": "claude-opus-4-8",
		"api_base_url": "https://api.anthropic.com",
		"config_key": "anthropic_api_key",
		"env_var": "ANTHROPIC_API_KEY",
	},
	"ChatGPT (OpenAI)": {
		"model": "gpt-4o",
		"api_base_url": "https://api.openai.com/v1",
		"config_key": "openai_api_key",
		"env_var": "OPENAI_API_KEY",
	},
	"Custom": {
		"model": "",
		"api_base_url": "",
		"config_key": "project_ai_api_key",
		"env_var": "PROJECT_AI_API_KEY",
	},
}


class ProjectAISettings(Document):
	def validate(self):
		if self.provider == "Custom" and not self.api_base_url:
			frappe.throw("API Base URL is required when Provider is Custom.")

	def resolved_model(self):
		return (self.model or "").strip() or PROVIDER_DEFAULTS[self.provider]["model"]

	def resolved_base_url(self):
		return (self.api_base_url or "").strip() or PROVIDER_DEFAULTS[self.provider]["api_base_url"]

	def resolved_api_key(self):
		"""Resolve the key by precedence: DocType field -> site_config.json -> env var.

		Never log the returned value.
		"""
		key = self.get_password("api_key", raise_exception=False)
		if key:
			return key
		defaults = PROVIDER_DEFAULTS[self.provider]
		key = frappe.conf.get(defaults["config_key"])
		if key:
			return key
		return os.environ.get(defaults["env_var"])


@frappe.whitelist()
def test_connection():
	"""Validate the configured key/endpoint without running a full scan.

	Returns a dict the client form can display. Does not raise on auth failure;
	it reports the outcome so the user can adjust settings.
	"""
	from awbix.project.ai_provider import get_provider

	settings = frappe.get_single("Project AI Settings")
	if not settings.enabled:
		return {"ok": False, "message": "AI layer is disabled. Enable it first."}

	provider = get_provider(settings)
	return provider.test_connection()
