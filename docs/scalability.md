# Scalability notes

The quiz runs in one API process. Session scores and WebSocket rooms live in memory. That is enough for this assessment and for a demo with several people in a few quizzes.

## What the current process already does

- Each quiz is stored and broadcast on its own. An update in one quiz is not sent to another.
- Two answers for the same quiz are applied one at a time, so a score cannot be counted twice.
- A closed socket is removed from its room. The other participants still receive the leaderboard.
- A browser refresh reconnects as the same participant. Joining again is a different person.

## What a later production version would add

- A shared store such as Redis, so more than one API process sees the same scores.
- Redis Pub/Sub, or a similar bus, so each process keeps its own sockets and forwards a leaderboard published for that quiz ID.
- A database when quizzes must survive a process restart. Today a restart clears sessions, and the page asks the user to join again.
- Authentication when a participant ID must not be reusable by anyone who can see it.

Room locks for finished quizzes are left in memory. Each lock is small, and removing it while a new connection is starting can let two answers run at once. A shared store would replace this process-local lock.
