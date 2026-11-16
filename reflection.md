# PawPal+ Project Reflection

## 1. System Design

### a. Initial design

My initial design focused on three core user actions: adding or deleting a pet, tracking care tasks, and viewing a daily plan. I modeled those actions with four classes:

- `Task` stores one activity's description, time, recurrence, date, duration, priority, and completion status.
- `Pet` stores pet details and owns that pet's tasks.
- `Owner` manages multiple pets and provides `get_all_tasks()` so the rest of the system can work across every pet.
- `Scheduler` is the logic layer that sorts, filters, prioritizes, completes, and checks tasks for conflicts.

The ownership chain is `Owner` → `Pet` → `Task`. `Scheduler` depends on `Owner` instead of on one `Pet`, which keeps multi-pet scheduling central to the design.

### b. Design changes

An early AI suggestion used six classes, including separate scheduled-task and daily-plan objects. I simplified that design to the four assignment-focused classes because the extra objects duplicated data and made a small app harder to follow. During implementation, I added `due_date`, `duration_minutes`, and `priority` to `Task`, plus `available_minutes` to `Owner`. These fields let the scheduler support recurrence, time constraints, and priority-aware selection without adding more classes.

I also changed recurrence from being handled only inside `Task` to a two-step collaboration: `Task.mark_complete()` creates the next occurrence, while `Scheduler.mark_task_complete()` adds that occurrence to the correct pet. This avoids giving a task knowledge of its parent pet.

## 2. Scheduling Logic and Tradeoffs

### a. Constraints and priorities

The scheduler considers due date, completion status, scheduled time, task duration, priority, pet name, and the owner's available minutes. `generate_daily_plan()` first limits candidates to incomplete tasks on the selected date. It ranks high-priority tasks before medium- and low-priority tasks, selects tasks that fit the time budget, and finally displays the selected work chronologically.

I treated date and completion status as hard constraints because a daily plan should not show completed or wrong-day work. Available minutes are also a hard limit. Priority controls which tasks are selected when everything cannot fit, while time controls the final display order.

### b. Tradeoffs

Conflict detection flags tasks only when their dates and start times match exactly. It does not calculate overlaps from task durations. This is a deliberate tradeoff: exact-time warnings are simple, predictable, and appropriate for the project's scope, but a future version should detect ranges such as an 08:00–08:30 walk overlapping an 08:15 medication task.

## 3. AI Collaboration

### a. How I used AI

I used an AI coding assistant to turn the requirements into a UML draft, generate and refine Python class structure, suggest sorting and filtering logic, design edge-case tests, connect Streamlit session state to backend objects, and review the final documentation. The most useful prompts named a specific behavior and constraint, such as asking how the scheduler should retrieve tasks from all of an owner's pets or how recurrence should be tested.

Keeping design, implementation, testing, and documentation as separate phase-focused conversations made the context easier to review. Each phase had one main goal, so suggestions were easier to compare against the rubric before accepting them.

### b. Judgment and verification

I did not keep the initial six-class AI design. Although it was flexible, it introduced `ScheduledTask` and `DailyPlan` before the project needed them. I chose the clearer four-class model and verified that it still covered every required behavior through the UML, CLI demo, UI, and tests.

I also kept the readable multi-step scheduling algorithm instead of compressing it into one dense expression. I verified the result by compiling the Python files, running the CLI demo, running all automated tests, and smoke-testing the Streamlit app. The final run passed 10 tests and reported no Streamlit exceptions.

## 4. Testing and Verification

### a. What I tested

The suite verifies that completing a task changes its status, adding a task increases a pet's task count, and an owner returns tasks from multiple pets. It also tests chronological sorting, filtering by pet and status, daily recurrence, duplicate-time conflict warnings, priority selection under a time limit, an empty pet schedule, and rejection of invalid time strings.

These behaviors cover both happy paths and the most important edge cases. Multi-pet retrieval is especially important because all scheduler algorithms depend on `Owner.get_all_tasks()`.

### b. Confidence

My confidence level is 5/5 for the implemented scope because all 10 automated tests pass, the CLI demonstration produces a correctly ordered schedule and warning, and the Streamlit smoke test reports no exceptions. With more time, I would test overlapping duration ranges, persistence across browser sessions, timezone behavior, and a larger number of pets and tasks.

## 5. Reflection

### a. What went well

I am most satisfied with the separation between the interface and the logic layer. The CLI and Streamlit app use the same four backend classes, so sorting, recurrence, filtering, and conflicts behave consistently in both places.

### b. What I would improve

In another iteration, I would store data in a database instead of only in Streamlit session state. I would also use stable task IDs, support notification reminders, and upgrade conflict detection to compare actual time ranges.

### c. Key takeaway

My main takeaway is that using AI effectively still requires acting as the lead architect. AI can quickly propose code and alternatives, but I need to compare those suggestions to the rubric, remove unnecessary complexity, choose clear ownership boundaries, and verify behavior with executable tests.
