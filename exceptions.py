"""
Custom exception classes for the task management system.

This module defines a comprehensive exception hierarchy to provide clear,
contextual error messages for validation and business logic failures.
"""
from typing import Any, Dict, Optional


class TaskManagerException(Exception):
    """
    Base exception class for all task manager errors.

    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code for programmatic handling
        details: Additional context about the error
        field_name: Optional field name associated with the error
    """

    def __init__(
        self,
        message: str,
        error_code: str,
        details: Optional[Dict[str, Any]] = None,
        field_name: Optional[str] = None
    ):
        """
        Initialize the base exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional context dictionary
            field_name: Optional field name related to the error
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.field_name = field_name

        # Construct the full error message
        full_message = f"[{error_code}] {message}"
        if field_name:
            full_message = f"[{error_code}] Field '{field_name}': {message}"

        super().__init__(full_message)

    def __str__(self) -> str:
        """Return a string representation of the exception."""
        parts = [f"[{self.error_code}]"]

        if self.field_name:
            parts.append(f"Field '{self.field_name}':")

        parts.append(self.message)

        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            parts.append(f"(Details: {details_str})")

        return " ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the exception to a dictionary for serialization.

        Returns:
            Dictionary containing error information
        """
        return {
            "error_code": self.error_code,
            "message": self.message,
            "field_name": self.field_name,
            "details": self.details
        }


class ValidationException(TaskManagerException):
    """
    General validation exception for data validation errors.

    Used for validation failures that don't fit into more specific categories.
    Supports error codes and field names for detailed error reporting.
    """

    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        error_code: str = "VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a validation exception.

        Args:
            message: Human-readable error message
            field_name: Optional field name that failed validation
            error_code: Error code (defaults to VALIDATION_ERROR)
            details: Additional context about the validation failure
        """
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            field_name=field_name
        )


class FieldValidationException(ValidationException):
    """
    Exception for field-specific validation failures.

    Raised when a specific field fails validation with detailed information
    about what value was provided and why it failed.
    """

    def __init__(
        self,
        field_name: str,
        message: str,
        invalid_value: Any = None,
        error_code: str = "FIELD_VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a field validation exception.

        Args:
            field_name: Name of the field that failed validation
            message: Human-readable error message
            invalid_value: The invalid value that was provided
            error_code: Error code (defaults to FIELD_VALIDATION_ERROR)
            details: Additional context about the failure
        """
        # Add invalid value to details if provided
        if details is None:
            details = {}

        if invalid_value is not None:
            details["invalid_value"] = invalid_value

        super().__init__(
            message=message,
            field_name=field_name,
            error_code=error_code,
            details=details
        )


class StateValidationException(ValidationException):
    """
    Exception for invalid state transitions.

    Raised when attempting to transition an object to an invalid state
    or when the current state doesn't allow a specific operation.
    """

    def __init__(
        self,
        message: str,
        current_state: Optional[str] = None,
        attempted_state: Optional[str] = None,
        error_code: str = "STATE_VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a state validation exception.

        Args:
            message: Human-readable error message
            current_state: The current state of the object
            attempted_state: The state that was attempted to transition to
            error_code: Error code (defaults to STATE_VALIDATION_ERROR)
            details: Additional context about the invalid transition
        """
        # Add state information to details
        if details is None:
            details = {}

        if current_state is not None:
            details["current_state"] = current_state

        if attempted_state is not None:
            details["attempted_state"] = attempted_state

        super().__init__(
            message=message,
            error_code=error_code,
            details=details
        )
