/* Pieces built on MIT-licensed elements from Uiverse.io (github.com/uiverse-io/galaxy, Copyright (c) 2023 Uiverse.io, MIT —
   full notice in LICENSES.md). Each element was reworked into a whole section: theme colours, real data, RTL, phones, reduced motion. */
(function (P) {
  var E = function (s) { return SITEKIT.esc(s); };
  var pad = function (n) { return (n < 10 ? "0" : "") + n; };
  var dishes = function (S) { var a = []; (S.menu || []).forEach(function (c) { (c.items || []).forEach(function (i) { if (i.img) a.push(i); }); }); return a; };
  var inView = function (sel) { // adds .on once the section is on screen
    var s = document.querySelector(sel); if (!s) return;
    if (!("IntersectionObserver" in window)) return s.classList.add("on");
    new IntersectionObserver(function (es, o) { if (es[0].isIntersecting) { s.classList.add("on"); o.disconnect(); } }, {threshold: .3}).observe(s);
  };

  /* features-glow — after Uiverse "swift-bullfrog-34" by SelfMadeSystem: a card whose border is a spinning conic gradient with a
     blurred copy behind it as glow. Here: the brand's accent instead of the rainbow, one card per real strength. */
  P["features-glow"] = {
    css: ".fgl{padding:clamp(70px,10vw,150px) var(--gut);background:var(--ink);color:var(--paper)}.fgl h2{font-size:var(--head);margin-bottom:clamp(28px,4vw,56px)}" +
      ".fgl .grid{display:grid;gap:22px;grid-template-columns:repeat(auto-fit,minmax(min(100%,230px),1fr))}" +
      ".fgl .card{position:relative;isolation:isolate;min-height:200px;border-radius:var(--r-card);background:var(--surface);padding:clamp(20px,2.4vw,30px);display:flex;flex-direction:column;justify-content:space-between}" +
      ".fgl .bg{position:absolute;z-index:-1;inset:-3px;border-radius:inherit;overflow:hidden}.fgl .bg.glow{filter:blur(10px);opacity:.7;transition:filter .3s,opacity .3s}" +
      ".fgl .bg:before{content:'';position:absolute;top:50%;left:50%;min-width:150%;min-height:150%;aspect-ratio:1;transform-origin:0 0;transform:rotate(0) translate(-50%,-50%);" +
      "background:conic-gradient(var(--accent),color-mix(in srgb,var(--accent) 25%,var(--paper)),var(--accent),color-mix(in srgb,var(--accent) 40%,var(--ink)),var(--accent));animation:fglSpin 5s linear infinite}" +
      ".fgl .card:nth-child(2n) .bg:before{animation-delay:-2.5s}.fgl .card:hover .bg.glow{filter:blur(16px);opacity:1}" +
      ".fgl .card:after{content:'';position:absolute;inset:0;z-index:-1;border-radius:inherit;background:var(--surface)}" +
      "@keyframes fglSpin{to{transform:rotate(360deg) translate(-50%,-50%)}}" +
      ".fgl .n{display:inline-grid;place-items:center;width:3.2em;height:3.2em;border-radius:1em;background:color-mix(in srgb,var(--paper) 14%,transparent);font:800 var(--small)/1 var(--display)}" +
      ".fgl .card b{display:block;margin-top:24px;font:800 clamp(22px,2.2vw,32px)/1.2 var(--display)}" +
      "@media (prefers-reduced-motion:reduce){.fgl .bg:before{animation:none}}",
    render: function (S, t) {
      var f = (S.features || []).slice(0, 4);
      if (f.length < 2) return "";
      return '<section class="fgl" id="why"><h2>' + (t.lang === "en" ? "Why us" : "ليه إحنا") + '</h2><div class="grid">' + f.map(function (x, i) {
        return '<div class="card rise" style="--i:' + i + '"><div class="bg glow" aria-hidden="true"></div><div class="bg" aria-hidden="true"></div><span class="n">' + pad(i + 1) + "</span><b>" + E(x) + "</b></div>";
      }).join("") + "</div></section>";
    }
  };

  /* menu-iso — after Uiverse "popular-walrus-75" by JaydipPrajapati1910: an isometric slab (rotate + skew) with two shaded sides
     that lifts off the table on hover. Here: each slab is a dish photo, the sides take the accent, the name and price sit under it. */
  P["menu-iso"] = {
    css: ".mis{padding:clamp(70px,10vw,150px) var(--gut);background:var(--paper);color:var(--ink);overflow:hidden}.mis h2{font-size:var(--head);margin-bottom:clamp(40px,6vw,80px)}" +
      ".mis ul{list-style:none;margin:0;padding:0;display:grid;gap:clamp(70px,8vw,110px) 30px;grid-template-columns:repeat(auto-fill,minmax(min(100%,240px),1fr))}" +
      ".mis li{display:grid;justify-items:center;gap:clamp(40px,5vw,60px)}.mis a{color:inherit;text-decoration:none;display:grid;justify-items:center;gap:inherit}" +
      ".mis .slab{position:relative;display:block;width:min(170px,44vw);aspect-ratio:4/5;background:var(--surface);transform:rotate(-30deg) skew(25deg);box-shadow:-20px 20px 12px #0004;transition:transform .5s,box-shadow .5s}" +
      ".mis .slab img{width:100%;height:100%;object-fit:cover;display:block}" +
      ".mis .slab:before,.mis .slab:after{content:'';position:absolute;transition:background .5s}" +
      ".mis .slab:before{top:10px;left:-16px;width:16px;height:100%;background:color-mix(in srgb,var(--accent) 70%,var(--ink));transform:skewY(-45deg)}" +
      ".mis .slab:after{bottom:-16px;left:-8px;height:16px;width:100%;background:color-mix(in srgb,var(--accent) 85%,var(--paper));transform:skewX(-45deg)}" +
      ".mis a:hover .slab,.mis a:focus-visible .slab{transform:rotate(-30deg) skew(25deg) translate(18px,-14px);box-shadow:-46px 46px 46px #0004}" +
      ".mis .cap{text-align:center}.mis .cap b{display:block;font:800 var(--lead)/1.25 var(--display)}.mis .cap small{color:var(--muted)}.mis .cap i{display:block;font-style:normal;font-weight:700;color:var(--accent);margin-top:4px}" +
      "@media (prefers-reduced-motion:reduce){.mis .slab{transition:none}}",
    render: function (S, t) {
      var list = dishes(S).slice(0, 6);
      if (list.length < 4) return "";
      return '<section class="mis" id="menu"><h2>' + E(t.menu) + "</h2><ul>" + list.map(function (it, i) {
        return '<li class="rise" style="--i:' + i % 3 + '"><a href="' + SITEKIT.wa((t.lang === "en" ? "I'd like: " : "عايز أطلب: ") + it.name) + '" target="_blank" rel="noopener noreferrer">' +
          '<span class="slab"><img src="' + E(it.img) + '" alt="' + E(it.name) + '" loading="lazy"></span><span class="cap"><b>' + E(it.name) + "</b>" + (it.desc ? "<small>" + E(it.desc) + "</small>" : "") +
          (it.price ? "<i>" + E(it.price) + " " + E(t.cur) + "</i>" : "") + "</span></a></li>";
      }).join("") + "</ul></section>";
    }
  };

  /* band-stripes — after Uiverse "afraid-sheep-52" by jeremyssocial: diagonal stripes sliding forever. Here: a band in the accent
     with the house's short lines (caps, else strengths) set big over the moving stripes. */
  P["band-stripes"] = {
    css: ".bst{background:linear-gradient(135deg,var(--accent) 25%,color-mix(in srgb,var(--accent) 82%,var(--ink)) 25% 50%,var(--accent) 50% 75%,color-mix(in srgb,var(--accent) 82%,var(--ink)) 75%) 0 0/48px 48px;" +
      "color:var(--on-accent);padding:clamp(26px,4vw,48px) var(--gut);display:flex;flex-wrap:wrap;justify-content:center;gap:.3em 1.1em;font:800 clamp(26px,4vw,60px)/1.1 var(--display);text-align:center;animation:bstMove 4s linear infinite}" +
      ".bst span{padding:.08em .3em;background:var(--accent);border-radius:.2em}" +
      "@keyframes bstMove{to{background-position:48px 48px}}@media (prefers-reduced-motion:reduce){.bst{animation:none}}",
    render: function (S) {
      var w = (S.caps && S.caps.length ? S.caps : S.features || []).slice(0, 4);
      if (!w.length) return "";
      return '<div class="bst">' + w.map(function (x) { return "<span>" + E(x) + "</span>"; }).join("") + "</div>";
    }
  };

  /* about-bubbles — after Uiverse "lovely-monkey-46" by csemszepp: layered soft rings over a gradient. Here: the rings in the
     paper colour over the brand's surface and ink, drifting slowly, with the about text on top. */
  P["about-bubbles"] = {
    css: ".abb{position:relative;overflow:hidden;padding:clamp(90px,13vw,200px) var(--gut);color:var(--paper);" +
      "background:radial-gradient(#fff0 0,#ffffff26 30%,#ffffff4d 32%,#fff0 33%) 0 0/470px 470px,radial-gradient(#fff0 0,#ffffff1a 11%,#ffffff4d 13%,#fff0 14%) 0 0/970px 970px," +
      "radial-gradient(#fff0 0,#fff3 17%,#ffffff6e 19%,#fff0 20%) 0 110px/410px 410px,radial-gradient(#fff0 0,#fff3 11%,#fff6 13%,#fff0 14%) -130px -170px/610px 610px," +
      "linear-gradient(45deg,var(--ink),var(--surface) 55%,color-mix(in srgb,var(--accent) 45%,var(--surface)));animation:abbDrift 40s linear infinite}" +
      "@keyframes abbDrift{to{background-position:470px 470px,-970px 970px,410px 520px,-740px 440px,0 0}}" +
      ".abb h2{font-size:var(--small);font-family:var(--text);letter-spacing:.2em;color:var(--accent);margin-bottom:22px}" +
      ".abb p{font:700 clamp(26px,4vw,64px)/1.2 var(--display);max-width:19em;margin:0;text-shadow:0 4px 24px #0006}" +
      "@media (prefers-reduced-motion:reduce){.abb{animation:none}}",
    render: function (S, t) {
      if (!S.about) return "";
      return '<section class="abb" id="about"><h2 class="rise">' + E(t.about) + '</h2><p class="rise" style="--i:1">' + E(S.about) + "</p></section>";
    }
  };

  /* cta-glow — after Uiverse "rare-rattlesnake-22" by Aryan-81: a dark card with a gradient plate behind it that turns, a blurred
     glow under it, and a button that rises from the bottom edge. Here: the invitation, in the brand's colours; the turn plays
     when the card scrolls in (phones have no hover) and again on hover. */
  P["cta-glow"] = {
    css: ".cgl{padding:clamp(90px,13vw,190px) var(--gut);background:var(--paper);display:grid;place-items:center;overflow:hidden}" +
      ".cgl .card{position:relative;isolation:isolate;width:min(640px,100%);min-height:280px;padding:clamp(28px,4vw,52px) clamp(22px,4vw,52px) 64px;border-radius:var(--r-card);color:var(--paper);text-align:center;display:grid;align-content:center;gap:14px}" +
      ".cgl .face{position:absolute;inset:0;z-index:-1;border-radius:inherit;background:var(--ink)}.cgl .card:before,.cgl .card:after{content:'';position:absolute;z-index:-2;border-radius:inherit;background:linear-gradient(-45deg,var(--accent),color-mix(in srgb,var(--accent) 35%,var(--surface)))}" +
      ".cgl .card:before{inset:-6px;transition:transform .7s cubic-bezier(.175,.885,.32,1.275)}.cgl .card:after{inset:0;transform:scale(.95);filter:blur(22px);transition:filter .4s}" +
      ".cgl.on .card:before{transform:rotate(-3deg) scale(1.02)}.cgl .card:hover:before{transform:rotate(-6deg) scale(1.04)}.cgl .card:hover:after{filter:blur(34px)}" +
      ".cgl h2{font-size:clamp(32px,5vw,72px);margin:0}.cgl p{margin:0 auto;max-width:36ch;color:var(--muted)}" +
      ".cgl .btn{position:absolute;left:50%;bottom:0;transform:translate(-50%,120%);opacity:0;transition:transform .45s ease-out,opacity .45s;white-space:nowrap}" +
      ".cgl.on .btn{transform:translate(-50%,50%);opacity:1}" +
      "@media (prefers-reduced-motion:reduce){.cgl .btn{transform:translate(-50%,50%);opacity:1;transition:none}.cgl .card:before{transition:none}}",
    render: function (S, t) {
      return '<section class="cgl" id="invite"><div class="card"><h2>' + E(S.invite || S.tagline || S.name) + "</h2>" + (S.lede ? "<p>" + E(S.lede) + "</p>" : "") +
        '<a class="btn a" href="' + SITEKIT.wa(t.lang === "en" ? "Hello" : "أهلاً، عايز أطلب") + '" target="_blank" rel="noopener noreferrer">' + E(t.order) + "</a><span class=\"face\" aria-hidden=\"true\"></span></div></section>";
    },
    init: function () { inView(".cgl"); }
  };
})(window.PIECES = window.PIECES || {});
