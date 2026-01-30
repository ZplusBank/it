# Performance Report (short)

- **Project snapshot:** Static site structure with many JSON data files, Python editor (`builder/editor.py`), JS renderer (`engine/renderer.js`). No build artifacts or bundler detected.
- **Likely bottlenecks:** Large JSON files loaded whole into browser; unminified CSS/JS; no caching or compression configured; synchronous tasks in Python editor may block; client-side rendering of large datasets.
- **How to measure:** Use Lighthouse, Chrome DevTools (network + performance), WebPageTest, `time` on Python scripts, and sample `console.time()` in JS.
- **Quick wins:**
  - Add HTTP compression (gzip/brotli) and cache headers.
  - Minify/concatenate CSS & JS; enable long-cache headers for static assets.
  - Lazy-load chapter JSONs; paginate or request only needed slices.
  - Serve static assets from a CDN for production.
- **Longer-term:** Introduce a build step to bundle and tree-shake JS, compress JSON to binary formats or index in a lightweight DB.
