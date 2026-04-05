"""Default configuration parameters for the garage scheduling problem."""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class GarageConfig:
    """All configurable parameters for the garage problem."""

    # Number of mechanics
    num_mechanics: int = 3

    # Consecutive tasks before mandatory break
    consecutive_limit: int = 3   # k

    # Random seed
    random_seed: int = 42

    # Car DAG definitions.
    # Each entry: list of (from_task, to_task, probability) tuples.
    # A task with no incoming edges is a root task.
    # Per problem spec: task IS generated when random() > probability,
    # so lower probability values make follow-up tasks more likely.
    car_dags: List[List[Tuple[str, str, float]]] = field(default_factory=lambda: [
        # Car type 0 — sedan service
        [
            ("inspect",       "oil_change",    0.3),
            ("inspect",       "tyre_check",    0.4),
            ("oil_change",    "filter_change", 0.5),
            ("tyre_check",    "alignment",     0.6),
            ("filter_change", "road_test",     0.2),
            ("alignment",     "road_test",     0.2),
        ],
        # Car type 1 — SUV repair
        [
            ("diagnose",      "brake_check",   0.4),
            ("diagnose",      "engine_scan",   0.5),
            ("brake_check",   "brake_replace", 0.3),
            ("engine_scan",   "tune_up",       0.4),
            ("brake_replace", "final_check",   0.1),
            ("tune_up",       "final_check",   0.1),
        ],
        # Car type 2 — electric vehicle
        [
            ("battery_diag",  "software_upd",  0.35),
            ("battery_diag",  "charger_check", 0.45),
            ("software_upd",  "calibrate",     0.25),
            ("charger_check", "calibrate",     0.55),
            ("calibrate",     "sign_off",      0.15),
        ],
    ])

    # Cars to service: list of car-type indices
    cars: List[int] = field(default_factory=lambda: [0, 1, 2, 0, 1])


DEFAULT_CONFIG = GarageConfig()
