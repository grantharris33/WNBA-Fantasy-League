# FANTASY‑15 — Dockerize Backend & Front‑End

> **Goal:** Provide reproducible container images for the FastAPI API, background worker, and React front‑end, plus a `docker‑compose.yml` for easy local or CI spin‑up.

---

## 1  Container Strategy

| Image        | Base                                       | Notes                                                                              |
| ------------ | ------------------------------------------ | ---------------------------------------------------------------------------------- |
| **api**      | python:3.12‑slim                           | Multi‑stage: builder installs Poetry deps, final copies virtualenv into slim image |
| **worker**   | Same as **api**                            | Runs Celery/APS jobs via separate command                                          |
| **frontend** | node:20‑alpine builder → nginx:1.27‑alpine | Copy `dist/` to `/usr/share/nginx/html`                                            |

Images tagged `wnba-fantasy-league/<service>:<git‑sha>` by CI.

---

## 2  Sub‑Tasks

| Key                          | Title                                                                            | What / Why                                                                                                                   | Acceptance Criteria |
| ---------------------------- | -------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ------------------- |
| **15‑A Backend Dockerfile**  | Create `ops/Dockerfile.api` multi‑stage                                          | `docker build -f ops/Dockerfile.api .` then `docker run -e PYTHONUNBUFFERED=1 api pytest -q` exits 0; image size < 150 MB.   |                     |
| **15‑B Frontend Dockerfile** | `ops/Dockerfile.frontend` builds Vite site then serves via nginx                 | `docker build -f ops/Dockerfile.frontend .` then `docker run -p 8080:80 image` serves React app at `http://localhost:8080/`. |                     |
| **15‑C docker‑compose.yml**  | Compose file defines **api**, **worker**, **frontend**, shared volume for dev db | `docker compose up --build` works on Apple Silicon and x86; healthcheck waiting ensures frontend depends\_on api ready.      |                     |
