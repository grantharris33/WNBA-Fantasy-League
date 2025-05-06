from __future__ import annotations

from datetime import datetime, date
from typing import Dict, Generic, List, TypeVar, Optional

from pydantic import BaseModel, Field, EmailStr
from pydantic.generics import GenericModel

T = TypeVar("T")


class Pagination(GenericModel, Generic[T]):
    """Generic pagination wrapper for list endpoints."""

    total: int = Field(..., description="Total number of available records")
    limit: int = Field(..., description="Limit originally requested")
    offset: int = Field(..., description="Offset originally requested")
    items: List[T] = Field(..., description="List of items in current page")


class LeagueOut(BaseModel):
    """DTO for ``league`` rows (read-only)."""

    id: int
    name: str
    created_at: datetime | None = None

    class Config:
        orm_mode = True


class PlayerOut(BaseModel):
    id: int
    full_name: str
    position: str | None = None
    team_abbr: str | None = None

    class Config:
        orm_mode = True


class TeamOut(BaseModel):
    id: int
    name: str
    league_id: int | None = None
    owner_id: int | None = None

    roster: List[PlayerOut] = Field(..., description="Current roster players")
    season_points: float = Field(..., description="Aggregated season points so far")

    class Config:
        orm_mode = True


class ScoreOut(BaseModel):
    team_id: int
    team_name: str
    season_points: float
    weekly_delta: float
    bonuses: Dict[str, float] = Field(default_factory=dict)

    class Config:
        orm_mode = True


# User schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    created_at: datetime

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str
