from pydantic import BaseModel, field_validator


class CreateQuizResponse(BaseModel):
    quiz_id: str


class JoinQuizRequest(BaseModel):
    display_name: str

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("display_name must not be blank")
        if len(cleaned) > 40:
            raise ValueError("display_name must be at most 40 characters")
        return cleaned


class ParticipantResponse(BaseModel):
    user_id: str
    display_name: str
    score: int


class QuestionResponse(BaseModel):
    question_id: str
    prompt: str
    choices: list[str]


class SubmitAnswerRequest(BaseModel):
    user_id: str
    question_id: str
    choice: str

    @field_validator("user_id", "question_id", "choice")
    @classmethod
    def require_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value


class SubmitAnswerResponse(BaseModel):
    correct: bool
    score: int


class LeaderboardEntryResponse(BaseModel):
    rank: int
    user_id: str
    display_name: str
    score: int
