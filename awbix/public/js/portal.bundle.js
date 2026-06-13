// AWBix Portal — sidebar nav, theme switcher, toast, track form

(function () {
	"use strict";

	// ── Theme ─────────────────────────────────────────────────────────────────

	const THEME_KEY = "awbix_portal_theme";
	const VALID = ["ocean", "teal", "dark"];

	function applyTheme(t) {
		if (!VALID.includes(t)) t = "ocean";
		document.documentElement.setAttribute("data-portal-theme", t);
		localStorage.setItem(THEME_KEY, t);
		document.querySelectorAll(".theme-dot").forEach((el) => {
			el.classList.toggle("active", el.dataset.theme === t);
			el.setAttribute("aria-pressed", el.dataset.theme === t ? "true" : "false");
		});
	}

	function initTheme() {
		applyTheme(localStorage.getItem(THEME_KEY) || "ocean");
		document.querySelectorAll(".theme-dot").forEach((dot) =>
			dot.addEventListener("click", () => applyTheme(dot.dataset.theme))
		);
	}

	// ── Sidebar ───────────────────────────────────────────────────────────────

	function initSidebar() {
		const sidebar  = document.getElementById("pt-sidebar");
		const hamburger = document.getElementById("pt-hamburger");
		const overlay  = document.getElementById("pt-sidebar-overlay");
		if (!sidebar || !hamburger) return;

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

		hamburger.addEventListener("click", () =>
			sidebar.classList.contains("open") ? close() : open()
		);
		overlay.addEventListener("click", close);
		document.addEventListener("keydown", (e) => {
			if (e.key === "Escape") close();
		});
		window.addEventListener("resize", () => {
			if (window.innerWidth > 900) close();
		});

		// Accordion sub-nav
		document.querySelectorAll(".pt-sidebar__link[data-has-sub]").forEach((btn) => {
			const subId = btn.dataset.hasSub;
			const sub = document.getElementById(subId);
			if (!sub) return;

			// Auto-open if a child is active
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

	// ── Active nav link ───────────────────────────────────────────────────────

	function markActiveLinks() {
		const path = window.location.pathname;
		document.querySelectorAll(".pt-sidebar__link[href], .pt-sidebar__sub a").forEach((a) => {
			try {
				const match = new URL(a.href, location.origin).pathname === path;
				a.classList.toggle("active", match);
			} catch {}
		});
	}

	// ── Toast ─────────────────────────────────────────────────────────────────

	window.ptToast = function (msg, type = "info", duration = 3500) {
		const icons = {
			success: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>`,
			error:   `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
			info:    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
		};
		const wrap = document.getElementById("pt-toasts");
		if (!wrap) return;
		const el = document.createElement("div");
		el.className = `pt-toast pt-toast--${type}`;
		el.innerHTML = (icons[type] || icons.info) + `<span>${esc(msg)}</span>`;
		wrap.appendChild(el);
		setTimeout(() => {
			el.classList.add("out");
			setTimeout(() => el.remove(), 250);
		}, duration);
	};

	// ── Track form ────────────────────────────────────────────────────────────

	function initTrackForm() {
		const form = document.querySelector("#pt-track-form");
		if (!form) return;

		form.addEventListener("submit", async (e) => {
			e.preventDefault();
			const awb = (form.querySelector("#awb-input")?.value || "").trim();
			if (!awb) return;
			const resultEl = document.querySelector("#pt-track-result");
			const loadingEl = document.querySelector("#pt-track-loading");
			if (resultEl) resultEl.innerHTML = "";
			if (loadingEl) loadingEl.style.display = "block";
			try {
				const res = await fetch(
					`/api/method/awbix.portal.api.track_shipment?awb=${encodeURIComponent(awb)}`,
					{ headers: { "X-Frappe-CSRF-Token": frappe.csrf_token } }
				);
				const data = await res.json();
				if (loadingEl) loadingEl.style.display = "none";
				renderTrackResult(data.message, resultEl);
			} catch {
				if (loadingEl) loadingEl.style.display = "none";
				if (resultEl) resultEl.innerHTML = alertHtml("error", "Unable to fetch tracking data.");
			}
		});
	}

	function renderTrackResult(data, container) {
		if (!container) return;
		if (!data || data.error) {
			container.innerHTML = alertHtml("warning", data?.error || "AWB not found.");
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
              ${infoItem("Origin", data.origin || "—")}
              ${infoItem("Destination", data.destination || "—")}
              ${infoItem("Pieces", data.pieces ?? "—")}
              ${infoItem("Weight", data.weight ? data.weight + " kg" : "—")}
            </div>
            ${data.events?.length ? `
              <div style="font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.07em;color:var(--pt-text-muted);margin-bottom:.75rem">Tracking Events</div>
              <div class="pt-timeline">${data.events.map((ev, i) => `
                <div class="pt-timeline__item ${i === 0 ? "current" : "done"}">
                  <div class="pt-timeline__item__title">${esc(ev.title)}</div>
                  <div class="pt-timeline__item__meta">${esc(ev.location || "")}${ev.time ? " · " + esc(ev.time) : ""}</div>
                </div>`).join("")}</div>` : ""}
          </div>
        </div>
      </div>`;
	}

	// ── Tabs ──────────────────────────────────────────────────────────────────

	window.ptInitTabs = function (containerSelector) {
		const container = document.querySelector(containerSelector);
		if (!container) return;

		// Tabs are in the container; panels are siblings of container or in container's parent
		const tabs   = container.querySelectorAll(".pt-tab");
		const scope  = container.parentElement;
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
				if (e.key === "ArrowRight") activate(Math.min(idx + 1, tabs.length - 1));
				if (e.key === "ArrowLeft")  activate(Math.max(idx - 1, 0));
			});
		});

		const already = [...tabs].findIndex((t) => t.classList.contains("active"));
		if (already < 0 && tabs.length) activate(0);
	};

	// ── Helpers ───────────────────────────────────────────────────────────────

	function alertHtml(type, msg) {
		const icon = type === "warning"
			? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`
			: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`;
		return `<div class="pt-alert pt-alert--${type}" style="margin-top:1rem">${icon}${esc(msg)}</div>`;
	}

	function infoItem(label, value) {
		return `<div class="pt-info-item"><div class="pt-info-item__label">${esc(label)}</div><div class="pt-info-item__value">${esc(String(value))}</div></div>`;
	}

	function esc(s) {
		return String(s ?? "")
			.replace(/&/g, "&amp;").replace(/</g, "&lt;")
			.replace(/>/g, "&gt;").replace(/"/g, "&quot;");
	}

	// ── Init ──────────────────────────────────────────────────────────────────

	document.addEventListener("DOMContentLoaded", () => {
		initTheme();
		initSidebar();
		markActiveLinks();
		initTrackForm();
	});
})();
