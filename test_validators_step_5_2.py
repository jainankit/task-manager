"""
Tests for Step 5.2: Enhanced Validator Testing.

This module tests that validators raise appropriate custom exceptions,
include field names and invalid values in error messages, provide helpful
suggestions, and handle edge cases properly.
"""
import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from models import Task, TaskList, Tag, User, Priority, TaskStatus
from exceptions import (
    FieldValidationException,
    DateValidationException,
    DuplicateTaskException,
    StateValidationException
)


class TestTagValidatorExceptions:
    """Test that Tag validators raise appropriate custom exceptions."""

    def test_tag_name_empty_raises_field_validation_exception(self):
        """Test that empty tag name raises FieldValidationException with details."""
        with pytest.raises(FieldValidationException) as exc_info:
            Tag(name="   ")

        # Verify exception type and fields
        assert exc_info.value.error_code == "TAG_NAME_EMPTY"
        assert exc_info.value.field_name == "name"
        assert "cannot be empty" in exc_info.value.message.lower()

        # Verify error message contains field name
        assert "name" in str(exc_info.value).lower()

        # Verify helpful suggestion is provided
        assert "suggestion" in exc_info.value.details
        assert len(exc_info.value.details["suggestion"]) > 0

    def test_tag_color_invalid_format_raises_field_validation_exception(self):
        """Test that invalid color format raises FieldValidationException with format details."""
        invalid_colors = ["red", "FF0000", "#FFF", "#GGGGGG", "123456", "#12345"]

        for invalid_color in invalid_colors:
            with pytest.raises(FieldValidationException) as exc_info:
                Tag(name="test", color=invalid_color)

            # Verify exception type and fields
            assert exc_info.value.error_code == "TAG_COLOR_INVALID_FORMAT"
            assert exc_info.value.field_name == "color"
            assert "hex format" in exc_info.value.message.lower()

            # Verify invalid value is included
            assert "invalid_value" in exc_info.value.details
            assert exc_info.value.details["invalid_value"] == invalid_color

            # Verify helpful context is provided
            assert "expected_format" in exc_info.value.details
            assert "examples" in exc_info.value.details
            assert "#RRGGBB" in exc_info.value.details["expected_format"]

    def test_tag_color_empty_raises_field_validation_exception(self):
        """Test that empty color raises FieldValidationException with helpful message."""
        with pytest.raises(FieldValidationException) as exc_info:
            Tag(name="test", color="")

        assert exc_info.value.error_code == "TAG_COLOR_EMPTY"
        assert exc_info.value.field_name == "color"
        assert "expected_format" in exc_info.value.details
        assert "examples" in exc_info.value.details

    def test_tag_color_validation_includes_helpful_examples(self):
        """Test that color validation errors include examples of valid colors."""
        with pytest.raises(FieldValidationException) as exc_info:
            Tag(name="test", color="invalid")

        examples = exc_info.value.details.get("examples", "")
        assert "#FF0000" in examples or "red" in examples.lower()

        # Should mention common mistakes
        details_str = str(exc_info.value.details)
        assert "mistake" in details_str.lower() or "format" in details_str.lower()


class TestTaskTitleValidator:
    """Test Task title validator with custom exceptions."""

    def test_title_whitespace_only_raises_field_validation_exception(self):
        """Test that whitespace-only title raises FieldValidationException."""
        with pytest.raises(FieldValidationException) as exc_info:
            Task(title="   ")

        assert exc_info.value.error_code == "TASK_TITLE_EMPTY"
        assert exc_info.value.field_name == "title"
        assert "empty" in exc_info.value.message.lower()
        assert "suggestion" in exc_info.value.details

    def test_title_exception_includes_invalid_value(self):
        """Test that title validation exception includes the invalid value."""
        invalid_title = "    \t\n    "

        with pytest.raises(FieldValidationException) as exc_info:
            Task(title=invalid_title)

        # Invalid value should be in details
        assert "invalid_value" in exc_info.value.details
        assert exc_info.value.details["invalid_value"] == invalid_title

    def test_title_validation_with_extremely_long_string(self):
        """Test title validation with extremely long strings."""
        # Title has max_length=200, so 201 characters should fail
        long_title = "A" * 201

        with pytest.raises(ValidationError):
            Task(title=long_title)

        # 200 characters should succeed
        valid_long_title = "A" * 200
        task = Task(title=valid_long_title)
        assert task.title == valid_long_title

    def test_title_validation_with_special_characters(self):
        """Test that titles with special characters are accepted."""
        special_titles = [
            "Task with emojis 🚀🎉",
            "Task with symbols !@#$%",
            "Task with unicode: café, naïve, 日本語",
            "Task with newlines\nand tabs\t",
            "Task with quotes \"'`"
        ]

        for title in special_titles:
            if len(title) <= 200:  # Within max length
                task = Task(title=title)
                assert task.title == title.strip()


