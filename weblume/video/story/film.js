// Weblume's story reel (from the approved «الكافيه بتاعك» ad): pure function of time. window.seek(t) paints frame t.
// The timing, camera and sound are the approved film's; the words, menu items and site pages come from story.json,
// written per client by Hassan (weblume/video/__init__.py: render_story).
// Timing is in beats (u) on the measured grid; docs/shotlist.md is the plan this file follows.
// Arabic is drawn a whole word at a time (per-glyph drawing would break the letter joins).
import * as M from './lib/motion.js';

const { W, H, E, prog, lerp, clamp, springU, springKeys, SPRING, kf, shake, font, fill, rrect, mix, hash01 } = M;

const C = { red: '#e5121d', white: '#ffffff', ink: '#111111', gray: '#8a8a90', paper: '#f3ead8', paperInk: '#2a2118' };
const D = 'Display', UI = 'UI';
const MC = document.createElement('canvas').getContext('2d');  // measures text for drawings first laid out with a stand-in context
const S = await fetch('story.json').then((r) => r.json());
// "صنف خلص؟ اتشطب *بالقلم*." -> the plain line, and the starred words in red
function marked(str) {
  const colors = {}, words = String(str || '').trim().split(/\s+/).map((w, i) => (/^\*.+\*[.؟!…،]*$/.test(w) ? ((colors[i] = C.red), w.replace(/\*/g, '')) : w));
  return { text: words.join(' '), colors };
}

// [beat, label, sfx, opts]: sfx.mjs voices every one, so sound can't drift from picture.
const HITS = [
  [0, 'hook word 1', 'impact', { len: 1.0 }],
  [2, 'hook word 2', 'thud'],
  [3.6, 'menu slides up', 'whoosh', { len: 0.4 }],
  [5, 'strike 1', 'type', { n: 4, len: 0.35 }],
  [6, 'strike 2', 'type', { n: 4, len: 0.35 }],
  [8, 'stamp', 'thud', { pitch: 'A2' }],
  [8.05, 'stamp click', 'click'],
  [10, 'reprints drop', 'thud'],
  [11.75, 'whip to chat', 'whoosh', { len: 0.4 }],
  [12, 'bubble 1', 'pop', { pitch: 'E5' }],
  [13, 'bubble 2', 'pop', { pitch: 'A5' }],
  [14, 'no reply', 'type', { n: 6, len: 0.6 }],
  [16, 'drop: QR card', 'riser', { len: 2 }],
  [16, 'drop impact', 'impact', { len: 1.2 }],
  [18, 'viewfinder', 'click'],
  [18.1, 'scan beep', 'blip', { pitch: 'E6' }],
  [19.75, 'into phone', 'whoosh', { len: 0.5 }],
  [20, 'phone lands', 'thud'],
  [22, 'caption menu', 'tick'],
  [22, 'swipe 1', 'whoosh', { len: 0.3, from: 2200, to: 800 }],
  [23.5, 'swipe 2', 'whoosh', { len: 0.3, from: 2200, to: 800 }],
  [25, 'caption paper', 'tick'],
  [26.5, 'swipe 4', 'whoosh', { len: 0.3, from: 2200, to: 800 }],
  [20.3, 'caption site', 'tick'],
  [28, 'swipe 5', 'whoosh', { len: 0.3, from: 2200, to: 800 }],
  [30, 'push in', 'pop', { pitch: 'D6' }],
  [34, 'back to cover', 'whoosh', { len: 0.4, from: 800, to: 2200 }],
  [35, 'circle', 'type', { n: 3, len: 0.3 }],
  [36, 'pull back', 'whoosh', { len: 0.5 }],
  [39.75, 'to offer', 'whoosh', { len: 0.5 }],
  [40, 'offer 1', 'impact', { len: 1.0 }],
  [41, 'marker 1', 'click'],
  [44, 'offer 2', 'thud'],
  [45, 'marker 2', 'click'],
  [49.75, 'to end', 'whoosh', { len: 0.5 }],
  [50, 'end card', 'impact', { len: 1.6 }],
  [50.5, 'logo', 'bell', { pitch: 'A6' }],
  [51.5, 'cta', 'pop', { pitch: 'E5' }],
  [52.5, 'handles', 'tick'],
];

