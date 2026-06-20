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

		// Verify Message button (when already composed)
		if (frm.doc.compose_status === "Composed") {
			frm.add_custom_button(__("Verify Message"), () => {
				frappe.call({
					method: "awbix.edx.engine.pipeline.verify_message_out",
					args: { name: frm.doc.name },
					freeze: true,
					freeze_message: __("Validating ABNF structure…"),
					callback(r) {
						frm.reload_doc();
						const res = r.message || {};
						_show_verify_modal(frm, res);
					},
					error(r) {
						frappe.msgprint({
							title: __("Verify Error"),
							message: r.message || __("An unexpected error occurred"),
							indicator: "red",
						});
					},
				});
			}, __("Actions"));
		}
	},
});

function _show_verify_modal(frm, res) {
	const violations = res.violations || [];
	const valid = res.valid;

	const statusHtml = valid
		? `<div class="alert alert-success">${__("✓ Passed — no errors found")}</div>`
		: `<div class="alert alert-danger">${__("✗ Failed — {0} error(s) found", [violations.filter(v => v.level === "Error").length])}</div>`;

	const rowsHtml = violations.length === 0
		? `<p class="text-muted">${__("No violations.")}</p>`
		: `<table class="table table-bordered table-sm">
			<thead><tr>
				<th style="width:10%">${__("Level")}</th>
				<th style="width:15%">${__("Code")}</th>
				<th style="width:20%">${__("Field")}</th>
				<th>${__("Message")}</th>
			</tr></thead>
			<tbody>
				${violations.map(v => `<tr class="${v.level === "Error" ? "table-danger" : v.level === "Warning" ? "table-warning" : ""}">
					<td><small>${frappe.utils.escape_html(v.level || "")}</small></td>
					<td><code style="font-size:0.8em">${frappe.utils.escape_html(v.code || "")}</code></td>
					<td><small>${frappe.utils.escape_html(v.field || "")}</small></td>
					<td><small>${frappe.utils.escape_html(v.message || "")}</small></td>
				</tr>`).join("")}
			</tbody>
		</table>`;

	const jsonBtn = violations.length
		? `<button class="btn btn-sm btn-secondary mt-2" id="copy-violations-json">${__("Copy as JSON")}</button>`
		: "";

	const d = new frappe.ui.Dialog({
		title: valid ? __("Verify Message — Passed ✓") : __("Verify Message — Failed ✗"),
		fields: [{ fieldtype: "HTML", fieldname: "content" }],
		primary_action_label: __("Close"),
		primary_action() { d.hide(); },
	});
	d.fields_dict.content.$wrapper.html(statusHtml + rowsHtml + jsonBtn);
	if (violations.length) {
		d.fields_dict.content.$wrapper.find("#copy-violations-json").on("click", () => {
			frappe.utils.copy_to_clipboard(JSON.stringify(violations, null, 2));
			frappe.show_alert({ message: __("Copied to clipboard ✓"), indicator: "green" });
		});
	}
	d.show();
}
