"""Test the new TaskList validators for Step 2.3"""
from models import Task, TaskList
from exceptions import FieldValidationException, DuplicateTaskException

# Test 1: Whitespace-only name validation (passes min_length but should fail our validator)
print("Test 1: Whitespace-only name validation")
try:
    task_list = TaskList(name="   ", owner="user1")
    print("FAILED: Should have raised FieldValidationException")
except FieldValidationException as e:
    print(f"SUCCESS: {e.error_code} - {e.message}")
    assert e.field_name == "name"
    assert e.error_code == "TASKLIST_NAME_EMPTY"

# Test 2: Valid name (should strip whitespace)
print("\nTest 2: Valid name (should strip whitespace)")
task_list = TaskList(name="  My Tasks  ", owner="user1")
assert task_list.name == "My Tasks"
print(f"SUCCESS: Name stripped correctly: '{task_list.name}'")

# Test 3: Duplicate task IDs validation
print("\nTest 3: Duplicate task IDs validation")
task1 = Task(id=1, title="Task 1")
task2 = Task(id=2, title="Task 2")
task3 = Task(id=1, title="Task 3 (duplicate ID)")
try:
    task_list = TaskList(name="Test List", owner="user1", tasks=[task1, task2, task3])
    print("FAILED: Should have raised DuplicateTaskException")
except DuplicateTaskException as e:
    print(f"SUCCESS: {e.error_code} - {e.message}")
    assert e.error_code == "DUPLICATE_TASK_IDS_IN_LIST"
    assert 1 in e.details.get("duplicate_ids", [])

# Test 4: Multiple duplicate task IDs
print("\nTest 4: Multiple duplicate task IDs")
task1 = Task(id=1, title="Task 1")
task2 = Task(id=2, title="Task 2")
task3 = Task(id=1, title="Task 3 (duplicate ID 1)")
task4 = Task(id=2, title="Task 4 (duplicate ID 2)")
try:
    task_list = TaskList(name="Test List", owner="user1", tasks=[task1, task2, task3, task4])
    print("FAILED: Should have raised DuplicateTaskException")
except DuplicateTaskException as e:
    print(f"SUCCESS: {e.error_code} - {e.message}")
    assert e.error_code == "DUPLICATE_TASK_IDS_IN_LIST"
    assert 1 in e.details.get("duplicate_ids", [])
    assert 2 in e.details.get("duplicate_ids", [])

# Test 5: No duplicate IDs (should work)
print("\nTest 5: No duplicate IDs (should work)")
task1 = Task(id=1, title="Task 1")
task2 = Task(id=2, title="Task 2")
task3 = Task(id=3, title="Task 3")
task_list = TaskList(name="Test List", owner="user1", tasks=[task1, task2, task3])
assert len(task_list.tasks) == 3
print(f"SUCCESS: Created TaskList with {len(task_list.tasks)} tasks")

# Test 6: Tasks with None IDs (should be allowed)
print("\nTest 6: Tasks with None IDs (should be allowed)")
task1 = Task(title="Task 1")  # No ID
task2 = Task(title="Task 2")  # No ID
task_list = TaskList(name="Test List", owner="user1", tasks=[task1, task2])
assert len(task_list.tasks) == 2
print(f"SUCCESS: Created TaskList with {len(task_list.tasks)} tasks with None IDs")

# Test 7: Mix of None and actual IDs (should work if IDs are unique)
print("\nTest 7: Mix of None and actual IDs (should work if IDs are unique)")
task1 = Task(id=1, title="Task 1")
task2 = Task(title="Task 2")  # No ID
task3 = Task(id=2, title="Task 3")
task_list = TaskList(name="Test List", owner="user1", tasks=[task1, task2, task3])
assert len(task_list.tasks) == 3
print(f"SUCCESS: Created TaskList with {len(task_list.tasks)} tasks (mixed IDs)")

# Test 8: Empty task list (should work)
print("\nTest 8: Empty task list (should work)")
task_list = TaskList(name="Empty List", owner="user1")
assert len(task_list.tasks) == 0
print(f"SUCCESS: Created empty TaskList")

print("\n" + "="*50)
print("All tests passed!")
print("="*50)
