from pydantic import BaseModel


class AgentMessage(BaseModel):
    message: str
    context: str | None = None  # e.g., "job_search", "cover_letter", "resume_review"


class AgentResponse(BaseModel):
    reply: str
    suggestions: list[str] = []


class CoverLetterRequest(BaseModel):
    job_id: str
    user_id: str


class MatchScoreRequest(BaseModel):
    job_description: str
    resume_text: str


class MatchScoreResponse(BaseModel):
    score: float
    strengths: list[str]
    gaps: list[str]
    suggestions: list[str]
