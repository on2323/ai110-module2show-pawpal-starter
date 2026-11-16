"""Core data models and scheduling logic for PawPal+."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta


VALID_FREQUENCIES = {"once", "daily", "weekly"}
VALID_PRIORITIES = {"low", "medium", "high"}
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


@dataclass
class Task:
    """Represent one scheduled pet-care activity."""

    description: str
    time: str
    frequency: str = "once"
    due_date: date = field(default_factory=date.today)
    duration_minutes: int = 15
    priority: str = "medium"
    completed: bool = False

    def __post_init__(self) -> None:
        """Validate and normalize task data after initialization."""
        self.description = self.description.strip()
        self.frequency = self.frequency.lower()
        self.priority = self.priority.lower()

        if not self.description:
            raise ValueError("Task description cannot be empty.")
        try:
            datetime.strptime(self.time, "%H:%M")
        except ValueError as error:
            raise ValueError("Task time must use 24-hour HH:MM format.") from error
        if self.frequency not in VALID_FREQUENCIES:
            raise ValueError("Frequency must be once, daily, or weekly.")
        if self.priority not in VALID_PRIORITIES:
            raise ValueError("Priority must be low, medium, or high.")
        if self.duration_minutes <= 0:
            raise ValueError("Duration must be greater than zero.")

    def mark_complete(self) -> Task | None:
        """Complete this task and return its next recurring occurrence, if any."""
        self.completed = True
        return self.next_occurrence()

    def next_occurrence(self) -> Task | None:
        """Create the next daily or weekly occurrence without changing this task."""
        days = {"daily": 1, "weekly": 7}.get(self.frequency)
        if days is None:
            return None
        return replace(
            self,
            due_date=self.due_date + timedelta(days=days),
            completed=False,
        )


@dataclass
class Pet:
    """Store a pet's details and care tasks."""

    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate and normalize the pet's basic details."""
        self.name = self.name.strip()
        self.species = self.species.strip().lower()
        if not self.name:
            raise ValueError("Pet name cannot be empty.")
        if not self.species:
            raise ValueError("Pet species cannot be empty.")

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet."""
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a care task from this pet."""
        self.tasks.remove(task)


@dataclass
class Owner:
    """Manage one owner's pets and expose all of their tasks."""

    name: str
    available_minutes: int = 480
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet unless another pet already has the same name."""
        if self.get_pet(pet.name) is not None:
            raise ValueError(f"A pet named {pet.name!r} already exists.")
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove the pet with the supplied name."""
        pet = self.get_pet(pet_name)
        if pet is None:
            raise ValueError(f"Pet {pet_name!r} was not found.")
        self.pets.remove(pet)

    def get_pet(self, pet_name: str) -> Pet | None:
        """Find a pet by name using a case-insensitive comparison."""
        target = pet_name.strip().casefold()
        return next((pet for pet in self.pets if pet.name.casefold() == target), None)

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every task paired with the pet it belongs to."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]


@dataclass
class Scheduler:
    """Organize, filter, complete, and inspect an owner's pet-care tasks."""

    owner: Owner

    def sort_by_time(
        self, tasks: list[tuple[Pet, Task]] | None = None
    ) -> list[tuple[Pet, Task]]:
        """Return task pairs ordered by due date and then scheduled time."""
        task_pairs = self.owner.get_all_tasks() if tasks is None else tasks
        return sorted(task_pairs, key=lambda pair: (pair[1].due_date, pair[1].time))

    def filter_tasks(
        self,
        pet_name: str | None = None,
        completed: bool | None = None,
        due_date: date | None = None,
    ) -> list[tuple[Pet, Task]]:
        """Filter all owner tasks by pet, completion status, and/or date."""
        matches = self.owner.get_all_tasks()
        if pet_name and pet_name != "All pets":
            target = pet_name.casefold()
            matches = [(pet, task) for pet, task in matches if pet.name.casefold() == target]
        if completed is not None:
            matches = [(pet, task) for pet, task in matches if task.completed is completed]
        if due_date is not None:
            matches = [(pet, task) for pet, task in matches if task.due_date == due_date]
        return self.sort_by_time(matches)

    def generate_daily_plan(
        self, plan_date: date, available_minutes: int | None = None
    ) -> list[tuple[Pet, Task]]:
        """Select priority-ranked incomplete tasks that fit the owner's time limit."""
        limit = self.owner.available_minutes if available_minutes is None else available_minutes
        if limit < 0:
            raise ValueError("Available minutes cannot be negative.")

        candidates = self.filter_tasks(completed=False, due_date=plan_date)
        ranked = sorted(
            candidates,
            key=lambda pair: (PRIORITY_RANK[pair[1].priority], pair[1].time),
        )
        selected: list[tuple[Pet, Task]] = []
        used_minutes = 0
        for pet, task in ranked:
            if used_minutes + task.duration_minutes <= limit:
                selected.append((pet, task))
                used_minutes += task.duration_minutes
        return self.sort_by_time(selected)

    def mark_task_complete(self, pet_name: str, task: Task) -> Task | None:
        """Complete a pet's task and add its next occurrence when recurring."""
        pet = self.owner.get_pet(pet_name)
        if pet is None:
            raise ValueError(f"Pet {pet_name!r} was not found.")
        if task not in pet.tasks:
            raise ValueError("That task does not belong to the selected pet.")

        next_task = task.mark_complete()
        if next_task is not None:
            pet.add_task(next_task)
        return next_task

    def detect_conflicts(
        self, tasks: list[tuple[Pet, Task]] | None = None
    ) -> list[str]:
        """Return warnings for incomplete tasks sharing the same date and time."""
        task_pairs = self.owner.get_all_tasks() if tasks is None else tasks
        grouped: dict[tuple[date, str], list[tuple[Pet, Task]]] = {}
        for pet, task in task_pairs:
            if not task.completed:
                grouped.setdefault((task.due_date, task.time), []).append((pet, task))

        warnings: list[str] = []
        for (task_date, task_time), matches in sorted(grouped.items()):
            if len(matches) > 1:
                details = ", ".join(
                    f"{pet.name}: {task.description}" for pet, task in matches
                )
                warnings.append(
                    f"Conflict at {task_time} on {task_date.isoformat()}: {details}"
                )
        return warnings
