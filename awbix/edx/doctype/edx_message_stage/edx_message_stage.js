// Copyright (c) 2026, Shofiq and contributors
// For license information, please see license.txt

frappe.ui.form.on("EDX Message Stage", {
	refresh(frm) {
		if (frm.is_new()) {
			return;
		}
		if (!frm.doc.message_in && frm.doc.detected_type) {
			frm.add_custom_button(__("Promote"), () => {
				frappe.call({
					method: "awbix.edx.engine.pipeline.promote_stage",
					args: { stage_name: frm.doc.name },
					freeze: true,
					freeze_message: __("Promoting…"),
					callback: () => frm.reload_doc(),
				});
			});
		}
	},
});
