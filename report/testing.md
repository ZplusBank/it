# Testing & Recommendations (short)

- **Unit tests:** Add `pytest` for Python (`builder/editor.py`) and `jest` for JS modules.
- **E2E tests:** Use Playwright or Cypress to cover critical flows (open chapter, render, navigate).
- **Automated CI:** Add GitHub Actions to run linters, tests, and basic security checks on PRs.
- **Linting & formatting:** Add `eslint` for JS, `flake8`/`black` for Python to enforce standards.
- **Quick setup:** Create `requirements.txt` and `package.json` to pin dependencies and allow reproducible CI.
