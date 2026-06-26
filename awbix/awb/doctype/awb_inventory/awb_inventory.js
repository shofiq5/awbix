// Copyright (c) 2026, CargoXY and contributors
// AWB Inventory – Client Script + Workbench Dialog

if (typeof console !== 'undefined') {
    // marker log to detect whether this file is delivered and executed in browser
    const _ts = (new Date()).toISOString();
    console.log('[AWB Workbench] awb_inventory.js loading... marker=v3', _ts);
    try {
        // small stack snippet to help identify load origin
        const stack = (new Error()).stack || '';
        console.log('[AWB Workbench] load stack (snippet):', stack.split('\n').slice(1,4));
    } catch(e) {
        // ignore
    }
    // set a global marker so manual checks from console are easy
    try { window.__awb_inventory_js_marker = 'awb_inventory_js_loaded_' + _ts; } catch(e) {}
}

// ====================================================================== //
//  Status colour map (shared)
// ====================================================================== //
const AWB_STATUS_COLOUR = {
    "Available":   "green",
    "Assigned":    "blue",
    "Withdrawn":   "orange",
    "Void":        "red",
    "Hold":        "yellow",
    "Blacklisted": "darkgrey",
};

const AWB_BADGE_CSS = {
    "Available":   "background:#d4edda;color:#155724;",
    "Assigned":    "background:#cce5ff;color:#004085;",
    "Withdrawn":   "background:#ffe8cc;color:#7a4100;",
    "Void":        "background:#f8d7da;color:#721c24;",
    "Hold":        "background:#fff3cd;color:#856404;",
    "Blacklisted": "background:#e2e3e5;color:#383d41;",
};

// ====================================================================== //
//  Safe Initialization — register hooks using available ready helpers
// ====================================================================== //
(function awb_safe_init(){
    function setup_listview_and_form() {
        try {
            // Listview settings
            frappe.listview_settings["AWB Inventory"] = {
                onload(listview) {
                    if (typeof console !== 'undefined') {
                        console.log('[AWB Workbench] Listview onload hook fired');
                    }

                    // Add Workbench button to toolbar
                    try {
                        listview.page.add_button(__("Workbench"), () => {
                            if (typeof console !== 'undefined') {
                                console.log('[AWB Workbench] Workbench button clicked');
                            }
                            if (typeof awb_open_workbench === 'function') {
                                awb_open_workbench(listview);
                            }
                        }, "primary");
                    } catch (e) {
                        if (typeof console !== 'undefined') console.warn('[AWB Workbench] add_button failed', e);
                    }
                },

                get_indicator(doc) {
                    const c = AWB_STATUS_COLOUR[doc.status] || "grey";
                    return [__(doc.status), c, "status,=," + doc.status];
                },
            };

            // Form view hook
            try {
                frappe.ui.form.on("AWB Inventory", {
                    refresh(frm) {
                        if (frm.doc.status) {
                            frm.page.set_indicator(
                                frm.doc.status,
                                AWB_STATUS_COLOUR[frm.doc.status] || "grey"
                            );
                        }
                    }
                });
            } catch (e) {
                if (typeof console !== 'undefined') console.warn('[AWB Workbench] form hook registration failed', e);
            }
        } catch (e) {
            if (typeof console !== 'undefined') console.error('[AWB Workbench] setup failed', e);
        }
    }

    // Prefer frappe.ready if available, otherwise fall back to jQuery or window load
    if (typeof frappe !== 'undefined' && typeof frappe.ready === 'function') {
        try { frappe.ready(setup_listview_and_form); } catch (e) { setup_listview_and_form(); }
    } else if (typeof $ !== 'undefined' && $.fn && $.fn.ready) {
        $(document).ready(setup_listview_and_form);
    } else {
        // Last resort: attempt immediate setup, wrapped in try/catch
        try { setup_listview_and_form(); } catch (e) {
            if (typeof console !== 'undefined') console.error('[AWB Workbench] Error during initialization:', e);
        }
    }
})();

