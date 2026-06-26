// AWB Inventory Workbench Page
// Series selection → Dashboard → Filters → Sortable Grid → Bulk Actions → History Panel

frappe.pages['awb-workbench'].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __('AWB Inventory Workbench'),
		single_column: true,
	});
	const wb = new AWBWorkbench(wrapper);
	frappe._awb_wb = wb;
};

frappe.pages['awb-workbench'].on_page_show = function (wrapper) {
	if (frappe._awb_wb && frappe._awb_wb.ready && frappe._awb_wb.series) {
		frappe._awb_wb.load_data();
	}
};

// ─────────────────────────────────────────────────────────────────────────── //

class AWBWorkbench {
	constructor(wrapper) {
		this.wrapper  = wrapper;
		this.$body    = $(wrapper).find('.page-content');
		this.ready    = false;

		// ── State ──────────────────────────────────────────────────────── //
		this.series   = '';
		this.filters  = { status: [], customer: '', search: '',
		                  date_from: '', date_to: '', range_start: '', range_end: '' };
		this.sort_by  = 'full_awb_number';
		this.sort_ord = 'asc';
		this.pg       = 1;
		this.pg_size  = 50;
		this.total    = 0;
		this.data     = [];
		this.sel      = new Set();

		this.SC = {
			Available:   { bg: '#d4edda', fg: '#155724', dot: '#28a745' },
			Assigned:    { bg: '#cce5ff', fg: '#004085', dot: '#007bff' },
			Withdrawn:   { bg: '#ffe8cc', fg: '#7a4100', dot: '#fd7e14' },
			Hold:        { bg: '#fff3cd', fg: '#856404', dot: '#ffc107' },
			Void:        { bg: '#f8d7da', fg: '#721c24', dot: '#dc3545' },
			Blacklisted: { bg: '#e2e3e5', fg: '#383d41', dot: '#6c757d' },
		};

		this._render();
		this._load_series();
		this.ready = true;
	}

	// ═══════════════════════════════════════════════════════════════════════ //
	//  Layout                                                                 //
	// ═══════════════════════════════════════════════════════════════════════ //

	_render() {
		this.$body.css('padding', '0').html(`
<div class="awb-wb" style="font-family:'Segoe UI',sans-serif;min-height:80vh;padding-bottom:80px;">

  <!-- ── Header bar ──────────────────────────────────────────────────── -->
  <div id="awb-hbar" style="background:#1a3c5e;padding:10px 18px;display:flex;
       align-items:center;gap:8px;flex-wrap:wrap;">
    <span style="color:#fff;font-weight:700;font-size:12px;white-space:nowrap;">${__('Series')}:</span>
    <select id="awb-series-sel" style="padding:5px 9px;border-radius:4px;border:none;
            font-size:11px;min-width:200px;max-width:340px;">
      <option value="">${__('— All (no series filter) —')}</option>
    </select>
    <span style="color:#adb5bd;font-size:10px;">${__('or prefix')}:</span>
    <input id="awb-prefix-in" type="text" maxlength="6" placeholder="${__('e.g. 157')}"
           style="width:64px;padding:5px 7px;border:none;border-radius:4px;font-size:11px;">
    <button id="awb-load-btn" class="awb-hbtn awb-hbtn-primary">${__('Load')}</button>
    <button id="awb-refresh-btn" class="awb-hbtn" title="${__('Refresh')}">↻</button>
    <div style="flex:1;min-width:10px;"></div>
    <input id="awb-search-in" type="search" placeholder="${__('Search AWB number…')}"
           style="padding:5px 10px;border:none;border-radius:4px;font-size:11px;width:180px;">
    <button id="awb-filter-btn" class="awb-hbtn">⚙ ${__('Filters')}</button>
    <button id="awb-export-btn" class="awb-hbtn">↓ ${__('Export')}</button>
  </div>

  <!-- ── Status dashboard ─────────────────────────────────────────────── -->
  <div id="awb-dash" style="display:none;padding:10px 18px;background:#f4f8ff;
       border-bottom:1px solid #c5d4e8;"></div>

  <!-- ── Filter panel (collapsible) ───────────────────────────────────── -->
  <div id="awb-filter-panel" style="display:none;padding:12px 18px;background:#fff;
       border-bottom:2px solid #e0e8f5;"></div>

  <!-- ── Grid area ────────────────────────────────────────────────────── -->
  <div style="padding:6px 18px 0;">
    <div id="awb-gtoolbar" style="display:flex;align-items:center;gap:8px;padding:5px 0;
         flex-wrap:wrap;min-height:34px;font-size:11px;"></div>
    <div id="awb-grid" style="overflow-x:auto;border:1px solid #c5d4e8;border-radius:4px;">
      <div class="awb-empty">${__('Select a series or enter a prefix above, then click Load.')}</div>
    </div>
    <div id="awb-pg" style="padding:6px 0;display:flex;align-items:center;gap:5px;
         justify-content:flex-end;flex-wrap:wrap;font-size:11px;"></div>
  </div>

  <!-- ── Bulk action toolbar (sticky bottom) ──────────────────────────── -->
  <div id="awb-bulk-bar" style="display:none;position:fixed;bottom:0;left:0;right:0;
       background:#1a3c5e;padding:8px 22px;align-items:center;gap:6px;flex-wrap:wrap;
       z-index:1050;box-shadow:0 -2px 10px rgba(0,0,0,.25);">
  </div>

  <!-- ── History slide panel ──────────────────────────────────────────── -->
  <div id="awb-hist" style="display:none;position:fixed;top:0;right:0;width:360px;
       height:100vh;background:#fff;border-left:2px solid #c5d4e8;overflow-y:auto;
       box-shadow:-4px 0 16px rgba(0,0,0,.15);z-index:2000;padding:14px;"></div>
</div>

<style>
.awb-hbtn{padding:4px 11px;background:rgba(255,255,255,.14);color:#fff;
  border:1px solid rgba(255,255,255,.28);border-radius:4px;cursor:pointer;
  font-size:11px;font-weight:600;}
.awb-hbtn:hover{background:rgba(255,255,255,.24);}
.awb-hbtn-primary{background:#2d6a9f!important;border-color:#2d6a9f!important;}
.awb-act{padding:4px 11px;background:rgba(255,255,255,.12);color:#fff;
  border:1px solid rgba(255,255,255,.3);border-radius:4px;cursor:pointer;
  font-size:11px;font-weight:700;white-space:nowrap;}
.awb-act:hover{background:rgba(255,255,255,.22);}
.awb-act.red{border-color:#f5a9ae;color:#f5a9ae;}
.awb-badge{display:inline-block;padding:2px 7px;border-radius:10px;font-size:10px;font-weight:700;}
.awb-tbl{width:100%;border-collapse:collapse;}
.awb-tbl th{background:#1a3c5e;color:#fff;padding:7px 10px;font-size:10.5px;
  text-align:left;position:sticky;top:0;cursor:pointer;user-select:none;
  white-space:nowrap;z-index:2;}
.awb-tbl th:hover{background:#234e75;}
.awb-tbl td{padding:5px 10px;border-bottom:1px solid #eaf0f8;vertical-align:middle;}
.awb-tbl tbody tr:hover td{background:#f0f5ff;}
.awb-tbl tbody tr.awb-row-even td{background:#fafcff;}
.awb-tbl tbody tr.awb-sel td,.awb-tbl tbody tr.awb-sel.awb-row-even td{background:#ddeeff;}
.awb-pg-btn{padding:3px 9px;border:1px solid #c5d4e8;border-radius:3px;
  cursor:pointer;background:#fff;font-size:11px;}
.awb-pg-btn:hover{background:#e8f0fb;}
.awb-pg-btn.cur{background:#1a3c5e;color:#fff;border-color:#1a3c5e;}
.awb-fi{display:block;margin-bottom:3px;font-size:11px;font-weight:600;color:#444;}
.awb-input{padding:5px 8px;border:1px solid #c5d4e8;border-radius:4px;
  font-size:11px;width:100%;box-sizing:border-box;}
.awb-scb{display:inline-flex;align-items:center;gap:4px;padding:3px 8px;
  border:1px solid #c5d4e8;border-radius:12px;cursor:pointer;font-size:11px;
  margin:2px;user-select:none;}
.awb-scb.on{border-color:#1a3c5e;background:#e8f3ff;font-weight:700;}
.awb-empty{padding:50px;text-align:center;color:#999;font-size:12px;}
</style>`);

		this._bind();
		this._render_filter_panel();
	}

