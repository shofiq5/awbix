// Common list view standard for all AWBix doctypes, loaded app-wide via
// hooks.app_include_js. Registers frappe.listview_settings so every list
// page shares the same indicators and behavior.

frappe.provide("frappe.listview_settings");

frappe.listview_settings["Shipment"] = {
	add_fields: ["docstatus", "origin", "destination", "issue_date", "number_of_pieces", "weight"],
	get_indicator(doc) {
		if (doc.docstatus === 1) {
			return [__("Submitted"), "green", "docstatus,=,1"];
		}
		if (doc.docstatus === 2) {
			return [__("Cancelled"), "red", "docstatus,=,2"];
		}
		return [__("Draft"), "orange", "docstatus,=,0"];
	},
};

const AWBIX_MASTER_DOCTYPES = [
	"Airline",
	"Airport",
	"Party",
	"Service Code",
	"Charge Code",
	"Other Charge Code",
	"Rate Class Code",
	"Special Handling Code",
	"Measurement Unit Code",
	"Volume Code",
	"ULD Type",
	"Participant Identifier",
	"Accounting Information Identifier",
	"Customs Information Identifier",
	"OCI Information Identifier",
];

const awbix_master_list_defaults = {
	get_indicator() {
		return [__("Active"), "blue", ""];
	},
};

for (const doctype of AWBIX_MASTER_DOCTYPES) {
	// Merge so a doctype-specific settings file can still override the defaults.
	frappe.listview_settings[doctype] = Object.assign(
		{},
		awbix_master_list_defaults,
		frappe.listview_settings[doctype] || {}
	);
}