class TestTaskDueDateValidator:
    """Test Task due_date validator with custom exceptions."""

    def test_due_date_far_past_raises_date_validation_exception(self):
        """Test that due date more than 1 year in the past raises DateValidationException."""
        two_years_ago = datetime.utcnow() - timedelta(days=730)

        with pytest.raises(DateValidationException) as exc_info:
            Task(title="Old Task", due_date=two_years_ago)

        assert exc_info.value.error_code == "DUE_DATE_FAR_PAST"
        assert exc_info.value.field_name == "due_date"
        assert "year" in exc_info.value.message.lower()

        # Should include helpful context
        assert "due_date" in exc_info.value.details
        assert "current_time" in exc_info.value.details
        assert "threshold" in exc_info.value.details
        assert "suggestion" in exc_info.value.details

    def test_due_date_validation_includes_invalid_date(self):
        """Test that due date validation includes the invalid date in error details."""
        invalid_date = datetime.utcnow() - timedelta(days=400)

        with pytest.raises(DateValidationException) as exc_info:
            Task(title="Task", due_date=invalid_date)

        # Invalid date should be in details
        assert "invalid_date" in exc_info.value.details
        assert str(invalid_date) in exc_info.value.details["invalid_date"]

    def test_due_date_recent_past_is_allowed(self):
        """Test that due dates within the past year are allowed."""
        six_months_ago = datetime.utcnow() - timedelta(days=180)

        # Should not raise exception
        task = Task(title="Recent Task", due_date=six_months_ago)
        assert task.due_date == six_months_ago

    def test_due_date_validation_context_includes_suggestions(self):
        """Test that due date validation provides helpful suggestions."""
        old_date = datetime.utcnow() - timedelta(days=500)

        with pytest.raises(DateValidationException) as exc_info:
            Task(title="Task", due_date=old_date)

        suggestion = exc_info.value.details.get("suggestion", "")
        assert len(suggestion) > 0
        assert "verify" in suggestion.lower() or "check" in suggestion.lower()


class TestTaskListNameValidator:
    """Test TaskList name validator with custom exceptions."""

    def test_tasklist_name_empty_raises_field_validation_exception(self):
        """Test that empty TaskList name raises FieldValidationException."""
        with pytest.raises(FieldValidationException) as exc_info:
            TaskList(name="   ", owner="user1")

        assert exc_info.value.error_code == "TASKLIST_NAME_EMPTY"
        assert exc_info.value.field_name == "name"
        assert "empty" in exc_info.value.message.lower()
        assert "suggestion" in exc_info.value.details

    def test_tasklist_name_exception_includes_field_name(self):
        """Test that exception includes field name in message."""
        # Empty string will be caught by Pydantic's min_length before our validator
        # So we test with whitespace instead
        with pytest.raises(FieldValidationException) as exc_info:
            TaskList(name="   ", owner="user1")

        # Field name should appear in the string representation
        exc_str = str(exc_info.value)
        assert "name" in exc_str.lower()

    def test_tasklist_name_with_extremely_long_string(self):
        """Test TaskList name validation with extremely long strings."""
        # Name has max_length=100, so 101 characters should fail
        long_name = "A" * 101

        with pytest.raises(ValidationError):
            TaskList(name=long_name, owner="user1")

        # 100 characters should succeed
        valid_long_name = "A" * 100
        tl = TaskList(name=valid_long_name, owner="user1")
        assert tl.name == valid_long_name


