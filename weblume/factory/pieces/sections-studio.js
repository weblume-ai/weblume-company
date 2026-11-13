/* Pieces written by Weblume after design ideas in a screen recording Asser shared of a creative studio's site:
   a blueprint opening drawn with lines, a curved wall of works, and text revealed in black labels. Original vanilla code,
   no code, images or brand taken. Each reads window.SITE and the theme, works RTL, and stands still under reduced motion. */
(function (P) {
  var E = function (s) { return SITEKIT.esc(s); };
  var once = function (el, cls, th) { // adds cls once the element is on screen
    if (!el) return;
    if (!("IntersectionObserver" in window) || SITEKIT.reduce) return el.classList.add(cls);
    new IntersectionObserver(function (es, o) { if (es[0].isIntersecting) { el.classList.add(cls); o.disconnect(); } }, {threshold: th || .3}).observe(el);
  };

  /* hero-blueprint — guide lines draw themselves across the screen like a blueprint, a window opens in the middle on the
     place's photo, then the brand word rises big at the bottom with the headline. */
  P["hero-blueprint"] = {
    css: ".hbp{position:relative;height:calc(100svh - var(--nav));min-height:560px;overflow:hidden;background:var(--ink);color:var(--paper)}" +
      ".hbp svg{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}" +
      ".hbp svg line{stroke:color-mix(in srgb,var(--paper) 38%,transparent);stroke-width:1;vector-effect:non-scaling-stroke;stroke-dasharray:1;stroke-dashoffset:1;animation:hbpDraw 1.4s cubic-bezier(.6,0,.2,1) forwards;animation-delay:calc(var(--d) * 90ms)}" +
      ".hbp svg line.x{stroke:var(--accent);stroke-width:1.5}" +
      "@keyframes hbpDraw{to{stroke-dashoffset:0}}" +
      ".hbp .win{position:absolute;top:12%;bottom:30%;inset-inline-start:40%;inset-inline-end:8%;overflow:hidden;clip-path:inset(50% 50% 50% 50%);animation:hbpOpen 1.3s cubic-bezier(.7,0,.2,1) 1.2s forwards}" +
      ".hbp .win img{width:100%;height:100%;object-fit:cover;transform:scale(1.25);animation:hbpZoom 2.6s cubic-bezier(.2,.7,.2,1) 1.2s forwards}" +
      "@keyframes hbpOpen{to{clip-path:inset(0)}}@keyframes hbpZoom{to{transform:scale(1)}}" +
      ".hbp .word{position:absolute;inset-inline:0;bottom:-.08em;text-align:center;font:800 clamp(80px,22vw,340px)/1 var(--display);white-space:nowrap;overflow:hidden;pointer-events:none}" +
      ".hbp .word span{display:inline-block;transform:translateY(105%);animation:hbpRise 1.1s cubic-bezier(.2,.8,.2,1) 2.1s forwards}@keyframes hbpRise{to{transform:none}}" +
      ".hbp .say{position:absolute;top:clamp(18px,5vh,48px);inset-inline-start:var(--gut);max-width:min(30ch,34vw);opacity:0;animation:hbpFade .8s ease 2.4s forwards}" +
      ".hbp h1{font-size:var(--head);line-height:1.05;margin:0 0 12px}.hbp .say p{margin:0 0 16px;color:var(--muted)}" +
      "@keyframes hbpFade{to{opacity:1}}" +
      "@media (max-width:700px){.hbp .win{top:40%;bottom:24%;inset-inline:8%}.hbp .say{max-width:84vw}}" +
      "@media (prefers-reduced-motion:reduce){.hbp svg line,.hbp .win,.hbp .win img,.hbp .word span,.hbp .say{animation:none;stroke-dashoffset:0;clip-path:none;transform:none;opacity:1}}",
    render: function (S, t) {
      var m = S.media || {}, ph = m.heroImg;
      var lines = [], d = 0, add = function (x1, y1, x2, y2, c) { lines.push('<line pathLength="1" x1="' + x1 + '" y1="' + y1 + '" x2="' + x2 + '" y2="' + y2 + '" style="--d:' + (d++) + '"' + (c ? ' class="x"' : "") + "/>"); };
      [12, 22, 50, 78, 88].forEach(function (x) { add(x, 0, x, 100); });
      [14, 70, 86].forEach(function (y) { add(0, y, 100, y); });
      add(22, 70, 50, 14, 1); add(78, 70, 50, 14, 1); add(8, 100, 50, 6); add(92, 100, 50, 6); // a roof of lines over the window
      var head = (S.heroLines && S.heroLines.length ? S.heroLines : [S.tagline || S.name]).map(E).join("<br>");
      return '<section class="hbp" id="top"><svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">' + lines.join("") + "</svg>" +
        (ph ? '<div class="win"><img src="' + E(ph) + '" alt="' + E(S.name) + '"></div>' : "") +
        '<div class="say"><h1>' + head + "</h1>" + (S.lede ? "<p>" + E(S.lede) + "</p>" : "") +
        '<a class="btn a" href="#menu">' + E(t.see) + '</a></div><div class="word" aria-hidden="true"><span>' + E(S.word || S.name) + "</span></div></section>";
    }
  };

  /* gallery-curve — the photos hang on a curved wall around you, in a dark room with a grid floor; drag, swipe or the
     arrows turn the wall, and the photo in front is named under it. */
  P["gallery-curve"] = {
    css: ".gcv{position:relative;overflow:hidden;padding:clamp(70px,9vw,130px) 0 clamp(50px,6vw,90px);color:var(--paper);" +
      "background:linear-gradient(transparent 62%,color-mix(in srgb,var(--accent) 12%,transparent)),repeating-linear-gradient(90deg,color-mix(in srgb,var(--paper) 7%,transparent) 0 1px,transparent 1px 64px)," +
      "repeating-linear-gradient(color-mix(in srgb,var(--paper) 7%,transparent) 0 1px,transparent 1px 64px),var(--ink)}" +
      ".gcv h2{padding:0 var(--gut);font-size:var(--head);margin-bottom:clamp(20px,3vw,40px)}" +
      ".gcv .stage{position:relative;height:clamp(260px,40vw,480px);perspective:1100px;touch-action:pan-y;cursor:grab}.gcv .stage:active{cursor:grabbing}" +
      ".gcv .ring{position:absolute;inset:0;transform-style:preserve-3d;transition:transform .8s cubic-bezier(.2,.8,.2,1)}.gcv .ring.drag{transition:none}" +
      ".gcv .card{position:absolute;left:50%;top:50%;width:var(--cw);height:calc(var(--cw)*.62);margin:calc(var(--cw)*-.31) 0 0 calc(var(--cw)/-2);border-radius:calc(var(--r-card)/3);overflow:hidden;" +
      "backface-visibility:hidden;box-shadow:0 30px 60px #0008;transition:filter .5s,opacity .5s}" +
      ".gcv .card img{width:100%;height:100%;object-fit:cover;display:block;pointer-events:none}.gcv .card:not(.on){filter:brightness(.55) saturate(.8)}" +
      ".gcv .foot{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:22px var(--gut) 0}" +
      ".gcv .cap{font:700 var(--lead)/1.3 var(--display)}.gcv .cap small{display:block;font:500 var(--small)/1.4 var(--text);color:var(--muted);letter-spacing:.12em}" +
      ".gcv .foot button{width:48px;height:48px;border-radius:50%;border:1px solid color-mix(in srgb,var(--paper) 45%,transparent);background:none;color:inherit;font-size:22px;cursor:pointer;margin-inline-start:8px}" +
      "[dir=rtl] .gcv .foot button{transform:scaleX(-1)}" +
      "@media (prefers-reduced-motion:reduce){.gcv .ring,.gcv .card{transition:none}}",
    render: function (S, t) {
      var m = S.media || {}, list = (m.gallery || []).slice(0, 8);
      if (list.length < 3) return "";
      return '<section class="gcv" id="gallery" aria-roledescription="carousel"><h2>' + E(t.gallery) + '</h2><div class="stage"><div class="ring">' +
        list.map(function (g, i) { return '<div class="card"><img src="' + E(g.src) + '" alt="' + E(g.alt || S.name) + '"' + (i > 2 ? ' loading="lazy"' : "") + "></div>"; }).join("") +
        '</div></div><div class="foot"><div class="cap" aria-live="polite"><small></small><span></span></div><div><button type="button" class="prev" aria-label="previous">‹</button>' +
        '<button type="button" class="next" aria-label="next">›</button></div></div></section>';
    },
    init: function (S) {
      var sec = document.querySelector(".gcv"); if (!sec) return;
      var list = (S.media.gallery || []).slice(0, 8), stage = sec.querySelector(".stage"), ring = sec.querySelector(".ring"), cards = sec.querySelectorAll(".card");
      var N = cards.length, at = 0, step = 0, R = 0, dir = document.documentElement.dir === "rtl" ? 1 : -1, drag = null; // RTL: the next photo is on the left
      function layout() {
        var w = stage.clientWidth, cw = Math.round(Math.min(560, w * (w > 700 ? .44 : .74)));
        stage.style.setProperty("--cw", cw + "px");
        R = Math.round(cw * 1.9); step = 2 * Math.atan(cw * .56 / R) * 180 / Math.PI; // neighbours just touch on the curve
        [].forEach.call(cards, function (c, i) { c.style.transform = "rotateY(" + (i * step * dir) + "deg) translateZ(" + (-R) + "px)"; });
        go(at);
      }
      function turn(deg) { ring.style.transform = "translateZ(" + R + "px) rotateY(" + deg + "deg)"; }
      function go(n) {
        at = Math.max(0, Math.min(N - 1, n)); turn(-at * step * dir);
        [].forEach.call(cards, function (c, i) { c.classList.toggle("on", i === at); });
        sec.querySelector(".cap small").textContent = (at < 9 ? "0" : "") + (at + 1) + " / " + (N < 10 ? "0" : "") + N;
        sec.querySelector(".cap span").textContent = list[at].alt || "";
      }
      sec.querySelector(".next").addEventListener("click", function () { go(at + 1); });
      sec.querySelector(".prev").addEventListener("click", function () { go(at - 1); });
      stage.addEventListener("pointerdown", function (e) { drag = {x: e.clientX, at: at}; ring.classList.add("drag"); });
      addEventListener("pointermove", function (e) { if (drag) turn(-drag.at * step * dir - (e.clientX - drag.x) / stage.clientWidth * step * 2.4); });
      addEventListener("pointerup", function (e) {
        if (!drag) return; ring.classList.remove("drag");
        var moved = (e.clientX - drag.x) / stage.clientWidth * 2.4; drag = null;
        go(at + Math.round(moved * dir));
      });
      addEventListener("resize", layout);
      layout();
    }
  };

  /* about-labels — on a light page the about text appears line by line in black labels that slide open, beside a giant
     outlined brand word and a thin beam of the accent colour that tilts as you scroll. */
  P["about-labels"] = {
    css: ".alb{position:relative;overflow:hidden;background:var(--paper);color:var(--ink);padding:clamp(90px,13vw,200px) var(--gut);min-height:70svh}" +
      ".alb .ghost{position:absolute;top:clamp(30px,5vw,70px);inset-inline-start:var(--gut);font:800 clamp(70px,14vw,220px)/1 var(--display);color:transparent;" +
      "-webkit-text-stroke:1px color-mix(in srgb,var(--ink) 30%,transparent);white-space:nowrap;pointer-events:none}" +
      ".alb .beam{position:absolute;top:8%;inset-inline-end:16%;width:clamp(6px,.8vw,12px);height:84%;border-radius:12px;background:linear-gradient(var(--accent),color-mix(in srgb,var(--accent) 30%,var(--paper)));" +
      "transform:rotate(var(--tilt,24deg));box-shadow:0 0 40px color-mix(in srgb,var(--accent) 50%,transparent);pointer-events:none}" +
      ".alb .txt{position:relative;max-width:min(30em,100%);font:700 clamp(20px,2.4vw,34px)/1.9 var(--display);margin:0}" +
      ".alb h2{position:relative;font-size:var(--small);letter-spacing:.2em;font-family:var(--text);color:var(--muted);margin:0 0 20px}" +
      ".alb .lb{background:var(--ink);color:var(--paper);padding:.08em .35em;-webkit-box-decoration-break:clone;box-decoration-break:clone;" +
      "clip-path:inset(0 100% 0 0);transition:clip-path .7s cubic-bezier(.7,0,.2,1);transition-delay:calc(var(--i) * 140ms)}" +
      "[dir=rtl] .alb .lb{clip-path:inset(0 0 0 100%)}.alb.on .lb{clip-path:inset(0)}" +
      "@media (max-width:700px){.alb .beam{inset-inline-end:6%;opacity:.6}}" +
      "@media (prefers-reduced-motion:reduce){.alb .lb{clip-path:none;transition:none}}",
    render: function (S, t) {
      if (!S.about) return "";
      var w = String(S.about).split(/\s+/), parts = [];
      for (var i = 0; i < w.length; i += 4) parts.push(w.slice(i, i + 4).join(" ")); // whole words only: Arabic letters stay joined
      return '<section class="alb" id="about"><div class="ghost" aria-hidden="true">' + E(S.word || S.name) + '</div><div class="beam" aria-hidden="true"></div>' +
        "<h2>" + E(t.about) + '</h2><p class="txt">' + parts.map(function (p, k) { return '<span class="lb" style="--i:' + k + '">' + E(p) + "</span>"; }).join(" ") + "</p></section>";
    },
    init: function () {
      var sec = document.querySelector(".alb"); if (!sec) return;
      once(sec, "on", .35);
      if (SITEKIT.reduce) return;
      var beam = sec.querySelector(".beam"), q = false;
      var tick = function () { q = false; var r = sec.getBoundingClientRect(), p = SITEKIT.clamp(1 - (r.top + r.height) / (innerHeight + r.height)); beam.style.setProperty("--tilt", (14 + p * 26).toFixed(1) + "deg"); };
      addEventListener("scroll", function () { if (!q) { q = true; requestAnimationFrame(tick); } }, {passive: true}); tick();
    }
  };
})(window.PIECES = window.PIECES || {});