// ====================================================================== //
//  Global Workbench Handler
// ====================================================================== //
window.open_awb_workbench = function open_awb_workbench() {
    if (typeof console !== 'undefined') {
        console.log('[AWB Workbench] open_awb_workbench called');
    }
    if (typeof cur_list !== 'undefined' && cur_list && cur_list.doctype === "AWB Inventory") {
        if (typeof awb_open_workbench === 'function') {
            awb_open_workbench(cur_list);
        }
    }
};

// ====================================================================== //
//  ── Phase 3: AWB Workbench Dialog ──────────────────────────────────── //
//  Flow: Mode/Action Input → Preview Grid → Confirm → Execute/Enqueue   //
//        → Progress Modal → Results + CSV download + Undo link           //
// ====================================================================== //

function awb_open_workbench(listview) {
    const selected_docs = listview ? listview.get_checked_items() : [];
    const selected_names = selected_docs.map(r => r.name);

    /* ── Step 1: Input dialog ─────────────────────────────────────── */
    const input_dialog = new frappe.ui.Dialog({
        title: __("AWB Inventory Workbench"),
        size:  "large",
        fields: [
            /* ── Header note ── */
            {
                fieldname: "wb_note",
                fieldtype: "HTML",
                options: `<div style="background:#f4f8ff;border-left:4px solid #1a3c5e;
                            padding:10px 14px;border-radius:4px;margin-bottom:4px;
                            font-size:11px;color:#1a3c5e;">
                    <strong>${__("AWB Inventory Workbench")}</strong> — 
                    ${__("Assign, Withdraw, Hold, Void or Blacklist AWBs in Single, Range or Selected mode.")}
                    ${__("Click Preview to validate before applying changes.")}
                </div>`,
            },
            /* ── Section: Operation ── */
            { fieldname: "sec_op", fieldtype: "Section Break", label: __("Operation") },
            {
                fieldname: "new_status",
                fieldtype: "Select",
                label: __("Action"),
                options: [
                    "Assigned",
                    "Withdrawn",
                    "Hold",
                    "Void",
                    "Blacklisted",
                ].join("\n"),
                reqd: 1,
            },
            { fieldname: "cb_op1", fieldtype: "Column Break" },
            {
                fieldname: "mode",
                fieldtype: "Select",
                label: __("Mode"),
                options: "Range\nSingle\nSelected",
                default: selected_names.length ? "Selected" : "Range",
                reqd: 1,
                onchange() { awb_toggle_mode_fields(input_dialog, selected_names); },
            },
            /* ── Section: Targeting ── */
            { fieldname: "sec_tgt", fieldtype: "Section Break", label: __("Targeting") },
            /* Single */
            {
                fieldname: "single_awb",
                fieldtype: "Data",
                label: __("Full AWB Number"),
                description: __("E.g. 157-0000001-1"),
                depends_on: "eval:doc.mode === 'Single'",
            },
            /* Range */
            {
                fieldname: "range_prefix",
                fieldtype: "Data",
                label: __("AWB Prefix"),
                description: __("3-digit carrier code, e.g. 157"),
                depends_on: "eval:doc.mode === 'Range'",
            },
            { fieldname: "cb_r1", fieldtype: "Column Break" },
            {
                fieldname: "range_start",
                fieldtype: "Data",
                label: __("Serial Start"),
                description: __("7-digit, e.g. 0000001"),
                depends_on: "eval:doc.mode === 'Range'",
            },
            { fieldname: "cb_r2", fieldtype: "Column Break" },
            {
                fieldname: "range_end",
                fieldtype: "Data",
                label: __("Serial End"),
                description: __("7-digit, e.g. 0000100"),
                depends_on: "eval:doc.mode === 'Range'",
            },
            /* Selected — read-only count */
            {
                fieldname: "selected_info",
                fieldtype: "HTML",
                depends_on: "eval:doc.mode === 'Selected'",
                options: `<div style="padding:8px 0;font-size:11px;color:#1a3c5e;">
                    <strong>${selected_names.length}</strong> ${__("AWB(s) selected from list view.")}
                    ${selected_names.length === 0
                        ? `<span style="color:#dc3545;"> ${__("⚠ No rows checked — please check rows in the list first.")}</span>`
                        : ""}
                </div>`,
            },
            /* ── Section: Details ── */
            { fieldname: "sec_det", fieldtype: "Section Break", label: __("Details") },
            {
                fieldname: "customer",
                fieldtype: "Link",
                options: "Customer",
                label: __("Assign To Customer"),
                depends_on: "eval:doc.new_status === 'Assigned'",
            },
            { fieldname: "cb_d1", fieldtype: "Column Break" },
            {
                fieldname: "reason",
                fieldtype: "Small Text",
                label: __("Reason / Notes"),
                description: __("Required for Withdraw, Void, Blacklist"),
            },
            { fieldname: "cb_d2", fieldtype: "Column Break" },
            {
                fieldname: "force",
                fieldtype: "Check",
                label: __("Force Transition (Admin Only)"),
                description: __("Override transition rules — logged in audit trail"),
            },
        ],
        primary_action_label: __("Preview"),
        secondary_action_label: __("Cancel"),
        secondary_action() { input_dialog.hide(); },

        primary_action(values) {
            /* Validate required fields before calling server */
            if (values.mode === "Selected" && !selected_names.length) {
                frappe.msgprint({
                    message: __("Please check at least one AWB row in the list view first."),
                    indicator: "red",
                });
                return;
            }
            if (values.new_status === "Assigned" && !values.customer) {
                input_dialog.set_df_property("customer", "reqd", 1);
                input_dialog.refresh();
                frappe.msgprint({
                    message: __("Customer is required when assigning AWBs. Please select a customer from the field below."),
                    indicator: "red",
                    title: __("Customer Not Selected")
                });
                return;
            }
            if (["Withdrawn", "Void", "Blacklisted"].includes(values.new_status) && !values.reason) {
                frappe.msgprint({
                    message: `${__("Reason is required for")} ${values.new_status} ${__("action.")}`,
                    indicator: "orange",
                });
                return;
            }

            input_dialog.hide();
            awb_do_preview(input_dialog, listview, selected_names, values);
        },
    });

    input_dialog.show();
    // Pre-select mode if rows were already checked
    if (selected_names.length) {
        input_dialog.set_value("mode", "Selected");
    }
    awb_toggle_mode_fields(input_dialog, selected_names);
}

