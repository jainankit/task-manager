"""
Tests for Step 5.3: Add tests for method error handling.

This test file provides comprehensive coverage for all error handling scenarios
in Task, TaskList, and User methods including:
- mark_complete() with invalid state transitions
- add_task() with duplicate IDs
- Serialization methods with problematic data
- Filtering methods with invalid enum values
- Business logic violations (archived task operations, etc.)
"""
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from models import Task, TaskList, User, TaskStatus, Priority, Tag
from exceptions import (
    InvalidStateTransitionException,
    DuplicateTaskException,
    SerializationException,
    FieldValidationException,
    DateValidationException,
    StateValidationException,
    OwnershipException
)


class TestMarkCompleteInvalidStateTransitions:
    """Test mark_complete() with various invalid state transitions."""

    def test_mark_complete_on_already_completed_task(self):
        """Test that marking an already completed task raises InvalidStateTransitionException."""
        task = Task(
            id=1,
            title="Already done",
            status=TaskStatus.DONE,
            completed_at=datetime.utcnow()
        )

        with pytest.raises(InvalidStateTransitionException) as exc_info:
            task.mark_complete()

        assert exc_info.value.error_code == "ALREADY_COMPLETED"
        assert "already marked as complete" in exc_info.value.message
        assert exc_info.value.details["current_status"] == TaskStatus.DONE.value
        assert exc_info.value.details["attempted_status"] == TaskStatus.DONE.value
        assert exc_info.value.details["task_title"] == "Already done"

    def test_mark_complete_on_archived_task(self):
        """Test that marking an archived task raises InvalidStateTransitionException."""
        # Create archived task using construct to bypass validators
        task = Task.construct(
            id=2,
            title="Archived task",
            status=TaskStatus.ARCHIVED.value,
            completed_at=datetime.utcnow(),
            priority=Priority.MEDIUM.value
        )

        with pytest.raises(InvalidStateTransitionException) as exc_info:
            task.mark_complete()

        assert exc_info.value.error_code == "ARCHIVED_TASK_COMPLETION"
        assert "Cannot mark archived tasks as complete" in exc_info.value.message
        assert exc_info.value.details["current_status"] == TaskStatus.ARCHIVED.value
        assert "Restore the task from archive" in exc_info.value.details["suggestion"]

    def test_mark_complete_includes_task_details_in_error(self):
        """Test that error includes comprehensive task details."""
        task = Task(
            id=123,
            title="Important Task",
            status=TaskStatus.DONE,
            completed_at=datetime.utcnow()
        )

        with pytest.raises(InvalidStateTransitionException) as exc_info:
            task.mark_complete()

        assert exc_info.value.details["task_id"] == "123"
        assert exc_info.value.details["task_title"] == "Important Task"
        assert "completed_at" in exc_info.value.details

    def test_mark_complete_valid_transitions(self):
        """Test that valid transitions work correctly."""
        # TODO -> DONE
        task_todo = Task(id=1, title="Todo task", status=TaskStatus.TODO)
        completed_todo = task_todo.mark_complete()
        assert completed_todo.status == TaskStatus.DONE
        assert completed_todo.completed_at is not None

        # IN_PROGRESS -> DONE
        task_progress = Task(id=2, title="In progress", status=TaskStatus.IN_PROGRESS)
        completed_progress = task_progress.mark_complete()
        assert completed_progress.status == TaskStatus.DONE
        assert completed_progress.completed_at is not None

    def test_mark_complete_preserves_task_data(self):
        """Test that marking complete preserves other task data."""
        task = Task(
            id=42,
            title="Test Task",
            description="Test description",
            priority=Priority.HIGH,
            status=TaskStatus.TODO,
            tags=[Tag(name="urgent", color="#FF0000")],
            due_date=datetime.utcnow() + timedelta(days=7)
        )

        completed = task.mark_complete()

        assert completed.id == 42
        assert completed.title == "Test Task"
        assert completed.description == "Test description"
        assert completed.priority == Priority.HIGH
        assert len(completed.tags) == 1
        assert completed.due_date == task.due_date


