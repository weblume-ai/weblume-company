# Skill: GSAP motion for hand-written sites (from the official GSAP skills, MIT)
Use GSAP when a page you write by hand needs real choreography: a timeline, a scroll-scrubbed scene, a pinned
chapter. A one-line hover or fade stays in CSS. (The factory's pieces have their own motion engine; this is for
pages Karim writes himself.)

Load (free, pinned, no build step), at the end of <body>:
  <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js"></script>
  then once: gsap.registerPlugin(ScrollTrigger);
If GSAP fails to load the page must still read: content is visible by default and GSAP only animates it in
(gsap.from / fromTo), never a CSS `opacity:0` that waits for JavaScript.

Core rules
- Animate transforms and opacity only: x, y, xPercent, scale, rotation, autoAlpha (opacity + hides when 0).
  Never width, height, top, left or margin for movement.
- Sequence with a timeline, never with chains of `delay`: gsap.timeline({ defaults: { duration: .8, ease: "power3.out" } })
  and place steps with the position parameter ("<", "-=0.3", labels).
- Same move on many items → one tween with `stagger: 0.08`, not a loop of tweens.
- Built-in eases only: power2/power3/power4 .out for entrances, "expo.out" for big reveals, "back.out(1.6)" for a
  playful pop, "none" for anything tied to the scroll.
- Several from() tweens on the same property of one element: give the later ones immediateRender: false.

ScrollTrigger
- Put scrollTrigger on a timeline or a top-level tween, never on a tween inside a timeline.
- Choose ONE: scrub (progress follows the scroll: parallax, a product turning, a line filling) or toggleActions
  ("play none none reverse": plays once as it arrives). Never both.
- Pinning: pin the section, end: "+=150%", scrub: 1; keep pinSpacing on. One or two pinned chapters per page, not more.
- Horizontal galleries driven by vertical scroll: the horizontal tween uses ease: "none".
- Create triggers top to bottom; call ScrollTrigger.refresh() after images or fonts change the layout
  (window.addEventListener("load", () => ScrollTrigger.refresh())).
- Never leave markers: true in a page we ship.

Accessibility and phones
- Wrap everything in gsap.matchMedia(): "(prefers-reduced-motion: no-preference)" gets the motion; reduced motion gets
  the final state instantly. Phones (max-width: 768px) get shorter distances and no pinning of tall sections.
- RTL: our pages are dir="rtl"; "from the start" means from the right (x: 60 enters from the right side in RTL
  reading order only if you mean it; check the direction by eye).

Patterns that fit Phainora sites (pick the ones the site's direction needs, not all of them)
- Masked headline: each line rises from behind its own baseline (wrap the line in overflow:hidden, from y:"110%"),
  0.9 s, expo.out, the second line 0.1 s later; then the button.
- Image that opens: clipPath from "inset(0 0 100% 0)" to "inset(0 0 0% 0)" while the photo settles from scale 1.12 to 1.
- Pinned story: the section pins while 3-4 short lines swap or a photo zooms (scrub: 1).
- Product on scroll: the hero product turns or rises (rotation / y, scrub) as the first screen leaves.
- Menu cards: batch them with ScrollTrigger.batch(".card", { onEnter: b => gsap.from(b, { y: 40, autoAlpha: 0, stagger: .08 }) }).
- Numbers that roll up only when the number is true (years open, branches), never invented stats.
Clean up: kill tweens you replace; don't create hundreds of triggers; test on a phone-sized window.
