"""
Data models for a simple task management API.
Currently using Pydantic v1 syntax.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, validator, root_validator, ConfigDict, field_validator, model_validator, ValidationInfo


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

    model_config = ConfigDict(frozen=True, json_schema_extra={"example": {"name": "urgent", "color": "#FF0000"}})

    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field(default="#808080", pattern=r"^#[0-9A-Fa-f]{6}$")


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

    model_config = ConfigDict(use_enum_values=True, validate_assignment=True, json_schema_extra={"example": {"title": "Complete project proposal", "description": "Write and submit the Q1 project proposal", "priority": "high", "status": "todo"}})

    @field_validator("title")
    @classmethod
    def title_must_not_be_empty(cls, v):
        """Ensure title is not just whitespace."""
        if not v.strip():
            raise ValueError("Title cannot be empty or whitespace only")
        return v.strip()

    @field_validator("due_date")
    @classmethod
    def due_date_must_be_future(cls, v: Optional[datetime], info: ValidationInfo) -> Optional[datetime]:
        """Warn if due date is in the past (but allow it)."""
        # Note: In v2, we use ValidationInfo to access other fields if needed
        if v and v < datetime.utcnow():
            # We allow past dates but could log a warning
            pass
        return v

    @model_validator(mode="after")
    def validate_and_set_completed_at(self) -> "Task":
        """Auto-set completed_at when status is DONE and validate consistency."""
        # Handle completed_at auto-setting
        is_done = self.status == TaskStatus.DONE or self.status == "done"
        if is_done and self.completed_at is None:
            object.__setattr__(self, 'completed_at', datetime.utcnow())
        elif not is_done:
            object.__setattr__(self, 'completed_at', None)

        # If archived, must have been completed
        is_archived = self.status == TaskStatus.ARCHIVED or self.status == "archived"
        if is_archived and self.completed_at is None:
            raise ValueError("Archived tasks must have a completed_at timestamp")

        return self

    def mark_complete(self) -> "Task":
        """Mark the task as complete."""
        return self.model_copy(update={
            "status": TaskStatus.DONE,
            "completed_at": datetime.utcnow()
        })

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return self.model_dump()

    def to_json(self) -> str:
        """Convert to JSON string."""
        return self.model_dump_json()


class TaskList(BaseModel):
    """A collection of tasks with metadata."""
    
    name: str = Field(..., min_length=1, max_length=100)
    tasks: List[Task] = Field(default_factory=list)
    owner: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(validate_assignment=True)

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v):
        """Ensure name is not just whitespace."""
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace only")
        return v.strip()

    def add_task(self, task: Task) -> "TaskList":
        """Add a task to the list."""
        new_tasks = self.tasks + [task]
        return self.model_copy(update={"tasks": new_tasks})

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
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    full_name: Optional[str] = None
    is_active: bool = True
    task_lists: List[TaskList] = Field(default_factory=list)

    model_config = ConfigDict(validate_assignment=True, json_schema_extra={"example": {"username": "johndoe", "email": "john@example.com", "full_name": "John Doe"}})

    @field_validator("email")
    @classmethod
    def email_must_be_lowercase(cls, v):
        """Normalize email to lowercase."""
        return v.lower()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return self.model_dump()
