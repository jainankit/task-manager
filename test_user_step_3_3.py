"""
Tests for Step 3.3: User method error handling enhancements.

This module tests the error handling for User methods:
- to_dict() with nested serialization error handling
- validate_task_list_ownership() method
- Error handling for operations on inactive users
"""
import pytest
from datetime import datetime

from models import User, TaskList, Task, TaskStatus
from exceptions import (
    SerializationException,
    OwnershipException,
    StateValidationException
)


class TestUserToDictErrorHandling:
    """Test User.to_dict() method with error handling for nested serialization errors."""

    def test_active_user_to_dict_succeeds(self):
        """Test that active user can be converted to dict successfully."""
        user = User(
            username="testuser",
            email="test@example.com",
            is_active=True
        )

        user_dict = user.to_dict()

        assert isinstance(user_dict, dict)
        assert user_dict["username"] == "testuser"
        assert user_dict["email"] == "test@example.com"
        assert user_dict["is_active"] is True

    def test_inactive_user_to_dict_raises_exception(self):
        """Test that inactive user cannot be serialized to dict."""
        user = User(
            username="testuser",
            email="test@example.com",
            is_active=False
        )

        with pytest.raises(StateValidationException) as exc_info:
            user.to_dict()

        assert exc_info.value.error_code == "INACTIVE_USER_OPERATION"
        assert "inactive user" in exc_info.value.message
        assert exc_info.value.details["operation"] == "to_dict"
        assert exc_info.value.details["is_active"] is False
        assert "suggestion" in exc_info.value.details

    def test_active_user_with_task_lists_to_dict(self):
        """Test that active user with task lists can be serialized."""
        task1 = Task(id=1, title="Test Task 1")
        task2 = Task(id=2, title="Test Task 2")
        task_list = TaskList(name="Work", owner="testuser", tasks=[task1, task2])

        user = User(
            username="testuser",
            email="test@example.com",
            is_active=True,
            task_lists=[task_list]
        )

        user_dict = user.to_dict()

        assert isinstance(user_dict, dict)
        assert user_dict["username"] == "testuser"
        assert len(user_dict["task_lists"]) == 1
        assert user_dict["task_lists"][0]["name"] == "Work"

    def test_inactive_user_with_task_lists_raises_exception(self):
        """Test that inactive user with task lists cannot be serialized."""
        task_list = TaskList(name="Work", owner="testuser")
        user = User(
            username="testuser",
            email="test@example.com",
            is_active=False,
            task_lists=[task_list]
        )

        with pytest.raises(StateValidationException) as exc_info:
            user.to_dict()

        assert exc_info.value.error_code == "INACTIVE_USER_OPERATION"
        assert exc_info.value.details["username"] == "testuser"

    def test_to_dict_error_includes_user_context(self):
        """Test that serialization errors include user context information."""
        user = User(
            id=42,
            username="testuser",
            email="test@example.com",
            is_active=False
        )

        with pytest.raises(StateValidationException) as exc_info:
            user.to_dict()

        # Verify context is included
        assert exc_info.value.details["username"] == "testuser"
        assert exc_info.value.details["user_id"] == "42"


