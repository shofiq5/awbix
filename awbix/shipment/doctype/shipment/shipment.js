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
					method: "awbix.edx.engine.pipeline.compose_and_validate_outbound",
					args: {
						source_doctype: "Shipment",
						source_name: frm.doc.name,
						message_type: "FWB",
						version: "16",
					},
					freeze: true,
					freeze_message: __("Validating FWB/16…"),
					callback(r) {
						const result = r.message;
						if (!result || !result.ok) {
							const issues = (result && result.issues) || [];
							const rows = issues
								.map(
									(i) =>
										`<tr><td><b>${frappe.utils.escape_html(i.level || "")}</b></td>` +
										`<td>${frappe.utils.escape_html(i.code || "")}</td>` +
										`<td>${frappe.utils.escape_html(i.message || "")}</td></tr>`
								)
								.join("");
							frappe.msgprint({
								title: __("FWB/16 Validation Failed"),
								message:
									`<table class="table table-bordered table-condensed">` +
									`<thead><tr><th>${__("Level")}</th><th>${__("Code")}</th><th>${__("Message")}</th></tr></thead>` +
									`<tbody>${rows || `<tr><td colspan="3">${__("Unknown error")}</td></tr>`}</tbody></table>`,
								indicator: "red",
							});
							return;
						}
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
				});
			},
			__("EDX")
		);
		frm.add_custom_button(
			__("Send FSR"),
			() => {
				frappe.call({
					method: "awbix.edx.engine.pipeline.compose_and_validate_outbound",
					args: {
						source_doctype: "Shipment",
						source_name: frm.doc.name,
						message_type: "FSR",
						version: "1",
					},
					freeze: true,
					freeze_message: __("Validating FSR…"),
					callback(r) {
						const result = r.message;
						if (!result || !result.ok) {
							const issues = (result && result.issues) || [];
							const rows = issues
								.map(
									(i) =>
										`<tr><td><b>${frappe.utils.escape_html(i.level || "")}</b></td>` +
										`<td>${frappe.utils.escape_html(i.code || "")}</td>` +
										`<td>${frappe.utils.escape_html(i.message || "")}</td></tr>`
								)
								.join("");
							frappe.msgprint({
								title: __("FSR Validation Failed"),
								message:
									`<table class="table table-bordered table-condensed">` +
									`<thead><tr><th>${__("Level")}</th><th>${__("Code")}</th><th>${__("Message")}</th></tr></thead>` +
									`<tbody>${rows || `<tr><td colspan="3">${__("Unknown error")}</td></tr>`}</tbody></table>`,
								indicator: "red",
							});
							return;
						}
						frappe.call({
							method: "awbix.edx.engine.pipeline.queue_outbound",
							args: {
								source_doctype: "Shipment",
								source_name: frm.doc.name,
								message_type: "FSR",
								version: "1",
							},
							freeze: true,
							freeze_message: __("Queuing FSR…"),
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
				});
			},
			__("EDX")
		);
		frm.add_custom_button(
			__("Send FFR"),
			() => {
				frappe.call({
					method: "awbix.edx.engine.pipeline.compose_and_validate_outbound",
					args: {
						source_doctype: "Shipment",
						source_name: frm.doc.name,
						message_type: "FFR",
						version: "6",
					},
					freeze: true,
					freeze_message: __("Validating FFR…"),
					callback(r) {
						const result = r.message;
						if (!result || !result.ok) {
							const issues = (result && result.issues) || [];
							const rows = issues
								.map(
									(i) =>
										`<tr><td><b>${frappe.utils.escape_html(i.level || "")}</b></td>` +
										`<td>${frappe.utils.escape_html(i.code || "")}</td>` +
										`<td>${frappe.utils.escape_html(i.message || "")}</td></tr>`
								)
								.join("");
							frappe.msgprint({
								title: __("FFR Validation Failed"),
								message:
									`<table class="table table-bordered table-condensed">` +
									`<thead><tr><th>${__("Level")}</th><th>${__("Code")}</th><th>${__("Message")}</th></tr></thead>` +
									`<tbody>${rows || `<tr><td colspan="3">${__("Unknown error")}</td></tr>`}</tbody></table>`,
								indicator: "red",
							});
							return;
						}
						frappe.call({
							method: "awbix.edx.engine.pipeline.queue_outbound",
							args: {
								source_doctype: "Shipment",
								source_name: frm.doc.name,
								message_type: "FFR",
								version: "6",
							},
							freeze: true,
							freeze_message: __("Queuing FFR…"),
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
				});
			},
			__("EDX")
		);
	},
});
