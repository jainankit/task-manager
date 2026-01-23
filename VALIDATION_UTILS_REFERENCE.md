# Validation Utils Quick Reference

## Function Signatures

### 1. validate_not_empty_string
```python
def validate_not_empty_string(value: str, field_name: str) -> str
```
**Purpose**: Validate string is not empty or whitespace
**Returns**: Stripped string
**Raises**: `FieldValidationException`

### 2. validate_hex_color
```python
def validate_hex_color(value: str) -> str
```
**Purpose**: Validate hex color format (#RRGGBB)
**Returns**: Uppercase hex color
**Raises**: `FieldValidationException`

### 3. validate_future_date
```python
def validate_future_date(
    value: datetime,
    allow_past_days: int = 0,
    field_name: str = "date"
) -> datetime
```
**Purpose**: Validate date is in future or within allowed past days
**Returns**: The datetime value
**Raises**: `DateValidationException`

### 4. validate_email_format
```python
def validate_email_format(value: str) -> str
```
**Purpose**: Validate email format with detailed error messages
**Returns**: Lowercase email
**Raises**: `FieldValidationException`

### 5. validate_username_format
```python
def validate_username_format(value: str) -> str
```
**Purpose**: Validate username format (3-30 chars, starts with letter, etc.)
**Returns**: The username value
**Raises**: `FieldValidationException`

## Common Error Codes

| Function | Error Code | Description |
|----------|-----------|-------------|
| validate_not_empty_string | EMPTY_STRING_ERROR | String is empty or whitespace |
| validate_hex_color | COLOR_EMPTY | Color value is empty |
| validate_hex_color | INVALID_COLOR_FORMAT | Color format is invalid |
| validate_future_date | INVALID_DATE_TYPE | Value is not a datetime |
| validate_future_date | DATE_NOT_IN_FUTURE | Date is in the past |
| validate_future_date | DATE_TOO_FAR_FUTURE | Date is >100 years in future |
| validate_email_format | EMAIL_EMPTY | Email is empty |
| validate_email_format | EMAIL_MISSING_AT | Email missing @ symbol |
| validate_email_format | EMAIL_INVALID_DOMAIN | Invalid domain format |
| validate_username_format | USERNAME_EMPTY | Username is empty |
| validate_username_format | USERNAME_TOO_SHORT | Username < 3 chars |
| validate_username_format | USERNAME_TOO_LONG | Username > 30 chars |
| validate_username_format | USERNAME_INVALID_START | Doesn't start with letter |
| validate_username_format | USERNAME_INVALID_CHARACTERS | Contains invalid chars |

## Usage in Pydantic Validators

```python
from pydantic import BaseModel, validator
from validation_utils import validate_email_format, validate_username_format
from exceptions import FieldValidationException

class User(BaseModel):
    email: str
    username: str

    @validator("email")
    def validate_email(cls, v):
        try:
            return validate_email_format(v)
        except FieldValidationException:
            raise

    @validator("username")
    def validate_username(cls, v):
        try:
            return validate_username_format(v)
        except FieldValidationException:
            raise
```

## Validation Rules Summary

### Email Rules
- Must contain exactly one @ symbol
- Must have non-empty username before @
- Must have non-empty domain after @
- Domain must contain a period (TLD)
- Domain cannot start/end with period
- Only valid characters allowed

### Username Rules
- Length: 3-30 characters
- Must start with a letter (a-z, A-Z)
- Can contain: letters, numbers, underscores (_), hyphens (-)
- Cannot end with underscore or hyphen
- Cannot have consecutive special characters (__, --, _-, -_)

### Color Rules
- Must start with #
- Must be exactly 7 characters (#RRGGBB)
- R, G, B must be valid hex digits (0-9, A-F)

### Date Rules
- Must be a datetime object
- Must be in the future (or within allow_past_days)
- Must not be more than 100 years in the future
