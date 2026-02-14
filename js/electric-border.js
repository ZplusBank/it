/**
 * ElectricBorder — Vanilla JS animated neon border effect on hover
 * Faithful port of reactbits.dev/animations/electric-border
 * Performance: hover-only rAF, event delegation, lazy DOM, skip touch devices
 */
(function () {
  'use strict';

  // Skip on touch-only devices
  if (window.matchMedia('(hover: none)').matches) return;

  // =============================================
  // ✦ CONFIGURATION — edit these values to tweak
  // =============================================
  var COLOR = '#7560ddff';   // Border glow color
  var SPEED = 0.2;           // Animation speed multiplier
  var CHAOS = 0.14;         // Noise amplitude (wigglyness)
  var OCTAVES = 10;          // Noise detail layers
  var LACUNARITY = 1.6;         // Frequency multiplier per octave
  var GAIN = 0.7;         // Amplitude multiplier per octave
  var FREQUENCY = 10;          // Base noise frequency
  var BASE_FLATNESS = 0;          // First-octave damping (0 = none)
  var DISPLACEMENT = 60;          // Max pixel displacement from border
  var BORDER_OFFSET = 60;         // Canvas padding around element (px)

  // --- Noise functions (exact match to React source) ---
  function random(x) {
    return (Math.sin(x * 12.9898) * 43758.5453) % 1;
  }

  function noise2D(x, y) {
    var i = Math.floor(x);
    var j = Math.floor(y);
    var fx = x - i;
    var fy = y - j;

    var a = random(i + j * 57);
    var b = random(i + 1 + j * 57);
    var c = random(i + (j + 1) * 57);
    var d = random(i + 1 + (j + 1) * 57);

    var ux = fx * fx * (3.0 - 2.0 * fx);
    var uy = fy * fy * (3.0 - 2.0 * fy);

    return a * (1 - ux) * (1 - uy) + b * ux * (1 - uy) + c * (1 - ux) * uy + d * ux * uy;
  }

  function octavedNoise(x, octaves, lacunarity, gain, baseAmplitude, baseFrequency, time, seed, baseFlatness) {
    var y = 0;
    var amplitude = baseAmplitude;
    var frequency = baseFrequency;

    for (var i = 0; i < octaves; i++) {
      var octaveAmplitude = amplitude;
      if (i === 0) {
        octaveAmplitude *= baseFlatness;
      }
      y += octaveAmplitude * noise2D(frequency * x + seed * 100, time * frequency * 0.3);
      frequency *= lacunarity;
      amplitude *= gain;
    }

    return y;
  }

  // --- Rounded rect point (exact match to React source) ---
  function getCornerPoint(centerX, centerY, radius, startAngle, arcLength, progress) {
    var angle = startAngle + progress * arcLength;
    return {
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle)
    };
  }

  function getRoundedRectPoint(t, left, top, width, height, radius) {
    var straightWidth = width - 2 * radius;
    var straightHeight = height - 2 * radius;
    var cornerArc = (Math.PI * radius) / 2;
    var totalPerimeter = 2 * straightWidth + 2 * straightHeight + 4 * cornerArc;
    var distance = t * totalPerimeter;
    var accumulated = 0;
    var progress;

    // Top edge
    if (distance <= accumulated + straightWidth) {
      progress = (distance - accumulated) / straightWidth;
      return { x: left + radius + progress * straightWidth, y: top };
    }
    accumulated += straightWidth;

    // Top-right corner
    if (distance <= accumulated + cornerArc) {
      progress = (distance - accumulated) / cornerArc;
      return getCornerPoint(left + width - radius, top + radius, radius, -Math.PI / 2, Math.PI / 2, progress);
    }
    accumulated += cornerArc;

    // Right edge
    if (distance <= accumulated + straightHeight) {
      progress = (distance - accumulated) / straightHeight;
      return { x: left + width, y: top + radius + progress * straightHeight };
    }
    accumulated += straightHeight;

    // Bottom-right corner
    if (distance <= accumulated + cornerArc) {
      progress = (distance - accumulated) / cornerArc;
      return getCornerPoint(left + width - radius, top + height - radius, radius, 0, Math.PI / 2, progress);
    }
    accumulated += cornerArc;

    // Bottom edge
    if (distance <= accumulated + straightWidth) {
      progress = (distance - accumulated) / straightWidth;
      return { x: left + width - radius - progress * straightWidth, y: top + height };
    }
    accumulated += straightWidth;

    // Bottom-left corner
    if (distance <= accumulated + cornerArc) {
      progress = (distance - accumulated) / cornerArc;
      return getCornerPoint(left + radius, top + height - radius, radius, Math.PI / 2, Math.PI / 2, progress);
    }
    accumulated += cornerArc;

    // Left edge
    if (distance <= accumulated + straightHeight) {
      progress = (distance - accumulated) / straightHeight;
      return { x: left, y: top + height - radius - progress * straightHeight };
    }
    accumulated += straightHeight;

    // Top-left corner
    progress = (distance - accumulated) / cornerArc;
    return getCornerPoint(left + radius, top + radius, radius, Math.PI, Math.PI / 2, progress);
  }

  // --- Per-element state ---
  var activeElements = new WeakMap();

  function setupElement(el) {
    if (activeElements.has(el)) return;

    var rect = el.getBoundingClientRect();
    var cs = getComputedStyle(el);
    var rawRadius = parseFloat(cs.borderRadius) || 16;

    // Ensure positioned
    if (cs.position === 'static') {
      el.style.position = 'relative';
    }

    // Handle overflow
    var origOverflow = cs.overflow;
    if (origOverflow === 'hidden') {
      el.style.overflow = 'visible';
    }

    // Set color variable for CSS glow layers
    el.style.setProperty('--electric-border-color', COLOR);
    el.classList.add('electric-border');

    // Create glow layers (CSS-driven, matching React structure)
    var layers = document.createElement('div');
    layers.className = 'eb-layers';
    layers.innerHTML =
      '<div class="eb-glow-1"></div>' +
      '<div class="eb-glow-2"></div>' +
      '<div class="eb-background-glow"></div>';

    // Create canvas container (centered, extends beyond element)
    var canvasContainer = document.createElement('div');
    canvasContainer.className = 'eb-canvas-container';

    var canvas = document.createElement('canvas');
    canvas.className = 'eb-canvas';
    canvasContainer.appendChild(canvas);

    el.appendChild(layers);
    el.appendChild(canvasContainer);

    // Size canvas
    var elWidth = rect.width;
    var elHeight = rect.height;
    var canvasW = elWidth + BORDER_OFFSET * 2;
    var canvasH = elHeight + BORDER_OFFSET * 2;

    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = canvasW * dpr;
    canvas.height = canvasH * dpr;
    canvas.style.width = canvasW + 'px';
    canvas.style.height = canvasH + 'px';

    var ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);

    // Compute border geometry
    var borderWidth = elWidth;
    var borderHeight = elHeight;
    var maxRadius = Math.min(borderWidth, borderHeight) / 2;
    var radius = Math.min(rawRadius, maxRadius);
    var approxPerimeter = 2 * (borderWidth + borderHeight) + 2 * Math.PI * radius;
    var sampleCount = Math.floor(approxPerimeter / 2);

    var state = {
      canvasContainer: canvasContainer,
      canvas: canvas,
      ctx: ctx,
      layers: layers,
      canvasW: canvasW,
      canvasH: canvasH,
      borderWidth: borderWidth,
      borderHeight: borderHeight,
      radius: radius,
      sampleCount: sampleCount,
      dpr: dpr,
      timeVal: 0,
      lastFrameTime: 0,
      rafId: null,
      origOverflow: origOverflow
    };

    activeElements.set(el, state);

    // Animation loop (matching React's drawElectricBorder)
    function draw(currentTime) {
      var s = activeElements.get(el);
      if (!s) return;

      var deltaTime = s.lastFrameTime === 0 ? 0.016 : (currentTime - s.lastFrameTime) / 1000;
      s.timeVal += deltaTime * SPEED;
      s.lastFrameTime = currentTime;

      var c = s.ctx;
      c.setTransform(1, 0, 0, 1, 0, 0);
      c.clearRect(0, 0, s.canvas.width, s.canvas.height);
      c.scale(s.dpr, s.dpr);

      c.strokeStyle = COLOR;
      c.lineWidth = 1;
      c.lineCap = 'round';
      c.lineJoin = 'round';

      c.beginPath();

      for (var i = 0; i <= s.sampleCount; i++) {
        var progress = i / s.sampleCount;

        var point = getRoundedRectPoint(
          progress,
          BORDER_OFFSET,
          BORDER_OFFSET,
          s.borderWidth,
          s.borderHeight,
          s.radius
        );

        var xNoise = octavedNoise(
          progress * 8, OCTAVES, LACUNARITY, GAIN,
          CHAOS, FREQUENCY, s.timeVal, 0, BASE_FLATNESS
        );

        var yNoise = octavedNoise(
          progress * 8, OCTAVES, LACUNARITY, GAIN,
          CHAOS, FREQUENCY, s.timeVal, 1, BASE_FLATNESS
        );

        var displacedX = point.x + xNoise * DISPLACEMENT;
        var displacedY = point.y + yNoise * DISPLACEMENT;

        if (i === 0) {
          c.moveTo(displacedX, displacedY);
        } else {
          c.lineTo(displacedX, displacedY);
        }
      }

      c.closePath();
      c.stroke();

      s.rafId = requestAnimationFrame(draw);
    }

    state.rafId = requestAnimationFrame(draw);
  }

  function teardownElement(el) {
    var state = activeElements.get(el);
    if (!state) return;

    if (state.rafId) cancelAnimationFrame(state.rafId);
    if (state.canvasContainer.parentNode === el) el.removeChild(state.canvasContainer);
    if (state.layers.parentNode === el) el.removeChild(state.layers);

    el.classList.remove('electric-border');
    el.style.removeProperty('--electric-border-color');

    if (state.origOverflow === 'hidden') {
      el.style.overflow = 'hidden';
    }

    activeElements.delete(el);
  }

  // --- Event delegation (IT project selectors) ---
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
