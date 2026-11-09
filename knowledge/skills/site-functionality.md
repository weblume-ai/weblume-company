# Skill: everything clickable works
- Mobile menu: button[aria-expanded] opens a panel; closes on link click and Escape; body scroll locked while open.
- Smooth anchors: html{scroll-behavior:smooth} + scroll-margin-top for the fixed header. No href="#" placeholders.
- Menu/product filters: buttons with data-filter, active state, short fade.
- WhatsApp order (cafés, shops): cart in localStorage (inside try/catch), +/- qty, total, checkout opens
  https://wa.me/<the CLIENT's number>?text=... with encodeURIComponent. Only the client's number from the request;
  if none, leave PHONE empty and say so. Never Weblume's or the owner's number.
- Booking/contact form: validate required fields, send through WhatsApp or mailto, show a success state.
- AR/EN switch: flips lang and dir, remembers the choice.
- Gallery lightbox with arrows and Escape. FAQ with <details>. Footer year from new Date().
- Images: the client's real photos, or free stock (Pexels) when they're weak. Add width/height and loading="lazy".
  Never draw illustrations in code instead of photos, never invent image links.
