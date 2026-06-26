// Copyright (c) 2026, CargoXY and contributors
// AWB Series Generator – Client Script

frappe.ui.form.on("AWB Series Generator", {
    // ---------------------------------------------------------------- //
    //  Form ready
    // ---------------------------------------------------------------- //
    refresh(frm) {
        frm.trigger("update_total_count");

        // Show Generate button only when status is Draft and document is saved
        if (!frm.is_new() && frm.doc.generation_status === "Draft") {
            frm.add_custom_button(__("Generate AWB Inventory"), () => {
                frm.trigger("confirm_generate");
            }, __("Actions")).addClass("btn-primary");
        }

        // Show a warning banner if already generated
        if (frm.doc.generation_status === "Generated") {
            frm.set_intro(
                __("✅ AWB Inventory has been generated for this series. " +
                   "{0} records created on {1}.",
                   [frm.doc.generated_count, frappe.datetime.str_to_user(frm.doc.generated_date)]),
                "green"
            );
        }
    },

    // ---------------------------------------------------------------- //
    //  Live total count update
    // ---------------------------------------------------------------- //
    serial_start(frm) { frm.trigger("update_total_count"); },
    serial_end(frm)   { frm.trigger("update_total_count"); },

    update_total_count(frm) {
        const start = parseInt(frm.doc.serial_start || 0);
        const end   = parseInt(frm.doc.serial_end   || 0);
        if (start > 0 && end >= start) {
            frm.set_value("total_count", end - start + 1);
        } else {
            frm.set_value("total_count", 0);
        }
    },

    // ---------------------------------------------------------------- //
    //  Confirm and trigger generation
    // ---------------------------------------------------------------- //
    confirm_generate(frm) {
        const count = frm.doc.total_count || 0;
        if (count <= 0) {
            frappe.msgprint({
                message: __("Please set a valid Serial Start and Serial End range first."),
                title: __("Invalid Range"),
                indicator: "red"
            });
            return;
        }

        frappe.confirm(
            __("This will generate <strong>{0}</strong> AWB Inventory records for prefix <strong>{1}</strong>. Continue?",
               [count, frm.doc.awb_prefix]),
            () => {
                frm.trigger("do_generate");
            }
        );
    },

    do_generate(frm) {
        frappe.dom.freeze(__("Generating AWB Inventory... Please wait."));
        frm.call({
            method: "generate_awb_inventory",
            doc: frm.doc,
            callback(r) {
                frappe.dom.unfreeze();
                if (!r.exc) {
                    frm.reload_doc();
                }
            },
            error() {
                frappe.dom.unfreeze();
            }
        });
    }
});
