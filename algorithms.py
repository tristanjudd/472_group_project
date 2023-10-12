from __future__ import annotations
from player import Player
from dataclasses import field
from unit import Unit
from game import CoordPair
from typing import Iterable, Tuple
from collections.abc import Callable

##############################################################################################################

# Heuristics
def e0(board: Board) -> int:
  grid = board.grid
  heuristic = 0

  # TODO: iterate on the units in the grid and add or substract depending on the heuristic

  return heuristic

##############################################################################################################

class Board:
  grid: list[list[Unit | None]] = field(default_factory=list)

  def move_candidates(self) -> Iterable[CoordPair]: 
    return []
  
  def clone_and_move(self, move: CoordPair) -> Board:
    # TODO: clone current board and perform the given move on that board
    return None 

def suggest_move():
  return


def minimax(board: Board, is_max: bool, move: CoordPair, e: Callable[[Board], int], depth: int, MAX_DEPTH: int) -> Tuple[int, CoordPair | None, float]:
  if depth == MAX_DEPTH:
    return (e(board), move, depth)
  
  total_depth = depth

  # best move is a tuple/pair with:
  # (score, move)
  best_move = None
  moves = board.move_candidates()
  for c_move in moves:
    c_board = board.clone_and_move(move)
    (c_score, c_depth) = minimax(c_board, not is_max, c_move, e, depth + 1, MAX_DEPTH)
    
    # sum the depth of the children to eventually calculate avg depth (we might need to also keep track of the count. creating a separate observer object might be more useful)
    total_depth += c_depth
    
    # Code that compares this move's score with the previous best_move, taking into account if is_max is true or not
  
  return (best_move[0], best_move[1], total_depth)

