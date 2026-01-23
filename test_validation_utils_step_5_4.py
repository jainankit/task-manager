"""
Comprehensive tests for validation utilities (Step 5.4).

This test module provides thorough coverage of:
- All helper functions in validation_utils.py with valid and invalid inputs
- Validation context manager with single and multiple errors
- ValidationErrorCollection formatting and error aggregation
- Batch validation to ensure all errors are collected before raising
"""
import pytest
from datetime import datetime, timedelta
from validation_utils import (
    validate_not_empty_string,
    validate_hex_color,
    validate_future_date,
    validate_email_format,
    validate_username_format,
    validation_context,
    ValidationContext
)
from exceptions import (
    FieldValidationException,
    DateValidationException,
    ValidationErrorCollection,
    TaskManagerException
)


class TestValidateNotEmptyString:
    """Test validate_not_empty_string helper function."""

    def test_valid_string(self):
        """Test that valid strings are accepted and stripped."""
        result = validate_not_empty_string("  Hello World  ", "test_field")
        assert result == "Hello World"

    def test_valid_single_char(self):
        """Test that single character strings are valid."""
        result = validate_not_empty_string("a", "test_field")
        assert result == "a"

    def test_valid_with_leading_spaces(self):
        """Test string with leading spaces is stripped."""
        result = validate_not_empty_string("   test", "name")
        assert result == "test"

    def test_valid_with_trailing_spaces(self):
        """Test string with trailing spaces is stripped."""
        result = validate_not_empty_string("test   ", "name")
        assert result == "test"

    def test_empty_string_raises_exception(self):
        """Test that empty string raises FieldValidationException."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_not_empty_string("", "username")

        error = exc_info.value
        assert error.error_code == "EMPTY_STRING_ERROR"
        assert error.field_name == "username"
        assert "cannot be empty" in error.message
        assert "suggestion" in error.details

    def test_whitespace_only_raises_exception(self):
        """Test that whitespace-only string raises FieldValidationException."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_not_empty_string("   ", "title")

        error = exc_info.value
        assert error.error_code == "EMPTY_STRING_ERROR"
        assert error.field_name == "title"

    def test_tabs_and_newlines_raises_exception(self):
        """Test that tabs and newlines only raises exception."""
        with pytest.raises(FieldValidationException):
            validate_not_empty_string("\t\n  \r\n", "description")

    def test_none_raises_exception(self):
        """Test that None raises exception (truthy check)."""
        with pytest.raises(FieldValidationException):
            validate_not_empty_string(None, "field")


