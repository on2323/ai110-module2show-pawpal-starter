"""Streamlit interface for the PawPal+ pet-care scheduler."""

from datetime import date

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task


st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan", available_minutes=120)

owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)

st.title("🐾 PawPal+")
st.caption("Plan clear, conflict-aware care schedules for all of your pets.")

with st.sidebar:
    st.header("Owner settings")
    owner.name = st.text_input("Owner name", value=owner.name).strip() or "Pet owner"
    owner.available_minutes = st.number_input(
        "Daily time available (minutes)",
        min_value=0,
        max_value=1440,
        value=owner.available_minutes,
        step=15,
    )

    st.header("Add a pet")
    with st.form("add_pet_form", clear_on_submit=True):
        pet_name = st.text_input("Pet name")
        species = st.selectbox("Species", ["dog", "cat", "bird", "other"])
        add_pet = st.form_submit_button("Add pet", use_container_width=True)
    if add_pet:
        try:
            owner.add_pet(Pet(pet_name.strip(), species))
            st.success(f"Added {pet_name.strip()}.")
        except ValueError as error:
            st.error(str(error))

    if owner.pets:
        st.header("Remove a pet")
        pet_to_remove = st.selectbox(
            "Choose pet", [pet.name for pet in owner.pets], key="remove_pet_name"
        )
        if st.button("Remove selected pet", use_container_width=True):
            owner.remove_pet(pet_to_remove)
            st.rerun()

if not owner.pets:
    st.info("Add your first pet in the sidebar to begin scheduling care.")
    st.stop()

pet_names = [pet.name for pet in owner.pets]
add_tab, manage_tab, schedule_tab = st.tabs(
    ["Add a task", "Manage tasks", "Today's plan"]
)

with add_tab:
    st.subheader("Schedule a care task")
    with st.form("add_task_form", clear_on_submit=True):
        first, second, third = st.columns(3)
        with first:
            selected_pet_name = st.selectbox("Pet", pet_names)
            description = st.text_input("Task description", placeholder="Morning walk")
            task_date = st.date_input("Due date", value=date.today())
        with second:
            task_time = st.time_input("Time")
            duration = st.number_input(
                "Duration (minutes)", min_value=1, max_value=240, value=20
            )
            frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
        with third:
            priority = st.selectbox("Priority", ["high", "medium", "low"])
            st.write("")
            st.write("")
            add_task = st.form_submit_button("Add task", use_container_width=True)

    if add_task:
        try:
            task = Task(
                description=description,
                time=task_time.strftime("%H:%M"),
                frequency=frequency,
                due_date=task_date,
                duration_minutes=int(duration),
                priority=priority,
            )
            selected_pet = owner.get_pet(selected_pet_name)
            if selected_pet is not None:
                selected_pet.add_task(task)
                st.success(f"Added {task.description} for {selected_pet.name}.")
        except ValueError as error:
            st.error(str(error))

with manage_tab:
    st.subheader("View, edit, or complete tasks")
    all_tasks = scheduler.sort_by_time()
    if not all_tasks:
        st.info("No tasks have been added yet.")
    else:
        filter_pet = st.selectbox("Filter by pet", ["All pets", *pet_names])
        status_label = st.selectbox("Filter by status", ["All", "Pending", "Completed"])
        status_filter = {"All": None, "Pending": False, "Completed": True}[status_label]
        visible_tasks = scheduler.filter_tasks(filter_pet, status_filter)

        if visible_tasks:
            st.table(
                [
                    {
                        "Date": task.due_date.isoformat(),
                        "Time": task.time,
                        "Pet": pet.name,
                        "Task": task.description,
                        "Minutes": task.duration_minutes,
                        "Priority": task.priority.title(),
                        "Frequency": task.frequency.title(),
                        "Status": "Complete" if task.completed else "Pending",
                    }
                    for pet, task in visible_tasks
                ]
            )

            selected_index = st.selectbox(
                "Select a task to manage",
                range(len(visible_tasks)),
                format_func=lambda index: (
                    f"{visible_tasks[index][1].due_date} {visible_tasks[index][1].time} — "
                    f"{visible_tasks[index][0].name}: {visible_tasks[index][1].description}"
                ),
            )
            selected_pet, selected_task = visible_tasks[selected_index]
            edit_key = f"{selected_pet.name}_{selected_index}"
            edited_description = st.text_input(
                "Description",
                value=selected_task.description,
                key=f"edit_description_{edit_key}",
            )
            edit_left, edit_middle, edit_right = st.columns(3)
            with edit_left:
                edited_duration = st.number_input(
                    "Minutes",
                    min_value=1,
                    max_value=240,
                    value=selected_task.duration_minutes,
                    key=f"edit_duration_{edit_key}",
                )
            with edit_middle:
                edited_priority = st.selectbox(
                    "Priority",
                    ["high", "medium", "low"],
                    index=["high", "medium", "low"].index(selected_task.priority),
                    key=f"edit_priority_{edit_key}",
                )
            with edit_right:
                st.write("")
                save_task = st.button("Save changes", use_container_width=True)

            action_left, action_right = st.columns(2)
            with action_left:
                complete_task = st.button(
                    "Mark complete",
                    disabled=selected_task.completed,
                    use_container_width=True,
                )
            with action_right:
                delete_task = st.button("Delete task", use_container_width=True)

            if save_task:
                try:
                    replacement = Task(
                        edited_description,
                        selected_task.time,
                        selected_task.frequency,
                        selected_task.due_date,
                        int(edited_duration),
                        edited_priority,
                        selected_task.completed,
                    )
                    task_position = selected_pet.tasks.index(selected_task)
                    selected_pet.tasks[task_position] = replacement
                    st.success("Task updated.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))
            if complete_task:
                next_task = scheduler.mark_task_complete(selected_pet.name, selected_task)
                if next_task is None:
                    st.success("Task completed.")
                else:
                    st.success(
                        f"Task completed. Next occurrence: {next_task.due_date.isoformat()}."
                    )
                st.rerun()
            if delete_task:
                selected_pet.remove_task(selected_task)
                st.rerun()
        else:
            st.info("No tasks match the selected filters.")

with schedule_tab:
    st.subheader(f"Daily plan for {owner.name}")
    plan_date = st.date_input("Plan date", value=date.today(), key="plan_date")
    plan = scheduler.generate_daily_plan(plan_date)
    all_due_tasks = scheduler.filter_tasks(completed=False, due_date=plan_date)
    warnings = scheduler.detect_conflicts(all_due_tasks)

    for warning in warnings:
        st.warning(warning)

    if plan:
        total_minutes = sum(task.duration_minutes for _, task in plan)
        st.success(
            f"Scheduled {len(plan)} task(s) using {total_minutes} of "
            f"{owner.available_minutes} available minutes."
        )
        st.table(
            [
                {
                    "Time": task.time,
                    "Pet": pet.name,
                    "Task": task.description,
                    "Duration": f"{task.duration_minutes} min",
                    "Priority": task.priority.title(),
                    "Why selected": (
                        f"{task.priority.title()} priority and fits the daily time limit"
                    ),
                }
                for pet, task in plan
            ]
        )
        skipped = [pair for pair in all_due_tasks if pair not in plan]
        if skipped:
            st.info(
                "Skipped because the daily time limit was reached: "
                + ", ".join(f"{pet.name}: {task.description}" for pet, task in skipped)
            )
    else:
        st.info("No pending tasks fit this date and time limit.")
