"""
Verification script for Step 2.4: Update User model validators.

This script verifies that all requirements of Step 2.4 have been implemented:
1. Username format validation with FieldValidationException
2. Enhanced email validator with common mistake detection
3. Duplicate task list name prevention
"""
import sys
from models import User, TaskList
from exceptions import FieldValidationException


def verify_username_validation():
    """Verify username format validation requirements."""
    print("Verifying Username Validation...")
    checks_passed = 0
    total_checks = 3

    # Check 1: Invalid characters raise FieldValidationException
    try:
        User(username="invalid-name", email="test@example.com")
        print("  ✗ Check 1 FAILED: Should reject invalid username format")
    except FieldValidationException as e:
        if e.error_code == "USERNAME_INVALID_FORMAT":
            print("  ✓ Check 1 PASSED: Raises FieldValidationException for invalid format")
            checks_passed += 1
        else:
            print(f"  ✗ Check 1 FAILED: Wrong error code: {e.error_code}")
    except Exception as e:
        print(f"  ✗ Check 1 FAILED: Wrong exception type: {type(e).__name__}")

    # Check 2: Error includes detailed information
    try:
        User(username="user@name", email="test@example.com")
    except FieldValidationException as e:
        if all(k in e.details for k in ["invalid_characters", "allowed_characters", "suggestion"]):
            print("  ✓ Check 2 PASSED: Error includes detailed information")
            checks_passed += 1
        else:
            print(f"  ✗ Check 2 FAILED: Missing details keys: {e.details.keys()}")
    except Exception as e:
        print(f"  ✗ Check 2 FAILED: Wrong exception type: {type(e).__name__}")

    # Check 3: Valid usernames are accepted
    try:
        user = User(username="valid_user123", email="test@example.com")
        print("  ✓ Check 3 PASSED: Valid usernames are accepted")
        checks_passed += 1
    except Exception as e:
        print(f"  ✗ Check 3 FAILED: Valid username rejected: {e}")

    print(f"  Result: {checks_passed}/{total_checks} checks passed\n")
    return checks_passed == total_checks


def verify_email_validation():
    """Verify email validation with common mistake detection."""
    print("Verifying Email Validation...")
    checks_passed = 0
    total_checks = 6

    # Check 1: Missing @ symbol detected
    try:
        User(username="testuser", email="testexample.com")
        print("  ✗ Check 1 FAILED: Should reject email without @")
    except FieldValidationException as e:
        if e.error_code == "EMAIL_MISSING_AT_SYMBOL":
            print("  ✓ Check 1 PASSED: Detects missing @ symbol")
            checks_passed += 1
        else:
            print(f"  ✗ Check 1 FAILED: Wrong error code: {e.error_code}")
    except Exception as e:
        print(f"  ✗ Check 1 FAILED: Wrong exception type: {type(e).__name__}")

    # Check 2: Multiple @ symbols detected
    try:
        User(username="testuser", email="test@example@com")
        print("  ✗ Check 2 FAILED: Should reject multiple @ symbols")
    except FieldValidationException as e:
        if e.error_code == "EMAIL_MULTIPLE_AT_SYMBOLS":
            print("  ✓ Check 2 PASSED: Detects multiple @ symbols")
            checks_passed += 1
        else:
            print(f"  ✗ Check 2 FAILED: Wrong error code: {e.error_code}")
    except Exception as e:
        print(f"  ✗ Check 2 FAILED: Wrong exception type: {type(e).__name__}")

    # Check 3: Missing domain extension detected
    try:
        User(username="testuser", email="test@example")
        print("  ✗ Check 3 FAILED: Should reject email without TLD")
    except FieldValidationException as e:
        if e.error_code == "EMAIL_MISSING_TLD":
            print("  ✓ Check 3 PASSED: Detects missing domain extension")
            checks_passed += 1
        else:
            print(f"  ✗ Check 3 FAILED: Wrong error code: {e.error_code}")
    except Exception as e:
        print(f"  ✗ Check 3 FAILED: Wrong exception type: {type(e).__name__}")

    # Check 4: Invalid domain detected
    try:
        User(username="testuser", email="@example.com")
        print("  ✗ Check 4 FAILED: Should reject empty local part")
    except FieldValidationException as e:
        if e.error_code == "EMAIL_EMPTY_LOCAL_PART":
            print("  ✓ Check 4 PASSED: Detects empty username part")
            checks_passed += 1
        else:
            print(f"  ✗ Check 4 FAILED: Wrong error code: {e.error_code}")
    except Exception as e:
        print(f"  ✗ Check 4 FAILED: Wrong exception type: {type(e).__name__}")

    # Check 5: Error messages include helpful details
    try:
        User(username="testuser", email="invalid")
        print("  ✗ Check 5 FAILED: Should reject invalid email")
    except FieldValidationException as e:
        if all(k in e.details for k in ["expected_format", "suggestion"]):
            print("  ✓ Check 5 PASSED: Error includes helpful details")
            checks_passed += 1
        else:
            print(f"  ✗ Check 5 FAILED: Missing details keys: {e.details.keys()}")
    except Exception as e:
        print(f"  ✗ Check 5 FAILED: Wrong exception type: {type(e).__name__}")

    # Check 6: Valid emails are accepted and normalized
    try:
        user = User(username="testuser", email="Test@Example.COM")
        if user.email == "test@example.com":
            print("  ✓ Check 6 PASSED: Valid emails accepted and normalized")
            checks_passed += 1
        else:
            print(f"  ✗ Check 6 FAILED: Email not normalized: {user.email}")
    except Exception as e:
        print(f"  ✗ Check 6 FAILED: Valid email rejected: {e}")

    print(f"  Result: {checks_passed}/{total_checks} checks passed\n")
    return checks_passed == total_checks