class TestTaskListDuplicateTaskIDValidator:
    """Test TaskList duplicate task ID validator."""

    def test_duplicate_task_ids_raises_duplicate_task_exception(self):
        """Test that duplicate task IDs raise DuplicateTaskException."""
        task1 = Task(id=1, title="Task 1")
        task2 = Task(id=2, title="Task 2")
        task3 = Task(id=1, title="Task 3 Duplicate")

        with pytest.raises(DuplicateTaskException) as exc_info:
            TaskList(name="List", owner="user1", tasks=[task1, task2, task3])

        assert exc_info.value.error_code == "DUPLICATE_TASK_IDS_IN_LIST"
        assert "duplicate_ids" in exc_info.value.details
        assert 1 in exc_info.value.details["duplicate_ids"]

    def test_duplicate_task_exception_includes_all_duplicates(self):
        """Test that exception includes all duplicate IDs, not just the first."""
        task1 = Task(id=1, title="Task 1")
        task2 = Task(id=2, title="Task 2")
        task3 = Task(id=1, title="Task 3")
        task4 = Task(id=2, title="Task 4")
        task5 = Task(id=3, title="Task 5")

        with pytest.raises(DuplicateTaskException) as exc_info:
            TaskList(name="List", owner="user1", tasks=[task1, task2, task3, task4, task5])

        duplicates = exc_info.value.details["duplicate_ids"]
        assert 1 in duplicates
        assert 2 in duplicates
        assert 3 not in duplicates  # Not a duplicate

    def test_duplicate_task_exception_includes_helpful_details(self):
        """Test that duplicate task exception includes helpful context."""
        tasks = [Task(id=1, title=f"Task {i}") for i in range(3)]

        with pytest.raises(DuplicateTaskException) as exc_info:
            TaskList(name="List", owner="user1", tasks=tasks)

        details = exc_info.value.details
        assert "total_tasks" in details
        assert "unique_ids" in details
        assert "suggestion" in details
        assert details["total_tasks"] == 3
        assert details["unique_ids"] == 1  # Only 1 unique ID


class TestUserUsernameValidator:
    """Test User username validator with custom exceptions."""

    def test_username_with_spaces_raises_field_validation_exception(self):
        """Test that username with spaces raises FieldValidationException."""
        with pytest.raises(FieldValidationException) as exc_info:
            User(username="john doe", email="john@example.com")

        assert exc_info.value.error_code == "USERNAME_INVALID_FORMAT"
        assert exc_info.value.field_name == "username"
        assert "letters, numbers, and underscores" in exc_info.value.message

    def test_username_exception_includes_invalid_characters(self):
        """Test that username exception identifies invalid characters."""
        with pytest.raises(FieldValidationException) as exc_info:
            User(username="john@doe", email="john@example.com")

        assert "invalid_characters" in exc_info.value.details
        assert "@" in exc_info.value.details["invalid_characters"]

    def test_username_exception_includes_allowed_characters(self):
        """Test that username exception lists allowed characters."""
        with pytest.raises(FieldValidationException) as exc_info:
            User(username="john-doe", email="john@example.com")

        assert "allowed_characters" in exc_info.value.details
        allowed = exc_info.value.details["allowed_characters"]
        assert "a-z" in allowed.lower()
        assert "0-9" in allowed or "number" in allowed.lower()
        assert "_" in allowed or "underscore" in allowed.lower()

    def test_username_exception_includes_examples(self):
        """Test that username exception provides examples of valid usernames."""
        with pytest.raises(FieldValidationException) as exc_info:
            User(username="john.doe", email="john@example.com")

        assert "examples" in exc_info.value.details
        examples = exc_info.value.details["examples"]
        assert len(examples) > 0

    def test_username_with_multiple_special_characters(self):
        """Test username validation with multiple special characters."""
        invalid_usernames = [
            "john@doe!",
            "user#$%",
            "test user-name",
            "user.name@domain",
            "spaces are bad"
        ]

        for invalid_username in invalid_usernames:
            with pytest.raises(FieldValidationException) as exc_info:
                User(username=invalid_username, email="test@example.com")

            assert exc_info.value.error_code == "USERNAME_INVALID_FORMAT"
            assert "invalid_characters" in exc_info.value.details
            # Should identify multiple invalid characters
            invalid_chars = exc_info.value.details["invalid_characters"]
            assert len(invalid_chars) > 0


