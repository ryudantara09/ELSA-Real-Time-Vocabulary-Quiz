from collections.abc import Iterator
from contextlib import contextmanager
from threading import Lock

from app.domain import QuizSession


class InMemoryQuizStore:
    """Process-local sessions keyed by quiz_id.

    Session reads and writes go through `locked` so scoring stays consistent.
    A later store can replace this class without changing the service rules.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, QuizSession] = {}
        self._lock = Lock()

    @contextmanager
    def locked(self) -> Iterator[dict[str, QuizSession]]:
        with self._lock:
            yield self._sessions
