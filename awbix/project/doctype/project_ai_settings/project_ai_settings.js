frappe.ui.form.on("Project AI Settings", {
	refresh(frm) {
		frm.add_custom_button(__("Test Connection"), () => {
			frappe.call({
				method: "awbix.project.doctype.project_ai_settings.project_ai_settings.test_connection",
				freeze: true,
				freeze_message: __("Testing connection…"),
				callback: (r) => {
					const res = r.message || {};
					if (res.ok) {
						frappe.msgprint({
							title: __("Connection OK"),
							message: res.message || __("Provider reachable."),
							indicator: "green",
						});
					} else {
						frappe.msgprint({
							title: __("Connection Failed"),
							message: res.message || __("Could not reach provider."),
							indicator: "red",
						});
					}
				},
			});
		});
	},
});
