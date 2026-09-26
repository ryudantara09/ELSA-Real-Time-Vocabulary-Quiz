import socket
import threading
import time

import pytest
import uvicorn
from fastapi.testclient import TestClient

from app.connections import connection_manager
from app.main import app
from app.service import quiz_service


class _Server(uvicorn.Server):
    def install_signal_handlers(self) -> None:
        return


def reset_quiz_state() -> None:
    with quiz_service._store.locked() as sessions:
        sessions.clear()
    connection_manager._rooms.clear()
    connection_manager._room_locks.clear()


@pytest.fixture(autouse=True)
def clean_state():
    reset_quiz_state()
    yield
    reset_quiz_state()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def api_port():
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()

    server = _Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.time() + 5
    while not server.started and time.time() < deadline:
        time.sleep(0.02)
    if not server.started:
        raise RuntimeError("test server did not start")

    yield port

    server.should_exit = True
    thread.join(timeout=5)
