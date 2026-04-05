# Garage Scheduling with Probabilistic Task Generation and Fatigue Constraints

**Project:** Problem 3 — Garage Scheduling  
**Companion code:** `garage_project/` (Python)

This document is a standalone project report. For installation and execution, see `README.md`.

---

## Executive summary

| Topic | Summary |
|--------|---------|
| **Problem statement** | Schedule \(M\) mechanics to service multiple cars; each car type follows a task DAG with unit-duration tasks; edges carry probabilities that a completed task *may* spawn a mandatory follow-up; mechanics need a 1-unit break after every \(k\) consecutive tasks. |
| **Assumptions** | Unit tasks; discrete time; independent uniform draws for edges; one DAG per car type; cars identified by instances with fixed type; “initial schedule” excludes tasks that are not yet known to exist (non-root nodes). |
| **Optimization criteria** | Primary: minimize **makespan** (time horizon until all *scheduled* work finishes) under precedence and fatigue. Initial phase uses a greedy list-scheduling heuristic; dynamic inserts use the same rule. |
| **Methodology** | Topological structure from DAGs; list scheduling (earliest-feasible mechanic); simulation loop with per-edge Bernoulli-style trials; **deferred placement** for tasks with multiple predecessors until all predecessors finish. |
| **Results** | With default configuration (`M=3`, `k=3`, fixed seed `42`), one reproducible run yields initial makespan 2, final makespan 6, nine dynamic spawn events logged, plus PNG Gantt/DAG figures (all depend on seed and config). |
| **Future scope** | Exact/stochastic optimization, re-optimization on inserts, multi-objective (fairness, tardiness), learning edge probabilities, and richer break policies. |

---

## 1. Introduction

Garage operations combine **precedence constraints** (some jobs must finish before others), **parallel resources** (several mechanics), and **uncertainty** (inspection may reveal extra work). The problem statement frames this as **live scheduling**: build a reasonable first plan, then **revise** the plan whenever new mandatory tasks appear, while protecting workers through **mandatory rest** after bursts of work.

This report presents a mathematical reading of that problem, documents modeling assumptions, describes the algorithms implemented in software, reports illustrative numerical outcomes, and outlines extensions for research and practice.

---

## 2. Existing literature (context)

The problem connects to several classical areas (without claiming this implementation implements any specific commercial solver):

- **Parallel machine scheduling:** \(P \mid \text{prec} \mid C_{\max}\) and variants ask for minimum makespan with precedence; most formulations are NP-hard, so **greedy heuristics** (e.g. list scheduling, longest-processing-time rules) are standard approximations.
- **Job shop / project scheduling:** Task graphs (often DAGs) appear in project management (CPM/PERT); **probabilistic** versions study duration or structure uncertainty; here uncertainty is **structural** (which extra tasks exist), closer to stochastic combinatorial scheduling.
- **Online and dynamic scheduling:** When jobs arrive over time, policies balance immediate assignment vs. reserve capacity; this project’s “new task after completion” is a simplified **dynamic job arrival** model.
- **Human factors / breaks:** Restrictions on consecutive work relate to **staffing and labor rules**; modeling them as fixed mandatory idle time is a common discrete-time abstraction.

The implementation follows a **transparent heuristic** (list scheduling + simulation) suitable for coursework and prototyping rather than industrial optimality guarantees.

---

## 3. Objectives of this work

1. **Formalize** the garage problem: inputs, constraints, stochastic rule for new tasks, and notion of “initial” vs. “updated” schedules.
2. **Implement** a working scheduler that:
   - builds an initial assignment ignoring unknown probabilistic follow-ups (in the sense of not scheduling tasks that have not yet been generated);
   - simulates edge outcomes using the problem’s sampling rule;
   - inserts new tasks while respecting **DAG precedence** and **fatigue breaks**;
   - handles tasks with **multiple predecessors** without starting them too early.
3. **Measure** makespan and qualitative behaviour via console logs and Gantt charts.
4. **Document** limitations and meaningful **future work**.

---

## 4. Mathematical description of the problem statement

### 4.1 Sets and indices

- Mechanics: \(m \in \{1,\ldots,M\}\).
- Car instances: \(c = 1,\ldots,C\); each car \(c\) has a type \(\tau(c) \in \{1,\ldots,N\}\).
- For each car type \(n\), a directed acyclic graph \(G_n = (V_n, E_n)\):
  - Nodes \(u \in V_n\) are task names (unit work).
  - Each edge \((u,v) \in E_n\) has weight \(p_{uv} \in [0,1]\), interpreted as a **threshold parameter** for the official sampling rule (Section 4.4).

