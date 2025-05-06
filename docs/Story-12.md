# FANTASY‑12 — React + Vite Front‑End Scaffold

> **Goal:** Spin up a modern, minimal React codebase with Tailwind styling and a tiny API helper so UI stories can begin immediately.

---

## 1  Context

The front‑end will live in `frontend/` to keep Python and Node worlds separate. We’ll use Vite for blaze‑fast dev server, Tailwind for utility CSS, and a slim `api.ts` wrapper to talk to FastAPI with JWT handling.

---

## 2  Sub‑Tasks

| Key                      | Title                                                                                                                                          | What / Why                                                                                                                                               | Acceptance Criteria |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------- |
| **12‑A Create Vite App** | Run `npm create vite@latest fantasy-app -- --template react-ts` inside `frontend/`                                                             | `npm run dev` serves app at `http://localhost:5173` with default Vite splash.                                                                            |                     |
| **12‑B Tailwind Setup**  | Install Tailwind + postcss + autoprefixer; generate `tailwind.config.js`; add `@tailwind base; components; utilities;` to `index.css`          | `<button className="bg-blue-500 text-white p-2 rounded">Click</button>` renders styled button; inspected styles show Tailwind classes. citeturn0link1 |                     |
| **12‑C API Client**      | Create `src/lib/api.ts` with `fetchJSON(url, opts)` that attaches JWT from `localStorage` and retries once on 401 (calls refresh endpoint TBD) | Unit test with msw (Mock Service Worker) verifies Authorization header present and refresh retry path.                                                   |                     |
