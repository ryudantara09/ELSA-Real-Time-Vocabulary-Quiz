from uuid import uuid4

from app.domain import (
    AnswerAlreadySubmitted,
    AnswerRecord,
    AnswerResult,
    InvalidChoice,
    LeaderboardEntry,
    Participant,
    ParticipantNotFound,
    Question,
    QuestionNotFound,
    QuizNotFound,
    QuizSession,
)
from app.questions import mock_questions
from app.store import InMemoryQuizStore


class QuizService:
    def __init__(self, store: InMemoryQuizStore) -> None:
        self._store = store

    def create_quiz(self) -> str:
        questions = {question.question_id: question for question in mock_questions()}
        session = QuizSession(quiz_id=uuid4().hex, questions=questions)
        with self._store.locked() as sessions:
            sessions[session.quiz_id] = session
        return session.quiz_id

    def join_quiz(self, quiz_id: str, display_name: str) -> Participant:
        participant = Participant(user_id=uuid4().hex, display_name=display_name)
        with self._store.locked() as sessions:
            session = self._require_session(sessions, quiz_id)
            session.participants[participant.user_id] = participant
        return participant

    def list_questions(self, quiz_id: str) -> list[Question]:
        with self._store.locked() as sessions:
            session = self._require_session(sessions, quiz_id)
            return list(session.questions.values())

    def submit_answer(
        self,
        quiz_id: str,
        user_id: str,
        question_id: str,
        choice: str,
    ) -> AnswerResult:
        with self._store.locked() as sessions:
            session = self._require_session(sessions, quiz_id)
            participant = session.participants.get(user_id)
            if participant is None:
                raise ParticipantNotFound(user_id)

            question = session.questions.get(question_id)
            if question is None:
                raise QuestionNotFound(question_id)
            if choice not in question.choices:
                raise InvalidChoice(choice)

            # The first submission is final, so a retry cannot change the score.
            key = (user_id, question_id)
            existing = session.answers.get(key)
            if existing is not None:
                raise AnswerAlreadySubmitted(correct=existing.correct, score=participant.score)

            correct = choice == question.correct_choice
            session.answers[key] = AnswerRecord(
                question_id=question_id,
                choice=choice,
                correct=correct,
            )
            if correct:
                participant.score += 1
            return AnswerResult(correct=correct, score=participant.score)

    def leaderboard(self, quiz_id: str) -> list[LeaderboardEntry]:
        with self._store.locked() as sessions:
            session = self._require_session(sessions, quiz_id)
            ordered = sorted(
                session.participants.values(),
                key=lambda participant: (
                    -participant.score,
                    participant.display_name.casefold(),
                    participant.user_id,
                ),
            )
            return [
                LeaderboardEntry(
                    rank=index,
                    user_id=participant.user_id,
                    display_name=participant.display_name,
                    score=participant.score,
                )
                for index, participant in enumerate(ordered, start=1)
            ]

    def _require_session(
        self,
        sessions: dict[str, QuizSession],
        quiz_id: str,
    ) -> QuizSession:
        session = sessions.get(quiz_id)
        if session is None:
            raise QuizNotFound(quiz_id)
        return session


quiz_service = QuizService(InMemoryQuizStore())