def verify_duplicate_task_list_prevention():
    """Verify duplicate task list name prevention."""
    print("Verifying Duplicate Task List Name Prevention...")
    checks_passed = 0
    total_checks = 4

    # Check 1: Exact duplicates detected
    try:
        list1 = TaskList(name="Work", owner="user1")
        list2 = TaskList(name="Work", owner="user1")
        User(username="testuser", email="test@example.com", task_lists=[list1, list2])
        print("  ✗ Check 1 FAILED: Should reject duplicate task list names")
    except FieldValidationException as e:
        if e.error_code == "DUPLICATE_TASKLIST_NAMES":
            print("  ✓ Check 1 PASSED: Detects exact duplicate names")
            checks_passed += 1
        else:
            print(f"  ✗ Check 1 FAILED: Wrong error code: {e.error_code}")
    except Exception as e:
        print(f"  ✗ Check 1 FAILED: Wrong exception type: {type(e).__name__}")

    # Check 2: Case-insensitive duplicates detected
    try:
        list1 = TaskList(name="Work", owner="user1")
        list2 = TaskList(name="WORK", owner="user1")
        User(username="testuser", email="test@example.com", task_lists=[list1, list2])
        print("  ✗ Check 2 FAILED: Should reject case-insensitive duplicates")
    except FieldValidationException as e:
        if e.error_code == "DUPLICATE_TASKLIST_NAMES":
            print("  ✓ Check 2 PASSED: Detects case-insensitive duplicates")
            checks_passed += 1
        else:
            print(f"  ✗ Check 2 FAILED: Wrong error code: {e.error_code}")
    except Exception as e:
        print(f"  ✗ Check 2 FAILED: Wrong exception type: {type(e).__name__}")

    # Check 3: Error includes detailed information
    try:
        list1 = TaskList(name="Work", owner="user1")
        list2 = TaskList(name="Work", owner="user1")
        User(username="testuser", email="test@example.com", task_lists=[list1, list2])
    except FieldValidationException as e:
        if all(k in e.details for k in ["duplicate_names", "total_lists", "unique_names"]):
            print("  ✓ Check 3 PASSED: Error includes detailed information")
            checks_passed += 1
        else:
            print(f"  ✗ Check 3 FAILED: Missing details keys: {e.details.keys()}")
    except Exception as e:
        print(f"  ✗ Check 3 FAILED: Wrong exception type: {type(e).__name__}")

    # Check 4: Unique names are accepted
    try:
        list1 = TaskList(name="Work", owner="user1")
        list2 = TaskList(name="Personal", owner="user1")
        list3 = TaskList(name="Shopping", owner="user1")
        user = User(username="testuser", email="test@example.com",
                   task_lists=[list1, list2, list3])
        if len(user.task_lists) == 3:
            print("  ✓ Check 4 PASSED: Unique task list names accepted")
            checks_passed += 1
        else:
            print(f"  ✗ Check 4 FAILED: Wrong number of task lists: {len(user.task_lists)}")
    except Exception as e:
        print(f"  ✗ Check 4 FAILED: Unique names rejected: {e}")

    print(f"  Result: {checks_passed}/{total_checks} checks passed\n")
    return checks_passed == total_checks


def main():
    """Run all verification checks."""
    print("=" * 70)
    print("STEP 2.4 VERIFICATION: Update User Model Validators")
    print("=" * 70)
    print()

    results = []

    # Run all verification checks
    results.append(("Username Validation", verify_username_validation()))
    results.append(("Email Validation", verify_email_validation()))
    results.append(("Duplicate Task List Prevention", verify_duplicate_task_list_prevention()))

    # Summary
    print("=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {name}")

    total_passed = sum(1 for _, passed in results if passed)
    total_checks = len(results)

    print()
    print(f"Overall Result: {total_passed}/{total_checks} requirement groups passed")
    print("=" * 70)

    # Exit with appropriate code
    if total_passed == total_checks:
        print("\n✓ All Step 2.4 requirements verified successfully!")
        return 0
    else:
        print("\n✗ Some Step 2.4 requirements failed verification!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