// ---------------------------------------------------------------- text helpers
function measure(ctx, str, f, dir = 'rtl') {
  ctx.save(); ctx.font = f; ctx.direction = dir; const w = ctx.measureText(str).width; ctx.restore(); return w;
}
function txt(ctx, str, x, y, f, color, align = 'right', dir = 'rtl') {
  ctx.save(); ctx.font = f; ctx.direction = dir; ctx.textAlign = align; ctx.fillStyle = color; ctx.fillText(str, x, y); ctx.restore();
}
const fit = (ctx, str, wt, fam, maxW, max) => Math.min(max, Math.floor((max * maxW) / measure(ctx, str, font(max, wt, fam))));

// A line of Arabic words rising out of a mask at its baseline, right to left, one spring each.
function rise(ctx, str, cx, y, size, wt, fam, color, u, u0, { stagger = 0.12, cfg = SPRING.snappy, colors = {}, marker = null } = {}) {
  const f = font(size, wt, fam), ws = str.split(' '), sp = measure(ctx, ' ', f);
  const widths = ws.map((w) => measure(ctx, w, f));
  const total = widths.reduce((a, b) => a + b, 0) + sp * (ws.length - 1);
  const right = cx + total / 2;
  if (marker) {   // red block wiping in right-to-left behind the line
    const p = E.outQuint(prog(u, marker, marker + 0.6));
    if (p > 0) { ctx.fillStyle = C.red; rrect(ctx, right + 22 - (total + 44) * p, y - size * 0.98, (total + 44) * p, size * 1.3, 14); ctx.fill(); }
  }
  let x = right;
  ws.forEach((w, i) => {
    const k = springU(u, u0 + i * stagger, cfg);
    if (k > 0.001) {
      ctx.save();
      ctx.beginPath(); ctx.rect(0, y - size * 1.4, W, size * 1.9); ctx.clip();
      txt(ctx, w, x, y + (1 - k) * size * 1.35, f, colors[i] || color);
      ctx.restore();
    }
    x -= widths[i] + sp;
  });
}

// A caption that rises in at u0 and drops out before u1, centred at y.
function caption(ctx, line, u, u0, u1, y, { size = 84 } = {}) {
  if (u < u0 - 0.1 || u > u1 || !line) return;
  const { text: str, colors } = marked(line);
  const out = E.inBack(prog(u, u1 - 0.35, u1), 1.4);
  ctx.save(); ctx.globalAlpha = 1 - out; ctx.translate(0, -out * 60);
  const s = fit(ctx, str, 900, D, 900, size);
  rise(ctx, str, W / 2, y, s, 900, D, C.white, u, u0, { stagger: 0.1, colors });
  ctx.restore();
}

// ---------------------------------------------------------------- phone (titanium, Dynamic Island, glass)
const PW = 620, PH = 1290, PR = 104, SI = 22, SW = PW - 2 * SI, SH = PH - 2 * SI, SRAD = PR - SI;

function button(ctx, x, y, w, h) {
  const g = ctx.createLinearGradient(x, 0, x + w, 0);
  g.addColorStop(0, '#5a5d61'); g.addColorStop(0.5, '#c4c6c9'); g.addColorStop(1, '#6b6e72');
  ctx.fillStyle = g; rrect(ctx, x, y, w, h, 3); ctx.fill();
}

