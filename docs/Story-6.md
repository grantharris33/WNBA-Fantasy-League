# FANTASY‑6 — Minimal User Authentication (JWT)

> **Goal:** Provide simple username + password login that returns a JWT bearer token so the API can protect private routes. Keeps friction low while maintaining basic security.

---

## 1  Context

Private league of 2–4 friends, but we still want hashed passwords and token‑based auth for later mobile clients. FastAPI’s built‑in OAuth2PasswordBearer + pyjwt fits our needs.

---

## 2  Sub‑Tasks

| Key                      | Title                                                                                        | What / Why                                                                                                                               | Acceptance Criteria |
| ------------------------ | -------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------- |
| **6‑A Password Hashing** | Configure `passlib[bcrypt]`; add `hash_password()` util                                      | Stored hash cannot be reversed by `bcrypt.checkpw(password, hash)` returning False for wrong pw in unit test.                            |                     |
| **6‑B Token Endpoint**   | Route `POST /api/v1/token` returns `{access_token, token_type}`                              | Implementation follows FastAPI docs example; token TTL = 30 days; integration test extracts token and decodes payload. |                     |
| **6‑C Dependency Guard** | Utility `get_current_user` verifies JWT signature & expiration                               | Hit protected dummy route without header ⇒ 401; with invalid token ⇒ 401; with valid token ⇒ 200.                                        |                     |
| **6‑D Login UI Hook**    | React auth context stores token in `localStorage`, attaches `Authorization: Bearer` on fetch | Manual QA: after login, user can navigate to protected standings page without 401; refresh preserves session.                            |                     |
