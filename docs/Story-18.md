# FANTASY‑18 — Repository Bootstrap & Dev Tooling

> **Goal:** Establish a clean, opinionated Python 3.12 repo so any engineer can clone, run a single install command, and immediately lint, format, test, and launch the FastAPI dev server. Removes “works on my machine” friction and sets quality gates from day 1.

---

## 1  Story Acceptance Criteria

1. GitHub repository `WNBA-Fantasy-League` with `main` as default branch.
2. `poetry install` → `make dev` starts hot‑reload server at `http://localhost:8000/health` returning `{"status":"ok"}`.
3. `pre‑commit run --all-files` passes on a fresh clone.
4. GitHub Actions CI runs **black --check**, **ruff**, **pytest**; status reported to PRs.
5. README contains one‑liner setup instructions for macOS, Linux, WSL.

---

## 2  Sub‑Tasks

| Key                  | Title                                 | Description & Deliverables                                                                                                                                   | Acceptance Criteria                             |
| -------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------- |
| **18‑A**             | Create Git repo & .gitignore          | Init remote repo, commit baseline, Python `.gitignore` & `.env` exclusion                                                                                    | Clean git status after initial commit.          |
| **18‑B**             | Add Poetry project config             | `poetry init -n --name wnba-fantasy-league --python ^3.12` + deps (fastapi, uvicorn\[standard]); dev‑deps (ruff, black, isort, pytest, pytest‑asyncio, pre‑commit) | `poetry check` passes; `poetry.lock` committed. |
| **18‑C**             | Configure tooling in `pyproject.toml` | Add `[tool.black]`, `[tool.ruff]`, `[tool.isort]`, `[tool.pytest.ini_options]` (line‑length 88, skip‑magic‑trailing‑comma)                                   | `black --check .` & `ruff .` exit 0.            |
| **18‑D**             | Pre‑commit hooks                      | `.pre‑commit-config.yaml` runs ruff‑format → black → isort → ruff → pytest‑short                                                                             | `pre‑commit run --all-files` passes.            |
| **18‑E**             | FastAPI Hello World                   | `app/main.py` creates app with `/health` route; `uvicorn app.main:app --reload` works                                                                        | Curl returns JSON OK.                           |
| **18‑F**             | Makefile & task aliases               | Targets: `dev`, `test`, `lint`, `format`                                                                                                                     | Each target executes without error.             |
| **18‑G**             | GitHub Actions CI                     | Workflow matrix (ubuntu‑latest, macos‑latest): setup‑python, cache Poetry, run `make lint test`                                                              | Passing badge visible in README.                |
| **18‑H**             | EditorConfig & IDE hints              | `.editorconfig`; `.vscode/settings.json` for Pylance paths, formatting on save                                                                               | Mis‑formatted file triggers lint error.         |
| **18‑I**             | Sample test suite                     | `tests/test_health.py` using FastAPI TestClient                                                                                                              | `pytest` collects ≥1 test and passes.           |
| **18‑J**             | Docs: README + CONTRIBUTING           | README with purpose, quick‑start, badges; CONTRIBUTING with style & pre‑commit guide                                                                         | Docs render; new dev up in <5 min.              |
| **18‑K**             | Code of Conduct                       | Contributor Covenant v2.1 in `.github/`                                                                                                                      | File present.                                   |
| **18**\*\*‑\*\***L** | License                               | MIT license with current year                                                                                                                                | `LICENSE` committed.                            |
| **18‑M**             | First tag & release draft             | GitHub release `v0.0.1-init` summarizing tooling                                                                                                             | Tag visible; draft notes posted.                |
