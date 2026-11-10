/* Weblume site factory runtime: reads window.SITE (data.js), renders the chosen pieces in order, then wires motion.
   Pieces register with PIECE({id, css, render(S, t), init(S, t)}). No piece depends on another. */
(function () {
  "use strict";
  var S = window.SITE || {}, P = window.PIECES || {};
  var store = function (k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } };
  var lang = (new URLSearchParams(location.search).get("lang") || store("site-lang") || S.lang || "ar") === "en" && S.en ? "en" : "ar";
  if (lang === "en") Object.keys(S.en).forEach(function (k) { S[k] = S.en[k]; });
  document.documentElement.lang = lang; document.documentElement.dir = lang === "en" ? "ltr" : "rtl";
  if (S.shape) document.documentElement.dataset.shape = S.shape; // arch | sharp | round | soft | organic
  var UI = {
    ar: {menu: "المنيو", visit: "زورونا", gallery: "الأجواء", about: "عننا", wa: "واتساب", open: "القائمة", close: "إغلاق",
         other: "English", see: "شوف المنيو", order: "اطلب دلوقتي", directions: "الاتجاهات", maps: "افتح في خرائط جوجل",
         hours: "المواعيد", address: "العنوان", design: "تصميم", all: "الكل", hint: "انزل لتحت"},
    en: {menu: "Menu", visit: "Visit", gallery: "The mood", about: "About", wa: "WhatsApp", open: "Menu", close: "Close",
         other: "عربي", see: "See the menu", order: "Order now", directions: "Directions", maps: "Open in Google Maps",
         hours: "Hours", address: "Address", design: "Design by", all: "All", hint: "Scroll down"}
  };
  var t = UI[lang];
  if (S.country === "EG" && lang === "ar") { t.see = "شوف المنيو"; t.order = "اطلب دلوقتي"; }
  t.lang = lang; t.cur = " " + (S.currency || "");

  /* the client's colors and fonts become CSS variables; pieces only use the variables */
  var c = S.colors || {}, f = S.fonts || {}, root = document.documentElement.style;
  [["--ink", c.ink || "#141210"], ["--paper", c.paper || "#ffffff"], ["--accent", c.accent || "#e50914"], ["--muted", c.muted || "#9a948c"],
   ["--surface", c.surface || "#1e1b18"], ["--on-accent", c.onAccent || "#141210"]].forEach(function (v) { root.setProperty(v[0], v[1]); });
  var display = f.display || "Alexandria", text = f.text || "IBM Plex Sans Arabic";
  root.setProperty("--display", "'" + display + "','" + text + "',sans-serif");
  root.setProperty("--text", "'" + text + "',system-ui,sans-serif");
  var fl = document.createElement("link"); fl.rel = "stylesheet";
  fl.href = "https://fonts.googleapis.com/css2?family=" + [display, text].filter(function (x, i, a) { return a.indexOf(x) === i; })
    .map(function (x) { return x.replace(/ /g, "+") + ":wght@400;500;700;800"; }).join("&family=") + "&display=swap";
  document.head.appendChild(fl);
  document.title = (S.name || "") + (S.tagline ? " | " + S.tagline : "");

  window.SITEKIT = {
    esc: function (s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (ch) { return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[ch]; }); },
    wa: function (msg) { var n = String(S.whatsapp || "").replace(/\D/g, ""); return n ? "https://wa.me/" + n + (msg ? "?text=" + encodeURIComponent(msg) : "") : "#visit"; },
    clamp: function (v) { return Math.max(0, Math.min(1, v)); },
    /* 0 → 1 as a pinned section scrolls through its sticky stage */
    progress: function (sec) { var r = sec.getBoundingClientRect(), span = sec.offsetHeight - innerHeight; return span > 0 ? Math.max(0, Math.min(1, -r.top / span)) : 0; },
    reduce: matchMedia("(prefers-reduced-motion: reduce)").matches,
    setLang: function () { store("site-lang", lang === "en" ? "ar" : "en"); location.reload(); }
  };

  var ids = (S.pieces || []).filter(function (id) { return P[id]; }), css = "", html = "";
  ids.forEach(function (id) { css += P[id].css || ""; html += P[id].render(S, t); });
  var st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);
  document.getElementById("app").innerHTML = html;

  /* a photo that fails to load removes its frame instead of leaving a broken image */
  addEventListener("error", function (e) { var el = e.target; if (el && el.tagName === "IMG") { var fig = el.closest("figure"); (fig || el).remove(); } }, true);
  ids.forEach(function (id) { if (P[id].init) P[id].init(S, t); });

  /* motion layer, by data.js "motion": calm (reveals only), lively (default: + drifting photos, word-by-word headings), cinematic (stronger) */
  var motion = S.motion || "lively", still = SITEKIT.reduce;
  if (!still) {
    [].forEach.call(document.querySelectorAll("section:not(.pin) figure"), function (f) { if (f.querySelector("img")) { f.classList.add("mv", "rise"); } });
    if (motion !== "calm") [].forEach.call(document.querySelectorAll("section:not(.pin):not(.hwd):not(.ctb) h2"), function (h) {
      if (h.children.length) return; // only plain-text headings: Arabic words stay whole, letters stay joined
      h.innerHTML = h.textContent.split(/\s+/).filter(Boolean).map(function (w, i) { return '<span class="hw" style="--w:' + i + '">' + SITEKIT.esc(w) + "</span>"; }).join(" ");
      h.classList.add("rise");
    });
    if (motion !== "calm") {
      var drift = motion === "cinematic" ? .16 : .08, figs = document.querySelectorAll(".mv");
      var q = false, tick = function () {
        q = false;
        [].forEach.call(figs, function (f) {
          var r = f.getBoundingClientRect();
          if (r.bottom < 0 || r.top > innerHeight) return;
          f.style.setProperty("--py", ((r.top + r.height / 2 - innerHeight / 2) * -drift).toFixed(1) + "px");
        });
      };
      addEventListener("scroll", function () { if (!q) { q = true; requestAnimationFrame(tick); } }, {passive: true});
      tick();
    }
  }

  /* parts rise in once as they enter */
  var io = "IntersectionObserver" in window && new IntersectionObserver(function (es) {
    es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
  }, {rootMargin: "0px 0px -10% 0px"});
  [].forEach.call(document.querySelectorAll(".rise"), function (el) { io ? io.observe(el) : el.classList.add("in"); });

  /* smooth scroll when Lenis is available (it may be blocked or offline: the page works without it) */
  if (window.Lenis && !SITEKIT.reduce) { var len = new Lenis({lerp: .1}); (function raf(tm) { len.raf(tm); requestAnimationFrame(raf); })(0); }
  [].forEach.call(document.querySelectorAll("[data-lang]"), function (b) { b.textContent = t.other; b.addEventListener("click", SITEKIT.setLang); });
})();
