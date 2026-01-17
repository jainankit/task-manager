# Task Manager Models

Data models for a simple task management system built with Pydantic.

## Models

- **Tag** - Immutable labels with name and hex color code
- **Task** - Tasks with title, description, status, priority, tags, and due dates
- **TaskList** - Collections of tasks with filtering and query methods
- **User** - Users with username, email, and associated task lists

## Features

- Field validation (email format, username patterns, color codes)
- Auto-timestamping for task creation and completion
- Status-aware validation (archived tasks require completion date)
- Immutable tags to prevent accidental modifications
- Filtering by status, priority, and overdue tasks

## Usage

```python
from models import Task, TaskList, Tag, User, Priority, TaskStatus

# Create a task with tags
tag = Tag(name="urgent", color="#FF0000")
task = Task(
    title="Review PR",
    priority=Priority.HIGH,
    tags=[tag]
)

# Create a task list and add tasks
task_list = TaskList(name="Sprint 1", owner="alice")
task_list = task_list.add_task(task)

# Filter tasks
high_priority = task_list.get_tasks_by_priority(Priority.HIGH)
overdue = task_list.get_overdue_tasks()

# Mark complete
completed_task = task.mark_complete()
```

## Running Tests

```bash
pip install -r requirements.txt
pytest test_models.py -v
```

## License

MIT