	_bind() {
		const W = this;

		$('#awb-load-btn, #awb-refresh-btn').on('click', () => {
			W.pg = 1; W.sel.clear(); W.load_data();
		});

		$('#awb-series-sel').on('change', function () {
			W.series = this.value;
			$('#awb-prefix-in').val('');
			W.pg = 1; W.sel.clear(); W.load_data();
		});

		$('#awb-prefix-in').on('keydown', function (e) {
			if (e.key === 'Enter') { W.pg = 1; W.sel.clear(); W.load_data(); }
		});

		let _st;
		$('#awb-search-in').on('input', function () {
			clearTimeout(_st);
			const v = this.value;
			_st = setTimeout(() => { W.filters.search = v; W.pg = 1; W.sel.clear(); W.load_data(); }, 380);
		});

		$('#awb-filter-btn').on('click', () => $('#awb-filter-panel').toggle());
		$('#awb-export-btn').on('click', () => W._export([]));
	}

	_render_filter_panel() {
		const W = this;
		const statuses = ['Available','Assigned','Withdrawn','Hold','Void','Blacklisted'];
		const chips = statuses.map(s => {
			const c = W.SC[s] || {};
			return `<span class="awb-scb" data-s="${s}">
				<span style="width:8px;height:8px;border-radius:50%;
				             background:${c.dot||'#ccc'};display:inline-block;"></span>
				${__(s)}</span>`;
		}).join('');

		$('#awb-filter-panel').html(`
		<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:10px;align-items:end;">
		  <div style="grid-column:1/-1;">
		    <label class="awb-fi">${__('Status')}</label>
		    <div id="awb-scbs" style="display:flex;flex-wrap:wrap;gap:2px;">${chips}</div>
		  </div>
		  <div>
		    <label class="awb-fi">${__('Customer')}</label>
		    <input id="awb-f-cust" class="awb-input" placeholder="${__('Customer name…')}">
		  </div>
		  <div>
		    <label class="awb-fi">${__('Date From')}</label>
		    <input id="awb-f-df" class="awb-input" type="date">
		  </div>
		  <div>
		    <label class="awb-fi">${__('Date To')}</label>
		    <input id="awb-f-dt" class="awb-input" type="date">
		  </div>
		  <div>
		    <label class="awb-fi">${__('Serial Range Start')}</label>
		    <input id="awb-f-rs" class="awb-input" placeholder="${__('e.g. 0000001')}">
		  </div>
		  <div>
		    <label class="awb-fi">${__('Serial Range End')}</label>
		    <input id="awb-f-re" class="awb-input" placeholder="${__('e.g. 0001000')}">
		  </div>
		  <div style="display:flex;gap:6px;align-items:flex-end;padding-top:14px;">
		    <button id="awb-apply-f" style="padding:6px 14px;background:#1a3c5e;color:#fff;
		            border:none;border-radius:4px;cursor:pointer;font-size:11px;font-weight:700;">
		        ${__('Apply')}
		    </button>
		    <button id="awb-reset-f" style="padding:6px 12px;background:#fff;color:#1a3c5e;
		            border:1px solid #1a3c5e;border-radius:4px;cursor:pointer;font-size:11px;">
		        ${__('Reset')}
		    </button>
		  </div>
		</div>`);

		$('#awb-scbs .awb-scb').on('click', function () { $(this).toggleClass('on'); });

		$('#awb-apply-f').on('click', () => {
			W.filters.status    = $('#awb-scbs .awb-scb.on').map(function(){ return $(this).data('s'); }).get();
			W.filters.customer  = $('#awb-f-cust').val().trim();
			W.filters.date_from = $('#awb-f-df').val();
			W.filters.date_to   = $('#awb-f-dt').val();
			W.filters.range_start = $('#awb-f-rs').val().trim();
			W.filters.range_end   = $('#awb-f-re').val().trim();
			W.pg = 1; W.sel.clear(); W.load_data();
		});

		$('#awb-reset-f').on('click', () => {
			W.filters = { status:[], customer:'', search:'', date_from:'', date_to:'', range_start:'', range_end:'' };
			$('#awb-scbs .awb-scb').removeClass('on');
			$('#awb-f-cust,#awb-f-df,#awb-f-dt,#awb-f-rs,#awb-f-re').val('');
			$('#awb-search-in').val('');
			W.pg = 1; W.sel.clear(); W.load_data();
		});
	}

