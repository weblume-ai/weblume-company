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

  /* lively and cinematic: text blocks, list rows, cards and the footer word come in one after another, and a thin bar
     shows how far you've read. Parts that move themselves (3D, pinned, carousels, labels) are left alone. */
  if (!still && motion !== "calm") {
    var own = ".pin,.gcv,.mrl,.hrg,.hst,.hsc,.hbp,.fsc,.alb,.ctb,.mq,.bst,.hwd,.hfr";
    [].forEach.call(document.querySelectorAll("#app section p, #app section li, #app section h3, #app section table, #app section .acts, #app section .tile, #app footer .huge"), function (el) {
      if (el.classList.contains("rise") || el.closest(own) || el.parentElement.closest(".rise") || el.querySelector(".rise")) return;
      var cs = getComputedStyle(el); if (cs.transform !== "none" || cs.animationName !== "none") return; // a tilted polaroid keeps its tilt
      el.classList.add("rise");
      el.style.setProperty("--i", Array.prototype.indexOf.call(el.parentElement.children, el) % 6);
    });
    var bar = document.createElement("div"), qb = false;
    bar.className = "readbar"; bar.setAttribute("aria-hidden", "true"); document.body.appendChild(bar);
    var fillBar = function () { qb = false; var h = document.documentElement.scrollHeight - innerHeight; bar.style.transform = "scaleX(" + (h > 0 ? Math.min(1, scrollY / h) : 0).toFixed(4) + ")"; };
    addEventListener("scroll", function () { if (!qb) { qb = true; requestAnimationFrame(fillBar); } }, {passive: true}); fillBar();

    /* big headings slide sideways as their section passes (like Loopie's words); buttons lean toward the pointer */
    var heads = [].filter.call(document.querySelectorAll("#app section h2, #app footer .huge"), function (h) { return !h.closest(own); });
    var reach = motion === "cinematic" ? 9 : 5, qh = false;
    var slide = function () {
      qh = false;
      heads.forEach(function (h, k) {
        var r = h.getBoundingClientRect(); if (r.bottom < -200 || r.top > innerHeight + 200) return;
        var p = (r.top + r.height / 2) / innerHeight - .5; // -0.5 (top) … 0.5 (bottom)
        h.style.translate = (p * reach * (k % 2 ? -1 : 1)).toFixed(2) + "vw 0";
      });
    };
    addEventListener("scroll", function () { if (!qh) { qh = true; requestAnimationFrame(slide); } }, {passive: true}); slide();
    if (matchMedia("(hover: hover)").matches) [].forEach.call(document.querySelectorAll("#app .btn"), function (b) {
      b.addEventListener("pointermove", function (e) { var r = b.getBoundingClientRect(); b.style.translate = ((e.clientX - r.left - r.width / 2) * .25).toFixed(1) + "px " + ((e.clientY - r.top - r.height / 2) * .35).toFixed(1) + "px"; });
      b.addEventListener("pointerleave", function () { b.style.translate = ""; });
    });
  }

  /* cinematic sites open like a film: the name in the middle, a counter to 100, then the curtain lifts.
     Once per visit, and never for the automatic review (its screenshots must show the page). */
  if (!still && motion === "cinematic" && !navigator.webdriver) {
    var seen = false;
    try { seen = !!sessionStorage.getItem("wl-intro"); sessionStorage.setItem("wl-intro", "1"); } catch (e) { seen = true; } // no storage (a sandboxed preview): no curtain
    if (!seen) {
      var cur = document.createElement("div"), num = document.createElement("i"), t0 = performance.now();
      cur.className = "curtain"; cur.setAttribute("aria-hidden", "true");
      cur.innerHTML = "<b>" + SITEKIT.esc(S.word || S.name) + "</b>"; cur.appendChild(num); document.body.appendChild(cur);
      (function count(now) {
        var k = Math.min(1, (now - t0) / 1100);
        num.textContent = String(Math.round(k * 100)).padStart(3, "0");
        if (k < 1) return requestAnimationFrame(count);
        cur.classList.add("go"); setTimeout(function () { cur.remove(); }, 900);
      })(t0);
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
