"""
Tests for Step 3.2: Add error handling to TaskList methods.

This test file verifies that TaskList methods have proper error handling:
- add_task() checks for duplicate task IDs
- get_tasks_by_status() handles invalid status values
- get_tasks_by_priority() handles invalid priority values
- get_overdue_tasks() handles datetime comparison errors
"""
from datetime import datetime, timedelta
import pytest
from models import Task, TaskList, TaskStatus, Priority
from exceptions import (
    DuplicateTaskException,
    FieldValidationException,
    DateValidationException
)


class TestTaskListAddTask:
    """Test add_task() error handling."""

    def test_add_task_with_duplicate_id_raises_exception(self):
        """Test that adding a task with duplicate ID raises DuplicateTaskException."""
        task1 = Task(id=1, title="First task")
        task2 = Task(id=1, title="Second task with same ID")

        task_list = TaskList(name="My List", owner="user1", tasks=[task1])

        with pytest.raises(DuplicateTaskException) as exc_info:
            task_list.add_task(task2)

        assert exc_info.value.error_code == "DUPLICATE_TASK_IN_ADD"
        assert "already exists" in str(exc_info.value)
        # Note: task_id is stored as string in DuplicateTaskException.details
        assert exc_info.value.details["task_id"] == "1"

    def test_add_task_without_id_succeeds(self):
        """Test that adding tasks without IDs works fine."""
        task1 = Task(title="Task without ID")
        task2 = Task(title="Another task without ID")

        task_list = TaskList(name="My List", owner="user1", tasks=[task1])
        updated_list = task_list.add_task(task2)

        assert len(updated_list.tasks) == 2

    def test_add_task_with_unique_ids_succeeds(self):
        """Test that adding tasks with unique IDs works fine."""
        task1 = Task(id=1, title="First task")
        task2 = Task(id=2, title="Second task")

        task_list = TaskList(name="My List", owner="user1", tasks=[task1])
        updated_list = task_list.add_task(task2)

        assert len(updated_list.tasks) == 2

    def test_add_task_exception_includes_helpful_details(self):
        """Test that duplicate task exception includes helpful details."""
        task1 = Task(id=42, title="Original task")
        task2 = Task(id=42, title="Duplicate task")

        task_list = TaskList(name="My List", owner="user1", tasks=[task1])

        with pytest.raises(DuplicateTaskException) as exc_info:
            task_list.add_task(task2)

        assert "suggestion" in exc_info.value.details
        assert "unique task ID" in exc_info.value.details["suggestion"]
        assert exc_info.value.details["task_title"] == "Duplicate task"


class TestTaskListGetTasksByStatus:
    """Test get_tasks_by_status() error handling."""

    def test_get_tasks_by_status_with_valid_enum(self):
        """Test that filtering by valid TaskStatus enum works."""
        task1 = Task(id=1, title="Todo task", status=TaskStatus.TODO)
        task2 = Task(id=2, title="Done task", status=TaskStatus.DONE)

        task_list = TaskList(name="My List", owner="user1", tasks=[task1, task2])

        todo_tasks = task_list.get_tasks_by_status(TaskStatus.TODO)
        assert len(todo_tasks) == 1
        assert todo_tasks[0].title == "Todo task"

    def test_get_tasks_by_status_with_valid_string(self):
        """Test that filtering by valid status string works."""
        task1 = Task(id=1, title="Todo task", status=TaskStatus.TODO)
        task2 = Task(id=2, title="Done task", status=TaskStatus.DONE)

        task_list = TaskList(name="My List", owner="user1", tasks=[task1, task2])

        todo_tasks = task_list.get_tasks_by_status("todo")
        assert len(todo_tasks) == 1
        assert todo_tasks[0].title == "Todo task"

    def test_get_tasks_by_status_with_invalid_string_raises_exception(self):
        """Test that filtering by invalid status string raises FieldValidationException."""
        task_list = TaskList(name="My List", owner="user1", tasks=[])

        with pytest.raises(FieldValidationException) as exc_info:
            task_list.get_tasks_by_status("invalid_status")

        assert exc_info.value.error_code == "INVALID_STATUS_VALUE"
        assert exc_info.value.field_name == "status"
        assert "invalid_status" in str(exc_info.value)

    def test_get_tasks_by_status_exception_includes_valid_values(self):
        """Test that invalid status exception includes valid status values."""
        task_list = TaskList(name="My List", owner="user1", tasks=[])

        with pytest.raises(FieldValidationException) as exc_info:
            task_list.get_tasks_by_status("bad_status")

        assert "valid_statuses" in exc_info.value.details
        valid_statuses = exc_info.value.details["valid_statuses"]
        assert "todo" in valid_statuses
        assert "done" in valid_statuses
        assert "in_progress" in valid_statuses
        assert "archived" in valid_statuses