Roots \(R_n = \{ u \in V_n : \text{in-degree}(u) = 0 \}\) are tasks with no predecessors.

### 4.2 Time and task duration

Time is discrete: \(t \in \{0,1,2,\ldots\}\). Each task occupies **exactly one** time unit. If task \(j\) starts at \(S_j\), it finishes at \(F_j = S_j + 1\).

Breaks are special idle intervals of length 1 on a mechanic’s timeline.

### 4.3 Fatigue (mandatory breaks)

For each mechanic, let a **work streak** count consecutive **non-break** assignments. After completing \(k\) consecutive tasks, the mechanic must take **one** break of length 1 before starting the next task. Breaks do not count toward the streak; after a break, the streak resets (implementation detail: streak is reset when the break is inserted).

### 4.4 Probabilistic task generation (problem text)

When a task \(u\) **completes** on car \(c\), for each outgoing edge \((u,v)\) in \(G_{\tau(c)}\):

1. Draw \(R \sim \mathrm{Uniform}(0,1)\).
2. If \(R > p_{uv}\), then task \(v\) is **generated** for car \(c\) and must eventually be executed (if not already present).

**Interpretation note:** Larger \(p_{uv}\) makes generation **less** likely under this rule. This matches the literal statement “if the number is **higher** than probability … then the task is generated.”

### 4.5 DAG semantics for generated tasks

If a task \(v\) has several predecessors in \(G_n\), it **cannot start** until **every** predecessor task of \(v\) for that same car instance has **finished** (whether those predecessors were scheduled initially or appeared earlier in the simulation). If \(v\) is generated when only a subset of predecessors has finished, its **placement** in the schedule must still respect:

\[
S_v \geq \max_{u:(u,v)\in E_n} F_u
\]

where the maximum is over predecessor tasks \(u\) that belong to the same car instance and have completed.

### 4.6 Objectives (optimization criteria)

- **Primary (implemented):** Minimize **makespan**  
  \[
  C_{\max} = \max_j F_j
  \]
  over all scheduled tasks and breaks, subject to: each task on at most one mechanic at a time; precedence; fatigue breaks; and release times implied by predecessor completion.

- **“Optimal” in the problem wording:** The codebase uses a **greedy list-scheduling heuristic**, not an exact optimizer. Thus “optimal” should be read as **heuristic / best-effort** under the chosen rule unless extended with MILP, CP-SAT, or other search.

### 4.7 Assumptions made (explicit)

1. **Unit tasks:** All tasks and breaks last exactly one time unit.
2. **No preemption:** Once started, a task runs to completion (same timestep as duration 1).
3. **Independent draws:** Random outcomes on different edges and events are independent (iid uniform).
4. **One graph per car type:** All cars of the same type share the same DAG template; instances differ by car index \(c\).
5. **Initial schedule:** Only **root** tasks are scheduled before simulation; non-root tasks enter only after generation. This matches “disregarding probabilistic tasks” as *tasks not yet known to exist*.
6. **Mechanics are identical:** No skill speeds or eligibility differences.
7. **No travel/setup:** Switching cars has no extra cost beyond timeline packing and breaks.
8. **Dynamic insertion policy:** New tasks are appended via the same greedy mechanic choice; **full global reschedule** (reordering all future work) is not performed.

---

## 5. Description of algorithms used

### 5.1 Initial scheduling

**Input:** List of cars with types; \(M\) mechanics; DAGs \(G_n\).

**Step A:** For each car instance \(c\), for each root task \(u \in R_{\tau(c)}\), create a pending job with earliest start time 0 (or more generally, the release time if roots had releases).

**Step B (list scheduling):** For each pending job with earliest start time \(r\), assign it to the mechanic \(m\) that minimizes \(\max(\text{free}_m, r)\), where \(\text{free}_m\) is the earliest time at which mechanic \(m\) can start the next activity after accounting for already placed tasks and mandatory breaks.

**Step C (fatigue state):** When assigning a real task, if the mechanic’s consecutive task count has reached \(k\), insert a break of length 1 first, then assign the task.

This is a variant of **greedy list scheduling** on parallel machines with **release times** \(r\) and **per-machine idle rules** (breaks).

### 5.2 Simulation of probabilistic structure

**Per-edge processing:** When a scheduled task \(u\) finishes for car \(c\), each outgoing edge \((u,v)\) is evaluated **at most once** in the simulation pass: draw \(R\); if \(R > p_{uv}\), mark \(v\) as **generated** for car \(c\).

