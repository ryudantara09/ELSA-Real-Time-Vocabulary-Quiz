from dataclasses import dataclass, field


class QuizError(Exception):
    """Base error for quiz rules that routes translate into HTTP responses."""


class QuizNotFound(QuizError):
    def __init__(self, quiz_id: str) -> None:
        self.quiz_id = quiz_id
        super().__init__(f"Quiz '{quiz_id}' was not found")


class ParticipantNotFound(QuizError):
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        super().__init__(f"Participant '{user_id}' was not found")


class QuestionNotFound(QuizError):
    def __init__(self, question_id: str) -> None:
        self.question_id = question_id
        super().__init__(f"Question '{question_id}' was not found")


class InvalidChoice(QuizError):
    def __init__(self, choice: str) -> None:
        self.choice = choice
        super().__init__(f"'{choice}' is not a valid choice")


class AnswerAlreadySubmitted(QuizError):
    def __init__(self, *, correct: bool, score: int) -> None:
        self.correct = correct
        self.score = score
        super().__init__("This question was already answered")


@dataclass(frozen=True)
class Question:
    question_id: str
    prompt: str
    choices: tuple[str, ...]
    correct_choice: str


@dataclass
class Participant:
    user_id: str
    display_name: str
    score: int = 0


@dataclass(frozen=True)
class AnswerRecord:
    question_id: str
    choice: str
    correct: bool


@dataclass(frozen=True)
class AnswerResult:
    correct: bool
    score: int


@dataclass(frozen=True)
class LeaderboardEntry:
    rank: int
    user_id: str
    display_name: str
    score: int


@dataclass
class QuizSession:
    quiz_id: str
    questions: dict[str, Question]
    participants: dict[str, Participant] = field(default_factory=dict)
    answers: dict[tuple[str, str], AnswerRecord] = field(default_factory=dict)