/* ── Toggle conditional inputs visibility ──────────────────────────── */
function awb_toggle_mode_fields(dialog, selected_names) {
    // Frappe depends_on handles visibility; we just refresh
    dialog.refresh();
    // Rebuild selected info HTML dynamically
    const mode = dialog.get_value("mode");
    if (mode === "Selected") {
        const html = `<div style="padding:8px 0;font-size:11px;color:#1a3c5e;">
            <strong>${selected_names.length}</strong> ${__("AWB(s) selected from list view.")}
            ${selected_names.length === 0
                ? `<span style="color:#dc3545;"> ${__("⚠ No rows checked — please check rows in the list first.")}</span>`
                : ""}
        </div>`;
        dialog.get_field("selected_info").html(html);
    }
}

/* ── Step 2: Call preview API and render grid ───────────────────────── */
function awb_do_preview(input_dialog, listview, selected_names, values) {
    // Validate that customer is present before making API call
    if (values.new_status === "Assigned" && !values.customer) {
        frappe.msgprint({
            message: __("Customer is required when assigning AWBs."),
            indicator: "red",
            title: __("Customer Not Selected")
        });
        return;
    }
    
    const args = awb_build_args(values, selected_names, { dry_run: false });
    args.force = values.force ? 1 : 0;

    frappe.call({
        method: "cargoxy.awb.api.awb_actions.preview_awb_operation",
        args:   args,
        freeze: true,
        freeze_message: __("Generating preview…"),
        callback(r) {
            if (!r.message) return;
            awb_show_preview_dialog(r.message, input_dialog, listview, selected_names, values);
        },
        error(r) {
            frappe.msgprint({
                message: r.responseText || __("Error generating preview"),
                indicator: "red",
                title: __("Preview Failed")
            });
        }
    });
}

