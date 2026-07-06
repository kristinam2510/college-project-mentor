from pydantic import BaseModel
from typing import Optional


class IntakeRequest(BaseModel):
    domain: str
    sector: Optional[str] = None
    difficulty: str          # Easy | Medium | Hard
    duration_months: int
    team_size: int


class SelectIdeaRequest(BaseModel):
    project_id: str
    idea_index: int          # which of the generated ideas was picked


class TaskUpdateRequest(BaseModel):
    task_id: str
    status: str              # pending | in_progress | done


class MentorCheckRequest(BaseModel):
    project_id: str