function phone(ctx, x, y, s, rot, screen, glare, over) {
  ctx.save();
  ctx.translate(x, y + (PH * s) / 2); ctx.rotate(rot); ctx.scale(s, s); ctx.translate(-PW / 2, -PH / 2);
  button(ctx, -5, 236, 8, 58); button(ctx, -5, 330, 8, 100); button(ctx, -5, 452, 8, 100); button(ctx, PW - 3, 390, 8, 160);
  const g = ctx.createLinearGradient(0, 0, PW, 0);
  [[0, '#4d5054'], [0.012, '#d9dbde'], [0.028, '#878a8f'], [0.2, '#b2b5b9'], [0.5, '#9b9ea3'], [0.8, '#b8bbbf'],
    [0.972, '#7e8186'], [0.988, '#e0e2e4'], [1, '#474a4e']].forEach(([o, c]) => g.addColorStop(o, c));
  rrect(ctx, 0, 0, PW, PH, PR); ctx.fillStyle = g; ctx.fill();
  const v = ctx.createLinearGradient(0, 0, 0, PH);
  v.addColorStop(0, 'rgba(255,255,255,.22)'); v.addColorStop(0.06, 'rgba(255,255,255,0)');
  v.addColorStop(0.94, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,.3)');
  ctx.fillStyle = v; ctx.fill();
  ctx.lineWidth = 2; ctx.strokeStyle = 'rgba(0,0,0,.55)'; rrect(ctx, 1, 1, PW - 2, PH - 2, PR - 1); ctx.stroke();
  ctx.lineWidth = 1.2; ctx.strokeStyle = 'rgba(255,255,255,.4)'; rrect(ctx, 4, 4, PW - 8, PH - 8, PR - 4); ctx.stroke();
  rrect(ctx, 9, 9, PW - 18, PH - 18, PR - 9); ctx.fillStyle = '#030303'; ctx.fill();
  ctx.save();
  ctx.translate(SI, SI);
  rrect(ctx, 0, 0, SW, SH, SRAD); ctx.clip();
  screen(ctx);
  ctx.fillStyle = '#000'; rrect(ctx, SW / 2 - 88, 20, 176, 52, 26); ctx.fill();
  const lens = ctx.createRadialGradient(SW / 2 + 56, 44, 1, SW / 2 + 56, 46, 12);
  lens.addColorStop(0, '#2b3f57'); lens.addColorStop(0.5, '#0b121b'); lens.addColorStop(1, '#000');
  ctx.fillStyle = lens; ctx.beginPath(); ctx.arc(SW / 2 + 56, 46, 11, 0, M.TAU); ctx.fill();
  const gx = lerp(-SW * 0.6, SW * 1.1, glare);
  const sh = ctx.createLinearGradient(gx, 0, gx + SW * 0.7, SH * 0.55);
  sh.addColorStop(0, 'rgba(255,255,255,0)'); sh.addColorStop(0.45, 'rgba(255,255,255,0.075)');
  sh.addColorStop(0.55, 'rgba(255,255,255,0.11)'); sh.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = sh; ctx.fillRect(0, 0, SW, SH);
  ctx.restore();
  if (over) { ctx.save(); ctx.translate(SI, SI); over(ctx); ctx.restore(); }
  ctx.restore();
}

function statusBar(ctx, time, color) {
  txt(ctx, time, 66, 52, font(29, 700, UI), color, 'left', 'ltr');
  ctx.fillStyle = color;
  const bx = SW - 156;
  [8, 11, 14, 17].forEach((h, i) => { rrect(ctx, bx + i * 8, 49 - h, 5.5, h, 1.5); ctx.fill(); });
  ctx.save(); ctx.strokeStyle = color; ctx.lineWidth = 3.4; ctx.lineCap = 'round';
  for (const r of [5, 10.5, 16]) { ctx.beginPath(); ctx.arc(SW - 102, 51, r, -Math.PI * 0.76, -Math.PI * 0.24); ctx.stroke(); }
  ctx.restore();
  ctx.save(); ctx.globalAlpha = 0.45; ctx.strokeStyle = color; ctx.lineWidth = 1.6; rrect(ctx, SW - 80, 32, 42, 20, 6); ctx.stroke();
  ctx.fillRect(SW - 36, 38, 3, 8); ctx.restore();
  rrect(ctx, SW - 77, 35, 30, 14, 3.5); ctx.fill();
}