/* ── Preview Dialog with per-item grid ───────────────────────────────── */
function awb_show_preview_dialog(preview, input_dialog, listview, selected_names, values) {
    const counts = preview.counts || {};
    const items  = preview.items  || [];

    /* Summary bar */
    const sum_color  = counts.blocked > 0 ? "#fff3cd" : "#d4edda";
    const sum_border = counts.blocked > 0 ? "#ffc107" : "#28a745";

    /* Table rows */
    const rows_html = items.map((item, idx) => {
        const badge_css   = AWB_BADGE_CSS[item.current_status] || "";
        const allowed_icon = item.allowed
            ? `<span style="color:#155724;font-weight:700;">✓</span>`
            : `<span style="color:#721c24;font-weight:700;">✗</span>`;
        const row_bg = idx % 2 === 0 ? "#fff" : "#f9fbff";
        return `<tr style="border-bottom:1px solid #e0e8f5;background:${row_bg};">
            <td style="padding:5px 8px;text-align:center;">${allowed_icon}</td>
            <td style="padding:5px 8px;font-weight:700;font-size:10.5px;">${item.full_awb_number}</td>
            <td style="padding:5px 8px;">
                <span style="padding:2px 8px;border-radius:10px;font-size:9.5px;
                             font-weight:700;${badge_css}">${__(item.current_status)}</span>
            </td>
            <td style="padding:5px 8px;font-size:10px;color:${item.allowed ? "#555" : "#721c24"};">
                ${item.reason || (item.allowed ? __("Will be updated") : "")}
            </td>
        </tr>`;
    }).join("");

    const grid_html = `
    <div style="font-family:'Segoe UI',Arial,sans-serif;font-size:11px;">
        <!-- Summary bar -->
        <div style="display:flex;gap:10px;margin-bottom:12px;flex-wrap:wrap;">
            <div style="flex:1;padding:8px 12px;background:#d4edda;border:1px solid #c3e6cb;
                        border-radius:4px;text-align:center;">
                <div style="font-size:20px;font-weight:700;color:#155724;">${counts.will_update}</div>
                <div style="font-size:10px;color:#155724;">${__("Will Update")}</div>
            </div>
            <div style="flex:1;padding:8px 12px;background:#f8d7da;border:1px solid #f5c6cb;
                        border-radius:4px;text-align:center;">
                <div style="font-size:20px;font-weight:700;color:#721c24;">${counts.blocked}</div>
                <div style="font-size:10px;color:#721c24;">${__("Blocked")}</div>
            </div>
            <div style="flex:1;padding:8px 12px;background:#e8f0fb;border:1px solid #c5d4e8;
                        border-radius:4px;text-align:center;">
                <div style="font-size:20px;font-weight:700;color:#1a3c5e;">${counts.total}</div>
                <div style="font-size:10px;color:#1a3c5e;">${__("Total")}</div>
            </div>
        </div>
        <!-- Per-item table -->
        <div style="max-height:320px;overflow-y:auto;border:1px solid #c5d4e8;border-radius:4px;">
            <table style="width:100%;border-collapse:collapse;">
                <thead>
                    <tr style="background:#1a3c5e;color:#fff;position:sticky;top:0;">
                        <th style="padding:7px 8px;font-size:10px;font-weight:700;width:32px;">&nbsp;</th>
                        <th style="padding:7px 8px;font-size:10px;font-weight:700;">${__("AWB Number")}</th>
                        <th style="padding:7px 8px;font-size:10px;font-weight:700;">${__("Current Status")}</th>
                        <th style="padding:7px 8px;font-size:10px;font-weight:700;">${__("Note")}</th>
                    </tr>
                </thead>
                <tbody>${rows_html}</tbody>
            </table>
        </div>
        ${counts.blocked > 0 ? `
        <div style="margin-top:10px;padding:8px 12px;background:#fff3cd;border:1px solid #ffc107;
                    border-radius:4px;font-size:10px;color:#856404;">
            ⚠ ${__("{0} AWB(s) are blocked and will be skipped. Only the {1} allowed will be updated.",
                [counts.blocked, counts.will_update])}
        </div>` : ""}
        ${values.new_status === "Assigned" && values.customer ? `
        <div style="margin-top:10px;padding:8px 12px;background:#d4edda;border:1px solid #c3e6cb;
                    border-radius:4px;font-size:10px;color:#155724;font-weight:700;">
            ✓ ${__("Customer to assign:")} <strong>${values.customer}</strong>
        </div>` : ""}
    </div>`;

    const preview_dialog = new frappe.ui.Dialog({
        title: __("Preview — {0} → {1}", [__("Status Change"), __(values.new_status)]),
        size:  "large",
        fields: [
            { fieldname: "grid_html",   fieldtype: "HTML",       options: grid_html },
            { fieldname: "sec_confirm", fieldtype: "Section Break", label: __("Confirm") },
            values.new_status === "Assigned" ? {
                fieldname: "preview_customer",
                fieldtype: "Link",
                options: "Customer",
                label: __("Assigned Customer (Read-only)"),
                default: values.customer,
                read_only: 1,
            } : { fieldname: "spacer1", fieldtype: "Column Break" },
            {
                fieldname: "confirm_reason",
                fieldtype: "Small Text",
                label: __("Confirm Reason"),
                description: __("Describe why you are making these changes."),
                default: values.reason || "",
            },
        ],
        primary_action_label: counts.will_update > 0
            ? __("Proceed — Update {0} AWB(s)", [counts.will_update])
            : __("Nothing to Update"),
        secondary_action_label: __("← Back"),
        secondary_action() {
            preview_dialog.hide();
            input_dialog.show();
        },

        primary_action(confirm_vals) {
            if (!counts.will_update) {
                frappe.show_alert({ message: __("No AWBs to update."), indicator: "orange" }, 4);
                preview_dialog.hide();
                return;
            }
            preview_dialog.hide();
            awb_execute(listview, selected_names, values, confirm_vals.confirm_reason);
        },
    });

    preview_dialog.show();
}

