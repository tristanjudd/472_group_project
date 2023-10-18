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
    
    # Hard assignment on who's looking to minimize and maximize scores
    @staticmethod
    def is_max(self) -> bool:
        return self is self.get_max_player()
    
    @staticmethod
    def get_max_player() -> Player:
        return Player.Attacker
    
    @staticmethod
    def get_min_player() -> Player:
        return Player.get_max_player().next()
        
    def to_string(self) -> str:
        if self is Player.Attacker:
            return "Attacker"
        else:
            return "Defender"