// ---------------------------------------------------------------- the real Bake Home menu (assets/bakehome/pageN.png, 1170×2532 = 390×844 @3x)
// The site is a pager: one category per page, swiped sideways. Prices are hidden for the ad (shoot-bakehome.mjs).
const PAGES = S.pages, CREDIT_Y = S.credit_y, LIGHT = S.light;   // pages with a light background (dark status bar)                 // cover page: «تصميم وتطوير Weblume» line, as a fraction of the screen height
// page index over time: cover, then a swipe on each beat pair, back to the cover for the credit
function pageAt(u) { return springKeys(u, [[-99, 0], [22, 1], [23.5, 2], [25, 3], [26.5, 4], [28, 5], [34, 0]].map(([b, pg]) => [b, Math.min(pg, PAGES - 1)]), SPRING.snappy); }

function siteScreen(u, IMG) {
  return (ctx) => {
    ctx.fillStyle = '#1b1310'; ctx.fillRect(0, 0, SW, SH);
    const p = pageAt(u), a = Math.floor(p), fr = p - a;
    // RTL pager: the next page comes in from the left
    for (const [i, off] of [[a, fr * SW], [a + 1, (fr - 1) * SW]]) {
      const img = IMG[`p${i}`];  // shortcut: still pages, not each page's own entrance animation (the Bake Home ad filmed those)
      if (img && i >= 0 && i < PAGES && Math.abs(off) < SW) ctx.drawImage(img, off, 0, SW, SH);
    }
    statusBar(ctx, '9:41', LIGHT.includes(Math.round(p)) ? C.ink : C.white);
  };
}

// hand-drawn red ring around the real credit line on the cover
function footerRing(u) {
  return (ctx) => {
    const p = CREDIT_Y ? E.outCubic(prog(u, 35, 35.7)) * (1 - prog(u, 39, 39.4)) : 0;  // only when the cover carries our credit line
    if (p <= 0) return;
    const cx = SW * 0.5, cy = SH * CREDIT_Y - 12;
    ctx.save(); ctx.strokeStyle = C.red; ctx.lineWidth = 6; ctx.lineCap = 'round';
    ctx.beginPath();
    for (let i = 0; i <= 60 * p; i++) {
      const ang = -Math.PI / 2 + (i / 60) * M.TAU * 1.06, r = 1 + 0.04 * Math.sin(i * 0.7);
      const px = cx + Math.cos(ang) * 200 * r, py = cy + Math.sin(ang) * 44 * r;
      i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
    }
    ctx.stroke(); ctx.restore();
  };
}

// ---------------------------------------------------------------- props: paper menu, chat, QR card
const ITEMS = S.items.slice(0, 6);

