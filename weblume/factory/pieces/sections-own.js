/* hero-split and menu-rows — from Weblume's own sites (Fluent Route's split hero, TYT Café's product rows). */
(function (P) {
  P["hero-split"] = { // a big headline beside one strong photo; for places without footage
    css: ".hs{min-height:calc(100svh - var(--nav));display:grid;align-items:center;gap:clamp(24px,5vw,72px);padding:clamp(32px,6vh,72px) var(--gut)}" +
      ".hs h1 span{display:block}.hs p{font-size:var(--lead);line-height:1.4;color:var(--muted);margin-top:20px;max-width:24em}.hs .acts{display:flex;flex-wrap:wrap;gap:12px;margin-top:28px}" +
      ".hs figure{aspect-ratio:4/5;border-radius:var(--r-card);overflow:hidden;background:var(--surface)}@media (min-width:860px){.hs{grid-template-columns:7fr 5fr}}",
    render: function (S, t) {
      var K = SITEKIT, lines = S.heroLines || [S.tagline || S.name], img = (S.media || {}).heroImg;
      return '<section class="hs" id="top"><div><h1 class="rise">' + lines.map(function (l) { return "<span>" + K.esc(l) + "</span>"; }).join("") + "</h1>" +
        '<p class="rise" style="--i:1">' + K.esc(S.lede) + '</p><div class="acts rise" style="--i:2"><a class="btn a" href="#menu">' + t.see + '</a><a class="btn o" href="' +
        K.wa() + '" target="_blank" rel="noopener noreferrer">' + t.wa + "</a></div></div>" +
        (img ? '<figure class="rise" style="--i:2"><img src="' + K.esc(img) + '" alt="' + K.esc(S.name) + '"></figure>' : "") + "</section>";
    }
  };
  P["menu-rows"] = { // a row of photo cards per category that scrolls sideways (TYT); best when every item has a photo
    css: ".mrow{padding:clamp(64px,9vw,140px) 0;background:var(--ink)}.mrow>h2{padding-inline:var(--gut);font-size:var(--giant);line-height:1;margin-bottom:clamp(24px,4vw,56px)}" +
      ".mrow h3{padding-inline:var(--gut);font-size:var(--lead);color:var(--accent);margin:32px 0 14px}" +
      ".mrow .row{display:flex;gap:16px;overflow-x:auto;padding:0 var(--gut) 8px;scroll-snap-type:x mandatory;scrollbar-width:thin}" +
      ".mrow article{flex:0 0 clamp(220px,24vw,300px);scroll-snap-align:start;background:var(--surface);border-radius:var(--r-card);overflow:hidden}" +
      ".mrow article figure{aspect-ratio:4/3;background:#2a2622}.mrow article div{padding:14px 16px 18px}.mrow b{font:700 20px/1.3 var(--display)}" +
      ".mrow p{color:var(--muted);font-size:var(--small);margin-top:4px}.mrow i{display:block;font-style:normal;font-weight:700;color:var(--accent);margin-top:8px}",
    render: function (S, t) {
      var K = SITEKIT;
      return '<section class="mrow" id="menu"><h2 class="rise">' + t.menu + "</h2>" + (S.menu || []).map(function (c) {
        return "<h3>" + K.esc(c.cat) + '</h3><div class="row" tabindex="0" aria-label="' + K.esc(c.cat) + '">' + (c.items || []).map(function (it) {
          return "<article>" + (it.img ? '<figure><img src="' + K.esc(it.img) + '" alt="' + K.esc(it.name) + '" loading="lazy"></figure>' : "") +
            "<div><b>" + K.esc(it.name) + "</b>" + (it.desc ? "<p>" + K.esc(it.desc) + "</p>" : "") + (it.price !== "" && it.price != null ? "<i>" + K.esc(it.price) + t.cur + "</i>" : "") + "</div></article>";
        }).join("") + "</div>";
      }).join("") + "</section>";
    }
  };
})(window.PIECES = window.PIECES || {});
