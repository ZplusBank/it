// Floating Lines Background — Vanilla JS (adapted from ReactBits)
// Uses Three.js + GLSL shaders for animated wave lines

(function () {
  const container = document.getElementById('floatingLinesBg');
  if (!container) return;

  // --- GLSL Shaders ---
  const vertexShader = `
precision highp float;
void main() {
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;

  const fragmentShader = `
precision highp float;

uniform float iTime;
uniform vec3  iResolution;
uniform float animationSpeed;

uniform bool enableTop;
uniform bool enableMiddle;
uniform bool enableBottom;

uniform int topLineCount;
uniform int middleLineCount;
uniform int bottomLineCount;

uniform float topLineDistance;
uniform float middleLineDistance;
uniform float bottomLineDistance;

uniform vec3 topWavePosition;
uniform vec3 middleWavePosition;
uniform vec3 bottomWavePosition;

uniform vec2 iMouse;
uniform bool interactive;
uniform float bendRadius;
uniform float bendStrength;
uniform float bendInfluence;

uniform bool parallax;
uniform float parallaxStrength;
uniform vec2 parallaxOffset;

uniform vec3 lineGradient[8];
uniform int lineGradientCount;

const vec3 BLACK = vec3(0.0);
const vec3 PINK  = vec3(233.0, 71.0, 245.0) / 255.0;
const vec3 BLUE  = vec3(47.0,  75.0, 162.0) / 255.0;

mat2 rotate(float r) {
  return mat2(cos(r), sin(r), -sin(r), cos(r));
}

vec3 background_color(vec2 uv) {
  vec3 col = vec3(0.0);
  float y = sin(uv.x - 0.2) * 0.3 - 0.1;
  float m = uv.y - y;
  col += mix(BLUE, BLACK, smoothstep(0.0, 1.0, abs(m)));
  col += mix(PINK, BLACK, smoothstep(0.0, 1.0, abs(m - 0.8)));
  return col * 0.5;
}

vec3 getLineColor(float t, vec3 baseColor) {
  if (lineGradientCount <= 0) { return baseColor; }
  vec3 gradientColor;
  if (lineGradientCount == 1) {
    gradientColor = lineGradient[0];
  } else {
    float clampedT = clamp(t, 0.0, 0.9999);
    float scaled = clampedT * float(lineGradientCount - 1);
    int idx = int(floor(scaled));
    float f = fract(scaled);
    int idx2 = min(idx + 1, lineGradientCount - 1);
    gradientColor = mix(lineGradient[idx], lineGradient[idx2], f);
  }
  return gradientColor * 0.5;
}

float wave(vec2 uv, float offset, vec2 screenUv, vec2 mouseUv, bool shouldBend) {
  float time = iTime * animationSpeed;
  float x_offset   = offset;
  float x_movement = time * 0.1;
  float amp        = sin(offset + time * 0.2) * 0.3;
  float y          = sin(uv.x + x_offset + x_movement) * amp;

  if (shouldBend) {
    vec2 d = screenUv - mouseUv;
    float influence = exp(-dot(d, d) * bendRadius);
    float bendOffset = (mouseUv.y - screenUv.y) * influence * bendStrength * bendInfluence;
    y += bendOffset;
  }

  float m = uv.y - y;
  return 0.0175 / max(abs(m) + 0.01, 1e-3) + 0.01;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
  vec2 baseUv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;
  baseUv.y *= -1.0;

  if (parallax) { baseUv += parallaxOffset; }

  vec3 col = vec3(0.0);
  vec3 b = lineGradientCount > 0 ? vec3(0.0) : background_color(baseUv);

  vec2 mouseUv = vec2(0.0);
  if (interactive) {
    mouseUv = (2.0 * iMouse - iResolution.xy) / iResolution.y;
    mouseUv.y *= -1.0;
  }

  if (enableBottom) {
    for (int i = 0; i < bottomLineCount; ++i) {
      float fi = float(i);
      float t = fi / max(float(bottomLineCount - 1), 1.0);
      vec3 lineCol = getLineColor(t, b);
      float angle = bottomWavePosition.z * log(length(baseUv) + 1.0);
      vec2 ruv = baseUv * rotate(angle);
      col += lineCol * wave(
        ruv + vec2(bottomLineDistance * fi + bottomWavePosition.x, bottomWavePosition.y),
        1.5 + 0.2 * fi, baseUv, mouseUv, interactive
      ) * 0.2;
    }
  }

  if (enableMiddle) {
    for (int i = 0; i < middleLineCount; ++i) {
      float fi = float(i);
      float t = fi / max(float(middleLineCount - 1), 1.0);
      vec3 lineCol = getLineColor(t, b);
      float angle = middleWavePosition.z * log(length(baseUv) + 1.0);
      vec2 ruv = baseUv * rotate(angle);
      col += lineCol * wave(
        ruv + vec2(middleLineDistance * fi + middleWavePosition.x, middleWavePosition.y),
        2.0 + 0.15 * fi, baseUv, mouseUv, interactive
      );
    }
  }

  if (enableTop) {
    for (int i = 0; i < topLineCount; ++i) {
      float fi = float(i);
      float t = fi / max(float(topLineCount - 1), 1.0);
      vec3 lineCol = getLineColor(t, b);
      float angle = topWavePosition.z * log(length(baseUv) + 1.0);
      vec2 ruv = baseUv * rotate(angle);
      ruv.x *= -1.0;
      col += lineCol * wave(
        ruv + vec2(topLineDistance * fi + topWavePosition.x, topWavePosition.y),
        1.0 + 0.2 * fi, baseUv, mouseUv, interactive
      ) * 0.1;
    }
  }

  fragColor = vec4(col, 1.0);
}

void main() {
  vec4 color = vec4(0.0);
  mainImage(color, gl_FragCoord.xy);
  gl_FragColor = color;
}
`;

  // --- Config ---
  const isMobile = window.innerWidth < 768;
  const config = {
    linesGradient: ['#3730a3', '#4338ca', '#5b21b6', '#6d28d9'],
    enabledWaves: ['top', 'middle', 'bottom'],
    lineCount: isMobile ? [3, 2, 3] : [6, 6, 6],
    lineDistance: [5, 5, 5],
    topWavePosition: { x: 10.0, y: 0.5, rotate: -0.4 },
    middleWavePosition: { x: 5.0, y: 0.0, rotate: 0.2 },
    bottomWavePosition: { x: 2.0, y: -0.7, rotate: -1.0 },
    animationSpeed: 1,
    interactive: !isMobile,
    bendRadius: 5.0,
    bendStrength: -0.5,
    mouseDamping: 0.05,
    parallax: !isMobile,
    parallaxStrength: 0.2
  };

  // --- Helpers ---
  function hexToVec3(hex) {
    let v = hex.replace('#', '');
    if (v.length === 3) v = v[0] + v[0] + v[1] + v[1] + v[2] + v[2];
    return new THREE.Vector3(
      parseInt(v.slice(0, 2), 16) / 255,
      parseInt(v.slice(2, 4), 16) / 255,
      parseInt(v.slice(4, 6), 16) / 255
    );
  }

  function getIdx(arr, wave, def) {
    if (typeof arr === 'number') return arr;
    const i = config.enabledWaves.indexOf(wave);
    return i >= 0 && i < arr.length ? arr[i] : def;
  }

  // --- Three.js Setup ---
  const scene = new THREE.Scene();
  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  camera.position.z = 1;

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.domElement.style.width = '100%';
  renderer.domElement.style.height = '100%';
  container.appendChild(renderer.domElement);

  // --- Uniforms ---
  const MAX_GRADIENT = 8;
  const gradientArr = Array.from({ length: MAX_GRADIENT }, () => new THREE.Vector3(1, 1, 1));
  let gradientCount = 0;

  if (config.linesGradient && config.linesGradient.length > 0) {
    const stops = config.linesGradient.slice(0, MAX_GRADIENT);
    gradientCount = stops.length;
    stops.forEach((hex, i) => {
      const c = hexToVec3(hex);
      gradientArr[i].set(c.x, c.y, c.z);
    });
  }

  const topLC = config.enabledWaves.includes('top') ? getIdx(config.lineCount, 'top', 6) : 0;
  const midLC = config.enabledWaves.includes('middle') ? getIdx(config.lineCount, 'middle', 6) : 0;
  const botLC = config.enabledWaves.includes('bottom') ? getIdx(config.lineCount, 'bottom', 6) : 0;

  const topLD = (config.enabledWaves.includes('top') ? getIdx(config.lineDistance, 'top', 5) : 0.1) * 0.01;
  const midLD = (config.enabledWaves.includes('middle') ? getIdx(config.lineDistance, 'middle', 5) : 0.1) * 0.01;
  const botLD = (config.enabledWaves.includes('bottom') ? getIdx(config.lineDistance, 'bottom', 5) : 0.1) * 0.01;

  const uniforms = {
    iTime: { value: 0 },
    iResolution: { value: new THREE.Vector3(1, 1, 1) },
    animationSpeed: { value: config.animationSpeed },

    enableTop: { value: config.enabledWaves.includes('top') },
    enableMiddle: { value: config.enabledWaves.includes('middle') },
    enableBottom: { value: config.enabledWaves.includes('bottom') },

    topLineCount: { value: topLC },
    middleLineCount: { value: midLC },
    bottomLineCount: { value: botLC },

    topLineDistance: { value: topLD },
    middleLineDistance: { value: midLD },
    bottomLineDistance: { value: botLD },

    topWavePosition: {
      value: new THREE.Vector3(config.topWavePosition.x, config.topWavePosition.y, config.topWavePosition.rotate)
    },
    middleWavePosition: {
      value: new THREE.Vector3(config.middleWavePosition.x, config.middleWavePosition.y, config.middleWavePosition.rotate)
    },
    bottomWavePosition: {
      value: new THREE.Vector3(config.bottomWavePosition.x, config.bottomWavePosition.y, config.bottomWavePosition.rotate)
    },

    iMouse: { value: new THREE.Vector2(-1000, -1000) },
    interactive: { value: config.interactive },
    bendRadius: { value: config.bendRadius },
    bendStrength: { value: config.bendStrength },
    bendInfluence: { value: 0 },

    parallax: { value: config.parallax },
    parallaxStrength: { value: config.parallaxStrength },
    parallaxOffset: { value: new THREE.Vector2(0, 0) },

    lineGradient: { value: gradientArr },
    lineGradientCount: { value: gradientCount }
  };

  const material = new THREE.ShaderMaterial({ uniforms, vertexShader, fragmentShader });
  const geometry = new THREE.PlaneGeometry(2, 2);
  const mesh = new THREE.Mesh(geometry, material);
  scene.add(mesh);

  // --- Resize Handler ---
  function setSize() {
    const w = container.clientWidth || 1;
    const h = container.clientHeight || 1;
    renderer.setSize(w, h, false);
    uniforms.iResolution.value.set(renderer.domElement.width, renderer.domElement.height, 1);

    // Update mobile state on resize
    const newIsMobile = window.innerWidth < 768;
    if (uniforms.interactive.value !== !newIsMobile) {
      // Update uniforms for mobile/desktop switch
      uniforms.interactive.value = !newIsMobile;
      uniforms.parallax.value = !newIsMobile;

      // Update line counts
      const newCounts = newIsMobile ? [3, 2, 3] : [6, 6, 6];
      uniforms.topLineCount.value = config.enabledWaves.includes('top') ? getIdx(newCounts, 'top', 6) : 0;
      uniforms.middleLineCount.value = config.enabledWaves.includes('middle') ? getIdx(newCounts, 'middle', 6) : 0;
      uniforms.bottomLineCount.value = config.enabledWaves.includes('bottom') ? getIdx(newCounts, 'bottom', 6) : 0;
    }
  }
  setSize();

  // (Resize observer moved to bottom to handle loop restart)

  // --- Mouse interactivity ---
  const targetMouse = new THREE.Vector2(-1000, -1000);
  const currentMouse = new THREE.Vector2(-1000, -1000);
  let targetInfluence = 0;
  let currentInfluence = 0;
  const targetParallax = new THREE.Vector2(0, 0);
  const currentParallax = new THREE.Vector2(0, 0);
  const damping = config.mouseDamping;

  document.addEventListener('pointermove', (e) => {
    const rect = renderer.domElement.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const dpr = renderer.getPixelRatio();
    targetMouse.set(x * dpr, (rect.height - y) * dpr);
    targetInfluence = 1.0;

    if (config.parallax) {
      const cx = rect.width / 2;
      const cy = rect.height / 2;
      targetParallax.set(
        ((x - cx) / rect.width) * config.parallaxStrength,
        -((y - cy) / rect.height) * config.parallaxStrength
      );
    }
  });

  document.addEventListener('pointerleave', () => {
    targetInfluence = 0.0;
  });

  // --- Render Loop ---
  const clock = new THREE.Clock();
  let animationId = null;

  function renderLoop() {
    // Mobile optimization: Render only once, then stop loop
    // But we still want to render at least one frame so the background appears
    if (window.innerWidth < 768) {
      renderer.render(scene, camera);
      return; // Stop the loop
    }

    uniforms.iTime.value = clock.getElapsedTime();

    currentMouse.lerp(targetMouse, damping);
    uniforms.iMouse.value.copy(currentMouse);
    currentInfluence += (targetInfluence - currentInfluence) * damping;
    uniforms.bendInfluence.value = currentInfluence;

    currentParallax.lerp(targetParallax, damping);
    uniforms.parallaxOffset.value.copy(currentParallax);

    renderer.render(scene, camera);
    animationId = requestAnimationFrame(renderLoop);
  }

  // Initial render
  renderLoop();

  // Resize logic to restart loop if moving from mobile -> desktop
  const originalSetSize = setSize;
  // We need to override or augment the setSize function or the resize listener
  // The original code defined setSize and added the listener. 
  // Let's modify how we handle the resize to ensure loop restarts if needed.

  // Re-attach our own resize listener that handles the loop restart
  function handleResize() {
    setSize(); // Call original sizing logic (which updates uniforms)

    const isNowMobile = window.innerWidth < 768;
    if (!isNowMobile && !animationId) {
      // Restart loop if we are now desktop and loop wasn't running
      clock.start();
      renderLoop();
    } else if (isNowMobile && animationId) {
      // Stop loop if we are now mobile (renderLoop will check condition and return, but we can also cancel here)
      cancelAnimationFrame(animationId);
      animationId = null;
      // Render one static frame for the new size
      renderer.render(scene, camera);
    } else if (isNowMobile) {
      // Just re-render static frame on resize
      renderer.render(scene, camera);
    }
  }

  // Remove the old listener if possible, or just overwrite the behavior.
  // Since we are inside the IIFE and 'setSize' is local, we can't easily remove the specific listener added before 
  // without cleaner code structure, but since we are REPLACING the bottom part of the file, we can just redefine the listener logic.

  // NOTE: The previous code block had `new ResizeObserver(setSize).observe(container)`. 
  // We should replace that part too if we want to be clean, but replacing just the renderLoop area is safer if we want to minimize diff.
  // However, to do this correctly, I should probably replace the ResizeObserver part too or just hook into `setSize`.

  // Let's look at the previous `setSize`... it was defined above this block.
  // I will just add the loop management to the `setSize` function if I could, but it is out of scope of this replace block.
  // Actually, I can just wrap the resize behavior here.

  if (typeof ResizeObserver !== 'undefined') {
    // Disconnect old one? We can't reach it. 
    // But we can just add our new logic. 
    // Actually, the previous code block ends with `renderLoop();`.
    // I will replace `renderLoop();` and the end of file with the new logic.

    // Let's attach the new resize handler that manages the loop.
    const resizeObserver = new ResizeObserver(() => {
      handleResize();
    });
    resizeObserver.observe(container);
  } else {
    window.addEventListener('resize', handleResize);
  }
})();
