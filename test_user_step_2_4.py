"""
Tests for Step 2.4: User model validator enhancements.

This module tests the enhanced validators for the User model:
- Username format validation with custom exceptions
- Email validation with detailed error messages
- Duplicate task list name prevention
"""
import pytest
from pydantic import ValidationError

from models import User, TaskList, Task
from exceptions import FieldValidationException


class TestUsernameValidation:
    """Test username validation with enhanced error messages."""

    def test_valid_username(self):
        """Test that valid usernames are accepted."""
        valid_usernames = [
            "john_doe",
            "user123",
            "my_username",
            "JohnDoe",
            "user_123_test",
            "abc",
            "a" * 50  # max length
        ]

        for username in valid_usernames:
            user = User(username=username, email="test@example.com")
            assert user.username == username.strip()

    def test_username_with_spaces_raises_exception(self):
        """Test that username with spaces raises FieldValidationException."""
        with pytest.raises(FieldValidationException) as exc_info:
            User(username="john doe", email="test@example.com")

        assert exc_info.value.error_code == "USERNAME_INVALID_FORMAT"
        assert exc_info.value.field_name == "username"
        assert "can only contain letters, numbers, and underscores" in exc_info.value.message
        assert " " in exc_info.value.details["invalid_characters"]

    def test_username_with_special_characters_raises_exception(self):
        """Test that username with special characters raises FieldValidationException."""
        invalid_usernames = [
            "john@doe",
            "user#123",
            "my-username",
            "user.name",
            "john!doe"
        ]

        for username in invalid_usernames:
            with pytest.raises(FieldValidationException) as exc_info:
                User(username=username, email="test@example.com")

            assert exc_info.value.error_code == "USERNAME_INVALID_FORMAT"
            assert exc_info.value.field_name == "username"
            assert "allowed_characters" in exc_info.value.details
            assert "invalid_characters" in exc_info.value.details

    def test_username_empty_raises_exception(self):
        """Test that empty username raises validation error (caught by Pydantic min_length)."""
        # Empty string is caught by Pydantic's min_length=3 before reaching our validator
        with pytest.raises((ValidationError, FieldValidationException)):
            User(username="", email="test@example.com")

    def test_username_whitespace_only_raises_exception(self):
        """Test that whitespace-only username raises FieldValidationException."""
        with pytest.raises(FieldValidationException) as exc_info:
            User(username="   ", email="test@example.com")

        assert exc_info.value.error_code == "USERNAME_EMPTY"
        assert exc_info.value.field_name == "username"

    def test_username_error_includes_examples(self):
        """Test that username validation error includes helpful examples."""
        with pytest.raises(FieldValidationException) as exc_info:
            User(username="user-name", email="test@example.com")

        assert "examples" in exc_info.value.details
        assert "suggestion" in exc_info.value.details


class TestEmailValidation:
    """Test email validation with enhanced error messages."""

    def test_valid_email(self):
        """Test that valid email addresses are accepted and normalized to lowercase."""
        valid_emails = [
            "john@example.com",
            "USER@EXAMPLE.COM",
            "user.name@company.org",
            "test_user@mail.co.uk",
            "user123@test-domain.com"
        ]

        for email in valid_emails:
            user = User(username="testuser", email=email)
            assert user.email == email.lower().strip()

    def test_email_missing_at_symbol(self):
        """Test that email without @ symbol raises specific exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            User(username="testuser", email="userexample.com")

        assert exc_info.value.error_code == "EMAIL_MISSING_AT_SYMBOL"
        assert exc_info.value.field_name == "email"
        assert "must contain @ symbol" in exc_info.value.message
        assert "expected_format" in exc_info.value.details

    def test_email_multiple_at_symbols(self):
        """Test that email with multiple @ symbols raises specific exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            User(username="testuser", email="user@example@com")

        assert exc_info.value.error_code == "EMAIL_MULTIPLE_AT_SYMBOLS"
        assert exc_info.value.field_name == "email"
        assert "at_symbol_count" in exc_info.value.details

    def test_email_empty_local_part(self):
        """Test that email with empty username raises specific exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            User(username="testuser", email="@example.com")

        assert exc_info.value.error_code == "EMAIL_EMPTY_LOCAL_PART"
        assert exc_info.value.field_name == "email"
        assert "username before @ symbol" in exc_info.value.message

    def test_email_empty_domain(self):
        """Test that email with empty domain raises specific exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            User(username="testuser", email="user@")

        assert exc_info.value.error_code == "EMAIL_EMPTY_DOMAIN"
        assert exc_info.value.field_name == "email"
        assert "domain after @ symbol" in exc_info.value.message

    def test_email_missing_tld(self):
        """Test that email without domain extension raises specific exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            User(username="testuser", email="user@example")

        assert exc_info.value.error_code == "EMAIL_MISSING_TLD"
        assert exc_info.value.field_name == "email"
        assert "top-level domain" in exc_info.value.message
        assert "domain_provided" in exc_info.value.details
        assert exc_info.value.details["domain_provided"] == "example"

    def test_email_invalid_tld(self):
        """Test that email with invalid TLD raises specific exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            User(username="testuser", email="user@example.c")

        assert exc_info.value.error_code == "EMAIL_INVALID_TLD"
        assert exc_info.value.field_name == "email"
        assert "at least 2 characters" in exc_info.value.message
        assert "tld_provided" in exc_info.value.details

    def test_email_empty_raises_exception(self):
        """Test that empty email raises FieldValidationException."""
        with pytest.raises(FieldValidationException) as exc_info:
            User(username="testuser", email="")

        assert exc_info.value.error_code == "EMAIL_EMPTY"
        assert exc_info.value.field_name == "email"

    def test_email_error_includes_helpful_details(self):
        """Test that email validation errors include helpful details."""
        with pytest.raises(FieldValidationException) as exc_info:
            User(username="testuser", email="invalid-email")

        assert "expected_format" in exc_info.value.details
        assert "suggestion" in exc_info.value.details