class TestValidateTaskListOwnership:
    """Test User.validate_task_list_ownership() method."""

    def test_validate_existing_task_list_succeeds(self):
        """Test that validating an existing task list with correct ownership succeeds."""
        task_list = TaskList(name="Work", owner="testuser")
        user = User(
            username="testuser",
            email="test@example.com",
            task_lists=[task_list]
        )

        # Should not raise any exception
        user.validate_task_list_ownership("Work")

    def test_validate_task_list_case_insensitive(self):
        """Test that task list validation is case-insensitive."""
        task_list = TaskList(name="Work", owner="testuser")
        user = User(
            username="testuser",
            email="test@example.com",
            task_lists=[task_list]
        )

        # Should work with different cases
        user.validate_task_list_ownership("work")
        user.validate_task_list_ownership("WORK")
        user.validate_task_list_ownership("WoRk")

    def test_validate_task_list_with_whitespace(self):
        """Test that task list validation handles whitespace correctly."""
        task_list = TaskList(name="Work", owner="testuser")
        user = User(
            username="testuser",
            email="test@example.com",
            task_lists=[task_list]
        )

        # Should work with whitespace
        user.validate_task_list_ownership("  Work  ")

    def test_validate_nonexistent_task_list_raises_exception(self):
        """Test that validating a non-existent task list raises OwnershipException."""
        task_list = TaskList(name="Work", owner="testuser")
        user = User(
            username="testuser",
            email="test@example.com",
            task_lists=[task_list]
        )

        with pytest.raises(OwnershipException) as exc_info:
            user.validate_task_list_ownership("Personal")

        assert exc_info.value.error_code == "TASKLIST_NOT_FOUND"
        assert "not found" in exc_info.value.message
        assert exc_info.value.details["task_list_name"] == "Personal"
        assert exc_info.value.details["user_id"] == "testuser"
        assert "available_lists" in exc_info.value.details
        assert "Work" in exc_info.value.details["available_lists"]

    def test_validate_task_list_ownership_mismatch_raises_exception(self):
        """Test that validating a task list with wrong owner raises OwnershipException."""
        task_list = TaskList(name="Work", owner="otheruser")
        user = User(
            username="testuser",
            email="test@example.com",
            task_lists=[task_list]
        )

        with pytest.raises(OwnershipException) as exc_info:
            user.validate_task_list_ownership("Work")

        assert exc_info.value.error_code == "TASKLIST_OWNERSHIP_MISMATCH"
        assert "does not belong to" in exc_info.value.message
        assert exc_info.value.details["expected_owner"] == "testuser"
        assert exc_info.value.details["actual_owner"] == "otheruser"
        assert exc_info.value.details["task_list_name"] == "Work"

    def test_validate_empty_task_lists_raises_exception(self):
        """Test that validating when user has no task lists raises OwnershipException."""
        user = User(
            username="testuser",
            email="test@example.com",
            task_lists=[]
        )

        with pytest.raises(OwnershipException) as exc_info:
            user.validate_task_list_ownership("Work")

        assert exc_info.value.error_code == "TASKLIST_NOT_FOUND"
        assert exc_info.value.details["available_lists"] == []

    def test_validate_multiple_task_lists(self):
        """Test validating ownership with multiple task lists."""
        list1 = TaskList(name="Work", owner="testuser")
        list2 = TaskList(name="Personal", owner="testuser")
        list3 = TaskList(name="Shopping", owner="testuser")

        user = User(
            username="testuser",
            email="test@example.com",
            task_lists=[list1, list2, list3]
        )

        # All should succeed
        user.validate_task_list_ownership("Work")
        user.validate_task_list_ownership("Personal")
        user.validate_task_list_ownership("Shopping")

    def test_validate_with_mixed_ownership(self):
        """Test validating when some task lists belong to other users."""
        list1 = TaskList(name="Work", owner="testuser")
        list2 = TaskList(name="Shared", owner="otheruser")
        list3 = TaskList(name="Personal", owner="testuser")

        user = User(
            username="testuser",
            email="test@example.com",
            task_lists=[list1, list2, list3]
        )

        # Should succeed for owned lists
        user.validate_task_list_ownership("Work")
        user.validate_task_list_ownership("Personal")

        # Should fail for other user's list
        with pytest.raises(OwnershipException) as exc_info:
            user.validate_task_list_ownership("Shared")

        assert exc_info.value.error_code == "TASKLIST_OWNERSHIP_MISMATCH"

    def test_validate_ownership_exception_includes_resource_info(self):
        """Test that ownership exception includes correct resource information."""
        user = User(
            username="testuser",
            email="test@example.com",
            task_lists=[]
        )

        with pytest.raises(OwnershipException) as exc_info:
            user.validate_task_list_ownership("Work")

        assert exc_info.value.details["resource_type"] == "task_list"
        assert exc_info.value.details["resource_id"] == "Work"
        assert exc_info.value.details["user_id"] == "testuser"


