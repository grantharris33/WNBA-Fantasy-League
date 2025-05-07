Okay, let's rewrite Story-14.md to be more comprehensive, focusing on the required frontend functionality and its interaction with the existing backend.

---

# FANTASY‑14 — Draft Room UI & Real‑Time Experience

> **Goal:** Implement the frontend user interface for the live fantasy draft. This includes connecting to the backend WebSocket for real-time updates, displaying the draft state (current pick, timer, available players, draft log), allowing authenticated users to make picks for their teams when it's their turn, enabling users to queue players, and providing commissioners with controls to pause/resume the draft. Styling is secondary; the focus is on functional UI elements and interaction logic.
>
> **Backend Dependencies:** Relies heavily on **Story-9 (Draft API & Real‑Time Orchestration)** for API endpoints and WebSocket events, and **Story-10 (Roster Management)** for the free agent list endpoint. Assumes **Story-12 (Frontend Foundation)** is complete for auth context, API client, and basic routing.

---

## 1. Context & Overview

The draft is a core, time-sensitive event in the fantasy league. The backend (Story-9) provides the necessary state management, timing, pick validation, and WebSocket broadcasting. This story focuses *entirely on the frontend (`frontend/src/pages/DraftPage.tsx` and related components/hooks)* to consume the backend services and provide an interactive user experience.

Users will navigate to `/draft/:leagueId`. The frontend needs to:
1.  Authenticate the WebSocket connection using the user's JWT.
2.  Fetch the initial draft state (`GET /api/v1/draft/{draft_id}/state`).
3.  Fetch the list of available players (`GET /api/v1/leagues/{league_id}/free-agents`).
4.  Listen for WebSocket events (`pick_made`, `draft_paused`, `draft_resumed`, `draft_started`, `draft_completed`) to update the UI dynamically.
5.  Display the current pick, the team on the clock, and the remaining time.
6.  Allow the user whose turn it is to select an available player and submit their pick (`POST /api/v1/draft/{draft_id}/pick`).
7.  Provide visual feedback for draft actions (e.g., toast notifications).
8.  Show a running log of picks already made.
9.  Allow users to manage a personal "watch list" or "queue" of players (client-side state, potentially using `localStorage`).
10. Conditionally display pause/resume controls for the league commissioner.

---

## 2. UI/UX Functional Requirements (Styling Deferred)

*   **Main Draft Room Page (`DraftPage.tsx`):**
    *   Retrieves `leagueId` from URL parameters.
    *   Handles fetching initial draft state and available players on load.
    *   Manages WebSocket connection lifecycle.
    *   Coordinates updates between different UI panels based on fetched data and WebSocket events.
    *   Displays loading indicators and error messages appropriately.

*   **Draft Status Display:**
    *   Clearly show current **Round** and **Pick Number** (overall).
    *   Indicate the **Draft Status** (e.g., "Active", "Paused", "Completed").
    *   Display the **Team Name** currently on the clock.
    *   Show a **Countdown Timer** based on `seconds_remaining` from the draft state. Needs client-side interval logic, synced/reset by incoming state updates. Visual cue when time is low (e.g., < 10 seconds).

*   **Available Players Panel:**
    *   Fetches list using `GET /api/v1/leagues/{league_id}/free-agents`. Needs pagination or efficient loading for potentially many players.
    *   Displays a list/table of available players (Name, Position, Team).
    *   **Search/Filter:** Input field to filter players by name. Buttons/dropdowns to filter by position (G, F, C). Debounce search input to avoid excessive filtering on type.
    *   **Pick Action:** Button next to each player:
        *   Enabled *only* if it's the current user's team's turn and the draft is active.
        *   Triggers the pick submission process (e.g., opens confirmation modal).
    *   **Queue Action:** Button next to each player to add/remove from the user's personal queue.

*   **Pick Submission:**
    *   When the user clicks the "Pick" button for a player:
        *   (Optional but recommended) Show a confirmation modal ("Draft Player X?").
        *   On confirmation, call `POST /api/v1/draft/{draft_id}/pick` with the `player_id`.
        *   Handle API success: The WebSocket `pick_made` event should ideally trigger the primary UI update.
        *   Handle API errors: Display error message to the user (e.g., "Player already drafted", "Not your turn", "Draft paused").

*   **Draft Log Panel:**
    *   Displays a list of picks already made, usually fetched from the `picks` array in the `GET /api/v1/draft/{draft_id}/state` response and updated by `pick_made` WebSocket events.
    *   Show: Round, Pick #, Team Name, Player Name, Player Position.
    *   Order chronologically (latest pick first or last).

*   **My Team Panel / User's Roster:**
    *   Displays the players currently drafted by the logged-in user's team(s) in this league.
    *   Updates dynamically when the user makes a pick or when a pick for their team comes through the WebSocket.

*   **Player Queue Panel (Client-Side):**
    *   A separate panel where users can add players they are interested in.
    *   State managed locally (React state + optionally `localStorage` for persistence across refreshes).
    *   Allows adding/removing players.
    *   (Optional) Allow drag-and-drop reordering.
    *   (Optional) Button next to the top player in the queue to quickly initiate the pick process for that player.

