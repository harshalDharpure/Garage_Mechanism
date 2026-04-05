"""Entry point for the garage scheduling demo."""

from __future__ import annotations

import argparse
import os

from .config import GarageConfig
from .simulation import GarageSimulation
from .visualization import plot_gantt_chart, plot_dag


def main(display: bool = True) -> None:
    """Run a complete demo scenario and produce visualisations."""
    cfg = GarageConfig(
        num_mechanics=3,
        consecutive_limit=3,
        random_seed=42,
    )

    print("=" * 60)
    print("Problem 3 - Garage Scheduling")
    print("=" * 60)
    print(f"  Mechanics        : {cfg.num_mechanics}")
    print(f"  Consecutive limit: {cfg.consecutive_limit}")
    print(f"  Cars to service  : {cfg.cars}")
    print()

    sim = GarageSimulation(cfg=cfg)
    results = sim.run()

    print(f"  Initial makespan  : {results['initial_makespan']} time units")
    print(f"  Final makespan    : {results['final_makespan']} time units")
    print(f"  Dynamic tasks added: {results['num_dynamic_tasks']}")
    print()

    if results["events"]:
        print("  Dynamic task events:")
        for ev in results["events"]:
            print(
                f"    t={ev.timestep:3d} | car={ev.car_id} | "
                f"triggered by '{ev.triggered_by}' -> '{ev.new_task}' "
                f"(p={ev.probability:.2f}, rand={ev.random_value:.2f})"
            )
        print()

    # Print schedule
    print("  Full schedule:")
    for task in results["all_tasks"]:
        label = "BREAK" if task.is_break else task.task_name
        print(
            f"    Mech {task.mechanic_id} | "
            f"t=[{task.start_time},{task.end_time}] | "
            f"car={task.car_id} | {label}"
        )

    out_dir = os.path.dirname(__file__)

    # Gantt chart
    mechanics_schedule = [mech.schedule for mech in sim.mechanics]
    plot_gantt_chart(
        mechanics_schedule,
        num_mechanics=cfg.num_mechanics,
        save_path=os.path.join(out_dir, "garage_gantt.png"),
        show=display,
    )

    # DAG visualisations
    for dag in sim.dags:
        plot_dag(
            dag,
            save_path=os.path.join(out_dir, f"garage_dag_type{dag.car_type_id}.png"),
            show=display,
        )

    print(f"\nFigures saved to: {out_dir}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Garage scheduling demo")
    parser.add_argument("--no-display", action="store_true")
    args = parser.parse_args()
    main(display=not args.no_display)
