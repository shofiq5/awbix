// Copyright (c) 2026, Shofiq and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shipment", {
	volume_amount(frm) {
		// Recalculate volume_weight and chargeable_weight when volume_amount changes.
		// With dimensions: take max(dim_volume_weight, volume_amount_derived_vw).
		// Without dimensions: derive volume_weight solely from volume_amount.
		const dim_rows = frm.doc.dimensions || [];
		frappe.call({
			method: "awbix.shipment.doctype.shipment.shipment.calculate_dimension_totals",
			args: {
				rows: JSON.stringify(dim_rows.map((r) => ({
					pieces: r.pieces,
					length: r.length,
					width: r.width,
					height: r.height,
					dim_unit: r.dim_unit,
				}))),
				weight: frm.doc.weight || 0,
				volume_weight_factor: frm.doc.volume_weight_factor || 6000,
				volume_amount: frm.doc.volume_amount || 0,
				volume_code: frm.doc.volume_code || null,
			},
			callback(r) {
				if (!r.message) return;
				const t = r.message;
				frm.set_value("volume_weight", t.volume_weight || 0);
				frm.set_value("chargeable_weight", t.chargeable_weight || 0);
			},
		});
	},

	auto_rate_line(frm) {
		frm.clear_table("rate_lines");
		const row = frm.add_child("rate_lines");
		row.line_number = 1;
		row.number_of_pieces = frm.doc.number_of_pieces;
		row.gross_weight_code = frm.doc.weight_code;
		row.gross_weight = frm.doc.weight;
		row.rate_class_code = "Q";
		row.chargeable_weight = frm.doc.chargeable_weight;
		row.description = frm.doc.nature_of_goods;
		row.goods_data_identifier = frm.doc.console ? "C" : "G";
		row.commodity_item_number = frm.doc.commodity_item_no;
		const iata_rate = frm.doc.iata_rate || 0;
		row.rate_charge = iata_rate;
		row.total =
			row.rate_class_code === "Q"
				? iata_rate * (row.chargeable_weight || 0)
				: iata_rate;
		frm.refresh_field("rate_lines");
	},

	refresh(frm) {
		// Dimension button — available on new and saved docs.
		frm.add_custom_button(__("Dimension"), () => open_dimension_dialog(frm));

		if (frm.is_new()) {
			frappe.db.get_single_value("Shipment Settings", "default_origin").then(() => {
				frappe.model.with_doc("Shipment Settings", "Shipment Settings", () => {
					const s = frappe.get_doc("Shipment Settings", "Shipment Settings");
					if (!frm.doc.origin && s.default_origin)
						frm.set_value("origin", s.default_origin);
					if (!frm.doc.destination && s.default_destination)
						frm.set_value("destination", s.default_destination);
					if (!frm.doc.agent && s.default_agent)
						frm.set_value("agent", s.default_agent);
					if (!frm.doc.sender_office_address && s.default_sender_office_message_address)
						frm.set_value("sender_office_address", s.default_sender_office_message_address);
					if (!frm.doc.currency && s.default_currency)
						frm.set_value("currency", s.default_currency);
				});
			});
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

// ---------------------------------------------------------------------------
// Dimension Dialog
// ---------------------------------------------------------------------------

const DIM_TEMPLATE_CSV = "Line,Pieces,Length,Width,Height,Unit\n1,1,,,, cm\n";

function open_dimension_dialog(frm) {
	// Seed dialog grid from the hidden child table already on the doc.
	const seed_rows = (frm.doc.dimensions || []).map((r) => ({
		line_number: r.line_number,
		pieces: r.pieces || 1,
		length: r.length || 0,
		width: r.width || 0,
		height: r.height || 0,
		dim_unit: r.dim_unit || "cm",
		volume: r.volume || 0,
		volume_weight: r.volume_weight || 0,
		remarks: r.remarks || "",
	}));

	// Build the dialog rows table HTML (editable).
	const dialog = new frappe.ui.Dialog({
		title: __("Shipment Dimensions"),
		size: "extra-large",
		fields: [
			// ---- Upload section ----
			{
				fieldname: "upload_section",
				fieldtype: "Section Break",
				label: __("Import from CSV / Excel"),
				collapsible: 1,
			},
			{
				fieldname: "dim_file",
				fieldtype: "Attach",
				label: __("Upload CSV / Excel"),
				description: __("Accepted: .csv, .xlsx, .xls — columns: pieces, length, width, height, unit"),
			},
			{
				fieldname: "cb_upload",
				fieldtype: "Column Break",
			},
			{
				fieldname: "upload_btn",
				fieldtype: "Button",
				label: __("Parse & Add Rows"),
			},
			{
				fieldname: "template_btn",
				fieldtype: "Button",
				label: __("Download Template"),
			},
			// ---- Grid section ----
			{
				fieldname: "dim_section",
				fieldtype: "Section Break",
				label: __("Dimension Lines"),
			},
			{
				fieldname: "dim_grid_html",
				fieldtype: "HTML",
				options: build_grid_html(seed_rows),
			},
			// ---- Totals section ----
			{
				fieldname: "totals_section",
				fieldtype: "Section Break",
				label: __("Totals"),
			},
			{
				fieldname: "total_volume_m3",
				fieldtype: "Float",
				label: __("Total Volume (m³)"),
				precision: 4,
				read_only: 1,
			},
			{
				fieldname: "cb_totals",
				fieldtype: "Column Break",
			},
			{
				fieldname: "total_volume_weight",
				fieldtype: "Float",
				label: __("Volume Weight (kg)"),
				precision: 2,
				read_only: 1,
			},
			{
				fieldname: "cb_totals2",
				fieldtype: "Column Break",
			},
			{
				fieldname: "total_chargeable_weight",
				fieldtype: "Float",
				label: __("Chargeable Weight (kg)"),
				precision: 2,
				read_only: 1,
			},
			// ---- Error section (hidden until needed) ----
			{
				fieldname: "error_section",
				fieldtype: "Section Break",
				label: __("Parse Errors"),
				hidden: 1,
			},
			{
				fieldname: "error_html",
				fieldtype: "HTML",
				options: "",
				hidden: 1,
			},
		],
		primary_action_label: __("Apply"),
		primary_action() {
			const rows = collect_grid_rows(dialog);
			apply_rows_to_frm(frm, rows);
			refresh_totals(frm, dialog, rows);
			dialog.hide();
		},
	});

	dialog.show();

	// Wire up buttons after show.
	dialog.fields_dict.upload_btn.$input.on("click", () => handle_upload(frm, dialog));
	dialog.fields_dict.template_btn.$input.on("click", () => download_template());

	// Delegate change events on the inline grid (change + input for immediate feedback).
	const _recalc = frappe.utils.debounce(() => {
		const rows = collect_grid_rows(dialog);
		refresh_totals(frm, dialog, rows);
	}, 300);
	dialog.$wrapper.on("change input", ".dim-grid-input", _recalc);

	// Add Row — delegated on the dialog wrapper so it fires even after DOM is ready.
	dialog.$wrapper.on("click", ".dim-add-row", () => {
		const tbody = dialog.$wrapper[0].querySelector("#dim-grid-body");
		if (!tbody) return;
		const idx = tbody.rows.length;
		const tr = document.createElement("tr");
		tr.innerHTML = build_row_inner_html({}, idx);
		tbody.appendChild(tr);
		_recalc();
	});

	// Delete Row — delegated.
	dialog.$wrapper.on("click", ".dim-del-row", function () {
		$(this).closest("tr").remove();
		// renumber
		const tbody = dialog.$wrapper[0].querySelector("#dim-grid-body");
		if (tbody) {
			Array.from(tbody.rows).forEach((row, i) => {
				const ln = row.querySelector(".dim-line");
				if (ln) ln.value = i + 1;
			});
		}
		_recalc();
	});

	// Initial totals render.
	refresh_totals(frm, dialog, seed_rows);
}

// ---------------------------------------------------------------------------
// Grid HTML builder
// ---------------------------------------------------------------------------

function build_grid_html(rows) {
	const head = `
		<div style="overflow-x:auto">
		<table class="table table-bordered table-condensed dim-grid" style="min-width:700px">
		<thead><tr>
			<th style="width:50px">${__("Line")}</th>
			<th style="width:70px">${__("Pcs")}</th>
			<th>${__("Length")}</th>
			<th>${__("Width")}</th>
			<th>${__("Height")}</th>
			<th style="width:70px">${__("Unit")}</th>
			<th style="width:90px">${__("Vol m³")}</th>
			<th style="width:110px">${__("Row Vol Wt kg")}</th>
			<th style="width:60px"></th>
		</tr></thead>
		<tbody id="dim-grid-body">`;

	const body = (rows.length ? rows : [{}]).map((r, i) => build_row_html(r, i)).join("");

	const foot = `</tbody></table>
		<button class="btn btn-xs btn-default dim-add-row" style="margin-top:6px">
			+ ${__("Add Row")}
		</button>
		</div>`;

	// No inline <script> — add-row / delete-row are wired via dialog.$wrapper delegation in open_dimension_dialog.
	return `<div class="dim-grid-wrapper">${head}${body}${foot}</div>`;
}

/** Returns only the <td>…</td> cells (no <tr> wrapper) — used by the add-row handler. */
function build_row_inner_html(r, i) {
	const line = r.line_number || i + 1;
	const unit_opts = ["cm", "in", "m"]
		.map((u) => `<option value="${u}"${(r.dim_unit || "cm") === u ? " selected" : ""}>${u}</option>`)
		.join("");
	return `
		<td><input class="form-control input-xs dim-grid-input dim-line" type="number" min="1" value="${line}" style="width:50px"></td>
		<td><input class="form-control input-xs dim-grid-input dim-pieces" type="number" min="1" value="${r.pieces || 1}" style="width:60px"></td>
		<td><input class="form-control input-xs dim-grid-input dim-length" type="number" min="0" step="0.01" value="${r.length || ""}" placeholder="0"></td>
		<td><input class="form-control input-xs dim-grid-input dim-width" type="number" min="0" step="0.01" value="${r.width || ""}" placeholder="0"></td>
		<td><input class="form-control input-xs dim-grid-input dim-height" type="number" min="0" step="0.01" value="${r.height || ""}" placeholder="0"></td>
		<td><select class="form-control input-xs dim-grid-input dim-unit" style="width:60px">${unit_opts}</select></td>
		<td><input class="form-control input-xs dim-vol" type="number" step="0.0001" value="${r.volume || ""}" readonly style="background:#f5f5f5"></td>
		<td><input class="form-control input-xs dim-vw" type="number" step="0.01" value="${r.volume_weight || ""}" readonly style="background:#f5f5f5"></td>
		<td><button class="btn btn-xs btn-danger dim-del-row" title="${__("Remove")}">✕</button></td>`;
}

/** Returns a full <tr>…</tr> row — used for the initial grid build. */
function build_row_html(r, i) {
	return `<tr>${build_row_inner_html(r, i)}</tr>`;
}

// ---------------------------------------------------------------------------
// Collect rows from dialog grid DOM
// ---------------------------------------------------------------------------

function collect_grid_rows(dialog) {
	const tbody = dialog.$wrapper[0].querySelector("#dim-grid-body");
	if (!tbody) return [];
	const rows = [];
	Array.from(tbody.rows).forEach((tr, i) => {
		const get = (cls) => {
			const el = tr.querySelector(cls);
			return el ? el.value : "";
		};
		const pieces = parseInt(get(".dim-pieces") || 1, 10) || 1;
		const length = parseFloat(get(".dim-length")) || 0;
		const width = parseFloat(get(".dim-width")) || 0;
		const height = parseFloat(get(".dim-height")) || 0;
		const dim_unit = get(".dim-unit") || "cm";
		rows.push({ line_number: i + 1, pieces, length, width, height, dim_unit });
	});
	return rows;
}

// ---------------------------------------------------------------------------
// Refresh totals via server endpoint (keeps FE/BE math identical)
// ---------------------------------------------------------------------------

function refresh_totals(frm, dialog, rows) {
	if (!rows || !rows.length) {
		dialog.set_value("total_volume_m3", 0);
		dialog.set_value("total_volume_weight", 0);
		dialog.set_value("total_chargeable_weight", 0);
		return;
	}
	frappe.call({
		method: "awbix.shipment.doctype.shipment.shipment.calculate_dimension_totals",
		args: {
			rows: JSON.stringify(rows),
			weight: frm.doc.weight || 0,
			volume_weight_factor: frm.doc.volume_weight_factor || 6000,
			volume_amount: frm.doc.volume_amount || 0,
			volume_code: frm.doc.volume_code || null,
		},
		callback(r) {
			if (!r.message) return;
			const t = r.message;

			// Update per-row computed cells in dialog grid.
			const tbody = dialog.$wrapper[0].querySelector("#dim-grid-body");
			if (tbody && t.rows) {
				Array.from(tbody.rows).forEach((tr, i) => {
					const rd = t.rows[i];
					if (!rd) return;
					const vEl = tr.querySelector(".dim-vol");
					const vwEl = tr.querySelector(".dim-vw");
					if (vEl) vEl.value = rd.volume || "";
					if (vwEl) vwEl.value = rd.volume_weight || "";
				});
			}

			dialog.set_value("total_volume_m3", t.total_volume_m3 || 0);
			dialog.set_value("total_volume_weight", t.volume_weight || 0);
			dialog.set_value("total_chargeable_weight", t.chargeable_weight || 0);
		},
	});
}

// ---------------------------------------------------------------------------
// Apply dialog rows back to the hidden child table on the form
// ---------------------------------------------------------------------------

function apply_rows_to_frm(frm, rows) {
	frm.clear_table("dimensions");
	rows.forEach((r, i) => {
		if (!r.length && !r.width && !r.height) return; // skip blank rows
		const child = frm.add_child("dimensions");
		child.line_number = i + 1;
		child.pieces = r.pieces || 1;
		child.length = r.length || 0;
		child.width = r.width || 0;
		child.height = r.height || 0;
		child.dim_unit = r.dim_unit || "cm";
	});
	frm.refresh_field("dimensions");

	// Preview the totals on the parent form fields immediately.
	if (!rows.length) return;
	frappe.call({
		method: "awbix.shipment.doctype.shipment.shipment.calculate_dimension_totals",
		args: {
			rows: JSON.stringify(rows),
			weight: frm.doc.weight || 0,
			volume_weight_factor: frm.doc.volume_weight_factor || 6000,
			volume_amount: frm.doc.volume_amount || 0,
			volume_code: frm.doc.volume_code || null,
		},
		callback(r) {
			if (!r.message) return;
			const t = r.message;
			frm.set_value("volume_weight", t.volume_weight || 0);
			frm.set_value("chargeable_weight", t.chargeable_weight || 0);
			if (t.suggested_volume_amount != null) {
				frm.set_value("volume_amount", t.suggested_volume_amount);
			}
		},
	});
}

// ---------------------------------------------------------------------------
// CSV / Excel upload inside dialog
// ---------------------------------------------------------------------------

function handle_upload(frm, dialog) {
	const file_url = dialog.get_value("dim_file");
	if (!file_url) {
		frappe.msgprint(__("Please attach a file first."));
		return;
	}
	frappe.call({
		method: "awbix.shipment.doctype.shipment.shipment.parse_dimension_file",
		args: { file_url },
		freeze: true,
		freeze_message: __("Parsing file…"),
		callback(r) {
			if (!r.message) return;
			const { rows, errors } = r.message;

			// Append parsed rows into the dialog grid.
			const tbody = dialog.$wrapper[0].querySelector("#dim-grid-body");
			if (tbody && rows && rows.length) {
				const offset = tbody.rows.length;
				rows.forEach((r2, i) => {
					const tr = document.createElement("tr");
					tr.innerHTML = build_row_inner_html(r2, offset + i);
					tbody.appendChild(tr);
				});
			}

			// Show errors if any.
			if (errors && errors.length) {
				const err_rows = errors
					.map((e) => `<tr><td>${e.row}</td><td>${frappe.utils.escape_html(e.message)}</td></tr>`)
					.join("");
				const html =
					`<table class="table table-bordered table-condensed" style="margin-top:8px">` +
					`<thead><tr><th>${__("Row")}</th><th>${__("Issue")}</th></tr></thead>` +
					`<tbody>${err_rows}</tbody></table>`;
				dialog.fields_dict.error_html.df.options = html;
				dialog.fields_dict.error_html.$wrapper.html(html);
				dialog.fields_dict.error_section.df.hidden = 0;
				dialog.fields_dict.error_html.df.hidden = 0;
				dialog.refresh();
			}

			// Refresh totals.
			const all_rows = collect_grid_rows(dialog);
			refresh_totals(frm, dialog, all_rows);
		},
	});
}

// ---------------------------------------------------------------------------
// Template download
// ---------------------------------------------------------------------------

function download_template() {
	const csv = "pieces,length,width,height,unit\n1,100,40,30,cm\n";
	const blob = new Blob([csv], { type: "text/csv" });
	const url = URL.createObjectURL(blob);
	const a = document.createElement("a");
	a.href = url;
	a.download = "dimension_template.csv";
	document.body.appendChild(a);
	a.click();
	document.body.removeChild(a);
	URL.revokeObjectURL(url);
}
