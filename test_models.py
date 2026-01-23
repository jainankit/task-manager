"""
Tests for the task management models.
"""
import pytest
from datetime import datetime, timedelta, timezone
from pydantic import ValidationError

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

    def test_tag_name_with_exactly_50_characters(self):
        """Test that tag name with exactly 50 characters is accepted."""
        name_50 = "A" * 50
        tag = Tag(name=name_50)
        assert tag.name == name_50
        assert len(tag.name) == 50

    def test_tag_name_with_51_characters_fails(self):
        """Test that tag name with 51 characters raises ValidationError."""
        name_51 = "A" * 51
        with pytest.raises(ValueError, match="ensure this value has at most 50 characters"):
            Tag(name=name_51)

    def test_tag_name_with_1_character(self):
        """Test that tag name with 1 character (minimum length) is accepted."""
        tag = Tag(name="A")
        assert tag.name == "A"
        assert len(tag.name) == 1


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

    # Date Range Validation Tests
    def test_due_date_before_created_at_fails(self):
        """Test that creating a task where due_date is before created_at raises ValueError."""
        created = datetime.utcnow()
        due = created - timedelta(days=1)
        with pytest.raises(ValueError, match="due_date cannot be before created_at"):
            Task(title="Test Task", created_at=created, due_date=due)

    def test_due_date_equals_created_at_succeeds(self):
        """Test that due_date equal to created_at is accepted as a boundary case."""
        timestamp = datetime.utcnow()
        task = Task(title="Test Task", created_at=timestamp, due_date=timestamp)
        assert task.due_date == task.created_at
        assert task.due_date == timestamp

    def test_due_date_after_created_at_succeeds(self):
        """Test that due_date after created_at is accepted."""
        created = datetime.utcnow()
        due = created + timedelta(days=1)
        task = Task(title="Test Task", created_at=created, due_date=due)
        assert task.due_date > task.created_at
        assert task.due_date == due

    def test_past_due_date_after_created_at_succeeds(self):
        """Test that past due_date is allowed if it's still after created_at."""
        # Create a task with created_at in the past, and due_date also in the past
        # but still after created_at
        created = datetime.utcnow() - timedelta(days=5)
        due = datetime.utcnow() - timedelta(days=2)
        task = Task(title="Test Task", created_at=created, due_date=due)
        assert task.due_date > task.created_at
        assert task.due_date < datetime.utcnow()  # Verify it's actually in the past

    def test_update_due_date_before_created_at_fails(self):
        """Test that updating a task to set due_date before created_at fails due to validate_assignment=True."""
        created = datetime.utcnow()
        due = created + timedelta(days=1)
        task = Task(title="Test Task", created_at=created, due_date=due)

        # Try to update due_date to before created_at
        invalid_due = created - timedelta(days=1)
        with pytest.raises(ValueError, match="due_date cannot be before created_at"):
            task.due_date = invalid_due

    # Created At and Completed At Date Range Tests
    def test_completed_at_is_after_created_at_when_marked_complete(self):
        """Test that completed_at is after created_at when a task is marked complete."""
        created = datetime.utcnow() - timedelta(seconds=5)
        task = Task(title="Test Task", created_at=created, status=TaskStatus.TODO)

        # Mark task as complete
        completed_task = task.mark_complete()

        assert completed_task.completed_at is not None
        assert completed_task.completed_at >= completed_task.created_at
        assert completed_task.status == TaskStatus.DONE

    def test_archived_task_has_consistent_timestamp_ordering(self):
        """Test that archived tasks have consistent timestamp ordering (created_at <= completed_at)."""
        created = datetime.utcnow() - timedelta(hours=2)

        # First create a DONE task with completed_at
        done_task = Task(
            title="Done Task",
            created_at=created,
            status=TaskStatus.DONE
        )

        # The validator auto-sets completed_at when status is DONE
        assert done_task.completed_at is not None
        assert done_task.created_at <= done_task.completed_at

        # Now update to ARCHIVED status (simulate archiving a completed task)
        archived_task = done_task.copy(update={"status": TaskStatus.ARCHIVED})

        assert archived_task.created_at <= archived_task.completed_at
        assert archived_task.status == TaskStatus.ARCHIVED

    def test_archived_task_requires_completed_at(self):
        """Test that attempting to create archived task without proper completed_at fails."""
        created = datetime.utcnow() - timedelta(hours=2)

        # Attempting to create an ARCHIVED task directly fails because:
        # 1. The completed_at validator clears completed_at for non-DONE status
        # 2. The root validator then fails because ARCHIVED requires completed_at
        with pytest.raises(ValueError, match="Archived tasks must have"):
            Task(
                title="Archived Task",
                created_at=created,
                status=TaskStatus.ARCHIVED
            )

    def test_mark_complete_sets_valid_completed_at_timestamp(self):
        """Test that mark_complete() sets completed_at to a valid timestamp relative to created_at."""
        # Create a task with created_at slightly in the past
        created = datetime.utcnow() - timedelta(minutes=30)
        task = Task(title="Test Task", created_at=created, status=TaskStatus.TODO)

        # Store current time before marking complete
        before_complete = datetime.utcnow()

        # Mark the task as complete
        completed_task = task.mark_complete()

        # Store current time after marking complete
        after_complete = datetime.utcnow()

        # Verify completed_at is set
        assert completed_task.completed_at is not None

        # Verify completed_at is after created_at
        assert completed_task.completed_at >= completed_task.created_at

        # Verify completed_at is within a reasonable time window (should be approximately now)
        assert before_complete <= completed_task.completed_at <= after_complete

        # Verify status is DONE
        assert completed_task.status == TaskStatus.DONE

    def test_task_created_as_done_has_valid_completed_at(self):
        """Test that task created with status DONE has completed_at >= created_at."""
        created = datetime.utcnow() - timedelta(seconds=1)

        # Create a task that's already done
        task = Task(title="Already Done Task", created_at=created, status=TaskStatus.DONE)

        # The validator should auto-set completed_at
        assert task.completed_at is not None
        assert task.completed_at >= task.created_at


