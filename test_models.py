"""
Tests for the task management models.
"""
import pytest
from datetime import datetime, timedelta

from models import Task, TaskList, Tag, User, Priority, TaskStatus


class TestTag:
    """Tests for the Tag model."""

    def test_create_tag_with_defaults(self):
        """Test creating a tag with default color."""
        tag = Tag(name="work")
        assert tag.name == "work"
        assert tag.color == "#808080"

    def test_create_tag_with_custom_color(self):
        """Test creating a tag with a custom color."""
        tag = Tag(name="urgent", color="#FF0000")
        assert tag.name == "urgent"
        assert tag.color == "#FF0000"

    def test_tag_invalid_color_format(self):
        """Test that invalid color format raises error."""
        with pytest.raises(ValueError):
            Tag(name="test", color="red")

    def test_tag_invalid_color_length(self):
        """Test that invalid color length raises error."""
        with pytest.raises(ValueError):
            Tag(name="test", color="#FFF")

    def test_tag_is_immutable(self):
        """Test that tags are immutable (frozen)."""
        tag = Tag(name="work")
        with pytest.raises(TypeError):
            tag.name = "personal"


class TestTask:
    """Tests for the Task model."""

    def test_create_minimal_task(self):
        """Test creating a task with minimal required fields."""
        task = Task(title="My Task")
        assert task.title == "My Task"
        assert task.status == TaskStatus.TODO
        assert task.priority == Priority.MEDIUM
        assert task.tags == []
        assert task.description is None

    def test_create_full_task(self):
        """Test creating a task with all fields."""
        due = datetime.utcnow() + timedelta(days=7)
        tag = Tag(name="work")
        task = Task(
            id=1,
            title="Complete report",
            description="Finish the quarterly report",
            status=TaskStatus.IN_PROGRESS,
            priority=Priority.HIGH,
            tags=[tag],
            due_date=due
        )
        assert task.id == 1
        assert task.title == "Complete report"
        assert task.description == "Finish the quarterly report"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == Priority.HIGH
        assert len(task.tags) == 1
        assert task.due_date == due

    def test_title_whitespace_stripped(self):
        """Test that title whitespace is stripped."""
        task = Task(title="  My Task  ")
        assert task.title == "My Task"

    def test_title_cannot_be_empty(self):
        """Test that empty title raises error."""
        with pytest.raises(ValueError, match="at least 1 character"):
            Task(title="")

    def test_title_cannot_be_whitespace_only(self):
        """Test that whitespace-only title raises error."""
        with pytest.raises(ValueError, match="Title cannot be empty"):
            Task(title="   ")

    def test_title_with_exactly_200_characters(self):
        """Test that title with exactly 200 characters is accepted."""
        title_200 = "A" * 200
        task = Task(title=title_200)
        assert task.title == title_200
        assert len(task.title) == 200

    def test_title_with_201_characters_fails(self):
        """Test that title with 201 characters raises ValidationError."""
        title_201 = "A" * 201
        with pytest.raises(ValueError, match="ensure this value has at most 200 characters"):
            Task(title=title_201)

    def test_title_with_199_characters(self):
        """Test that title with 199 characters is accepted."""
        title_199 = "A" * 199
        task = Task(title=title_199)
        assert task.title == title_199
        assert len(task.title) == 199

    def test_title_boundary_with_whitespace_stripping(self):
        """Test that whitespace stripping works correctly with boundary-length titles."""
        title_196_with_spaces = "  " + ("A" * 196) + "  "
        task = Task(title=title_196_with_spaces)
        assert task.title == "A" * 196
        assert len(task.title) == 196

        title_199_with_spaces = "  " + ("A" * 199) + "  "
        with pytest.raises(ValueError, match="ensure this value has at most 200 characters"):
            Task(title=title_199_with_spaces)

    def test_description_with_exactly_2000_characters(self):
        """Test that description with exactly 2000 characters is accepted."""
        description_2000 = "D" * 2000
        task = Task(title="Test Task", description=description_2000)
        assert task.description == description_2000
        assert len(task.description) == 2000

    def test_description_with_2001_characters_fails(self):
        """Test that description with 2001 characters raises ValidationError."""
        description_2001 = "D" * 2001
        with pytest.raises(ValueError, match="ensure this value has at most 2000 characters"):
            Task(title="Test Task", description=description_2001)

    def test_description_with_1999_characters(self):
        """Test that description with 1999 characters is accepted."""
        description_1999 = "D" * 1999
        task = Task(title="Test Task", description=description_1999)
        assert task.description == description_1999
        assert len(task.description) == 1999

    def test_description_with_none(self):
        """Test that description can be None as it's an optional field."""
        task = Task(title="Test Task", description=None)
        assert task.description is None

    def test_completed_at_auto_set_when_done(self):
        """Test that completed_at is auto-set when status is DONE."""
        task = Task(title="Test", status=TaskStatus.DONE)
        assert task.completed_at is not None

    def test_completed_at_cleared_when_not_done(self):
        """Test that completed_at is cleared when status is not DONE."""
        task = Task(title="Test", status=TaskStatus.TODO)
        assert task.completed_at is None

    def test_archived_requires_completed_at(self):
        """Test that archived tasks must have completed_at."""
        with pytest.raises(ValueError, match="Archived tasks must have"):
            Task(
                title="Test",
                status=TaskStatus.ARCHIVED,
                completed_at=None
            )

    def test_mark_complete(self):
        """Test marking a task as complete."""
        task = Task(title="Test", status=TaskStatus.TODO)
        completed = task.mark_complete()
        assert completed.status == TaskStatus.DONE
        assert completed.completed_at is not None

    def test_to_dict(self):
        """Test converting task to dictionary."""
        task = Task(title="Test")
        d = task.to_dict()
        assert isinstance(d, dict)
        assert d["title"] == "Test"
        assert "status" in d
        assert "priority" in d

    def test_to_json(self):
        """Test converting task to JSON."""
        task = Task(title="Test")
        j = task.to_json()
        assert isinstance(j, str)
        assert "Test" in j


