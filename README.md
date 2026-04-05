# Problem 3 — Garage Scheduling

Python demo for the garage scheduling problem: **M** mechanics, **N** car types as task DAGs with probabilistic edges, mandatory breaks after **k** consecutive tasks, dynamic rescheduling when new tasks appear.

## Requirements

- Python 3.10 or newer (tested on 3.13)
- Dependencies: `networkx`, `matplotlib`

## Setup

From a terminal:

```powershell
cd c:\Users\HARSHAL\Downloads\garage_project
pip install -r requirements.txt
```

(Use your own path if the project lives elsewhere.)

## How to run

The code uses **package imports** (`from .config import …`). Run the module **from the parent folder** of `garage_project` so Python can resolve the package name `garage_project`.

**Windows (PowerShell):**

```powershell
cd c:\Users\HARSHAL\Downloads
python -m garage_project.main
```

**Skip opening plot windows** (recommended on servers or SSH; figures are still saved):

```powershell
python -m garage_project.main --no-display
```

**Alternative** (same parent directory):

```powershell
$env:PYTHONPATH = "c:\Users\HARSHAL\Downloads"
python -m garage_project.main --no-display
```

Do **not** run `python main.py` from inside `garage_project`; relative imports will fail.

## Output

- **Console:** initial and final makespan, probabilistic events, full per-mechanic schedule (tasks and `BREAK` slots).
- **PNG files** next to the package (under `garage_project/`):
  - `garage_gantt.png` — Gantt chart for all mechanics
  - `garage_dag_type0.png`, `garage_dag_type1.png`, … — task DAGs per car type

DAG layout uses Graphviz **if** `pygraphviz` and Graphviz are installed; otherwise a spring layout is used automatically.

## Behaviour vs problem statement

| Spec | Implementation |
|------|------------------|
| 1 time unit per task | Each task occupies `[t, t+1)`. |
| Edge weight = spawn probability | After a task finishes, for each outgoing edge a draw `r = random.random()` runs; the child is **generated** if `r > probability` (as stated). |
| Initial schedule ignoring probabilistic outcomes | Only **root** tasks (no predecessors) are placed first; other nodes enter the plan when generated. |
| Update schedule when a new task appears | Generated tasks are assigned with list scheduling (mechanic with earliest availability), respecting **all** predecessor finish times for multi-parent tasks. |
| Break after **k** consecutive tasks | Before the next task, a 1-unit `BREAK` is inserted when the limit is reached. |

Tune **M**, **k**, car list, and DAGs in `garage_project/config.py` (`GarageConfig`).

## Project layout

```
garage_project/
├── __init__.py
├── config.py          # GarageConfig (M, k, DAGs, cars, seed)
├── task_dag.py        # TaskDAG (NetworkX DAG + probabilities)
├── mechanic.py        # Mechanic fatigue / ScheduledTask
├── scheduler.py       # Initial + dynamic scheduling
├── simulation.py      # Probabilistic simulation loop
├── visualization.py   # Gantt + DAG plots
├── main.py            # CLI entry point
├── requirements.txt
├── README.md
└── 3 Garage Scheduling.txt   # problem statement
```