	// ═══════════════════════════════════════════════════════════════════════ //
	//  Data loading                                                           //
	// ═══════════════════════════════════════════════════════════════════════ //

	_load_series() {
		frappe.call({
			method: 'cargoxy.awb.api.awb_actions.get_workbench_series',
			callback: r => {
				if (!r.message) return;
				const $sel = $('#awb-series-sel');
				(r.message.series || []).forEach(s => {
					$sel.append(`<option value="${s.name}">
						${s.awb_prefix} / ${s.awb_cycle || ''}  —  ${s.name}
						${s.generated_count ? '(' + s.generated_count + ')' : ''}
					</option>`);
				});
			}
		});
	}

	load_data() {
		const W = this;
		const prefix_ov = $('#awb-prefix-in').val().trim();

		$('#awb-grid').html(`<div class="awb-empty">${__('Loading…')}</div>`);

		const args = {
			series:          W.series,
			awb_prefix:      prefix_ov,
			status:          JSON.stringify(W.filters.status),
			customer:        W.filters.customer,
			search:          W.filters.search || $('#awb-search-in').val().trim(),
			date_from:       W.filters.date_from,
			date_to:         W.filters.date_to,
			awb_range_start: W.filters.range_start,
			awb_range_end:   W.filters.range_end,
			page:            W.pg,
			page_size:       W.pg_size,
			sort_by:         W.sort_by,
			sort_order:      W.sort_ord,
		};

		frappe.call({
			method: 'cargoxy.awb.api.awb_actions.get_workbench_data',
			args,
			callback(r) {
				if (!r.message) return;
				W.data  = r.message.items || [];
				W.total = r.message.total || 0;
				W._render_grid();
				W._render_toolbar();
				W._render_pagination(r.message);
				W._load_dashboard(prefix_ov);
			},
			error() {
				$('#awb-grid').html(`<div class="awb-empty" style="color:#dc3545;">
					${__('Error loading data. Check console.')}</div>`);
			}
		});
	}

	_load_dashboard(prefix_ov) {
		frappe.call({
			method: 'cargoxy.awb.api.awb_actions.get_status_dashboard',
			args:   { series: this.series, awb_prefix: prefix_ov || '' },
			callback: r => { if (r.message) this._render_dashboard(r.message); }
		});
	}

	// ═══════════════════════════════════════════════════════════════════════ //
	//  Rendering                                                              //
	// ═══════════════════════════════════════════════════════════════════════ //

	_render_dashboard(counts) {
		const W = this;
		const sts = ['Available','Assigned','Withdrawn','Hold','Void','Blacklisted'];
		const boxes = sts.map(s => {
			const c = W.SC[s] || { bg:'#eee', fg:'#333' };
			const active = W.filters.status.includes(s) ? `border:2px solid ${c.dot};` : '';
			return `<div style="flex:1;min-width:80px;padding:7px 8px;background:${c.bg};
			             border:1px solid ${c.dot||'#ccc'};${active}border-radius:6px;
			             text-align:center;cursor:pointer;" onclick="frappe._awb_wb.quick_status('${s}')">
			    <div style="font-size:19px;font-weight:800;color:${c.fg};">${counts[s]||0}</div>
			    <div style="font-size:9px;font-weight:700;color:${c.fg};letter-spacing:.3px;">
			        ${__(s).toUpperCase()}</div>
			</div>`;
		}).join('');
		$('#awb-dash').html(`
		<div style="display:flex;gap:7px;flex-wrap:wrap;align-items:stretch;">
		    ${boxes}
		    <div style="flex:1;min-width:80px;padding:7px 8px;background:#e8f0fb;
		         border:1px solid #c5d4e8;border-radius:6px;text-align:center;">
		        <div style="font-size:19px;font-weight:800;color:#1a3c5e;">${counts.Total||0}</div>
		        <div style="font-size:9px;font-weight:700;color:#1a3c5e;letter-spacing:.3px;">${__('TOTAL')}</div>
		    </div>
		</div>`).show();
	}

