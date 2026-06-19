// Copyright (c) 2026, Shofiq and contributors
// For license information, please see license.txt

console.log("EDX Message Stage JS file loaded");

frappe.listview_settings["EDX Message Stage"] = {
	onload(listview) {
		console.log("EDX Message Stage listview onload fired");
		listview.page.add_inner_button(__("Sync Message"), () => {
			console.log("Sync Message button clicked");
			frappe.call({
				method: "awbix.edx.engine.pipeline.sync_email_messages",
				freeze: true,
				freeze_message: __("Checking email…"),
				callback(r) {
					console.log("sync_email_messages response:", r);
					const msg = r && r.message;
					if (msg && msg.ok) {
						frappe.show_alert({ message: __(msg.message), indicator: "green" }, 5);
						listview.refresh();
					} else {
						frappe.msgprint(__(msg && msg.message) || __("Sync failed"));
					}
				},
			});
		});
	},
};

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
