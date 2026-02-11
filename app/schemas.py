# This defines what data a worker must send

from pydantic import BaseModel, EmailStr, Field

class WorkerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    email: EmailStr
    skill: str
    experience_years: int = Field(ge=0, le=50)
    salary: int = Field(gt=0)

class WorkerOut(BaseModel):
    id: int
    name: str
    email: str
    skill: str
    experience_years: int
    salary: int

class WorkerResponse(BaseModel):
    message: str
    worker: WorkerOut