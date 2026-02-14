/**
 * ElectricBorder — Vanilla JS animated neon border effect on hover
 * Adapted from reactbits.dev/animations/electric-border (React component)
 * Performance-optimized: hover-only animation, event delegation, lazy canvas creation
 */
(function () {
  'use strict';

  // Skip on touch-only devices
  if (window.matchMedia('(hover: none)').matches) return;

  // --- Noise functions (procedural, no dependencies) ---
  function pseudoRandom(x, y) {
    const n = Math.sin(x * 12.9898 + y * 78.233) * 43758.5453;
    return n - Math.floor(n);
  }

  function noise2D(x, y) {
    const ix = Math.floor(x), iy = Math.floor(y);
    const fx = x - ix, fy = y - iy;
    const ux = fx * fx * (3 - 2 * fx), uy = fy * fy * (3 - 2 * fy);
    const a = pseudoRandom(ix, iy);
    const b = pseudoRandom(ix + 1, iy);
    const c = pseudoRandom(ix, iy + 1);
    const d = pseudoRandom(ix + 1, iy + 1);
    return a + (b - a) * ux + (c - a) * uy + (a - b - c + d) * ux * uy;
  }

  function fractalNoise(x, y, octaves) {
    let val = 0, amp = 0.5, freq = 1;
    for (let i = 0; i < octaves; i++) {
      val += noise2D(x * freq, y * freq) * amp;
      amp *= 0.5;
      freq *= 2;
    }
    return val;
  }

  // --- Rounded rect path sampling ---
  function roundedRectPerimeter(w, h, r) {
    return 2 * (w - 2 * r) + 2 * (h - 2 * r) + 2 * Math.PI * r;
  }

  function pointOnRoundedRect(w, h, r, t) {
    // t is 0..1 around the perimeter
    const p = roundedRectPerimeter(w, h, r);
    let d = ((t % 1) + 1) % 1 * p;

    const top = w - 2 * r;
    const right = h - 2 * r;
    const bottom = w - 2 * r;
    const left = h - 2 * r;
    const cornerLen = (Math.PI / 2) * r;

    // Top edge
    if (d < top) return { x: r + d, y: 0 };
    d -= top;
    // Top-right corner
    if (d < cornerLen) {
      const a = d / r;
      return { x: w - r + Math.sin(a) * r, y: r - Math.cos(a) * r };
    }
    d -= cornerLen;
    // Right edge
    if (d < right) return { x: w, y: r + d };
    d -= right;
    // Bottom-right corner
    if (d < cornerLen) {
      const a = d / r;
      return { x: w - r + Math.cos(a) * r, y: h - r + Math.sin(a) * r };
    }
    d -= cornerLen;
    // Bottom edge
    if (d < bottom) return { x: w - r - d, y: h };
    d -= bottom;
    // Bottom-left corner
    if (d < cornerLen) {
      const a = d / r;
      return { x: r - Math.sin(a) * r, y: h - r + Math.cos(a) * r };
    }
    d -= cornerLen;
    // Left edge
    if (d < left) return { x: 0, y: h - r - d };
    d -= left;
    // Top-left corner
    {
      const a = d / r;
      return { x: r - Math.cos(a) * r, y: r - Math.sin(a) * r };
    }
  }

  // --- Config ---
  var OCTAVES = 6;         // Reduced from 10 — still visually rich
  var SPEED = 0.012;
  var NOISE_SCALE = 0.08;
  var INTENSITY = 1.2;
  var LINE_WIDTH = 1.5;
  var PADDING = 4;         // px outside element boundary

  // --- Per-element state ---
  var activeElements = new WeakMap();

  function getColor() {
    // Read from CSS custom property for theme compatibility
    var root = getComputedStyle(document.documentElement);
    var primary = root.getPropertyValue('--primary').trim() ||
      root.getPropertyValue('--accent-color').trim() ||
      '#6366f1';
    return primary;
  }

  function hexToRgb(hex) {
    hex = hex.replace('#', '');
    if (hex.length === 3) hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
    return {
      r: parseInt(hex.slice(0, 2), 16),
      g: parseInt(hex.slice(2, 4), 16),
      b: parseInt(hex.slice(4, 6), 16)
    };
  }

  function setupElement(el) {
    if (activeElements.has(el)) return; // Already active

    var rect = el.getBoundingClientRect();
    var w = rect.width + PADDING * 2;
    var h = rect.height + PADDING * 2;

    // Get border-radius from computed styles
    var cs = getComputedStyle(el);
    var rawRadius = parseFloat(cs.borderRadius) || 0;
    var radius = Math.min(rawRadius + 2, Math.min(w, h) / 2);

    // Create canvas
    var canvas = document.createElement('canvas');
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.cssText =
      'position:absolute;pointer-events:none;z-index:1;' +
      'top:' + (-PADDING) + 'px;left:' + (-PADDING) + 'px;' +
      'width:' + w + 'px;height:' + h + 'px;';

    var ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);

    // Ensure parent is positioned
    if (cs.position === 'static') {
      el.style.position = 'relative';
    }

    // Handle overflow — need visible for border to show
    var origOverflow = cs.overflow;
    if (origOverflow === 'hidden') {
      el.style.overflow = 'visible';
    }

    el.appendChild(canvas);

    var perimeter = roundedRectPerimeter(w, h, radius);
    var sampleCount = Math.max(60, Math.round(perimeter / 3));

    var color = getColor();
    var rgb = hexToRgb(color);

    var state = {
      canvas: canvas,
      ctx: ctx,
      w: w,
      h: h,
      radius: radius,
      perimeter: perimeter,
      sampleCount: sampleCount,
      rgb: rgb,
      rafId: null,
      startTime: performance.now(),
      origOverflow: origOverflow
    };

    activeElements.set(el, state);

    // Start animation loop
    function draw() {
      var s = activeElements.get(el);
      if (!s) return;

      var elapsed = (performance.now() - s.startTime) * 0.001;
      var c = s.ctx;
      c.clearRect(0, 0, s.w, s.h);

      c.lineWidth = LINE_WIDTH;
      c.lineCap = 'round';
      c.lineJoin = 'round';

      // Build path
      c.beginPath();
      for (var i = 0; i <= s.sampleCount; i++) {
        var t = i / s.sampleCount;
        var pt = pointOnRoundedRect(s.w, s.h, s.radius, t);

        // Compute noise displacement
        var n = fractalNoise(t * s.perimeter * NOISE_SCALE, elapsed * SPEED * 100, OCTAVES);
        var displacement = (n - 0.5) * 2 * INTENSITY;

        // Normal direction (approximate)
        var tNext = (i + 1) / s.sampleCount;
        var ptNext = pointOnRoundedRect(s.w, s.h, s.radius, tNext);
        var dx = ptNext.x - pt.x;
        var dy = ptNext.y - pt.y;
        var len = Math.sqrt(dx * dx + dy * dy) || 1;
        var nx = -dy / len;
        var ny = dx / len;

        var px = pt.x + nx * displacement;
        var py = pt.y + ny * displacement;

        if (i === 0) c.moveTo(px, py);
        else c.lineTo(px, py);
      }
      c.closePath();

      // Glow layers (3 passes for glow effect)
      var r = s.rgb.r, g = s.rgb.g, b = s.rgb.b;

      c.shadowColor = 'rgba(' + r + ',' + g + ',' + b + ',0.6)';
      c.shadowBlur = 15;
      c.strokeStyle = 'rgba(' + r + ',' + g + ',' + b + ',0.25)';
      c.lineWidth = 4;
      c.stroke();

      c.shadowBlur = 8;
      c.strokeStyle = 'rgba(' + r + ',' + g + ',' + b + ',0.5)';
      c.lineWidth = 2;
      c.stroke();

      c.shadowBlur = 0;
      c.strokeStyle = 'rgba(' + r + ',' + g + ',' + b + ',0.9)';
      c.lineWidth = LINE_WIDTH;
      c.stroke();

      s.rafId = requestAnimationFrame(draw);
    }

    state.rafId = requestAnimationFrame(draw);
  }

  function teardownElement(el) {
    var state = activeElements.get(el);
    if (!state) return;

    if (state.rafId) cancelAnimationFrame(state.rafId);
    if (state.canvas.parentNode === el) el.removeChild(state.canvas);

    // Restore overflow
    if (state.origOverflow === 'hidden') {
      el.style.overflow = 'hidden';
    }

    activeElements.delete(el);
  }

  // --- Event delegation ---
  var SELECTORS = [
    '.subject-card',
    '.chapter-card',
    '.start-exam-btn',
    '.restart-btn',
    '.check-btn',
    '.submit-btn',
    '.logo-mark',
    '.back-home-btn'
  ].join(',');

  document.addEventListener('pointerenter', function (e) {
    var target = e.target.closest(SELECTORS);
    if (!target) return;
    setupElement(target);
  }, true);

  document.addEventListener('pointerleave', function (e) {
    var target = e.target.closest(SELECTORS);
    if (!target) return;
    teardownElement(target);
  }, true);
})();