	quick_status(s) {
		const idx = this.filters.status.indexOf(s);
		if (idx >= 0) this.filters.status.splice(idx, 1);
		else           this.filters.status.push(s);
		$(`#awb-scbs .awb-scb[data-s="${s}"]`).toggleClass('on', this.filters.status.includes(s));
		this.pg = 1; this.load_data();
	}

	_render_grid() {
		const W = this;
		if (!W.data.length) {
			$('#awb-grid').html(`<div class="awb-empty">${__('No records match the current filters.')}</div>`);
			W._update_bulk_bar();
			return;
		}

		const si = f => {
			if (W.sort_by !== f) return '<span style="opacity:.3;font-size:9px;">⇅</span>';
			return W.sort_ord === 'asc' ? '<span style="font-size:9px;">↑</span>' : '<span style="font-size:9px;">↓</span>';
		};
		const th = (f, lbl) =>
			`<th onclick="frappe._awb_wb.set_sort('${f}')">${__(lbl)} ${si(f)}</th>`;

		const all_checked = W.data.length && W.data.every(d => W.sel.has(d.name));

		const rows = W.data.map((d, i) => {
			const c   = W.SC[d.status] || { bg:'#eee', fg:'#333' };
			const sel = W.sel.has(d.name);
			const cls = [sel ? 'awb-sel' : '', i%2===1 ? 'awb-row-even' : ''].join(' ');
			const chk = sel ? 'checked' : '';
			const created = d.creation ? (d.creation+'').split(' ')[0] : '';
			return `<tr class="${cls}" data-n="${frappe.utils.escape_html(d.name)}">
			    <td style="width:28px;text-align:center;">
			        <input type="checkbox" class="awb-chk" data-n="${frappe.utils.escape_html(d.name)}" ${chk}
			               style="cursor:pointer;width:13px;height:13px;">
			    </td>
			    <td style="font-weight:700;white-space:nowrap;font-size:11px;">
			        <a href="/app/awb-inventory/${encodeURIComponent(d.name)}" target="_blank"
			           style="color:#1a3c5e;text-decoration:none;"
			           onclick="event.stopPropagation();">${frappe.utils.escape_html(d.full_awb_number||d.name)}</a>
			    </td>
			    <td>
			        <span class="awb-badge" style="background:${c.bg};color:${c.fg};">${__(d.status)}</span>
			    </td>
			    <td style="font-size:11px;">${d.assigned_to ? frappe.utils.escape_html(d.assigned_to) : '<span style="color:#bbb;">—</span>'}</td>
			    <td style="font-size:10.5px;color:#555;">${frappe.utils.escape_html(d.awb_cycle||'')}</td>
			    <td style="font-size:10.5px;color:#555;">${frappe.utils.escape_html(d.awb_type||'')}</td>
			    <td style="font-size:10.5px;color:#777;">${frappe.utils.escape_html(created)}</td>
			    <td style="text-align:center;">
			        <button class="awb-hist-btn" data-n="${frappe.utils.escape_html(d.name)}"
			                style="padding:2px 7px;font-size:10px;background:#f0f5ff;
			                       color:#1a3c5e;border:1px solid #c5d4e8;border-radius:3px;
			                       cursor:pointer;" onclick="event.stopPropagation();"
			                title="${__('View audit history')}">≡</button>
			    </td>
			</tr>`;
		}).join('');

		$('#awb-grid').html(`
		<table class="awb-tbl">
		  <thead><tr>
		    <th style="width:28px;text-align:center;">
		        <input type="checkbox" id="awb-chk-all" ${all_checked?'checked':''}
		               style="cursor:pointer;width:13px;height:13px;" title="${__('Select all on page')}">
		    </th>
		    ${th('full_awb_number','AWB Number')}
		    ${th('status','Status')}
		    ${th('assigned_to','Assigned To')}
		    ${th('awb_cycle','Cycle')}
		    ${th('awb_type','Type')}
		    ${th('creation','Created')}
		    <th>${__('History')}</th>
		  </tr></thead>
		  <tbody>${rows}</tbody>
		</table>`);

		// Select-all toggle
		$('#awb-chk-all').on('change', function () {
			if (this.checked) W.data.forEach(d => W.sel.add(d.name));
			else              W.data.forEach(d => W.sel.delete(d.name));
			W._render_grid();
		});

		// Row checkbox
		$('#awb-grid .awb-chk').on('change', function () {
			const n = $(this).data('n');
			this.checked ? W.sel.add(n) : W.sel.delete(n);
			$(this).closest('tr').toggleClass('awb-sel', this.checked);
			W._update_bulk_bar();
			$('#awb-chk-all').prop('checked', W.data.every(d => W.sel.has(d.name)));
		});

		// Row click → toggle checkbox
		$('#awb-grid tbody tr').on('click', function (e) {
			if (['INPUT','A','BUTTON'].includes(e.target.tagName)) return;
			const chk = $(this).find('.awb-chk')[0];
			chk.checked = !chk.checked;
			$(chk).trigger('change');
		});

		// History button
		$('#awb-grid .awb-hist-btn').on('click', function () {
			W.show_history($(this).data('n'));
		});

		W._update_bulk_bar();
	}

	set_sort(field) {
		if (this.sort_by === field) this.sort_ord = this.sort_ord === 'asc' ? 'desc' : 'asc';
		else { this.sort_by = field; this.sort_ord = 'asc'; }
		this.load_data();
	}

