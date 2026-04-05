"""Mechanic class with fatigue management."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class ScheduledTask:
    """A single task assigned to a mechanic."""

    mechanic_id: int
    car_id: int
    car_type: int
    task_name: str
    start_time: int
    end_time: int   # start_time + 1  (each task = 1 time unit)
    is_break: bool = False

    def __repr__(self) -> str:
        label = "BREAK" if self.is_break else self.task_name
        return (
            f"ScheduledTask(mech={self.mechanic_id}, car={self.car_id}, "
            f"task={label}, t=[{self.start_time},{self.end_time}])"
        )


class Mechanic:
    """A garage mechanic with fatigue tracking.

    Parameters
    ----------
    mechanic_id:
        Unique identifier.
    consecutive_limit:
        Number of consecutive tasks before a mandatory 1-unit break.
    """

    def __init__(self, mechanic_id: int, consecutive_limit: int = 3) -> None:
        self.mechanic_id = mechanic_id
        self.consecutive_limit = consecutive_limit

        self.schedule: List[ScheduledTask] = []
        self._consecutive_count: int = 0
        self._free_at: int = 0  # earliest timestep this mechanic is available

    @property
    def free_at(self) -> int:
        """Earliest timestep at which this mechanic is free."""
        return self._free_at

    def assign_task(
        self, car_id: int, car_type: int, task_name: str, earliest: int = 0
    ) -> ScheduledTask:
        """Schedule *task_name* for this mechanic at the earliest possible time.

        Inserts a break automatically if the consecutive limit is reached.

        Parameters
        ----------
        car_id:
            Identifier of the car being worked on.
        car_type:
            Car type index.
        task_name:
            Name of the task.
        earliest:
            The task cannot start before this timestep.

        Returns
        -------
        ScheduledTask
        """
        start = max(self._free_at, earliest)

        # Insert break if consecutive limit reached
        if self._consecutive_count >= self.consecutive_limit:
            brk = ScheduledTask(
                mechanic_id=self.mechanic_id,
                car_id=-1,
                car_type=-1,
                task_name="BREAK",
                start_time=start,
                end_time=start + 1,
                is_break=True,
            )
            self.schedule.append(brk)
            start += 1
            self._consecutive_count = 0

        task = ScheduledTask(
            mechanic_id=self.mechanic_id,
            car_id=car_id,
            car_type=car_type,
            task_name=task_name,
            start_time=start,
            end_time=start + 1,
        )
        self.schedule.append(task)
        self._free_at = start + 1
        self._consecutive_count += 1
        return task

    def __repr__(self) -> str:
        return (
            f"Mechanic(id={self.mechanic_id}, free_at={self._free_at}, "
            f"consecutive={self._consecutive_count})"
        )
