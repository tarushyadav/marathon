from typing import Optional
from enum import Enum
from pydantic import BaseModel, EmailStr, Field


# -------------------------
# SKILL ENUM (Controlled Vocabulary)
# -------------------------

class SkillEnum(str, Enum):
    delivery = "delivery"
    cleaning = "cleaning"
    driver = "driver"


# -------------------------
# WORKER CREATION (DB)
# -------------------------

class WorkerCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    skill: SkillEnum

    experience_years: int = Field(..., ge=0, le=50)
    salary: int = Field(..., gt=0)

    # Performance fields
    rating: Optional[float] = Field(default=0, ge=0, le=5)
    on_time: Optional[float] = Field(default=0, ge=0, le=100)
    completion: Optional[float] = Field(default=0, ge=0, le=100)
    complaints: Optional[int] = Field(default=0, ge=0)
    jobs_completed: Optional[int] = Field(default=0, ge=0)


# -------------------------
# WORKER OUTPUT
# -------------------------

class WorkerOut(BaseModel):
    id: int
    name: str
    email: str
    skill: SkillEnum

    experience_years: int
    salary: int

    rating: float
    on_time: float
    completion: float
    complaints: int
    jobs_completed: int

    class Config:
        from_attributes = True


class WorkerResponse(BaseModel):
    message: str
    worker: WorkerOut


# -------------------------
# SCORING INPUT (API)
# -------------------------

class WorkerScoreInput(BaseModel):
    rating: float = Field(..., ge=1, le=5)
    on_time: float = Field(..., ge=0, le=100)
    completion: float = Field(..., ge=0, le=100)

    experience_years: float = Field(..., ge=0)
    salary: float = Field(..., ge=0)

    complaints: int = Field(..., ge=0)
    jobs_completed: int = Field(..., ge=0)
    active_days: int = Field(..., ge=0)

    skill: Optional[SkillEnum] = None