# FANTASY‑8 — Change‑Log Middleware & Viewer

> **Goal:** Capture every mutating request (add/drop, draft picks, etc.) and record a diff so users can view a timeline of actions for fun and traceability.

---

## 1  Context

Because the league is small and trusted, we need only lightweight audit logging. A custom FastAPI middleware can diff DB rows pre‑ and post‑request and write JSONPatch to `transaction_log`.

---

## 2  Sub‑Tasks

| Key                         | Title                                                          | What / Why                                                                                                            | Acceptance Criteria |
| --------------------------- | -------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | ------------------- |
| **8‑A Middleware Skeleton** | Add middleware `ChangeLogMiddleware` registered in `main.py`   | Only triggers on POST/PUT/DELETE; logging disabled for GET; unit test verifies skip on GET. citeturn0link1         |                     |
| **8‑B Diff Utility**        | Serialize before & after SQLModel instances, compute JSONPatch | Stored in `transaction_log` table with `user_id`, `path`, `method`, `patch`. Idempotent for repeated identical calls. |                     |
| **8‑C Viewer Endpoint**     | `GET /api/v1/logs?limit=100&offset=0` (admin‑only)             | Returns paginated list; requires user flag `is_admin`; 403 otherwise. UI endpoint formatted for frontend table.       |                     |