class TestTaskList:
    """Tests for the TaskList model."""

    def test_create_empty_task_list(self):
        """Test creating an empty task list."""
        tl = TaskList(name="My List", owner="john")
        assert tl.name == "My List"
        assert tl.owner == "john"
        assert tl.tasks == []

    def test_create_task_list_with_tasks(self):
        """Test creating a task list with tasks."""
        tasks = [Task(title="Task 1"), Task(title="Task 2")]
        tl = TaskList(name="My List", owner="john", tasks=tasks)
        assert len(tl.tasks) == 2

    def test_name_whitespace_stripped(self):
        """Test that name whitespace is stripped."""
        tl = TaskList(name="  My List  ", owner="john")
        assert tl.name == "My List"

    def test_name_cannot_be_empty(self):
        """Test that empty name raises error."""
        with pytest.raises(ValueError, match="at least 1 character"):
            TaskList(name="", owner="john")

    def test_add_task(self):
        """Test adding a task to the list."""
        tl = TaskList(name="My List", owner="john")
        task = Task(title="New Task")
        new_tl = tl.add_task(task)
        assert len(new_tl.tasks) == 1
        assert len(tl.tasks) == 0  # Original unchanged

    def test_get_tasks_by_status(self):
        """Test filtering tasks by status."""
        tasks = [
            Task(title="Task 1", status=TaskStatus.TODO),
            Task(title="Task 2", status=TaskStatus.DONE),
            Task(title="Task 3", status=TaskStatus.TODO),
        ]
        tl = TaskList(name="My List", owner="john", tasks=tasks)
        todo_tasks = tl.get_tasks_by_status(TaskStatus.TODO)
        assert len(todo_tasks) == 2

    def test_get_tasks_by_priority(self):
        """Test filtering tasks by priority."""
        tasks = [
            Task(title="Task 1", priority=Priority.HIGH),
            Task(title="Task 2", priority=Priority.LOW),
            Task(title="Task 3", priority=Priority.HIGH),
        ]
        tl = TaskList(name="My List", owner="john", tasks=tasks)
        high_priority = tl.get_tasks_by_priority(Priority.HIGH)
        assert len(high_priority) == 2

    def test_get_overdue_tasks(self):
        """Test getting overdue tasks."""
        past = datetime.utcnow() - timedelta(days=1)
        future = datetime.utcnow() + timedelta(days=1)
        tasks = [
            Task(title="Overdue", due_date=past, status=TaskStatus.TODO),
            Task(title="Not overdue", due_date=future, status=TaskStatus.TODO),
            Task(title="Done overdue", due_date=past, status=TaskStatus.DONE),
        ]
        tl = TaskList(name="My List", owner="john", tasks=tasks)
        overdue = tl.get_overdue_tasks()
        assert len(overdue) == 1
        assert overdue[0].title == "Overdue"


class TestUser:
    """Tests for the User model."""

    def test_create_minimal_user(self):
        """Test creating a user with minimal fields."""
        user = User(username="johndoe", email="john@example.com")
        assert user.username == "johndoe"
        assert user.email == "john@example.com"
        assert user.is_active is True
        assert user.task_lists == []

    def test_create_full_user(self):
        """Test creating a user with all fields."""
        tl = TaskList(name="Work", owner="johndoe")
        user = User(
            id=1,
            username="johndoe",
            email="john@example.com",
            full_name="John Doe",
            is_active=True,
            task_lists=[tl]
        )
        assert user.id == 1
        assert user.full_name == "John Doe"
        assert len(user.task_lists) == 1

    def test_email_normalized_to_lowercase(self):
        """Test that email is normalized to lowercase."""
        user = User(username="johndoe", email="John@EXAMPLE.com")
        assert user.email == "john@example.com"

    def test_invalid_username_format(self):
        """Test that invalid username format raises error."""
        with pytest.raises(ValueError):
            User(username="john doe", email="john@example.com")

    def test_invalid_email_format(self):
        """Test that invalid email format raises error."""
        with pytest.raises(ValueError):
            User(username="johndoe", email="not-an-email")

    def test_to_dict(self):
        """Test converting user to dictionary."""
        user = User(username="johndoe", email="john@example.com")
        d = user.to_dict()
        assert isinstance(d, dict)
        assert d["username"] == "johndoe"
        assert d["email"] == "john@example.com"


class TestModelSerialization:
    """Tests for model serialization and parsing."""

    def test_task_json_roundtrip(self):
        """Test that a task can be serialized and deserialized."""
        original = Task(
            title="Test Task",
            priority=Priority.HIGH,
            status=TaskStatus.IN_PROGRESS
        )
        json_str = original.json()
        restored = Task.parse_raw(json_str)
        assert restored.title == original.title
        assert restored.priority == original.priority
        assert restored.status == original.status

    def test_task_dict_roundtrip(self):
        """Test that a task can be converted to dict and back."""
        original = Task(title="Test Task")
        d = original.dict()
        restored = Task(**d)
        assert restored.title == original.title

    def test_nested_model_serialization(self):
        """Test serialization of nested models."""
        tag = Tag(name="work")
        task = Task(title="Test", tags=[tag])
        tl = TaskList(name="My List", owner="john", tasks=[task])
        
        d = tl.dict()
        assert d["tasks"][0]["tags"][0]["name"] == "work"
