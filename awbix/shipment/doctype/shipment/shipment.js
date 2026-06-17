// Copyright (c) 2026, Shofiq and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shipment", {
	refresh(frm) {
		if (frm.is_new()) {
			return;
		}
		frm.add_custom_button(
			__("Send FWB/16"),
			() => {
				frappe.call({
					method: "awbix.edx.engine.pipeline.queue_outbound",
					args: {
						source_doctype: "Shipment",
						source_name: frm.doc.name,
						message_type: "FWB",
						version: "16",
					},
					freeze: true,
					freeze_message: __("Queuing FWB…"),
					callback(r) {
						if (r.message) {
							frappe.show_alert({
								message: __("Queued EDX Message Out {0}", [r.message]),
								indicator: "green",
							});
						}
					},
				});
			},
			__("EDX")
		);
	},
});
