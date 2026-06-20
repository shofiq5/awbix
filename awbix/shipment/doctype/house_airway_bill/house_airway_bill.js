// Copyright (c) 2026, Shofiq and Contributors
// See license.txt

frappe.ui.form.on("House Airway Bill", {
	refresh(frm) {
		if (frm.doc.awb_assignment_status === "Unassigned AWB" && !frm.is_new()) {
			frm.add_custom_button(__("Assign AWB"), function () {
				frappe.call({
					method: "awbix.shipment.doctype.house_airway_bill.house_airway_bill.assign_awb",
					args: { names: [frm.doc.name] },
					freeze: true,
					callback(r) {
						if (!r.exc && r.message) {
							const { assigned, not_found } = r.message;
							if (assigned.length) {
								frappe.msgprint(__("AWB assigned successfully."));
								frm.reload_doc();
							} else {
								frappe.msgprint(
									__(
										"Master AWB {0} is not yet available in the system.",
										[frm.doc.pending_awb_number]
									)
								);
							}
						}
					},
				});
			});
		}
	},
});

frappe.listview_settings["House Airway Bill"] = {
	onload(listview) {
		listview.page.add_action_item(__("Assign AWB"), function () {
			const names = listview.get_checked_items(true);
			if (!names.length) {
				frappe.msgprint(__("Please select one or more records."));
				return;
			}
			frappe.call({
				method: "awbix.shipment.doctype.house_airway_bill.house_airway_bill.assign_awb",
				args: { names: names },
				freeze: true,
				freeze_message: __("Assigning AWB…"),
				callback(r) {
					if (!r.exc && r.message) {
						const { assigned, not_found } = r.message;
						let msg = assigned.length
							? __("{0} HAWB(s) successfully assigned.", [assigned.length])
							: "";
						if (not_found.length) {
							msg +=
								(msg ? " " : "") +
								__(
									"{0} HAWB(s) — master AWB not yet available.",
									[not_found.length]
								);
						}
						frappe.msgprint(msg || __("Nothing to assign."));
						listview.refresh();
					}
				},
			});
		});
	},
};
