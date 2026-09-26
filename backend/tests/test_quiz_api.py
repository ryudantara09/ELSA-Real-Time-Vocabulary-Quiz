import json
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient


def _create_quiz(client: TestClient) -> str:
    response = client.post("/quizzes")
    assert response.status_code == 200
    return response.json()["quiz_id"]


def _join(client: TestClient, quiz_id: str, name: str) -> dict:
    response = client.post(
        f"/quizzes/{quiz_id}/participants",
        json={"display_name": name},
    )
    assert response.status_code == 200
    return response.json()


def test_join_rejects_an_unknown_quiz(client: TestClient):
    response = client.post(
        "/quizzes/missing/participants",
        json={"display_name": "Ada"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Quiz 'missing' was not found"


def test_join_rejects_a_blank_name(client: TestClient):
    quiz_id = _create_quiz(client)

    response = client.post(
        f"/quizzes/{quiz_id}/participants",
        json={"display_name": "   "},
    )

    assert response.status_code == 422


def test_join_trims_the_name_and_starts_at_zero(client: TestClient):
    quiz_id = _create_quiz(client)

    participant = _join(client, quiz_id, "  Ada  ")

    assert participant["display_name"] == "Ada"
    assert participant["score"] == 0
    assert participant["user_id"]


def test_questions_hide_the_correct_choice(client: TestClient):
    quiz_id = _create_quiz(client)

    response = client.get(f"/quizzes/{quiz_id}/questions")

    assert response.status_code == 200
    questions = response.json()
    assert questions[0]["question_id"] == "q1"
    assert "ephemeral" in questions[0]["choices"]
    assert "correct_choice" not in json.dumps(questions)


def test_correct_and_incorrect_answers_score_independently(client: TestClient):
    quiz_id = _create_quiz(client)
    ada = _join(client, quiz_id, "Ada")
    grace = _join(client, quiz_id, "Grace")

    correct = client.post(
        f"/quizzes/{quiz_id}/answers",
        json={"user_id": ada["user_id"], "question_id": "q1", "choice": "ephemeral"},
    )
    wrong = client.post(
        f"/quizzes/{quiz_id}/answers",
        json={"user_id": grace["user_id"], "question_id": "q1", "choice": "permanent"},
    )
    second = client.post(
        f"/quizzes/{quiz_id}/answers",
        json={"user_id": ada["user_id"], "question_id": "q2", "choice": "benevolent"},
    )

    assert correct.json() == {"correct": True, "score": 1}
    assert wrong.json() == {"correct": False, "score": 0}
    assert second.json() == {"correct": True, "score": 2}


def test_duplicate_answer_keeps_the_first_score(client: TestClient):
    quiz_id = _create_quiz(client)
    ada = _join(client, quiz_id, "Ada")
    client.post(
        f"/quizzes/{quiz_id}/answers",
        json={"user_id": ada["user_id"], "question_id": "q1", "choice": "ephemeral"},
    )

    duplicate = client.post(
        f"/quizzes/{quiz_id}/answers",
        json={"user_id": ada["user_id"], "question_id": "q1", "choice": "permanent"},
    )

    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == {
        "message": "This question was already answered",
        "question_id": "q1",
        "correct": True,
        "score": 1,
        "already_answered": True,
    }


def test_invalid_answer_payloads_are_rejected(client: TestClient):
    quiz_id = _create_quiz(client)
    ada = _join(client, quiz_id, "Ada")

    missing_choice = client.post(
        f"/quizzes/{quiz_id}/answers",
        json={"user_id": ada["user_id"], "question_id": "q1"},
    )
    blank_choice = client.post(
        f"/quizzes/{quiz_id}/answers",
        json={"user_id": ada["user_id"], "question_id": "q1", "choice": "   "},
    )
    unknown_question = client.post(
        f"/quizzes/{quiz_id}/answers",
        json={"user_id": ada["user_id"], "question_id": "missing", "choice": "ephemeral"},
    )
    unknown_user = client.post(
        f"/quizzes/{quiz_id}/answers",
        json={"user_id": "nobody", "question_id": "q1", "choice": "ephemeral"},
    )
    bad_choice = client.post(
        f"/quizzes/{quiz_id}/answers",
        json={"user_id": ada["user_id"], "question_id": "q1", "choice": "nope"},
    )

    assert missing_choice.status_code == 422
    assert blank_choice.status_code == 422
    assert unknown_question.status_code == 404
    assert unknown_user.status_code == 404
    assert bad_choice.status_code == 422


def test_leaderboard_orders_by_score_then_name(client: TestClient):
    quiz_id = _create_quiz(client)
    grace = _join(client, quiz_id, "Grace")
    ada = _join(client, quiz_id, "Ada")
    bea = _join(client, quiz_id, "Bea")
    ace = _join(client, quiz_id, "ace")
    client.post(
        f"/quizzes/{quiz_id}/answers",
        json={"user_id": ada["user_id"], "question_id": "q1", "choice": "ephemeral"},
    )
    client.post(
        f"/quizzes/{quiz_id}/answers",
        json={"user_id": grace["user_id"], "question_id": "q1", "choice": "permanent"},
    )
    client.post(
        f"/quizzes/{quiz_id}/answers",
        json={"user_id": bea["user_id"], "question_id": "q1", "choice": "ancient"},
    )
    client.post(
        f"/quizzes/{quiz_id}/answers",
        json={"user_id": ace["user_id"], "question_id": "q1", "choice": "solid"},
    )

    names = [row["display_name"] for row in client.get(f"/quizzes/{quiz_id}/leaderboard").json()]

    assert names == ["Ada", "ace", "Bea", "Grace"]


def test_quizzes_do_not_share_participants(client: TestClient):
    first = _create_quiz(client)
    second = _create_quiz(client)
    ada = _join(client, first, "Ada")

    response = client.post(
        f"/quizzes/{second}/answers",
        json={"user_id": ada["user_id"], "question_id": "q1", "choice": "ephemeral"},
    )

    assert response.status_code == 404
    assert client.get(f"/quizzes/{second}/leaderboard").json() == []


def test_overlapping_answers_score_once(client: TestClient):
    quiz_id = _create_quiz(client)
    ada = _join(client, quiz_id, "Ada")

    def submit() -> int:
        response = client.post(
            f"/quizzes/{quiz_id}/answers",
            json={"user_id": ada["user_id"], "question_id": "q5", "choice": "resilient"},
        )
        return response.status_code

    with ThreadPoolExecutor(max_workers=8) as pool:
        codes = list(pool.map(lambda _: submit(), range(8)))

    assert codes.count(200) == 1
    assert codes.count(409) == 7
    board = client.get(f"/quizzes/{quiz_id}/leaderboard").json()
    assert board[0]["score"] == 1