class TestValidateHexColor:
    """Test validate_hex_color helper function."""

    def test_valid_lowercase_color(self):
        """Test that valid lowercase hex color is accepted and uppercased."""
        result = validate_hex_color("#ff0000")
        assert result == "#FF0000"

    def test_valid_uppercase_color(self):
        """Test that valid uppercase hex color is accepted."""
        result = validate_hex_color("#00FF00")
        assert result == "#00FF00"

    def test_valid_mixed_case_color(self):
        """Test that valid mixed case hex color is accepted and normalized."""
        result = validate_hex_color("#AbCdEf")
        assert result == "#ABCDEF"

    def test_valid_with_numbers(self):
        """Test hex color with numbers."""
        result = validate_hex_color("#123456")
        assert result == "#123456"

    def test_valid_black(self):
        """Test black color."""
        result = validate_hex_color("#000000")
        assert result == "#000000"

    def test_valid_white(self):
        """Test white color."""
        result = validate_hex_color("#ffffff")
        assert result == "#FFFFFF"

    def test_empty_string_raises_exception(self):
        """Test that empty string raises FieldValidationException."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_hex_color("")

        error = exc_info.value
        assert error.error_code == "COLOR_EMPTY"
        assert error.field_name == "color"
        assert "cannot be empty" in error.message
        assert "expected_format" in error.details
        assert "examples" in error.details

    def test_missing_hash_raises_exception(self):
        """Test that color without # raises exception with hint."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_hex_color("FF0000")

        error = exc_info.value
        assert error.error_code == "INVALID_COLOR_FORMAT"
        assert error.field_name == "color"
        assert "Invalid color format" in error.message
        assert error.details["hint"] == "Color must start with '#' symbol"

    def test_too_short_raises_exception(self):
        """Test that too short color raises exception with length hint."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_hex_color("#FF00")

        error = exc_info.value
        assert error.error_code == "INVALID_COLOR_FORMAT"
        assert "must be exactly 7 characters" in error.details["hint"]

    def test_too_long_raises_exception(self):
        """Test that too long color raises exception with length hint."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_hex_color("#FF0000AA")

        error = exc_info.value
        assert error.error_code == "INVALID_COLOR_FORMAT"
        assert "must be exactly 7 characters" in error.details["hint"]

    def test_invalid_characters_raises_exception(self):
        """Test that invalid hex characters raise exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_hex_color("#GGGGGG")

        error = exc_info.value
        assert error.error_code == "INVALID_COLOR_FORMAT"
        assert "hexadecimal digits" in error.details["hint"]

    def test_special_characters_raises_exception(self):
        """Test that special characters raise exception."""
        with pytest.raises(FieldValidationException):
            validate_hex_color("#FF@0!0")


class TestValidateFutureDate:
    """Test validate_future_date helper function."""

    def test_valid_future_date(self):
        """Test that future date is accepted."""
        future = datetime.now() + timedelta(days=7)
        result = validate_future_date(future, field_name="due_date")
        assert result == future

    def test_valid_far_future_date(self):
        """Test that far future date (within 100 years) is accepted."""
        future = datetime.now() + timedelta(days=365 * 50)  # 50 years
        result = validate_future_date(future, field_name="due_date")
        assert result == future

    def test_valid_with_allow_past_days(self):
        """Test that recent past date is accepted with allow_past_days."""
        recent_past = datetime.now() - timedelta(days=3)
        result = validate_future_date(recent_past, allow_past_days=7, field_name="due_date")
        assert result == recent_past

    def test_slightly_future_date_valid(self):
        """Test that slightly future date is accepted."""
        slightly_future = datetime.now() + timedelta(seconds=1)
        result = validate_future_date(slightly_future, field_name="due_date")
        assert result == slightly_future

    def test_past_date_raises_exception(self):
        """Test that past date raises DateValidationException."""
        past = datetime.now() - timedelta(days=7)

        with pytest.raises(DateValidationException) as exc_info:
            validate_future_date(past, field_name="due_date")

        error = exc_info.value
        assert error.error_code == "DATE_NOT_IN_FUTURE"
        assert error.field_name == "due_date"
        assert "must be in the future" in error.message
        assert "provided_date" in error.details
        assert "current_time" in error.details
        assert "hint" in error.details

    def test_past_beyond_allowed_days_raises_exception(self):
        """Test that past date beyond allowed days raises exception."""
        past = datetime.now() - timedelta(days=10)

        with pytest.raises(DateValidationException) as exc_info:
            validate_future_date(past, allow_past_days=5, field_name="deadline")

        error = exc_info.value
        assert error.error_code == "DATE_NOT_IN_FUTURE"
        assert "cannot be more than 5 days in the past" in error.message
        assert error.details["allow_past_days"] == 5

    def test_unreasonably_far_future_raises_exception(self):
        """Test that date more than 100 years in future raises exception."""
        far_future = datetime.now() + timedelta(days=365 * 150)  # 150 years

        with pytest.raises(DateValidationException) as exc_info:
            validate_future_date(far_future, field_name="due_date")

        error = exc_info.value
        assert error.error_code == "DATE_TOO_FAR_FUTURE"
        assert "unreasonably far in the future" in error.message
        assert "max_allowed" in error.details

    def test_non_datetime_raises_exception(self):
        """Test that non-datetime value raises exception."""
        with pytest.raises(DateValidationException) as exc_info:
            validate_future_date("2025-12-31", field_name="date")

        error = exc_info.value
        assert error.error_code == "INVALID_DATE_TYPE"
        assert "must be a datetime object" in error.message
        assert error.details["provided_type"] == "str"
        assert error.details["expected_type"] == "datetime"

    def test_integer_raises_exception(self):
        """Test that integer raises exception."""
        with pytest.raises(DateValidationException) as exc_info:
            validate_future_date(20251231, field_name="date")

        error = exc_info.value
        assert error.error_code == "INVALID_DATE_TYPE"


class TestValidateEmailFormat:
    """Test validate_email_format helper function."""

    def test_valid_simple_email(self):
        """Test that valid simple email is accepted and lowercased."""
        result = validate_email_format("user@example.com")
        assert result == "user@example.com"

    def test_valid_email_with_uppercase(self):
        """Test that email with uppercase is normalized to lowercase."""
        result = validate_email_format("User@EXAMPLE.COM")
        assert result == "user@example.com"

    def test_valid_email_with_dots(self):
        """Test email with dots in local part."""
        result = validate_email_format("john.doe@example.com")
        assert result == "john.doe@example.com"

    def test_valid_email_with_hyphens(self):
        """Test email with hyphens."""
        result = validate_email_format("user-name@example-site.com")
        assert result == "user-name@example-site.com"

    def test_valid_email_with_underscores(self):
        """Test email with underscores."""
        result = validate_email_format("user_123@example.com")
        assert result == "user_123@example.com"

    def test_valid_email_with_percent(self):
        """Test email with percent sign."""
        result = validate_email_format("user%tag@example.com")
        assert result == "user%tag@example.com"

    def test_valid_email_with_subdomain(self):
        """Test email with subdomain."""
        result = validate_email_format("admin@mail.example.com")
        assert result == "admin@mail.example.com"

    def test_valid_email_with_numbers(self):
        """Test email with numbers."""
        result = validate_email_format("user123@example456.com")
        assert result == "user123@example456.com"

    def test_valid_email_with_spaces_stripped(self):
        """Test that leading/trailing spaces are stripped."""
        result = validate_email_format("  user@example.com  ")
        assert result == "user@example.com"

    def test_empty_string_raises_exception(self):
        """Test that empty email raises exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_email_format("")

        error = exc_info.value
        assert error.error_code == "EMAIL_EMPTY"
        assert error.field_name == "email"
        assert "cannot be empty" in error.message

    def test_whitespace_only_raises_exception(self):
        """Test that whitespace-only email raises exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_email_format("   ")

        error = exc_info.value
        assert error.error_code == "EMAIL_EMPTY"

    def test_missing_at_symbol_raises_exception(self):
        """Test that email without @ raises exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_email_format("userexample.com")

        error = exc_info.value
        assert error.error_code == "EMAIL_MISSING_AT"
        assert "must contain '@' symbol" in error.message
        assert "hint" in error.details

    def test_multiple_at_symbols_raises_exception(self):
        """Test that email with multiple @ raises exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_email_format("user@name@example.com")

        error = exc_info.value
        assert error.error_code == "EMAIL_MULTIPLE_AT"
        assert "exactly one '@' symbol" in error.message

    def test_empty_local_part_raises_exception(self):
        """Test that email with no username raises exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_email_format("@example.com")

        error = exc_info.value
        assert error.error_code == "EMAIL_EMPTY_LOCAL"
        assert "username before '@'" in error.message

    def test_empty_domain_raises_exception(self):
        """Test that email with no domain raises exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_email_format("user@")

        error = exc_info.value
        assert error.error_code == "EMAIL_EMPTY_DOMAIN"
        assert "domain after '@'" in error.message

    def test_domain_without_tld_raises_exception(self):
        """Test that domain without TLD raises exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_email_format("user@example")

        error = exc_info.value
        assert error.error_code == "EMAIL_INVALID_DOMAIN"
        assert "must contain a period" in error.message
        assert "examples" in error.details

    def test_domain_starts_with_period_raises_exception(self):
        """Test that domain starting with period raises exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_email_format("user@.example.com")

        error = exc_info.value
        assert error.error_code == "EMAIL_INVALID_DOMAIN_FORMAT"
        assert "cannot start or end with a period" in error.message

    def test_domain_ends_with_period_raises_exception(self):
        """Test that domain ending with period raises exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_email_format("user@example.com.")

        error = exc_info.value
        assert error.error_code == "EMAIL_INVALID_DOMAIN_FORMAT"

    def test_invalid_characters_raises_exception(self):
        """Test that invalid characters raise exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_email_format("user name@example.com")  # space in username

        error = exc_info.value
        assert error.error_code == "EMAIL_INVALID_FORMAT"
        assert "invalid characters" in error.message

    def test_special_characters_raises_exception(self):
        """Test that certain special characters raise exception."""
        with pytest.raises(FieldValidationException):
            validate_email_format("user!@#$@example.com")


class TestValidateUsernameFormat:
    """Test validate_username_format helper function."""

    def test_valid_simple_username(self):
        """Test that valid simple username is accepted."""
        result = validate_username_format("john")
        assert result == "john"

    def test_valid_username_with_underscore(self):
        """Test username with underscore."""
        result = validate_username_format("john_doe")
        assert result == "john_doe"

    def test_valid_username_with_hyphen(self):
        """Test username with hyphen."""
        result = validate_username_format("john-doe")
        assert result == "john-doe"

    def test_valid_username_with_numbers(self):
        """Test username with numbers."""
        result = validate_username_format("user123")
        assert result == "user123"

    def test_valid_username_mixed(self):
        """Test username with mixed valid characters."""
        result = validate_username_format("Alice_Smith-99")
        assert result == "Alice_Smith-99"

    def test_valid_username_min_length(self):
        """Test username with minimum length (3 chars)."""
        result = validate_username_format("abc")
        assert result == "abc"

    def test_valid_username_max_length(self):
        """Test username with maximum length (30 chars)."""
        username = "a" * 30
        result = validate_username_format(username)
        assert result == username

    def test_valid_username_uppercase(self):
        """Test username with uppercase letters."""
        result = validate_username_format("JohnDoe")
        assert result == "JohnDoe"

    def test_valid_username_ending_with_number(self):
        """Test username ending with number."""
        result = validate_username_format("user1")
        assert result == "user1"

    def test_empty_string_raises_exception(self):
        """Test that empty username raises exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_username_format("")

        error = exc_info.value
        assert error.error_code == "USERNAME_EMPTY"
        assert error.field_name == "username"
        assert "cannot be empty" in error.message
        assert "rules" in error.details
        assert "examples" in error.details

    def test_whitespace_only_raises_exception(self):
        """Test that whitespace-only username raises exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_username_format("   ")

        error = exc_info.value
        assert error.error_code == "USERNAME_EMPTY"

    def test_too_short_raises_exception(self):
        """Test that username shorter than 3 chars raises exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_username_format("ab")

        error = exc_info.value
        assert error.error_code == "USERNAME_TOO_SHORT"
        assert "at least 3 characters" in error.message
        assert error.details["min_length"] == 3

    def test_too_long_raises_exception(self):
        """Test that username longer than 30 chars raises exception."""
        username = "a" * 31
        with pytest.raises(FieldValidationException) as exc_info:
            validate_username_format(username)

        error = exc_info.value
        assert error.error_code == "USERNAME_TOO_LONG"
        assert "at most 30 characters" in error.message
        assert error.details["max_length"] == 30

    def test_starts_with_number_raises_exception(self):
        """Test that username starting with number raises exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_username_format("123user")

        error = exc_info.value
        assert error.error_code == "USERNAME_INVALID_START"
        assert "must start with a letter" in error.message

    def test_starts_with_underscore_raises_exception(self):
        """Test that username starting with underscore raises exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_username_format("_user")

        error = exc_info.value
        assert error.error_code == "USERNAME_INVALID_START"

    def test_starts_with_hyphen_raises_exception(self):
        """Test that username starting with hyphen raises exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_username_format("-user")

        error = exc_info.value
        assert error.error_code == "USERNAME_INVALID_START"

    def test_ends_with_underscore_raises_exception(self):
        """Test that username ending with underscore raises exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_username_format("user_")

        error = exc_info.value
        assert error.error_code == "USERNAME_INVALID_END"
        assert "cannot end with" in error.message

    def test_ends_with_hyphen_raises_exception(self):
        """Test that username ending with hyphen raises exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_username_format("user-")

        error = exc_info.value
        assert error.error_code == "USERNAME_INVALID_END"

    def test_consecutive_underscores_raises_exception(self):
        """Test that consecutive underscores raise exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_username_format("user__name")

        error = exc_info.value
        assert error.error_code == "USERNAME_CONSECUTIVE_SPECIAL"
        assert "consecutive special characters" in error.message

    def test_consecutive_hyphens_raises_exception(self):
        """Test that consecutive hyphens raise exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_username_format("user--name")

        error = exc_info.value
        assert error.error_code == "USERNAME_CONSECUTIVE_SPECIAL"

    def test_mixed_consecutive_special_raises_exception(self):
        """Test that mixed consecutive special chars raise exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_username_format("user_-name")

        error = exc_info.value
        assert error.error_code == "USERNAME_CONSECUTIVE_SPECIAL"

    def test_space_raises_exception(self):
        """Test that space in username raises exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_username_format("john doe")

        error = exc_info.value
        assert error.error_code == "USERNAME_INVALID_CHARACTERS"
        assert "invalid characters" in error.message
        assert "invalid_characters" in error.details

    def test_special_characters_raises_exception(self):
        """Test that special characters raise exception."""
        with pytest.raises(FieldValidationException) as exc_info:
            validate_username_format("user@name")

        error = exc_info.value
        assert error.error_code == "USERNAME_INVALID_CHARACTERS"
        assert "@" in str(error.details["invalid_characters"])


class TestValidationContext:
    """Test ValidationContext class and validation_context context manager."""

    def test_validation_context_no_errors(self):
        """Test validation context with no errors passes silently."""
        with validation_context() as ctx:
            ctx.validate(lambda: validate_not_empty_string("valid", "field"))
            ctx.validate(lambda: validate_hex_color("#FF0000"))

        # Should not raise any exception

    def test_validation_context_single_error(self):
        """Test validation context with single error raises ValidationErrorCollection."""
        with pytest.raises(ValidationErrorCollection) as exc_info:
            with validation_context() as ctx:
                ctx.validate(lambda: validate_not_empty_string("", "username"))

        error = exc_info.value
        assert error.error_code == "MULTIPLE_VALIDATION_ERRORS"
        assert len(error.errors) == 1
        assert error.errors[0].error_code == "EMPTY_STRING_ERROR"

    def test_validation_context_multiple_errors(self):
        """Test validation context collects multiple errors."""
        with pytest.raises(ValidationErrorCollection) as exc_info:
            with validation_context() as ctx:
                ctx.validate(lambda: validate_not_empty_string("", "username"))
                ctx.validate(lambda: validate_hex_color("invalid"))
                ctx.validate(lambda: validate_email_format("not-an-email"))

        error = exc_info.value
        assert len(error.errors) == 3
        assert error.details["error_count"] == 3
        assert "3 errors" in error.message

    def test_validation_context_mixed_success_and_failure(self):
        """Test validation context with mix of successful and failed validations."""
        with pytest.raises(ValidationErrorCollection) as exc_info:
            with validation_context() as ctx:
                result1 = ctx.validate(lambda: validate_not_empty_string("valid", "field"))
                result2 = ctx.validate(lambda: validate_hex_color("invalid"))
                result3 = ctx.validate(lambda: validate_email_format("user@example.com"))
                result4 = ctx.validate(lambda: validate_username_format("ab"))

                assert result1 is True  # Should pass
                assert result2 is False  # Should fail
                assert result3 is True  # Should pass
                assert result4 is False  # Should fail

        error = exc_info.value
        assert len(error.errors) == 2  # Only 2 failures

    def test_validation_context_has_errors(self):
        """Test has_errors method returns correct status."""
        with pytest.raises(ValidationErrorCollection):
            with validation_context() as ctx:
                assert ctx.has_errors() is False

                ctx.validate(lambda: validate_hex_color("invalid"))

                assert ctx.has_errors() is True

    def test_validation_context_get_errors(self):
        """Test get_errors returns list of errors."""
        with pytest.raises(ValidationErrorCollection):
            with validation_context() as ctx:
                ctx.validate(lambda: validate_not_empty_string("", "field1"))
                ctx.validate(lambda: validate_hex_color("bad"))

                errors = ctx.get_errors()
                assert len(errors) == 2
                assert all(isinstance(e, TaskManagerException) for e in errors)

    def test_validation_context_add_error_manually(self):
        """Test manually adding errors with add_error method."""
        with pytest.raises(ValidationErrorCollection) as exc_info:
            with validation_context() as ctx:
                # Manually add an error
                manual_error = FieldValidationException(
                    field_name="custom",
                    message="Custom error message",
                    error_code="CUSTOM_ERROR"
                )
                ctx.add_error(manual_error)

        error = exc_info.value
        assert len(error.errors) == 1
        assert error.errors[0].error_code == "CUSTOM_ERROR"

    def test_validation_context_clear_errors(self):
        """Test clearing errors with clear_errors method."""
        # This test shows clear_errors works but still raises if errors added after
        with pytest.raises(ValidationErrorCollection):
            with validation_context() as ctx:
                ctx.validate(lambda: validate_hex_color("invalid"))
                assert ctx.has_errors() is True

                ctx.clear_errors()
                assert ctx.has_errors() is False

                # Add another error
                ctx.validate(lambda: validate_not_empty_string("", "field"))

    def test_validation_error_collection_format_errors(self):
        """Test ValidationErrorCollection format_errors method."""
        with pytest.raises(ValidationErrorCollection) as exc_info:
            with validation_context() as ctx:
                ctx.validate(lambda: validate_not_empty_string("", "username"))
                ctx.validate(lambda: validate_hex_color("#ZZZ"))

        error = exc_info.value
        formatted = error.format_errors(include_details=True)

        assert "Found 2 validation error(s)" in formatted
        assert "EMPTY_STRING_ERROR" in formatted
        assert "INVALID_COLOR_FORMAT" in formatted

    def test_validation_error_collection_format_errors_without_details(self):
        """Test format_errors without details."""
        with pytest.raises(ValidationErrorCollection) as exc_info:
            with validation_context() as ctx:
                ctx.validate(lambda: validate_not_empty_string("", "username"))

        error = exc_info.value
        formatted = error.format_errors(include_details=False)

        assert "Found 1 validation error(s)" in formatted
        assert "EMPTY_STRING_ERROR" in formatted

    def test_validation_error_collection_to_dict(self):
        """Test ValidationErrorCollection includes all errors in details."""
        with pytest.raises(ValidationErrorCollection) as exc_info:
            with validation_context() as ctx:
                ctx.validate(lambda: validate_not_empty_string("", "field1"))
                ctx.validate(lambda: validate_hex_color("bad"))

        error = exc_info.value
        error_dict = error.to_dict()

        assert error_dict["error_code"] == "MULTIPLE_VALIDATION_ERRORS"
        assert error_dict["details"]["error_count"] == 2
        assert len(error_dict["details"]["errors"]) == 2

    def test_validation_error_collection_str_representation(self):
        """Test string representation of ValidationErrorCollection."""
        with pytest.raises(ValidationErrorCollection) as exc_info:
            with validation_context() as ctx:
                ctx.validate(lambda: validate_not_empty_string("", "username"))

        error = exc_info.value
        error_str = str(error)

        assert "validation error" in error_str.lower()
        assert "username" in error_str

    def test_batch_validation_collects_all_errors_before_raising(self):
        """Test that batch validation collects ALL errors before raising exception."""
        all_validations_executed = []

        with pytest.raises(ValidationErrorCollection) as exc_info:
            with validation_context() as ctx:
                # All of these should be executed even though they all fail
                ctx.validate(lambda: (all_validations_executed.append(1), validate_not_empty_string("", "field1"))[1])
                ctx.validate(lambda: (all_validations_executed.append(2), validate_hex_color("bad"))[1])
                ctx.validate(lambda: (all_validations_executed.append(3), validate_email_format("invalid"))[1])
                ctx.validate(lambda: (all_validations_executed.append(4), validate_username_format("x"))[1])

        # Verify all 4 validations were executed
        assert all_validations_executed == [1, 2, 3, 4]

        # Verify all 4 errors were collected
        error = exc_info.value
        assert len(error.errors) == 4

    def test_validation_context_different_exception_types(self):
        """Test validation context with different exception types."""
        with pytest.raises(ValidationErrorCollection) as exc_info:
            with validation_context() as ctx:
                ctx.validate(lambda: validate_not_empty_string("", "name"))
                past = datetime.now() - timedelta(days=10)
                ctx.validate(lambda: validate_future_date(past, field_name="date"))
                ctx.validate(lambda: validate_email_format("@invalid"))

        error = exc_info.value
        assert len(error.errors) == 3

        # Check we have different exception types
        exception_types = [type(e).__name__ for e in error.errors]
        assert "FieldValidationException" in exception_types
        assert "DateValidationException" in exception_types


class TestValidationContextEdgeCases:
    """Test edge cases and special scenarios for validation context."""

    def test_empty_validation_context(self):
        """Test validation context with no validations passes silently."""
        with validation_context() as ctx:
            pass  # Do nothing

        # Should not raise

    def test_validation_context_with_only_successful_validations(self):
        """Test validation context with only passing validations."""
        with validation_context() as ctx:
            ctx.validate(lambda: validate_not_empty_string("valid", "field"))
            ctx.validate(lambda: validate_hex_color("#AABBCC"))
            ctx.validate(lambda: validate_email_format("test@example.com"))
            ctx.validate(lambda: validate_username_format("john_doe"))

        # Should not raise

    def test_validation_context_nested_validation_errors(self):
        """Test validation context properly captures nested validation details."""
        with pytest.raises(ValidationErrorCollection) as exc_info:
            with validation_context() as ctx:
                ctx.validate(lambda: validate_username_format("user__name"))  # Consecutive special chars

        error = exc_info.value
        assert len(error.errors) == 1
        nested_error = error.errors[0]
        assert nested_error.error_code == "USERNAME_CONSECUTIVE_SPECIAL"
        assert "consecutive special characters" in nested_error.message

    def test_direct_validation_context_class_usage(self):
        """Test using ValidationContext class directly without context manager."""
        ctx = ValidationContext()

        ctx.validate(lambda: validate_not_empty_string("", "field1"))
        ctx.validate(lambda: validate_hex_color("invalid"))

        assert ctx.has_errors() is True
        assert len(ctx.get_errors()) == 2

        # Manually raise if needed
        if ctx.has_errors():
            with pytest.raises(ValidationErrorCollection):
                raise ValidationErrorCollection(errors=ctx.get_errors())
