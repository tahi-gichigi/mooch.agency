/* Mooch entrance motion — declarative and page-agnostic.
   Timing is read from CSS custom properties (tokens.css), so the feel is tuned in
   one place. Two behaviours:
     - Word stagger on any [data-stagger] element (hero subheadings); an optional
       start time in seconds (data-stagger="0.2") leads or trails other elements.
     - Scroll reveal on any [data-reveal="child: <selector>; cap: <n>"] container.
   Both are no-ops under reduced motion or without IntersectionObserver, so content
   is always served fully visible — never trapped at opacity 0. */
(function () {
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var rootStyle = getComputedStyle(document.documentElement);

  function cssSeconds(prop, fallback) {
    var v = rootStyle.getPropertyValue(prop).trim();
    if (!v) return fallback;
    var n = parseFloat(v);
    if (isNaN(n)) return fallback;
    return /ms$/.test(v) ? n / 1000 : n;
  }

  // ── Word stagger ──
  // Walks child nodes recursively so nested spans (e.g. deck-lead / deck-tail)
  // are preserved and each word inherits its parent's colour.
  var wordBase = cssSeconds('--word-base', 0.40);
  var wordStep = cssSeconds('--word-step', 0.05);
  document.querySelectorAll('[data-stagger]').forEach(function (el) {
    // data-stagger may carry a start time in seconds (e.g. data-stagger="0.2")
    // to lead or trail other staggered elements; bare data-stagger uses --word-base.
    var attr = el.getAttribute('data-stagger');
    var base = attr && !isNaN(parseFloat(attr)) ? parseFloat(attr) : wordBase;
    var counter = 0;
    (function splitNode(node) {
      Array.prototype.slice.call(node.childNodes).forEach(function (child) {
        if (child.nodeType === Node.TEXT_NODE) {
          var parts = child.textContent.split(/(\s+)/);
          var frag = document.createDocumentFragment();
          parts.forEach(function (p) {
            if (p.trim() === '') { frag.appendChild(document.createTextNode(p)); return; }
            var span = document.createElement('span');
            span.className = 'word';
            if (!reduce) span.style.setProperty('--word-delay', (base + counter * wordStep).toFixed(2) + 's');
            counter++;
            span.textContent = p;
            frag.appendChild(span);
          });
          node.replaceChild(frag, child);
        } else if (child.nodeType === Node.ELEMENT_NODE) {
          splitNode(child);
        }
      });
    })(el);
  });

  // ── Scroll reveal ──
  // The .rise class is added here only, so no-JS and reduced-motion visitors keep
  // content in its final, visible state.
  if (reduce || !('IntersectionObserver' in window)) return;
  var beat = cssSeconds('--stagger-beat', 0.1) * 1000; // ms

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      var el = entry.target;
      el.classList.add('in');
      io.unobserve(el);
      // Once the entrance settles, strip the reveal classes. The .rise animation
      // fills forwards on transform; leaving it on would pin transform and block
      // the element's own snappy hover/press lift (--t-deliver). The final visual
      // state equals the base state, so removal is seamless.
      el.addEventListener('animationend', function handler(e) {
        if (e.target !== el) return;
        el.classList.remove('rise', 'in');
        el.removeEventListener('animationend', handler);
      });
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });

  // Parse data-reveal="child: <selector>; cap: <n>" on each annotated container.
  function parseSpec(raw) {
    var spec = { child: ':scope > *', cap: 5 };
    (raw || '').split(';').forEach(function (part) {
      var i = part.indexOf(':');
      if (i === -1) return;
      var key = part.slice(0, i).trim();
      var val = part.slice(i + 1).trim();
      if (key === 'child') spec.child = val;
      else if (key === 'cap') { var n = parseInt(val, 10); if (!isNaN(n)) spec.cap = n; }
    });
    return spec;
  }

  document.querySelectorAll('[data-reveal]').forEach(function (container) {
    var spec = parseSpec(container.getAttribute('data-reveal'));
    container.querySelectorAll(spec.child).forEach(function (el, i) {
      el.classList.add('rise');
      el.style.setProperty('--rise-delay', Math.min(i, spec.cap) * beat + 'ms');
      io.observe(el);
    });
  });
})();
