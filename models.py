"""
Data models for a simple task management API.
Currently using Pydantic v1 syntax.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, validator, root_validator, ValidationError

from exceptions import (
    FieldValidationException,
    StateValidationException,
    DateValidationException,
    DuplicateTaskException,
    InvalidStateTransitionException,
    SerializationException
)


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
            raise FieldValidationException(
                field_name="title",
                message="Title cannot be empty or whitespace only",
                invalid_value=v,
                error_code="TASK_TITLE_EMPTY",
                details={
                    "suggestion": "Provide a non-empty title with at least one non-whitespace character"
                }
            )
        return v.strip()

    @validator("due_date")
    def due_date_must_be_future(cls, v, values):
        """Validate due date is reasonable and provide warnings for far past dates."""
        if v is None:
            return v

        try:
            now = datetime.utcnow()

            # Check if due date is more than 1 year in the past
            one_year_ago = datetime(now.year - 1, now.month, now.day, now.hour, now.minute, now.second)

            if v < one_year_ago:
                raise DateValidationException(
                    field_name="due_date",
                    message="Due date is more than 1 year in the past, which may be an error",
                    invalid_date=v,
                    error_code="DUE_DATE_FAR_PAST",
                    details={
                        "due_date": str(v),
                        "current_time": str(now),
                        "threshold": "1 year ago",
                        "suggestion": "Verify the due date is correct. Tasks should not typically have due dates more than 1 year in the past."
                    }
                )

            return v
        except (TypeError, AttributeError, ValueError) as e:
            raise DateValidationException(
                field_name="due_date",
                message=f"Invalid due date format or value: {str(e)}",
                invalid_date=v,
                error_code="DUE_DATE_INVALID",
                details={
                    "original_error": str(e),
                    "error_type": type(e).__name__,
                    "suggestion": "Provide a valid datetime object for due_date"
                }
            )

    @validator("completed_at", always=True)
    def set_completed_at_when_done(cls, v, values):
        """Auto-set completed_at when status is DONE."""
        try:
            status = values.get("status")

            if status == TaskStatus.DONE and v is None:
                return datetime.utcnow()
            if status != TaskStatus.DONE:
                return None

            return v
        except (TypeError, AttributeError) as e:
            raise DateValidationException(
                field_name="completed_at",
                message=f"Error handling completed_at datetime: {str(e)}",
                invalid_date=v,
                error_code="COMPLETED_AT_ERROR",
                details={
                    "original_error": str(e),
                    "error_type": type(e).__name__,
                    "status": str(values.get("status")),
                    "suggestion": "Ensure status is a valid TaskStatus and completed_at is a datetime object or None"
                }
            )

    @root_validator(skip_on_failure=True)
    def validate_task_consistency(cls, values):
        """Ensure task data is consistent."""
        status = values.get("status")
        completed_at = values.get("completed_at")

        # If archived, must have been completed
        if status == TaskStatus.ARCHIVED and completed_at is None:
            raise StateValidationException(
                message="Archived tasks must have a completed_at timestamp",
                current_state=str(status),
                error_code="ARCHIVED_WITHOUT_COMPLETION",
                details={
                    "status": str(status),
                    "completed_at": str(completed_at),
                    "suggestion": "Tasks must be marked as DONE with a completed_at timestamp before they can be ARCHIVED"
                }
            )

        return values

    def mark_complete(self) -> "Task":
        """
        Mark the task as complete.

        Raises:
            InvalidStateTransitionException: If the task is already completed or archived
        """
        # Get status value (handle both enum and string values due to use_enum_values)
        current_status = self.status if isinstance(self.status, str) else self.status.value

        if current_status == TaskStatus.DONE.value:
            raise InvalidStateTransitionException(
                message="Task is already marked as complete",
                current_status=current_status,
                attempted_status=TaskStatus.DONE.value,
                error_code="ALREADY_COMPLETED",
                details={
                    "task_id": str(self.id) if self.id else "None",
                    "task_title": self.title,
                    "completed_at": str(self.completed_at) if self.completed_at else "None",
                    "suggestion": "Task is already in DONE status. No action needed."
                }
            )

        if current_status == TaskStatus.ARCHIVED.value:
            raise InvalidStateTransitionException(
                message="Cannot mark archived tasks as complete",
                current_status=current_status,
                attempted_status=TaskStatus.DONE.value,
                error_code="ARCHIVED_TASK_COMPLETION",
                details={
                    "task_id": str(self.id) if self.id else "None",
                    "task_title": self.title,
                    "suggestion": "Archived tasks cannot be modified. Restore the task from archive before marking it complete."
                }
            )

        try:
            return self.copy(update={
                "status": TaskStatus.DONE,
                "completed_at": datetime.utcnow()
            })
        except Exception as e:
            raise InvalidStateTransitionException(
                message=f"Failed to mark task as complete: {str(e)}",
                current_status=current_status,
                attempted_status=TaskStatus.DONE.value,
                error_code="MARK_COMPLETE_FAILED",
                details={
                    "task_id": str(self.id) if self.id else "None",
                    "task_title": self.title,
                    "original_error": str(e),
                    "error_type": type(e).__name__,
                    "suggestion": "Check task data integrity and ensure all required fields are valid."
                }
            )

    def to_dict(self) -> dict:
        """
        Convert to dictionary (Pydantic v1 style).

        Raises:
            SerializationException: If conversion to dict fails
        """
        try:
            return self.dict()
        except Exception as e:
            raise SerializationException(
                message=f"Failed to convert Task to dictionary: {str(e)}",
                operation="to_dict",
                original_error=e,
                error_code="TASK_TO_DICT_FAILED",
                details={
                    "task_id": str(self.id) if self.id else "None",
                    "task_title": self.title if hasattr(self, "title") else "Unknown",
                    "suggestion": "Verify that all task fields contain serializable data types."
                }
            )

    def to_json(self) -> str:
        """
        Convert to JSON string (Pydantic v1 style).

        Raises:
            SerializationException: If JSON encoding fails
        """
        try:
            return self.json()
        except Exception as e:
            raise SerializationException(
                message=f"Failed to convert Task to JSON: {str(e)}",
                operation="to_json",
                original_error=e,
                error_code="TASK_TO_JSON_FAILED",
                details={
                    "task_id": str(self.id) if self.id else "None",
                    "task_title": self.title if hasattr(self, "title") else "Unknown",
                    "suggestion": "Ensure all task fields are JSON-serializable. Convert datetime objects appropriately."
                }
            )


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
        try:
            if not v or not v.strip():
                raise FieldValidationException(
                    field_name="name",
                    message="TaskList name cannot be empty or whitespace only",
                    invalid_value=v,
                    error_code="TASKLIST_NAME_EMPTY",
                    details={
                        "suggestion": "Provide a non-empty name with at least one non-whitespace character"
                    }
                )
            return v.strip()
        except (TypeError, AttributeError) as e:
            raise FieldValidationException(
                field_name="name",
                message=f"TaskList name validation failed: {str(e)}",
                invalid_value=v,
                error_code="TASKLIST_NAME_VALIDATION_ERROR",
                details={
                    "original_error": str(e),
                    "error_type": type(e).__name__,
                    "suggestion": "Ensure name is a string between 1 and 100 characters"
                }
            )

    @validator("tasks")
    def validate_no_duplicate_task_ids(cls, v):
        """Ensure no duplicate task IDs within the list."""
        if not v:
            return v

        try:
            task_ids = [task.id for task in v if task.id is not None]

            if len(task_ids) != len(set(task_ids)):
                # Find the duplicate IDs
                seen = set()
                duplicates = set()
                for task_id in task_ids:
                    if task_id in seen:
                        duplicates.add(task_id)
                    seen.add(task_id)

                raise DuplicateTaskException(
                    task_id=str(list(duplicates)),
                    message=f"Duplicate task IDs found in list: {', '.join(str(d) for d in duplicates)}",
                    error_code="DUPLICATE_TASK_IDS_IN_LIST",
                    details={
                        "duplicate_ids": list(duplicates),
                        "total_tasks": len(v),
                        "unique_ids": len(set(task_ids)),
                        "suggestion": "Each task in a TaskList must have a unique ID. Remove or reassign duplicate IDs."
                    }
                )

            return v
        except (TypeError, AttributeError) as e:
            raise FieldValidationException(
                field_name="tasks",
                message=f"Task list validation failed: {str(e)}",
                invalid_value=f"{len(v)} tasks" if v else "None",
                error_code="TASKLIST_TASKS_VALIDATION_ERROR",
                details={
                    "original_error": str(e),
                    "error_type": type(e).__name__,
                    "suggestion": "Ensure tasks is a list of Task objects with valid IDs"
                }
            )

    def add_task(self, task: Task) -> "TaskList":
        """
        Add a task to the list.

        Raises:
            DuplicateTaskException: If a task with the same ID already exists
            FieldValidationException: If the task object is invalid
        """
        # Check for None task ID - allow adding tasks without IDs (will be assigned later)
        if task.id is not None:
            # Check if task with this ID already exists
            existing_ids = [t.id for t in self.tasks if t.id is not None]

            if task.id in existing_ids:
                raise DuplicateTaskException(
                    task_id=str(task.id),
                    message=f"Cannot add task: A task with ID '{task.id}' already exists in this list",
                    error_code="DUPLICATE_TASK_IN_ADD",
                    details={
                        "task_id": task.id,
                        "task_title": task.title,
                        "existing_task_count": len(self.tasks),
                        "suggestion": "Use a unique task ID or update the existing task instead"
                    }
                )

        try:
            new_tasks = self.tasks + [task]
            return self.copy(update={"tasks": new_tasks})
        except Exception as e:
            raise FieldValidationException(
                field_name="tasks",
                message=f"Failed to add task to list: {str(e)}",
                invalid_value=f"Task ID {task.id}" if task.id else "Task without ID",
                error_code="ADD_TASK_FAILED",
                details={
                    "task_id": str(task.id) if task.id else "None",
                    "task_title": task.title if hasattr(task, "title") else "Unknown",
                    "original_error": str(e),
                    "error_type": type(e).__name__,
                    "suggestion": "Verify the task object is valid and the list can be updated"
                }
            )

    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """
        Filter tasks by status.

        Args:
            status: The TaskStatus to filter by

        Returns:
            List of tasks with the specified status

        Raises:
            FieldValidationException: If the status value is invalid
        """
        try:
            # Validate that status is a valid TaskStatus
            if isinstance(status, str):
                # If string is passed, try to convert it to TaskStatus enum
                try:
                    status = TaskStatus(status)
                except ValueError:
                    valid_statuses = [s.value for s in TaskStatus]
                    raise FieldValidationException(
                        field_name="status",
                        message=f"Invalid status value '{status}'",
                        invalid_value=status,
                        error_code="INVALID_STATUS_VALUE",
                        details={
                            "valid_statuses": valid_statuses,
                            "suggestion": f"Use one of the valid status values: {', '.join(valid_statuses)}"
                        }
                    )

            # Filter tasks by status
            return [t for t in self.tasks if t.status == status or t.status == status.value]
        except FieldValidationException:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            raise FieldValidationException(
                field_name="status",
                message=f"Error filtering tasks by status: {str(e)}",
                invalid_value=str(status),
                error_code="FILTER_BY_STATUS_FAILED",
                details={
                    "original_error": str(e),
                    "error_type": type(e).__name__,
                    "suggestion": "Ensure the status parameter is a valid TaskStatus enum value"
                }
            )

    def get_tasks_by_priority(self, priority: Priority) -> List[Task]:
        """
        Filter tasks by priority.

        Args:
            priority: The Priority to filter by

        Returns:
            List of tasks with the specified priority

        Raises:
            FieldValidationException: If the priority value is invalid
        """
        try:
            # Validate that priority is a valid Priority
            if isinstance(priority, str):
                # If string is passed, try to convert it to Priority enum
                try:
                    priority = Priority(priority)
                except ValueError:
                    valid_priorities = [p.value for p in Priority]
                    raise FieldValidationException(
                        field_name="priority",
                        message=f"Invalid priority value '{priority}'",
                        invalid_value=priority,
                        error_code="INVALID_PRIORITY_VALUE",
                        details={
                            "valid_priorities": valid_priorities,
                            "suggestion": f"Use one of the valid priority values: {', '.join(valid_priorities)}"
                        }
                    )

            # Filter tasks by priority
            return [t for t in self.tasks if t.priority == priority or t.priority == priority.value]
        except FieldValidationException:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            raise FieldValidationException(
                field_name="priority",
                message=f"Error filtering tasks by priority: {str(e)}",
                invalid_value=str(priority),
                error_code="FILTER_BY_PRIORITY_FAILED",
                details={
                    "original_error": str(e),
                    "error_type": type(e).__name__,
                    "suggestion": "Ensure the priority parameter is a valid Priority enum value"
                }
            )

    def get_overdue_tasks(self) -> List[Task]:
        """
        Get all tasks that are past their due date.

        Returns:
            List of overdue tasks (tasks with due_date in the past and not completed)

        Raises:
            DateValidationException: If datetime comparison fails
        """
        try:
            now = datetime.utcnow()
            overdue_tasks = []

            for t in self.tasks:
                try:
                    # Skip tasks without due dates
                    if not t.due_date:
                        continue

                    # Skip completed tasks
                    task_status = t.status if isinstance(t.status, str) else t.status.value
                    if task_status == TaskStatus.DONE.value:
                        continue

                    # Check if task is overdue
                    if t.due_date < now:
                        overdue_tasks.append(t)

                except (TypeError, AttributeError) as e:
                    # Handle individual task comparison errors
                    raise DateValidationException(
                        field_name="due_date",
                        message=f"Error comparing due date for task '{t.title if hasattr(t, 'title') else 'Unknown'}': {str(e)}",
                        invalid_date=t.due_date if hasattr(t, "due_date") else None,
                        error_code="OVERDUE_COMPARISON_ERROR",
                        details={
                            "task_id": str(t.id) if hasattr(t, "id") and t.id else "None",
                            "task_title": t.title if hasattr(t, "title") else "Unknown",
                            "due_date": str(t.due_date) if hasattr(t, "due_date") else "None",
                            "original_error": str(e),
                            "error_type": type(e).__name__,
                            "suggestion": "Ensure all tasks have valid datetime objects for due_date field"
                        }
                    )

            return overdue_tasks

        except DateValidationException:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            raise DateValidationException(
                field_name="due_date",
                message=f"Error retrieving overdue tasks: {str(e)}",
                error_code="GET_OVERDUE_TASKS_FAILED",
                details={
                    "original_error": str(e),
                    "error_type": type(e).__name__,
                    "suggestion": "Verify all tasks have valid due_date and status fields"
                }
            )


class User(BaseModel):
    """A user in the system."""

    id: Optional[int] = None
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(...)
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

    @validator("username")
    def validate_username_format(cls, v):
        """Validate username contains only allowed characters."""
        import re

        try:
            if not v or not v.strip():
                raise FieldValidationException(
                    field_name="username",
                    message="Username cannot be empty or whitespace only",
                    invalid_value=v,
                    error_code="USERNAME_EMPTY",
                    details={
                        "suggestion": "Provide a username with at least 3 characters"
                    }
                )

            # Check username format: alphanumeric and underscore only
            username_pattern = r"^[a-zA-Z0-9_]+$"
            if not re.match(username_pattern, v):
                # Identify the problematic characters
                invalid_chars = [c for c in v if not re.match(r"[a-zA-Z0-9_]", c)]

                raise FieldValidationException(
                    field_name="username",
                    message="Username can only contain letters, numbers, and underscores",
                    invalid_value=v,
                    error_code="USERNAME_INVALID_FORMAT",
                    details={
                        "allowed_characters": "a-z, A-Z, 0-9, _ (underscore)",
                        "invalid_characters": list(set(invalid_chars)),
                        "examples": "john_doe, user123, my_username",
                        "suggestion": "Remove special characters, spaces, or non-alphanumeric characters except underscores"
                    }
                )

            return v.strip()
        except ValidationError as e:
            raise FieldValidationException(
                field_name="username",
                message=f"Username validation failed: {str(e)}",
                invalid_value=v,
                error_code="USERNAME_VALIDATION_ERROR",
                details={
                    "original_error": str(e),
                    "suggestion": "Username must be 3-50 characters containing only letters, numbers, and underscores"
                }
            )

    @validator("email")
    def validate_email_format(cls, v):
        """Validate email format with detailed error messages for common mistakes."""
        import re

        try:
            if not v or not v.strip():
                raise FieldValidationException(
                    field_name="email",
                    message="Email cannot be empty",
                    invalid_value=v,
                    error_code="EMAIL_EMPTY",
                    details={
                        "expected_format": "user@domain.com",
                        "suggestion": "Provide a valid email address"
                    }
                )

            v = v.lower().strip()

            # Check for missing @ symbol
            if "@" not in v:
                raise FieldValidationException(
                    field_name="email",
                    message="Email address must contain @ symbol",
                    invalid_value=v,
                    error_code="EMAIL_MISSING_AT_SYMBOL",
                    details={
                        "expected_format": "user@domain.com",
                        "examples": "john@example.com, user@company.org",
                        "suggestion": "Add @ symbol between username and domain (e.g., user@domain.com)"
                    }
                )

            # Check for multiple @ symbols
            if v.count("@") > 1:
                raise FieldValidationException(
                    field_name="email",
                    message="Email address can only contain one @ symbol",
                    invalid_value=v,
                    error_code="EMAIL_MULTIPLE_AT_SYMBOLS",
                    details={
                        "at_symbol_count": v.count("@"),
                        "expected_format": "user@domain.com",
                        "suggestion": "Ensure only one @ symbol separates username and domain"
                    }
                )

            # Split into local and domain parts
            local_part, domain_part = v.rsplit("@", 1)

            # Validate local part is not empty
            if not local_part:
                raise FieldValidationException(
                    field_name="email",
                    message="Email must have a username before @ symbol",
                    invalid_value=v,
                    error_code="EMAIL_EMPTY_LOCAL_PART",
                    details={
                        "expected_format": "user@domain.com",
                        "suggestion": "Add username before @ symbol (e.g., john@example.com)"
                    }
                )

            # Validate domain part is not empty
            if not domain_part:
                raise FieldValidationException(
                    field_name="email",
                    message="Email must have a domain after @ symbol",
                    invalid_value=v,
                    error_code="EMAIL_EMPTY_DOMAIN",
                    details={
                        "expected_format": "user@domain.com",
                        "suggestion": "Add domain after @ symbol (e.g., user@example.com)"
                    }
                )

            # Check for missing domain extension (TLD)
            if "." not in domain_part:
                raise FieldValidationException(
                    field_name="email",
                    message="Email domain must include a top-level domain (e.g., .com, .org)",
                    invalid_value=v,
                    error_code="EMAIL_MISSING_TLD",
                    details={
                        "domain_provided": domain_part,
                        "expected_format": "user@domain.com",
                        "examples": "user@example.com, user@company.org, user@mail.co.uk",
                        "suggestion": f"Add a domain extension like .com, .org, .net to '{domain_part}'"
                    }
                )

            # Check that domain extension is valid (at least 2 characters)
            domain_parts = domain_part.split(".")
            tld = domain_parts[-1]
            if len(tld) < 2:
                raise FieldValidationException(
                    field_name="email",
                    message="Email domain extension must be at least 2 characters",
                    invalid_value=v,
                    error_code="EMAIL_INVALID_TLD",
                    details={
                        "tld_provided": tld,
                        "expected_format": "user@domain.com",
                        "examples": ".com, .org, .net, .co.uk",
                        "suggestion": "Use a valid domain extension like .com, .org, or .net"
                    }
                )

            # Validate full email format with regex
            email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
            if not re.match(email_pattern, v):
                raise FieldValidationException(
                    field_name="email",
                    message="Email format is invalid",
                    invalid_value=v,
                    error_code="EMAIL_INVALID_FORMAT",
                    details={
                        "expected_format": "user@domain.com",
                        "examples": "john@example.com, user.name@company.org, test_user@mail.co.uk",
                        "allowed_characters": "letters, numbers, dots (.), hyphens (-), and underscores (_)",
                        "suggestion": "Ensure email follows standard format: username@domain.extension"
                    }
                )

            return v
        except ValidationError as e:
            raise FieldValidationException(
                field_name="email",
                message=f"Email validation failed: {str(e)}",
                invalid_value=v,
                error_code="EMAIL_VALIDATION_ERROR",
                details={
                    "original_error": str(e),
                    "expected_format": "user@domain.com",
                    "suggestion": "Provide a valid email address in the format username@domain.extension"
                }
            )

    @validator("task_lists")
    def validate_no_duplicate_task_list_names(cls, v):
        """Ensure no duplicate task list names per user."""
        if not v:
            return v

        try:
            # Extract all task list names
            list_names = [task_list.name for task_list in v]

            # Check for duplicates (case-insensitive)
            normalized_names = [name.lower() for name in list_names]

            if len(normalized_names) != len(set(normalized_names)):
                # Find the duplicate names
                seen = set()
                duplicates = set()
                for name in normalized_names:
                    if name in seen:
                        # Find original case version
                        original_names = [ln for ln in list_names if ln.lower() == name]
                        duplicates.update(original_names)
                    seen.add(name)

                raise FieldValidationException(
                    field_name="task_lists",
                    message=f"Duplicate task list names found: {', '.join(sorted(duplicates))}",
                    invalid_value=f"{len(v)} task lists",
                    error_code="DUPLICATE_TASKLIST_NAMES",
                    details={
                        "duplicate_names": sorted(duplicates),
                        "total_lists": len(v),
                        "unique_names": len(set(normalized_names)),
                        "comparison": "case-insensitive",
                        "suggestion": "Each task list must have a unique name (case-insensitive). Rename duplicate lists."
                    }
                )

            return v
        except (TypeError, AttributeError) as e:
            raise FieldValidationException(
                field_name="task_lists",
                message=f"Task lists validation failed: {str(e)}",
                invalid_value=f"{len(v)} task lists" if v else "None",
                error_code="TASKLISTS_VALIDATION_ERROR",
                details={
                    "original_error": str(e),
                    "error_type": type(e).__name__,
                    "suggestion": "Ensure task_lists is a list of TaskList objects with valid names"
                }
            )

    def to_dict(self) -> dict:
        """Convert to dictionary (Pydantic v1 style)."""
        return self.dict()