	_render_toolbar() {
		const W = this;
		$('#awb-gtoolbar').html(`
		<span style="color:#555;">
		    ${__('Showing')} <strong>${W.data.length}</strong>
		    ${__('of')} <strong>${W.total}</strong>
		    ${W.sel.size ? `— <strong style="color:#1a3c5e;">${W.sel.size} ${__('selected')}</strong>` : ''}
		</span>
		<div style="flex:1;"></div>
		<label style="color:#555;">${__('Per page')}:
		    <select id="awb-pgsize" style="font-size:11px;padding:2px 5px;border:1px solid #c5d4e8;border-radius:3px;">
		        ${[25,50,100,200].map(n=>`<option value="${n}" ${n==W.pg_size?'selected':''}>${n}</option>`).join('')}
		    </select>
		</label>`);

		$('#awb-pgsize').on('change', function () {
			W.pg_size = parseInt(this.value); W.pg = 1; W.load_data();
		});
	}

	_render_pagination(meta) {
		const W = this;
		const { page, total_pages } = meta;
		if (total_pages <= 1) { $('#awb-pg').empty(); return; }

		let html = `<span style="color:#777;">${__('Page')} ${page} ${__('of')} ${total_pages}</span>`;
		if (page > 1) html += `<button class="awb-pg-btn" data-p="${page-1}">‹</button>`;

		const lo = Math.max(1, page-2), hi = Math.min(total_pages, page+2);
		if (lo > 1)           html += `<button class="awb-pg-btn" data-p="1">1</button><span style="padding:0 3px;color:#aaa;">…</span>`;
		for (let i=lo;i<=hi;i++) html += `<button class="awb-pg-btn${i===page?' cur':''}" data-p="${i}">${i}</button>`;
		if (hi < total_pages) html += `<span style="padding:0 3px;color:#aaa;">…</span><button class="awb-pg-btn" data-p="${total_pages}">${total_pages}</button>`;
		if (page < total_pages) html += `<button class="awb-pg-btn" data-p="${page+1}">›</button>`;

		$('#awb-pg').html(html);
		$('#awb-pg .awb-pg-btn').on('click', function () {
			W.pg = parseInt($(this).data('p')); W.load_data();
		});
	}

	// ═══════════════════════════════════════════════════════════════════════ //
	//  Bulk action toolbar                                                    //
	// ═══════════════════════════════════════════════════════════════════════ //

	_update_bulk_bar() {
		const W   = this;
		const cnt = W.sel.size;
		if (!cnt) { $('#awb-bulk-bar').hide(); return; }

		const ACTS = [
			{ lbl: __('Assign'),       st: 'Assigned',    extra: '' },
			{ lbl: __('Withdraw'),     st: 'Withdrawn',   extra: '' },
			{ lbl: __('Hold'),         st: 'Hold',        extra: '' },
			{ lbl: __('Release Hold'), st: 'Available',   extra: '' },
			{ lbl: __('Blacklist'),    st: 'Blacklisted', extra: 'red' },
			{ lbl: __('Void'),         st: 'Void',        extra: 'red' },
		];

		const btns = ACTS.map(a =>
			`<button class="awb-act ${a.extra}"
			         onclick="frappe._awb_wb.do_action('${a.st}')">
			    ${a.lbl}
			</button>`
		).join('');

		$('#awb-bulk-bar').html(`
		<span style="color:#fff;font-weight:700;font-size:12px;margin-right:4px;">
		    ${cnt} ${__('selected')}
		</span>
		${btns}
		<div style="flex:1;"></div>
		<button class="awb-act" onclick="frappe._awb_wb.sel.clear();frappe._awb_wb._render_grid();">
		    ✕ ${__('Clear')}
		</button>
		<button class="awb-act" onclick="frappe._awb_wb._export(Array.from(frappe._awb_wb.sel));">
		    ↓ ${__('Export Selected')}
		</button>`).css('display','flex').show();
	}

	// ═══════════════════════════════════════════════════════════════════════ //
	//  Action flow: dialog → preview → execute → results                     //
	// ═══════════════════════════════════════════════════════════════════════ //

	do_action(new_status) {
		const names = Array.from(this.sel);
		if (!names.length) {
			frappe.show_alert({ message: __('No AWBs selected.'), indicator: 'orange' }, 3);
			return;
		}
		this._action_dialog(new_status, names);
	}

	_action_dialog(new_status, names) {
		const W = this;
		const need_cust   = new_status === 'Assigned';
		const need_reason = ['Withdrawn','Void','Blacklisted'].includes(new_status);

		const fields = [
			{
				fieldname: 'info', fieldtype: 'HTML',
				options: `<div style="padding:8px 12px;background:#e8f0fb;border-radius:4px;
				               font-size:11px;margin-bottom:2px;">
				    ${__('Updating')} <strong>${names.length}</strong>
				    ${__('AWB(s)')} → <strong style="color:#1a3c5e;">${__(new_status)}</strong>
				</div>`
			},
			...(need_cust ? [{
				fieldname: 'customer', fieldtype: 'Link', options: 'Customer',
				label: __('Assign To Customer'), reqd: 1,
			}] : []),
			{
				fieldname: 'reason', fieldtype: 'Small Text',
				label: __('Reason / Notes'),
				description: need_reason ? __('Required for this action') : __('Optional'),
				reqd: need_reason ? 1 : 0,
			},
			{
				fieldname: 'force', fieldtype: 'Check',
				label: __('Force Transition (Admin Only)'),
				description: __('Override state-machine rules — logged in audit trail'),
			},
		];

		const d = new frappe.ui.Dialog({
			title: `${__(new_status)} — ${names.length} ${__('AWB(s)')}`,
			size:  'large',
			fields,
			primary_action_label: __('Preview →'),
			secondary_action_label: __('Cancel'),
			secondary_action() { d.hide(); },
			primary_action(vals) {
				if (need_cust && !vals.customer) {
					frappe.msgprint({ message: __('Customer is required.'), indicator: 'red' }); return;
				}
				if (need_reason && !(vals.reason||'').trim()) {
					frappe.msgprint({ message: __('Reason is required for this action.'), indicator: 'orange' }); return;
				}
				d.hide();
				W._preview(new_status, names, vals);
			},
		});
		d.show();
	}