function paperMenu(ctx, cx, cy, s, rot, u, seed) {
  const w = 760, h = 1040;
  ctx.save(); ctx.translate(cx, cy); ctx.rotate(rot); ctx.scale(s, s);
  ctx.shadowColor = 'rgba(0,0,0,.55)'; ctx.shadowBlur = 50; ctx.shadowOffsetY = 26;
  ctx.fillStyle = C.paper; ctx.fillRect(-w / 2, -h / 2, w, h);
  ctx.shadowColor = 'transparent';
  // paper fibre: seeded specks, a centre fold and a coffee ring
  for (let i = 0; i < 900; i++) {
    const x = (hash01(i, seed) - 0.5) * w, y = (hash01(i + 9999, seed) - 0.5) * h;
    ctx.fillStyle = `rgba(90,70,40,${0.03 + 0.05 * hash01(i + 333, seed)})`; ctx.fillRect(x, y, 2, 2);
  }
  const fold = ctx.createLinearGradient(-20, 0, 20, 0);
  fold.addColorStop(0, 'rgba(0,0,0,0)'); fold.addColorStop(0.5, 'rgba(0,0,0,.08)'); fold.addColorStop(0.52, 'rgba(255,255,255,.35)'); fold.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = fold; ctx.fillRect(-20, -h / 2, 40, h);
  ctx.strokeStyle = 'rgba(120,72,30,.22)'; ctx.lineWidth = 10;
  ctx.beginPath(); ctx.ellipse(-w * 0.22, h * 0.3, 95, 90, 0.3, 0.2, M.TAU - 0.5); ctx.stroke();
  ctx.lineWidth = 3; ctx.beginPath(); ctx.ellipse(-w * 0.22, h * 0.3, 104, 99, 0.3, 0.8, M.TAU - 1.2); ctx.stroke();
  // printed type
  txt(ctx, 'المنيو', 0, -h / 2 + 150, font(96, 900, D), C.paperInk, 'center');
  ctx.fillStyle = C.paperInk; ctx.fillRect(-90, -h / 2 + 182, 180, 4);
  ITEMS.forEach((it, i) => {
    const y = -h / 2 + 300 + i * 118;
    txt(ctx, it, w / 2 - 90, y, font(Math.min(58, fit(ctx, it, 700, D, w - 200, 58)), 700, D), C.paperInk, 'right', /[\u0600-\u06FF]/.test(it) ? 'rtl' : 'ltr');
    ctx.fillStyle = 'rgba(42,33,24,.25)'; ctx.fillRect(-w / 2 + 90, y + 24, w - 180, 2);
  });
  // red marker strikes on two items, drawn as the beat lands
  [[1, 5], [Math.min(4, ITEMS.length - 1), 6]].forEach(([i, b]) => {
    const p = E.outCubic(prog(u, b, b + 0.4));
    if (p <= 0) return;
    const y = -h / 2 + 300 + i * 118 - 18, x0 = w / 2 - 70, x1 = -w / 2 + 160;
    ctx.save(); ctx.strokeStyle = C.red; ctx.lineWidth = 16; ctx.lineCap = 'round'; ctx.globalAlpha = 0.92;
    ctx.beginPath(); ctx.moveTo(x0, y);
    for (let k = 1; k <= 24; k++) { const f = (k / 24) * p; ctx.lineTo(lerp(x0, x1, f), y + Math.sin(f * 11 + i) * 7); }
    ctx.stroke(); ctx.restore();
  });
  ctx.restore();
}

function stamp(ctx, u) {
  const k = springU(u, 8, SPRING.bouncy);
  if (k <= 0.001) return;
  const s = 2.6 * (1 / 2.6) ** clamp(k, 0, 1.1);
  ctx.save(); ctx.translate(W / 2, 1420); ctx.rotate(-0.08); ctx.scale(s, s);
  ctx.globalAlpha = clamp(k * 2);
  const str = S.stamp, f = font(Math.min(84, fit(ctx, S.stamp, 900, D, 820, 84)), 900, D), w = measure(ctx, str, f) + 80;
  ctx.shadowColor = 'rgba(0,0,0,.45)'; ctx.shadowBlur = 30; ctx.fillStyle = '#fbf6ec'; rrect(ctx, -w / 2, -80, w, 140, 16); ctx.fill(); ctx.shadowColor = 'transparent';
  ctx.strokeStyle = C.red; ctx.lineWidth = 10; rrect(ctx, -w / 2, -80, w, 140, 16); ctx.stroke();
  ctx.lineWidth = 3; rrect(ctx, -w / 2 + 14, -66, w - 28, 112, 10); ctx.stroke();
  txt(ctx, str, 0, 20, f, C.red, 'center');
  ctx.restore();
}

function bubble(ctx, str, u, u0, y, side, { grey = false, size = 78 } = {}) {
  const k = springU(u, u0, SPRING.bouncy);
  if (k <= 0.001) return;
  size = Math.min(size, fit(ctx, str, 800, D, W - 280, size));  // never wider than the screen
  const f = font(size, 800, D), w = measure(ctx, str, f) + 96, h = size * 1.9;
  const x = side === 'r' ? W - 90 - w : 90;
  ctx.save(); ctx.translate(x + (side === 'r' ? w : 0), y + h); ctx.scale(k, k); ctx.translate(-(x + (side === 'r' ? w : 0)), -(y + h));
  ctx.fillStyle = grey ? 'transparent' : '#2b2b2e';
  if (!grey) { rrect(ctx, x, y, w, h, 46); ctx.fill(); }
  txt(ctx, str, x + w - 48, y + h * 0.66, f, grey ? C.gray : C.white, 'right');
  ctx.restore();
}

