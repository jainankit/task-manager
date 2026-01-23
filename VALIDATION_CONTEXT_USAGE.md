# Validation Context Manager Usage Guide

## Overview

The `validation_context()` context manager provides batch validation functionality that collects multiple validation errors and reports them all at once, instead of failing on the first error. This creates a better user experience by showing all validation issues that need to be fixed in a single response.

## Key Components

### 1. ValidationContext Class

A helper class that collects validation errors during the validation process.

**Methods:**
- `validate(validation_func)` - Execute a validation function and collect any errors
- `add_error(error)` - Manually add an error to the collection
- `has_errors()` - Check if any errors have been collected
- `get_errors()` - Get the list of collected errors
- `clear_errors()` - Clear all collected errors

### 2. validation_context() Function

A context manager that creates a ValidationContext and raises a `ValidationErrorCollection` if any errors were collected during validation.

### 3. ValidationErrorCollection Exception

An exception class that holds multiple validation errors and provides formatted output.

**Methods:**
- `format_errors(include_details=True)` - Format all errors for user-friendly display

## Basic Usage

```python
from validation_utils import validation_context, validate_email_format, validate_username_format
from exceptions import ValidationErrorCollection

# Batch validation - all errors collected before raising
try:
    with validation_context() as ctx:
        ctx.validate(lambda: validate_username_format(username))
        ctx.validate(lambda: validate_email_format(email))
    # If we reach here, all validations passed
    print("All validations passed!")
except ValidationErrorCollection as e:
    # Handle multiple validation errors
    print(f"Found {len(e.errors)} validation errors:")
    print(e.format_errors())
```

## Advanced Usage Patterns

### 1. Checking Validation Results

```python
with validation_context() as ctx:
    username_valid = ctx.validate(lambda: validate_username_format(username))
    email_valid = ctx.validate(lambda: validate_email_format(email))

    print(f"Username valid: {username_valid}")
    print(f"Email valid: {email_valid}")

    if ctx.has_errors():
        print(f"Found {len(ctx.get_errors())} errors")
# ValidationErrorCollection raised here if any errors exist
```

### 2. Manually Adding Custom Errors

```python
from exceptions import FieldValidationException

with validation_context() as ctx:
    # Automatic validation
    ctx.validate(lambda: validate_email_format(email))

    # Manual validation with custom error
    if email.endswith("@tempmail.com"):
        ctx.add_error(
            FieldValidationException(
                field_name="email",
                message="Temporary email addresses are not allowed",
                invalid_value=email,
                error_code="TEMP_EMAIL_NOT_ALLOWED"
            )
        )
```

### 3. Conditional Validation

```python
with validation_context() as ctx:
    ctx.validate(lambda: validate_not_empty_string(title, "title"))

    # Only validate due_date if it was provided
    if due_date is not None:
        ctx.validate(lambda: validate_future_date(due_date, field_name="due_date"))

    # Validate tags if any were provided
    for tag_color in tag_colors:
        ctx.validate(lambda: validate_hex_color(tag_color))
```

## Error Formatting

The `ValidationErrorCollection` provides rich formatting for error display:

```python
try:
    with validation_context() as ctx:
        ctx.validate(lambda: validate_username_format("ab"))  # Too short
        ctx.validate(lambda: validate_email_format("invalid"))  # No @
        ctx.validate(lambda: validate_hex_color("red"))  # Wrong format
except ValidationErrorCollection as e:
    # Formatted output with details
    print(e.format_errors(include_details=True))

    # Formatted output without details (brief)
    print(e.format_errors(include_details=False))

    # Access individual errors
    for error in e.errors:
        print(f"Error: {error.error_code} - {error.message}")
        print(f"Field: {error.field_name}")
        print(f"Details: {error.details}")
```

## Real-World Example

```python
def validate_task_creation(title: str, description: str, due_date: datetime,
                          tags: list[dict]) -> dict:
    """
    Validate all task creation inputs at once.

    Raises:
        ValidationErrorCollection: If any validation errors occur
    """
    with validation_context() as ctx:
        # Validate required fields
        ctx.validate(lambda: validate_not_empty_string(title, "title"))
        ctx.validate(lambda: validate_not_empty_string(description, "description"))

        # Validate due date
        ctx.validate(lambda: validate_future_date(due_date, field_name="due_date"))

        # Validate all tags
        for i, tag in enumerate(tags):
            ctx.validate(lambda: validate_not_empty_string(tag['name'], f"tags[{i}].name"))
            ctx.validate(lambda: validate_hex_color(tag['color']))

    # All validations passed, return normalized data
    return {
        "title": title.strip(),
        "description": description.strip(),
        "due_date": due_date,
        "tags": tags
    }

# Usage
try:
    task_data = validate_task_creation(
        title="  Important Task  ",
        description="Task description",
        due_date=datetime.now() + timedelta(days=7),
        tags=[
            {"name": "urgent", "color": "#FF0000"},
            {"name": "", "color": "BLUE"},  # Two errors: empty name, invalid color
        ]
    )
    print("Task validated successfully!")
except ValidationErrorCollection as e:
    # All 2 errors (empty tag name + invalid color) reported together
    print(e.format_errors())
```

## Benefits

1. **Better User Experience**: Users see all validation errors at once, rather than fixing one error only to discover another.

2. **Efficient Validation**: All validations run even if some fail, providing complete feedback.

3. **Consistent Error Format**: All errors use the same exception hierarchy with detailed context.

4. **Flexible**: Supports both automatic validation via helper functions and manual error addition.

5. **Rich Context**: Each error includes field names, invalid values, error codes, and helpful suggestions.

## Integration with Existing Validation Functions

All validation utility functions work seamlessly with the validation context:

- `validate_not_empty_string(value, field_name)`
- `validate_hex_color(value)`
- `validate_future_date(value, allow_past_days, field_name)`
- `validate_email_format(value)`
- `validate_username_format(value)`

Each of these functions raises `TaskManagerException` subclasses that are automatically caught and collected by the validation context.
