"""
Validation utility functions for common validation patterns.

This module provides reusable helper functions for input validation to reduce
code duplication and ensure consistent validation behavior across the codebase.
"""
import re
from datetime import datetime, timedelta
from typing import Optional

from exceptions import FieldValidationException, DateValidationException


def validate_not_empty_string(value: str, field_name: str) -> str:
    """
    Validate that a string is not empty or only whitespace.

    Args:
        value: The string value to validate
        field_name: Name of the field being validated (for error messages)

    Returns:
        The stripped string value if valid

    Raises:
        FieldValidationException: If the string is empty or only whitespace
    """
    if not value or not value.strip():
        raise FieldValidationException(
            field_name=field_name,
            message=f"{field_name} cannot be empty or whitespace only",
            invalid_value=value,
            error_code="EMPTY_STRING_ERROR",
            details={
                "suggestion": f"Provide a non-empty {field_name} with at least one non-whitespace character"
            }
        )
    return value.strip()


def validate_hex_color(value: str) -> str:
    """
    Validate that a color value is in valid hex format (#RRGGBB).

    Args:
        value: The color string to validate

    Returns:
        The validated color string

    Raises:
        FieldValidationException: If the color format is invalid
    """
    if not value:
        raise FieldValidationException(
            field_name="color",
            message="Color cannot be empty",
            invalid_value=value,
            error_code="COLOR_EMPTY",
            details={
                "expected_format": "#RRGGBB",
                "examples": ["#FF0000 (red)", "#00FF00 (green)", "#0000FF (blue)", "#808080 (gray)"]
            }
        )

    # Validate hex color format: # followed by exactly 6 hex digits
    hex_pattern = r"^#[0-9A-Fa-f]{6}$"
    if not re.match(hex_pattern, value):
        # Provide specific feedback based on common mistakes
        details = {
            "expected_format": "#RRGGBB (e.g., #FF0000)",
            "examples": ["#FF0000 (red)", "#00FF00 (green)", "#0000FF (blue)"]
        }

        if not value.startswith("#"):
            details["hint"] = "Color must start with '#' symbol"
        elif len(value) != 7:
            details["hint"] = f"Color must be exactly 7 characters (# + 6 hex digits), got {len(value)} characters"
        else:
            details["hint"] = "Color must contain only hexadecimal digits (0-9, A-F) after the '#' symbol"

        raise FieldValidationException(
            field_name="color",
            message=f"Invalid color format: '{value}'. Expected format: #RRGGBB",
            invalid_value=value,
            error_code="INVALID_COLOR_FORMAT",
            details=details
        )

    return value.upper()  # Normalize to uppercase


def validate_future_date(
    value: datetime,
    allow_past_days: int = 0,
    field_name: str = "date"
) -> datetime:
    """
    Validate that a date is in the future or within allowed past days.

    Args:
        value: The datetime value to validate
        allow_past_days: Number of days in the past to allow (default: 0)
        field_name: Name of the field being validated (for error messages)

    Returns:
        The validated datetime value

    Raises:
        DateValidationException: If the date is not within the allowed range
    """
    if not isinstance(value, datetime):
        raise DateValidationException(
            message=f"{field_name} must be a datetime object",
            field_name=field_name,
            invalid_date=value,
            error_code="INVALID_DATE_TYPE",
            details={
                "provided_type": type(value).__name__,
                "expected_type": "datetime"
            }
        )

    now = datetime.now()
    earliest_allowed = now - timedelta(days=allow_past_days)

    if value < earliest_allowed:
        if allow_past_days == 0:
            message = f"{field_name} must be in the future, not in the past"
            hint = "Provide a date and time that is after the current time"
        else:
            message = f"{field_name} cannot be more than {allow_past_days} days in the past"
            hint = f"Provide a date within the last {allow_past_days} days or in the future"

        raise DateValidationException(
            message=message,
            field_name=field_name,
            invalid_date=value,
            error_code="DATE_NOT_IN_FUTURE",
            details={
                "provided_date": value.isoformat(),
                "current_time": now.isoformat(),
                "earliest_allowed": earliest_allowed.isoformat(),
                "allow_past_days": allow_past_days,
                "hint": hint
            }
        )

    # Check if the date is unreasonably far in the future (more than 100 years)
    max_future = now + timedelta(days=365 * 100)
    if value > max_future:
        raise DateValidationException(
            message=f"{field_name} is unreasonably far in the future (more than 100 years)",
            field_name=field_name,
            invalid_date=value,
            error_code="DATE_TOO_FAR_FUTURE",
            details={
                "provided_date": value.isoformat(),
                "current_time": now.isoformat(),
                "max_allowed": max_future.isoformat(),
                "hint": "Ensure the date is realistic and within a reasonable timeframe"
            }
        )

    return value


