from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class CaseStatus(str, Enum):
    PENDING_MODERATION = "pending_moderation"
    ACTIVE = "active"
    CLOSED = "closed"


class VoteSide(str, Enum):
    YES = "YES"
    NO = "NO"


class RewardType(str, Enum):
    WINNING_VOTER = "winning_voter"
    TOP_ARGUMENT = "top_argument"
    PARTICIPANT = "participant"
    CREATOR = "creator"


class RewardStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Request Models
class CreateCaseRequest(BaseModel):
    title: str = Field(..., min_length=10, max_length=200)
    context: str = Field(..., min_length=50, max_length=2000)

    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()

    @validator('context')
    def context_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Context cannot be empty')
        return v.strip()


class VoteRequest(BaseModel):
    side: VoteSide


class SubmitArgumentRequest(BaseModel):
    content: str = Field(..., min_length=20, max_length=300)
    side: VoteSide

    @validator('content')
    def content_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Argument content cannot be empty')
        return v.strip()


# Response Models
class UserBasicInfo(BaseModel):
    id: int
    name: str
    total_points: int

    class Config:
        from_attributes = True


class ArgumentResponse(BaseModel):
    id: int
    case_id: int
    user: UserBasicInfo
    content: str
    side: str
    votes: int
    is_top_3: bool
    created_at: datetime
    is_liked_by_user: bool = False

    class Config:
        from_attributes = True


class CaseListItem(BaseModel):
    id: int
    title: str
    context: str
    status: str
    yes_votes: int
    no_votes: int
    total_participants: int
    is_ai_generated: bool
    created_at: datetime
    closes_at: Optional[datetime]
    closed_at: Optional[datetime]
    creator: Optional[UserBasicInfo] = None
    user_voted_side: Optional[str] = None

    class Config:
        from_attributes = True


class CaseDetailResponse(BaseModel):
    id: int
    title: str
    context: str
    status: str
    ai_verdict: Optional[str] = None
    ai_verdict_reasoning: Optional[str] = None
    ai_confidence: Optional[float] = None
    yes_votes: int
    no_votes: int
    total_participants: int
    is_ai_generated: bool
    created_at: datetime
    closes_at: Optional[datetime]
    closed_at: Optional[datetime]
    creator: Optional[UserBasicInfo] = None
    arguments: List[ArgumentResponse] = []
    user_vote: Optional[dict] = None
    blockchain_tx_hash: Optional[str] = None
    verdict_hash: Optional[str] = None

    class Config:
        from_attributes = True


class CaseListResponse(BaseModel):
    cases: List[CaseListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class VoteResponse(BaseModel):
    message: str
    case_id: int
    side: str
    yes_votes: int
    no_votes: int
    total_participants: int


class ArgumentVoteResponse(BaseModel):
    message: str
    argument_id: int
    votes: int
    is_liked: bool
