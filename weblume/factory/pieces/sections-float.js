/* Pieces written by Weblume after design ideas in a screen recording Asser shared of a studio site: the brand name as
   big as the screen with objects floating around it, and a short statement with products floating below at different
   depths. Original vanilla code, no code, images or brand taken. RTL, phones, reduced motion respected. */
(function (P) {
  var E = function (s) { return SITEKIT.esc(s); };
  var things = function (S) { // cut-out products first (they float best), then dish photos
    var a = (S.showcase || []).filter(function (s) { return s.cut; }).map(function (s) { return {img: s.cut, name: s.name, cut: 1}; });
    (S.menu || []).forEach(function (c) { (c.items || []).forEach(function (i) { if (i.img && a.length < 6) a.push({img: i.img, name: i.name}); }); });
    return a.slice(0, 5);
  };
  var floaters = function (list, spots) {
    return list.map(function (t, i) {
      var s = spots[i % spots.length];
      return '<span class="fl' + (t.cut ? " cut" : "") + '" style="left:' + s[0] + "%;top:" + s[1] + "%;--z:" + s[2] + ";--d:" + (-i * 1.7) + 's" aria-hidden="true"><img src="' + E(t.img) + '" alt="" loading="lazy"></span>';
    }).join("");
  };
  var drift = function (sec) { // floaters follow the pointer (desktop) and the scroll, each at its own depth
    if (SITEKIT.reduce) return;
    var fl = sec.querySelectorAll(".fl"), mx = 0, my = 0, q = false;
    var tick = function () {
      q = false;
      var r = sec.getBoundingClientRect(), p = (r.top + r.height / 2) / innerHeight - .5;
      [].forEach.call(fl, function (f) { var z = +f.style.getPropertyValue("--z"); f.style.translate = (mx * 30 * z).toFixed(1) + "px " + (my * 24 * z - p * 160 * z).toFixed(1) + "px"; });
    };
    var ask = function () { if (!q) { q = true; requestAnimationFrame(tick); } };
    addEventListener("scroll", ask, {passive: true});
    if (matchMedia("(hover: hover)").matches) sec.addEventListener("pointermove", function (e) { mx = e.clientX / innerWidth - .5; my = e.clientY / innerHeight - .5; ask(); });
    tick();
  };
  var FLOAT_CSS = function (c) {
    return "." + c + " .fl{position:absolute;width:clamp(70px,calc(var(--z)*11vw),190px);aspect-ratio:1;pointer-events:none;z-index:calc(var(--z)*2);transition:translate .6s cubic-bezier(.2,.7,.2,1)}" +
      "." + c + " .fl img{width:100%;height:100%;object-fit:cover;border-radius:50%;box-shadow:0 24px 40px #0005;animation:flBob 7s ease-in-out var(--d) infinite}" +
      "." + c + " .fl.cut img{object-fit:contain;border-radius:0;box-shadow:none;filter:drop-shadow(0 24px 30px #0006)}@keyframes flBob{50%{transform:translateY(-14px) rotate(6deg)}}";
  };

  /* hero-wordmark — the place's name fills the screen edge to edge; its products float over and around it, following
     the pointer and drifting apart as you scroll; the headline and the order button sit small above. */
  P["hero-wordmark"] = {
    css: ".hwm{position:relative;min-height:calc(100svh - var(--nav));overflow:hidden;background:var(--paper);color:var(--ink);display:grid;grid-template-rows:auto 1fr;padding:clamp(18px,3vw,36px) var(--gut) 0}" +
      ".hwm .top{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:end;gap:14px 30px;position:relative;z-index:6}" +
      ".hwm h1{font-size:clamp(26px,3.2vw,48px);line-height:1.15;margin:0;max-width:16em}.hwm .top p{margin:6px 0 0;color:var(--muted);max-width:36ch}" +
      ".hwm .word{align-self:end;text-align:center;font:900 var(--wsize,20vw)/.86 var(--display);white-space:nowrap;letter-spacing:-.02em;margin:0 calc(var(--gut)*-1);overflow:hidden}" +
      ".hwm .word span{display:inline-block;transform:translateY(100%);animation:hwmRise 1.2s cubic-bezier(.2,.8,.2,1) .2s forwards}@keyframes hwmRise{to{transform:none}}" +
      FLOAT_CSS("hwm") +
      "@media (prefers-reduced-motion:reduce){.hwm .word span{animation:none;transform:none}.hwm .fl img{animation:none}}",
    render: function (S, t) {
      var head = (S.heroLines && S.heroLines.length ? S.heroLines : [S.tagline || S.name]).map(E).join(" ");
      return '<section class="hwm" id="top"><div class="top"><div><h1>' + head + "</h1>" + (S.lede ? "<p>" + E(S.lede) + "</p>" : "") +
        '</div><a class="btn a" href="#menu">' + E(t.see) + "</a></div>" +
        floaters(things(S), [[6, 30, 1.2], [78, 22, .8], [60, 58, 1.5], [18, 66, .9], [88, 62, 1.1]]) +
        '<div class="word" aria-hidden="true"><span>' + E(S.word || S.name) + "</span></div></section>";
    },
    init: function () {
      var sec = document.querySelector(".hwm"); if (!sec) return;
      var w = sec.querySelector(".word"), span = w.querySelector("span");
      var fit = function () { // the name is as wide as the screen, whatever its length
        w.style.setProperty("--wsize", "100px");
        var k = (w.clientWidth * .96) / Math.max(1, span.scrollWidth);
        w.style.setProperty("--wsize", Math.min(100 * k, innerHeight * .55) + "px");
      };
      fit(); addEventListener("resize", fit); if (document.fonts) document.fonts.ready.then(fit);
      drift(sec);
    }
  };

  /* about-floats — one short statement about the place, big and quiet, with its products floating below at different
     depths: the near ones move faster than the far ones as you scroll. */
  P["about-floats"] = {
    css: ".abf{position:relative;overflow:hidden;background:var(--ink);color:var(--paper);padding:clamp(80px,11vw,170px) var(--gut) 0;min-height:110svh}" +
      ".abf .say{position:relative;z-index:6;font:700 clamp(26px,3.8vw,58px)/1.25 var(--display);max-width:20em;margin:0}" +
      ".abf h2{font-size:var(--small);letter-spacing:.2em;font-family:var(--text);color:var(--accent);margin:0 0 18px}" +
      ".abf .field{position:relative;height:clamp(380px,60vw,640px)}" + FLOAT_CSS("abf") +
      ".abf .fl{width:clamp(90px,calc(var(--z)*14vw),240px)}" +
      "@media (prefers-reduced-motion:reduce){.abf .fl img{animation:none}}",
    render: function (S, t) {
      var list = things(S);
      if (!S.about || list.length < 3) return "";
      return '<section class="abf" id="about"><h2 class="rise">' + E(t.about) + '</h2><p class="say rise" style="--i:1">' + E(S.together || S.about) +
        '</p><div class="field">' + floaters(list, [[8, 10, 1.4], [62, 4, .8], [36, 40, 1.8], [80, 50, 1.1], [14, 62, .9]]) + "</div></section>";
    },
    init: function () { var sec = document.querySelector(".abf"); if (sec) drift(sec); }
  };
})(window.PIECES = window.PIECES || {});