class TestAddTaskWithDuplicateIDs:
    """Test add_task() with duplicate ID scenarios."""

    def test_add_task_with_duplicate_id(self):
        """Test that adding a task with duplicate ID raises DuplicateTaskException."""
        task1 = Task(id=1, title="First task")
        task2 = Task(id=1, title="Duplicate ID task")

        task_list = TaskList(name="My List", owner="user1", tasks=[task1])

        with pytest.raises(DuplicateTaskException) as exc_info:
            task_list.add_task(task2)

        assert exc_info.value.error_code == "DUPLICATE_TASK_IN_ADD"
        assert "already exists" in exc_info.value.message
        # task_id stored as int in details
        assert exc_info.value.details["task_id"] in [1, "1"]
        assert exc_info.value.details["task_title"] == "Duplicate ID task"

    def test_add_task_with_multiple_existing_tasks(self):
        """Test duplicate detection with multiple tasks in the list."""
        task1 = Task(id=1, title="Task 1")
        task2 = Task(id=2, title="Task 2")
        task3 = Task(id=3, title="Task 3")
        duplicate_task = Task(id=2, title="Duplicate of Task 2")

        task_list = TaskList(name="My List", owner="user1", tasks=[task1, task2, task3])

        with pytest.raises(DuplicateTaskException) as exc_info:
            task_list.add_task(duplicate_task)

        # task_id stored as int in details
        assert exc_info.value.details["task_id"] in [2, "2"]
        assert "unique task ID" in exc_info.value.details["suggestion"]

    def test_add_task_without_id_allows_multiple(self):
        """Test that tasks without IDs can be added multiple times."""
        task1 = Task(title="Task without ID 1")
        task2 = Task(title="Task without ID 2")
        task3 = Task(title="Task without ID 3")

        task_list = TaskList(name="My List", owner="user1", tasks=[task1])
        task_list = task_list.add_task(task2)
        task_list = task_list.add_task(task3)

        assert len(task_list.tasks) == 3

    def test_add_task_with_none_id_not_considered_duplicate(self):
        """Test that None IDs are not considered duplicates."""
        task1 = Task(id=None, title="Task 1")
        task2 = Task(id=None, title="Task 2")

        task_list = TaskList(name="My List", owner="user1", tasks=[task1])
        updated_list = task_list.add_task(task2)

        assert len(updated_list.tasks) == 2

    def test_add_task_duplicate_error_includes_context(self):
        """Test that duplicate error includes full context."""
        task1 = Task(id=99, title="Original")
        task2 = Task(id=99, title="Duplicate")

        task_list = TaskList(name="My List", owner="user1", tasks=[task1])

        with pytest.raises(DuplicateTaskException) as exc_info:
            task_list.add_task(task2)

        assert exc_info.value.details["existing_task_count"] == 1
        assert "suggestion" in exc_info.value.details