class TestTaskListDuplicateNames:
    """Test validation of duplicate task list names per user."""

    def test_user_with_unique_task_list_names(self):
        """Test that user with unique task list names is valid."""
        list1 = TaskList(name="Work", owner="user1")
        list2 = TaskList(name="Personal", owner="user1")
        list3 = TaskList(name="Shopping", owner="user1")

        user = User(
            username="testuser",
            email="test@example.com",
            task_lists=[list1, list2, list3]
        )

        assert len(user.task_lists) == 3

    def test_user_with_duplicate_task_list_names_raises_exception(self):
        """Test that duplicate task list names raise FieldValidationException."""
        list1 = TaskList(name="Work", owner="user1")
        list2 = TaskList(name="Personal", owner="user1")
        list3 = TaskList(name="Work", owner="user1")  # Duplicate

        with pytest.raises(FieldValidationException) as exc_info:
            User(
                username="testuser",
                email="test@example.com",
                task_lists=[list1, list2, list3]
            )

        assert exc_info.value.error_code == "DUPLICATE_TASKLIST_NAMES"
        assert exc_info.value.field_name == "task_lists"
        assert "Work" in exc_info.value.details["duplicate_names"]

    def test_user_with_case_insensitive_duplicate_names(self):
        """Test that duplicate names are detected case-insensitively."""
        list1 = TaskList(name="Work", owner="user1")
        list2 = TaskList(name="WORK", owner="user1")  # Case variation
        list3 = TaskList(name="work", owner="user1")  # Another case variation

        with pytest.raises(FieldValidationException) as exc_info:
            User(
                username="testuser",
                email="test@example.com",
                task_lists=[list1, list2, list3]
            )

        assert exc_info.value.error_code == "DUPLICATE_TASKLIST_NAMES"
        assert exc_info.value.field_name == "task_lists"
        # Should include at least some of the duplicate names
        assert len(exc_info.value.details["duplicate_names"]) > 0
        assert "comparison" in exc_info.value.details
        assert exc_info.value.details["comparison"] == "case-insensitive"

    def test_user_with_multiple_duplicate_names(self):
        """Test detection of multiple sets of duplicate names."""
        list1 = TaskList(name="Work", owner="user1")
        list2 = TaskList(name="Work", owner="user1")  # Duplicate
        list3 = TaskList(name="Personal", owner="user1")
        list4 = TaskList(name="Personal", owner="user1")  # Duplicate

        with pytest.raises(FieldValidationException) as exc_info:
            User(
                username="testuser",
                email="test@example.com",
                task_lists=[list1, list2, list3, list4]
            )

        assert exc_info.value.error_code == "DUPLICATE_TASKLIST_NAMES"
        assert "Work" in exc_info.value.details["duplicate_names"]
        assert "Personal" in exc_info.value.details["duplicate_names"]

    def test_empty_task_lists_is_valid(self):
        """Test that user with no task lists is valid."""
        user = User(username="testuser", email="test@example.com", task_lists=[])
        assert len(user.task_lists) == 0

    def test_task_list_duplicate_error_includes_helpful_details(self):
        """Test that duplicate task list error includes helpful details."""
        list1 = TaskList(name="Work", owner="user1")
        list2 = TaskList(name="Work", owner="user1")

        with pytest.raises(FieldValidationException) as exc_info:
            User(
                username="testuser",
                email="test@example.com",
                task_lists=[list1, list2]
            )

        assert "total_lists" in exc_info.value.details
        assert "unique_names" in exc_info.value.details
        assert "suggestion" in exc_info.value.details


class TestUserModelIntegration:
    """Integration tests for User model with all validators."""

    def test_create_complete_valid_user(self):
        """Test creating a user with all valid fields."""
        task1 = Task(id=1, title="Task 1")
        task2 = Task(id=2, title="Task 2")
        list1 = TaskList(name="Work", owner="johndoe", tasks=[task1])
        list2 = TaskList(name="Personal", owner="johndoe", tasks=[task2])

        user = User(
            id=1,
            username="johndoe",
            email="JOHN@EXAMPLE.COM",
            full_name="John Doe",
            is_active=True,
            task_lists=[list1, list2]
        )

        assert user.username == "johndoe"
        assert user.email == "john@example.com"  # Should be lowercase
        assert user.full_name == "John Doe"
        assert user.is_active is True
        assert len(user.task_lists) == 2

    def test_user_with_invalid_username_and_email(self):
        """Test that validation catches both username and email errors."""
        # First error caught will be raised (username is validated first)
        with pytest.raises(FieldValidationException) as exc_info:
            User(username="invalid-name", email="invalid-email")

        # Could be either username or email error depending on validation order
        assert exc_info.value.field_name in ["username", "email"]

    def test_user_to_dict_method(self):
        """Test that to_dict method works correctly."""
        user = User(username="testuser", email="test@example.com")
        user_dict = user.to_dict()

        assert isinstance(user_dict, dict)
        assert user_dict["username"] == "testuser"
        assert user_dict["email"] == "test@example.com"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
