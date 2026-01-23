"""
Data models for a simple task management API.
Currently using Pydantic v1 syntax.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, validator, root_validator


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ARCHIVED = "archived"


class Tag(BaseModel):
    """A tag that can be applied to tasks."""
    
    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field(default="#808080", regex=r"^#[0-9A-Fa-f]{6}$")

    class Config:
        # Pydantic v1 config style
        frozen = True
        schema_extra = {
            "example": {
                "name": "urgent",
                "color": "#FF0000"
            }
        }


class Task(BaseModel):
    """A task in the task management system."""
    
    id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    status: TaskStatus = TaskStatus.TODO
    priority: Priority = Priority.MEDIUM
    tags: List[Tag] = Field(default_factory=list)
    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Config:
        # Pydantic v1 config style
        use_enum_values = True
        validate_assignment = True
        schema_extra = {
            "example": {
                "title": "Complete project proposal",
                "description": "Write and submit the Q1 project proposal",
                "priority": "high",
                "status": "todo"
            }
        }

    @validator("title")
    def title_must_not_be_empty(cls, v):
        """Ensure title is not just whitespace."""
        if not v.strip():
            raise ValueError("Title cannot be empty or whitespace only")
        return v.strip()

    @validator("due_date")
    def due_date_must_be_future(cls, v, values):
        """Warn if due date is in the past (but allow it)."""
        # Note: In v1, we access other fields via 'values' dict
        if v and v < datetime.utcnow():
            # We allow past dates but could log a warning
            pass
        return v

    @validator("completed_at", always=True)
    def set_completed_at_when_done(cls, v, values):
        """Auto-set completed_at when status is DONE."""
        status = values.get("status")
        if status == TaskStatus.DONE and v is None:
            return datetime.utcnow()
        if status != TaskStatus.DONE:
            return None
        return v

    @root_validator
    def validate_task_consistency(cls, values):
        """Ensure task data is consistent."""
        status = values.get("status")
        completed_at = values.get("completed_at")

        # If archived, must have been completed
        if status == TaskStatus.ARCHIVED and completed_at is None:
            raise ValueError("Archived tasks must have a completed_at timestamp")

        # Check that due_date is not before created_at
        due_date = values.get("due_date")
        created_at = values.get("created_at")
        if due_date is not None and created_at is not None and due_date < created_at:
            raise ValueError("due_date cannot be before created_at")

        return values

    def mark_complete(self) -> "Task":
        """Mark the task as complete."""
        return self.copy(update={
            "status": TaskStatus.DONE,
            "completed_at": datetime.utcnow()
        })

    def to_dict(self) -> dict:
        """Convert to dictionary (Pydantic v1 style)."""
        return self.dict()

    def to_json(self) -> str:
        """Convert to JSON string (Pydantic v1 style)."""
        return self.json()


class TaskList(BaseModel):
    """A collection of tasks with metadata."""
    
    name: str = Field(..., min_length=1, max_length=100)
    tasks: List[Task] = Field(default_factory=list)
    owner: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        # Pydantic v1 config style
        validate_assignment = True

    @validator("name")
    def name_must_not_be_empty(cls, v):
        """Ensure name is not just whitespace."""
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace only")
        return v.strip()

    def add_task(self, task: Task) -> "TaskList":
        """Add a task to the list."""
        new_tasks = self.tasks + [task]
        return self.copy(update={"tasks": new_tasks})

    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Filter tasks by status."""
        return [t for t in self.tasks if t.status == status]

    def get_tasks_by_priority(self, priority: Priority) -> List[Task]:
        """Filter tasks by priority."""
        return [t for t in self.tasks if t.priority == priority]

    def get_overdue_tasks(self) -> List[Task]:
        """Get all tasks that are past their due date."""
        now = datetime.utcnow()
        return [
            t for t in self.tasks 
            if t.due_date and t.due_date < now and t.status != TaskStatus.DONE
        ]


class User(BaseModel):
    """A user in the system."""
    
    id: Optional[int] = None
    username: str = Field(..., min_length=3, max_length=50, regex=r"^[a-zA-Z0-9_]+$")
    email: str = Field(..., regex=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    full_name: Optional[str] = None
    is_active: bool = True
    task_lists: List[TaskList] = Field(default_factory=list)

    class Config:
        # Pydantic v1 config style
        validate_assignment = True
        schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john@example.com",
                "full_name": "John Doe"
            }
        }

    @validator("email")
    def email_must_be_lowercase(cls, v):
        """Normalize email to lowercase."""
        return v.lower()

    def to_dict(self) -> dict:
        """Convert to dictionary (Pydantic v1 style)."""
        return self.dict()