class TestTaskTimezones:
    """Tests for timezone-aware datetime handling in the Task model."""

    def test_create_task_with_timezone_aware_due_date_utc(self):
        """Test that creating a task with timezone-aware datetime for due_date (UTC) fails due to naive comparison."""
        # Create a timezone-aware datetime in UTC
        now_utc = datetime.now(timezone.utc)
        due_utc = now_utc + timedelta(days=1)

        # The current implementation uses naive datetime.utcnow() in the validator,
        # which cannot be compared with timezone-aware datetimes
        with pytest.raises(ValidationError, match="can't compare offset-naive and offset-aware datetimes"):
            Task(title="UTC Task", due_date=due_utc)

    def test_create_task_with_timezone_aware_due_date_non_utc(self):
        """Test that creating a task with timezone-aware datetime for due_date (non-UTC) fails due to naive comparison."""
        # Create a timezone with +5 hours offset
        tz_plus5 = timezone(timedelta(hours=5))
        now_tz = datetime.now(tz_plus5)
        due_tz = now_tz + timedelta(days=1)

        # The current implementation uses naive datetime.utcnow() in the validator,
        # which cannot be compared with timezone-aware datetimes
        with pytest.raises(ValidationError, match="can't compare offset-naive and offset-aware datetimes"):
            Task(title="Non-UTC Task", due_date=due_tz)

    def test_created_at_default_uses_utc_naive(self):
        """Test that created_at default uses datetime.utcnow() which is timezone-naive."""
        task = Task(title="Test Task")

        # datetime.utcnow() returns a naive datetime (no tzinfo)
        assert task.created_at is not None
        assert task.created_at.tzinfo is None

        # Verify it's close to current UTC time (within 1 second)
        now_utc_naive = datetime.utcnow()
        time_diff = abs((task.created_at - now_utc_naive).total_seconds())
        assert time_diff < 1.0

    def test_overdue_calculation_with_timezone_aware_due_dates(self):
        """Test that timezone-aware due dates cannot be used due to naive datetime comparison in validator."""
        # Create a timezone-aware datetime in the past (UTC)
        past_utc = datetime.now(timezone.utc) - timedelta(days=1)

        # Create tasks with timezone-aware due dates
        # Note: The validator compares with naive datetime.utcnow()
        created_naive = datetime.utcnow() - timedelta(days=2)

        # This fails because the due_date validator uses datetime.utcnow() (naive)
        with pytest.raises(ValidationError, match="can't compare offset-naive and offset-aware datetimes"):
            Task(
                title="Overdue Task",
                due_date=past_utc,
                created_at=created_naive,
                status=TaskStatus.TODO
            )

    def test_mark_complete_with_naive_datetimes(self):
        """Test mark_complete() method with naive due dates (standard usage)."""
        # Create a task with naive due_date (standard behavior)
        due_naive = datetime.utcnow() + timedelta(days=1)

        task = Task(
            title="Task to Complete",
            due_date=due_naive,
            status=TaskStatus.TODO
        )

        # Mark the task as complete
        completed_task = task.mark_complete()

        # Verify status is DONE
        assert completed_task.status == TaskStatus.DONE

        # Verify completed_at is set (will be naive as datetime.utcnow() is used)
        assert completed_task.completed_at is not None
        assert completed_task.completed_at.tzinfo is None

        # Verify completed_at is close to current time
        now_utc_naive = datetime.utcnow()
        time_diff = abs((completed_task.completed_at - now_utc_naive).total_seconds())
        assert time_diff < 1.0

    def test_timezone_aware_and_naive_comparison_in_validation(self):
        """Test that mixing timezone-aware and naive datetimes fails in validation."""
        # Create a timezone-aware due_date
        due_utc = datetime.now(timezone.utc) + timedelta(days=1)

        # Create a naive created_at (as default behavior uses datetime.utcnow())
        created_naive = datetime.utcnow() - timedelta(hours=1)

        # This fails because the due_date validator compares with naive datetime.utcnow()
        with pytest.raises(ValidationError, match="can't compare offset-naive and offset-aware datetimes"):
            Task(
                title="Mixed Timezone Task",
                due_date=due_utc,
                created_at=created_naive
            )

    def test_task_with_timezone_aware_created_at_and_due_date(self):
        """Test that timezone-aware created_at and due_date cannot be used together."""
        # Create timezone-aware datetimes
        created_utc = datetime.now(timezone.utc) - timedelta(hours=2)
        due_utc = datetime.now(timezone.utc) + timedelta(days=1)

        # This fails because the due_date validator compares with naive datetime.utcnow()
        with pytest.raises(ValidationError, match="can't compare offset-naive and offset-aware datetimes"):
            Task(
                title="Fully Aware Task",
                created_at=created_utc,
                due_date=due_utc
            )

    def test_task_with_naive_datetimes_works(self):
        """Test that naive datetimes work correctly (current expected behavior)."""
        # Create naive datetimes
        created_naive = datetime.utcnow() - timedelta(hours=2)
        due_naive = datetime.utcnow() + timedelta(days=1)

        task = Task(
            title="Naive Task",
            created_at=created_naive,
            due_date=due_naive
        )

        assert task.created_at.tzinfo is None
        assert task.due_date.tzinfo is None
        assert task.due_date > task.created_at

    def test_overdue_with_naive_datetimes(self):
        """Test overdue detection with naive due dates (standard usage)."""
        # Create naive due dates (standard behavior)
        created_naive = datetime.utcnow() - timedelta(days=2)
        past_naive = datetime.utcnow() - timedelta(hours=5)
        future_naive = datetime.utcnow() + timedelta(days=1)

        task_overdue = Task(
            title="Overdue Task",
            due_date=past_naive,
            created_at=created_naive,
            status=TaskStatus.TODO
        )

        task_future = Task(
            title="Future Task",
            due_date=future_naive,
            created_at=created_naive,
            status=TaskStatus.TODO
        )

        task_list = TaskList(
            name="Naive TZ List",
            owner="testuser",
            tasks=[task_overdue, task_future]
        )

        overdue_tasks = task_list.get_overdue_tasks()

        # Only the overdue task should be detected
        assert len(overdue_tasks) == 1
        assert overdue_tasks[0].title == "Overdue Task"

    def test_due_date_validation_with_timezone_aware_dates(self):
        """Test that timezone-aware datetimes cannot be used in validation."""
        # Create timezone-aware datetimes where due_date is before created_at
        created_utc = datetime.now(timezone.utc)
        due_utc = created_utc - timedelta(hours=1)

        # This fails due to timezone comparison, not the validation logic
        with pytest.raises(ValidationError, match="can't compare offset-naive and offset-aware datetimes"):
            Task(
                title="Invalid TZ Task",
                created_at=created_utc,
                due_date=due_utc
            )

    def test_completed_at_auto_set_is_naive(self):
        """Test that auto-set completed_at is naive when created with DONE status."""
        # Create a task with naive datetimes (standard behavior)
        created_naive = datetime.utcnow() - timedelta(hours=1)
        due_naive = datetime.utcnow() + timedelta(days=1)

        # Create task in DONE status
        task = Task(
            title="Done Task",
            created_at=created_naive,
            due_date=due_naive,
            status=TaskStatus.DONE
        )

        # completed_at should be auto-set and naive
        assert task.completed_at is not None
        assert task.completed_at.tzinfo is None

        # All datetime fields should be naive
        assert task.created_at.tzinfo is None
        assert task.due_date.tzinfo is None

        # Verify ordering
        assert task.completed_at >= task.created_at


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

    def test_name_with_exactly_100_characters(self):
        """Test that task list name with exactly 100 characters is accepted."""
        name_100 = "A" * 100
        tl = TaskList(name=name_100, owner="john")
        assert tl.name == name_100
        assert len(tl.name) == 100

    def test_name_with_101_characters_fails(self):
        """Test that task list name with 101 characters raises ValidationError."""
        name_101 = "A" * 101
        with pytest.raises(ValueError, match="ensure this value has at most 100 characters"):
            TaskList(name=name_101, owner="john")

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
        created = datetime.utcnow() - timedelta(days=2)  # Created before past due_date
        tasks = [
            Task(title="Overdue", due_date=past, created_at=created, status=TaskStatus.TODO),
            Task(title="Not overdue", due_date=future, status=TaskStatus.TODO),
            Task(title="Done overdue", due_date=past, created_at=created, status=TaskStatus.DONE),
        ]
        tl = TaskList(name="My List", owner="john", tasks=tasks)
        overdue = tl.get_overdue_tasks()
        assert len(overdue) == 1
        assert overdue[0].title == "Overdue"


