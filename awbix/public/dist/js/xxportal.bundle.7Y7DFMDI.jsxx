(() => {
  // ../awbix/awbix/public/js/portal.bundle.js
  (function() {
    "use strict";
    const ICONS = {
      dashboard: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/>',
      shipments: '<path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/>',
      track: '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
      reports: '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
      doctype: '<path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/>',
      link: '<path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/>',
      cog: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/>',
      user: '<path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/>',
      chart: '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
      calendar: '<rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',
      bell: '<path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/>',
      folder: '<path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>',
      star: '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
      check: '<polyline points="20 6 9 17 4 12"/>'
    };
    const COG_SVG = ICONS.cog;
    const THEME_KEY = "awbix_portal_theme";
    const VALID_THEMES = ["ocean", "teal", "dark"];
    function applyTheme(t) {
      if (!VALID_THEMES.includes(t))
        t = "ocean";
      document.documentElement.setAttribute("data-portal-theme", t);
      localStorage.setItem(THEME_KEY, t);
      document.querySelectorAll(".theme-dot").forEach((el) => {
        el.classList.toggle("active", el.dataset.theme === t);
        el.setAttribute("aria-pressed", el.dataset.theme === t ? "true" : "false");
      });
    }
    function initTheme() {
      applyTheme(localStorage.getItem(THEME_KEY) || "ocean");
      document.querySelectorAll(".theme-dot").forEach(
        (dot) => dot.addEventListener("click", () => applyTheme(dot.dataset.theme))
      );
    }
    function initSidebar() {
      const sidebar = document.getElementById("pt-sidebar");
      const hamburger = document.getElementById("pt-hamburger");
      const overlay = document.getElementById("pt-sidebar-overlay");
      if (!sidebar || !hamburger)
        return;
      function open() {
        sidebar.classList.add("open");
        overlay.classList.add("active");
        hamburger.classList.add("open");
        hamburger.setAttribute("aria-expanded", "true");
        document.body.style.overflow = "hidden";
      }
      function close() {
        sidebar.classList.remove("open");
        overlay.classList.remove("active");
        hamburger.classList.remove("open");
        hamburger.setAttribute("aria-expanded", "false");
        document.body.style.overflow = "";
      }
      hamburger.addEventListener(
        "click",
        () => sidebar.classList.contains("open") ? close() : open()
      );
      overlay.addEventListener("click", close);
      document.addEventListener("keydown", (e) => {
        if (e.key === "Escape")
          close();
      });
      window.addEventListener("resize", () => {
        if (window.innerWidth > 900)
          close();
      });
    }
    function initAccordion() {
      document.querySelectorAll(".pt-sidebar__link[data-has-sub]").forEach((btn) => {
        const sub = document.getElementById(btn.dataset.hasSub);
        if (!sub)
          return;
        if (sub.querySelector("a.active")) {
          sub.classList.add("open");
          btn.setAttribute("aria-expanded", "true");
        }
        btn.addEventListener("click", () => {
          const isOpen = sub.classList.toggle("open");
          btn.setAttribute("aria-expanded", isOpen ? "true" : "false");
        });
      });
    }
    function markActiveLinks() {
      const path = window.location.pathname;
      document.querySelectorAll(".pt-sidebar__link[href], .pt-sidebar__sub a").forEach((a) => {
        try {
          const match = new URL(a.href, location.origin).pathname === path;
          a.classList.toggle("active", match);
        } catch (_) {
        }
      });
    }
    const MENU_CACHE_KEY = "awbix_portal_menu";
    const MENU_CACHE_TTL = 5 * 60 * 1e3;
    function iconSvg(name) {
      return ICONS[name] || ICONS.link;
    }
    function buildNavHtml(items) {
      if (!items || !items.length)
        return null;
      const topLevel = items.filter((i) => !i.parent_item);
      const groups = [];
      const groupSeen = /* @__PURE__ */ new Set();
      for (const item of topLevel) {
        const g = item.group_label || "";
        if (!groupSeen.has(g)) {
          groupSeen.add(g);
          groups.push(g);
        }
      }
      let html = "";
      for (const group of groups) {
        if (group) {
          html += `<div class="pt-sidebar__group-label">${esc(group)}</div>`;
        }
        const groupItems = topLevel.filter((i) => (i.group_label || "") === group);
        for (const item of groupItems) {
          const subItems = items.filter((i) => i.parent_item === item.label || i.parent_item === item.name);
          const subId = "sub-" + esc(item.label).toLowerCase().replace(/\s+/g, "-");
          const svg = `<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">${item.icon_svg || iconSvg(item.icon)}</svg>`;
          const target = item.open_in_new_tab ? ' target="_blank" rel="noopener"' : "";
          if (subItems.length) {
            html += `
						<button class="pt-sidebar__link" data-has-sub="${subId}" aria-expanded="false">
							${svg}${esc(item.label)}
							<svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
								<polyline points="9 18 15 12 9 6"/>
							</svg>
						</button>
						<div class="pt-sidebar__sub" id="${subId}">
							${subItems.map((s) => `<a href="${esc(s.route || "")}"${target}>${esc(s.label)}</a>`).join("")}
						</div>`;
          } else {
            html += `
						<a href="${esc(item.route || "")}" class="pt-sidebar__link"${target}>
							${svg}${esc(item.label)}
						</a>`;
          }
        }
      }
      return html;
    }
    async function loadDynamicMenu() {
      if (frappe.is_guest)
        return;
      const cached = (() => {
        try {
          const c = JSON.parse(localStorage.getItem(MENU_CACHE_KEY) || "null");
          if (c && Date.now() - c.ts < MENU_CACHE_TTL)
            return c.items;
        } catch (_) {
        }
        return null;
      })();
      if (cached)
        applyDynamicMenu(cached);
      try {
        const data = await apiGet("awbix.portal.api.get_portal_menu");
        if (!data || !data.items)
          return;
        localStorage.setItem(MENU_CACHE_KEY, JSON.stringify({ ts: Date.now(), items: data.items }));
        applyDynamicMenu(data.items);
      } catch (_) {
      }
    }
    function applyDynamicMenu(items) {
      const nav = document.getElementById("pt-nav");
      if (!nav)
        return;
      const html = buildNavHtml(items);
      if (!html)
        return;
      const adminHtml = `
			<div class="pt-sidebar__group-label" style="margin-top:.5rem">Admin</div>
			<a href="/portal/menu-config" class="pt-sidebar__link">
				<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					${COG_SVG}
				</svg>
				Configure Menu
			</a>`;
      nav.innerHTML = html + (frappe.is_admin ? adminHtml : "");
      initAccordion();
      markActiveLinks();
    }
    function initAdminNav() {
      const slot = document.getElementById("pt-nav-admin");
      if (!slot || !frappe.is_admin)
        return;
      slot.innerHTML = `
			<div class="pt-sidebar__group-label" style="margin-top:.5rem">Admin</div>
			<a href="/portal/menu-config" class="pt-sidebar__link">
				<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					${COG_SVG}
				</svg>
				Configure Menu
			</a>`;
    }
    window.ptToast = function(msg, type = "info", duration = 3500) {
      const icons = {
        success: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>`,
        error: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
        info: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`
      };
      const wrap = document.getElementById("pt-toasts");
      if (!wrap)
        return;
      const el = document.createElement("div");
      el.className = `pt-toast pt-toast--${type}`;
      el.innerHTML = (icons[type] || icons.info) + `<span>${esc(msg)}</span>`;
      wrap.appendChild(el);
      setTimeout(() => {
        el.classList.add("out");
        setTimeout(() => el.remove(), 250);
      }, duration);
    };
    function initTrackForm() {
      const form = document.querySelector("#pt-track-form");
      if (!form)
        return;
      form.addEventListener("submit", async (e) => {
        var _a;
        e.preventDefault();
        const awb = (((_a = form.querySelector("#awb-input")) == null ? void 0 : _a.value) || "").trim();
        if (!awb)
          return;
        const resultEl = document.querySelector("#pt-track-result");
        const loadingEl = document.querySelector("#pt-track-loading");
        if (resultEl)
          resultEl.innerHTML = "";
        if (loadingEl)
          loadingEl.style.display = "block";
        try {
          const data = await apiGet("awbix.portal.api.track_shipment", { awb });
          if (loadingEl)
            loadingEl.style.display = "none";
          renderTrackResult(data, resultEl);
        } catch (e2) {
          if (loadingEl)
            loadingEl.style.display = "none";
          if (resultEl)
            resultEl.innerHTML = alertHtml("error", "Unable to fetch tracking data.");
        }
      });
    }
    function renderTrackResult(data, container) {
      var _a, _b;
      if (!container)
        return;
      if (!data || data.error) {
        container.innerHTML = alertHtml("warning", (data == null ? void 0 : data.error) || "AWB not found.");
        return;
      }
      container.innerHTML = `
			<div style="margin-top:1.25rem">
				<div class="pt-card">
					<div class="pt-card__header">
						<h3>AWB: <span style="font-family:monospace;font-size:.95rem;color:var(--pt-primary);font-weight:700">${esc(data.awb_number)}</span></h3>
						<span class="pt-badge pt-badge--${esc(data.status_class)}">${esc(data.status)}</span>
					</div>
					<div class="pt-card__body">
						<div class="pt-info-grid" style="margin-bottom:1.25rem">
							${infoItem("Origin", data.origin || "\u2014")}
							${infoItem("Destination", data.destination || "\u2014")}
							${infoItem("Pieces", (_a = data.pieces) != null ? _a : "\u2014")}
							${infoItem("Weight", data.weight ? data.weight + " kg" : "\u2014")}
						</div>
						${((_b = data.events) == null ? void 0 : _b.length) ? `
							<div style="font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.07em;color:var(--pt-text-muted);margin-bottom:.75rem">Tracking Events</div>
							<div class="pt-timeline">${data.events.map((ev, i) => `
								<div class="pt-timeline__item ${i === 0 ? "current" : "done"}">
									<div class="pt-timeline__item__title">${esc(ev.title)}</div>
									<div class="pt-timeline__item__meta">${esc(ev.location || "")}${ev.time ? " \xB7 " + esc(ev.time) : ""}</div>
								</div>`).join("")}</div>` : ""}
					</div>
				</div>
			</div>`;
    }
    window.ptInitTabs = function(containerSelector) {
      const container = document.querySelector(containerSelector);
      if (!container)
        return;
      const tabs = container.querySelectorAll(".pt-tab");
      const scope = container.parentElement;
      const panels = scope ? scope.querySelectorAll(".pt-tab-panel") : [];
      function activate(idx) {
        tabs.forEach((t, i) => {
          t.classList.toggle("active", i === idx);
          t.setAttribute("aria-selected", i === idx ? "true" : "false");
        });
        panels.forEach((p, i) => p.classList.toggle("active", i === idx));
      }
      tabs.forEach((tab, idx) => {
        tab.setAttribute("role", "tab");
        tab.setAttribute("aria-selected", tab.classList.contains("active") ? "true" : "false");
        tab.addEventListener("click", () => activate(idx));
        tab.addEventListener("keydown", (e) => {
          if (e.key === "ArrowRight")
            activate(Math.min(idx + 1, tabs.length - 1));
          if (e.key === "ArrowLeft")
            activate(Math.max(idx - 1, 0));
        });
      });
      const already = [...tabs].findIndex((t) => t.classList.contains("active"));
      if (already < 0 && tabs.length)
        activate(0);
    };
    async function apiGet(method, params = {}) {
      const qs = new URLSearchParams(params).toString();
      const url = `/api/method/${method}${qs ? "?" + qs : ""}`;
      const res = await fetch(url, {
        headers: { "X-Frappe-CSRF-Token": frappe.csrf_token }
      });
      const json = await res.json();
      if (json.exc) {
        const msg = json._server_messages ? JSON.parse(JSON.parse(json._server_messages)[0]).message : "Server error";
        throw new Error(msg);
      }
      return json.message;
    }
    function alertHtml(type, msg) {
      const icon = type === "warning" ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>` : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`;
      return `<div class="pt-alert pt-alert--${type}" style="margin-top:1rem">${icon}${esc(msg)}</div>`;
    }
    function infoItem(label, value) {
      return `<div class="pt-info-item">
			<div class="pt-info-item__label">${esc(label)}</div>
			<div class="pt-info-item__value">${esc(String(value))}</div>
		</div>`;
    }
    function esc(s) {
      return String(s != null ? s : "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }
    document.addEventListener("DOMContentLoaded", () => {
      initTheme();
      initSidebar();
      initAccordion();
      markActiveLinks();
      initAdminNav();
      initTrackForm();
      loadDynamicMenu();
    });
  })();
})();
//# sourceMappingURL=portal.bundle.7Y7DFMDI.js.map
