# AI collaboration

Cursor was the only AI tool used on this assessment. It drafted plans and code from a scope I set one commit at a time. I approved each plan before files were written, and I kept Redis, a database, authentication, and extra frameworks out of the build.

Cursor was an assistant. I decided the scoring rules, the boundary between the quiz service and the WebSocket handler, and what was in or out of each commit. Drafts were checked with the API, the browser, and the test suites before I accepted them. A first draft was corrected when that check failed. Those corrections are listed below.

The private working notes used while building stayed outside this repository. This file is the submission record.

## Design

### Task

I asked for an architecture that a reviewer can follow in one sitting: a Vue client, a FastAPI process, live leaderboards, and in-memory sessions. I asked for the production shape to be written down, not built.

### Suggestion

Cursor proposed a quiz service that owns join, scoring, and the leaderboard, with REST and WebSocket code only translating messages. Sessions would be a locked dictionary. Socket rooms would be a second in-memory map. Redis Pub/Sub and a database were described as the step that allows more than one API process.

### Review

I accepted that split. I did not accept a separate scoring service, a message bus, or a persistence layer in this repository. The leaderboard had to be derived from the session, in one order: score, then name, then participant id.

### What changed

The service, the store, the routes, and the socket handler were written as separate modules after that plan. `docs/system-design.md` labels Redis, Pub/Sub, and a database as later work.

### Verification

The REST flow was exercised by hand: create, join, hidden answers, a correct score, a duplicate that does not change the score, and two quizzes that do not share participants. The design document was checked against those modules so it does not describe components that are not in the code.

## WebSocket implementation

### Task

I asked for live updates on top of the existing service. The socket handler was not allowed to reimplement scoring. Several people could share a quiz, and another quiz had to stay isolated.

### Suggestion

Cursor added a connection manager and a WebSocket route. On connect the server sends `connected` and the current board. On `submit_answer` it calls `QuizService.submit_answer`, then broadcasts `leaderboard` to that quiz only.

### Review

I kept the first-answer rule in the service. A duplicate is an error to that client and does not broadcast. One failed send must drop only that socket.

### What changed

While checking the endpoint, plain Uvicorn returned 404 on the upgrade and reported that no WebSocket library was installed. `websockets` was added. The larger `uvicorn[standard]` extra was not, because it pulls in packages this demo does not need.

### Verification

Two simulated clients joined one quiz. One answer updated both leaderboards. A client in a second quiz received nothing. Closing one client did not stop the other from receiving the next board. Unknown quizzes and unknown participants received an error and the socket closed.

## Browser client and a refresh bug

### Task

I asked for a Vue screen that joins with a quiz ID and a name, shows one question, submits over the existing socket, and replaces the leaderboard when a `leaderboard` message arrives.

### Suggestion

Cursor added the four components and `useQuizSocket`. The Vite dev server proxies `/quizzes` and `/ws` to the API, so the backend did not gain a CORS change. The page creates a quiz through the existing `POST /quizzes` so two windows can share an id.

### Review

I wanted the server order kept on the leaderboard, submit disabled unless the socket is open, and a reconnect that uses the same participant.

### What changed

The first refresh check failed. The page reconnected the same person but jumped back to question 1, because the question list was empty at restore time and the index was reset. The current question index is now stored with the session, and a restore keeps that index when the question list arrives.

On this machine the Vite server first listened only on IPv6 localhost. It is bound to `127.0.0.1` so `http://127.0.0.1:5173` connects.

### Verification

In two browser tabs, Ada created and joined a quiz and Grace joined the same id. Ada's correct answer showed Ada 1 and Grace 0 on both boards. After Ada moved to question 2, a refresh still showed question 2, score 1, and one leaderboard row. Leave returned to the join form. An unknown quiz id showed "Quiz was not found".

## Reliability pass

### Task

I asked for safer errors, logging, and refresh behavior. I did not ask for new infrastructure.

### Suggestion

Cursor proposed structured socket errors, logs for connect, score, disconnect, and dropped sockets, and a saved browser session.

### Review

I left the scoring rules alone. I did not want a new endpoint for previous answers, and I did not want finished quiz locks deleted, because removing a lock during a new connection can apply two answers at once.

### What changed

The page clears the saved session when the quiz or participant is gone. A payload that is not a known message shows "Received an unexpected update" and keeps the current board.

### Verification

A duplicate REST answer returned 409 with the question id, the original correctness, and the score. Server logs showed connect, answer scored, and disconnect for the same participant id. `python -m compileall` and the frontend production build succeeded.

## Tests

### Task

I asked for tests of scoring, quiz isolation, live broadcasts, and the main Vue path. I did not want the service mocked, and I did not want a test-only rewrite of the room lock.

### Suggestion

Cursor proposed pytest for REST, a real Uvicorn process for WebSocket clients, and Vitest for the join form, the socket composable, and the screen.

### Review

I accepted the real service. I rejected driving two WebSockets through FastAPI's `TestClient`: each of those sockets uses its own event loop, and the room lock is bound to the first loop. That is a limit of the test tool. The application runs on one loop under Uvicorn.

### What changed

The first pytest run failed before any test because this environment's `TestClient` imports `httpx2`. That package was added next to pytest. One `websockets` deprecation warning was removed by using `connect()` as a context manager.

### Verification

From `backend`, `python -m pytest` reported 17 passed. From `frontend`, `npm test` reported 8 passed. The overlapping REST test submits the same correct answer eight times and expects one success, seven conflicts, and a score of 1.

## Limits I kept in view

Cursor will follow a broad prompt into extra infrastructure. The commit scope was the control for that. Cursor also produced code that did not run on the first try: the missing WebSocket library, the IPv6-only dev server, the refresh index, and the `httpx2` import. Those were found by running the app and the tests, then fixed and run again. I did not treat a clean draft as correct until that check passed.
