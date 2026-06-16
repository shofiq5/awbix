"""EDX install / migrate hooks.

``after_migrate`` seeds the built-in message definitions if missing. Idempotent and
safe to run on every migrate — it only inserts what isn't already there, so an admin
can freely edit/disable a definition afterwards without it being clobbered.
"""

import frappe

# Built-in definitions. Add new (type, version) handlers here or create them in the UI.
_DEFINITIONS = [
	{
		"message_type": "FWB",
		"version": "16",
		"title": "FWB/16 — Air Waybill (Cargo-IMP)",
		"standard": "Cargo-IMP",
		"parser_class": "awbix.edx.handlers.fwb.fwb16_parser.FWB16Parser",
		"target_doctype": "Shipment",
		"is_parser_enabled": 1,
		"detection_pattern": "^FWB/16",
		"amendment_mode": "Auto Apply",
	},
]


def after_migrate():
	seed_definitions()


def seed_definitions():
	if not frappe.db.exists("DocType", "EDX Message Definition"):
		return
	for d in _DEFINITIONS:
		name = f"{d['message_type']}-{d['version']}"
		if frappe.db.exists("EDX Message Definition", name):
			continue
		doc = frappe.new_doc("EDX Message Definition")
		doc.update(d)
		doc.flags.ignore_permissions = True
		doc.insert()
	frappe.db.commit()