function qrCard(ctx, cx, cy, s) {
  const w = 600, h = 760;
  ctx.save(); ctx.translate(cx, cy); ctx.scale(s, s);
  ctx.shadowColor = 'rgba(0,0,0,.6)'; ctx.shadowBlur = 60; ctx.shadowOffsetY = 30;
  ctx.fillStyle = '#ffffff'; rrect(ctx, -w / 2, -h / 2, w, h, 36); ctx.fill(); ctx.shadowColor = 'transparent';
  txt(ctx, S.qr_title, 0, -h / 2 + 110, font(Math.min(56, fit(MC, S.qr_title, 900, D, w - 80, 56)), 900, D), C.ink, 'center');
  // QR modules: seeded pattern with the three finder squares (no real link encoded)
  const n = 25, q = 16, x0 = -(n * q) / 2, y0 = -h / 2 + 170;
  ctx.fillStyle = C.ink;
  for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) {
    const inF = (r < 8 && c < 8) || (r < 8 && c >= n - 8) || (r >= n - 8 && c < 8);
    if (!inF && hash01(r * n + c, 41) > 0.52) ctx.fillRect(x0 + c * q, y0 + r * q, q, q);
  }
  for (const [r, c] of [[0, 0], [0, n - 7], [n - 7, 0]]) {
    ctx.fillRect(x0 + c * q, y0 + r * q, 7 * q, 7 * q);
    ctx.fillStyle = '#fff'; ctx.fillRect(x0 + (c + 1) * q, y0 + (r + 1) * q, 5 * q, 5 * q);
    ctx.fillStyle = C.ink; ctx.fillRect(x0 + (c + 2) * q, y0 + (r + 2) * q, 3 * q, 3 * q);
  }
  txt(ctx, S.qr_sub, 0, h / 2 - 70, font(36, 700, UI), '#55555a', 'center');
  ctx.restore();
  return { x: cx, y: cy - h / 2 * s + (170 + (n * q) / 2) * s, size: n * q * s };
}

// ---------------------------------------------------------------- scenes
function background(ctx, u) {
  fill(ctx, '#000');
  const warm = u < 16 ? 0.25 : u < 40 ? 0.55 : 0.2;
  const r = ctx.createRadialGradient(W / 2, 1100, 40, W / 2, 1100, 1150);
  r.addColorStop(0, mix('#151517', '#2a0b0e', warm)); r.addColorStop(1, '#000');
  ctx.fillStyle = r; ctx.fillRect(0, 0, W, H);
}

function hook(ctx, u) {
  if (u > 4.2) return;
  const out = E.inBack(prog(u, 3.5, 4.1), 1.4) * 700;
  ctx.save(); ctx.translate(0, -out); shake(ctx, u, 2, 14);
  rise(ctx, S.hook1, W / 2, 820, fit(ctx, S.hook1, 900, D, 900, 150), 900, D, C.white, u, -0.3, { stagger: 0.15 });
  rise(ctx, S.hook2, W / 2, 1010, fit(ctx, S.hook2, 900, D, 900, 150), 900, D, C.red, u, 2, { cfg: SPRING.bouncy, stagger: 0.12 });
  ctx.restore();
}

function paperScenes(ctx, u) {
  if (u < 3.4 || u > 12.1) return;
  const enter = 1 - springU(u, 3.6, SPRING.gentle);
  const whip = E.inCubic(prog(u, 11.6, 12));               // menu slides out left as the chat slides in
  const z = 1.0 * (1.12 / 1.0) ** prog(u, 4, 12);           // slow log-space push
  ctx.save(); ctx.translate(-whip * W * 1.1, enter * 1500);
  // reprinted copies land under the menu on beat 10
  for (let i = 2; i >= 0; i--) {
    const k = springU(u, 10 + i * 0.12, SPRING.snappy);
    if (k > 0.001) paperMenu(ctx, W / 2 + (i - 1) * 46, 1060 + (1 - k) * -900 + i * 18, 0.92 * z, -0.05 + i * 0.07, -99, 7 + i);
  }
  paperMenu(ctx, W / 2, 1060, 0.92 * z, 0.035, u, 3);
  caption(ctx, S.paper1, u, 4.2, 8, 330);
  caption(ctx, S.paper2, u, 8.4, 12.2, 330);
  stamp(ctx, u);
  ctx.restore();
}