	_preview(new_status, names, vals) {
		const W = this;
		frappe.call({
			method: 'cargoxy.awb.api.awb_actions.preview_awb_operation',
			args: {
				mode: 'selected', new_status,
				names, customer: vals.customer||'',
				force: vals.force ? 1 : 0, reason: vals.reason||'',
			},
			freeze: true, freeze_message: __('Generating preview…'),
			callback(r) {
				if (!r.message) return;
				W._preview_dialog(r.message, new_status, names, vals);
			},
		});
	}

	_preview_dialog(pv, new_status, names, vals) {
		const W = this;
		const { counts, items } = pv;

		const rows = items.map((item, i) => {
			const c  = W.SC[item.current_status] || { bg:'#eee', fg:'#333' };
			const ok = item.allowed;
			return `<tr style="border-bottom:1px solid #e8f0fb;background:${i%2?'#f9fbff':'#fff'};">
			    <td style="padding:4px 8px;text-align:center;">
			        ${ok ? '<span style="color:#155724;font-weight:700;">✓</span>'
			             : '<span style="color:#721c24;font-weight:700;">✗</span>'}
			    </td>
			    <td style="padding:4px 8px;font-weight:700;font-size:10.5px;">
			        ${frappe.utils.escape_html(item.full_awb_number)}</td>
			    <td style="padding:4px 8px;">
			        <span style="padding:2px 7px;border-radius:10px;font-size:9.5px;font-weight:700;
			                     background:${c.bg};color:${c.fg};">${__(item.current_status)}</span>
			    </td>
			    <td style="padding:4px 8px;font-size:10px;color:${ok?'#555':'#721c24'};">
			        ${frappe.utils.escape_html(item.reason || (ok ? __('Will be updated') : ''))}</td>
			</tr>`;
		}).join('');

		const pd = new frappe.ui.Dialog({
			title: __('Preview — {0} AWB(s)', [counts.total]),
			size:  'large',
			fields: [{
				fieldname: 'html', fieldtype: 'HTML',
				options: `
				<div style="font-size:11px;">
				  <div style="display:flex;gap:8px;margin-bottom:10px;">
				    <div style="flex:1;padding:8px;background:#d4edda;border-radius:4px;text-align:center;">
				        <div style="font-size:18px;font-weight:800;color:#155724;">${counts.will_update}</div>
				        <div style="font-size:9px;color:#155724;">${__('WILL UPDATE')}</div>
				    </div>
				    <div style="flex:1;padding:8px;background:#f8d7da;border-radius:4px;text-align:center;">
				        <div style="font-size:18px;font-weight:800;color:#721c24;">${counts.blocked}</div>
				        <div style="font-size:9px;color:#721c24;">${__('BLOCKED')}</div>
				    </div>
				    <div style="flex:1;padding:8px;background:#e8f0fb;border-radius:4px;text-align:center;">
				        <div style="font-size:18px;font-weight:800;color:#1a3c5e;">${counts.total}</div>
				        <div style="font-size:9px;color:#1a3c5e;">${__('TOTAL')}</div>
				    </div>
				  </div>
				  <div style="max-height:280px;overflow-y:auto;border:1px solid #c5d4e8;border-radius:4px;">
				    <table style="width:100%;border-collapse:collapse;">
				      <thead><tr style="background:#1a3c5e;color:#fff;position:sticky;top:0;">
				        <th style="padding:6px 8px;font-size:10px;width:28px;"></th>
				        <th style="padding:6px 8px;font-size:10px;">${__('AWB Number')}</th>
				        <th style="padding:6px 8px;font-size:10px;">${__('Current Status')}</th>
				        <th style="padding:6px 8px;font-size:10px;">${__('Note')}</th>
				      </tr></thead>
				      <tbody>${rows}</tbody>
				    </table>
				  </div>
				  ${counts.blocked > 0 ? `
				  <div style="margin-top:8px;padding:6px 10px;background:#fff3cd;
				       border:1px solid #ffc107;border-radius:4px;font-size:10px;color:#856404;">
				       ⚠ ${__('Only {0} of {1} will be updated. {2} are blocked.',
				               [counts.will_update, counts.total, counts.blocked])}
				  </div>` : ''}
				</div>`
			}],
			primary_action_label: counts.will_update > 0
				? __('Execute — Update {0}', [counts.will_update])
				: __('Nothing to Update'),
			secondary_action_label: __('← Back'),
			secondary_action() { pd.hide(); W._action_dialog(new_status, names); },
			primary_action() {
				if (!counts.will_update) { pd.hide(); return; }
				pd.hide();
				W._execute(new_status, names, vals);
			},
		});
		pd.show();
	}

	_execute(new_status, names, vals) {
		const W = this;
		frappe.call({
			method: 'cargoxy.awb.api.awb_actions.bulk_update_awb_status',
			args: {
				mode: 'selected', new_status, names,
				customer: vals.customer||'', reason: vals.reason||'',
				force: vals.force ? 1 : 0, dry_run: false,
			},
			freeze: true, freeze_message: __('Updating AWBs…'),
			callback(r) {
				if (!r.message) return;
				const msg = r.message;
				if (msg.enqueued) W._progress_dialog(msg.operation_id);
				else              W._results_dialog(msg, null);
			},
		});
	}

