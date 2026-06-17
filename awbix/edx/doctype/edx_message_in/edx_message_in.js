// Copyright (c) 2026, Shofiq and contributors
// For license information, please see license.txt

frappe.ui.form.on("EDX Message In", {
	refresh(frm) {
		if (frm.is_new()) {
			return;
		}
		frm.add_custom_button(__("Verify"), () => run(frm, "verify_message_in", __("Verifying…")));
		frm.add_custom_button(__("Process"), () => run(frm, "process_message_in", __("Processing…")));
	},
});

function run(frm, method, message) {
	frappe.call({
		method: `awbix.edx.engine.pipeline.${method}`,
		args: { name: frm.doc.name },
		freeze: true,
		freeze_message: message,
		callback(r) {
			const res = r.message || {};
			frappe.show_alert({
				message: res.ok === false ? __("Completed with issues") : __("Done"),
				indicator: res.ok === false ? "orange" : "green",
			});
			frm.reload_doc();
		},
	});
}
