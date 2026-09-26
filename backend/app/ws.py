import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.connections import connection_manager
from app.domain import (
    AnswerAlreadySubmitted,
    InvalidChoice,
    LeaderboardEntry,
    ParticipantNotFound,
    Question,
    QuestionNotFound,
    QuizError,
    QuizNotFound,
)
from app.schemas import SubmitAnswerMessage
from app.service import quiz_service

router = APIRouter()

_INVALID_MESSAGE = {
    "type": "error",
    "code": "invalid_message",
    "message": "Message must be a submit_answer object",
}


@router.websocket("/ws/quizzes/{quiz_id}/participants/{user_id}")
async def quiz_socket(websocket: WebSocket, quiz_id: str, user_id: str) -> None:
    await websocket.accept()
    try:
        participant = quiz_service.get_participant(quiz_id, user_id)
        questions = quiz_service.list_questions(quiz_id)
    except QuizError as exc:
        await websocket.send_json(_error_payload(exc))
        await websocket.close(code=1008)
        return

    await connection_manager.connect(quiz_id, user_id, websocket)
    try:
        async with connection_manager.room_lock(quiz_id):
            leaderboard = quiz_service.leaderboard(quiz_id)
            await websocket.send_json(
                {
                    "type": "connected",
                    "quiz_id": quiz_id,
                    "user_id": user_id,
                    "display_name": participant.display_name,
                    "questions": [_question_payload(question) for question in questions],
                    "leaderboard": [_leaderboard_row(entry) for entry in leaderboard],
                }
            )
            await connection_manager.broadcast(quiz_id, _leaderboard_message(leaderboard))

        while True:
            raw = await websocket.receive_text()
            await _handle_message(websocket, quiz_id, user_id, raw)
    except WebSocketDisconnect:
        return
    finally:
        await connection_manager.disconnect(quiz_id, user_id, websocket)


async def _handle_message(
    websocket: WebSocket,
    quiz_id: str,
    user_id: str,
    raw: str,
) -> None:
    try:
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("not an object")
        message = SubmitAnswerMessage.model_validate(payload)
    except (json.JSONDecodeError, ValueError, ValidationError):
        await websocket.send_json(_INVALID_MESSAGE)
        return

    async with connection_manager.room_lock(quiz_id):
        try:
            result = quiz_service.submit_answer(
                quiz_id,
                user_id,
                message.question_id,
                message.choice,
            )
        except QuizError as exc:
            await websocket.send_json(_error_payload(exc, message.question_id))
            return

        leaderboard = quiz_service.leaderboard(quiz_id)
        await websocket.send_json(
            {
                "type": "answer_result",
                "question_id": message.question_id,
                "correct": result.correct,
                "score": result.score,
            }
        )
        await connection_manager.broadcast(quiz_id, _leaderboard_message(leaderboard))


def _question_payload(question: Question) -> dict[str, object]:
    return {
        "question_id": question.question_id,
        "prompt": question.prompt,
        "choices": list(question.choices),
    }


def _leaderboard_row(entry: LeaderboardEntry) -> dict[str, object]:
    return {
        "rank": entry.rank,
        "user_id": entry.user_id,
        "display_name": entry.display_name,
        "score": entry.score,
    }


def _leaderboard_message(entries: list[LeaderboardEntry]) -> dict[str, object]:
    return {
        "type": "leaderboard",
        "leaderboard": [_leaderboard_row(entry) for entry in entries],
    }


def _error_payload(exc: QuizError, question_id: str | None = None) -> dict[str, object]:
    if isinstance(exc, QuizNotFound):
        return {
            "type": "error",
            "code": "quiz_not_found",
            "message": f"Quiz '{exc.quiz_id}' was not found",
        }
    if isinstance(exc, ParticipantNotFound):
        return {
            "type": "error",
            "code": "participant_not_found",
            "message": f"Participant '{exc.user_id}' was not found",
        }
    if isinstance(exc, QuestionNotFound):
        return {
            "type": "error",
            "code": "question_not_found",
            "message": f"Question '{exc.question_id}' was not found",
        }
    if isinstance(exc, InvalidChoice):
        return {
            "type": "error",
            "code": "invalid_choice",
            "message": f"'{exc.choice}' is not a valid choice",
        }
    if isinstance(exc, AnswerAlreadySubmitted):
        payload: dict[str, object] = {
            "type": "error",
            "code": "already_answered",
            "message": "This question was already answered",
            "correct": exc.correct,
            "score": exc.score,
        }
        if question_id is not None:
            payload["question_id"] = question_id
        return payload
    return {
        "type": "error",
        "code": "invalid_message",
        "message": "Quiz request failed",
    }
