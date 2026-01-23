"""
Demonstration script for validation_utils.py helper functions.

This script showcases all the validation helper functions with various test cases.
"""

from datetime import datetime, timedelta
from validation_utils import (
    validate_not_empty_string,
    validate_hex_color,
    validate_future_date,
    validate_email_format,
    validate_username_format
)
from exceptions import FieldValidationException, DateValidationException


def demo_validate_not_empty_string():
    """Demonstrate validate_not_empty_string function."""
    print("=" * 70)
    print("DEMO: validate_not_empty_string(value, field_name)")
    print("=" * 70)

    test_cases = [
        ("Hello World", "title", True),
        ("  Trimmed  ", "name", True),
        ("", "description", False),
        ("   ", "content", False),
        ("\t\n", "text", False),
    ]

    for value, field_name, should_pass in test_cases:
        try:
            result = validate_not_empty_string(value, field_name)
            print(f"✓ PASS: '{value}' -> '{result}'")
            if not should_pass:
                print(f"  WARNING: Expected to fail but passed!")
        except FieldValidationException as e:
            if should_pass:
                print(f"✗ FAIL: '{value}' -> {e.error_code}: {e.message}")
            else:
                print(f"✓ EXPECTED: '{value}' -> {e.error_code}")
                print(f"  Message: {e.message}")
    print()


def demo_validate_hex_color():
    """Demonstrate validate_hex_color function."""
    print("=" * 70)
    print("DEMO: validate_hex_color(value)")
    print("=" * 70)

    test_cases = [
        ("#FF0000", True),
        ("#00ff00", True),
        ("#0000FF", True),
        ("#808080", True),
        ("FF0000", False),  # Missing #
        ("#FF00", False),    # Too short
        ("#FF00000", False), # Too long
        ("#GGGGGG", False),  # Invalid hex
        ("", False),         # Empty
    ]

    for value, should_pass in test_cases:
        try:
            result = validate_hex_color(value)
            print(f"✓ PASS: '{value}' -> '{result}'")
            if not should_pass:
                print(f"  WARNING: Expected to fail but passed!")
        except FieldValidationException as e:
            if should_pass:
                print(f"✗ FAIL: '{value}' -> {e.error_code}")
            else:
                print(f"✓ EXPECTED: '{value}' -> {e.error_code}")
                if 'hint' in e.details:
                    print(f"  Hint: {e.details['hint']}")
    print()


def demo_validate_future_date():
    """Demonstrate validate_future_date function."""
    print("=" * 70)
    print("DEMO: validate_future_date(value, allow_past_days, field_name)")
    print("=" * 70)

    now = datetime.now()

    test_cases = [
        (now + timedelta(days=7), 0, "due_date", True),
        (now + timedelta(hours=1), 0, "reminder", True),
        (now - timedelta(days=1), 0, "deadline", False),
        (now - timedelta(days=1), 2, "deadline", True),  # Allowed 2 days in past
        (now + timedelta(days=365*150), 0, "far_future", False),  # Too far in future
    ]

    for date_value, allow_past, field_name, should_pass in test_cases:
        try:
            result = validate_future_date(date_value, allow_past_days=allow_past, field_name=field_name)
            relative = "future" if date_value > now else "past"
            print(f"✓ PASS: {relative} date (allow_past_days={allow_past})")
            if not should_pass:
                print(f"  WARNING: Expected to fail but passed!")
        except DateValidationException as e:
            if should_pass:
                print(f"✗ FAIL: {e.error_code}")
            else:
                print(f"✓ EXPECTED: {e.error_code}")
                if 'hint' in e.details:
                    print(f"  Hint: {e.details['hint']}")
    print()


def demo_validate_email_format():
    """Demonstrate validate_email_format function."""
    print("=" * 70)
    print("DEMO: validate_email_format(value)")
    print("=" * 70)

    test_cases = [
        ("user@example.com", True),
        ("John.Doe@Company.COM", True),
        ("admin_123@site.co.uk", True),
        ("test+tag@domain.org", True),
        ("invalid-email", False),      # Missing @
        ("@example.com", False),        # Missing local part
        ("user@", False),               # Missing domain
        ("user@@example.com", False),   # Multiple @
        ("user@domain", False),         # Missing TLD
        ("user@.example.com", False),   # Domain starts with dot
        ("", False),                    # Empty
    ]

    for email, should_pass in test_cases:
        try:
            result = validate_email_format(email)
            print(f"✓ PASS: '{email}' -> '{result}'")
            if not should_pass:
                print(f"  WARNING: Expected to fail but passed!")
        except FieldValidationException as e:
            if should_pass:
                print(f"✗ FAIL: '{email}' -> {e.error_code}")
            else:
                print(f"✓ EXPECTED: '{email}' -> {e.error_code}")
                if 'hint' in e.details:
                    print(f"  Hint: {e.details['hint']}")
    print()


def demo_validate_username_format():
    """Demonstrate validate_username_format function."""
    print("=" * 70)
    print("DEMO: validate_username_format(value)")
    print("=" * 70)

    test_cases = [
        ("john_doe", True),
        ("alice123", True),
        ("Bob-Smith", True),
        ("user_name_123", True),
        ("ab", False),              # Too short
        ("a" * 31, False),          # Too long
        ("123user", False),         # Doesn't start with letter
        ("user_", False),           # Ends with underscore
        ("user-", False),           # Ends with hyphen
        ("user__name", False),      # Consecutive underscores
        ("user--name", False),      # Consecutive hyphens
        ("user@name", False),       # Invalid character
        ("user name", False),       # Contains space
        ("", False),                # Empty
    ]

    for username, should_pass in test_cases:
        try:
            result = validate_username_format(username)
            print(f"✓ PASS: '{username}' -> '{result}'")
            if not should_pass:
                print(f"  WARNING: Expected to fail but passed!")
        except FieldValidationException as e:
            if should_pass:
                print(f"✗ FAIL: '{username}' -> {e.error_code}")
            else:
                print(f"✓ EXPECTED: '{username}' -> {e.error_code}")
                if 'hint' in e.details:
                    print(f"  Hint: {e.details['hint']}")
    print()


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("VALIDATION UTILITIES DEMONSTRATION")
    print("=" * 70)
    print()

    demo_validate_not_empty_string()
    demo_validate_hex_color()
    demo_validate_future_date()
    demo_validate_email_format()
    demo_validate_username_format()

    print("=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
