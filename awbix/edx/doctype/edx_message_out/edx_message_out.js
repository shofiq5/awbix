// Copyright (c) 2026, Shofiq and contributors
// For license information, please see license.txt

frappe.ui.form.on("EDX Message Out", {
	refresh(frm) {
		if (frm.is_new()) {
			return;
		}
		const label = frm.doc.delivery_status === "Failed" ? __("Re-send") : __("Dispatch");
		if (["Queued", "Failed"].includes(frm.doc.delivery_status)) {
			frm.add_custom_button(label, () => {
				frappe.call({
					doc: frm.doc,
					method: "dispatch",
					freeze: true,
					freeze_message: __("Dispatching…"),
					callback(r) {
						const res = r.message || {};
						frappe.show_alert({
							message: res.ok ? __("Sent") : __("Failed: {0}", [res.error || res.status || ""]),
							indicator: res.ok ? "green" : "red",
						});
						frm.reload_doc();
					},
				});
			});
		}
	},
});
