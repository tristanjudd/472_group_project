from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime


@dataclass()
class Stats:
    """Representation of the global game statistics."""
    evaluations_per_depth: dict[int, int] = field(default_factory=dict)
    total_seconds: float = 0.0
    branch_count: int = 0
    parent_count: int = 0

    def record_branching(self, branches:int):
        self.branch_count += branches
        self.parent_count += 1

    def get_branching_factor(self) -> float:
        return float(self.branch_count)/self.parent_count

    def record_evaluation(self, current_depth: int):
        """Record an evaluation at a specific depth."""
        if current_depth in self.evaluations_per_depth:
            self.evaluations_per_depth[current_depth] += 1
        else:
            self.evaluations_per_depth[current_depth] = 1

class MinimaxDepthManager:
    depth: float
    min: int
    max: int
    binary_search: bool
    start: int
    end: int

    POSITIVE_INCREMENT = 0.1

    def __init__(self, min: int, max: int) -> None:
        self.min = min
        self.max = max
        self.start = min
        self.end = max

        self.binary_search = True
        self.depth = max
    
    def get_depth(self) -> int:
        if self.binary_search:
            return int((self.start + self.end)/2)
        return int(self.depth)

    def notify(self, early_return: bool):
        self.binary_search = (self.start != self.end)
        mid = self.get_depth()

        if self.binary_search:
            if early_return:
                self.end = mid
            else:
                self.start = mid
            self.depth = self.get_depth()
        else:
            if early_return:
                self.depth -= 1
                self.depth = max(self.depth, self.min)
            else:
                self.depth += self.POSITIVE_INCREMENT
                self.depth = min(self.depth, self.max)
                

class MinimaxTimeManager:
    start_time: datetime
    max_time: datetime
    returned_early: bool
    PERCENTAGE_THRESHOLD = 95

    def __init__(self, max_time: float):
        self.start_time = datetime.now()
        self.max_time = max_time * self.PERCENTAGE_THRESHOLD / 100
        self.returned_early = False

    def minimax_should_return(self):
        time_elapsed = (datetime.now() - self.start_time).total_seconds()
        return_early = time_elapsed >= self.max_time
        self.returned_early = return_early
        return return_early

    def did_minimax_return_early(self) -> bool:
        return self.returned_early