class TestSerializationMethodsWithProblematicData:
    """Test serialization methods (to_dict, to_json) with problematic data."""

    def test_task_to_dict_success_with_normal_data(self):
        """Test that normal tasks serialize successfully."""
        task = Task(
            id=1,
            title="Normal Task",
            description="A normal task",
            priority=Priority.HIGH,
            status=TaskStatus.TODO
        )

        result = task.to_dict()

        assert isinstance(result, dict)
        assert result["title"] == "Normal Task"
        assert result["priority"] == Priority.HIGH.value

    def test_task_to_dict_with_all_fields_populated(self):
        """Test serialization with all fields populated."""
        task = Task(
            id=42,
            title="Complete Task",
            description="Full description",
            status=TaskStatus.DONE,
            priority=Priority.CRITICAL,
            tags=[Tag(name="urgent", color="#FF0000")],
            due_date=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )

        result = task.to_dict()

        assert result["id"] == 42
        assert result["title"] == "Complete Task"
        assert "tags" in result
        assert len(result["tags"]) == 1
        assert "due_date" in result
        assert "completed_at" in result

    def test_task_to_json_success(self):
        """Test successful JSON conversion."""
        task = Task(title="Test", priority=Priority.LOW)

        json_str = task.to_json()

        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["title"] == "Test"
        assert parsed["priority"] == Priority.LOW.value

    def test_task_to_json_produces_valid_json(self):
        """Test that JSON output is valid and parseable."""
        task = Task(
            id=10,
            title="JSON Test",
            description="Testing JSON output",
            status=TaskStatus.IN_PROGRESS,
            priority=Priority.MEDIUM,
            tags=[Tag(name="test", color="#00FF00")]
        )

        json_str = task.to_json()

        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert parsed["id"] == 10
        assert parsed["status"] == TaskStatus.IN_PROGRESS.value

    def test_user_to_dict_with_inactive_user_raises_error(self):
        """Test that serializing an inactive user raises StateValidationException."""
        user = User(
            username="testuser",
            email="test@example.com",
            is_active=False
        )

        with pytest.raises(StateValidationException) as exc_info:
            user.to_dict()

        assert exc_info.value.error_code == "INACTIVE_USER_OPERATION"
        assert "inactive user" in exc_info.value.message.lower()
        assert exc_info.value.details["operation"] == "to_dict"
        assert exc_info.value.details["is_active"] is False

    def test_user_to_dict_with_nested_task_lists(self):
        """Test user serialization with nested task lists."""
        task = Task(id=1, title="Task 1")
        task_list = TaskList(name="List 1", owner="user1", tasks=[task])
        user = User(
            username="user1",
            email="user1@example.com",
            task_lists=[task_list]
        )

        result = user.to_dict()

        assert isinstance(result, dict)
        assert "task_lists" in result
        assert len(result["task_lists"]) == 1

    def test_user_to_dict_active_user_success(self):
        """Test that active users serialize successfully."""
        user = User(
            id=1,
            username="activeuser",
            email="active@example.com",
            full_name="Active User",
            is_active=True
        )

        result = user.to_dict()

        assert result["username"] == "activeuser"
        assert result["email"] == "active@example.com"
        assert result["is_active"] is True