*   **Commissioner Controls:**
    *   Buttons for "Pause Draft" and "Resume Draft".
    *   Visible *only* if the logged-in user is the commissioner of the league (requires checking `league.commissioner_id` against `user.id` - league details might need to be fetched separately or included in draft state).
    *   Clicking calls `POST /api/v1/draft/{draft_id}/pause` or `/resume` respectively.
    *   UI should reflect the "Paused" status when applicable (e.g., disable pick buttons, show banner).

*   **Notifications:**
    *   Use a simple toast notification library (or build basic ones) to announce:
        *   "Team X picked Player Y"
        *   "Draft Paused by Commissioner"
        *   "Draft Resumed"
        *   "Draft Completed"

*   **Responsiveness:**
    *   Ensure the layout adapts reasonably on smaller screens. A single-column layout stacking the panels might be necessary. Functionality remains the priority over perfect mobile styling for this story.

---

## 3. Backend Interaction Summary

*   **HTTP API Endpoints:**
    *   `GET /api/v1/draft/{draft_id}/state`: Fetch initial state and list of past picks.
    *   `GET /api/v1/leagues/{league_id}/free-agents`: Fetch list of available players (likely needs pagination params).
    *   `POST /api/v1/draft/{draft_id}/pick` (Body: `{ "player_id": int }`): Submit a pick.
    *   `POST /api/v1/draft/{draft_id}/pause`: Commissioner action.
    *   `POST /api/v1/draft/{draft_id}/resume`: Commissioner action.
    *   `GET /api/v1/leagues/{league_id}` (Potentially): To get league details like commissioner ID if not included elsewhere.
    *   `GET /api/v1/users/me/teams`: To identify the user's team(s) in the current league.
*   **WebSocket Endpoint:**
    *   `CONNECT /ws/draft/{league_id}?token={jwt_token}`: Establish connection.
    *   **Listen for Events:**
        *   `draft_started`: Contains initial draft state.
        *   `pick_made`: Contains the `pick` details and the `updated_draft` state. Use this to update the draft log, available players list, current pick info, timer, and potentially user rosters.
        *   `draft_paused`: Contains the updated draft state (`status: "paused"`). Update status display, disable pick controls.
        *   `draft_resumed`: Contains the updated draft state (`status: "active"`). Update status display, re-enable pick controls.
        *   `draft_completed`: Update status display.
        *   *(Note: Explicit clock tick events are not currently sent by the backend. Frontend syncs timer based on `seconds_remaining` in state updates).*

---

## 4. Frontend Component Breakdown (Potential Structure)

*   `pages/DraftPage.tsx`: Main container, fetches data, manages WebSocket hook, orchestrates state.
*   `hooks/useDraftWebSocket.ts`: Custom hook to manage WebSocket connection, authentication, message handling, and state updates.
*   `components/draft/DraftStatusBanner.tsx`: Displays round, pick #, team on clock, draft status.
*   `components/draft/DraftTimer.tsx`: Displays the countdown timer, handles client-side ticking logic, shows urgency state.
*   `components/draft/AvailablePlayersPanel.tsx`: Contains list, search, filter controls, player rows/cards.
    *   `components/draft/PlayerFilterControls.tsx`
    *   `components/draft/PlayerListItem.tsx`: Displays player info, Pick button, Add to Queue button.
*   `components/draft/DraftLogPanel.tsx`: Displays the history of picks.
*   `components/draft/MyTeamPanel.tsx`: Shows players drafted by the user's team.
*   `components/draft/PlayerQueuePanel.tsx`: Manages and displays the user's personal queue (client-side state).
*   `components/draft/CommissionerControls.tsx`: Conditional pause/resume buttons.
*   `components/common/ConfirmationModal.tsx`: Reusable modal for pick confirmation.
*   `components/common/ToastNotification.tsx`: Simple component for showing transient messages.

---

## 5. Sub-Tasks (Implementation Steps)

