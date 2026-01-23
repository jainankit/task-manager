"""
Tests for Task method error handling (Step 3.1).

Tests the error handling added to Task.mark_complete(), Task.to_dict(),
and Task.to_json() methods.
"""
import json
import pytest
from datetime import datetime
from models import Task, TaskStatus, Priority
from exceptions import InvalidStateTransitionException, SerializationException


class TestMarkCompleteErrorHandling:
    """Test error handling in mark_complete() method."""

    def test_mark_complete_when_already_completed(self):
        """Test that marking an already completed task raises InvalidStateTransitionException."""
        task = Task(
            title="Test Task",
            status=TaskStatus.DONE,
            completed_at=datetime.utcnow()
        )

        with pytest.raises(InvalidStateTransitionException) as exc_info:
            task.mark_complete()

        assert exc_info.value.error_code == "ALREADY_COMPLETED"
        assert "already marked as complete" in exc_info.value.message
        assert exc_info.value.details["current_status"] == TaskStatus.DONE.value
        assert exc_info.value.details["attempted_status"] == TaskStatus.DONE.value

    def test_mark_complete_when_archived(self):
        """Test that marking an archived task raises InvalidStateTransitionException."""
        # First create a completed task
        task = Task(
            title="Test Task",
            status=TaskStatus.DONE,
            completed_at=datetime.utcnow()
        )
        # Then manually set it to archived using copy to bypass validators
        from pydantic import ValidationError
        try:
            # Use copy to create archived version
            task = task.copy(update={"status": TaskStatus.ARCHIVED})
        except ValidationError:
            # If validation fails, create it directly with construct (bypasses validation)
            task = Task.construct(
                title="Test Task",
                status=TaskStatus.ARCHIVED.value,
                completed_at=datetime.utcnow(),
                priority=Priority.MEDIUM.value
            )

        with pytest.raises(InvalidStateTransitionException) as exc_info:
            task.mark_complete()

        assert exc_info.value.error_code == "ARCHIVED_TASK_COMPLETION"
        assert "Cannot mark archived tasks as complete" in exc_info.value.message
        assert exc_info.value.details["current_status"] == TaskStatus.ARCHIVED.value
        assert exc_info.value.details["attempted_status"] == TaskStatus.DONE.value
        assert "Restore the task from archive" in exc_info.value.details["suggestion"]

    def test_mark_complete_success_from_todo(self):
        """Test successful completion from TODO status."""
        task = Task(title="Test Task", status=TaskStatus.TODO)

        completed_task = task.mark_complete()

        assert completed_task.status == TaskStatus.DONE
        assert completed_task.completed_at is not None

    def test_mark_complete_success_from_in_progress(self):
        """Test successful completion from IN_PROGRESS status."""
        task = Task(title="Test Task", status=TaskStatus.IN_PROGRESS)

        completed_task = task.mark_complete()

        assert completed_task.status == TaskStatus.DONE
        assert completed_task.completed_at is not None

    def test_mark_complete_error_details_include_task_info(self):
        """Test that error includes task ID and title."""
        task = Task(id=123, title="Important Task", status=TaskStatus.DONE)

        with pytest.raises(InvalidStateTransitionException) as exc_info:
            task.mark_complete()

        assert exc_info.value.details["task_id"] == "123"
        assert exc_info.value.details["task_title"] == "Important Task"


class TestToDictErrorHandling:
    """Test error handling in to_dict() method."""

    def test_to_dict_success(self):
        """Test successful conversion to dictionary."""
        task = Task(title="Test Task", priority=Priority.HIGH)

        result = task.to_dict()

        assert isinstance(result, dict)
        assert result["title"] == "Test Task"
        assert result["priority"] == Priority.HIGH.value

    def test_to_dict_with_all_fields(self):
        """Test conversion with all fields populated."""
        task = Task(
            id=1,
            title="Complete Task",
            description="A test task",
            status=TaskStatus.DONE,
            priority=Priority.CRITICAL,
            completed_at=datetime.utcnow()
        )

        result = task.to_dict()

        assert result["id"] == 1
        assert result["title"] == "Complete Task"
        assert result["description"] == "A test task"
        assert result["status"] == TaskStatus.DONE.value
        assert result["priority"] == Priority.CRITICAL.value
        assert "completed_at" in result