def validate_email_format(value: str) -> str:
    """
    Validate email format with detailed error messages for common mistakes.

    Args:
        value: The email string to validate

    Returns:
        The validated email string (lowercased)

    Raises:
        FieldValidationException: If the email format is invalid
    """
    if not value or not value.strip():
        raise FieldValidationException(
            field_name="email",
            message="Email address cannot be empty",
            invalid_value=value,
            error_code="EMAIL_EMPTY",
            details={
                "expected_format": "username@domain.com",
                "example": "user@example.com"
            }
        )

    value = value.strip()

    # Check for missing @ symbol
    if "@" not in value:
        raise FieldValidationException(
            field_name="email",
            message="Email address must contain '@' symbol",
            invalid_value=value,
            error_code="EMAIL_MISSING_AT",
            details={
                "expected_format": "username@domain.com",
                "hint": "Email must have format: username@domain.com"
            }
        )

    # Split into local and domain parts
    parts = value.split("@")
    if len(parts) != 2:
        raise FieldValidationException(
            field_name="email",
            message="Email address must contain exactly one '@' symbol",
            invalid_value=value,
            error_code="EMAIL_MULTIPLE_AT",
            details={
                "expected_format": "username@domain.com",
                "hint": "Email should have only one '@' separating username and domain"
            }
        )

    local_part, domain_part = parts

    # Validate local part (username)
    if not local_part:
        raise FieldValidationException(
            field_name="email",
            message="Email address must have a username before '@'",
            invalid_value=value,
            error_code="EMAIL_EMPTY_LOCAL",
            details={
                "expected_format": "username@domain.com",
                "hint": "Provide a username before the '@' symbol"
            }
        )

    # Validate domain part
    if not domain_part:
        raise FieldValidationException(
            field_name="email",
            message="Email address must have a domain after '@'",
            invalid_value=value,
            error_code="EMAIL_EMPTY_DOMAIN",
            details={
                "expected_format": "username@domain.com",
                "hint": "Provide a domain after the '@' symbol (e.g., example.com)"
            }
        )

    # Check for domain with TLD
    if "." not in domain_part:
        raise FieldValidationException(
            field_name="email",
            message="Email domain must contain a period (e.g., example.com)",
            invalid_value=value,
            error_code="EMAIL_INVALID_DOMAIN",
            details={
                "expected_format": "username@domain.com",
                "hint": "Domain should include a top-level domain like '.com', '.org', '.net', etc.",
                "examples": ["user@example.com", "admin@company.org", "info@site.co.uk"]
            }
        )

    # Check domain doesn't start or end with period
    if domain_part.startswith(".") or domain_part.endswith("."):
        raise FieldValidationException(
            field_name="email",
            message="Email domain cannot start or end with a period",
            invalid_value=value,
            error_code="EMAIL_INVALID_DOMAIN_FORMAT",
            details={
                "hint": "Domain should be in format: example.com (not .example.com or example.com.)"
            }
        )

    # More comprehensive email regex validation
    # This pattern checks for:
    # - Local part: alphanumeric, dots, hyphens, underscores
    # - Domain: alphanumeric with dots and hyphens
    # - TLD: at least 2 characters
    email_pattern = r"^[a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, value):
        raise FieldValidationException(
            field_name="email",
            message="Email address contains invalid characters or format",
            invalid_value=value,
            error_code="EMAIL_INVALID_FORMAT",
            details={
                "expected_format": "username@domain.com",
                "allowed_characters": "Letters, numbers, dots, hyphens, underscores in username; letters, numbers, dots, hyphens in domain",
                "examples": ["user@example.com", "john.doe@company.co.uk", "admin_123@site.org"]
            }
        )

    return value.lower()  # Normalize to lowercase