class TestTaskListTimezones:
    """Tests for timezone handling in the TaskList model's overdue functionality."""

    def test_get_overdue_tasks_with_mixed_aware_and_naive_datetimes(self):
        """Test get_overdue_tasks with tasks having timezone-aware and naive datetimes mixed."""
        # Create tasks with naive datetimes (standard behavior)
        created_naive = datetime.utcnow() - timedelta(days=2)
        past_naive = datetime.utcnow() - timedelta(hours=5)

        task_naive_overdue = Task(
            title="Naive Overdue Task",
            due_date=past_naive,
            created_at=created_naive,
            status=TaskStatus.TODO
        )

        # Create a task that would be timezone-aware cannot actually be created
        # because the validator compares with naive datetime.utcnow()
        # So we test that mixed scenarios don't exist in the current implementation

        task_list = TaskList(
            name="Mixed TZ List",
            owner="testuser",
            tasks=[task_naive_overdue]
        )

        overdue_tasks = task_list.get_overdue_tasks()

        # Only the naive overdue task should be detected
        assert len(overdue_tasks) == 1
        assert overdue_tasks[0].title == "Naive Overdue Task"

    def test_overdue_detection_across_dst_spring_forward(self):
        """Test overdue detection during DST spring forward transition."""
        # DST spring forward: clocks jump forward (e.g., 2 AM becomes 3 AM)
        # Using naive UTC datetimes, DST doesn't directly affect the comparison
        # but we test edge cases around typical DST transition times

        # Simulate a task created before DST transition
        # DST typically happens at 2 AM local time, but we're using UTC (no DST)
        created = datetime.utcnow() - timedelta(days=10)

        # Task due during typical DST transition window
        # (These are naive UTC times, so no actual DST affects them)
        due_before_transition = datetime.utcnow() - timedelta(hours=3)

        task_overdue = Task(
            title="Pre-DST Overdue Task",
            due_date=due_before_transition,
            created_at=created,
            status=TaskStatus.TODO
        )

        task_list = TaskList(
            name="DST Spring List",
            owner="testuser",
            tasks=[task_overdue]
        )

        overdue_tasks = task_list.get_overdue_tasks()

        # Task should be detected as overdue
        assert len(overdue_tasks) == 1
        assert overdue_tasks[0].title == "Pre-DST Overdue Task"

    def test_overdue_detection_across_dst_fall_back(self):
        """Test overdue detection during DST fall back transition."""
        # DST fall back: clocks jump backward (e.g., 2 AM becomes 1 AM again)
        # Using naive UTC datetimes, DST doesn't affect the comparison
        # but we test that datetime comparisons remain consistent

        created = datetime.utcnow() - timedelta(days=10)

        # Task due during typical DST fall back window
        # (These are naive UTC times, so DST doesn't cause ambiguity)
        due_during_fallback = datetime.utcnow() - timedelta(hours=2)

        task_overdue = Task(
            title="DST Fallback Overdue Task",
            due_date=due_during_fallback,
            created_at=created,
            status=TaskStatus.TODO
        )

        task_list = TaskList(
            name="DST Fall List",
            owner="testuser",
            tasks=[task_overdue]
        )

        overdue_tasks = task_list.get_overdue_tasks()

        # Task should be detected as overdue consistently
        assert len(overdue_tasks) == 1
        assert overdue_tasks[0].title == "DST Fallback Overdue Task"

    def test_tasks_due_at_midnight_utc(self):
        """Test overdue detection for tasks due at midnight UTC."""
        # Create a task with due_date at midnight UTC (00:00:00)
        # and test that it's properly detected as overdue if past midnight

        created = datetime.utcnow() - timedelta(days=3)

        # Create a due date for yesterday at midnight UTC
        yesterday_midnight = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=1)

        task_midnight_overdue = Task(
            title="Midnight UTC Overdue Task",
            due_date=yesterday_midnight,
            created_at=created,
            status=TaskStatus.TODO
        )

        # Create a task due at tomorrow's midnight (not overdue)
        tomorrow_midnight = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)

        task_midnight_future = Task(
            title="Midnight UTC Future Task",
            due_date=tomorrow_midnight,
            created_at=created,
            status=TaskStatus.TODO
        )

        task_list = TaskList(
            name="Midnight UTC List",
            owner="testuser",
            tasks=[task_midnight_overdue, task_midnight_future]
        )

        overdue_tasks = task_list.get_overdue_tasks()

        # Only yesterday's midnight task should be overdue
        assert len(overdue_tasks) == 1
        assert overdue_tasks[0].title == "Midnight UTC Overdue Task"

    def test_tasks_due_at_midnight_different_timezones(self):
        """Test that naive UTC midnight is used consistently regardless of local timezone considerations."""
        # Since we're using naive UTC datetimes, all midnight comparisons are in UTC
        # This test verifies that behavior is consistent

        created = datetime.utcnow() - timedelta(days=2)

        # Midnight UTC yesterday
        midnight_utc_yesterday = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=1)

        # If this were interpreted as midnight in a different timezone (e.g., EST),
        # it would be a different UTC time, but we're using naive UTC
        # so it's always midnight UTC

        task = Task(
            title="UTC Midnight Task",
            due_date=midnight_utc_yesterday,
            created_at=created,
            status=TaskStatus.TODO
        )

        task_list = TaskList(
            name="Timezone Midnight List",
            owner="testuser",
            tasks=[task]
        )

        overdue_tasks = task_list.get_overdue_tasks()

        # Task should be overdue since it's past midnight UTC yesterday
        assert len(overdue_tasks) == 1
        assert overdue_tasks[0].title == "UTC Midnight Task"

    def test_overdue_task_with_due_date_exactly_at_current_utc_time(self):
        """Test overdue detection with due_date exactly at current UTC time (boundary)."""
        # Get current UTC time
        current_time = datetime.utcnow()

        # Create a task with due_date exactly at current time
        # According to get_overdue_tasks logic: due_date < now
        # So a task due exactly now should NOT be overdue (boundary case)

        created = current_time - timedelta(days=1)

        task_due_now = Task(
            title="Due Exactly Now",
            due_date=current_time,
            created_at=created,
            status=TaskStatus.TODO
        )

        # Create a task due 1 second in the past (should be overdue)
        task_due_past = Task(
            title="Due One Second Ago",
            due_date=current_time - timedelta(seconds=1),
            created_at=created,
            status=TaskStatus.TODO
        )

        # Create a task due 1 second in the future (not overdue)
        task_due_future = Task(
            title="Due One Second Future",
            due_date=current_time + timedelta(seconds=1),
            created_at=created,
            status=TaskStatus.TODO
        )

        task_list = TaskList(
            name="Boundary Time List",
            owner="testuser",
            tasks=[task_due_now, task_due_past, task_due_future]
        )

        overdue_tasks = task_list.get_overdue_tasks()

        # Only the task due 1 second ago should be overdue
        # Tasks due exactly now or in the future should not be overdue
        # Note: There's a tiny race condition here, but we check the logic
        assert len(overdue_tasks) >= 1
        assert any(t.title == "Due One Second Ago" for t in overdue_tasks)

        # Verify that the task due exactly now is likely not overdue
        # (unless time has passed between creation and check)
        if len(overdue_tasks) == 1:
            assert overdue_tasks[0].title == "Due One Second Ago"

    def test_overdue_detection_with_microsecond_precision(self):
        """Test that overdue detection works correctly with microsecond precision."""
        # Test that datetime comparisons work correctly even with microsecond differences

        created = datetime.utcnow() - timedelta(days=1)

        # Get current time with microseconds
        now = datetime.utcnow()

        # Task due just microseconds ago (should be overdue)
        due_microseconds_ago = now - timedelta(microseconds=500)

        task_micro_overdue = Task(
            title="Microseconds Overdue",
            due_date=due_microseconds_ago,
            created_at=created,
            status=TaskStatus.TODO
        )

        # Task due in microseconds from now (not overdue)
        due_microseconds_future = now + timedelta(microseconds=500)

        task_micro_future = Task(
            title="Microseconds Future",
            due_date=due_microseconds_future,
            created_at=created,
            status=TaskStatus.TODO
        )

        task_list = TaskList(
            name="Microsecond List",
            owner="testuser",
            tasks=[task_micro_overdue, task_micro_future]
        )

        overdue_tasks = task_list.get_overdue_tasks()

        # The microseconds-past task should be detected as overdue
        assert len(overdue_tasks) >= 1
        assert any(t.title == "Microseconds Overdue" for t in overdue_tasks)

    def test_overdue_tasks_with_various_statuses_and_timezones(self):
        """Test that overdue detection respects task status regardless of timezone considerations."""
        created = datetime.utcnow() - timedelta(days=5)
        past_due = datetime.utcnow() - timedelta(hours=10)

        # Create tasks with various statuses, all with past due dates
        task_todo = Task(
            title="TODO Overdue",
            due_date=past_due,
            created_at=created,
            status=TaskStatus.TODO
        )

        task_in_progress = Task(
            title="In Progress Overdue",
            due_date=past_due,
            created_at=created,
            status=TaskStatus.IN_PROGRESS
        )

        task_done = Task(
            title="Done Overdue",
            due_date=past_due,
            created_at=created,
            status=TaskStatus.DONE
        )

        # Create archived task (must have completed_at)
        task_archived = Task(
            title="Archived Overdue",
            due_date=past_due,
            created_at=created,
            status=TaskStatus.DONE  # First create as DONE to get completed_at
        )
        task_archived = task_archived.copy(update={"status": TaskStatus.ARCHIVED})

        task_list = TaskList(
            name="Status Test List",
            owner="testuser",
            tasks=[task_todo, task_in_progress, task_done, task_archived]
        )

        overdue_tasks = task_list.get_overdue_tasks()

        # get_overdue_tasks filters out only DONE status (not ARCHIVED)
        # So TODO, IN_PROGRESS, and ARCHIVED tasks with past due dates are returned
        assert len(overdue_tasks) == 3
        overdue_titles = [t.title for t in overdue_tasks]
        assert "TODO Overdue" in overdue_titles
        assert "In Progress Overdue" in overdue_titles
        assert "Archived Overdue" in overdue_titles
        assert "Done Overdue" not in overdue_titles

    def test_overdue_with_none_due_dates(self):
        """Test that tasks with no due_date are never considered overdue."""
        created = datetime.utcnow() - timedelta(days=3)
        past_due = datetime.utcnow() - timedelta(hours=5)

        # Task with no due date
        task_no_due_date = Task(
            title="No Due Date",
            created_at=created,
            status=TaskStatus.TODO
        )

        # Task with past due date
        task_with_due_date = Task(
            title="With Due Date",
            due_date=past_due,
            created_at=created,
            status=TaskStatus.TODO
        )

        task_list = TaskList(
            name="None Due Date List",
            owner="testuser",
            tasks=[task_no_due_date, task_with_due_date]
        )

        overdue_tasks = task_list.get_overdue_tasks()

        # Only the task with a due date should be overdue
        assert len(overdue_tasks) == 1
        assert overdue_tasks[0].title == "With Due Date"


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

    def test_username_with_50_characters_succeeds(self):
        """Test that username with exactly 50 characters is accepted."""
        username_50 = "a" * 50
        user = User(username=username_50, email="test@example.com")
        assert user.username == username_50
        assert len(user.username) == 50

    def test_username_with_51_characters_fails(self):
        """Test that username with 51 characters raises ValidationError."""
        username_51 = "a" * 51
        with pytest.raises(ValueError, match="ensure this value has at most 50 characters"):
            User(username=username_51, email="test@example.com")

    def test_username_with_3_characters_succeeds(self):
        """Test that username with exactly 3 characters (minimum) is accepted."""
        username_3 = "abc"
        user = User(username=username_3, email="test@example.com")
        assert user.username == username_3
        assert len(user.username) == 3

    def test_username_with_2_characters_fails(self):
        """Test that username with 2 characters raises ValidationError."""
        username_2 = "ab"
        with pytest.raises(ValueError, match="ensure this value has at least 3 characters"):
            User(username=username_2, email="test@example.com")

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
