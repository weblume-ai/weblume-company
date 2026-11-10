/* about-say, menu-cols, invite-video, gallery-track, visit, footer-huge, bar — from Loopie, made independent.
   Each reads only window.SITE and the shared CSS variables. */
(function (P) {
  P["about-say"] = { // a big statement on the accent color, with one photo
    css: ".say{background:var(--accent);color:var(--on-accent);padding:clamp(72px,10vw,160px) var(--gut);display:grid;gap:40px;align-items:center}" +
      ".say .big{font:500 clamp(22px,2.4vw,36px)/1.45 var(--display);max-width:24em;margin-top:clamp(18px,3vw,36px)}" +
      ".say figure{aspect-ratio:1;width:min(100%,620px);justify-self:center}@media (min-width:860px){.say{grid-template-columns:7fr 5fr;gap:64px}}",
    render: function (S, t) {
      var K = SITEKIT, ph = (S.media || {}).about;
      return '<section class="say" id="about"><div><h2 class="rise">' + K.esc(S.together || S.name) + '</h2><p class="big rise" style="--i:1">' + K.esc(S.about) + "</p></div>" +
        (ph ? '<figure class="disc rise" style="--i:2"><img src="' + K.esc(ph.src) + '" alt="' + K.esc(ph.alt) + '" loading="lazy"></figure>' : "") + "</section>";
    }
  };
  P["menu-cols"] = { // categories in two columns, prices in the accent color, filter chips
    css: ".menu{background:var(--ink);padding:clamp(72px,10vw,160px) var(--gut)}.mhead{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:12px 24px;margin-bottom:clamp(32px,5vw,80px)}" +
      ".menu h2{font-size:var(--giant);line-height:1}.chips{display:flex;flex-wrap:wrap;gap:8px}.chips button{min-height:44px;padding:0 18px;border-radius:999px;border:2px solid var(--muted);background:none;color:inherit;font:700 var(--small) var(--text);cursor:pointer}" +
      ".chips button[aria-pressed=true]{background:var(--accent);border-color:var(--accent);color:var(--on-accent)}" +
      ".cols{display:grid;gap:clamp(48px,6vw,104px) clamp(32px,6vw,96px)}@media (min-width:860px){.cols{grid-template-columns:1fr 1fr}}" +
      ".cat header{display:flex;align-items:center;gap:18px;margin-bottom:14px}.cat header figure{width:clamp(80px,8vw,128px);aspect-ratio:1;flex:none;background:var(--surface)}" +
      ".cat h3{font-size:var(--lead);color:var(--accent)}.it{padding:12px 0;border-bottom:1px solid color-mix(in srgb,var(--muted) 25%,transparent)}" +
      ".it div{display:flex;align-items:baseline;justify-content:space-between;gap:16px}.it b{font:700 clamp(20px,1.8vw,26px)/1.3 var(--display)}" +
      ".it i{flex:none;font-style:normal;font-weight:700;color:var(--accent);font-variant-numeric:tabular-nums}.it p{color:var(--muted);line-height:1.45;margin-top:3px}",
    render: function (S, t) {
      var K = SITEKIT, m = S.menu || [];
      return '<section class="menu" id="menu"><div class="mhead"><h2 class="rise">' + t.menu + "</h2>" +
        (m.length > 1 ? '<div class="chips rise" role="group"><button type="button" aria-pressed="true" data-c="-1">' + t.all + "</button>" +
          m.map(function (c, i) { return '<button type="button" aria-pressed="false" data-c="' + i + '">' + K.esc(c.cat) + "</button>"; }).join("") + "</div>" : "") +
        '</div><div class="cols">' + m.map(function (c, i) {
          return '<div class="cat rise" data-c="' + i + '"><header>' + (c.img ? '<figure class="disc"><img src="' + K.esc(c.img) + '" alt="' + K.esc(c.cat) + '" loading="lazy"></figure>' : "") +
            "<h3>" + K.esc(c.cat) + "</h3></header>" + (c.items || []).map(function (it) {
              return '<div class="it"><div><b>' + K.esc(it.name) + "</b>" + (it.price !== "" && it.price != null ? "<i>" + K.esc(it.price) + t.cur + "</i>" : "") + "</div>" +
                (it.desc ? "<p>" + K.esc(it.desc) + "</p>" : "") + "</div>";
            }).join("") + "</div>";
        }).join("") + "</div>" + (S.order ? '<p style="margin-top:40px"><a class="btn a" href="' + K.esc(S.order) + '" target="_blank" rel="noopener noreferrer">' + t.order + "</a></p>" : "") + "</section>";
    },
    init: function () {
      var bs = document.querySelectorAll(".chips button");
      [].forEach.call(bs, function (b) { b.addEventListener("click", function () {
        [].forEach.call(bs, function (x) { x.setAttribute("aria-pressed", x === b); });
        [].forEach.call(document.querySelectorAll(".cat"), function (c) { c.hidden = b.dataset.c !== "-1" && c.dataset.c !== b.dataset.c; });
      }); });
    }
  };
  P["invite-video"] = { // pinned: the clip grows from a small loop to the whole screen, then the invite
    css: ".pour{height:280vh;background:var(--ink)}.pour .vid{position:absolute;left:50%;top:50%;width:100vw;height:100svh;transform:translate(-50%,-50%) scale(.3);border-radius:999px;overflow:hidden;will-change:transform,border-radius}" +
      ".pour .inv{position:absolute;inset-inline:var(--gut);bottom:clamp(24px,7vh,64px);display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:16px 32px;z-index:2;opacity:0;transition:opacity .5s}.pour .inv h2{max-width:14em;text-shadow:0 2px 24px #0008}",
    render: function (S, t) {
      var K = SITEKIT, v = (S.media || {}).video, poster = (S.media || {}).poster;
      if (!v && !poster) return "";
      return '<section class="pin pour" id="invite"><div class="stage"><div class="vid">' + (v ? '<video muted loop playsinline preload="none"' + (poster ? ' poster="' + K.esc(poster) + '"' : "") +
        ' aria-hidden="true"><source src="' + K.esc(v) + '" type="video/mp4"></video>' : '<img src="' + K.esc(poster) + '" alt="">') +
        '</div><div class="inv"><h2>' + K.esc(S.invite || S.tagline) + '</h2><a class="btn a" href="#visit">' + t.visit + "</a></div></div></section>";
    },
    init: function () {
      var K = SITEKIT, sec = document.querySelector(".pour"); if (!sec) return;
      var box = sec.querySelector(".vid"), inv = sec.querySelector(".inv"), vid = sec.querySelector("video");
      function tick() {
        var p = K.progress(sec), g = K.clamp(p / .7), s = .3 + .7 * g * g * (3 - 2 * g);
        box.style.transform = "translate(-50%,-50%) scale(" + s + ")"; box.style.borderRadius = (1 - g) * 999 + "px";
        inv.style.opacity = 1; // the invite reads from the start; only the clip grows
        if (vid) { var r = sec.getBoundingClientRect(), on = r.top < innerHeight && r.bottom > 0; if (on && vid.paused && !K.reduce) vid.play().catch(function () {}); if (!on && !vid.paused) vid.pause(); }
      }
      addEventListener("scroll", function () { requestAnimationFrame(tick); }, {passive: true}); tick();
    }
  };
  P["gallery-track"] = { // pinned: a row of tall photos slides sideways while you scroll down
    css: ".place{height:300vh;background:var(--ink)}.place .stage{display:flex;flex-direction:column;justify-content:center;gap:clamp(16px,3vh,28px);padding-top:var(--nav)}" +
      ".place h2{padding-inline:var(--gut)}.track{display:flex;gap:clamp(12px,1.6vw,24px);padding-inline:var(--gut);height:min(62vh,680px);width:max-content;will-change:transform}" +
      ".track figure{height:100%;aspect-ratio:9/14;flex:none;background:var(--surface)}",
    render: function (S, t) {
      var K = SITEKIT, g = (S.media || {}).gallery || [];
      if (!g.length) return "";
      return '<section class="pin place" id="gallery"><div class="stage"><h2>' + t.gallery + '</h2><div class="track">' +
        g.map(function (p) { return '<figure class="loop"><img src="' + K.esc(p.src) + '" alt="' + K.esc(p.alt) + '" loading="lazy"></figure>'; }).join("") + "</div></div></section>";
    },
    init: function () {
      var K = SITEKIT, sec = document.querySelector(".place"); if (!sec) return;
      var tr = sec.querySelector(".track"), dir = document.documentElement.dir === "rtl" ? 1 : -1;
      function tick() { var max = Math.max(0, tr.scrollWidth - innerWidth); tr.style.transform = "translateX(" + dir * K.progress(sec) * max + "px)"; }
      addEventListener("scroll", function () { requestAnimationFrame(tick); }, {passive: true}); addEventListener("resize", tick); tick();
    }
  };
  P.visit = { // address, hours, WhatsApp and directions, beside a photo of the place (never an embedded map: the owner's rule)
    css: ".visit{background:var(--paper);color:var(--ink);padding:clamp(72px,10vw,160px) var(--gut);display:grid;gap:40px;align-items:center}" +
      ".addr{font:800 var(--lead)/1.3 var(--display);margin-top:18px;max-width:20em}.days{width:100%;max-width:360px;border-collapse:collapse;margin-top:14px}.days td{padding:3px 0}.days td:last-child{text-align:end}" +
      ".visit .acts{display:flex;flex-wrap:wrap;gap:12px;margin-top:28px}.visit .btn.o{color:var(--ink)}" +
      ".visit figure{margin:0;aspect-ratio:4/3;border-radius:var(--r-card);overflow:hidden;background:var(--surface)}.visit figure img{width:100%;height:100%;object-fit:cover;display:block}" +
      "@media (min-width:860px){.visit:has(figure){grid-template-columns:1fr 1fr;gap:64px}}",
    render: function (S, t) {
      var K = SITEKIT, q = encodeURIComponent(S.maps || S.address || S.name), m = S.media || {}, g = m.gallery || [];
      var ph = g.length > 1 ? g[g.length - 1] : g[0] || (m.heroImg ? {src: m.heroImg, alt: S.name} : null);
      return '<section class="visit" id="visit"><div><h2 class="rise">' + t.visit + "</h2>" + (S.address ? '<p class="addr rise" style="--i:1">' + K.esc(S.address) + "</p>" : "") +
        (S.hours && S.hours.length ? '<table class="days rise" style="--i:2"><caption class="sr" style="position:absolute;left:-9999px">' + t.hours + "</caption>" +
          S.hours.map(function (h) { return "<tr><td>" + K.esc(h[0]) + "</td><td>" + K.esc(h[1]) + "</td></tr>"; }).join("") + "</table>" : "") +
        '<div class="acts rise" style="--i:3"><a class="btn a" href="' + K.wa("أهلاً، عايز أحجز / أطلب") + '" target="_blank" rel="noopener noreferrer">' + t.wa + "</a>" +
        '<a class="btn o" href="' + (S.mapsLink ? K.esc(S.mapsLink) : 'https://www.google.com/maps/search/?api=1&query=' + q) + '" target="_blank" rel="noopener noreferrer">' + t.directions + "</a></div></div>" +
        (ph ? '<figure class="rise"><img src="' + K.esc(ph.src) + '" alt="' + K.esc(ph.alt || S.name) + '" loading="lazy"></figure>' : "") + "</section>";
    }
  };
  P["footer-huge"] = { // the brand word as big as the screen, links and the Weblume credit
    css: "footer{background:var(--ink);padding:clamp(48px,6vw,96px) var(--gut) 28px;font-size:var(--small);overflow:hidden}footer .huge{font:800 min(26vw,360px)/1 var(--display);text-align:center;color:var(--accent)}" +
      "footer .row{display:flex;flex-wrap:wrap;justify-content:space-between;gap:10px 28px;margin-top:28px;font-size:var(--body)}footer ul{display:flex;flex-wrap:wrap;gap:20px;font-weight:700}footer .by a{text-decoration:underline}",
    render: function (S, t) {
      var K = SITEKIT, soc = [["instagram", "Instagram"], ["tiktok", "TikTok"]].filter(function (s) { return S[s[0]]; });
      return '<footer><div class="huge" aria-hidden="true">' + K.esc(S.word || S.name) + '</div><div class="row"><ul>' +
        soc.map(function (s) { return '<li><a href="' + K.esc(S[s[0]]) + '" target="_blank" rel="noopener noreferrer">' + s[1] + "</a></li>"; }).join("") +
        '<li><a href="' + K.wa() + '" target="_blank" rel="noopener noreferrer">' + t.wa + '</a></li></ul><div class="by">© ' + new Date().getFullYear() + " " + K.esc(S.name) +
        " · " + t.design + ' <a href="https://weblume-sa.github.io/" target="_blank" rel="noopener noreferrer">Weblume</a>' +
        (S.credits ? ' · <a href="' + K.esc(S.credits) + '" target="_blank" rel="noopener">' + (t.lang === "en" ? "Photo credits" : "حقوق الصور") + "</a>" : "") + "</div></div></footer>";
    }
  };
  P.bar = { // phones: WhatsApp and directions always one tap away
    css: ".bar{position:fixed;inset:auto 0 0;z-index:25;display:grid;grid-template-columns:1fr 1fr;padding-bottom:env(safe-area-inset-bottom);background:var(--ink)}" +
      ".bar a{min-height:56px;display:flex;align-items:center;justify-content:center;font-weight:700}.bar a:first-child{background:var(--accent);color:var(--on-accent)}" +
      "@media (min-width:860px){.bar{display:none}}@media (max-width:859px){body{padding-bottom:56px}}",
    render: function (S, t) {
      var K = SITEKIT;
      return '<nav class="bar" aria-label="quick"><a href="' + K.wa() + '" target="_blank" rel="noopener noreferrer">' + t.wa + '</a><a href="#visit">' + t.directions + "</a></nav>";
    }
  };
})(window.PIECES = window.PIECES || {});
