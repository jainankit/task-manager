"""Test script for validation_utils.py"""
from validation_utils import (
    validate_not_empty_string,
    validate_hex_color,
    validate_future_date,
    validate_email_format,
    validate_username_format
)
from datetime import datetime, timedelta
from exceptions import FieldValidationException, DateValidationException

print('Testing validation utilities...')
print()

# Test validate_not_empty_string
print('1. Testing validate_not_empty_string:')
try:
    result = validate_not_empty_string('  Hello  ', 'test_field')
    print(f'   ✓ Valid string: "{result}"')
except Exception as e:
    print(f'   ✗ Unexpected error: {e}')

try:
    validate_not_empty_string('   ', 'test_field')
    print('   ✗ Should have raised exception for whitespace')
except FieldValidationException as e:
    print(f'   ✓ Correctly rejected whitespace: {e.error_code}')

# Test validate_hex_color
print()
print('2. Testing validate_hex_color:')
try:
    result = validate_hex_color('#ff0000')
    print(f'   ✓ Valid color: {result}')
except Exception as e:
    print(f'   ✗ Unexpected error: {e}')

try:
    validate_hex_color('ff0000')
    print('   ✗ Should have raised exception for missing #')
except FieldValidationException as e:
    print(f'   ✓ Correctly rejected color without #: {e.error_code}')

# Test validate_future_date
print()
print('3. Testing validate_future_date:')
try:
    future = datetime.now() + timedelta(days=7)
    result = validate_future_date(future, field_name='due_date')
    print(f'   ✓ Valid future date accepted')
except Exception as e:
    print(f'   ✗ Unexpected error: {e}')

try:
    past = datetime.now() - timedelta(days=7)
    validate_future_date(past, field_name='due_date')
    print('   ✗ Should have raised exception for past date')
except DateValidationException as e:
    print(f'   ✓ Correctly rejected past date: {e.error_code}')

# Test validate_email_format
print()
print('4. Testing validate_email_format:')
try:
    result = validate_email_format('User@Example.COM')
    print(f'   ✓ Valid email: {result}')
except Exception as e:
    print(f'   ✗ Unexpected error: {e}')

try:
    validate_email_format('invalid-email')
    print('   ✗ Should have raised exception for missing @')
except FieldValidationException as e:
    print(f'   ✓ Correctly rejected email without @: {e.error_code}')

# Test validate_username_format
print()
print('5. Testing validate_username_format:')
try:
    result = validate_username_format('john_doe')
    print(f'   ✓ Valid username: {result}')
except Exception as e:
    print(f'   ✗ Unexpected error: {e}')

try:
    validate_username_format('ab')
    print('   ✗ Should have raised exception for short username')
except FieldValidationException as e:
    print(f'   ✓ Correctly rejected short username: {e.error_code}')

print()
print('All validation utility tests passed!')
