# FANTASY‑17 — Continuous Integration Pipeline & Quality Gates

> **Goal:** Ensure every pull request is automatically linted, tested, and built within 5 minutes using a split backend / frontend matrix on GitHub Actions.

---

## 1  Pipeline Overview

* Job **lint‑backend** → Ruff + Black‑check
* Job **test‑backend** → Pytest with coverage
* Job **lint‑frontend** → ESLint (future), TypeScript compile
* Job **test‑frontend** → Jest + React Testing Library snapshots
* **Docker build** jobs fan‑out after tests pass (see FANTASY‑15)

Jobs run in parallel with a `needs:` graph so total wall‑time stays under 5 minutes on `ubuntu‑latest` runners.

---

## 2  Sub‑Tasks

| Key                      | Title                                                                                                   | What / Why                                                                                     | Acceptance Criteria |
| ------------------------ | ------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ------------------- |
| **17‑A Pytest Coverage** | Add `--cov=app --cov-report=xml` to backend tests; fail if `<80%`                                       | Coverage gate in `pytest.ini` (`fail_under = 80`); CI job fails when dropping below threshold. |                     |
| **17‑B Ruff Lint**       | Include `ruff check .` in dedicated lint job                                                            | Baseline passes with 0 errors; future PRs show inline annotations.                             |                     |
| **17‑C Frontend Jest**   | Configure Jest + jsdom + `react-testing-library` snapshot tests for Scoreboard, DraftRoom, Roster pages | `npm test` completes in ≤90 s; 3 snapshots stored; job finishes under 5 min total CI run.      |                     |
| **17‑D Parallel Matrix** | Create `ci.yml` with separate backend / frontend jobs running in parallel                               | GH Actions run completes in ≤5 min for green build (verified by badge time).                   |                     |