class TestFilteringMethodsWithInvalidEnumValues:
    """Test filtering methods with invalid enum values."""

    def test_get_tasks_by_status_with_invalid_string(self):
        """Test filtering by invalid status string raises FieldValidationException."""
        task_list = TaskList(name="My List", owner="user1", tasks=[])

        with pytest.raises(FieldValidationException) as exc_info:
            task_list.get_tasks_by_status("invalid_status")

        assert exc_info.value.error_code == "INVALID_STATUS_VALUE"
        assert exc_info.value.field_name == "status"
        assert "invalid_status" in exc_info.value.details["invalid_value"]

    def test_get_tasks_by_status_invalid_includes_valid_options(self):
        """Test that error includes all valid status options."""
        task_list = TaskList(name="My List", owner="user1", tasks=[])

        with pytest.raises(FieldValidationException) as exc_info:
            task_list.get_tasks_by_status("bad_status")

        valid_statuses = exc_info.value.details["valid_statuses"]
        assert "todo" in valid_statuses
        assert "in_progress" in valid_statuses
        assert "done" in valid_statuses
        assert "archived" in valid_statuses

    def test_get_tasks_by_status_with_valid_string(self):
        """Test that valid status strings work correctly."""
        task1 = Task(id=1, title="Todo", status=TaskStatus.TODO)
        task2 = Task(id=2, title="Done", status=TaskStatus.DONE)
        task_list = TaskList(name="My List", owner="user1", tasks=[task1, task2])

        result = task_list.get_tasks_by_status("todo")

        assert len(result) == 1
        assert result[0].title == "Todo"

    def test_get_tasks_by_priority_with_invalid_string(self):
        """Test filtering by invalid priority string raises FieldValidationException."""
        task_list = TaskList(name="My List", owner="user1", tasks=[])

        with pytest.raises(FieldValidationException) as exc_info:
            task_list.get_tasks_by_priority("invalid_priority")

        assert exc_info.value.error_code == "INVALID_PRIORITY_VALUE"
        assert exc_info.value.field_name == "priority"
        assert "invalid_priority" in exc_info.value.details["invalid_value"]

    def test_get_tasks_by_priority_invalid_includes_valid_options(self):
        """Test that error includes all valid priority options."""
        task_list = TaskList(name="My List", owner="user1", tasks=[])

        with pytest.raises(FieldValidationException) as exc_info:
            task_list.get_tasks_by_priority("super_urgent")

        valid_priorities = exc_info.value.details["valid_priorities"]
        assert "low" in valid_priorities
        assert "medium" in valid_priorities
        assert "high" in valid_priorities
        assert "critical" in valid_priorities

    def test_get_tasks_by_priority_with_valid_string(self):
        """Test that valid priority strings work correctly."""
        task1 = Task(id=1, title="High", priority=Priority.HIGH)
        task2 = Task(id=2, title="Low", priority=Priority.LOW)
        task_list = TaskList(name="My List", owner="user1", tasks=[task1, task2])

        result = task_list.get_tasks_by_priority("high")

        assert len(result) == 1
        assert result[0].title == "High"

    def test_get_tasks_by_status_with_enum_works(self):
        """Test that filtering with actual enum values works."""
        task1 = Task(id=1, title="In Progress", status=TaskStatus.IN_PROGRESS)
        task2 = Task(id=2, title="Done", status=TaskStatus.DONE)
        task_list = TaskList(name="My List", owner="user1", tasks=[task1, task2])

        result = task_list.get_tasks_by_status(TaskStatus.IN_PROGRESS)

        assert len(result) == 1
        assert result[0].title == "In Progress"

    def test_get_tasks_by_priority_with_enum_works(self):
        """Test that filtering with actual enum values works."""
        task1 = Task(id=1, title="Critical", priority=Priority.CRITICAL)
        task2 = Task(id=2, title="Medium", priority=Priority.MEDIUM)
        task_list = TaskList(name="My List", owner="user1", tasks=[task1, task2])

        result = task_list.get_tasks_by_priority(Priority.CRITICAL)

        assert len(result) == 1
        assert result[0].title == "Critical"


