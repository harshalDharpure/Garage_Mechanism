"""Visualisation utilities for the garage simulation."""

from __future__ import annotations

import os
from typing import Dict, List, Optional

import matplotlib
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import networkx as nx

from .mechanic import ScheduledTask
from .task_dag import TaskDAG

if not os.environ.get("DISPLAY"):
    matplotlib.use("Agg")


_COLORS = [
    "#3498db", "#e74c3c", "#2ecc71", "#f39c12",
    "#9b59b6", "#1abc9c", "#e67e22", "#e91e63",
    "#34495e", "#16a085",
]


def plot_gantt_chart(
    mechanics_schedule: List[List[ScheduledTask]],
    num_mechanics: int,
    save_path: Optional[str] = None,
    show: bool = True,
) -> None:
    """Draw a Gantt chart for all mechanics.

    Parameters
    ----------
    mechanics_schedule:
        ``mechanics_schedule[i]`` is the list of ``ScheduledTask`` for mechanic *i*.
    num_mechanics:
        Total number of mechanics.
    save_path:
        Save figure to this path if given.
    show:
        Whether to call ``plt.show()``.
    """
    fig, ax = plt.subplots(figsize=(14, max(4, num_mechanics * 1.5)))
    height = 0.6

    for mech_id in range(num_mechanics):
        tasks = mechanics_schedule[mech_id]
        for task in tasks:
            if task.is_break:
                color = "#bdc3c7"
                label = "BREAK"
            else:
                color = _COLORS[task.car_id % len(_COLORS)]
                label = f"C{task.car_id}:{task.task_name[:8]}"
            duration = task.end_time - task.start_time
            ax.barh(
                mech_id,
                width=duration,
                left=task.start_time,
                height=height,
                color=color,
                edgecolor="white",
                alpha=0.85,
            )
            if duration > 0:
                ax.text(
                    task.start_time + duration / 2,
                    mech_id,
                    label,
                    ha="center",
                    va="center",
                    fontsize=6,
                    color="black",
                )

    ax.set_yticks(range(num_mechanics))
    ax.set_yticklabels([f"Mechanic {i}" for i in range(num_mechanics)])
    ax.set_xlabel("Time (units)")
    ax.set_title("Garage Schedule — Gantt Chart")
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=100)
    if show:
        plt.show()
    plt.close(fig)


def plot_dag(
    dag: TaskDAG,
    save_path: Optional[str] = None,
    show: bool = True,
) -> None:
    """Visualise a task DAG with edge probabilities.

    Parameters
    ----------
    dag:
        TaskDAG to visualise.
    save_path:
        Save figure to this path if given.
    show:
        Whether to call ``plt.show()``.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    G = dag.G
    try:
        pos = nx.nx_agraph.graphviz_layout(G, prog="dot")
    except Exception:
        pos = nx.spring_layout(G, seed=42)

    nx.draw_networkx(
        G,
        pos=pos,
        ax=ax,
        node_color="#3498db",
        node_size=1500,
        font_size=8,
        font_color="white",
        arrows=True,
        arrowsize=20,
        edge_color="#7f8c8d",
    )
    edge_labels = {
        (u, v): f"{d['probability']:.2f}"
        for u, v, d in G.edges(data=True)
    }
    nx.draw_networkx_edge_labels(G, pos=pos, edge_labels=edge_labels, font_size=7, ax=ax)
    ax.set_title(f"Task DAG — Car Type {dag.car_type_id}")
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=100)
    if show:
        plt.show()
    plt.close(fig)