function chatScene(ctx, u) {
  if (u < 11.6 || u > 16.05) return;
  const enter = 1 - E.outCubic(prog(u, 11.6, 12));
  ctx.save(); ctx.translate(enter * W * 1.1, 0);
  txt(ctx, S.chat_to, W / 2, 600, font(44, 700, UI), C.gray, 'center');
  bubble(ctx, S.ask1, u, 12, 700, 'r');
  bubble(ctx, S.ask2, u, 13, 920, 'r');
  // «مفيش رد» types on, letter group by letter group
  rise(ctx, S.noreply, W / 2, 1280, fit(ctx, S.noreply, 900, D, 900, 110), 900, D, C.gray, u, 14, { stagger: 0.25 });
  ctx.restore();
}

function qrScene(ctx, u) {
  if (u < 15.95 || u > 20.2) return;
  const k = springU(u, 16, SPRING.bouncy);
  const s = 1.6 * (1 / 1.6) ** clamp(k, 0, 1.1);
  // camera dives into the QR from beat 18.4 (log-space zoom)
  const dive = E.inCubic(prog(u, 18.4, 20));
  const z = 1 * (7 / 1) ** dive;
  ctx.save();
  const card = { x: W / 2, y: 1000 };
  const q = qrCard(new Proxy({}, { get: () => () => {} }), card.x, card.y, s);   // geometry only
  M.zoomAbout(ctx, z, q.x, q.y);
  qrCard(ctx, card.x, card.y, s);
  // viewfinder corners snap on at beat 18
  const v = springU(u, 18, SPRING.snappy);
  if (v > 0.001) {
    const half = q.size * (0.75 + 0.35 * (1 - v));
    ctx.strokeStyle = C.white; ctx.lineWidth = 10; ctx.lineCap = 'round';
    for (const [sx, sy] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) {
      const x = q.x + sx * half, y = q.y + sy * half;
      ctx.beginPath(); ctx.moveTo(x, y - sy * 70); ctx.lineTo(x, y); ctx.lineTo(x - sx * 70, y); ctx.stroke();
    }
  }
  ctx.restore();
  if (u < 18.4) caption(ctx, S.qr_line, u, 16.2, 18.4, 330);
}

function phoneShot(ctx, u, IMG) {
  if (u < 19.9 || u > 41.2) return;
  const k = springU(u, 20, SPRING.gentle);
  const out = E.inCubic(prog(u, 39.7, 40.6));
  const s = springKeys(u, [[-99, 1.14], [30, 1.5], [33, 1.14], [36, 1.0]], SPRING.gentle);
  const y0 = 440 + (1 - k) * 1500 + out * 1700;
  const focus = springKeys(u, [[-99, 0], [30, 1], [33, 0], [36, 1.25]], SPRING.gentle);
  const fy = u < 34 || !CREDIT_Y ? SH * 0.3 : SH * CREDIT_Y;                 // featured item, or the credit line
  const shiftY = focus * (H * 0.56 - (y0 + (fy + SI) * s));
  const rot = springKeys(u, [[-99, 0.06], [20, 0], [36, -0.03]], SPRING.gentle);
  ctx.save();
  shake(ctx, u, 20, 8);
  phone(ctx, W / 2, y0 + shiftY, s, rot, siteScreen(u, IMG), clamp(prog(u, 20, 40)), footerRing(u));
  ctx.restore();
  const band = ctx.createLinearGradient(0, 0, 0, 470); band.addColorStop(0, 'rgba(0,0,0,.92)'); band.addColorStop(0.75, 'rgba(0,0,0,.8)'); band.addColorStop(1, 'rgba(0,0,0,0)');
  if (u > 21.8) { ctx.fillStyle = band; ctx.fillRect(0, 0, W, 470); }
  caption(ctx, S.phone[0], u, 20.3, 22, 300);
  caption(ctx, S.phone[1], u, 22, 25, 300);
  caption(ctx, S.phone[2], u, 25, 28, 300);
  caption(ctx, S.phone[3], u, 28.2, 33.6, 300);
  caption(ctx, S.phone[4], u, 34, 39.5, 300);
}