/* ── Step 3 & 4: Execute (sync or enqueue) ───────────────────────────── */
function awb_execute(listview, selected_names, values, confirmed_reason) {
    const args = awb_build_args(values, selected_names, {
        dry_run:  false,
        enqueue:  false,  // server decides based on its async threshold
        force:    values.force ? 1 : 0,
        reason:   confirmed_reason || values.reason || "",
    });
    
    // Ensure customer is preserved and explicitly passed for Assignment
    if (values.new_status === "Assigned" && values.customer) {
        args.customer = values.customer;
    }

    frappe.call({
        method: "cargoxy.awb.api.awb_actions.bulk_update_awb_status",
        args:   args,
        freeze: true,
        freeze_message: __("Saving…"),
        callback(r) {
            if (!r.message) return;
            const msg = r.message;
            if (msg.enqueued) {
                /* ── Large batch: show progress modal ─────────────── */
                awb_show_progress(msg.operation_id, listview);
            } else {
                /* ── Small batch: show results directly ───────────── */
                awb_show_results(msg, null, listview);
            }
        },
    });
}

/* ── Progress modal (Phase 4) ────────────────────────────────────────── */
function awb_show_progress(operation_id, listview) {
    const progress_html = `
    <div id="awb-progress-wrap" style="font-family:'Segoe UI',Arial;padding:12px;">
        <p style="color:#1a3c5e;font-weight:700;margin:0 0 10px 0;">
            ${__("Processing AWBs in background…")}
        </p>
        <!-- Progress bar -->
        <div style="width:100%;height:22px;background:#e8f0fb;border-radius:4px;
                    overflow:hidden;border:1px solid #c5d4e8;margin-bottom:6px;">
            <div id="awb-prog-bar"
                 style="width:0%;height:100%;background:linear-gradient(90deg,#1a3c5e,#2d6a9f);
                        transition:width 0.4s ease;"></div>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:10px;color:#666;margin-bottom:10px;">
            <span id="awb-prog-pct">0%</span>
            <span id="awb-prog-counts">0 / 0</span>
        </div>
        <!-- Live log -->
        <div id="awb-prog-log"
             style="max-height:160px;overflow-y:auto;background:#f9fbff;
                    border:1px solid #c5d4e8;border-radius:4px;padding:8px 10px;
                    font-size:9.5px;font-family:monospace;color:#333;line-height:1.7;">
        </div>
    </div>`;

    const prog_dialog = new frappe.ui.Dialog({
        title: __("Operation in Progress"),
        size:  "large",
        fields: [{ fieldname: "prog_html", fieldtype: "HTML", options: progress_html }],
        secondary_action_label: __("Cancel Operation"),
        secondary_action() {
            frappe.call({
                method: "cargoxy.awb.api.awb_actions.cancel_bulk_operation",
                args:   { operation_id },
            });
        },
    });
    prog_dialog.show();

    /* Realtime progress subscription */
    const on_progress = (data) => {
        if (data.operation_id !== operation_id) return;
        const pct = data.progress || 0;
        const bar = prog_dialog.$wrapper.find("#awb-prog-bar");
        const pct_el = prog_dialog.$wrapper.find("#awb-prog-pct");
        const cnt_el = prog_dialog.$wrapper.find("#awb-prog-counts");
        const log_el = prog_dialog.$wrapper.find("#awb-prog-log");
        bar.css("width", pct + "%");
        pct_el.text(pct + "%");
        cnt_el.text(`${data.processed || 0} / ${data.total || 0}`);
        if (data.message) {
            const ts = frappe.datetime.now_time();
            log_el.append(`<div>${ts} — ${data.message}</div>`);
            log_el.scrollTop(log_el[0].scrollHeight);
        }
    };

    const on_finished = (data) => {
        if (data.operation_id !== operation_id) return;
        frappe.realtime.off("awb_bulk_progress", on_progress);
        frappe.realtime.off("awb_bulk_finished", on_finished);
        prog_dialog.hide();
        if (data.error) {
            frappe.msgprint({ message: data.error, indicator: "red", title: __("Operation Failed") });
        } else {
            // Fetch final status to get CSV link
            frappe.call({
                method: "cargoxy.awb.api.awb_actions.get_bulk_operation_status",
                args:   { operation_id },
                callback(r) {
                    if (r.message) awb_show_results(r.message, operation_id, listview);
                },
            });
        }
    };

    frappe.realtime.on("awb_bulk_progress", on_progress);
    frappe.realtime.on("awb_bulk_finished", on_finished);

    /* Fallback poll every 3 s in case realtime is unavailable */
    const poll_id = setInterval(() => {
        frappe.call({
            method: "cargoxy.awb.api.awb_actions.get_bulk_operation_status",
            args:   { operation_id },
            callback(r) {
                if (!r.message) return;
                const st = r.message.status;
                on_progress({
                    operation_id,
                    progress:  r.message.progress,
                    processed: r.message.processed,
                    total:     r.message.total,
                    message:   null,
                });
                if (st === "Completed" || st === "Failed" || st === "Cancelled") {
                    clearInterval(poll_id);
                    on_finished({ operation_id, error: st === "Failed" ? __("Operation failed.") : null });
                }
            },
        });
    }, 3000);
}

