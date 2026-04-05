"""Initial scheduler and dynamic rescheduler for garage tasks.

Scheduling strategy:
- Build a global task list from all cars' DAGs using topological order.
- Assign tasks to the mechanic that will finish earliest (list scheduling /
  critical-path-style).
- When new probabilistic tasks are added, insert them respecting dependencies
  and re-pack the mechanic schedules from the insertion point.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .mechanic import Mechanic, ScheduledTask
from .task_dag import TaskDAG


# ---------------------------------------------------------------------------
# Task entry in the global queue
# ---------------------------------------------------------------------------

class PendingTask:
    """A task waiting to be scheduled.

    Parameters
    ----------
    car_id:
        Which car this task belongs to.
    car_type:
        Car type index.
    task_name:
        Name of the task.
    earliest_start:
        Cannot be scheduled before this timestep (set by predecessor finish).
    """

    def __init__(
        self,
        car_id: int,
        car_type: int,
        task_name: str,
        earliest_start: int = 0,
    ) -> None:
        self.car_id = car_id
        self.car_type = car_type
        self.task_name = task_name
        self.earliest_start = earliest_start

    def __lt__(self, other: "PendingTask") -> bool:
        return self.earliest_start < other.earliest_start

    def __repr__(self) -> str:
        return (
            f"PendingTask(car={self.car_id}, task={self.task_name}, "
            f"earliest={self.earliest_start})"
        )


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class GarageScheduler:
    """Schedules cars' tasks across multiple mechanics.

    Parameters
    ----------
    mechanics:
        List of Mechanic instances.
    dags:
        List of TaskDAG objects (one per car type).
    """

    def __init__(self, mechanics: List[Mechanic], dags: List[TaskDAG]) -> None:
        self.mechanics = mechanics
        self.dags = dags
        # Maps (car_id, task_name) → ScheduledTask
        self.completed: Dict[Tuple[int, str], ScheduledTask] = {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _pick_mechanic(self, earliest: int) -> Mechanic:
        """Return the mechanic that can start *earliest* at or after *earliest*."""
        return min(self.mechanics, key=lambda m: max(m.free_at, earliest))

    def _schedule_task(self, pending: PendingTask) -> ScheduledTask:
        """Assign *pending* to a mechanic and record it."""
        mech = self._pick_mechanic(pending.earliest_start)
        task = mech.assign_task(
            car_id=pending.car_id,
            car_type=pending.car_type,
            task_name=pending.task_name,
            earliest=pending.earliest_start,
        )
        self.completed[(pending.car_id, pending.task_name)] = task
        return task

    # ------------------------------------------------------------------
    # Initial schedule (no probabilistic tasks)
    # ------------------------------------------------------------------

    def build_initial_schedule(self, cars: List[int]) -> None:
        """Build the initial optimal schedule for *cars*.

        Only **root tasks** (no predecessors) are scheduled initially.
        Probabilistic successors are added dynamically during simulation.

        Parameters
        ----------
        cars:
            List of car-type indices to service (in order).
        """
        for car_id, car_type in enumerate(cars):
            dag = self.dags[car_type]
            for task_name in dag.root_tasks:
                pending = PendingTask(
                    car_id=car_id,
                    car_type=car_type,
                    task_name=task_name,
                    earliest_start=0,
                )
                self._schedule_task(pending)

    # ------------------------------------------------------------------
    # Dynamic rescheduling
    # ------------------------------------------------------------------

    def add_dynamic_task(
        self,
        car_id: int,
        car_type: int,
        task_name: str,
    ) -> Optional[ScheduledTask]:
        """Schedule a probabilistically generated task when the DAG allows it.

        A task with several predecessors cannot start until **all** of them have
        finished; ``earliest_start`` is the maximum of their end times.  Returns
        ``None`` if predecessors are not all completed yet or the task is
        already scheduled.
        """
        if (car_id, task_name) in self.completed:
            return None

        dag = self.dags[car_type]
        if task_name not in dag.G:
            return None

        preds = list(dag.G.predecessors(task_name))
        if preds:
            if not all((car_id, p) in self.completed for p in preds):
                return None
            earliest = max(self.completed[(car_id, p)].end_time for p in preds)
        else:
            earliest = 0

        pending = PendingTask(
            car_id=car_id,
            car_type=car_type,
            task_name=task_name,
            earliest_start=earliest,
        )
        return self._schedule_task(pending)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def makespan(self) -> int:
        """Return overall schedule makespan."""
        if not self.completed:
            return 0
        return max(t.end_time for t in self.completed.values())

    def all_scheduled_tasks(self) -> List[ScheduledTask]:
        """Return all tasks (including breaks) sorted by start time."""
        all_tasks: List[ScheduledTask] = []
        for mech in self.mechanics:
            all_tasks.extend(mech.schedule)
        all_tasks.sort(key=lambda t: (t.start_time, t.mechanic_id))
        return all_tasks
