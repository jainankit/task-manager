"""
Basic verification tests for the exception classes.
"""
from exceptions import (
    TaskManagerException,
    ValidationException,
    FieldValidationException,
    StateValidationException
)


def test_base_exception():
    """Test TaskManagerException initialization and attributes."""
    exc = TaskManagerException(
        message='Test error',
        error_code='TEST_ERROR',
        details={'key': 'value'},
        field_name='test_field'
    )

    assert exc.message == 'Test error'
    assert exc.error_code == 'TEST_ERROR'
    assert exc.details == {'key': 'value'}
    assert exc.field_name == 'test_field'
    assert '[TEST_ERROR]' in str(exc)
    assert 'test_field' in str(exc)

    # Test to_dict method
    exc_dict = exc.to_dict()
    assert exc_dict['error_code'] == 'TEST_ERROR'
    assert exc_dict['message'] == 'Test error'
    assert exc_dict['field_name'] == 'test_field'
    assert exc_dict['details'] == {'key': 'value'}

    print("✓ TaskManagerException test passed")


def test_validation_exception():
    """Test ValidationException initialization."""
    exc = ValidationException(
        message='Invalid data',
        field_name='email'
    )

    assert exc.message == 'Invalid data'
    assert exc.error_code == 'VALIDATION_ERROR'
    assert exc.field_name == 'email'
    assert isinstance(exc, TaskManagerException)

    print("✓ ValidationException test passed")


def test_field_validation_exception():
    """Test FieldValidationException with invalid value."""
    exc = FieldValidationException(
        field_name='color',
        message='Color must be in hex format #RRGGBB',
        invalid_value='red'
    )

    assert exc.field_name == 'color'
    assert exc.message == 'Color must be in hex format #RRGGBB'
    assert exc.error_code == 'FIELD_VALIDATION_ERROR'
    assert exc.details['invalid_value'] == 'red'
    assert isinstance(exc, ValidationException)
    assert isinstance(exc, TaskManagerException)

    print("✓ FieldValidationException test passed")


def test_state_validation_exception():
    """Test StateValidationException with state information."""
    exc = StateValidationException(
        message='Cannot mark archived task as complete',
        current_state='archived',
        attempted_state='done'
    )

    assert exc.message == 'Cannot mark archived task as complete'
    assert exc.error_code == 'STATE_VALIDATION_ERROR'
    assert exc.details['current_state'] == 'archived'
    assert exc.details['attempted_state'] == 'done'
    assert isinstance(exc, ValidationException)
    assert isinstance(exc, TaskManagerException)

    print("✓ StateValidationException test passed")


if __name__ == '__main__':
    test_base_exception()
    test_validation_exception()
    test_field_validation_exception()
    test_state_validation_exception()
    print("\n✅ All exception tests passed!")