	_progress_dialog(operation_id) {
		const W = this;
		const pd = new frappe.ui.Dialog({
			title: __('Processing in background…'),
			size:  'large',
			fields: [{
				fieldname: 'html', fieldtype: 'HTML',
				options: `
				<div style="padding:8px;">
				  <div style="width:100%;height:20px;background:#e8f0fb;border-radius:4px;
				              overflow:hidden;margin-bottom:6px;">
				    <div id="awb-pb" style="width:0%;height:100%;
				         background:linear-gradient(90deg,#1a3c5e,#2d6a9f);transition:width .3s;"></div>
				  </div>
				  <div style="display:flex;justify-content:space-between;font-size:10px;
				              color:#666;margin-bottom:8px;">
				    <span id="awb-pp">0%</span><span id="awb-pc">0 / 0</span>
				  </div>
				  <div id="awb-pl" style="max-height:110px;overflow-y:auto;background:#f9fbff;
				       border:1px solid #c5d4e8;border-radius:4px;padding:6px;
				       font-size:9.5px;font-family:monospace;color:#333;"></div>
				</div>`
			}],
			secondary_action_label: __('Cancel'),
			secondary_action() {
				frappe.call({ method: 'cargoxy.awb.api.awb_actions.cancel_bulk_operation',
				              args: { operation_id } });
			}
		});
		pd.show();

		const upd = data => {
			if (data.operation_id !== operation_id) return;
			pd.$wrapper.find('#awb-pb').css('width', (data.progress||0) + '%');
			pd.$wrapper.find('#awb-pp').text((data.progress||0) + '%');
			pd.$wrapper.find('#awb-pc').text(`${data.processed||0} / ${data.total||0}`);
			if (data.message) {
				const $l = pd.$wrapper.find('#awb-pl');
				$l.append(`<div>${frappe.datetime.now_time()} — ${data.message}</div>`);
				$l[0].scrollTop = $l[0].scrollHeight;
			}
		};
		const fin = data => {
			if (data.operation_id !== operation_id) return;
			frappe.realtime.off('awb_bulk_progress', upd);
			frappe.realtime.off('awb_bulk_finished', fin);
			pd.hide();
			if (data.error) {
				frappe.msgprint({ message: data.error, indicator: 'red', title: __('Failed') });
				return;
			}
			frappe.call({
				method: 'cargoxy.awb.api.awb_actions.get_bulk_operation_status',
				args: { operation_id },
				callback(r) { if (r.message) W._results_dialog(r.message, operation_id); }
			});
		};

		frappe.realtime.on('awb_bulk_progress', upd);
		frappe.realtime.on('awb_bulk_finished', fin);

		const poll = setInterval(() => {
			frappe.call({
				method: 'cargoxy.awb.api.awb_actions.get_bulk_operation_status',
				args: { operation_id },
				callback(r) {
					if (!r.message) return;
					upd({ operation_id, progress: r.message.progress,
					      processed: r.message.processed, total: r.message.total });
					const st = r.message.status;
					if (['Completed','Failed','Cancelled'].includes(st)) {
						clearInterval(poll);
						fin({ operation_id, error: st==='Failed' ? __('Operation failed.') : null });
					}
				}
			});
		}, 3000);
	}

	_results_dialog(result, operation_id) {
		const W = this;
		const updated = result.counts ? result.counts.updated : (result.processed||0);
		const failed  = result.counts ? result.counts.failed  : (result.errors||0);

		const rd = new frappe.ui.Dialog({
			title: __('Operation Complete'),
			size:  'large',
			fields: [{
				fieldname: 'html', fieldtype: 'HTML',
				options: `
				<div style="font-size:11px;">
				  <div style="display:flex;gap:10px;margin-bottom:12px;">
				    <div style="flex:1;padding:10px;background:#d4edda;border-radius:4px;text-align:center;">
				        <div style="font-size:22px;font-weight:800;color:#155724;">✓ ${updated}</div>
				        <div style="font-size:10px;color:#155724;">${__('Updated')}</div>
				    </div>
				    ${failed > 0 ? `
				    <div style="flex:1;padding:10px;background:#f8d7da;border-radius:4px;text-align:center;">
				        <div style="font-size:22px;font-weight:800;color:#721c24;">✗ ${failed}</div>
				        <div style="font-size:10px;color:#721c24;">${__('Failed / Skipped')}</div>
				    </div>` : ''}
				  </div>
				  ${(result.items||[]).filter(i=>!i.success).slice(0,5).map(i=>
				    `<div style="padding:4px 10px;background:#fff3cd;border-left:4px solid #ffc107;
				          border-radius:2px;margin-bottom:3px;font-size:10px;color:#856404;">
				        <strong>${frappe.utils.escape_html(i.full_awb_number)}</strong>: ${frappe.utils.escape_html(i.message)}
				    </div>`
				  ).join('')}
				  <div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;">
				    ${result.result_file ? `
				    <a href="/app/file/${frappe.utils.escape_html(result.result_file)}" target="_blank"
				       style="padding:5px 12px;background:#1a3c5e;color:#fff;border-radius:4px;
				              text-decoration:none;font-size:10.5px;font-weight:700;">
				        📥 ${__('Download CSV')}</a>` : ''}
				    ${operation_id ? `
				    <button id="awb-undo-btn"
				            style="padding:5px 12px;background:#fff;color:#dc3545;
				                   border:1px solid #dc3545;border-radius:4px;
				                   cursor:pointer;font-size:10.5px;font-weight:700;">
				        ↩ ${__('Undo This Operation')}</button>` : ''}
				  </div>
				</div>`
			}],
			primary_action_label: __('Close'),
			primary_action() {
				rd.hide(); W.sel.clear(); W.load_data();
			}
		});
		rd.show();

		if (operation_id) {
			rd.$wrapper.find('#awb-undo-btn').on('click', () => {
				frappe.confirm(
					__('Revert all {0} change(s) from this operation?', [updated]),
					() => {
						frappe.call({
							method: 'cargoxy.awb.api.awb_actions.undo_bulk_operation',
							args: { operation_id },
							freeze: true, freeze_message: __('Reverting…'),
							callback(r) {
								rd.hide();
								if (r.message && r.message.success) {
									frappe.show_alert({ message: r.message.message, indicator: 'green' }, 5);
								}
								W.sel.clear(); W.load_data();
							}
						});
					}
				);
			});
		}
	}

