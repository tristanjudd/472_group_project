from __future__ import annotations
from enum import Enum

class Player(Enum):
    """The 2 players."""
    Attacker = 0
    Defender = 1

    def next(self) -> Player:
        """The next (other) player."""
        if self is Player.Attacker:
            return Player.Defender
        else:
            return Player.Attacker
        
    def to_string(self) -> str:
        if self is Player.Attacker:
            return "Attacker"
        else:
            return "Defender"