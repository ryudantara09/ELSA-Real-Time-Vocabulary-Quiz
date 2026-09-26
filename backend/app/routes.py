from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.domain import (
    AnswerAlreadySubmitted,
    InvalidChoice,
    ParticipantNotFound,
    QuestionNotFound,
    QuizError,
    QuizNotFound,
)
from app.schemas import (
    CreateQuizResponse,
    JoinQuizRequest,
    LeaderboardEntryResponse,
    ParticipantResponse,
    QuestionResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)
from app.service import quiz_service

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


@router.post("", response_model=CreateQuizResponse)
def create_quiz() -> CreateQuizResponse:
    return CreateQuizResponse(quiz_id=quiz_service.create_quiz())


@router.post("/{quiz_id}/participants", response_model=ParticipantResponse)
def join_quiz(quiz_id: str, body: JoinQuizRequest) -> ParticipantResponse:
    participant = quiz_service.join_quiz(quiz_id, body.display_name)
    return ParticipantResponse(
        user_id=participant.user_id,
        display_name=participant.display_name,
        score=participant.score,
    )


@router.get("/{quiz_id}/questions", response_model=list[QuestionResponse])
def list_questions(quiz_id: str) -> list[QuestionResponse]:
    questions = quiz_service.list_questions(quiz_id)
    return [
        QuestionResponse(
            question_id=question.question_id,
            prompt=question.prompt,
            choices=list(question.choices),
        )
        for question in questions
    ]


@router.post("/{quiz_id}/answers", response_model=SubmitAnswerResponse)
def submit_answer(quiz_id: str, body: SubmitAnswerRequest) -> SubmitAnswerResponse:
    try:
        result = quiz_service.submit_answer(
            quiz_id,
            body.user_id,
            body.question_id,
            body.choice,
        )
    except AnswerAlreadySubmitted as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "This question was already answered",
                "question_id": body.question_id,
                "correct": exc.correct,
                "score": exc.score,
                "already_answered": True,
            },
        ) from exc
    return SubmitAnswerResponse(correct=result.correct, score=result.score)


@router.get("/{quiz_id}/leaderboard", response_model=list[LeaderboardEntryResponse])
def leaderboard(quiz_id: str) -> list[LeaderboardEntryResponse]:
    return [
        LeaderboardEntryResponse(
            rank=entry.rank,
            user_id=entry.user_id,
            display_name=entry.display_name,
            score=entry.score,
        )
        for entry in quiz_service.leaderboard(quiz_id)
    ]


def register_quiz_errors(app: FastAPI) -> None:
    @app.exception_handler(QuizError)
    async def handle_quiz_error(_request: Request, exc: QuizError) -> JSONResponse:
        if isinstance(exc, QuizNotFound):
            return JSONResponse(
                status_code=404,
                content={"detail": f"Quiz '{exc.quiz_id}' was not found"},
            )
        if isinstance(exc, ParticipantNotFound):
            return JSONResponse(
                status_code=404,
                content={"detail": f"Participant '{exc.user_id}' was not found"},
            )
        if isinstance(exc, QuestionNotFound):
            return JSONResponse(
                status_code=404,
                content={"detail": f"Question '{exc.question_id}' was not found"},
            )
        if isinstance(exc, InvalidChoice):
            return JSONResponse(
                status_code=422,
                content={"detail": f"'{exc.choice}' is not a valid choice"},
            )
        if isinstance(exc, AnswerAlreadySubmitted):
            return JSONResponse(
                status_code=409,
                content={
                    "detail": {
                        "message": "This question was already answered",
                        "correct": exc.correct,
                        "score": exc.score,
                        "already_answered": True,
                    }
                },
            )
        return JSONResponse(status_code=500, content={"detail": "Quiz request failed"})
