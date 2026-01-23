#!/usr/bin/env python3
"""Quick verification script for exceptions.py"""

import sys

try:
    from exceptions import (
        TaskManagerException,
        ValidationException,
        FieldValidationException,
        StateValidationException
    )

    # Verify all classes exist
    assert TaskManagerException is not None
    assert ValidationException is not None
    assert FieldValidationException is not None
    assert StateValidationException is not None

    # Verify inheritance
    assert issubclass(ValidationException, TaskManagerException)
    assert issubclass(FieldValidationException, ValidationException)
    assert issubclass(StateValidationException, ValidationException)

    # Test basic instantiation
    exc1 = TaskManagerException("test", "TEST", {"key": "value"}, "field")
    assert exc1.message == "test"
    assert exc1.error_code == "TEST"
    assert exc1.details == {"key": "value"}
    assert exc1.field_name == "field"

    exc2 = ValidationException("validation error", field_name="email")
    assert exc2.error_code == "VALIDATION_ERROR"
    assert exc2.field_name == "email"

    exc3 = FieldValidationException("color", "Invalid color", invalid_value="red")
    assert exc3.field_name == "color"
    assert exc3.details["invalid_value"] == "red"

    exc4 = StateValidationException(
        "Invalid transition",
        current_state="archived",
        attempted_state="done"
    )
    assert exc4.details["current_state"] == "archived"
    assert exc4.details["attempted_state"] == "done"

    print("✅ All verification checks passed!")
    print("\nException classes defined:")
    print("  - TaskManagerException (base)")
    print("  - ValidationException")
    print("  - FieldValidationException")
    print("  - StateValidationException")

    sys.exit(0)

except Exception as e:
    print(f"❌ Verification failed: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
