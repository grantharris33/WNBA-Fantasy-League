# FANTASY‑7 — Session Cookie Authentication Fallback

> **Goal:** Provide a cookie‑based auth option for users who prefer not to manage JWT tokens manually. Uses FastAPI‑Users cookie transport and adds CSRF protection.

---

**Status:** Skipped for MVP

## 1  Context

While JWTs cover API access, some browsers/extensions handle cookies more smoothly. We’ll support both strategies behind an environment variable toggle so devs can switch without code changes.

---

## 2  Sub‑Tasks

| Key                             | Title                                                                                  | What / Why                                                                                                                         | Acceptance Criteria                                           |
| ------------------------------- | -------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| **7‑A Enable Cookie Transport** | Integrate FastAPI‑Users cookie backend (`CookieTransport`)                             | Response sets `Set‑Cookie: access_token=...; HttpOnly; SameSite=Lax`; path `/`; integration test confirms flags. citeturn0link1 |                                                               |
| **7‑B Toggle Strategy**         | Read env var \`AUTH\_MODE=jwt                                                          | cookie\` at startup; wire appropriate auth backend                                                                                 | CI test runs twice with both modes; logs show chosen backend. |
| **7‑C CSRF Token**              | Implement double‑submit cookie pattern (`X-CSRF-Token` header must match cookie value) | Cypress e2e test submits POST with correct token ⇒ 200; wrong/missing ⇒ 403.                                                       |                                                               |
