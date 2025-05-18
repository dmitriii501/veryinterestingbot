from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel


class Employee(BaseModel):
    id: int
    full_name: str
    department: str
    position: str
    email: Optional[str] = None
    birthday: Optional[date] = None
    projects: List[str] = []
    skills: List[str] = []
    telegram_id: Optional[int] = None


class Event(BaseModel):
    id: int
    title: str
    description: str
    date: date
    time: Optional[str] = None
    location: Optional[str] = None
    organizer_id: int
    participants: List[int] = []
    type: str  # 'corporate', 'birthday', 'team_building', etc.


class Task(BaseModel):
    id: int
    title: str
    description: str
    assignee_id: int
    due_date: datetime
    status: str  # 'pending', 'in_progress', 'completed'
    priority: str  # 'low', 'medium', 'high'
    project: Optional[str] = None 