def validate_username_format(value: str) -> str:
    """
    Validate username format with explanation of valid characters.

    Username rules:
    - Must be 3-30 characters long
    - Can contain letters (a-z, A-Z), numbers (0-9), underscores (_), and hyphens (-)
    - Must start with a letter
    - Cannot end with an underscore or hyphen
    - Cannot contain consecutive special characters

    Args:
        value: The username string to validate

    Returns:
        The validated username string

    Raises:
        FieldValidationException: If the username format is invalid
    """
    if not value or not value.strip():
        raise FieldValidationException(
            field_name="username",
            message="Username cannot be empty",
            invalid_value=value,
            error_code="USERNAME_EMPTY",
            details={
                "rules": [
                    "Must be 3-30 characters long",
                    "Must start with a letter",
                    "Can contain letters, numbers, underscores, and hyphens"
                ],
                "examples": ["john_doe", "user123", "alice-smith"]
            }
        )

    value = value.strip()

    # Check length
    if len(value) < 3:
        raise FieldValidationException(
            field_name="username",
            message=f"Username must be at least 3 characters long (got {len(value)})",
            invalid_value=value,
            error_code="USERNAME_TOO_SHORT",
            details={
                "min_length": 3,
                "max_length": 30,
                "hint": "Provide a username with at least 3 characters"
            }
        )

    if len(value) > 30:
        raise FieldValidationException(
            field_name="username",
            message=f"Username must be at most 30 characters long (got {len(value)})",
            invalid_value=value,
            error_code="USERNAME_TOO_LONG",
            details={
                "min_length": 3,
                "max_length": 30,
                "hint": "Shorten the username to 30 characters or less"
            }
        )

    # Check that it starts with a letter
    if not value[0].isalpha():
        raise FieldValidationException(
            field_name="username",
            message=f"Username must start with a letter (got '{value[0]}')",
            invalid_value=value,
            error_code="USERNAME_INVALID_START",
            details={
                "hint": "Username should begin with a letter (a-z or A-Z)",
                "examples": ["john_doe", "alice123", "user_name"]
            }
        )

    # Check that it doesn't end with special characters
    if value[-1] in ("_", "-"):
        raise FieldValidationException(
            field_name="username",
            message=f"Username cannot end with '{value[-1]}'",
            invalid_value=value,
            error_code="USERNAME_INVALID_END",
            details={
                "hint": "Username should end with a letter or number",
                "examples": ["john_doe", "user123", "alice_smith"]
            }
        )

    # Check for consecutive special characters
    if "__" in value or "--" in value or "_-" in value or "-_" in value:
        raise FieldValidationException(
            field_name="username",
            message="Username cannot contain consecutive special characters",
            invalid_value=value,
            error_code="USERNAME_CONSECUTIVE_SPECIAL",
            details={
                "hint": "Use only single underscores or hyphens between words",
                "valid": "john_doe, user-name",
                "invalid": "john__doe, user--name, name_-test"
            }
        )

    # Comprehensive pattern validation
    # ^[a-zA-Z] - starts with letter
    # [a-zA-Z0-9_-]* - followed by letters, numbers, underscores, or hyphens
    # [a-zA-Z0-9]$ - ends with letter or number (if more than 1 char)
    username_pattern = r"^[a-zA-Z]([a-zA-Z0-9_-]*[a-zA-Z0-9])?$"
    if not re.match(username_pattern, value):
        # Identify specific invalid characters
        valid_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
        invalid_chars = set(value) - valid_chars

        if invalid_chars:
            raise FieldValidationException(
                field_name="username",
                message=f"Username contains invalid characters: {', '.join(repr(c) for c in sorted(invalid_chars))}",
                invalid_value=value,
                error_code="USERNAME_INVALID_CHARACTERS",
                details={
                    "allowed_characters": "letters (a-z, A-Z), numbers (0-9), underscores (_), hyphens (-)",
                    "invalid_characters": list(invalid_chars),
                    "hint": "Remove or replace the invalid characters"
                }
            )

        # If no invalid characters, the format is still wrong
        raise FieldValidationException(
            field_name="username",
            message="Username format is invalid",
            invalid_value=value,
            error_code="USERNAME_INVALID_FORMAT",
            details={
                "rules": [
                    "Must start with a letter",
                    "Can contain letters, numbers, underscores, and hyphens",
                    "Cannot end with underscore or hyphen",
                    "Cannot have consecutive special characters"
                ],
                "examples": ["john_doe", "user123", "alice-smith", "bob_jones2"]
            }
        )

    return value
