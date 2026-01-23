"""
Demonstration of Step 2.4: Enhanced User model validators.

This script demonstrates the improved error handling for the User model:
1. Username validation with detailed error messages
2. Email validation with common mistake detection
3. Duplicate task list name prevention
"""
from models import User, TaskList, Task
from exceptions import FieldValidationException


def demo_username_validation():
    """Demonstrate username validation."""
    print("=" * 70)
    print("DEMO: Username Validation")
    print("=" * 70)

    # Valid username
    print("\n1. Valid username:")
    try:
        user = User(username="john_doe", email="john@example.com")
        print(f"   ✓ Created user with username: {user.username}")
    except FieldValidationException as e:
        print(f"   ✗ Error: {e}")

    # Invalid username with spaces
    print("\n2. Invalid username with spaces:")
    try:
        user = User(username="john doe", email="john@example.com")
        print(f"   ✓ Created user with username: {user.username}")
    except FieldValidationException as e:
        print(f"   ✗ Error Code: {e.error_code}")
        print(f"   ✗ Message: {e.message}")
        print(f"   ✗ Invalid chars: {e.details.get('invalid_characters')}")
        print(f"   ✗ Suggestion: {e.details.get('suggestion')}")

    # Invalid username with special characters
    print("\n3. Invalid username with special characters:")
    try:
        user = User(username="john@doe", email="john@example.com")
        print(f"   ✓ Created user with username: {user.username}")
    except FieldValidationException as e:
        print(f"   ✗ Error Code: {e.error_code}")
        print(f"   ✗ Message: {e.message}")
        print(f"   ✗ Invalid chars: {e.details.get('invalid_characters')}")
        print(f"   ✗ Examples: {e.details.get('examples')}")


def demo_email_validation():
    """Demonstrate email validation."""
    print("\n" + "=" * 70)
    print("DEMO: Email Validation")
    print("=" * 70)

    # Valid email
    print("\n1. Valid email:")
    try:
        user = User(username="testuser", email="test@example.com")
        print(f"   ✓ Created user with email: {user.email}")
    except FieldValidationException as e:
        print(f"   ✗ Error: {e}")

    # Missing @ symbol
    print("\n2. Email missing @ symbol:")
    try:
        user = User(username="testuser", email="testexample.com")
        print(f"   ✓ Created user with email: {user.email}")
    except FieldValidationException as e:
        print(f"   ✗ Error Code: {e.error_code}")
        print(f"   ✗ Message: {e.message}")
        print(f"   ✗ Invalid value: {e.details.get('invalid_value')}")
        print(f"   ✗ Suggestion: {e.details.get('suggestion')}")

    # Missing domain extension (TLD)
    print("\n3. Email missing domain extension:")
    try:
        user = User(username="testuser", email="test@example")
        print(f"   ✓ Created user with email: {user.email}")
    except FieldValidationException as e:
        print(f"   ✗ Error Code: {e.error_code}")
        print(f"   ✗ Message: {e.message}")
        print(f"   ✗ Domain provided: {e.details.get('domain_provided')}")
        print(f"   ✗ Examples: {e.details.get('examples')}")

    # Empty local part
    print("\n4. Email with empty username part:")
    try:
        user = User(username="testuser", email="@example.com")
        print(f"   ✓ Created user with email: {user.email}")
    except FieldValidationException as e:
        print(f"   ✗ Error Code: {e.error_code}")
        print(f"   ✗ Message: {e.message}")

    # Multiple @ symbols
    print("\n5. Email with multiple @ symbols:")
    try:
        user = User(username="testuser", email="test@example@com")
        print(f"   ✓ Created user with email: {user.email}")
    except FieldValidationException as e:
        print(f"   ✗ Error Code: {e.error_code}")
        print(f"   ✗ Message: {e.message}")
        print(f"   ✗ @ symbol count: {e.details.get('at_symbol_count')}")


def demo_duplicate_task_list_names():
    """Demonstrate duplicate task list name validation."""
    print("\n" + "=" * 70)
    print("DEMO: Duplicate Task List Name Prevention")
    print("=" * 70)

    # Valid unique task list names
    print("\n1. Valid unique task list names:")
    try:
        list1 = TaskList(name="Work", owner="user1")
        list2 = TaskList(name="Personal", owner="user1")
        list3 = TaskList(name="Shopping", owner="user1")

        user = User(
            username="testuser",
            email="test@example.com",
            task_lists=[list1, list2, list3]
        )
        print(f"   ✓ Created user with {len(user.task_lists)} task lists:")
        for tl in user.task_lists:
            print(f"      - {tl.name}")
    except FieldValidationException as e:
        print(f"   ✗ Error: {e}")

    # Duplicate task list names
    print("\n2. Duplicate task list names:")
    try:
        list1 = TaskList(name="Work", owner="user1")
        list2 = TaskList(name="Personal", owner="user1")
        list3 = TaskList(name="Work", owner="user1")  # Duplicate

        user = User(
            username="testuser",
            email="test@example.com",
            task_lists=[list1, list2, list3]
        )
        print(f"   ✓ Created user with {len(user.task_lists)} task lists")
    except FieldValidationException as e:
        print(f"   ✗ Error Code: {e.error_code}")
        print(f"   ✗ Message: {e.message}")
        print(f"   ✗ Duplicate names: {e.details.get('duplicate_names')}")
        print(f"   ✗ Total lists: {e.details.get('total_lists')}")
        print(f"   ✗ Unique names: {e.details.get('unique_names')}")

    # Case-insensitive duplicate detection
    print("\n3. Case-insensitive duplicate detection:")
    try:
        list1 = TaskList(name="Work", owner="user1")
        list2 = TaskList(name="WORK", owner="user1")  # Different case
        list3 = TaskList(name="work", owner="user1")  # Different case

        user = User(
            username="testuser",
            email="test@example.com",
            task_lists=[list1, list2, list3]
        )
        print(f"   ✓ Created user with {len(user.task_lists)} task lists")
    except FieldValidationException as e:
        print(f"   ✗ Error Code: {e.error_code}")
        print(f"   ✗ Message: {e.message}")
        print(f"   ✗ Duplicate names: {e.details.get('duplicate_names')}")
        print(f"   ✗ Comparison: {e.details.get('comparison')}")
        print(f"   ✗ Suggestion: {e.details.get('suggestion')}")


def main():
    """Run all demonstrations."""
    print("\n")
    print("*" * 70)
    print("* Step 2.4: User Model Validator Enhancements")
    print("*" * 70)
    print("\nThis demo showcases the enhanced error handling for User model:")
    print("- Username format validation with detailed error messages")
    print("- Email validation detecting common mistakes")
    print("- Prevention of duplicate task list names (case-insensitive)")

    demo_username_validation()
    demo_email_validation()
    demo_duplicate_task_list_names()

    print("\n" + "=" * 70)
    print("Demo completed!")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
