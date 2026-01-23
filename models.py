"""
Data models for a simple task management API.
Currently using Pydantic v1 syntax.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, validator, root_validator, ValidationError

from exceptions import FieldValidationException


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
    color: str = Field(default="#808080")

    class Config:
        # Pydantic v1 config style
        frozen = True
        schema_extra = {
            "example": {
                "name": "urgent",
                "color": "#FF0000"
            }
        }

    @validator("name")
    def validate_name_not_empty(cls, v):
        """Ensure name is not just whitespace."""
        try:
            if not v or not v.strip():
                raise FieldValidationException(
                    field_name="name",
                    message="Tag name cannot be empty or whitespace only",
                    invalid_value=v,
                    error_code="TAG_NAME_EMPTY",
                    details={
                        "suggestion": "Provide a non-empty tag name with at least one non-whitespace character"
                    }
                )
            return v.strip()
        except ValidationError as e:
            raise FieldValidationException(
                field_name="name",
                message=f"Tag name validation failed: {str(e)}",
                invalid_value=v,
                error_code="TAG_NAME_VALIDATION_ERROR",
                details={
                    "original_error": str(e),
                    "suggestion": "Ensure tag name is between 1 and 50 characters"
                }
            )

    @validator("color")
    def validate_color_format(cls, v):
        """Validate color is in hex format with detailed error message."""
        import re

        try:
            if not v:
                raise FieldValidationException(
                    field_name="color",
                    message="Color cannot be empty",
                    invalid_value=v,
                    error_code="TAG_COLOR_EMPTY",
                    details={
                        "expected_format": "#RRGGBB",
                        "examples": "#FF0000 (red), #00FF00 (green), #0000FF (blue)"
                    }
                )

            hex_pattern = r"^#[0-9A-Fa-f]{6}$"
            if not re.match(hex_pattern, v):
                raise FieldValidationException(
                    field_name="color",
                    message="Color must be in hex format #RRGGBB",
                    invalid_value=v,
                    error_code="TAG_COLOR_INVALID_FORMAT",
                    details={
                        "expected_format": "#RRGGBB where R, G, B are hexadecimal digits (0-9, A-F)",
                        "examples": "#FF0000 (red), #00FF00 (green), #0000FF (blue), #808080 (gray)",
                        "common_mistakes": "Missing # prefix, wrong length (must be exactly 7 characters), invalid characters"
                    }
                )

            return v.upper()
        except ValidationError as e:
            raise FieldValidationException(
                field_name="color",
                message=f"Color validation failed: {str(e)}",
                invalid_value=v,
                error_code="TAG_COLOR_VALIDATION_ERROR",
                details={
                    "original_error": str(e),
                    "expected_format": "#RRGGBB",
                    "examples": "#FF0000 (red), #00FF00 (green), #0000FF (blue), #808080 (gray)"
                }
            )


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

    @root_validator(skip_on_failure=True)
    def validate_task_consistency(cls, values):
        """Ensure task data is consistent."""
        status = values.get("status")
        completed_at = values.get("completed_at")
        
        # If archived, must have been completed
        if status == TaskStatus.ARCHIVED and completed_at is None:
            raise ValueError("Archived tasks must have a completed_at timestamp")
        
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
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
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
