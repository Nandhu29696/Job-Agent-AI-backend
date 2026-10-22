from typing import Literal
from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=8000)


class AgentMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=20)


class AgentStep(BaseModel):
    tool: str
    args: dict
    summary: str


class AgentAction(BaseModel):
    type: str
    label: str
    to: str


class AgentResponse(BaseModel):
    reply: str
    steps: list[AgentStep] = []
    actions: list[AgentAction] = []


class MatchScoreRequest(BaseModel):
    job_description: str = Field(..., max_length=15000)
    resume_text: str = Field(..., max_length=15000)


class MatchScoreResponse(BaseModel):
    score: float
    strengths: list[str]
    gaps: list[str]
    suggestions: list[str]