class TestInactiveUserOperations:
    """Test error handling for operations on inactive users."""

    def test_inactive_user_check_method(self):
        """Test the _check_user_active() method directly."""
        user = User(
            username="testuser",
            email="test@example.com",
            is_active=False
        )

        with pytest.raises(StateValidationException) as exc_info:
            user._check_user_active("test_operation")

        assert exc_info.value.error_code == "INACTIVE_USER_OPERATION"
        assert "inactive user" in exc_info.value.message
        assert exc_info.value.details["operation"] == "test_operation"
        assert exc_info.value.details["is_active"] is False

    def test_active_user_check_passes(self):
        """Test that active user passes the check."""
        user = User(
            username="testuser",
            email="test@example.com",
            is_active=True
        )

        # Should not raise any exception
        user._check_user_active("test_operation")

    def test_inactive_user_to_dict_operation(self):
        """Test that to_dict() checks if user is active."""
        user = User(
            username="testuser",
            email="test@example.com",
            is_active=False
        )

        with pytest.raises(StateValidationException) as exc_info:
            user.to_dict()

        assert exc_info.value.error_code == "INACTIVE_USER_OPERATION"
        assert exc_info.value.details["operation"] == "to_dict"

    def test_inactive_user_exception_includes_suggestion(self):
        """Test that inactive user exception includes helpful suggestion."""
        user = User(
            username="testuser",
            email="test@example.com",
            is_active=False
        )

        with pytest.raises(StateValidationException) as exc_info:
            user.to_dict()

        assert "suggestion" in exc_info.value.details
        assert "activate" in exc_info.value.details["suggestion"].lower()

    def test_inactive_user_exception_includes_state_info(self):
        """Test that inactive user exception includes state information."""
        user = User(
            id=123,
            username="testuser",
            email="test@example.com",
            is_active=False
        )

        with pytest.raises(StateValidationException) as exc_info:
            user._check_user_active("custom_operation")

        assert exc_info.value.details["current_state"] == "inactive"
        assert exc_info.value.details["attempted_state"] == "active"
        assert exc_info.value.details["user_id"] == "123"
        assert exc_info.value.details["username"] == "testuser"


class TestUserMethodErrorHandlingIntegration:
    """Integration tests for User method error handling."""

    def test_active_user_with_tasks_full_workflow(self):
        """Test complete workflow with active user and task lists."""
        task1 = Task(id=1, title="Task 1", status=TaskStatus.TODO)
        task2 = Task(id=2, title="Task 2", status=TaskStatus.DONE)
        task_list = TaskList(name="Work", owner="testuser", tasks=[task1, task2])

        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            is_active=True,
            task_lists=[task_list]
        )

        # Validate ownership
        user.validate_task_list_ownership("Work")

        # Serialize to dict
        user_dict = user.to_dict()

        assert user_dict["is_active"] is True
        assert len(user_dict["task_lists"]) == 1

    def test_inactive_user_prevents_operations(self):
        """Test that inactive user is prevented from operations."""
        task_list = TaskList(name="Work", owner="testuser")
        user = User(
            username="testuser",
            email="test@example.com",
            is_active=False,
            task_lists=[task_list]
        )

        # Ownership validation should still work (doesn't check active status)
        user.validate_task_list_ownership("Work")

        # But serialization should fail
        with pytest.raises(StateValidationException):
            user.to_dict()

    def test_error_messages_include_context(self):
        """Test that all error messages include helpful context."""
        user = User(
            id=42,
            username="testuser",
            email="test@example.com",
            is_active=False,
            task_lists=[]
        )

        # Test inactive user error
        with pytest.raises(StateValidationException) as exc_info:
            user.to_dict()

        assert "user_id" in exc_info.value.details
        assert "username" in exc_info.value.details
        assert "suggestion" in exc_info.value.details

        # Reactivate user for ownership test
        user.is_active = True

        # Test ownership error
        with pytest.raises(OwnershipException) as exc_info:
            user.validate_task_list_ownership("NonExistent")

        assert "user_id" in exc_info.value.details
        assert "available_lists" in exc_info.value.details
        assert "suggestion" in exc_info.value.details


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