**Generation vs. scheduling:** A task may be generated as soon as **any** incoming edge succeeds (under multiple parents, several edges may be rolled as different parents complete). The task is **eligible for scheduling** only when **all** predecessors for that car have finished.

**Iterative closure:** The simulation repeats passes until no new scheduling actions occur: new completions enable new edge rolls; new generations become schedulable when precedences are satisfied.

### 5.3 Novel or distinguishing contributions (in this codebase)

Relative to a minimal “spawn and greedily append” prototype, the implementation emphasizes:

1. **Correct multi-predecessor handling:** Generated tasks with several predecessors are **not** scheduled at the first parent’s finish time; earliest start is the **maximum** of predecessor finish times, and scheduling is **deferred** until all predecessors have completed.
2. **Per-edge simulation bookkeeping:** Uses processed edge keys \((c,u,v)\) so each stochastic edge is resolved once when \(u\) completes, avoiding duplicate rolls from revisiting the same completion.
3. **Fatigue as part of assignment:** Break insertion is integrated into the mechanic’s `assign_task` pipeline so list scheduling sees realistic availability times.

### 5.4 Visualization

- **Gantt chart:** Per-mechanic bars for tasks and breaks.
- **DAG plots:** Nodes and edges with probability labels; layout uses Graphviz if available, else a spring layout.

---

## 6. Results obtained

Results depend on **configuration** (`GarageConfig` in `config.py`: \(M\), \(k\), car list, DAGs, random seed).

**Default demo settings (illustrative):** `num_mechanics = 3`, `consecutive_limit = 3`, `random_seed = 42`, five cars with mixed types.

**Sample observed metrics (one run, reproducible with seed 42):**

| Metric | Value (example) |
|--------|------------------|
| Initial makespan | 2 time units |
| Final makespan | 6 time units (horizon of last finishing activity in that run) |
| Reported dynamic task events | 9 |
| Outputs | Console schedule and event log; `garage_gantt.png`; `garage_dag_type*.png` |

**Interpretation:** The initial makespan is small because only **one root task per car** is placed at time 0 across three mechanics. The final makespan grows as probabilistic chains unfold and breaks insert idle time. Different seeds or probabilities change both the **number** of dynamic tasks and the **final makespan**.

**Limitation:** No exhaustive benchmark against optimal lower bounds is included; results demonstrate **behaviour** of the heuristic and **correctness** of precedence/break logic rather than optimality gaps.

---

## 7. Conclusion

The garage problem combines **parallel scheduling**, **DAG precedences**, **structural randomness** on edges, and **workload safeguards** for mechanics. The implemented solution provides a clear pipeline: **roots first**, **simulate** stochastic edge outcomes, **insert** work with list scheduling while respecting **latest necessary start** from all predecessors and **mandatory breaks**. The approach is easy to explain and visualize, suitable for education and prototyping.

The main trade-off is **solution quality:** greedy list scheduling is fast and interpretable but not guaranteed to minimize makespan, especially after many dynamic insertions.

---

## 8. Future work

1. **Exact or bounded optimality:** Formulate mixed-integer or constraint programming models for small instances; compare heuristic makespan to optimal or branch-and-bound bounds.
2. **Stochastic optimization:** Optimize expected makespan or a risk measure (e.g. percentile) using scenario trees or sample-average approximation, instead of a single sampled trajectory.
3. **Global rescheduling:** On each new task, re-optimize remaining unstarted work (rolling horizon) rather than only greedy insertion.
4. **Richer fatigue models:** Variable break length, cumulative fatigue, or per-mechanic limits; night shifts and calendar constraints.
5. **Multi-objective goals:** Balance makespan with fairness across mechanics, maximum lateness per car, or energy use.
6. **Learning:** Estimate edge probabilities \(p_{uv}\) from historical service data; active learning while scheduling.
7. **Scalability:** Faster data structures for very large garages; distributed or real-time integration with shop-floor systems.

---

## References (topics for further reading)

- Graham, R. L. Bounds on multiprocessing timing anomalies. *SIAM Journal on Applied Mathematics* (1966) — classic list scheduling motivation.  
- Pinedo, M. *Scheduling: Theory, Algorithms, and Systems* — parallel machines, precedence, heuristics.  
- Herroelen, W., Leus, R. Project scheduling under uncertainty: survey. *European Journal of Operational Research* (2005) — stochastic project scheduling context.

*(Full bibliographic details should be verified in the user’s target style guide.)*

---

*End of report.*
