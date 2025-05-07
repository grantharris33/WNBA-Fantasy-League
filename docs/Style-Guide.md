## WNBA Fantasy League - LLM Contributor Style Guide

**Core Philosophy:** Consistency, Clarity, Maintainability. When in doubt, adhere to the patterns established in the existing codebase.

### 1. General Principles

*   **Language:** Use Python 3.10+ for the backend and TypeScript for the frontend.
*   **Directory Structure:** Strictly adhere to the established directory structure (`app/`, `frontend/src/`, `tests/`, `scripts/`, etc.). Place new files in the logically appropriate directories (e.g., new API endpoints in `app/api/`, new services in `app/services/`).
*   **Tooling:**
    *   Use `poetry` for backend dependency management and running scripts (`poetry run ...`).
    *   Use `npm` for frontend dependency management and running scripts (`cd frontend && npm run ...`).
    *   Utilize the `Makefile` for common tasks (`make dev`, `make test`, `make lint`, `make format`).
    *   Ensure all code passes `pre-commit` checks before finalizing changes (`pre-commit run --all-files`).
*   **Configuration:** Use environment variables (`python-dotenv`) for configuration. Add new variables to `env.example`. Do not commit `.env` files.
*   **Git:** Use feature branches. Write clear, concise commit messages describing the change. Reference relevant User Story IDs (e.g., `FANTASY-XX: Implement feature Y`).
*   **Documentation:**
    *   Update relevant User Story markdown files (`docs/Story-X.md`) or architecture documents (`docs/Architecture.md`) when implementing features or making significant changes.
    *   Write clear docstrings for Python functions and classes (follow Google Style).
    *   Ensure FastAPI endpoints are auto-documented via OpenAPI (use clear descriptions in endpoint decorators and Pydantic schemas).

### 2. Python Backend (FastAPI)

*   **Framework Conventions:** Follow FastAPI best practices. Use `APIRouter` for organizing endpoints. Use `Depends()` for dependency injection (e.g., `get_db`, `get_current_user`).
*   **Typing:** Use Python type hints extensively and correctly for all function signatures, variables, and class attributes. Use types from the `typing` module (`List`, `Optional`, `Dict`, `Annotated`, etc.). Ensure `mypy` would pass (even if not explicitly in pre-commit yet).
*   **Async:** Use `async def` for all FastAPI path operation functions. Use `await` for asynchronous operations (e.g., external API calls using `httpx`, database operations if using an async driver - though current setup seems synchronous). Synchronous service functions called from async endpoints should be run in a thread pool if they are blocking (e.g., `await anyio.to_thread.run_sync(...)`).
*   **Services:** Encapsulate business logic within service classes in `app/services/`. Services should interact with the database session and models. Keep API endpoint functions thin, delegating logic to services.
*   **Models:** Define SQLAlchemy models in `app/models/__init__.py`. Use the declarative base (`app.core.database.Base`). Define relationships using `relationship` with `back_populates`. Define constraints (`UniqueConstraint`, `ForeignKeyConstraint`) within the model or `__table_args__`.
*   **Schemas (Pydantic):** Define API request/response schemas in `app/api/schemas.py` using Pydantic `BaseModel`. Use descriptive names ending in `Out` for responses, `In` or `Create`/`Update` for requests. Leverage `orm_mode = True` (or `model_config = {'from_attributes': True}` in Pydantic v2) for easy conversion from ORM models.
*   **Error Handling:** Raise `HTTPException` from API layers with appropriate status codes (400, 401, 403, 404, 409). Raise specific Python exceptions (e.g., `ValueError`, `PermissionError`) from service layers and handle/convert them in the API layer.
*   **Naming:**
    *   Modules, functions, variables: `snake_case`
    *   Classes: `PascalCase`
    *   Constants: `UPPER_SNAKE_CASE`
*   **Formatting & Linting:** Code *must* pass `ruff`, `black`, and `isort` checks (use `make format` and `make lint`).

### 3. Database (SQLAlchemy & Alembic)

*   **ORM:** Use SQLAlchemy ORM patterns as established in `app/models/`.
*   **Sessions:** Obtain DB sessions using the `get_db` dependency (`Depends(get_db)`). Ensure sessions are properly managed (closed/committed/rolled back) within the scope of a request or task. For background jobs, create a session explicitly (e.g., `db = SessionLocal()`) and ensure it's closed in a `finally` block.
*   **Migrations:** When changing SQLAlchemy models in `app/models/`, generate a new migration script using `poetry run alembic revision --autogenerate -m "Description of change"`. Review the generated script before committing. Apply migrations using `poetry run alembic upgrade head`.
*   **Querying:** Use ORM query methods (`db.query(...)`, `db.get(...)`). Use explicit `select()` statements for more complex queries where appropriate.
*   **Naming:**
    *   Tables: `snake_case` (e.g., `team_score`, `draft_pick`)
    *   Columns: `snake_case` (e.g., `league_id`, `moves_this_week`, `is_starter`)

### 4. Frontend (React + TypeScript + Vite)

*   **Framework:** Use React functional components with Hooks.
*   **Language:** Use TypeScript for all code. Define interfaces and types in `src/types/` (e.g., `src/types/User.ts`, `src/types/League.ts`), often mirroring backend Pydantic schemas.
*   **Structure:** Follow the established `src/` structure (`components`, `contexts`, `hooks`, `lib`, `pages`, `types`). Create subdirectories within `components` for specific features (e.g., `components/draft/`).
*   **Styling:** Use TailwindCSS utility classes for styling. Define minimal global styles in `src/index.css`.
*   **State Management:** Use React Context (`AuthContext`) for global state like authentication. For local component state, use `useState` and `useEffect`. If state becomes significantly more complex, discuss introducing a dedicated state management library (like Zustand or Redux Toolkit).
*   **API Interaction:** Use the central API client (`src/lib/api.ts` - *ensure this exists or is created as per Story-12*). This client should handle adding the base URL, setting `Authorization` headers using the token from `AuthContext` or `localStorage`, and basic JSON parsing/error handling.
*   **Routing:** Use `react-router-dom` for client-side routing as set up in `App.tsx`. Use the `ProtectedRoute` component for routes requiring authentication.
*   **Naming:**
    *   Components, Interfaces, Types: `PascalCase` (e.g., `DashboardPage`, `LeagueOut`)
    *   Functions, variables, hooks: `camelCase` (e.g., `fetchLeagues`, `useAuth`)
*   **Hooks:** Create custom hooks (`useMyHook`) for reusable logic (e.g., WebSocket handling, fetching specific data).
*   **Formatting & Linting:** Code *must* pass ESLint checks (`npm run lint` in `frontend/`). Follow the configured rules.

### 5. Testing (Pytest)

*   **Backend Tests:** Write tests using `pytest` in the `/tests` directory.
    *   Use fixtures (`@pytest.fixture`) for setting up test data (like `db`, `client`, `auth_client`, `setup_..._data`).
    *   Use FastAPI's `TestClient` for integration testing API endpoints.
    *   Mock external dependencies (like `httpx` calls or external services) using `unittest.mock.patch` or `pytest-httpx`.
    *   Use `freezegun` for testing time-dependent logic (scheduler jobs, token expiry).
    *   Test both success and failure paths, including validation errors and authorization checks.
    *   Aim for good test coverage.
*   **Frontend Tests:** (Based on planned Story-17)
    *   Use Jest and React Testing Library (`@testing-library/react`).
    *   Focus on testing component rendering, user interactions, and state changes.
    *   Mock API calls using `msw` (Mock Service Worker) or Jest's mocking capabilities.

---