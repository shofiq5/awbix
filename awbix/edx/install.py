"""EDX install / migrate hooks.

``after_migrate`` seeds the built-in message definitions if missing. Idempotent and
safe to run on every migrate — it only inserts what isn't already there, so an admin
can freely edit/disable a definition afterwards without it being clobbered.
"""

import frappe

# Built-in definitions. Add new (type, version) handlers here or create them in the UI.
_DEFINITIONS = [
	{
		"message_type": "FHL",
		"version": "5",
		"title": "FHL/5 — Consolidation List / House Waybills (Cargo-IMP)",
		"standard": "Cargo-IMP",
		"parser_class": "awbix.edx.handlers.fhl.fhl_parser.FHLParser",
		"composer_class": "awbix.edx.handlers.fhl.fhl_composer.FHLComposer",
		"target_doctype": "House Airway Bill",
		"is_parser_enabled": 1,
		"is_composer_enabled": 1,
		"auto_promote": 1,
		"auto_process": 1,
		"detection_pattern": "^FHL/5",
		"amendment_mode": "Auto Apply",
	},
	{
		"message_type": "FWB",
		"version": "16",
		"title": "FWB/16 — Air Waybill (Cargo-IMP)",
		"standard": "Cargo-IMP",
		"parser_class": "awbix.edx.handlers.fwb.fwb16_parser.FWB16Parser",
		"composer_class": "awbix.edx.handlers.fwb.fwb16_composer.FWB16Composer",
		"target_doctype": "Shipment",
		"is_parser_enabled": 1,
		"is_composer_enabled": 1,
		"auto_promote": 1,
		"auto_process": 1,
		"detection_pattern": "^FWB/16",
		"amendment_mode": "Auto Apply",
	},
	{
		"message_type": "FMA",
		"version": "1",
		"title": "FMA — Acknowledgement (Cargo-IMP)",
		"standard": "Cargo-IMP",
		"parser_class": "awbix.edx.handlers.ack.fma_parser.FMAParser",
		"target_doctype": "Shipment",
		"is_parser_enabled": 1,
		"detection_pattern": "^FMA",
		"bypass_amendment": 1,
		"auto_promote": 1,
		"auto_process": 1,
	},
	{
		"message_type": "FNA",
		"version": "1",
		"title": "FNA — Rejection (Cargo-IMP)",
		"standard": "Cargo-IMP",
		"parser_class": "awbix.edx.handlers.ack.fna_parser.FNAParser",
		"target_doctype": "Shipment",
		"is_parser_enabled": 1,
		"detection_pattern": "^FNA",
		"bypass_amendment": 1,
		"auto_promote": 1,
		"auto_process": 1,
	},
	{
		"message_type": "FSU",
		"version": "14",
		"title": "FSU/14 — Functional Status Update (Cargo-IMP)",
		"standard": "Cargo-IMP",
		"parser_class": "awbix.edx.handlers.fsu.fsu_parser.FSUParser",
		"target_doctype": "Shipment FSU",
		"is_parser_enabled": 1,
		"is_composer_enabled": 0,
		"detection_pattern": "^FSU/14",
		"bypass_amendment": 1,
		"auto_promote": 1,
		"auto_process": 1,
	},
	{
		"message_type": "FSA",
		"version": "14",
		"title": "FSA/14 — Freight Status Advice (Cargo-IMP)",
		"standard": "Cargo-IMP",
		"parser_class": "awbix.edx.handlers.fsu.fsa_parser.FSAParser",
		"target_doctype": "Shipment FSU",
		"is_parser_enabled": 1,
		"is_composer_enabled": 0,
		"detection_pattern": "^FSA/14",
		"bypass_amendment": 1,
		"auto_promote": 1,
		"auto_process": 1,
	},
	{
		"message_type": "FSR",
		"version": "1",
		"title": "FSR — Flight Status Request (Cargo-IMP)",
		"standard": "Cargo-IMP",
		"composer_class": "awbix.edx.handlers.fsr.fsr_composer.FSRComposer",
		"target_doctype": "Shipment",
		"is_parser_enabled": 0,
		"is_composer_enabled": 1,
		"detection_pattern": "^FSR",
		"bypass_amendment": 1,
	},
	{
		"message_type": "FFR",
		"version": "6",
		"title": "FFR/6 — AWB Space Allocation Request (Cargo-IMP)",
		"standard": "Cargo-IMP",
		"composer_class": "awbix.edx.handlers.ffr.ffr_composer.FFRComposer",
		"target_doctype": "Shipment",
		"is_parser_enabled": 0,
		"is_composer_enabled": 1,
		"detection_pattern": "^FFR/6",
		"bypass_amendment": 1,
	},
]

# Fields backfilled onto an already-seeded definition so a re-migrate activates new
# capabilities (e.g. the M5 composer) without an admin editing the row by hand.
_BACKFILL_FIELDS = ("composer_class", "is_composer_enabled", "auto_promote", "auto_process")


# EDX roles (referenced by the EDX DocTypes' permissions). Desk roles, not restricted.
_ROLES = ["EDX Manager", "EDX Operator", "EDX Viewer"]


def after_migrate():
	seed_roles()
	seed_definitions()


def seed_roles():
	for role in _ROLES:
		if frappe.db.exists("Role", role):
			continue
		doc = frappe.new_doc("Role")
		doc.role_name = role
		doc.desk_access = 1
		doc.flags.ignore_permissions = True
		doc.insert()
	frappe.db.commit()


def seed_definitions():
	if not frappe.db.exists("DocType", "EDX Message Definition"):
		return
	for d in _DEFINITIONS:
		name = f"{d['message_type']}-{d['version']}"
		if frappe.db.exists("EDX Message Definition", name):
			_backfill_definition(name, d)
			continue
		doc = frappe.new_doc("EDX Message Definition")
		doc.update(d)
		doc.flags.ignore_permissions = True
		doc.insert()
	frappe.db.commit()


def _backfill_definition(name, defaults):
	"""Set only the backfill fields that are still empty — never clobber admin edits."""
	current = frappe.db.get_value("EDX Message Definition", name, _BACKFILL_FIELDS, as_dict=True)
	updates = {f: defaults[f] for f in _BACKFILL_FIELDS if f in defaults and not current.get(f)}
	if updates:
		frappe.db.set_value("EDX Message Definition", name, updates)
