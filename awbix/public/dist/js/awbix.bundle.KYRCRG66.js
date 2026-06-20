(() => {
  // ../awbix/awbix/public/js/list_settings.js
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
    }
  };
  var AWBIX_MASTER_DOCTYPES = [
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
    "OCI Information Identifier"
  ];
  var awbix_master_list_defaults = {
    get_indicator() {
      return [__("Active"), "blue", ""];
    }
  };
  for (const doctype of AWBIX_MASTER_DOCTYPES) {
    frappe.listview_settings[doctype] = Object.assign(
      {},
      awbix_master_list_defaults,
      frappe.listview_settings[doctype] || {}
    );
  }
})();
//# sourceMappingURL=awbix.bundle.KYRCRG66.js.map
