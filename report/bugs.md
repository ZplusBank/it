# Bugs & Likely Issues (short)

- **No formal tests** — regressions are likely unnoticed.
- **Inconsistent JSON:** Multiple `chapters.json` files across folders; possible schema drift or missing fields.
- **Hardcoded paths:** Look for path assumptions in `editor.py`, `renderer.js`, and `sections.js` that break across environments.
- **Global state in JS:** Renderer/engine files may use globals; this can cause race conditions.
- **Error handling:** Many small projects omit robust try/catch and user-friendly error messages.

Recommended immediate actions:
- Run a schema validation pass across `data/**/chapters.json`.
- Add basic unit tests for `builder/editor.py` and JS functions.
- Run linters to catch obvious mistakes and enforce consistent style.
