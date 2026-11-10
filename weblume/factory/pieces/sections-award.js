/* Pieces written for Weblume after patterns described in the award-site library (knowledge/inspiration, MIT):
   original code, the patterns only. Each reads window.SITE and the shared CSS variables. */
(function (P) {
  var img = function (src, alt, cls) { return src ? '<img' + (cls ? ' class="' + cls + '"' : "") + ' src="' + SITEKIT.esc(src) + '" alt="' + SITEKIT.esc(alt || "") + '" loading="lazy">' : ""; };
  var lines = function (S) { return (S.heroLines || [S.tagline || S.name]).map(function (l) { return "<span>" + SITEKIT.esc(l) + "</span>"; }).join(""); };

  P["hero-name-photo"] = { // "name under a photograph": a photo on top, the name huge on a flat band below
    css: ".hnp{min-height:calc(100svh - var(--nav));display:grid;grid-template-rows:58fr 42fr}.hnp figure{background:var(--surface)}" +
      ".hnp .band{background:var(--accent);color:var(--on-accent);display:flex;flex-direction:column;justify-content:center;padding:clamp(16px,3vh,32px) var(--gut)}" +
      ".hnp h1{font-size:clamp(64px,17vw,280px);line-height:.9;letter-spacing:-.02em;white-space:nowrap;overflow:hidden}" +
      ".hnp .row{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:12px 24px;margin-top:12px}.hnp p{font-size:var(--lead);max-width:26em}",
    render: function (S, t) {
      var m = S.media || {};
      return '<section class="hnp" id="top"><figure>' + img(m.heroImg, S.name) + '</figure><div class="band"><h1>' + SITEKIT.esc(S.word || S.name) +
        '</h1><div class="row"><p>' + SITEKIT.esc(S.tagline) + '</p><a class="btn w" href="#menu">' + t.see + "</a></div></div></section>";
    }
  };
  P["hero-film-title"] = { // "film title on the bottom edge": one photo or clip fills the screen, the title sits on its lower edge
    css: ".hft{position:relative;height:calc(100svh - var(--nav));overflow:hidden;background:var(--surface)}.hft video,.hft img{position:absolute;inset:0}" +
      ".hft .shade{position:absolute;inset:auto 0 0;height:55%;background:linear-gradient(transparent,rgba(0,0,0,.72))}" +
      ".hft .txt{position:absolute;inset-inline:var(--gut);bottom:clamp(20px,6vh,56px);display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:16px 32px}" +
      ".hft h1{font-size:clamp(40px,7vw,120px)}.hft h1 span{display:block}.hft p{max-width:22em;font-size:var(--lead);line-height:1.35}",
    render: function (S, t) {
      var m = S.media || {}, media = m.video ? '<video autoplay muted loop playsinline poster="' + SITEKIT.esc(m.poster || m.heroImg || "") + '" aria-hidden="true"><source src="' +
        SITEKIT.esc(m.video) + '" type="video/mp4"></video>' : img(m.heroImg, S.name);
      return '<section class="hft" id="top">' + media + '<div class="shade"></div><div class="txt"><h1>' + lines(S) + "</h1><div><p>" + SITEKIT.esc(S.lede) +
        '</p><p style="margin-top:18px"><a class="btn a" href="#menu">' + t.see + "</a></p></div></div></section>";
    }
  };
  P["hero-card-room"] = { // "card over a dim room": the place, darkened, with an invitation card in the middle
    css: ".hcr{position:relative;min-height:calc(100svh - var(--nav));display:grid;place-items:center;padding:6vh var(--gut);overflow:hidden;background:var(--surface)}" +
      ".hcr>img{position:absolute;inset:0;filter:brightness(.6)}.hcr .card{position:relative;background:var(--paper);color:var(--ink);border-radius:28px;padding:clamp(28px,4vw,56px);max-width:560px;text-align:center}" +
      ".hcr h1{font-size:clamp(40px,6vw,88px)}.hcr p{margin:14px auto 24px;max-width:24em;color:color-mix(in srgb,var(--ink) 70%,transparent)}.hcr .btn.o{color:var(--ink)}" +
      ".hcr .acts{display:flex;flex-wrap:wrap;justify-content:center;gap:10px}",
    render: function (S, t) {
      return '<section class="hcr" id="top">' + img((S.media || {}).heroImg, "") + '<div class="card rise"><h1>' + SITEKIT.esc(S.name) + "</h1><p>" + SITEKIT.esc(S.lede) +
        '</p><div class="acts"><a class="btn a" href="#menu">' + t.see + '</a><a class="btn o" href="#visit">' + t.visit + "</a></div></div></section>";
    }
  };
  P["hero-waterline"] = { // "headline across two fields": no photo needed; two flat colors, the headline on the seam
    css: ".hwl{min-height:calc(100svh - var(--nav));display:grid;grid-template-rows:1fr 1fr;position:relative}.hwl .up{background:var(--paper)}.hwl .down{background:var(--accent)}" +
      ".hwl h1{position:absolute;inset-inline:var(--gut);top:50%;transform:translateY(-50%);font-size:clamp(48px,10vw,170px);line-height:1;color:var(--ink);mix-blend-mode:normal}" +
      ".hwl h1 span{display:block}.hwl h1 span:last-child{color:var(--on-accent)}.hwl .foot{position:absolute;inset-inline:var(--gut);bottom:clamp(18px,4vh,40px);display:flex;flex-wrap:wrap;gap:12px 24px;justify-content:space-between;align-items:center;color:var(--on-accent)}",
    render: function (S, t) {
      var l = S.heroLines || [S.name, S.tagline];
      return '<section class="hwl" id="top"><div class="up"></div><div class="down"></div><h1><span>' + SITEKIT.esc(l[0]) + "</span><span>" + SITEKIT.esc(l[1] || "") +
        '</span></h1><div class="foot"><p>' + SITEKIT.esc(S.lede) + '</p><a class="btn w" href="#menu">' + t.see + "</a></div></section>";
    }
  };
  P["marquee-band"] = { // a moving strip of the house's names (dishes, drinks): pauses for reduced motion
    css: ".mq{background:var(--accent);color:var(--on-accent);overflow:hidden;padding:clamp(14px,2vw,24px) 0;font:800 clamp(28px,4vw,64px)/1 var(--display);white-space:nowrap}" +
      ".mq div{display:inline-flex;gap:1.2em;animation:mq 30s linear infinite;padding-inline-start:1.2em}.mq span::after{content:'•';margin-inline-start:1.2em;opacity:.5}" +
      "html[dir=rtl] .mq div{animation-name:mqr}@keyframes mq{to{transform:translateX(-50%)}}@keyframes mqr{to{transform:translateX(50%)}}@media (prefers-reduced-motion:reduce){.mq div{animation:none}}",
    render: function (S) {
      var names = [];
      (S.menu || []).forEach(function (c) { (c.items || []).forEach(function (i) { names.push(i.name); }); });
      names = names.slice(0, 10);
      if (!names.length) return "";
      var row = names.map(function (n) { return "<span>" + SITEKIT.esc(n) + "</span>"; }).join("");
      return '<div class="mq" aria-hidden="true"><div>' + row + row + "</div></div>";
    }
  };
  P["about-statement"] = { // "two-line statement, full width": paper and ink only, the about text as a big statement
    css: ".abs{background:var(--paper);color:var(--ink);padding:clamp(80px,12vw,200px) var(--gut)}.abs h2{font-size:clamp(14px,1.1vw,16px);font-family:var(--text);font-weight:700;color:var(--accent);margin-bottom:24px}" +
      ".abs p{font:700 clamp(28px,4.4vw,72px)/1.18 var(--display);max-width:20em}",
    render: function (S, t) {
      return '<section class="abs" id="about"><h2 class="rise">' + t.about + '</h2><p class="rise" style="--i:1">' + SITEKIT.esc(S.about) + "</p></section>";
    }
  };
  P["menu-sticky-photo"] = { // "menu column beside a sticky photo": the list scrolls, the photo stays
    css: ".msp{display:grid;gap:12px;padding:12px;background:var(--ink)}.msp .list{background:var(--surface);border-radius:20px;padding:clamp(28px,4vw,64px)}" +
      ".msp h2{font-size:var(--head);margin-bottom:24px}.msp h3{color:var(--accent);font-size:var(--lead);margin:28px 0 8px}" +
      ".msp .it{display:flex;justify-content:space-between;gap:16px;padding:10px 0;border-bottom:1px dashed color-mix(in srgb,var(--muted) 40%,transparent)}" +
      ".msp .it small{display:block;color:var(--muted)}.msp .it i{font-style:normal;font-weight:700;color:var(--accent);white-space:nowrap}" +
      ".msp figure{border-radius:20px;overflow:hidden;background:var(--surface);min-height:50vh}@media (min-width:860px){.msp{grid-template-columns:1fr 1fr}.msp figure{position:sticky;top:calc(var(--nav) + 12px);height:calc(100svh - var(--nav) - 24px)}}",
    render: function (S, t) {
      var m = S.media || {};
      return '<section class="msp" id="menu"><div class="list"><h2>' + t.menu + "</h2>" + (S.menu || []).map(function (c) {
        return "<h3>" + SITEKIT.esc(c.cat) + "</h3>" + (c.items || []).map(function (i) {
          return '<div class="it"><div><b>' + SITEKIT.esc(i.name) + "</b>" + (i.desc ? "<small>" + SITEKIT.esc(i.desc) + "</small>" : "") + "</div>" +
            (i.price ? "<i>" + SITEKIT.esc(i.price) + t.cur + "</i>" : "") + "</div>";
        }).join("");
      }).join("") + "</div><figure>" + img((m.about || {}).src || m.heroImg, S.name) + "</figure></section>";
    }
  };
  P["menu-tiles"] = { // "specimen catalogue": every item alone on a flat tile, same scale, named plainly
    css: ".mtl{padding:clamp(64px,9vw,140px) var(--gut);background:var(--paper);color:var(--ink)}.mtl h2{font-size:var(--giant);line-height:1;margin-bottom:clamp(24px,4vw,56px)}" +
      ".mtl .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,230px),1fr));gap:12px}" +
      ".mtl article{border-radius:18px;overflow:hidden;background:color-mix(in srgb,var(--accent) 14%,var(--paper))}.mtl article:nth-child(3n+2){background:color-mix(in srgb,var(--accent) 26%,var(--paper))}" +
      ".mtl figure{aspect-ratio:1}.mtl article div{padding:14px 16px 18px}.mtl b{font:700 19px/1.3 var(--display)}.mtl small{display:block;color:color-mix(in srgb,var(--ink) 60%,transparent)}" +
      ".mtl i{display:block;font-style:normal;font-weight:700;margin-top:6px}",
    render: function (S, t) {
      var all = [];
      (S.menu || []).forEach(function (c) { (c.items || []).forEach(function (i) { all.push(i); }); });
      return '<section class="mtl" id="menu"><h2 class="rise">' + t.menu + '</h2><div class="grid">' + all.map(function (i, k) {
        return '<article class="rise" style="--i:' + (k % 4) + '">' + (i.img ? "<figure>" + img(i.img, i.name) + "</figure>" : "") + "<div><b>" + SITEKIT.esc(i.name) + "</b>" +
          (i.desc ? "<small>" + SITEKIT.esc(i.desc) + "</small>" : "") + (i.price ? "<i>" + SITEKIT.esc(i.price) + t.cur + "</i>" : "") + "</div></article>";
      }).join("") + "</div></section>";
    }
  };
  P["gallery-sheet"] = { // "contact sheet": columns of photos at their natural shapes, like a photographer's sheet
    css: ".gsh{padding:clamp(64px,9vw,140px) 12px;background:var(--ink)}.gsh h2{padding-inline:calc(var(--gut) - 12px);margin-bottom:24px}" +
      ".gsh .cols{columns:2 160px;column-gap:12px}.gsh figure{break-inside:avoid;margin-bottom:12px;border-radius:14px;overflow:hidden;background:var(--surface)}.gsh img{height:auto}" +
      "@media (min-width:860px){.gsh .cols{columns:4}}",
    render: function (S, t) {
      var g = (S.media || {}).gallery || [];
      if (g.length < 3) return "";
      return '<section class="gsh" id="gallery"><h2 class="rise">' + t.gallery + '</h2><div class="cols">' +
        g.map(function (p) { return '<figure class="rise">' + img(p.src, p.alt) + "</figure>"; }).join("") + "</div></section>";
    }
  };
  P["steps-order"] = { // how ordering works, in three real steps (no invented numbers)
    css: ".sto{background:var(--surface);padding:clamp(64px,9vw,140px) var(--gut)}.sto h2{margin-bottom:clamp(24px,4vw,48px)}" +
      ".sto ol{list-style:none;display:grid;gap:12px;counter-reset:s}@media (min-width:860px){.sto ol{grid-template-columns:repeat(3,1fr)}}" +
      ".sto li{background:var(--ink);border-radius:22px;padding:28px;counter-increment:s}.sto li::before{content:counter(s);display:block;font:800 clamp(48px,6vw,88px)/1 var(--display);color:var(--accent);margin-bottom:12px}" +
      ".sto b{font:700 var(--lead)/1.25 var(--display)}.sto p{color:var(--muted);margin-top:6px}",
    render: function (S, t) {
      var ar = t.lang !== "en", st = ar ? [["اختار من المنيو", "شوف الأصناف والأسعار"], ["ابعتلنا على واتساب", "اكتب طلبك أو احجز ترابيزة"], ["استلم أو تعالى", "نجهزه في معاده"]]
        : [["Pick from the menu", "See the dishes and prices"], ["Message us on WhatsApp", "Send your order or book a table"], ["Pick it up or come in", "Ready on time"]];
      return '<section class="sto" id="order"><h2 class="rise">' + (ar ? "اطلب في ٣ خطوات" : "Order in 3 steps") + "</h2><ol>" +
        st.map(function (s, i) { return '<li class="rise" style="--i:' + i + '"><b>' + s[0] + "</b><p>" + s[1] + "</p></li>"; }).join("") +
        '</ol><p style="margin-top:28px"><a class="btn a" href="' + SITEKIT.wa(ar ? "أهلاً، عايز أطلب" : "Hello, I'd like to order") + '" target="_blank" rel="noopener noreferrer">' + t.wa + "</a></p></section>";
    }
  };
})(window.PIECES = window.PIECES || {});
