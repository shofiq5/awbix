"""Resolve (message_type, version) → handler classes via the DB registry.

This is the only module that knows how to find a handler. Handlers are referenced by
dotted path stored on ``EDX Message Definition`` and loaded with ``frappe.get_attr``,
so a new message kind needs no core edits — just a class plus one definition row.
"""

import frappe
from frappe import _

from awbix.edx.engine.exceptions import EDXNotRegisteredError

# Default adapter per channel; an EDX Connection may override via ``transport_class``.
_DEFAULT_TRANSPORTS = {
	"Email": "awbix.edx.transports.email_transport.EmailTransport",
	"SFTP": "awbix.edx.transports.sftp_transport.SFTPTransport",
	"MQ": "awbix.edx.transports.mq_transport.MQTransport",
	"Manual": "awbix.edx.transports.manual_transport.ManualTransport",
}


def get_definition(message_type: str, version: str):
	"""Return the ``EDX Message Definition`` for a (type, version) or raise."""
	name = f"{message_type}-{version}"
	if not frappe.db.exists("EDX Message Definition", name):
		raise EDXNotRegisteredError(
			_("No EDX Message Definition for {0}/{1}").format(message_type, version)
		)
	return frappe.get_cached_doc("EDX Message Definition", name)


def get_parser(message_type: str, version: str):
	d = get_definition(message_type, version)
	if not d.is_parser_enabled:
		raise EDXNotRegisteredError(_("Parser for {0}/{1} is not enabled").format(message_type, version))
	if not d.parser_class:
		raise EDXNotRegisteredError(
			_("No parser class configured for {0}/{1}").format(message_type, version)
		)
	return frappe.get_attr(d.parser_class)()


def get_composer(message_type: str, version: str):
	d = get_definition(message_type, version)
	if not d.is_composer_enabled:
		raise EDXNotRegisteredError(
			_("Composer for {0}/{1} is not enabled").format(message_type, version)
		)
	if not d.composer_class:
		raise EDXNotRegisteredError(
			_("No composer class configured for {0}/{1}").format(message_type, version)
		)
	return frappe.get_attr(d.composer_class)()


def get_transport(connection):
	"""Resolve a ``BaseTransport`` for an ``EDX Connection`` (doc or name)."""
	if isinstance(connection, str):
		connection = frappe.get_doc("EDX Connection", connection)
	path = connection.get("transport_class") or _DEFAULT_TRANSPORTS.get(connection.channel)
	if not path:
		raise EDXNotRegisteredError(_("No transport adapter for channel {0}").format(connection.channel))
	return frappe.get_attr(path)(connection)


def enabled_parser_definitions():
	"""Enabled parser definitions, ordered for deterministic classification."""
	return frappe.get_all(
		"EDX Message Definition",
		filters={"is_parser_enabled": 1},
		fields=["name", "message_type", "version", "detection_pattern", "target_doctype"],
		order_by="message_type asc, version desc",
	)
