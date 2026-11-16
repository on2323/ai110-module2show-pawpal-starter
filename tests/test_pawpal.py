"""Automated tests for PawPal+'s core behaviors."""

from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task


@pytest.fixture
def system() -> tuple[Owner, Pet, Scheduler]:
    """Create a basic owner, pet, and scheduler for tests."""
    owner = Owner("Jordan")
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    return owner, pet, Scheduler(owner)


def test_mark_complete_changes_task_status() -> None:
    task = Task("Walk", "08:00")

    task.mark_complete()

    assert task.completed is True


def test_adding_task_increases_pet_task_count() -> None:
    pet = Pet("Mochi", "dog")

    pet.add_task(Task("Walk", "08:00"))

    assert len(pet.tasks) == 1


def test_owner_returns_tasks_from_multiple_pets() -> None:
    owner = Owner("Jordan")
    first_pet = Pet("Mochi", "dog", [Task("Walk", "09:00")])
    second_pet = Pet("Luna", "cat", [Task("Feed", "08:00")])
    owner.add_pet(first_pet)
    owner.add_pet(second_pet)

    assert len(owner.get_all_tasks()) == 2


def test_sorting_returns_chronological_order(system) -> None:
    _, pet, scheduler = system
    pet.add_task(Task("Evening walk", "18:00"))
    pet.add_task(Task("Breakfast", "07:30"))
    pet.add_task(Task("Medication", "12:00"))

    descriptions = [task.description for _, task in scheduler.sort_by_time()]

    assert descriptions == ["Breakfast", "Medication", "Evening walk"]


def test_filtering_by_pet_and_status() -> None:
    owner = Owner("Jordan")
    mochi = Pet("Mochi", "dog", [Task("Walk", "08:00", completed=True)])
    luna = Pet("Luna", "cat", [Task("Feed", "09:00")])
    owner.add_pet(mochi)
    owner.add_pet(luna)
    scheduler = Scheduler(owner)

    matches = scheduler.filter_tasks(pet_name="Luna", completed=False)

    assert [(pet.name, task.description) for pet, task in matches] == [("Luna", "Feed")]


def test_daily_recurrence_creates_task_for_next_day(system) -> None:
    _, pet, scheduler = system
    original = Task("Walk", "08:00", frequency="daily", due_date=date(2026, 11, 16))
    pet.add_task(original)

    next_task = scheduler.mark_task_complete("Mochi", original)

    assert original.completed is True
    assert next_task is not None
    assert next_task.due_date == original.due_date + timedelta(days=1)
    assert next_task in pet.tasks
    assert next_task.completed is False


def test_conflict_detection_flags_duplicate_times(system) -> None:
    _, pet, scheduler = system
    task_date = date(2026, 11, 16)
    pet.add_task(Task("Walk", "08:00", due_date=task_date))
    pet.add_task(Task("Medication", "08:00", due_date=task_date))

    warnings = scheduler.detect_conflicts()

    assert len(warnings) == 1
    assert "Conflict at 08:00" in warnings[0]


def test_daily_plan_respects_priority_and_available_time(system) -> None:
    _, pet, scheduler = system
    task_date = date(2026, 11, 16)
    pet.add_task(Task("Optional grooming", "08:00", due_date=task_date, duration_minutes=30, priority="low"))
    pet.add_task(Task("Medication", "09:00", due_date=task_date, duration_minutes=10, priority="high"))

    plan = scheduler.generate_daily_plan(task_date, available_minutes=10)

    assert [task.description for _, task in plan] == ["Medication"]


def test_empty_pet_has_no_scheduled_tasks(system) -> None:
    _, _, scheduler = system

    assert scheduler.sort_by_time() == []
    assert scheduler.detect_conflicts() == []


def test_invalid_time_is_rejected() -> None:
    with pytest.raises(ValueError, match="HH:MM"):
        Task("Walk", "8 AM")
