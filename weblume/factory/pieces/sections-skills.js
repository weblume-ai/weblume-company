/* Pieces written for Weblume after effect ideas in the design skills (React Bits effects, ui-ux-pro-max motion presets):
   original vanilla code, the ideas only. Arabic is animated word by word, never letter by letter (letters must stay joined). */
(function (P) {
  var E = function (s) { return SITEKIT.esc(s); };
  var img = function (src, alt, extra) { return src ? '<img src="' + E(src) + '" alt="' + E(alt || "") + '" loading="lazy"' + (extra || "") + ">" : ""; };
  var words = function (text, cls) { // each word in its own span with a growing delay
    return String(text || "").split(/\s+/).filter(Boolean).map(function (w, i) { return '<span class="' + cls + '" style="--w:' + i + '">' + E(w) + "</span>"; }).join(" ");
  };
  var items = function (S) { var a = []; (S.menu || []).forEach(function (c) { (c.items || []).forEach(function (i) { a.push(i); }); }); return a; };
  var onScroll = function (fn) { var q = false; addEventListener("scroll", function () { if (!q) { q = true; requestAnimationFrame(function () { q = false; fn(); }); } }, {passive: true}); addEventListener("resize", fn); fn(); };

  P["hero-arch"] = { // one photo in a tall arched window, the headline split above and below it
    css: ".har{min-height:calc(100svh - var(--nav));display:grid;place-items:center;text-align:center;gap:clamp(14px,2.4vh,24px);padding:clamp(24px,5vh,56px) var(--gut)}" +
      ".har h1{font-size:clamp(40px,7.4vw,124px);line-height:1}.har .win{width:min(70vw,360px);aspect-ratio:3/4;border-radius:999px 999px 24px 24px;overflow:hidden;background:var(--surface)}" +
      ".har p{max-width:30em;color:var(--muted);font-size:var(--lead);line-height:1.4}@media (min-width:860px){.har{grid-template-columns:1fr auto 1fr;text-align:start}.har h1:last-of-type{text-align:end}.har p{grid-column:1/-1;text-align:center;margin-inline:auto}}",
    render: function (S, t) {
      var l = S.heroLines || [S.name, S.tagline], m = S.media || {};
      return '<section class="har" id="top"><h1 class="rise">' + E(l[0]) + '</h1><div class="win rise" style="--i:1">' + img(m.heroImg, S.name) + '</div><h1 class="rise" style="--i:2">' +
        E(l[1] || S.tagline || "") + '</h1><p class="rise" style="--i:3">' + E(S.lede) + ' <br><a class="btn a" style="margin-top:18px" href="#menu">' + t.see + "</a></p></section>";
    }
  };
  P["hero-words"] = { // the headline arrives word by word, three round photos float around it
    css: ".hwd{position:relative;min-height:calc(100svh - var(--nav));display:grid;place-items:center;text-align:center;padding:8vh var(--gut);overflow:hidden}" +
      ".hwd h1{font-size:clamp(44px,8vw,140px);line-height:1.05;max-width:12em;position:relative;z-index:2;text-shadow:0 2px 30px var(--ink),0 0 2px var(--ink)}.hwd p{position:relative;z-index:2;margin-top:20px;font-size:var(--lead);color:var(--muted)}" +
      ".hwd .wd{display:inline-block;opacity:0;transform:translateY(.4em);filter:blur(8px);transition:opacity .7s,transform .7s cubic-bezier(.2,.7,.2,1),filter .7s;transition-delay:calc(var(--w)*110ms)}" +
      ".hwd.on .wd{opacity:1;transform:none;filter:none}.hwd figure{position:absolute;width:clamp(110px,16vw,240px);aspect-ratio:1;z-index:1;will-change:transform}" +
      ".hwd figure:nth-of-type(1){top:4%;inset-inline-start:2%;opacity:.85}.hwd figure:nth-of-type(2){bottom:10%;inset-inline-start:14%;width:clamp(90px,11vw,170px)}.hwd figure:nth-of-type(3){bottom:6%;inset-inline-end:3%;width:clamp(120px,16vw,240px);opacity:.85}" +
      "@media (max-width:700px){.hwd figure{opacity:.55}}@media (prefers-reduced-motion:reduce){.hwd .wd{opacity:1;transform:none;filter:none;transition:none}}",
    render: function (S, t) {
      var m = S.media || {}, ph = [m.heroImg].concat((m.gallery || []).map(function (g) { return g.src; })).filter(Boolean).slice(0, 3);
      return '<section class="hwd" id="top"><div><h1>' + words((S.heroLines || [S.tagline]).join(" "), "wd") + "</h1><p>" + E(S.lede) +
        '</p><p><a class="btn a" href="#menu">' + t.see + "</a></p></div>" + ph.map(function (p) { return '<figure class="disc">' + img(p, "") + "</figure>"; }).join("") + "</section>";
    },
    init: function () {
      var s = document.querySelector(".hwd"); if (!s) return;
      setTimeout(function () { s.classList.add("on"); }, 120);
      var f = s.querySelectorAll("figure");
      onScroll(function () { var y = scrollY; [].forEach.call(f, function (el, i) { el.style.transform = "translateY(" + (y * (i + 1) * -.08) + "px)"; }); });
    }
  };
  P["hero-layers"] = { // three photos at different depths: they part as the page scrolls
    css: ".hly{position:relative;height:160vh}.hly .stage{display:grid;place-items:center}.hly figure{position:absolute;border-radius:var(--r-card);overflow:hidden;background:var(--surface);will-change:transform}" +
      ".hly .l1{width:min(46vw,560px);aspect-ratio:4/5;z-index:1}.hly .l2{width:min(28vw,320px);aspect-ratio:1;inset-inline-start:6%;top:18%;z-index:2}.hly .l3{width:min(24vw,280px);aspect-ratio:3/4;inset-inline-end:6%;bottom:12%;z-index:2}" +
      ".hly .txt{position:relative;z-index:3;text-align:center;padding:0 var(--gut)}.hly h1{font-size:clamp(44px,8.6vw,150px);text-shadow:0 4px 40px #0009}.hly p{font-size:var(--lead);margin-top:14px;text-shadow:0 2px 20px #000a}" +
      "@media (max-width:700px){.hly .l1{width:78vw}.hly .l2,.hly .l3{width:34vw}}",
    render: function (S, t) {
      var m = S.media || {}, g = (m.gallery || []).map(function (x) { return x.src; });
      return '<section class="pin hly" id="top"><div class="stage"><figure class="l1">' + img(m.heroImg || g[0], S.name) + '</figure><figure class="l2">' + img(g[0] || m.heroImg, "") +
        '</figure><figure class="l3">' + img(g[1] || m.heroImg, "") + '</figure><div class="txt"><h1>' + E((S.heroLines || [S.name])[0]) + "</h1><p>" + E(S.lede) +
        '</p><p style="margin-top:22px"><a class="btn a" href="#menu">' + t.see + "</a></p></div></div></section>";
    },
    init: function () {
      var K = SITEKIT, s = document.querySelector(".hly"); if (!s || K.reduce) return;
      var l = s.querySelectorAll("figure"), dir = document.documentElement.dir === "rtl" ? -1 : 1;
      onScroll(function () {
        var p = K.progress(s);
        l[0].style.transform = "scale(" + (1 + p * .15) + ")";
        l[1].style.transform = "translate(" + (-dir * p * 18) + "vw," + (-p * 30) + "vh) rotate(" + (-p * 8) + "deg)";
        l[2].style.transform = "translate(" + (dir * p * 18) + "vw," + (p * 30) + "vh) rotate(" + (p * 8) + "deg)";
      });
    }
  };
  P["about-badge"] = { // the about text beside a photo stamped with a slowly turning circular badge
    css: ".abg{padding:clamp(72px,10vw,160px) var(--gut);display:grid;gap:clamp(32px,5vw,72px);align-items:center;background:var(--paper);color:var(--ink)}" +
      ".abg .ph{position:relative;width:min(100%,520px);justify-self:center}.abg .ph figure{aspect-ratio:4/5;background:var(--surface)}" +
      ".abg svg{position:absolute;width:clamp(120px,14vw,170px);inset-inline-end:-24px;top:-24px;animation:spin 18s linear infinite}" +
      ".abg text{font:700 13px var(--text);letter-spacing:.18em;fill:var(--ink)}.abg circle{fill:var(--accent)}@keyframes spin{to{transform:rotate(360deg)}}" +
      ".abg h2{color:var(--accent);font-size:var(--head)}.abg p{font:500 clamp(20px,2vw,30px)/1.5 var(--display);margin-top:18px;max-width:24em}" +
      "@media (min-width:860px){.abg{grid-template-columns:5fr 7fr}}@media (prefers-reduced-motion:reduce){.abg svg{animation:none}}",
    render: function (S, t) {
      var m = S.media || {}, ring = (E(S.word || S.name) + " • " + E(S.tagline || "") + " • ").repeat(2);
      return '<section class="abg" id="about"><div class="ph rise"><figure class="loop">' + img((m.about || {}).src || m.heroImg, S.name) +
        '</figure><svg viewBox="0 0 200 200" aria-hidden="true"><circle cx="100" cy="100" r="100"/><path id="ring" fill="none" d="M100,100 m-72,0 a72,72 0 1,1 144,0 a72,72 0 1,1 -144,0"/>' +
        '<text><textPath href="#ring">' + ring + '</textPath></text></svg></div><div><h2 class="rise">' + E(S.together || t.about) + '</h2><p class="rise" style="--i:1">' + E(S.about) + "</p></div></section>";
    }
  };
  P["gallery-stack"] = { // pinned: photo cards slide up one over the other as you scroll
    css: ".gst{height:340vh;background:var(--ink)}.gst .stage{display:grid;place-items:center}.gst h2{position:absolute;top:calc(var(--nav) + 2vh);inset-inline-start:var(--gut);z-index:9}" +
      ".gst figure{position:absolute;width:min(84vw,860px);aspect-ratio:16/10;border-radius:var(--r-card);overflow:hidden;background:var(--surface);box-shadow:0 30px 80px #0008;will-change:transform}" +
      "@media (max-width:700px){.gst figure{aspect-ratio:4/5;width:82vw}}",
    render: function (S, t) {
      var g = ((S.media || {}).gallery || []).slice(0, 5);
      if (g.length < 3) return "";
      return '<section class="pin gst" id="gallery"><div class="stage"><h2>' + t.gallery + "</h2>" + g.map(function (p, i) { return '<figure style="z-index:' + (i + 1) + '">' + img(p.src, p.alt) + "</figure>"; }).join("") + "</div></section>";
    },
    init: function () {
      var K = SITEKIT, s = document.querySelector(".gst"); if (!s) return;
      var f = s.querySelectorAll("figure"), n = f.length;
      onScroll(function () {
        var p = K.progress(s) * (n - 1);
        [].forEach.call(f, function (el, i) {
          var d = i - p; // > 0: still below, waiting; 0: in front; < 0: covered and shrinking back
          el.style.transform = d > 0 ? "translateY(" + Math.min(d, 1) * 110 + "vh)" : "translateY(" + d * 3 + "vh) scale(" + (1 + d * .06) + ")";
          el.style.filter = d < -.1 ? "brightness(" + Math.max(.4, 1 + d * .3) + ")" : "";
        });
      });
    }
  };
  P["menu-flip"] = { // menu cards that turn over (tap or hover) to show what is in the dish and its price
    css: ".mfl{padding:clamp(64px,9vw,140px) var(--gut);background:var(--ink)}.mfl h2{font-size:var(--giant);line-height:1;margin-bottom:clamp(24px,4vw,56px)}" +
      ".mfl .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,220px),1fr));gap:14px}" +
      ".mfl button{all:unset;cursor:pointer;display:block;aspect-ratio:3/4;perspective:900px}.mfl .in{position:relative;width:100%;height:100%;transition:transform .7s cubic-bezier(.2,.7,.2,1);transform-style:preserve-3d}" +
      ".mfl button:hover .in,.mfl button[aria-pressed=true] .in{transform:rotateY(180deg)}.mfl button:focus-visible{outline:3px solid var(--accent);outline-offset:4px}" +
      ".mfl .f,.mfl .b{position:absolute;inset:0;border-radius:var(--r-card);overflow:hidden;backface-visibility:hidden;background:var(--surface)}" +
      ".mfl .f b{position:absolute;inset:auto 0 0;padding:14px 16px;font:700 20px/1.3 var(--display);background:linear-gradient(transparent,#000b);color:#fff}" +
      ".mfl .b{transform:rotateY(180deg);display:flex;flex-direction:column;justify-content:center;gap:10px;padding:22px;background:var(--accent);color:var(--on-accent)}" +
      ".mfl .b b{font:800 22px/1.3 var(--display)}.mfl .b i{font-style:normal;font-weight:800;font-size:22px}@media (prefers-reduced-motion:reduce){.mfl .in{transition:none}}",
    render: function (S, t) {
      return '<section class="mfl" id="menu"><h2 class="rise">' + t.menu + '</h2><div class="grid">' + items(S).map(function (i, k) {
        return '<button type="button" class="rise" style="--i:' + (k % 4) + '" aria-pressed="false" aria-label="' + E(i.name) + '"><div class="in"><div class="f">' + img(i.img, i.name) + "<b>" + E(i.name) +
          '</b></div><div class="b"><b>' + E(i.name) + "</b>" + (i.desc ? "<span>" + E(i.desc) + "</span>" : "") + (i.price ? "<i>" + E(i.price) + t.cur + "</i>" : "") + "</div></div></button>";
      }).join("") + "</div></section>";
    },
    init: function () {
      [].forEach.call(document.querySelectorAll(".mfl button"), function (b) { b.addEventListener("click", function () { b.setAttribute("aria-pressed", b.getAttribute("aria-pressed") !== "true"); }); });
    }
  };
  P["menu-polaroid"] = { // dishes as tilted instant photos on the page, straightening when you point at them
    css: ".mpl{padding:clamp(64px,9vw,140px) var(--gut);background:var(--paper);color:var(--ink)}.mpl h2{font-size:var(--giant);line-height:1;margin-bottom:clamp(28px,4vw,64px)}" +
      ".mpl .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,230px),1fr));gap:clamp(18px,3vw,40px)}" +
      ".mpl article{background:#fff;padding:12px 12px 18px;box-shadow:0 14px 40px #0002;transform:rotate(var(--t));transition:transform .4s}.mpl article:hover{transform:rotate(0) scale(1.03)}" +
      ".mpl figure{aspect-ratio:1;background:#eee}.mpl b{display:block;font:700 19px/1.3 var(--display);margin-top:12px}.mpl small{color:#666}.mpl i{float:inline-end;font-style:normal;font-weight:800;color:var(--accent)}",
    render: function (S, t) {
      var tilt = [-3, 2, -1.5, 3, -2.5, 1.5];
      return '<section class="mpl" id="menu"><h2 class="rise">' + t.menu + '</h2><div class="grid">' + items(S).map(function (i, k) {
        return '<article class="rise" style="--t:' + tilt[k % 6] + "deg;--i:" + (k % 4) + '"><figure>' + img(i.img, i.name) + "</figure><b>" + E(i.name) +
          (i.price ? "<i>" + E(i.price) + t.cur + "</i>" : "") + "</b>" + (i.desc ? "<small>" + E(i.desc) + "</small>" : "") + "</article>";
      }).join("") + "</div></section>";
    }
  };
  P["features-bento"] = { // a bento board of the place's real strengths (from data "features"), one tile is a photo
    css: ".bnt{padding:clamp(64px,9vw,140px) var(--gut);background:var(--ink)}.bnt .board{display:grid;gap:12px;grid-template-columns:repeat(2,1fr)}" +
      ".bnt .tile{border-radius:var(--r-card);padding:clamp(20px,2.6vw,36px);background:var(--surface);min-height:170px;display:flex;flex-direction:column;justify-content:flex-end}" +
      ".bnt .tile b{font:800 clamp(22px,2.4vw,36px)/1.15 var(--display)}.bnt .tile:nth-child(2){background:var(--accent);color:var(--on-accent)}.bnt .tile.ph{padding:0;overflow:hidden;min-height:240px}" +
      "@media (min-width:860px){.bnt .board{grid-template-columns:repeat(4,1fr);grid-auto-rows:200px}.bnt .tile.ph{grid-column:span 2;grid-row:span 2}.bnt .tile:nth-child(2){grid-column:span 2}}",
    render: function (S) {
      var f = (S.features || []).slice(0, 4), m = S.media || {};
      if (f.length < 2) return "";
      return '<section class="bnt" id="why"><div class="board"><div class="tile ph rise">' + img((m.gallery || [])[0] ? m.gallery[0].src : m.heroImg, S.name) + "</div>" +
        f.map(function (x, i) { return '<div class="tile rise" style="--i:' + (i + 1) + '"><b>' + E(x) + "</b></div>"; }).join("") + "</div></section>";
    }
  };
  P["cta-blur"] = { // a big invitation whose words come out of the blur as it scrolls in, then the WhatsApp button
    css: ".ctb{padding:clamp(90px,14vw,220px) var(--gut);text-align:center;background:var(--accent);color:var(--on-accent)}.ctb h2{font-size:clamp(40px,7vw,120px);max-width:12em;margin:0 auto 32px}" +
      ".ctb .bw{display:inline-block;opacity:.08;filter:blur(10px);transition:opacity .8s,filter .8s;transition-delay:calc(var(--w)*120ms)}.ctb.on .bw{opacity:1;filter:none}" +
      "@media (prefers-reduced-motion:reduce){.ctb .bw{opacity:1;filter:none;transition:none}}",
    render: function (S, t) {
      return '<section class="ctb" id="invite"><h2>' + words(S.invite || S.tagline, "bw") + '</h2><a class="btn w" href="' + SITEKIT.wa(t.lang === "en" ? "Hello" : "أهلاً، عايز أطلب") +
        '" target="_blank" rel="noopener noreferrer">' + t.wa + "</a></section>";
    },
    init: function () {
      var s = document.querySelector(".ctb"); if (!s) return;
      if (!("IntersectionObserver" in window)) return s.classList.add("on");
      new IntersectionObserver(function (es, o) { if (es[0].isIntersecting) { s.classList.add("on"); o.disconnect(); } }, {threshold: .35}).observe(s);
    }
  };
})(window.PIECES = window.PIECES || {});
