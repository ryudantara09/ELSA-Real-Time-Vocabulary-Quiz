import json

from fastapi.testclient import TestClient
from websockets.exceptions import ConnectionClosed
from websockets.sync.client import connect


def _create_quiz(client: TestClient) -> str:
    return client.post("/quizzes").json()["quiz_id"]


def _join(client: TestClient, quiz_id: str, name: str) -> dict:
    return client.post(
        f"/quizzes/{quiz_id}/participants",
        json={"display_name": name},
    ).json()


def _url(port: int, quiz_id: str, user_id: str) -> str:
    return f"ws://127.0.0.1:{port}/ws/quizzes/{quiz_id}/participants/{user_id}"


def _recv(socket, timeout: float = 3):
    return json.loads(socket.recv(timeout=timeout))


def _scores(message: dict) -> dict[str, int]:
    return {row["display_name"]: row["score"] for row in message["leaderboard"]}


def test_participant_receives_questions_without_the_answer(client: TestClient, api_port: int):
    quiz_id = _create_quiz(client)
    ada = _join(client, quiz_id, "Ada")

    with connect(_url(api_port, quiz_id, ada["user_id"])) as ada_ws:
        connected = _recv(ada_ws)
        board = _recv(ada_ws)

    assert connected["type"] == "connected"
    assert connected["display_name"] == "Ada"
    assert connected["questions"][0]["question_id"] == "q1"
    assert "correct_choice" not in json.dumps(connected["questions"])
    assert _scores(board) == {"Ada": 0}


def test_answer_updates_every_participant_in_the_quiz(client: TestClient, api_port: int):
    quiz_id = _create_quiz(client)
    ada = _join(client, quiz_id, "Ada")
    grace = _join(client, quiz_id, "Grace")

    with (
        connect(_url(api_port, quiz_id, ada["user_id"])) as ada_ws,
        connect(_url(api_port, quiz_id, grace["user_id"])) as grace_ws,
    ):
        _recv(ada_ws)
        _recv(ada_ws)
        _recv(grace_ws)
        _recv(grace_ws)
        _recv(ada_ws)
        ada_ws.send(
            json.dumps(
                {"type": "submit_answer", "question_id": "q1", "choice": "ephemeral"}
            )
        )
        result = _recv(ada_ws)
        ada_board = _recv(ada_ws)
        grace_board = _recv(grace_ws)

    assert result == {
        "type": "answer_result",
        "question_id": "q1",
        "correct": True,
        "score": 1,
    }
    assert _scores(ada_board) == {"Ada": 1, "Grace": 0}
    assert _scores(grace_board) == {"Ada": 1, "Grace": 0}


def test_another_quiz_does_not_receive_the_update(client: TestClient, api_port: int):
    quiz_id = _create_quiz(client)
    other_id = _create_quiz(client)
    ada = _join(client, quiz_id, "Ada")
    sam = _join(client, other_id, "Sam")

    with (
        connect(_url(api_port, quiz_id, ada["user_id"])) as ada_ws,
        connect(_url(api_port, other_id, sam["user_id"])) as sam_ws,
    ):
        _recv(ada_ws)
        _recv(ada_ws)
        _recv(sam_ws)
        _recv(sam_ws)
        ada_ws.send(
            json.dumps(
                {"type": "submit_answer", "question_id": "q1", "choice": "ephemeral"}
            )
        )
        _recv(ada_ws)
        _recv(ada_ws)
        timed_out = False
        try:
            sam_ws.recv(timeout=0.4)
        except TimeoutError:
            timed_out = True

    assert timed_out


def test_invalid_message_keeps_the_socket_open(client: TestClient, api_port: int):
    quiz_id = _create_quiz(client)
    ada = _join(client, quiz_id, "Ada")

    with connect(_url(api_port, quiz_id, ada["user_id"])) as ada_ws:
        _recv(ada_ws)
        _recv(ada_ws)
        ada_ws.send("not-json")
        error = _recv(ada_ws)
        ada_ws.send(
            json.dumps(
                {"type": "submit_answer", "question_id": "q1", "choice": "ephemeral"}
            )
        )
        result = _recv(ada_ws)

    assert error["code"] == "invalid_message"
    assert result["correct"] is True
    assert result["score"] == 1


def test_duplicate_answer_is_not_broadcast(client: TestClient, api_port: int):
    quiz_id = _create_quiz(client)
    ada = _join(client, quiz_id, "Ada")
    grace = _join(client, quiz_id, "Grace")

    with (
        connect(_url(api_port, quiz_id, ada["user_id"])) as ada_ws,
        connect(_url(api_port, quiz_id, grace["user_id"])) as grace_ws,
    ):
        _recv(ada_ws)
        _recv(ada_ws)
        _recv(grace_ws)
        _recv(grace_ws)
        _recv(ada_ws)
        ada_ws.send(
            json.dumps(
                {"type": "submit_answer", "question_id": "q1", "choice": "ephemeral"}
            )
        )
        _recv(ada_ws)
        _recv(ada_ws)
        _recv(grace_ws)
        ada_ws.send(
            json.dumps(
                {"type": "submit_answer", "question_id": "q1", "choice": "permanent"}
            )
        )
        duplicate = _recv(ada_ws)
        timed_out = False
        try:
            grace_ws.recv(timeout=0.4)
        except TimeoutError:
            timed_out = True

    assert duplicate["code"] == "already_answered"
    assert duplicate["score"] == 1
    assert timed_out


def test_one_disconnect_does_not_stop_the_other_participant(client: TestClient, api_port: int):
    quiz_id = _create_quiz(client)
    ada = _join(client, quiz_id, "Ada")
    grace = _join(client, quiz_id, "Grace")

    with (
        connect(_url(api_port, quiz_id, ada["user_id"])) as ada_ws,
        connect(_url(api_port, quiz_id, grace["user_id"])) as grace_ws,
    ):
        _recv(ada_ws)
        _recv(ada_ws)
        _recv(grace_ws)
        _recv(grace_ws)
        _recv(ada_ws)
        grace_ws.close()
        ada_ws.send(
            json.dumps(
                {"type": "submit_answer", "question_id": "q2", "choice": "benevolent"}
            )
        )
        result = _recv(ada_ws)
        board = _recv(ada_ws)

    assert result["score"] == 1
    assert _scores(board)["Ada"] == 1


def test_unknown_quiz_returns_an_error(api_port: int):
    with connect(_url(api_port, "missing", "nobody")) as socket:
        error = _recv(socket)
        closed = False
        try:
            socket.recv(timeout=1)
        except ConnectionClosed:
            closed = True

    assert error["code"] == "quiz_not_found"
    assert closed
