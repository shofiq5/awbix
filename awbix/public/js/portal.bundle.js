// AWBix Portal — theme switcher, mobile nav, keyboard nav, track form

(function () {
	"use strict";

	// ── Theme ─────────────────────────────────────────────────────────────────

	const THEME_KEY = "awbix_portal_theme";
	const VALID_THEMES = ["ocean", "teal", "dark"];

	function applyTheme(theme) {
		if (!VALID_THEMES.includes(theme)) theme = "ocean";
		document.documentElement.setAttribute("data-portal-theme", theme);
		localStorage.setItem(THEME_KEY, theme);
		document.querySelectorAll(".theme-dot").forEach((el) => {
			el.classList.toggle("active", el.dataset.theme === theme);
			el.setAttribute("aria-pressed", el.dataset.theme === theme ? "true" : "false");
		});
	}

	function initTheme() {
		const saved = localStorage.getItem(THEME_KEY) || "ocean";
		applyTheme(saved);
		document.querySelectorAll(".theme-dot").forEach((dot) => {
			dot.addEventListener("click", () => applyTheme(dot.dataset.theme));
		});
	}

	// ── Mobile nav ────────────────────────────────────────────────────────────

	function initMobileNav() {
		const hamburger = document.querySelector(".pt-navbar__hamburger");
		const drawer = document.querySelector(".pt-mobile-nav");
		const overlay = document.querySelector(".pt-mobile-nav__overlay");
		if (!hamburger || !drawer) return;

		function openDrawer() {
			drawer.classList.add("open");
			hamburger.classList.add("open");
			hamburger.setAttribute("aria-expanded", "true");
			document.body.style.overflow = "hidden";
		}

		function closeDrawer() {
			drawer.classList.remove("open");
			hamburger.classList.remove("open");
			hamburger.setAttribute("aria-expanded", "false");
			document.body.style.overflow = "";
		}

		hamburger.addEventListener("click", () =>
			drawer.classList.contains("open") ? closeDrawer() : openDrawer()
		);

		overlay?.addEventListener("click", closeDrawer);

		document.addEventListener("keydown", (e) => {
			if (e.key === "Escape" && drawer.classList.contains("open")) closeDrawer();
		});

		// Mobile accordion sub-menus
		drawer.querySelectorAll(".pt-mobile-nav__link[data-has-sub]").forEach((btn) => {
			btn.addEventListener("click", () => {
				const sub = btn.nextElementSibling;
				if (!sub) return;
				const isOpen = sub.classList.toggle("open");
				btn.setAttribute("aria-expanded", isOpen ? "true" : "false");
			});
		});

		window.addEventListener("resize", () => {
			if (window.innerWidth > 768) closeDrawer();
		});
	}

	// ── Active link ───────────────────────────────────────────────────────────

	function markActiveLink() {
		const path = window.location.pathname;

		document.querySelectorAll(".pt-navbar__link[href], .pt-mobile-nav__link[href]").forEach((a) => {
			try {
				if (new URL(a.href, location.origin).pathname === path) {
					a.classList.add("active");
				}
			} catch {}
		});

		// Highlight parent nav item when a dropdown child is active
		document.querySelectorAll(".pt-navbar__dropdown li a").forEach((a) => {
			try {
				if (new URL(a.href, location.origin).pathname === path) {
					a.closest(".pt-navbar__item")
						?.querySelector(".pt-navbar__link")
						?.classList.add("active");
				}
			} catch {}
		});
	}

	// ── Keyboard accessibility for desktop dropdowns ───────────────────────────

	function initKeyboardNav() {
		document.querySelectorAll(".pt-navbar__item").forEach((item) => {
			const trigger = item.querySelector(".pt-navbar__link");
			const dropdown = item.querySelector(".pt-navbar__dropdown");
			if (!trigger || !dropdown) return;

			trigger.addEventListener("keydown", (e) => {
				if (e.key === "Enter" || e.key === " ") {
					e.preventDefault();
					const visible = dropdown.style.opacity === "1";
					dropdown.style.opacity = visible ? "0" : "1";
					dropdown.style.pointerEvents = visible ? "none" : "auto";
					dropdown.style.transform = visible ? "translateY(-6px)" : "translateY(0)";
				}
				if (e.key === "Escape") {
					dropdown.style.opacity = "0";
					dropdown.style.pointerEvents = "none";
					dropdown.style.transform = "translateY(-6px)";
				}
			});
		});
	}

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

			const csrf = window.frappe?.csrf_token || "";

			try {
				const res = await fetch(
					`/api/method/awbix.portal.api.track_shipment?awb=${encodeURIComponent(awb)}`,
					{ headers: { "X-Frappe-CSRF-Token": csrf } }
				);
				const data = await res.json();
				if (loadingEl) loadingEl.style.display = "none";
				renderTrackResult(data.message, resultEl);
			} catch {
				if (loadingEl) loadingEl.style.display = "none";
				if (resultEl)
					resultEl.innerHTML = alertHtml("error", "Unable to fetch tracking data. Please try again.");
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
      <div class="pt-track-result" style="margin-top:1.5rem">
        <div class="pt-card">
          <div class="pt-card__header">
            <h3>AWB: <span style="font-family:monospace;font-size:.95rem;color:var(--pt-primary);font-weight:700">${esc(data.awb_number)}</span></h3>
            <span class="pt-badge pt-badge--${esc(data.status_class)}">${esc(data.status)}</span>
          </div>
          <div class="pt-card__body">
            <div class="pt-info-grid">
              ${infoItem("Origin", data.origin || "—")}
              ${infoItem("Destination", data.destination || "—")}
              ${infoItem("Pieces", data.pieces ?? "—")}
              ${infoItem("Weight", data.weight ? data.weight + " kg" : "—")}
            </div>
            ${
							data.events?.length
								? `<div style="margin-top:1rem"><div style="font-size:.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--pt-text-muted);margin-bottom:.75rem">Tracking Events</div>
              <div class="pt-timeline">${data.events
								.map(
									(ev, i) => `
                <div class="pt-timeline__item ${i === 0 ? "current" : "done"}">
                  <div class="pt-timeline__item__title">${esc(ev.title)}</div>
                  <div class="pt-timeline__item__meta">${esc(ev.location || "")}${ev.time ? " · " + esc(ev.time) : ""}</div>
                </div>`
								)
								.join("")}</div></div>`
								: ""
						}
          </div>
        </div>
      </div>`;
	}

	function infoItem(label, value) {
		return `<div class="pt-info-item"><div class="pt-info-item__label">${esc(label)}</div><div class="pt-info-item__value">${esc(String(value))}</div></div>`;
	}

	function alertHtml(type, msg) {
		const icons = {
			error: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
			warning: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
		};
		return `<div class="pt-alert pt-alert--${type}" style="margin-top:1rem">${icons[type] || ""}${esc(msg)}</div>`;
	}

	function esc(str) {
		return String(str ?? "")
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;");
	}

	// ── Init ──────────────────────────────────────────────────────────────────

	document.addEventListener("DOMContentLoaded", () => {
		initTheme();
		initMobileNav();
		markActiveLink();
		initKeyboardNav();
		initTrackForm();
	});
})();