class TestTaskListGetTasksByPriority:
    """Test get_tasks_by_priority() error handling."""

    def test_get_tasks_by_priority_with_valid_enum(self):
        """Test that filtering by valid Priority enum works."""
        task1 = Task(id=1, title="High priority", priority=Priority.HIGH)
        task2 = Task(id=2, title="Low priority", priority=Priority.LOW)

        task_list = TaskList(name="My List", owner="user1", tasks=[task1, task2])

        high_tasks = task_list.get_tasks_by_priority(Priority.HIGH)
        assert len(high_tasks) == 1
        assert high_tasks[0].title == "High priority"

    def test_get_tasks_by_priority_with_valid_string(self):
        """Test that filtering by valid priority string works."""
        task1 = Task(id=1, title="High priority", priority=Priority.HIGH)
        task2 = Task(id=2, title="Low priority", priority=Priority.LOW)

        task_list = TaskList(name="My List", owner="user1", tasks=[task1, task2])

        high_tasks = task_list.get_tasks_by_priority("high")
        assert len(high_tasks) == 1
        assert high_tasks[0].title == "High priority"

    def test_get_tasks_by_priority_with_invalid_string_raises_exception(self):
        """Test that filtering by invalid priority string raises FieldValidationException."""
        task_list = TaskList(name="My List", owner="user1", tasks=[])

        with pytest.raises(FieldValidationException) as exc_info:
            task_list.get_tasks_by_priority("invalid_priority")

        assert exc_info.value.error_code == "INVALID_PRIORITY_VALUE"
        assert exc_info.value.field_name == "priority"
        assert "invalid_priority" in str(exc_info.value)

    def test_get_tasks_by_priority_exception_includes_valid_values(self):
        """Test that invalid priority exception includes valid priority values."""
        task_list = TaskList(name="My List", owner="user1", tasks=[])

        with pytest.raises(FieldValidationException) as exc_info:
            task_list.get_tasks_by_priority("bad_priority")

        assert "valid_priorities" in exc_info.value.details
        valid_priorities = exc_info.value.details["valid_priorities"]
        assert "low" in valid_priorities
        assert "medium" in valid_priorities
        assert "high" in valid_priorities
        assert "critical" in valid_priorities


class TestTaskListGetOverdueTasks:
    """Test get_overdue_tasks() error handling."""

    def test_get_overdue_tasks_with_valid_dates(self):
        """Test that getting overdue tasks works with valid dates."""
        past = datetime.utcnow() - timedelta(days=1)
        future = datetime.utcnow() + timedelta(days=1)

        task1 = Task(id=1, title="Overdue task", due_date=past, status=TaskStatus.TODO)
        task2 = Task(id=2, title="Future task", due_date=future, status=TaskStatus.TODO)
        task3 = Task(id=3, title="No due date", status=TaskStatus.TODO)

        task_list = TaskList(name="My List", owner="user1", tasks=[task1, task2, task3])

        overdue = task_list.get_overdue_tasks()
        assert len(overdue) == 1
        assert overdue[0].title == "Overdue task"

    def test_get_overdue_tasks_excludes_completed(self):
        """Test that completed tasks are not included in overdue list."""
        past = datetime.utcnow() - timedelta(days=1)

        task1 = Task(id=1, title="Overdue but done", due_date=past, status=TaskStatus.DONE)
        task2 = Task(id=2, title="Overdue and not done", due_date=past, status=TaskStatus.TODO)

        task_list = TaskList(name="My List", owner="user1", tasks=[task1, task2])

        overdue = task_list.get_overdue_tasks()
        assert len(overdue) == 1
        assert overdue[0].title == "Overdue and not done"

    def test_get_overdue_tasks_handles_none_due_dates(self):
        """Test that tasks without due dates don't cause errors."""
        task1 = Task(id=1, title="No due date", status=TaskStatus.TODO)
        task2 = Task(id=2, title="Another no due date", status=TaskStatus.IN_PROGRESS)

        task_list = TaskList(name="My List", owner="user1", tasks=[task1, task2])

        overdue = task_list.get_overdue_tasks()
        assert len(overdue) == 0

    def test_get_overdue_tasks_with_empty_list(self):
        """Test that getting overdue tasks from empty list works."""
        task_list = TaskList(name="My List", owner="user1", tasks=[])

        overdue = task_list.get_overdue_tasks()
        assert len(overdue) == 0


class TestTaskListMethodIntegration:
    """Integration tests for TaskList methods with error handling."""

    def test_add_multiple_tasks_with_error_handling(self):
        """Test adding multiple tasks with proper error handling."""
        task_list = TaskList(name="My List", owner="user1", tasks=[])

        # Add first task successfully
        task1 = Task(id=1, title="Task 1")
        task_list = task_list.add_task(task1)
        assert len(task_list.tasks) == 1

        # Add second task successfully
        task2 = Task(id=2, title="Task 2")
        task_list = task_list.add_task(task2)
        assert len(task_list.tasks) == 2

        # Try to add duplicate - should fail
        task_duplicate = Task(id=1, title="Duplicate")
        with pytest.raises(DuplicateTaskException):
            task_list.add_task(task_duplicate)

        # Original list should still have 2 tasks
        assert len(task_list.tasks) == 2

    def test_filter_and_add_workflow(self):
        """Test a workflow combining filtering and adding tasks."""
        task1 = Task(id=1, title="High priority todo", priority=Priority.HIGH, status=TaskStatus.TODO)
        task2 = Task(id=2, title="Low priority done", priority=Priority.LOW, status=TaskStatus.DONE)

        task_list = TaskList(name="My List", owner="user1", tasks=[task1, task2])

        # Filter by priority
        high_tasks = task_list.get_tasks_by_priority(Priority.HIGH)
        assert len(high_tasks) == 1

        # Filter by status
        todo_tasks = task_list.get_tasks_by_status(TaskStatus.TODO)
        assert len(todo_tasks) == 1

        # Add a new task
        task3 = Task(id=3, title="New critical task", priority=Priority.CRITICAL, status=TaskStatus.TODO)
        task_list = task_list.add_task(task3)

        # Filter again
        critical_tasks = task_list.get_tasks_by_priority(Priority.CRITICAL)
        assert len(critical_tasks) == 1
        assert critical_tasks[0].title == "New critical task"
