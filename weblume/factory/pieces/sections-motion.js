/* Pieces written by Weblume after design ideas in the motionsites.ai library (the ideas only: original vanilla code,
   no prompt text, no assets). Each reads window.SITE and the theme variables, works RTL, and stands still under reduced motion. */
(function (P) {
  var E = function (s) { return SITEKIT.esc(s); };
  var items = function (S) { // dishes with a photo: cut-outs from the showcase first, then menu photos
    var a = (S.showcase || []).filter(function (s) { return s.cut; }).map(function (s) { return {name: s.name, desc: s.desc, price: s.price, img: s.cut, cut: 1}; });
    if (a.length >= 3) return a;
    a = [];
    (S.menu || []).forEach(function (c) { (c.items || []).forEach(function (i) { if (i.img) a.push(i); }); });
    return a;
  };
  var order = function (t, it) { return SITEKIT.wa((t.lang === "en" ? "I'd like: " : "عايز أطلب: ") + it.name); };
  var pad = function (n) { return (n < 10 ? "0" : "") + n; };

  /* menu-rail — after "Clothing Rail": the dishes hang edge-on along a polished rail, the one you point at swings round
     to face you while the others slide apart, and a tap lifts it into a big detail card with prev/next. */
  P["menu-rail"] = {
    css: ".mrl{position:relative;padding:clamp(64px,9vw,130px) 0 clamp(56px,7vw,100px);background:radial-gradient(70% 55% at 50% 40%,var(--surface),var(--ink));overflow:hidden}" +
      ".mrl h2{text-align:center;padding:0 var(--gut);margin-bottom:clamp(30px,5vw,60px)}" +
      ".mrl .stage{--gw:200px;position:relative;height:calc(var(--gw)*1.25 + 110px);margin:0 var(--gut)}" +
      ".mrl .bar{position:absolute;inset-inline:0;top:14px;height:10px;border-radius:6px;background:linear-gradient(#fafafa,#b9bcc1 28%,#5d6066 55%,#a9adb3 78%,#e6e7e9);box-shadow:0 10px 18px #0007}" +
      ".mrl .bar:before,.mrl .bar:after{content:'';position:absolute;top:-8px;width:14px;height:26px;border-radius:5px;background:linear-gradient(90deg,#8d9096,#f3f3f4 45%,#7a7d83)}.mrl .bar:before{left:-10px}.mrl .bar:after{right:-10px}" +
      ".mrl .g{position:absolute;top:0;width:var(--gw);margin-left:calc(var(--gw)/-2);perspective:900px;cursor:pointer;background:none;border:0;padding:0;color:inherit;transition:left .75s cubic-bezier(.2,.8,.2,1)}" +
      ".mrl .g .hang{display:block;transform-origin:50% 4%;transform:rotateY(-74deg);filter:brightness(.7);transition:transform .75s cubic-bezier(.2,.8,.2,1),filter .75s}" +
      ".mrl .g.face .hang{transform:none;filter:none}.mrl .g{pointer-events:none}.mrl .g .hang{pointer-events:auto}.mrl .g.face{z-index:2}" +
      ".mrl .hook{display:block;width:22px;height:30px;margin:0 auto -4px;border:3px solid #c9ccd1;border-bottom:0;border-radius:14px 14px 0 0;position:relative;z-index:1}" +
      ".mrl .g img{display:block;width:100%;aspect-ratio:4/5;object-fit:cover;border-radius:var(--r-card);box-shadow:0 22px 26px #0008;background:var(--surface)}" +
      ".mrl .g.cut img{object-fit:contain;background:none;box-shadow:none;filter:drop-shadow(0 20px 22px #0009)}" +
      ".mrl .cap{position:absolute;top:calc(var(--gw)*1.25 + 44px);transform:translateX(-50%);text-align:center;white-space:nowrap;font-size:var(--small);color:var(--muted);opacity:0;pointer-events:none;transition:left .75s cubic-bezier(.2,.8,.2,1),opacity .35s}" +
      ".mrl .cap.on{opacity:1}.mrl .cap b{display:block;color:var(--paper);font:700 var(--lead)/1.2 var(--display);margin-bottom:4px}" +
      ".mrl .hint{text-align:center;margin-top:16px;font-size:var(--small);color:var(--muted)}" +
      ".mrl .det{position:absolute;inset:0;z-index:5;display:grid;place-items:center;align-content:center;gap:18px;padding:var(--gut);background:color-mix(in srgb,var(--ink) 82%,transparent);backdrop-filter:blur(6px);opacity:0;visibility:hidden;transition:opacity .5s,visibility .5s}" +
      ".mrl.open .det{opacity:1;visibility:visible}" +
      ".mrl .det .big{width:min(360px,62vw);aspect-ratio:4/5;object-fit:cover;border-radius:var(--r-card);box-shadow:0 30px 40px #0009}.mrl .det .big.cut{object-fit:contain;box-shadow:none;filter:drop-shadow(0 30px 40px #0009)}" +
      ".mrl .det .num{font-size:var(--small);letter-spacing:.16em;color:var(--muted);text-align:center}" +
      ".mrl .det h3{font:800 clamp(28px,3.6vw,48px)/1.15 var(--display);text-align:center;margin:0}.mrl .det p{margin:0;text-align:center;color:var(--muted);max-width:40ch}" +
      ".mrl .det .row{display:flex;align-items:center;justify-content:center;gap:12px}" +
      ".mrl .arr,.mrl .x{width:48px;height:48px;border-radius:50%;border:1px solid color-mix(in srgb,var(--paper) 50%,transparent);background:none;color:var(--paper);font-size:22px;cursor:pointer;transition:background .2s,color .2s}" +
      "[dir=rtl] .mrl .arr,[dir=rtl] .hrg .ctl .prev,[dir=rtl] .hrg .ctl .next{transform:scaleX(-1)}.mrl .arr:hover,.mrl .x:hover{background:var(--paper);color:var(--ink)}.mrl .x{position:absolute;top:var(--gut);inset-inline-end:var(--gut)}" +
      "@media (prefers-reduced-motion:reduce){.mrl .g,.mrl .g .hang,.mrl .cap,.mrl .det{transition:none}}",
    render: function (S, t) {
      var list = items(S).slice(0, 10), en = t.lang === "en";
      if (list.length < 4) return "";
      return '<section class="mrl" id="menu"><h2>' + E(t.menu) + '</h2><div class="stage"><div class="bar" aria-hidden="true"></div>' +
        list.map(function (it, i) {
          return '<button type="button" class="g' + (it.cut ? " cut" : "") + '" data-i="' + i + '" aria-label="' + E(it.name) + '"><span class="hang"><span class="hook"></span><img src="' + E(it.img) + '" alt="' + E(it.name) + '" loading="lazy"></span></button>';
        }).join("") + '<div class="cap" aria-live="polite"><b></b><span></span></div></div>' +
        '<p class="hint">' + (en ? "Point at a dish, tap to open it" : "قرّب على أي صنف، ودوس عشان تفتحه") + "</p>" +
        '<div class="det" role="dialog" aria-modal="true" aria-label="' + E(t.menu) + '"><button type="button" class="x" aria-label="' + E(t.close) + '">✕</button>' +
        '<img class="big" src="' + E(list[0].img) + '" alt="" loading="lazy"><div class="num" dir="ltr"></div><h3></h3><p class="desc"></p><div class="row"><button type="button" class="arr prev" aria-label="previous">‹</button>' +
        '<a class="btn a" target="_blank" rel="noopener noreferrer"></a><button type="button" class="arr next" aria-label="next">›</button></div></div></section>';
    },
    init: function (S, t) {
      var sec = document.querySelector(".mrl"); if (!sec) return;
      var list = items(S).slice(0, 10), stage = sec.querySelector(".stage"), G = sec.querySelectorAll(".g"), cap = sec.querySelector(".cap"), det = sec.querySelector(".det");
      var big = det.querySelector(".big"), rtl = document.documentElement.dir === "rtl", N = list.length, hov = -1, open = -1, gw = 0;
      function layout() {
        var w = stage.clientWidth, wide = w > 700;
        gw = Math.round(Math.min(wide ? 230 : 150, w * (wide ? .2 : .42)));
        stage.style.setProperty("--gw", gw + "px");
        var gap = Math.min(gw * .62, wide ? 86 : 44), slot = Math.min(wide ? 108 : 70, (w - gw - (hov >= 0 ? 2 * gap : 0)) / Math.max(1, N - 1));
        [].forEach.call(G, function (g, k) {
          var x = w / 2 + (k - (N - 1) / 2) * slot;
          if (hov >= 0 && k !== hov) x += (k > hov ? 1 : -1) * gap;
          if (rtl) x = w - x; // the first dish starts on the right in Arabic
          g.style.left = x + "px"; g.classList.toggle("face", k === hov);
          if (k === hov) cap.style.left = x + "px";
        });
        cap.classList.toggle("on", hov >= 0);
        if (hov >= 0) { cap.firstChild.textContent = list[hov].name; cap.lastChild.textContent = list[hov].price ? list[hov].price + " " + t.cur : ""; }
      }
      function fill(k) {
        var it = list[k], a = det.querySelector(".btn");
        big.src = it.img; big.alt = it.name; big.classList.toggle("cut", !!it.cut);
        det.querySelector(".num").textContent = pad(k + 1) + " / " + pad(N);
        det.querySelector("h3").textContent = it.name; det.querySelector(".desc").textContent = it.desc || "";
        a.href = order(t, it); a.textContent = (it.price ? it.price + " " + t.cur + " · " : "") + t.order;
      }
      function lift(k) { // the big card grows out of the dish's own place on the rail
        if (SITEKIT.reduce || !big.animate) return;
        var g = G[k].getBoundingClientRect(), b = big.getBoundingClientRect();
        if (!b.width) return;
        big.animate([{transform: "translate(" + (g.left + g.width / 2 - b.left - b.width / 2) + "px," + (g.top - b.top) + "px) scale(" + g.width / b.width + ")", transformOrigin: "50% 0"},
          {transform: "none", transformOrigin: "50% 0"}], {duration: 750, easing: "cubic-bezier(.2,.8,.2,1)"});
      }
      function openG(k) { open = k; hov = k; layout(); fill(k); sec.classList.add("open"); lift(k); det.querySelector(".x").focus({preventScroll: true}); }
      function step(d) {
        open = (open + d + N) % N; hov = open; layout(); fill(open);
        if (!SITEKIT.reduce && big.animate) big.animate([{transform: "translateX(" + d * (rtl ? -1 : 1) * 120 + "px) scale(.94)", opacity: 0, filter: "blur(6px)"}, {transform: "none", opacity: 1, filter: "none"}], {duration: 600, easing: "cubic-bezier(.2,.8,.2,1)"});
      }
      function closeG() { if (open < 0) return; var k = open; sec.classList.remove("open"); open = -1; G[k].focus({preventScroll: true}); }
      [].forEach.call(G, function (g, k) {
        g.addEventListener("pointerenter", function (e) { if (open < 0 && e.pointerType === "mouse") { hov = k; layout(); } });
        g.addEventListener("focus", function () { if (open < 0 && g.matches(":focus-visible")) { hov = k; layout(); } });
        g.addEventListener("click", function () { if (hov === k) openG(k); else { hov = k; layout(); } }); // phones: first tap faces it, second opens
      });
      stage.addEventListener("pointerleave", function () { if (open < 0) { hov = -1; layout(); } });
      det.querySelector(".x").addEventListener("click", closeG);
      det.querySelector(".prev").addEventListener("click", function () { step(-1); });
      det.querySelector(".next").addEventListener("click", function () { step(1); });
      det.addEventListener("click", function (e) { if (e.target === det) closeG(); });
      sec.addEventListener("keydown", function (e) {
        if (open >= 0) { if (e.key === "Escape") closeG(); else if (e.key === "ArrowRight") step(rtl ? -1 : 1); else if (e.key === "ArrowLeft") step(rtl ? 1 : -1); }
      });
      addEventListener("resize", layout);
      layout();
    }
  };

  /* hero-ring — after "Outfit Carousel": the dishes stand on a turning stage, the front one sharp and big, the ones behind
     smaller and blurred; it turns every 5 seconds with a numbered progress line, arrows, a pause button and a swipe. */
  P["hero-ring"] = {
    css: ".hrg{position:relative;min-height:calc(100svh - var(--nav));display:grid;grid-template-rows:auto 1fr auto;overflow:hidden;background:var(--paper);color:var(--ink);padding:clamp(18px,3vw,36px) var(--gut)}" +
      ".hrg h1{font-size:var(--head);margin:0;max-width:14em;line-height:1.05}.hrg h1 small{display:block;font:500 var(--small)/1.4 var(--text);color:var(--muted);margin-top:8px;letter-spacing:.02em}" +
      ".hrg .ring{position:relative;perspective:1400px;min-height:clamp(260px,46vh,520px);touch-action:pan-y}" +
      ".hrg .it{position:absolute;left:50%;top:50%;width:clamp(170px,28vw,360px);margin:calc(clamp(170px,28vw,360px)*-.6) 0 0 calc(clamp(170px,28vw,360px)/-2);transition:transform 1s cubic-bezier(.2,.8,.2,1),filter 1s,opacity 1s;will-change:transform}" +
      ".hrg .it img{display:block;width:100%;aspect-ratio:5/6;object-fit:cover;border-radius:var(--r-card);box-shadow:0 26px 40px #0003}.hrg .it.cut img{object-fit:contain;box-shadow:none;filter:drop-shadow(0 26px 30px #0004)}" +
      ".hrg .foot{display:grid;gap:16px;align-items:end}" +
      ".hrg .info b{display:block;font:800 clamp(24px,3vw,44px)/1.1 var(--display)}.hrg .info p{margin:6px 0 12px;color:var(--muted);max-width:40ch}" +
      ".hrg .ctl{display:flex;align-items:center;gap:10px}.hrg .ctl button{width:46px;height:46px;border-radius:50%;border:1px solid currentColor;background:none;color:inherit;font-size:20px;cursor:pointer;flex:none}" +
      ".hrg .prog{display:flex;align-items:center;gap:10px;flex:1;min-width:140px;font-size:var(--small);font-variant-numeric:tabular-nums}.hrg .line{flex:1;height:2px;background:color-mix(in srgb,var(--ink) 18%,transparent);position:relative;overflow:hidden}" +
      ".hrg .line i{position:absolute;inset:0;background:var(--accent);transform-origin:0 50%;transform:scaleX(0)}[dir=rtl] .hrg .line i{transform-origin:100% 50%}" +
      ".hrg.run .line i{animation:hrgP var(--dur,5s) linear forwards}.hrg.paused .line i{animation-play-state:paused}@keyframes hrgP{to{transform:scaleX(1)}}" +
      "@media (min-width:900px){.hrg .foot{grid-template-columns:1fr minmax(320px,440px)}}" +
      "@media (prefers-reduced-motion:reduce){.hrg .it{transition:none}.hrg.run .line i{animation:none;transform:scaleX(1)}}",
    render: function (S, t) {
      var list = items(S).slice(0, 7);
      if (list.length < 3) return "";
      var lines = (S.heroLines && S.heroLines.length ? S.heroLines : [S.name]).map(E).join("<br>");
      return '<section class="hrg" id="top" aria-roledescription="carousel" aria-label="' + E(S.name) + '"><h1>' + lines + "<small>" + E(S.tagline || S.lede || "") + "</small></h1>" +
        '<div class="ring">' + list.map(function (it, i) {
          return '<div class="it' + (it.cut ? " cut" : "") + '" role="group" aria-label="' + E(it.name) + '"><img src="' + E(it.img) + '" alt="' + E(it.name) + '"' + (i ? ' loading="lazy"' : "") + "></div>";
        }).join("") + '</div><div class="foot"><div class="info" aria-live="polite"><b></b><p></p><a class="btn a" target="_blank" rel="noopener noreferrer"></a></div>' +
        '<div class="ctl"><button type="button" class="prev" aria-label="previous">‹</button><div class="prog" dir="ltr"><span class="n">01</span><span class="line"><i></i></span><span>' + pad(list.length) + "</span></div>" +
        '<button type="button" class="next" aria-label="next">›</button><button type="button" class="pause" aria-label="pause">❚❚</button></div></div></section>';
    },
    init: function (S, t) {
      var sec = document.querySelector(".hrg"); if (!sec) return;
      var list = items(S).slice(0, 7), its = sec.querySelectorAll(".it"), N = list.length, at = 0, timer, paused = SITEKIT.reduce;
      var rtl = document.documentElement.dir === "rtl", line = sec.querySelector(".line i"), info = sec.querySelector(".info");
      function place() {
        var w = sec.clientWidth, R = Math.min(w * .42, 520);
        [].forEach.call(its, function (el, i) {
          var d = ((i - at) % N + N) % N; if (d > N / 2) d -= N; // nearest way round the ring
          var a = d * (2 * Math.PI / Math.max(N, 5)) * (rtl ? -1 : 1), x = Math.sin(a) * R, z = (Math.cos(a) - 1) * R, ad = Math.abs(d);
          el.style.transform = "translate3d(" + x.toFixed(1) + "px,0," + z.toFixed(1) + "px)";
          el.style.filter = ad ? "blur(" + Math.min(ad * 3, 8) + "px)" : "none";
          el.style.opacity = ad > 2 ? 0 : 1 - ad * .25; el.style.zIndex = 10 - ad;
          el.setAttribute("aria-hidden", ad ? "true" : "false");
        });
        var it = list[at], a = info.querySelector("a");
        info.querySelector("b").textContent = it.name; info.querySelector("p").textContent = it.desc || "";
        a.href = order(t, it); a.textContent = (it.price ? it.price + " " + t.cur + " · " : "") + t.order;
        sec.querySelector(".n").textContent = pad(at + 1);
        sec.classList.remove("run"); void line.offsetWidth; if (!SITEKIT.reduce) sec.classList.add("run"); // restart the progress line
      }
      function go(n) { at = (n + N) % N; place(); auto(); }
      function auto() { clearTimeout(timer); if (!paused) timer = setTimeout(function () { go(at + 1); }, 5000); }
      sec.querySelector(".next").addEventListener("click", function () { go(at + 1); });
      sec.querySelector(".prev").addEventListener("click", function () { go(at - 1); });
      var pb = sec.querySelector(".pause");
      pb.addEventListener("click", function () { paused = !paused; sec.classList.toggle("paused", paused); pb.textContent = paused ? "▶" : "❚❚"; pb.setAttribute("aria-label", paused ? "play" : "pause"); auto(); });
      if (paused) { pb.textContent = "▶"; pb.setAttribute("aria-label", "play"); }
      var x0 = null, ring = sec.querySelector(".ring");
      ring.addEventListener("pointerdown", function (e) { x0 = e.clientX; });
      ring.addEventListener("pointerup", function (e) { if (x0 !== null && Math.abs(e.clientX - x0) > 40) go(at + ((e.clientX < x0) !== rtl ? 1 : -1)); x0 = null; });
      [].forEach.call(its, function (el, i) { el.addEventListener("click", function () { if (i !== at) go(i); }); });
      addEventListener("resize", place);
      place(); auto();
    }
  };

  /* features-scrub — after "Freight Scroll Hero": a sticky full-screen video that scrolling plays forward and back
     (or a photo that slowly zooms), while the big promise and the place's strengths rise up either side of the middle. */
  P["features-scrub"] = {
    css: ".fsc{position:relative;background:var(--ink);color:#fff}" +
      ".fsc .scene{position:sticky;top:0;height:100svh;overflow:hidden}.fsc .scene video,.fsc .scene img{width:100%;height:100%;object-fit:cover;display:block;transform-origin:50% 50%}" +
      ".fsc .scene:after{content:'';position:absolute;inset:0;background:linear-gradient(#0006,#0003 30%,#0003 70%,#0008)}" +
      ".fsc .flow{position:relative;margin-top:-100svh;padding:70svh var(--gut) 60svh;display:grid;gap:clamp(110px,26svh,260px);text-shadow:0 6px 24px #0009}" +
      ".fsc .intro{text-align:center}.fsc .eye{font-size:var(--small);letter-spacing:.3em;color:var(--accent);font-weight:700}" +
      ".fsc .intro h2{font-size:var(--giant);line-height:1.05;margin:10px auto 0;max-width:11em;color:#fff}" +
      ".fsc .f{max-width:340px;text-align:center;margin:0 auto}.fsc .f .ic{display:inline-grid;place-items:center;width:46px;height:46px;border-radius:50%;border:1px dashed #fffa;font:700 var(--small)/1 var(--display);margin-bottom:14px}" +
      ".fsc .f b{display:block;font:800 clamp(22px,2.2vw,32px)/1.15 var(--display)}" +
      "@media (min-width:800px){.fsc .f{width:300px;justify-self:center;margin:0;transform:translateX(calc(var(--side) * 220px))}.fsc .f.l{text-align:end}.fsc .f.r{text-align:start}}" +
      "@media (prefers-reduced-motion:reduce){.fsc .scene img{transform:none!important}}",
    render: function (S, t) {
      var f = (S.features || []).slice(0, 5), m = S.media || {};
      if (f.length < 2 || !(m.video || m.heroImg || m.poster)) return "";
      var en = t.lang === "en", rtl = !en;
      var scene = m.video ? '<video muted playsinline preload="auto" src="' + E(m.video) + '"' + (m.poster ? ' poster="' + E(m.poster) + '"' : "") + ' aria-hidden="true"></video>' :
        '<img src="' + E(m.heroImg || m.poster) + '" alt="" aria-hidden="true">';
      return '<section class="fsc" id="why"><div class="scene">' + scene + '</div><div class="flow"><div class="intro"><div class="eye">' + (en ? "WHY US" : "ليه إحنا") +
        "</div><h2>" + E(S.together || S.tagline || S.name) + "</h2></div>" +
        f.map(function (x, i) {
          var last = i === f.length - 1 && f.length % 2, side = last ? 0 : (i % 2 ? 1 : -1) * (rtl ? -1 : 1); // mirrored around the middle, an odd last one centred
          return '<div class="f' + (last ? "" : i % 2 ? " r" : " l") + '" style="--side:' + side + '"><span class="ic" aria-hidden="true">' + pad(i + 1) + "</span><b>" + E(x) + "</b></div>";
        }).join("") + "</div></section>";
    },
    init: function () {
      var sec = document.querySelector(".fsc"); if (!sec || SITEKIT.reduce) return;
      var v = sec.querySelector(".scene video"), im = sec.querySelector(".scene img"), cur = 0, target = 0;
      function prog() { var r = sec.getBoundingClientRect(), span = sec.offsetHeight - innerHeight; return span > 0 ? SITEKIT.clamp(-r.top / span) : 0; }
      if (im) {
        var q = false, zoom = function () { q = false; im.style.transform = "scale(" + (1 + prog() * .25).toFixed(4) + ")"; };
        addEventListener("scroll", function () { if (!q) { q = true; requestAnimationFrame(zoom); } }, {passive: true}); zoom();
        return;
      }
      v.pause();
      (function tick() { // the video is never played, only moved to the time that matches the scroll
        if (v.duration) {
          target = prog() * (v.duration - .05); cur += (target - cur) * .22;
          if (!v.seeking && Math.abs(v.currentTime - cur) > 1 / 60) v.currentTime = cur;
        }
        requestAnimationFrame(tick);
      })();
    }
  };
})(window.PIECES = window.PIECES || {});
