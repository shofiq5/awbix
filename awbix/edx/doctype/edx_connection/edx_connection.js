// EDX Connection — Test Incoming / Test Outgoing buttons.
frappe.ui.form.on("EDX Connection", {
	refresh(frm) {
		if (frm.is_new()) {
			return;
		}
		const dir = frm.doc.direction;

		if (dir !== "Outbound") {
			frm.add_custom_button(__("Test Incoming"), () => run_test(frm, "test_incoming"), __("Test"));
		}
		if (dir !== "Inbound") {
			frm.add_custom_button(__("Test Outgoing"), () => run_test(frm, "test_outgoing"), __("Test"));
		}
		if (dir !== "Outbound") {
			frm.add_custom_button(__("Manual Ingest"), () => manual_ingest(frm));
		}
	},
});

function manual_ingest(frm) {
	frappe.prompt(
		[
			{
				fieldname: "raw_message",
				fieldtype: "Long Text",
				label: __("Raw Message"),
				reqd: 1,
			},
		],
		(values) => {
			frappe.call({
				method: "awbix.edx.engine.pipeline.ingest_raw",
				args: { raw: values.raw_message, connection: frm.doc.name },
				freeze: true,
				freeze_message: __("Ingesting…"),
				callback(r) {
					if (r.message) {
						frappe.show_alert({
							message: __("Staged as {0}", [r.message]),
							indicator: "green",
						});
					}
				},
			});
		},
		__("Manual Ingest"),
		__("Ingest")
	);
}

function run_test(frm, method) {
	frappe.dom.freeze(__("Testing connection…"));
	frm.call(method)
		.then((r) => {
			const res = r.message || {};
			frappe.msgprint({
				title: res.ok ? __("Connection OK") : __("Connection Failed"),
				indicator: res.ok ? "green" : "red",
				message: frappe.utils.escape_html(res.message || ""),
			});
			frm.reload_doc();
		})
		.always(() => frappe.dom.unfreeze());
}
