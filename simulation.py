"""Simulation with probabilistic task generation for the garage."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .config import GarageConfig
from .mechanic import Mechanic, ScheduledTask
from .scheduler import GarageScheduler
from .task_dag import TaskDAG, build_dags_from_config


@dataclass
class SimulationEvent:
    """Record of a probabilistic task being spawned."""
    timestep: int
    car_id: int
    car_type: int
    triggered_by: str
    new_task: str
    probability: float
    random_value: float


class GarageSimulation:
    """Simulate the garage including dynamic task generation.

    Parameters
    ----------
    cfg:
        Garage configuration.
    """

    def __init__(self, cfg: Optional[GarageConfig] = None) -> None:
        self.cfg = cfg or GarageConfig()
        if self.cfg.random_seed is not None:
            random.seed(self.cfg.random_seed)

        self.dags: List[TaskDAG] = build_dags_from_config(self.cfg.car_dags)
        self.mechanics: List[Mechanic] = [
            Mechanic(i, self.cfg.consecutive_limit)
            for i in range(self.cfg.num_mechanics)
        ]
        self.scheduler = GarageScheduler(self.mechanics, self.dags)
        self.events: List[SimulationEvent] = []

    def run(self) -> Dict:
        """Build the initial schedule then run probabilistic task generation.

        Returns
        -------
        dict with keys:
            initial_makespan, final_makespan, num_dynamic_tasks,
            all_tasks, events
        """
        # 1. Initial schedule — only root tasks
        self.scheduler.build_initial_schedule(self.cfg.cars)
        initial_makespan = self.scheduler.makespan()

        # 2. Simulate probabilistic follow-ups.
        # Each DAG edge is rolled once when its tail task completes.  A task is
        # "generated" when any incoming edge succeeds; it is scheduled only
        # after all its predecessors have finished (DAG semantics).
        processed_edges: set = set()
        generated_tasks: set = set()
        changed = True
        while changed:
            changed = False
            # Collect all currently scheduled tasks sorted by end_time
            current_tasks = list(self.scheduler.completed.items())
            current_tasks.sort(key=lambda x: x[1].end_time)
            for (car_id, task_name), completed_task in current_tasks:
                car_type = completed_task.car_type
                dag = self.dags[car_type]
                if task_name not in dag.G:
                    continue
                for succ, prob in dag.successors(task_name):
                    edge_key = (car_id, task_name, succ)
                    if edge_key in processed_edges:
                        continue
                    processed_edges.add(edge_key)
                    if (car_id, succ) in self.scheduler.completed:
                        continue
                    rand_val = random.random()
                    # Task IS generated if rand_val > probability
                    if rand_val > prob:
                        was_new = (car_id, succ) not in generated_tasks
                        generated_tasks.add((car_id, succ))
                        if was_new:
                            self.events.append(
                                SimulationEvent(
                                    timestep=completed_task.end_time,
                                    car_id=car_id,
                                    car_type=car_type,
                                    triggered_by=task_name,
                                    new_task=succ,
                                    probability=prob,
                                    random_value=rand_val,
                                )
                            )
                        changed = True

            # Schedule any generated task whose predecessors are all complete.
            for car_id, task_name in list(generated_tasks):
                if (car_id, task_name) in self.scheduler.completed:
                    continue
                car_type = self.cfg.cars[car_id]
                scheduled = self.scheduler.add_dynamic_task(
                    car_id=car_id,
                    car_type=car_type,
                    task_name=task_name,
                )
                if scheduled is not None:
                    changed = True

        final_makespan = self.scheduler.makespan()
        all_tasks = self.scheduler.all_scheduled_tasks()

        return {
            "initial_makespan": initial_makespan,
            "final_makespan": final_makespan,
            "num_dynamic_tasks": len(self.events),
            "all_tasks": all_tasks,
            "events": self.events,
        }