class TestToJsonErrorHandling:
    """Test error handling in to_json() method."""

    def test_to_json_success(self):
        """Test successful conversion to JSON string."""
        task = Task(title="Test Task", priority=Priority.MEDIUM)

        result = task.to_json()

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["title"] == "Test Task"
        assert parsed["priority"] == Priority.MEDIUM.value

    def test_to_json_with_complete_task(self):
        """Test JSON conversion of a completed task."""
        task = Task(
            id=42,
            title="Done Task",
            status=TaskStatus.DONE,
            completed_at=datetime.utcnow()
        )

        result = task.to_json()

        parsed = json.loads(result)
        assert parsed["id"] == 42
        assert parsed["title"] == "Done Task"
        assert parsed["status"] == TaskStatus.DONE.value
        assert "completed_at" in parsed

    def test_to_json_is_valid_json(self):
        """Test that the output is valid JSON that can be parsed."""
        task = Task(
            title="Test Task",
            description="With various fields",
            priority=Priority.LOW,
            status=TaskStatus.IN_PROGRESS
        )

        json_str = task.to_json()

        # Should not raise an exception
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)


class TestTaskStatePrevention:
    """Test that invalid states are prevented."""

    def test_cannot_mark_archived_task_complete(self):
        """Verify archived tasks cannot be marked complete."""
        # Use construct to bypass validators for archived task
        task = Task.construct(
            title="Archived Task",
            status=TaskStatus.ARCHIVED.value,
            completed_at=datetime.utcnow(),
            priority=Priority.MEDIUM.value
        )

        with pytest.raises(InvalidStateTransitionException) as exc_info:
            task.mark_complete()

        assert "archived" in exc_info.value.message.lower()

    def test_idempotency_check_on_mark_complete(self):
        """Verify that marking complete twice raises appropriate error."""
        task = Task(title="Test Task", status=TaskStatus.TODO)

        # First completion should succeed
        completed_task = task.mark_complete()
        assert completed_task.status == TaskStatus.DONE

        # Second completion should fail
        with pytest.raises(InvalidStateTransitionException) as exc_info:
            completed_task.mark_complete()

        assert exc_info.value.error_code == "ALREADY_COMPLETED"


class TestErrorMessageQuality:
    """Test that error messages are helpful and informative."""

    def test_archived_error_includes_suggestion(self):
        """Test that archived task error includes helpful suggestion."""
        # Use construct to bypass validators for archived task
        task = Task.construct(
            title="Test",
            status=TaskStatus.ARCHIVED.value,
            completed_at=datetime.utcnow(),
            priority=Priority.MEDIUM.value
        )

        with pytest.raises(InvalidStateTransitionException) as exc_info:
            task.mark_complete()

        suggestion = exc_info.value.details.get("suggestion", "")
        assert "Restore" in suggestion or "restore" in suggestion
        assert "archive" in suggestion.lower()

    def test_already_completed_error_includes_suggestion(self):
        """Test that already completed error includes helpful suggestion."""
        task = Task(title="Test", status=TaskStatus.DONE)

        with pytest.raises(InvalidStateTransitionException) as exc_info:
            task.mark_complete()

        suggestion = exc_info.value.details.get("suggestion", "")
        assert "already" in suggestion.lower() or "DONE" in suggestion

    def test_error_codes_are_unique(self):
        """Test that different errors have different error codes."""
        # Use construct to bypass validators for archived task
        archived_task = Task.construct(
            title="Archived",
            status=TaskStatus.ARCHIVED.value,
            completed_at=datetime.utcnow(),
            priority=Priority.MEDIUM.value
        )
        done_task = Task(title="Done", status=TaskStatus.DONE)

        # Get error codes
        try:
            archived_task.mark_complete()
        except InvalidStateTransitionException as e:
            archived_code = e.error_code

        try:
            done_task.mark_complete()
        except InvalidStateTransitionException as e:
            done_code = e.error_code

        # They should be different
        assert archived_code != done_code
        assert archived_code == "ARCHIVED_TASK_COMPLETION"
        assert done_code == "ALREADY_COMPLETED"
