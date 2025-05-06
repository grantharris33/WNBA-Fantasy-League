# FANTASY‑14 — Draft Room UI & Real‑Time Experience

> **Goal:** Deliver a polished in‑browser draft room where 2–4 managers can make picks in real‑time, watch the countdown, queue players, and (for the commissioner) pause or resume the timer.
>
> Back‑end events come from the WebSocket implemented in FANTASY‑9; this story focuses on the front‑end implementation plus the extra pause/resume API for admins.

---

## 1  UX Checklist

* **Left column:** Available players list with filter & position tags.
* **Center:** Current pick card with 60‑second countdown and auto‑pick warning.
* **Right column:** User’s roster + pick queue (drag‑drop reorder).
* Toast notifications for each pick.
* Responsive: one‑column stacked on <640 px widths.

---

## 2  Sub‑Tasks

| Key                                | Title                                                                     | What / Why                                                                               | Acceptance Criteria |
| ---------------------------------- | ------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | ------------------- |
| **14‑A WebSocket Setup**           | Connect to `/ws/draft/{league}` via `useDraftSocket` hook                 | On “PICK\_MADE” event, state updates within 250 ms locally; disconnect → auto‑reconnect. |                     |
| **14‑B Countdown Timer**           | `useCountdown(seconds)` hook tied to current pick                         | Displays mm\:ss; resets on new pick; at 0 launches auto‑pick animation.                  |                     |
| **14‑C Live Search List**          | `PlayerSearch` component filters by name or position with debounce 150 ms | Typing returns results in <50 ms local dev; 0 results shows empty‑state graphic.         |                     |
| **14‑D Pick Queue Drag‑Drop**      | Allow managers to queue players and drag to reorder                       | Uses `@dnd-kit/core`; unit test verifies order persists after reload via localStorage.   |                     |
| **14‑E Pick Confirmation Modal**   | Double‑confirm when selecting player; shows basic stats                   | Modal closes & emits `PICK` event WebSocket message.                                     |                     |
| **14‑F Pause/Resume API + Button** | Admin‑only button hits `POST /api/v1/draft/{id}/pause` or `/resume`       | Button hidden for non‑admins; WS event `STATUS_PAUSED` updates UI banner.                |                     |
| **14‑G Draft Status Banner**       | Show round, pick number, paused state, and whose turn                     | Banner sticky at top; updates via WS.                                                    |                     |
| **14‑H Mobile Responsive Styles**  | Collapse columns into accordion sections on mobile                        | Tested with Chrome DevTools; no horizontal scroll.                                       |                     |
| **14‑I E2E Cypress Flow**          | Simulate 2 browsers drafting 2 rounds                                     | Asserts countdown, pick propagation, pause/resume, and queue.                            |                     |