function offer(ctx, u) {
  if (u < 39.8 || u > 49.8) return;
  const enter = 1 - E.outCubic(prog(u, 39.6, 40.2));
  const out = E.inBack(prog(u, 49.05, 49.75), 1.4) * 1400;
  const z = 1.035 ** prog(u, 44, 49);
  ctx.save(); ctx.translate(0, enter * 900 - out); M.zoomAbout(ctx, z, W / 2, 1030);
  const [a, b, c, d] = S.offer;
  // each pair sized on its own line
  const s1 = fit(ctx, a, 800, D, 840, 140), s2 = fit(ctx, c, 800, D, 920, 140), s3 = Math.min(s2 * 1.22, fit(ctx, d, 900, D, 880, 170));
  rise(ctx, a, W / 2, 680, s1, 800, D, C.white, u, 40, { stagger: 0.1 });
  rise(ctx, b, W / 2, 860, s1 * 1.22, 900, D, C.white, u, 40.4, { stagger: 0.1, marker: 41 });
  rise(ctx, c, W / 2, 1140, s2, 800, D, C.white, u, 44, { stagger: 0.1 });
  rise(ctx, d, W / 2, 1320, s3, 900, D, C.white, u, 44.4, { stagger: 0.1, marker: 45 });
  ctx.restore();
}

function endCard(ctx, u, IMG) {
  if (u < 49.75) return;
  const k = springU(u, 49.85, SPRING.gentle);
  const s = 0.55 * (1 / 0.55) ** clamp(k, 0, 1.08) * (1 + 0.025 * prog(u, 52, 60));   // log-space scale
  const lw = 640, lh = lw;
  ctx.save();
  ctx.translate(0, (1 - k) * 500);
  ctx.globalCompositeOperation = 'screen';
  ctx.translate(W / 2, 780); ctx.scale(s, s);
  if (IMG.logo) ctx.drawImage(IMG.logo, -lw / 2, -lh / 2, lw, lh);
  ctx.restore();
  const s1 = fit(ctx, S.end1, 800, D, 900, 100);
  rise(ctx, S.end1, W / 2, 1170, s1, 800, D, C.white, u, 51.5, { stagger: 0.08 });
  rise(ctx, S.end2, W / 2, 1275, Math.min(s1 * 0.82, fit(ctx, S.end2, 700, D, 900, 82)), 700, D, '#d2d2d6', u, 52, { stagger: 0.08 });
  const hk = springU(u, 52.5, SPRING.snappy);
  if (hk > 0) {
    ctx.save(); ctx.beginPath(); ctx.rect(0, 1310, W, 100); ctx.clip();
    txt(ctx, '@weblume1  ·  @weblume9', W / 2, 1378 + (1 - hk) * 90, font(54, 700, UI), C.red, 'center', 'ltr');
    ctx.restore();
  }
}

M.film({
  fonts: [font(100, 800, D), font(100, 900, D), font(100, 700, D), font(40, 500, UI), font(40, 700, UI)],
  images: { logo: 'assets/weblume-logo.png', ...Object.fromEntries(Array.from({ length: PAGES }, (_, i) => [`p${i}`, `pages/p${i}.jpg`])) },
  hits: HITS,
  samples: 8,
  draw(ctx, u, t, IMG) {
    background(ctx, u);
    hook(ctx, u);
    paperScenes(ctx, u);
    chatScene(ctx, u);
    qrScene(ctx, u);
    phoneShot(ctx, u, IMG);
    offer(ctx, u);
    endCard(ctx, u, IMG);
  },
});
