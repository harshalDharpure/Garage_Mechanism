"""Task Dependency Graph (DAG) models for car types."""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple

import networkx as nx


class TaskDAG:
    """A DAG representing the task dependency structure for one car type.

    Nodes are task names (strings).  Edge ``(u, v)`` carries a ``probability``
    attribute indicating the chance that completing *u* spawns the follow-up
    task *v*.

    Parameters
    ----------
    dag_edges:
        List of ``(from_task, to_task, probability)`` tuples.
    car_type_id:
        Identifier for this car type.
    """

    def __init__(
        self,
        dag_edges: List[Tuple[str, str, float]],
        car_type_id: int = 0,
    ) -> None:
        self.car_type_id = car_type_id
        self.G: nx.DiGraph = nx.DiGraph()
        for u, v, p in dag_edges:
            self.G.add_edge(u, v, probability=p)

    @property
    def tasks(self) -> List[str]:
        """All task names in topological order."""
        return list(nx.topological_sort(self.G))

    @property
    def root_tasks(self) -> List[str]:
        """Tasks with no predecessors."""
        return [n for n in self.G.nodes if self.G.in_degree(n) == 0]

    def successors(self, task: str) -> List[Tuple[str, float]]:
        """Return ``[(successor_task, probability), ...]`` for *task*."""
        return [
            (v, self.G[task][v]["probability"])
            for v in self.G.successors(task)
        ]

    def topological_order(self) -> List[str]:
        """Tasks in topological order (dependencies before dependents)."""
        return list(nx.topological_sort(self.G))

    def __repr__(self) -> str:
        return f"TaskDAG(car_type={self.car_type_id}, tasks={self.tasks})"


def build_dags_from_config(
    car_dags: List[List[Tuple[str, str, float]]],
) -> List[TaskDAG]:
    """Build a list of TaskDAG objects from the config definition."""
    return [TaskDAG(edges, car_type_id=i) for i, edges in enumerate(car_dags)]