class TestUserEmailValidator:
    """Test User email validator with custom exceptions."""

    def test_email_missing_at_symbol_raises_specific_exception(self):
        """Test that email without @ raises specific FieldValidationException."""
        with pytest.raises(FieldValidationException) as exc_info:
            User(username="testuser", email="userexample.com")

        assert exc_info.value.error_code == "EMAIL_MISSING_AT_SYMBOL"
        assert exc_info.value.field_name == "email"
        assert "@" in exc_info.value.message

    def test_email_multiple_at_symbols_raises_specific_exception(self):
        """Test that email with multiple @ raises specific exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            User(username="testuser", email="user@@example.com")

        assert exc_info.value.error_code == "EMAIL_MULTIPLE_AT_SYMBOLS"
        assert "at_symbol_count" in exc_info.value.details

    def test_email_missing_domain_raises_specific_exception(self):
        """Test that email without domain raises specific exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            User(username="testuser", email="user@")

        assert exc_info.value.error_code == "EMAIL_EMPTY_DOMAIN"
        assert "domain" in exc_info.value.message.lower()

    def test_email_missing_username_raises_specific_exception(self):
        """Test that email without username raises specific exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            User(username="testuser", email="@example.com")

        assert exc_info.value.error_code == "EMAIL_EMPTY_LOCAL_PART"
        assert "username" in exc_info.value.message.lower()

    def test_email_missing_tld_raises_specific_exception(self):
        """Test that email without TLD raises specific exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            User(username="testuser", email="user@example")

        assert exc_info.value.error_code == "EMAIL_MISSING_TLD"
        assert "top-level domain" in exc_info.value.message.lower()
        assert "domain_provided" in exc_info.value.details

    def test_email_invalid_tld_raises_specific_exception(self):
        """Test that email with invalid TLD raises specific exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            User(username="testuser", email="user@example.c")

        assert exc_info.value.error_code == "EMAIL_INVALID_TLD"
        assert "tld_provided" in exc_info.value.details
        assert exc_info.value.details["tld_provided"] == "c"

    def test_email_validation_includes_format_examples(self):
        """Test that email validation errors include format examples."""
        with pytest.raises(FieldValidationException) as exc_info:
            User(username="testuser", email="invalid")

        assert "expected_format" in exc_info.value.details
        assert "examples" in exc_info.value.details
        examples = exc_info.value.details["examples"]
        assert "@" in examples and ".com" in examples

    def test_email_with_special_characters_in_domain(self):
        """Test email validation with special characters."""
        invalid_emails = [
            "user@exa mple.com",
            "user@example!.com",
            "user@[example].com",
            "user@exam ple.com"
        ]

        for invalid_email in invalid_emails:
            with pytest.raises(FieldValidationException) as exc_info:
                User(username="testuser", email=invalid_email)

            # Should raise some kind of validation error
            assert exc_info.value.field_name == "email"


class TestUserTaskListDuplicateNameValidator:
    """Test User task list duplicate name validator."""

    def test_duplicate_task_list_names_raises_field_validation_exception(self):
        """Test that duplicate task list names raise FieldValidationException."""
        list1 = TaskList(name="Work", owner="user1")
        list2 = TaskList(name="Personal", owner="user1")
        list3 = TaskList(name="Work", owner="user1")

        with pytest.raises(FieldValidationException) as exc_info:
            User(
                username="testuser",
                email="test@example.com",
                task_lists=[list1, list2, list3]
            )

        assert exc_info.value.error_code == "DUPLICATE_TASKLIST_NAMES"
        assert exc_info.value.field_name == "task_lists"
        assert "duplicate_names" in exc_info.value.details

    def test_case_insensitive_duplicate_detection(self):
        """Test that duplicate names are detected case-insensitively."""
        list1 = TaskList(name="Work", owner="user1")
        list2 = TaskList(name="WORK", owner="user1")
        list3 = TaskList(name="work", owner="user1")

        with pytest.raises(FieldValidationException) as exc_info:
            User(
                username="testuser",
                email="test@example.com",
                task_lists=[list1, list2, list3]
            )

        assert "comparison" in exc_info.value.details
        assert exc_info.value.details["comparison"] == "case-insensitive"

    def test_duplicate_names_exception_includes_list_counts(self):
        """Test that duplicate exception includes helpful counts."""
        lists = [
            TaskList(name="Work", owner="user1"),
            TaskList(name="Work", owner="user1"),
            TaskList(name="Personal", owner="user1")
        ]

        with pytest.raises(FieldValidationException) as exc_info:
            User(username="testuser", email="test@example.com", task_lists=lists)

        details = exc_info.value.details
        assert "total_lists" in details
        assert "unique_names" in details
        assert details["total_lists"] == 3
        assert details["unique_names"] == 2


class TestValidatorEdgeCases:
    """Test validators with edge cases and boundary conditions."""

    def test_tag_name_with_unicode_characters(self):
        """Test tag name with unicode characters."""
        unicode_names = ["café", "日本語", "emoji🚀", "Ñoño", "привет"]

        for name in unicode_names:
            if len(name) <= 50:  # Within max length
                tag = Tag(name=name)
                assert tag.name == name.strip()

    def test_task_title_at_boundary_length(self):
        """Test task title at exact boundary of max length."""
        # Exactly 200 characters should work
        title_200 = "A" * 200
        task = Task(title=title_200)
        assert len(task.title) == 200

        # 201 characters should fail
        title_201 = "A" * 201
        with pytest.raises(ValidationError):
            Task(title=title_201)

    def test_task_description_at_boundary_length(self):
        """Test task description at exact boundary of max length."""
        # Exactly 2000 characters should work
        desc_2000 = "A" * 2000
        task = Task(title="Test", description=desc_2000)
        assert len(task.description) == 2000

        # 2001 characters should fail
        desc_2001 = "A" * 2001
        with pytest.raises(ValidationError):
            Task(title="Test", description=desc_2001)

    def test_tasklist_name_at_boundary_length(self):
        """Test TaskList name at exact boundary of max length."""
        # Exactly 100 characters should work
        name_100 = "A" * 100
        tl = TaskList(name=name_100, owner="user1")
        assert len(tl.name) == 100

        # 101 characters should fail
        name_101 = "A" * 101
        with pytest.raises(ValidationError):
            TaskList(name=name_101, owner="user1")

    def test_username_at_boundary_length(self):
        """Test username at exact boundary lengths."""
        # Exactly 3 characters (minimum) should work
        user_3 = User(username="abc", email="test@example.com")
        assert len(user_3.username) == 3

        # Exactly 50 characters (maximum) should work
        username_50 = "a" * 50
        user_50 = User(username=username_50, email="test@example.com")
        assert len(user_50.username) == 50

        # 51 characters should fail
        username_51 = "a" * 51
        with pytest.raises(ValidationError):
            User(username=username_51, email="test@example.com")

    def test_tag_color_case_normalization(self):
        """Test that tag colors are normalized to uppercase."""
        tag = Tag(name="test", color="#ff0000")
        assert tag.color == "#FF0000"

        tag2 = Tag(name="test", color="#AbCdEf")
        assert tag2.color == "#ABCDEF"

    def test_email_case_normalization(self):
        """Test that emails are normalized to lowercase."""
        user = User(username="testuser", email="Test@EXAMPLE.COM")
        assert user.email == "test@example.com"

    def test_whitespace_trimming_in_all_string_fields(self):
        """Test that string fields properly trim whitespace."""
        # Tag name
        tag = Tag(name="  test  ")
        assert tag.name == "test"

        # Task title
        task = Task(title="  My Task  ")
        assert task.title == "My Task"

        # TaskList name
        tl = TaskList(name="  My List  ", owner="user1")
        assert tl.name == "My List"

        # Username - has validation that rejects spaces, so can't have leading/trailing spaces
        # Only test with valid username (no spaces)
        user = User(username="testuser", email="test@example.com")
        assert user.username == "testuser"

    def test_validators_with_none_values_where_optional(self):
        """Test that validators handle None values for optional fields correctly."""
        # Task with no description or due_date
        task = Task(title="Test", description=None, due_date=None)
        assert task.description is None
        assert task.due_date is None

        # User with no full_name
        user = User(username="testuser", email="test@example.com", full_name=None)
        assert user.full_name is None


class TestValidatorErrorMessageQuality:
    """Test the quality and helpfulness of validator error messages."""

    def test_all_field_validation_exceptions_include_field_name(self):
        """Test that all FieldValidationException instances include field_name."""
        test_cases = [
            (lambda: Tag(name="   "), "name"),
            (lambda: Tag(name="test", color="invalid"), "color"),
            (lambda: Task(title="   "), "title"),
            (lambda: TaskList(name="   ", owner="user1"), "name"),
            (lambda: User(username="john doe", email="test@example.com"), "username"),
            (lambda: User(username="testuser", email="invalid"), "email"),
        ]

        for func, expected_field in test_cases:
            with pytest.raises(FieldValidationException) as exc_info:
                func()

            assert exc_info.value.field_name == expected_field
            # Field name should appear in string representation
            assert expected_field in str(exc_info.value).lower()

    def test_all_exceptions_include_error_codes(self):
        """Test that all custom exceptions include error codes."""
        test_cases = [
            lambda: Tag(name="   "),
            lambda: Tag(name="test", color="red"),
            lambda: Task(title="   "),
            lambda: Task(title="Test", due_date=datetime.utcnow() - timedelta(days=500)),
            lambda: TaskList(name="   ", owner="user1"),
            lambda: User(username="john doe", email="test@example.com"),
            lambda: User(username="testuser", email="invalid"),
        ]

        for func in test_cases:
            try:
                func()
                # If no exception is raised, fail the test
                pytest.fail("Expected an exception to be raised")
            except (FieldValidationException, DateValidationException) as e:
                assert hasattr(e, "error_code")
                assert e.error_code is not None
                assert len(e.error_code) > 0
                # Error code should be uppercase with underscores
                assert e.error_code.isupper()

    def test_all_exceptions_include_suggestions(self):
        """Test that all custom exceptions include helpful suggestions."""
        test_cases = [
            lambda: Tag(name="   "),
            lambda: Tag(name="test", color="red"),
            lambda: Task(title="   "),
            lambda: Task(title="Test", due_date=datetime.utcnow() - timedelta(days=500)),
            lambda: User(username="john doe", email="test@example.com"),
        ]

        for func in test_cases:
            try:
                func()
                pytest.fail("Expected an exception to be raised")
            except (FieldValidationException, DateValidationException) as e:
                # Check for either "suggestion" or "common_mistakes" as helpful context
                has_suggestion = "suggestion" in e.details or "common_mistakes" in e.details
                assert has_suggestion, f"Exception details missing helpful context: {e.details.keys()}"

                if "suggestion" in e.details:
                    suggestion = e.details["suggestion"]
                    assert isinstance(suggestion, str)
                    assert len(suggestion) > 0
                elif "common_mistakes" in e.details:
                    mistakes = e.details["common_mistakes"]
                    assert isinstance(mistakes, str)
                    assert len(mistakes) > 0

    def test_exception_to_dict_includes_all_fields(self):
        """Test that exception to_dict() method includes all relevant fields."""
        try:
            Tag(name="test", color="invalid")
        except FieldValidationException as e:
            exc_dict = e.to_dict()

            assert "error_code" in exc_dict
            assert "message" in exc_dict
            assert "field_name" in exc_dict
            assert "details" in exc_dict

            assert exc_dict["error_code"] == e.error_code
            assert exc_dict["message"] == e.message
            assert exc_dict["field_name"] == e.field_name
            assert exc_dict["details"] == e.details


class TestTaskStateConsistencyValidator:
    """Test Task state consistency validator."""

    def test_archived_without_completion_raises_state_validation_exception(self):
        """Test that archived task without completed_at raises StateValidationException."""
        with pytest.raises(StateValidationException) as exc_info:
            Task(
                title="Test",
                status=TaskStatus.ARCHIVED,
                completed_at=None
            )

        assert exc_info.value.error_code == "ARCHIVED_WITHOUT_COMPLETION"
        assert "archived" in exc_info.value.message.lower()
        assert "completed_at" in exc_info.value.message.lower()

    def test_state_validation_exception_includes_current_state(self):
        """Test that state validation exception includes state information."""
        with pytest.raises(StateValidationException) as exc_info:
            Task(
                title="Test",
                status=TaskStatus.ARCHIVED,
                completed_at=None
            )

        assert "current_state" in exc_info.value.details or "status" in exc_info.value.details
        assert "suggestion" in exc_info.value.details


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
