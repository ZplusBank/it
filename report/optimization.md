# Optimization / How to Make It Fast (short)

- **Serve efficiently:** Use compression (gzip/brotli), set `Cache-Control`, and enable CDN for large/static assets.
- **Payload reduction:** Minify CSS/JS, remove unused code, compress/trim JSON, and convert large images to modern formats (WebP/AVIF).
- **Runtime improvements:** Defer non-critical JS, use code-splitting, and lazy-load chapter data only when requested.
- **Backend & tooling:** Introduce a build step (Rollup/Webpack/Vite) and consider pre-rendering heavy pages.
- **Data handling:** Replace monolithic JSON loads with paged APIs or an indexed search (e.g., small DB or indexed JSON files).
