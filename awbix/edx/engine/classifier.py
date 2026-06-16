"""Detect (message_type, version) from a raw inbound payload.

Stage-level classification only decides which handler *would* apply; it never parses.
The first enabled definition whose ``detection_pattern`` matches wins.
"""

import re

import frappe

from awbix.edx.engine.registry import enabled_parser_definitions


def classify(raw: str) -> tuple[str | None, str | None]:
	"""Return ``(message_type, version)`` or ``(None, None)`` if nothing matches."""
	if not raw:
		return None, None
	head = raw.lstrip()
	for d in enabled_parser_definitions():
		pattern = (d.get("detection_pattern") or "").strip()
		if not pattern:
			continue
		try:
			if re.search(pattern, head, re.IGNORECASE | re.MULTILINE):
				return d["message_type"], d["version"]
		except re.error:
			frappe.log_error(f"Invalid detection_pattern on {d['name']}", "EDX classify")
			continue
	return None, None