	// ═══════════════════════════════════════════════════════════════════════ //
	//  History panel                                                          //
	// ═══════════════════════════════════════════════════════════════════════ //

	show_history(awb_name) {
		const W = this;
		const $p = $('#awb-hist');
		$p.html(`<div style="padding:20px;text-align:center;color:#999;font-size:11px;">
		    ${__('Loading history…')}</div>`).show();

		frappe.call({
			method: 'cargoxy.awb.api.awb_actions.get_awb_audit_history',
			args: { awb_name },
			callback(r) {
				const entries = r.message || [];
				const header  = `
				<div style="display:flex;justify-content:space-between;align-items:center;
				     padding-bottom:10px;margin-bottom:10px;border-bottom:1px solid #e0e8f5;
				     position:sticky;top:0;background:#fff;z-index:10;">
				  <strong style="font-size:12px;color:#1a3c5e;">
				      ${__('History')}: ${frappe.utils.escape_html(awb_name)}</strong>
				  <button onclick="$('#awb-hist').hide();"
				          style="background:none;border:none;cursor:pointer;color:#999;
				                 font-size:18px;padding:2px 6px;">✕</button>
				</div>`;

				if (!entries.length) {
					$p.html(header + `<div style="padding:20px;text-align:center;color:#999;font-size:11px;">
					    ${__('No audit history found.')}</div>`);
					return;
				}

				const rows = entries.map(e => {
					const ps   = W.SC[e.prev_status] || { bg:'#eee', fg:'#333' };
					const ns   = W.SC[e.new_status]  || { bg:'#eee', fg:'#333' };
					const when = e.performed_at ? frappe.datetime.str_to_user((e.performed_at+'').split('.')[0]) : '';
					const who  = (e.performed_by||'').split('@')[0];
					return `<div style="padding:9px 12px;border-bottom:1px solid #eaf0f8;">
					  <div style="display:flex;align-items:center;gap:5px;flex-wrap:wrap;margin-bottom:3px;">
					    <span style="font-size:10px;font-weight:700;color:#1a3c5e;">
					        ${__(e.operation_type)}</span>
					    <span style="padding:1px 6px;border-radius:8px;font-size:9px;font-weight:700;
					                 background:${ps.bg};color:${ps.fg};">${__(e.prev_status||'')}</span>
					    <span style="color:#bbb;font-size:10px;">→</span>
					    <span style="padding:1px 6px;border-radius:8px;font-size:9px;font-weight:700;
					                 background:${ns.bg};color:${ns.fg};">${__(e.new_status||'')}</span>
					  </div>
					  ${e.new_assigned_to ? `<div style="font-size:9.5px;color:#555;">
					      ${__('To')}: <strong>${frappe.utils.escape_html(e.new_assigned_to)}</strong></div>` : ''}
					  ${e.reason ? `<div style="font-size:9.5px;color:#777;font-style:italic;">
					      ${frappe.utils.escape_html(e.reason)}</div>` : ''}
					  <div style="font-size:9px;color:#aaa;margin-top:3px;">${who} • ${when}</div>
					</div>`;
				}).join('');

				$p.html(header + `<div style="font-size:11px;">${rows}</div>`);
			}
		});
	}

	// ═══════════════════════════════════════════════════════════════════════ //
	//  CSV export                                                             //
	// ═══════════════════════════════════════════════════════════════════════ //

	_export(name_filter) {
		const rows = name_filter.length
			? this.data.filter(d => name_filter.includes(d.name))
			: this.data;

		if (!rows.length) {
			frappe.show_alert({ message: __('No data to export.'), indicator: 'orange' }, 3);
			return;
		}

		const hdr = ['AWB Name','Full AWB Number','Prefix','Cycle','Type',
		              'Status','Assigned To','Assigned Date','Created'];
		const csv_rows = rows.map(d => [
			d.name, d.full_awb_number, d.awb_prefix, d.awb_cycle, d.awb_type,
			d.status, d.assigned_to||'', d.assigned_date||'',
			(d.creation||'').split(' ')[0],
		]);

		const csv = [hdr, ...csv_rows]
			.map(r => r.map(v => `"${(v||'').toString().replace(/"/g,'""')}"`).join(','))
			.join('\n');

		const blob = new Blob([csv], { type: 'text/csv' });
		const url  = URL.createObjectURL(blob);
		const a    = document.createElement('a');
		a.href     = url;
		a.download = `AWB_Export_${frappe.datetime.nowdate()}.csv`;
		a.click();
		URL.revokeObjectURL(url);
	}
}