class TestBusinessLogicViolations:
    """Test business logic violations including archived task operations."""

    def test_archived_task_cannot_be_marked_complete(self):
        """Test that archived tasks cannot be marked complete."""
        # Create an archived task
        task = Task.construct(
            title="Archived",
            status=TaskStatus.ARCHIVED.value,
            completed_at=datetime.utcnow(),
            priority=Priority.MEDIUM.value
        )

        with pytest.raises(InvalidStateTransitionException) as exc_info:
            task.mark_complete()

        assert exc_info.value.error_code == "ARCHIVED_TASK_COMPLETION"
        assert "Cannot mark archived tasks" in exc_info.value.message

    def test_archived_task_must_have_completed_at(self):
        """Test that archived tasks must have a completed_at timestamp."""
        with pytest.raises(StateValidationException) as exc_info:
            Task(
                title="Archived without completion",
                status=TaskStatus.ARCHIVED,
                completed_at=None
            )

        assert exc_info.value.error_code == "ARCHIVED_WITHOUT_COMPLETION"
        assert "Archived tasks must have a completed_at timestamp" in exc_info.value.message

    def test_duplicate_task_ids_in_tasklist_rejected(self):
        """Test that creating a TaskList with duplicate task IDs is rejected."""
        task1 = Task(id=1, title="Task 1")
        task2 = Task(id=1, title="Task 2 with duplicate ID")

        with pytest.raises(DuplicateTaskException) as exc_info:
            TaskList(name="My List", owner="user1", tasks=[task1, task2])

        assert exc_info.value.error_code == "DUPLICATE_TASK_IDS_IN_LIST"
        assert "Duplicate task IDs found" in exc_info.value.message

    def test_user_task_list_ownership_validation(self):
        """Test user validates task list ownership correctly."""
        task_list1 = TaskList(name="List 1", owner="user1", tasks=[])
        task_list2 = TaskList(name="List 2", owner="user1", tasks=[])
        user = User(
            username="user1",
            email="user1@example.com",
            task_lists=[task_list1, task_list2]
        )

        # Valid ownership check should not raise
        user.validate_task_list_ownership("List 1")
        user.validate_task_list_ownership("List 2")

    def test_user_task_list_ownership_not_found(self):
        """Test ownership validation fails for non-existent list."""
        task_list = TaskList(name="Existing List", owner="user1", tasks=[])
        user = User(
            username="user1",
            email="user1@example.com",
            task_lists=[task_list]
        )

        with pytest.raises(OwnershipException) as exc_info:
            user.validate_task_list_ownership("Non-Existent List")

        assert exc_info.value.error_code == "TASKLIST_NOT_FOUND"
        assert "not found" in exc_info.value.message.lower()
        assert "Existing List" in exc_info.value.details["available_lists"]

    def test_user_task_list_ownership_mismatch(self):
        """Test ownership validation fails when owner doesn't match."""
        task_list = TaskList(name="Shared List", owner="otheruser", tasks=[])
        user = User(
            username="user1",
            email="user1@example.com",
            task_lists=[task_list]
        )

        with pytest.raises(OwnershipException) as exc_info:
            user.validate_task_list_ownership("Shared List")

        assert exc_info.value.error_code == "TASKLIST_OWNERSHIP_MISMATCH"
        assert exc_info.value.details["expected_owner"] == "user1"
        assert exc_info.value.details["actual_owner"] == "otheruser"

    def test_inactive_user_cannot_serialize(self):
        """Test that inactive users cannot perform serialization operations."""
        user = User(
            username="inactiveuser",
            email="inactive@example.com",
            is_active=False
        )

        with pytest.raises(StateValidationException) as exc_info:
            user.to_dict()

        assert exc_info.value.error_code == "INACTIVE_USER_OPERATION"
        assert exc_info.value.details["is_active"] is False
        assert "Activate the user account" in exc_info.value.details["suggestion"]

    def test_get_overdue_tasks_handles_edge_cases(self):
        """Test get_overdue_tasks with various edge cases."""
        past = datetime.utcnow() - timedelta(days=1)
        future = datetime.utcnow() + timedelta(days=1)

        task1 = Task(id=1, title="Overdue", due_date=past, status=TaskStatus.TODO)
        task2 = Task(id=2, title="Not due yet", due_date=future, status=TaskStatus.TODO)
        task3 = Task(id=3, title="No due date", status=TaskStatus.TODO)
        task4 = Task(id=4, title="Overdue but done", due_date=past, status=TaskStatus.DONE)

        task_list = TaskList(
            name="My List",
            owner="user1",
            tasks=[task1, task2, task3, task4]
        )

        overdue = task_list.get_overdue_tasks()

        assert len(overdue) == 1
        assert overdue[0].title == "Overdue"

    def test_duplicate_tasklist_names_rejected(self):
        """Test that duplicate task list names are rejected."""
        task_list1 = TaskList(name="My List", owner="user1", tasks=[])
        task_list2 = TaskList(name="My List", owner="user1", tasks=[])

        with pytest.raises(FieldValidationException) as exc_info:
            User(
                username="user1",
                email="user1@example.com",
                task_lists=[task_list1, task_list2]
            )

        assert exc_info.value.error_code == "DUPLICATE_TASKLIST_NAMES"
        assert "My List" in exc_info.value.details["duplicate_names"]


