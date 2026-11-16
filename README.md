# PawPal+

PawPal+ is a Streamlit pet-care planner for owners managing one or more pets. It stores care tasks, builds a priority-aware daily plan, identifies exact-time conflicts, and automatically schedules the next occurrence of recurring tasks.

## Features

- Add and remove multiple pets.
- Add, edit, complete, delete, and filter care tasks.
- Store task time, date, duration, priority, frequency, and completion status.
- Sort every pet's tasks chronologically.
- Build a daily plan that favors higher-priority work while respecting the owner's available time.
- Warn when two pending tasks share the same date and time.
- Create the next occurrence when a daily or weekly task is completed.
- Preserve owner, pet, and task objects during Streamlit reruns with `st.session_state`.

## Architecture

The backend in `pawpal_system.py` contains four focused classes:

- `Task` represents one care activity and handles recurrence.
- `Pet` owns a list of its care tasks.
- `Owner` manages multiple pets and exposes all pet tasks through `get_all_tasks()`.
- `Scheduler` reads tasks through the `Owner`, then sorts, filters, selects, completes, and checks them for conflicts.

The final Mermaid source is in [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd). The initial draft is preserved in [`diagrams/uml_draft.mmd`](diagrams/uml_draft.mmd), and a JavaScript-exportable copy is available in [`mermaid.js`](mermaid.js).

## Setup and Run

```bash
python -m venv .venv
source .venv/Scripts/activate  # Git Bash on Windows
python -m pip install -r requirements.txt
streamlit run app.py
```

For PowerShell, activate with:

```powershell
.\.venv\Scripts\Activate.ps1
```

Run the command-line demonstration with:

```bash
python main.py
```

## Sample CLI Output

```text
Today's Schedule for Jordan
===============================
08:00 | Mochi (dog) | Morning medication | 5 min | high priority
08:00 | Luna (cat) | Breakfast | 10 min | high priority
14:30 | Luna (cat) | Brush coat | 15 min | medium priority
18:00 | Mochi (dog) | Evening walk | 30 min | high priority

Warnings
--------
! Conflict at 08:00 on 2026-11-16: Mochi: Morning medication, Luna: Breakfast
```

## Smarter Scheduling

| Feature | Method | Behavior |
|---|---|---|
| Task sorting | `Scheduler.sort_by_time()` | Sorts by due date and `HH:MM` time. |
| Filtering | `Scheduler.filter_tasks()` | Filters by pet, completion status, and/or date. |
| Daily planning | `Scheduler.generate_daily_plan()` | Selects high-priority tasks first within the time limit, then returns them chronologically. |
| Conflict handling | `Scheduler.detect_conflicts()` | Returns warnings for pending tasks at the same date and time. |
| Recurring tasks | `Task.next_occurrence()` and `Scheduler.mark_task_complete()` | Adds the next daily or weekly task after completion. |

Conflict detection intentionally checks exact date-and-time matches instead of calculating overlapping duration ranges. This keeps warnings predictable and easy to understand.

## Testing PawPal+

Run the automated suite with:

```bash
python -m pytest
```

The tests cover completion, task addition, multi-pet retrieval, chronological sorting, filtering, recurrence, conflict detection, priority/time constraints, empty schedules, and invalid time input.

```text
..........                                                               [100%]
10 passed in 0.19s
```

**Confidence level:** ★★★★★ (5/5) based on passing backend tests and a Streamlit smoke test with no application exceptions.

## Demo Walkthrough

1. Start the app with `streamlit run app.py` and enter the owner's name and daily available minutes in the sidebar.
2. Add at least two pets from the sidebar.
3. Open **Add a task** and enter each task's pet, date, time, duration, priority, and recurrence.
4. Open **Manage tasks** to filter, edit, complete, or delete tasks. Completing a recurring task creates its next occurrence.
5. Open **Today's plan** to see the selected tasks in time order, the reason each task was selected, skipped tasks, and conflict warnings.
6. Run `python main.py` to view the same multi-pet scheduling behavior in the terminal.