| Key       | Title                                                      | Description & Deliverables                                                                                                                                                                                                                                                         | Acceptance Criteria                                                                                                                                                                            |
| :-------- | :--------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **14-A**  | **WebSocket Hook (`useDraftWebSocket`)**                   | Create a custom hook to handle WebSocket connection (`/ws/draft/{league_id}?token=...`), message parsing (JSON), state updates (e.g., using `useState` or a state management library like Zustand/Redux), and cleanup on unmount. Exposes draft state and connection status.             | Hook connects successfully with token. Parses incoming JSON messages. Updates local state based on `pick_made`, `draft_paused`, etc. Handles connection errors/disconnects gracefully.     |
| **14-B**  | **Draft Page Structure & Initial State Fetch**             | Create `DraftPage.tsx`. On mount, fetch initial state (`GET /state`) and available players (`GET /free-agents`). Use `useDraftWebSocket` hook. Display loading states. Get user's team ID(s) for the league (`GET /users/me/teams`).                                                 | Page loads, displays loading state, then shows initial draft status (round, pick, team on clock) and list of available players based on API responses. User's team ID is identified.      |
| **14-C**  | **Draft Status & Timer Display**                           | Implement `DraftStatusBanner.tsx` and `DraftTimer.tsx`. Display data from fetched/WebSocket state. Timer component uses `setInterval` locally, reset by `seconds_remaining` from state updates.                                                                                   | Banner shows correct round, pick, status. Timer counts down accurately and resets when the state updates (e.g., after a pick).                                                              |
| **14-D**  | **Available Players List & Filtering**                     | Implement `AvailablePlayersPanel.tsx`. Display players from API. Add client-side name search (debounced) and position filtering functionality.                                                                                                                                   | Panel displays players. Search filters by name as user types. Position filters update the list. Pick/Queue buttons are present (functionality TBD). Handles pagination if API supports it. |
| **14-E**  | **Make Pick Functionality**                                | Implement pick confirmation modal and API call (`POST /pick`) triggered from `PlayerListItem.tsx`. Button enabled only for the correct user/team turn and active draft status. Update UI optimistically or wait for WebSocket confirmation. Handle API errors.                     | Correct user can click "Pick", confirm, and the API call is made. UI updates (available list shrinks, log updates) upon WS `pick_made` event. Errors are displayed.                       |
| **14-F**  | **Draft Log Display**                                      | Implement `DraftLogPanel.tsx`. Display `picks` array from initial state fetch. Append new picks received via `pick_made` WebSocket events.                                                                                                                                   | Panel shows historical picks correctly. New picks appear in the log in real-time.                                                                                                              |
| **14-G**  | **Player Queue (Client-Side)**                             | Implement `PlayerQueuePanel.tsx`. Use local state (`useState`) and `localStorage` to manage a list of player IDs. Add/remove buttons in `AvailablePlayersPanel.tsx` update this queue.                                                                                             | User can add/remove players to the queue. Queue persists across page reloads. (Drag-drop is optional stretch goal).                                                                       |
| **14-H**  | **My Team Display**                                        | Implement `MyTeamPanel.tsx`. Filter the draft log or roster slots (if available) to show players drafted by the current user's team(s) in this league. Updates when `pick_made` event involves user's team.                                                                    | Panel correctly displays players drafted by the logged-in user's team. Updates in real-time.                                                                                                   |
| **14-I**  | **Commissioner Controls**                                  | Implement `CommissionerControls.tsx`. Fetch league details if needed to check `commissioner_id`. Conditionally render Pause/Resume buttons. Buttons call `POST /pause` and `POST /resume` APIs.                                                                                | Buttons are visible only to commissioner. Clicking calls the correct API. UI updates (status banner, pick buttons disabled) based on WS `draft_paused`/`draft_resumed` events.         |
| **14-J**  | **Notifications**                                          | Integrate a simple toast notification system to display messages for key events (`pick_made`, `draft_paused`, `draft_resumed`, `draft_completed`).                                                                                                                               | User sees transient notifications when picks are made or draft status changes.                                                                                                                |
| **14-K**  | **Basic Responsiveness**                                   | Apply simple TailwindCSS responsive modifiers (`sm:`, `md:`, etc.) to stack panels or adjust layout on smaller screens. Ensure basic usability.                                                                                                                                | Layout adapts on smaller viewports without breaking or causing horizontal scroll. Functionality remains accessible.                                                                          |
| **14-L**  | **Basic Frontend Tests**                                   | Add basic component tests (e.g., using React Testing Library) for key components like `DraftTimer`, `PlayerFilterControls` to verify rendering and basic interactions. (Full E2E tests like Cypress are out of scope for this story unless specifically requested). | Unit/integration tests for selected components pass.                                                                                                                                          |

---

## 6. Considerations & Open Questions

*   **WebSocket Authentication:** Ensure the token is correctly passed as a query parameter and handled securely.
*   **Draft ID:** How does the frontend know the `draft_id`? It likely needs to be fetched based on the `league_id` or included in the league details. The backend currently uses `league_id` for the WebSocket connection but `draft_id` for API calls. This needs clarification/consistency or a lookup mechanism. The `GET /draft/{draft_id}/state` endpoint suggests `draft_id` is the primary key. Perhaps the `league` object should link to its `draft_state.id`. *Update:* The backend `DraftState` model has a `league_id` FK, so fetching the draft state by `league_id` first might be needed, or the initial `/leagues/{league_id}` endpoint could return the active `draft_id`.
*   **Error Handling:** Robustly handle API errors (invalid picks, auth issues) and WebSocket disconnection/reconnection attempts.
*   **Performance:** The available players list could be large. Consider virtualization or smarter loading strategies if performance becomes an issue. Filtering/searching should be performant.
*   **Auto-Pick Indication:** How is an auto-pick visually distinct in the draft log? The backend `DraftPick` has `is_auto`.
*   **State Management:** For complex state interactions (WebSocket updates, API fetches, local queue), consider a dedicated state management library if `useState` + Context becomes unwieldy.

---