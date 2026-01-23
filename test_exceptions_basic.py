"""
Basic verification tests for the exception classes.
"""
from exceptions import (
    TaskManagerException,
    ValidationException,
    FieldValidationException,
    StateValidationException,
    DuplicateTaskException,
    TaskNotFoundException,
    InvalidStateTransitionException,
    DateValidationException,
    OwnershipException
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


def test_duplicate_task_exception():
    """Test DuplicateTaskException with task ID."""
    exc = DuplicateTaskException(task_id='task-123')

    assert exc.message == "Task with ID 'task-123' already exists"
    assert exc.error_code == 'DUPLICATE_TASK'
    assert exc.details['task_id'] == 'task-123'
    assert isinstance(exc, TaskManagerException)

    # Test with custom message
    exc_custom = DuplicateTaskException(
        task_id='task-456',
        message='Custom duplicate message'
    )
    assert exc_custom.message == 'Custom duplicate message'
    assert exc_custom.details['task_id'] == 'task-456'

    print("✓ DuplicateTaskException test passed")


def test_task_not_found_exception():
    """Test TaskNotFoundException with task ID."""
    exc = TaskNotFoundException(task_id='task-789')

    assert exc.message == "Task with ID 'task-789' not found"
    assert exc.error_code == 'TASK_NOT_FOUND'
    assert exc.details['task_id'] == 'task-789'
    assert isinstance(exc, TaskManagerException)

    print("✓ TaskNotFoundException test passed")


def test_invalid_state_transition_exception():
    """Test InvalidStateTransitionException with status information."""
    exc = InvalidStateTransitionException(
        message='Cannot complete an archived task',
        current_status='archived',
        attempted_status='completed'
    )

    assert exc.message == 'Cannot complete an archived task'
    assert exc.error_code == 'INVALID_STATE_TRANSITION'
    assert exc.details['current_status'] == 'archived'
    assert exc.details['attempted_status'] == 'completed'
    assert isinstance(exc, TaskManagerException)

    print("✓ InvalidStateTransitionException test passed")


def test_date_validation_exception():
    """Test DateValidationException with date information."""
    exc = DateValidationException(
        message='Due date must be in the future',
        field_name='due_date',
        invalid_date='2020-01-01'
    )

    assert exc.message == 'Due date must be in the future'
    assert exc.error_code == 'DATE_VALIDATION_ERROR'
    assert exc.field_name == 'due_date'
    assert exc.details['invalid_date'] == '2020-01-01'
    assert isinstance(exc, ValidationException)
    assert isinstance(exc, TaskManagerException)

    print("✓ DateValidationException test passed")


def test_ownership_exception():
    """Test OwnershipException with resource information."""
    exc = OwnershipException(
        message='User does not have permission to modify this task',
        resource_type='task',
        resource_id='task-101',
        user_id='user-001'
    )

    assert exc.message == 'User does not have permission to modify this task'
    assert exc.error_code == 'OWNERSHIP_ERROR'
    assert exc.details['resource_type'] == 'task'
    assert exc.details['resource_id'] == 'task-101'
    assert exc.details['user_id'] == 'user-001'
    assert isinstance(exc, TaskManagerException)

    print("✓ OwnershipException test passed")


if __name__ == '__main__':
    test_base_exception()
    test_validation_exception()
    test_field_validation_exception()
    test_state_validation_exception()
    test_duplicate_task_exception()
    test_task_not_found_exception()
    test_invalid_state_transition_exception()
    test_date_validation_exception()
    test_ownership_exception()
    print("\n✅ All exception tests passed!")
