"""
Comprehensive tests for all custom exception classes.

This module contains the TestExceptions class that tests all custom exception
initialization, message formatting, error code assignment, details dictionary
structure, and inheritance chain verification.
"""
import pytest
from typing import Any, Dict
from datetime import datetime

from exceptions import (
    TaskManagerException,
    ValidationException,
    FieldValidationException,
    StateValidationException,
    DuplicateTaskException,
    TaskNotFoundException,
    InvalidStateTransitionException,
    DateValidationException,
    OwnershipException,
    DataIntegrityException,
    SerializationException,
    ValidationErrorCollection
)


class TestExceptions:
    """Test class for all custom exception types."""

    def test_base_exception_minimal_initialization(self):
        """Test TaskManagerException with minimal parameters."""
        exc = TaskManagerException(
            message="Test error",
            error_code="TEST_ERROR"
        )

        assert exc.message == "Test error"
        assert exc.error_code == "TEST_ERROR"
        assert exc.details == {}
        assert exc.field_name is None

    def test_base_exception_full_initialization(self):
        """Test TaskManagerException with all parameters."""
        exc = TaskManagerException(
            message="Test error",
            error_code="TEST_ERROR",
            details={"key": "value", "count": 42},
            field_name="test_field"
        )

        assert exc.message == "Test error"
        assert exc.error_code == "TEST_ERROR"
        assert exc.details == {"key": "value", "count": 42}
        assert exc.field_name == "test_field"

    def test_base_exception_string_formatting_without_field(self):
        """Test string representation without field name."""
        exc = TaskManagerException(
            message="Test error",
            error_code="TEST_ERROR",
            details={"info": "additional"}
        )

        str_repr = str(exc)
        assert "[TEST_ERROR]" in str_repr
        assert "Test error" in str_repr
        assert "info=additional" in str_repr

    def test_base_exception_string_formatting_with_field(self):
        """Test string representation with field name."""
        exc = TaskManagerException(
            message="Invalid value",
            error_code="FIELD_ERROR",
            field_name="username"
        )

        str_repr = str(exc)
        assert "[FIELD_ERROR]" in str_repr
        assert "Field 'username':" in str_repr
        assert "Invalid value" in str_repr

    def test_base_exception_to_dict(self):
        """Test to_dict serialization method."""
        exc = TaskManagerException(
            message="Test error",
            error_code="TEST_ERROR",
            details={"key": "value"},
            field_name="test_field"
        )

        exc_dict = exc.to_dict()
        assert exc_dict == {
            "error_code": "TEST_ERROR",
            "message": "Test error",
            "field_name": "test_field",
            "details": {"key": "value"}
        }

    def test_base_exception_inheritance(self):
        """Test that TaskManagerException inherits from Exception."""
        exc = TaskManagerException(message="Test", error_code="TEST")
        assert isinstance(exc, Exception)

    def test_validation_exception_default_error_code(self):
        """Test ValidationException uses default error code."""
        exc = ValidationException(message="Invalid data")

        assert exc.message == "Invalid data"
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.field_name is None
        assert exc.details == {}

    def test_validation_exception_with_field_name(self):
        """Test ValidationException with field name."""
        exc = ValidationException(
            message="Invalid email format",
            field_name="email"
        )

        assert exc.field_name == "email"
        assert "email" in str(exc)

    def test_validation_exception_custom_error_code(self):
        """Test ValidationException with custom error code."""
        exc = ValidationException(
            message="Custom validation error",
            error_code="CUSTOM_VALIDATION",
            details={"reason": "test"}
        )

        assert exc.error_code == "CUSTOM_VALIDATION"
        assert exc.details == {"reason": "test"}

    def test_validation_exception_inheritance(self):
        """Test ValidationException inherits from TaskManagerException."""
        exc = ValidationException(message="Test")
        assert isinstance(exc, TaskManagerException)
        assert isinstance(exc, Exception)

    def test_field_validation_exception_with_invalid_value(self):
        """Test FieldValidationException stores invalid value in details."""
        exc = FieldValidationException(
            field_name="color",
            message="Color must be in hex format",
            invalid_value="red"
        )

        assert exc.field_name == "color"
        assert exc.message == "Color must be in hex format"
        assert exc.error_code == "FIELD_VALIDATION_ERROR"
        assert exc.details["invalid_value"] == "red"

    def test_field_validation_exception_without_invalid_value(self):
        """Test FieldValidationException without invalid value."""
        exc = FieldValidationException(
            field_name="title",
            message="Title is required"
        )

        assert exc.field_name == "title"
        assert "invalid_value" not in exc.details

    def test_field_validation_exception_with_additional_details(self):
        """Test FieldValidationException merges additional details."""
        exc = FieldValidationException(
            field_name="age",
            message="Age must be positive",
            invalid_value=-5,
            details={"minimum": 0, "maximum": 120}
        )

        assert exc.details["invalid_value"] == -5
        assert exc.details["minimum"] == 0
        assert exc.details["maximum"] == 120

    def test_field_validation_exception_inheritance(self):
        """Test FieldValidationException inheritance chain."""
        exc = FieldValidationException(field_name="test", message="Test")
        assert isinstance(exc, ValidationException)
        assert isinstance(exc, TaskManagerException)
        assert isinstance(exc, Exception)

    def test_state_validation_exception_with_states(self):
        """Test StateValidationException with state information."""
        exc = StateValidationException(
            message="Cannot mark archived task as complete",
            current_state="archived",
            attempted_state="done"
        )

        assert exc.message == "Cannot mark archived task as complete"
        assert exc.error_code == "STATE_VALIDATION_ERROR"
        assert exc.details["current_state"] == "archived"
        assert exc.details["attempted_state"] == "done"

    def test_state_validation_exception_without_states(self):
        """Test StateValidationException without state parameters."""
        exc = StateValidationException(message="Invalid state")

        assert exc.message == "Invalid state"
        assert "current_state" not in exc.details
        assert "attempted_state" not in exc.details

    def test_state_validation_exception_inheritance(self):
        """Test StateValidationException inheritance chain."""
        exc = StateValidationException(message="Test")
        assert isinstance(exc, ValidationException)
        assert isinstance(exc, TaskManagerException)

    def test_duplicate_task_exception_default_message(self):
        """Test DuplicateTaskException generates default message."""
        exc = DuplicateTaskException(task_id="task-123")

        assert exc.message == "Task with ID 'task-123' already exists"
        assert exc.error_code == "DUPLICATE_TASK"
        assert exc.details["task_id"] == "task-123"

    def test_duplicate_task_exception_custom_message(self):
        """Test DuplicateTaskException with custom message."""
        exc = DuplicateTaskException(
            task_id="task-456",
            message="Cannot add duplicate task"
        )

        assert exc.message == "Cannot add duplicate task"
        assert exc.details["task_id"] == "task-456"

    def test_duplicate_task_exception_with_details(self):
        """Test DuplicateTaskException preserves additional details."""
        exc = DuplicateTaskException(
            task_id="task-789",
            details={"list_id": "list-1", "user_id": "user-1"}
        )

        assert exc.details["task_id"] == "task-789"
        assert exc.details["list_id"] == "list-1"
        assert exc.details["user_id"] == "user-1"

    def test_duplicate_task_exception_inheritance(self):
        """Test DuplicateTaskException inherits from TaskManagerException."""
        exc = DuplicateTaskException(task_id="test")
        assert isinstance(exc, TaskManagerException)
        assert isinstance(exc, Exception)

    def test_task_not_found_exception_default_message(self):
        """Test TaskNotFoundException generates default message."""
        exc = TaskNotFoundException(task_id="task-999")

        assert exc.message == "Task with ID 'task-999' not found"
        assert exc.error_code == "TASK_NOT_FOUND"
        assert exc.details["task_id"] == "task-999"

    def test_task_not_found_exception_custom_message(self):
        """Test TaskNotFoundException with custom message."""
        exc = TaskNotFoundException(
            task_id="task-404",
            message="Requested task does not exist"
        )

        assert exc.message == "Requested task does not exist"
        assert exc.details["task_id"] == "task-404"

    def test_task_not_found_exception_inheritance(self):
        """Test TaskNotFoundException inheritance."""
        exc = TaskNotFoundException(task_id="test")
        assert isinstance(exc, TaskManagerException)

    def test_invalid_state_transition_exception_with_statuses(self):
        """Test InvalidStateTransitionException with status information."""
        exc = InvalidStateTransitionException(
            message="Cannot transition from archived to in-progress",
            current_status="archived",
            attempted_status="in_progress"
        )

        assert exc.message == "Cannot transition from archived to in-progress"
        assert exc.error_code == "INVALID_STATE_TRANSITION"
        assert exc.details["current_status"] == "archived"
        assert exc.details["attempted_status"] == "in_progress"

    def test_invalid_state_transition_exception_minimal(self):
        """Test InvalidStateTransitionException with only message."""
        exc = InvalidStateTransitionException(
            message="Invalid status change"
        )

        assert exc.message == "Invalid status change"
        assert "current_status" not in exc.details
        assert "attempted_status" not in exc.details

    def test_invalid_state_transition_exception_inheritance(self):
        """Test InvalidStateTransitionException inheritance."""
        exc = InvalidStateTransitionException(message="Test")
        assert isinstance(exc, TaskManagerException)

    def test_date_validation_exception_with_invalid_date(self):
        """Test DateValidationException stores invalid date."""
        exc = DateValidationException(
            message="Due date must be in the future",
            field_name="due_date",
            invalid_date=datetime(2020, 1, 1)
        )

        assert exc.message == "Due date must be in the future"
        assert exc.error_code == "DATE_VALIDATION_ERROR"
        assert exc.field_name == "due_date"
        assert "2020-01-01" in exc.details["invalid_date"]

    def test_date_validation_exception_string_date(self):
        """Test DateValidationException with string date."""
        exc = DateValidationException(
            message="Invalid date format",
            field_name="created_at",
            invalid_date="not-a-date"
        )

        assert exc.details["invalid_date"] == "not-a-date"

    def test_date_validation_exception_without_date(self):
        """Test DateValidationException without invalid_date parameter."""
        exc = DateValidationException(
            message="Date is required",
            field_name="due_date"
        )

        assert "invalid_date" not in exc.details

    def test_date_validation_exception_inheritance(self):
        """Test DateValidationException inheritance chain."""
        exc = DateValidationException(message="Test")
        assert isinstance(exc, ValidationException)
        assert isinstance(exc, TaskManagerException)

    def test_ownership_exception_with_all_params(self):
        """Test OwnershipException with all resource parameters."""
        exc = OwnershipException(
            message="User does not own this resource",
            resource_type="task_list",
            resource_id="list-123",
            user_id="user-456"
        )

        assert exc.message == "User does not own this resource"
        assert exc.error_code == "OWNERSHIP_ERROR"
        assert exc.details["resource_type"] == "task_list"
        assert exc.details["resource_id"] == "list-123"
        assert exc.details["user_id"] == "user-456"

    def test_ownership_exception_minimal(self):
        """Test OwnershipException with only message."""
        exc = OwnershipException(message="Access denied")

        assert exc.message == "Access denied"
        assert "resource_type" not in exc.details
        assert "resource_id" not in exc.details
        assert "user_id" not in exc.details

    def test_ownership_exception_partial_params(self):
        """Test OwnershipException with some parameters."""
        exc = OwnershipException(
            message="Unauthorized access",
            resource_type="task",
            user_id="user-789"
        )

        assert exc.details["resource_type"] == "task"
        assert exc.details["user_id"] == "user-789"
        assert "resource_id" not in exc.details

    def test_ownership_exception_inheritance(self):
        """Test OwnershipException inheritance."""
        exc = OwnershipException(message="Test")
        assert isinstance(exc, TaskManagerException)

    def test_data_integrity_exception_basic(self):
        """Test DataIntegrityException with basic parameters."""
        exc = DataIntegrityException(
            message="Data consistency violation detected"
        )

        assert exc.message == "Data consistency violation detected"
        assert exc.error_code == "DATA_INTEGRITY_ERROR"
        assert exc.details == {}

    def test_data_integrity_exception_with_resolution_hint(self):
        """Test DataIntegrityException with resolution hint."""
        exc = DataIntegrityException(
            message="Circular reference detected",
            resolution_hint="Remove circular dependencies between objects"
        )

        assert exc.message == "Circular reference detected"
        assert exc.details["resolution_hint"] == "Remove circular dependencies between objects"

    def test_data_integrity_exception_with_details_and_hint(self):
        """Test DataIntegrityException with both details and hint."""
        exc = DataIntegrityException(
            message="Inconsistent task dates",
            details={"completed_at": "2024-01-01", "created_at": "2024-01-02"},
            resolution_hint="Ensure completed_at is after created_at"
        )

        assert exc.details["completed_at"] == "2024-01-01"
        assert exc.details["created_at"] == "2024-01-02"
        assert exc.details["resolution_hint"] == "Ensure completed_at is after created_at"

    def test_data_integrity_exception_custom_error_code(self):
        """Test DataIntegrityException with custom error code."""
        exc = DataIntegrityException(
            message="Custom integrity error",
            error_code="CUSTOM_INTEGRITY_ERROR"
        )

        assert exc.error_code == "CUSTOM_INTEGRITY_ERROR"

    def test_data_integrity_exception_inheritance(self):
        """Test DataIntegrityException inheritance."""
        exc = DataIntegrityException(message="Test")
        assert isinstance(exc, TaskManagerException)

    def test_serialization_exception_minimal(self):
        """Test SerializationException with minimal parameters."""
        exc = SerializationException(message="Serialization failed")

        assert exc.message == "Serialization failed"
        assert exc.error_code == "SERIALIZATION_ERROR"
        assert exc.field_name is None

    def test_serialization_exception_with_operation(self):
        """Test SerializationException with operation type."""
        exc = SerializationException(
            message="Failed to convert to JSON",
            operation="to_json"
        )

        assert exc.details["operation"] == "to_json"

    def test_serialization_exception_with_field_name(self):
        """Test SerializationException with field name."""
        exc = SerializationException(
            message="Cannot serialize field",
            operation="to_dict",
            field_name="created_at"
        )

        assert exc.field_name == "created_at"
        assert exc.details["operation"] == "to_dict"

    def test_serialization_exception_with_original_error(self):
        """Test SerializationException captures original error."""
        original = TypeError("Object of type datetime is not JSON serializable")
        exc = SerializationException(
            message="JSON serialization failed",
            operation="to_json",
            original_error=original
        )

        assert exc.details["original_error"] == str(original)
        assert exc.details["error_type"] == "TypeError"
        assert "resolution_hint" in exc.details
        assert "JSON-serializable types" in exc.details["resolution_hint"]

    def test_serialization_exception_recursion_error_hint(self):
        """Test SerializationException provides hint for RecursionError."""
        original = RecursionError("maximum recursion depth exceeded")
        exc = SerializationException(
            message="Circular reference detected",
            original_error=original
        )

        assert exc.details["error_type"] == "RecursionError"
        assert "Circular reference" in exc.details["resolution_hint"]

    def test_serialization_exception_attribute_error_hint(self):
        """Test SerializationException provides hint for AttributeError."""
        original = AttributeError("'NoneType' object has no attribute 'to_dict'")
        exc = SerializationException(
            message="Missing required attribute",
            original_error=original
        )

        assert exc.details["error_type"] == "AttributeError"
        assert "missing required attributes" in exc.details["resolution_hint"]

    def test_serialization_exception_generic_error_hint(self):
        """Test SerializationException provides generic hint for other errors."""
        original = ValueError("Invalid value")
        exc = SerializationException(
            message="Serialization error",
            original_error=original
        )

        assert exc.details["error_type"] == "ValueError"
        assert "ValueError" in exc.details["resolution_hint"]

    def test_serialization_exception_inheritance(self):
        """Test SerializationException inheritance."""
        exc = SerializationException(message="Test")
        assert isinstance(exc, TaskManagerException)

    def test_validation_error_collection_basic(self):
        """Test ValidationErrorCollection with multiple errors."""
        error1 = FieldValidationException(
            field_name="email",
            message="Invalid email format"
        )
        error2 = FieldValidationException(
            field_name="username",
            message="Username too short"
        )

        exc = ValidationErrorCollection(errors=[error1, error2])

        assert exc.errors == [error1, error2]
        assert exc.error_code == "MULTIPLE_VALIDATION_ERRORS"
        assert "2 errors" in exc.message
        assert exc.details["error_count"] == 2
        assert len(exc.details["errors"]) == 2

    def test_validation_error_collection_single_error(self):
        """Test ValidationErrorCollection with single error."""
        error = ValidationException(message="Single validation error")
        exc = ValidationErrorCollection(errors=[error])

        assert len(exc.errors) == 1
        assert "1 error" in exc.message
        assert exc.details["error_count"] == 1

    def test_validation_error_collection_custom_message(self):
        """Test ValidationErrorCollection with custom message."""
        errors = [ValidationException(message="Error 1")]
        exc = ValidationErrorCollection(
            errors=errors,
            message="Custom error message"
        )

        assert exc.message == "Custom error message"

    def test_validation_error_collection_format_errors_basic(self):
        """Test format_errors method with basic formatting."""
        error1 = FieldValidationException(
            field_name="email",
            message="Invalid format",
            invalid_value="not-an-email"
        )
        error2 = ValidationException(
            message="General validation error"
        )

        exc = ValidationErrorCollection(errors=[error1, error2])
        formatted = exc.format_errors(include_details=True)

        assert "Found 2 validation error(s):" in formatted
        assert "FIELD_VALIDATION_ERROR" in formatted
        assert "Field 'email'" in formatted
        assert "Invalid format" in formatted
        assert "VALIDATION_ERROR" in formatted
        assert "General validation error" in formatted

    def test_validation_error_collection_format_errors_without_details(self):
        """Test format_errors method without details."""
        error = FieldValidationException(
            field_name="title",
            message="Title is required",
            invalid_value=""
        )

        exc = ValidationErrorCollection(errors=[error])
        formatted = exc.format_errors(include_details=False)

        assert "Found 1 validation error(s):" in formatted
        assert "FIELD_VALIDATION_ERROR" in formatted
        assert "Title is required" in formatted
        assert "invalid_value" not in formatted

    def test_validation_error_collection_format_empty_errors(self):
        """Test format_errors with empty error list."""
        exc = ValidationErrorCollection(errors=[])
        formatted = exc.format_errors()

        assert formatted == "No validation errors"

    def test_validation_error_collection_str_representation(self):
        """Test string representation includes formatted errors."""
        error = ValidationException(message="Test error")
        exc = ValidationErrorCollection(errors=[error])

        str_repr = str(exc)
        assert "Found 1 validation error(s):" in str_repr
        assert "Test error" in str_repr

    def test_validation_error_collection_to_dict(self):
        """Test to_dict includes all errors."""
        error1 = ValidationException(message="Error 1")
        error2 = ValidationException(message="Error 2")

        exc = ValidationErrorCollection(errors=[error1, error2])
        exc_dict = exc.to_dict()

        assert exc_dict["error_code"] == "MULTIPLE_VALIDATION_ERRORS"
        assert exc_dict["details"]["error_count"] == 2
        assert len(exc_dict["details"]["errors"]) == 2

    def test_validation_error_collection_inheritance(self):
        """Test ValidationErrorCollection inheritance."""
        exc = ValidationErrorCollection(errors=[])
        assert isinstance(exc, TaskManagerException)

    def test_exception_error_code_assignment(self):
        """Test that all exceptions assign correct default error codes."""
        test_cases = [
            (ValidationException(message="Test"), "VALIDATION_ERROR"),
            (FieldValidationException(field_name="test", message="Test"), "FIELD_VALIDATION_ERROR"),
            (StateValidationException(message="Test"), "STATE_VALIDATION_ERROR"),
            (DuplicateTaskException(task_id="test"), "DUPLICATE_TASK"),
            (TaskNotFoundException(task_id="test"), "TASK_NOT_FOUND"),
            (InvalidStateTransitionException(message="Test"), "INVALID_STATE_TRANSITION"),
            (DateValidationException(message="Test"), "DATE_VALIDATION_ERROR"),
            (OwnershipException(message="Test"), "OWNERSHIP_ERROR"),
            (DataIntegrityException(message="Test"), "DATA_INTEGRITY_ERROR"),
            (SerializationException(message="Test"), "SERIALIZATION_ERROR"),
            (ValidationErrorCollection(errors=[]), "MULTIPLE_VALIDATION_ERRORS"),
        ]

        for exc, expected_code in test_cases:
            assert exc.error_code == expected_code, f"{type(exc).__name__} has wrong error code"

    def test_exception_details_dictionary_structure(self):
        """Test that all exceptions maintain proper details dictionary structure."""
        exceptions = [
            TaskManagerException(message="Test", error_code="TEST", details={"key": "value"}),
            ValidationException(message="Test", details={"key": "value"}),
            FieldValidationException(field_name="test", message="Test", invalid_value="bad"),
            StateValidationException(message="Test", current_state="state1", attempted_state="state2"),
            DuplicateTaskException(task_id="test"),
            TaskNotFoundException(task_id="test"),
            InvalidStateTransitionException(message="Test", current_status="status1"),
            DateValidationException(message="Test", invalid_date="2020-01-01"),
            OwnershipException(message="Test", resource_type="task", user_id="user1"),
            DataIntegrityException(message="Test", resolution_hint="Fix it"),
            SerializationException(message="Test", operation="to_json"),
        ]

        for exc in exceptions:
            assert isinstance(exc.details, dict), f"{type(exc).__name__} details is not a dict"
            exc_dict = exc.to_dict()
            assert "details" in exc_dict, f"{type(exc).__name__} to_dict missing details"
            assert isinstance(exc_dict["details"], dict), f"{type(exc).__name__} to_dict details not a dict"

    def test_inheritance_chain_verification(self):
        """Test that all exceptions inherit from TaskManagerException."""
        exceptions = [
            ValidationException(message="Test"),
            FieldValidationException(field_name="test", message="Test"),
            StateValidationException(message="Test"),
            DuplicateTaskException(task_id="test"),
            TaskNotFoundException(task_id="test"),
            InvalidStateTransitionException(message="Test"),
            DateValidationException(message="Test"),
            OwnershipException(message="Test"),
            DataIntegrityException(message="Test"),
            SerializationException(message="Test"),
            ValidationErrorCollection(errors=[]),
        ]

        for exc in exceptions:
            assert isinstance(exc, TaskManagerException), f"{type(exc).__name__} doesn't inherit from TaskManagerException"
            assert isinstance(exc, Exception), f"{type(exc).__name__} doesn't inherit from Exception"

    def test_validation_exception_subclass_chain(self):
        """Test that validation-related exceptions form proper inheritance chain."""
        validation_exceptions = [
            FieldValidationException(field_name="test", message="Test"),
            StateValidationException(message="Test"),
            DateValidationException(message="Test"),
        ]

        for exc in validation_exceptions:
            assert isinstance(exc, ValidationException), f"{type(exc).__name__} doesn't inherit from ValidationException"
            assert isinstance(exc, TaskManagerException), f"{type(exc).__name__} doesn't inherit from TaskManagerException"
