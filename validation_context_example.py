"""
Example demonstrating the validation context manager usage.

This file shows practical examples of how to use validation_context() for
batch validation of user inputs.
"""
from validation_utils import (
    validation_context,
    validate_not_empty_string,
    validate_email_format,
    validate_hex_color,
    validate_username_format,
    ValidationContext
)
from exceptions import ValidationErrorCollection


def validate_user_registration(username: str, email: str, bio: str) -> dict:
    """
    Validate user registration data and report all errors at once.

    Args:
        username: The username to validate
        email: The email address to validate
        bio: The user biography to validate

    Returns:
        Dictionary with validation results

    Raises:
        ValidationErrorCollection: If any validation errors occur
    """
    with validation_context() as ctx:
        # Validate all fields and collect errors
        ctx.validate(lambda: validate_username_format(username))
        ctx.validate(lambda: validate_email_format(email))
        ctx.validate(lambda: validate_not_empty_string(bio, "bio"))

    # If we get here, all validations passed
    return {
        "username": username,
        "email": email.lower(),
        "bio": bio.strip()
    }


def validate_tag_creation(name: str, color: str, description: str) -> dict:
    """
    Validate tag creation data with batch validation.

    Args:
        name: The tag name
        color: The tag color in hex format
        description: The tag description

    Returns:
        Dictionary with validated tag data

    Raises:
        ValidationErrorCollection: If any validation errors occur
    """
    with validation_context() as ctx:
        ctx.validate(lambda: validate_not_empty_string(name, "name"))
        ctx.validate(lambda: validate_hex_color(color))
        ctx.validate(lambda: validate_not_empty_string(description, "description"))

    return {
        "name": name.strip(),
        "color": color.upper(),
        "description": description.strip()
    }


def example_successful_validation():
    """Example of successful validation."""
    print("Example 1: Successful validation")
    print("-" * 50)

    try:
        result = validate_user_registration(
            username="john_doe",
            email="john@example.com",
            bio="Software developer"
        )
        print("✓ Validation passed!")
        print(f"  Validated data: {result}")
    except ValidationErrorCollection as e:
        print(f"✗ Validation failed: {e}")

    print()


def example_multiple_errors():
    """Example of validation with multiple errors."""
    print("Example 2: Multiple validation errors")
    print("-" * 50)

    try:
        result = validate_user_registration(
            username="ab",  # Too short
            email="invalid-email",  # Missing @
            bio="   "  # Empty/whitespace
        )
        print("✓ Validation passed!")
        print(f"  Validated data: {result}")
    except ValidationErrorCollection as e:
        print(f"✗ Validation failed with {len(e.errors)} errors:")
        print()
        print(e.format_errors(include_details=True))

    print()


def example_partial_errors():
    """Example with some valid and some invalid fields."""
    print("Example 3: Partial validation errors")
    print("-" * 50)

    try:
        result = validate_tag_creation(
            name="Important",  # Valid
            color="FF0000",  # Invalid - missing #
            description="High priority items"  # Valid
        )
        print("✓ Validation passed!")
        print(f"  Validated data: {result}")
    except ValidationErrorCollection as e:
        print(f"✗ Validation failed with {len(e.errors)} error(s):")
        print()
        print(e.format_errors(include_details=True))

    print()


def example_manual_error_collection():
    """Example of manually adding errors to the context."""
    print("Example 4: Manual error collection")
    print("-" * 50)

    from exceptions import FieldValidationException

    try:
        with validation_context() as ctx:
            # Use automatic validation
            ctx.validate(lambda: validate_username_format("john123"))

            # Manually add a custom validation error
            if "john" in "john123".lower():
                ctx.add_error(
                    FieldValidationException(
                        field_name="username",
                        message="Username cannot contain the word 'john' (reserved)",
                        invalid_value="john123",
                        error_code="RESERVED_USERNAME",
                        details={
                            "suggestion": "Choose a different username without reserved words"
                        }
                    )
                )

            ctx.validate(lambda: validate_email_format("john@example.com"))

        print("✓ All validations passed")
    except ValidationErrorCollection as e:
        print(f"✗ Validation failed with {len(e.errors)} error(s):")
        print()
        print(e.format_errors(include_details=True))

    print()


def example_checking_errors_before_exit():
    """Example of checking for errors before context exits."""
    print("Example 5: Checking errors during validation")
    print("-" * 50)

    try:
        with validation_context() as ctx:
            result1 = ctx.validate(lambda: validate_username_format("alice"))
            result2 = ctx.validate(lambda: validate_email_format("bad-email"))
            result3 = ctx.validate(lambda: validate_hex_color("#FF0000"))

            print(f"  Username validation: {'✓ passed' if result1 else '✗ failed'}")
            print(f"  Email validation: {'✓ passed' if result2 else '✗ failed'}")
            print(f"  Color validation: {'✓ passed' if result3 else '✗ failed'}")
            print(f"\n  Total errors collected: {len(ctx.get_errors())}")

            if ctx.has_errors():
                print(f"  ⚠ Warning: {len(ctx.get_errors())} error(s) will be raised on exit")

        print("\n✓ All validations passed")
    except ValidationErrorCollection as e:
        print(f"\n✗ ValidationErrorCollection raised on context exit")
        print(f"   Error count: {len(e.errors)}")

    print()


if __name__ == "__main__":
    print("=" * 70)
    print("Validation Context Manager - Practical Examples")
    print("=" * 70)
    print()

    example_successful_validation()
    example_multiple_errors()
    example_partial_errors()
    example_manual_error_collection()
    example_checking_errors_before_exit()

    print("=" * 70)
    print("Examples completed!")
    print("=" * 70)
