/* Weblume motion kit: injected into every site Karim builds. Vanilla JS, no libraries. */
(() => {
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches, $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const ready = fn => document.readyState === "loading" ? document.addEventListener("DOMContentLoaded", fn) : fn();
  ready(() => {
    const root = document.documentElement;
    // page loader + scroll progress bar (created here, so templates need no extra markup)
    if (!document.getElementById("wl-loader")) { const l = document.createElement("div"); l.id = "wl-loader"; l.innerHTML = "<span></span>"; document.body.prepend(l) }
    addEventListener("load", () => root.classList.add("wl-loaded")); setTimeout(() => root.classList.add("wl-loaded"), 2500);
    const bar = document.createElement("div"); bar.id = "wl-progress"; document.body.append(bar);

    // split headings into words that rise one by one
    $$(".split").forEach(el => {
      if (el.dataset.wlSplit) return; el.dataset.wlSplit = 1;
      const words = el.textContent.trim().split(/\s+/);
      el.textContent = "";
      words.forEach((w, i) => { const o = document.createElement("span"), n = document.createElement("span"); o.className = "w"; o.style.setProperty("--i", i); n.textContent = w; o.append(n); el.append(o, " ") });
    });
    // stagger children: <div data-stagger> children get --i
    $$("[data-stagger]").forEach(p => [...p.children].forEach((c, i) => { c.style.setProperty("--i", i); c.classList.add("reveal") }));

    // reveal on scroll
    const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); if (e.target.matches("[data-count]")) count(e.target) } }), {threshold: .15, rootMargin: "0px 0px -8% 0px"});
    $$(".reveal,.split,[data-count]").forEach(el => reduce ? el.classList.add("in") : io.observe(el));

    // counters: <b data-count="250" data-suffix="+">0</b>
    function count(el) {
      const end = parseFloat(el.dataset.count) || 0, dec = (el.dataset.count.split(".")[1] || "").length, suf = el.dataset.suffix || "", t0 = performance.now(), dur = 1600;
      const fmt = v => v.toLocaleString(document.documentElement.lang || "ar", {minimumFractionDigits: dec, maximumFractionDigits: dec}) + suf;
      if (reduce) { el.textContent = fmt(end); return }
      (function tick(now) { const p = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - p, 3); el.textContent = fmt(end * e); if (p < 1) requestAnimationFrame(tick) })(t0);
    }

    // marquee: duplicate content once so the loop is seamless
    $$(".marquee>div").forEach(d => { if (!d.dataset.wlDup) { d.dataset.wlDup = 1; d.innerHTML += d.innerHTML } });

    const fine = matchMedia("(hover:hover) and (pointer:fine)").matches;
    if (!reduce && fine) {
      // 3D tilt cards
      $$(".tilt").forEach(c => {
        c.addEventListener("pointermove", e => { const r = c.getBoundingClientRect(), x = (e.clientX - r.left) / r.width - .5, y = (e.clientY - r.top) / r.height - .5; c.style.transform = `perspective(900px) rotateY(${x * 12}deg) rotateX(${-y * 12}deg)` });
        c.addEventListener("pointerleave", () => { c.style.transform = "" });
      });
      // magnetic buttons
      $$(".magnetic").forEach(b => {
        b.addEventListener("pointermove", e => { const r = b.getBoundingClientRect(); b.style.transform = `translate(${(e.clientX - r.left - r.width / 2) * .3}px,${(e.clientY - r.top - r.height / 2) * .4}px)` });
        b.addEventListener("pointerleave", () => { b.style.transform = "" });
      });
      // soft glow that follows the cursor (opt-in: <body data-glow>)
      if (document.body.hasAttribute("data-glow")) {
        const g = document.createElement("div"); g.id = "wl-glow"; document.body.prepend(g);
        addEventListener("pointermove", e => { root.classList.add("wl-glow-on"); g.style.left = e.clientX + "px"; g.style.top = e.clientY + "px" }, {passive: true});
      }
    }

    // scroll effects: progress bar, header shadow, parallax (data-speed="0.2")
    const header = document.querySelector("header"), par = reduce ? [] : $$("[data-speed]");
    let ticking = false;
    function onScroll() {
      const y = scrollY, max = document.documentElement.scrollHeight - innerHeight;
      bar.style.transform = `scaleX(${max > 0 ? y / max : 0})`;
      header && header.classList.toggle("wl-header-scrolled", y > 20);
      par.forEach(el => { el.style.transform = `translateY(${y * parseFloat(el.dataset.speed)}px)` });
      ticking = false;
    }
    addEventListener("scroll", () => { if (!ticking) { ticking = true; requestAnimationFrame(onScroll) } }, {passive: true}); onScroll();

    // mobile menu: a button with [data-menu-toggle] opens the element with [data-menu]
    $$("[data-menu-toggle]").forEach(b => b.addEventListener("click", () => { const open = root.classList.toggle("wl-menu-open"); b.setAttribute("aria-expanded", open) }));
    $$("[data-menu] a").forEach(a => a.addEventListener("click", () => root.classList.remove("wl-menu-open")));

    // Arabic / English: any element with data-en="English text" switches; Arabic stays in the markup
    const flip = lang => {
      $$("[data-en]").forEach(el => { if (el.dataset.ar == null) el.dataset.ar = el.textContent; el.textContent = lang === "en" ? el.dataset.en : el.dataset.ar });
      $$("[data-en-placeholder]").forEach(el => { if (el.dataset.arPlaceholder == null) el.dataset.arPlaceholder = el.placeholder; el.placeholder = lang === "en" ? el.dataset.enPlaceholder : el.dataset.arPlaceholder });
      root.lang = lang; root.dir = lang === "en" ? "ltr" : "rtl";
      $$("[data-lang-toggle]").forEach(b => b.textContent = lang === "en" ? "عربي" : "EN");
      try { localStorage.setItem("wl-lang", lang) } catch (e) {}
    };
    $$("[data-lang-toggle]").forEach(b => b.addEventListener("click", () => flip(root.lang === "en" ? "ar" : "en")));
    try { if (localStorage.getItem("wl-lang") === "en") flip("en") } catch (e) {}

    // WhatsApp: <body data-wa="2010xxxxxxx">, links/buttons with data-wa-msg="text" open a chat with that text
    const wa = (document.body.dataset.wa || "").replace(/\D/g, "");
    $$("[data-wa-msg]").forEach(el => el.addEventListener("click", e => {
      e.preventDefault();
      const extra = el.dataset.waFrom ? "\n" + [...document.querySelectorAll(el.dataset.waFrom)].map(i => i.value).filter(Boolean).join("\n") : "";
      const url = "https://wa.me/" + wa + "?text=" + encodeURIComponent(el.dataset.waMsg + extra);
      if (wa) open(url, "_blank", "noopener"); else alert("Add the WhatsApp number in <body data-wa>");
    }));
  });
})();
