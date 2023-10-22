
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime

@dataclass()
class Stats:
    """Representation of the global game statistics."""
    evaluations_per_depth : dict[int,int] = field(default_factory=dict)
    total_seconds: float = 0.0

class MinimaxStatCollector:
  start_time: datetime
  max_time: datetime
  PERCENTAGE_THRESHOLD = 90

  def __init__(self, max_time: float):
    self.start_time = datetime.now()
    self.max_time = max_time * self.PERCENTAGE_THRESHOLD / 100
  
  def minimax_should_return(self):
    time_elapsed = (datetime.now() - self.start_time).total_seconds()
    return time_elapsed >= self.max_time