class TestEdgeCasesAndErrorMessages:
    """Test edge cases and error message quality."""

    def test_mark_complete_error_messages_are_helpful(self):
        """Test that error messages provide helpful context."""
        task = Task(title="Test", status=TaskStatus.DONE)

        with pytest.raises(InvalidStateTransitionException) as exc_info:
            task.mark_complete()

        assert "suggestion" in exc_info.value.details
        suggestion = exc_info.value.details["suggestion"]
        assert len(suggestion) > 10

    def test_duplicate_task_error_includes_suggestion(self):
        """Test that duplicate task errors include helpful suggestions."""
        task1 = Task(id=1, title="First")
        task2 = Task(id=1, title="Duplicate")
        task_list = TaskList(name="My List", owner="user1", tasks=[task1])

        with pytest.raises(DuplicateTaskException) as exc_info:
            task_list.add_task(task2)

        assert "suggestion" in exc_info.value.details
        assert "unique" in exc_info.value.details["suggestion"].lower()

    def test_invalid_enum_errors_list_valid_values(self):
        """Test that invalid enum errors show all valid values."""
        task_list = TaskList(name="My List", owner="user1", tasks=[])

        with pytest.raises(FieldValidationException) as exc_info:
            task_list.get_tasks_by_status("wrong")

        assert "valid_statuses" in exc_info.value.details
        assert len(exc_info.value.details["valid_statuses"]) == 4

    def test_ownership_error_shows_available_lists(self):
        """Test that ownership errors show available task lists."""
        task_list1 = TaskList(name="List A", owner="user1", tasks=[])
        task_list2 = TaskList(name="List B", owner="user1", tasks=[])
        user = User(
            username="user1",
            email="user1@example.com",
            task_lists=[task_list1, task_list2]
        )

        with pytest.raises(OwnershipException) as exc_info:
            user.validate_task_list_ownership("List C")

        assert "available_lists" in exc_info.value.details
        assert "List A" in exc_info.value.details["available_lists"]
        assert "List B" in exc_info.value.details["available_lists"]

    def test_error_codes_are_unique_and_descriptive(self):
        """Test that different errors have unique, descriptive error codes."""
        error_codes = set()

        # Collect error codes from different scenarios
        task = Task(title="Test", status=TaskStatus.DONE)
        try:
            task.mark_complete()
        except InvalidStateTransitionException as e:
            error_codes.add(e.error_code)

        task_archived = Task.construct(
            title="Test",
            status=TaskStatus.ARCHIVED.value,
            completed_at=datetime.utcnow(),
            priority=Priority.MEDIUM.value
        )
        try:
            task_archived.mark_complete()
        except InvalidStateTransitionException as e:
            error_codes.add(e.error_code)

        # Ensure error codes are unique
        assert len(error_codes) == 2
        assert "ALREADY_COMPLETED" in error_codes
        assert "ARCHIVED_TASK_COMPLETION" in error_codes

    def test_empty_tasklist_filtering_works(self):
        """Test that filtering empty task lists doesn't cause errors."""
        task_list = TaskList(name="Empty", owner="user1", tasks=[])

        assert len(task_list.get_tasks_by_status(TaskStatus.TODO)) == 0
        assert len(task_list.get_tasks_by_priority(Priority.HIGH)) == 0
        assert len(task_list.get_overdue_tasks()) == 0

    def test_tasklist_with_many_tasks_handles_duplicate_correctly(self):
        """Test duplicate detection in list with many tasks."""
        tasks = [Task(id=i, title=f"Task {i}") for i in range(1, 101)]
        duplicate_task = Task(id=50, title="Duplicate of Task 50")

        task_list = TaskList(name="Large List", owner="user1", tasks=tasks)

        with pytest.raises(DuplicateTaskException) as exc_info:
            task_list.add_task(duplicate_task)

        # task_id stored as int in details
        assert exc_info.value.details["task_id"] in [50, "50"]
        assert exc_info.value.details["existing_task_count"] == 100