/* ── Results dialog ─────────────────────────────────────────────────── */
function awb_show_results(result, operation_id, listview) {
    /* result may be per-item {items, counts} or get_bulk_operation_status snapshot */
    const updated = result.counts  ? result.counts.updated    :
                    result.updated ? result.updated            : (result.processed || 0);
    const failed  = result.counts  ? result.counts.failed     :
                    result.errors  ? result.errors             : 0;
    const csv_link = result.result_file
        ? `<a href="/private/files/${result.result_file.split("AWB_Operation_")[1] || ""}"
               target="_blank" style="color:#004085;text-decoration:underline;">
               ${__("Download Summary CSV")}</a>`
        : "";

    const results_html = `
    <div style="font-family:'Segoe UI',Arial;font-size:11px;">
        <!-- Counts -->
        <div style="display:flex;gap:10px;margin-bottom:16px;">
            <div style="flex:1;padding:10px 14px;background:#d4edda;border:1px solid #c3e6cb;
                        border-radius:4px;text-align:center;">
                <div style="font-size:22px;font-weight:700;color:#155724;">✓ ${updated}</div>
                <div style="font-size:10px;color:#155724;">${__("Updated Successfully")}</div>
            </div>
            ${failed > 0 ? `
            <div style="flex:1;padding:10px 14px;background:#f8d7da;border:1px solid #f5c6cb;
                        border-radius:4px;text-align:center;">
                <div style="font-size:22px;font-weight:700;color:#721c24;">✗ ${failed}</div>
                <div style="font-size:10px;color:#721c24;">${__("Skipped / Failed")}</div>
            </div>` : ""}
        </div>
        <!-- Errors preview (first 5) -->
        ${(result.items || []).filter(i => !i.success).slice(0, 5).map(i =>
            `<div style="padding:5px 10px;background:#fff3cd;border-left:4px solid #ffc107;
                         border-radius:2px;margin-bottom:4px;font-size:10px;color:#856404;">
                <strong>${i.full_awb_number}</strong>: ${i.message}
             </div>`
        ).join("")}
        <!-- CSV & Undo links -->
        <div style="margin-top:12px;display:flex;gap:12px;flex-wrap:wrap;font-size:10.5px;">
            ${result.result_file ? `
            <a href="/app/file/${result.result_file}" target="_blank"
               style="padding:6px 14px;background:#1a3c5e;color:#fff;border-radius:4px;
                      text-decoration:none;font-weight:700;">
                📥 ${__("Download CSV")}
            </a>` : ""}
            ${operation_id ? `
            <button id="awb-undo-btn"
                    style="padding:6px 14px;background:#fff;color:#dc3545;border:1px solid #dc3545;
                           border-radius:4px;cursor:pointer;font-size:10.5px;font-weight:700;">
                ↩ ${__("Undo This Operation")}
            </button>` : ""}
        </div>
    </div>`;

    const res_dialog = new frappe.ui.Dialog({
        title: __("Operation Complete"),
        size:  "large",
        fields: [{ fieldname: "res_html", fieldtype: "HTML", options: results_html }],
        primary_action_label: __("Close"),
        primary_action() { res_dialog.hide(); },
    });
    res_dialog.show();

    if (operation_id) {
        res_dialog.$wrapper.find("#awb-undo-btn").on("click", () => {
            frappe.confirm(
                __("This will revert all {0} changes from this operation. Continue?", [updated]),
                () => awb_do_undo(operation_id, res_dialog, listview)
            );
        });
    }

    if (listview) listview.refresh();
}

/* ── Undo handler ────────────────────────────────────────────────────── */
function awb_do_undo(operation_id, res_dialog, listview) {
    frappe.call({
        method: "cargoxy.awb.api.awb_actions.undo_bulk_operation",
        args:   { operation_id },
        freeze: true,
        freeze_message: __("Reverting…"),
        callback(r) {
            res_dialog.hide();
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: r.message.message,
                    indicator: "green",
                }, 6);
            }
            if (listview) listview.refresh();
        },
    });
}

/* ── Build API args from dialog values ───────────────────────────────── */
function awb_build_args(values, selected_names, overrides) {
    const base = {
        mode:       (values.mode || "range").toLowerCase(),
        new_status: values.new_status,
        customer:   values.customer   || "",   // empty string → Python falsy, never "null"
        reason:     values.reason     || "",
        force:      values.force      ? 1 : 0,
    };
    if (values.mode === "Single") {
        base.full_awb_number = values.single_awb;
    } else if (values.mode === "Range") {
        base.awb_prefix   = values.range_prefix;
        base.serial_start = values.range_start;
        base.serial_end   = values.range_end;
    } else if (values.mode === "Selected") {
        base.names = selected_names;
    }
    return Object.assign(base, overrides);
}
