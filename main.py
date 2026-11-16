"""Run a small command-line demonstration of PawPal+."""

from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


def build_demo() -> tuple[Owner, Scheduler]:
    """Create deterministic sample data for the CLI demonstration."""
    today = date.today()
    owner = Owner("Jordan", available_minutes=90)
    mochi = Pet("Mochi", "dog")
    luna = Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Tasks are intentionally added out of chronological order.
    mochi.add_task(Task("Evening walk", "18:00", "daily", today, 30, "high"))
    luna.add_task(Task("Breakfast", "08:00", "daily", today, 10, "high"))
    mochi.add_task(Task("Morning medication", "08:00", "daily", today, 5, "high"))
    luna.add_task(Task("Brush coat", "14:30", "weekly", today, 15, "medium"))
    return owner, Scheduler(owner)


def main() -> None:
    """Print today's sorted schedule and any conflict warnings."""
    owner, scheduler = build_demo()
    today = date.today()

    print(f"Today's Schedule for {owner.name}")
    print("=" * 31)
    for pet, task in scheduler.generate_daily_plan(today):
        print(
            f"{task.time} | {pet.name} ({pet.species}) | {task.description} "
            f"| {task.duration_minutes} min | {task.priority} priority"
        )

    print("\nWarnings")
    print("-" * 8)
    warnings = scheduler.detect_conflicts()
    if warnings:
        for warning in warnings:
            print(f"! {warning}")
    else:
        print("No scheduling conflicts.")


if __name__ == "__main__":
    main()
