from __future__ import annotations
from game import CoordPair
from collections.abc import Callable
from board import Board
from player import Player
from unit import UnitType
import sys


##############################################################################################################

# Heuristics
def e0(board: Board) -> int:
  h_val = 0
  
  for _, unit in board.player_units(Player.get_max_player()):
      if unit.type == UnitType.AI:
          h_val += 9999
      else:
          h_val += 3

  for _, unit in board.player_units(Player.get_min_player()):
      if unit.type == UnitType.AI:
          h_val -= 9999
      else:
          h_val -= 3

  return h_val

##############################################################################################################



def suggest_move():
  return

def better_move(is_max: bool, original_score: int, new_score: int) -> bool:
  if is_max:
    return new_score > original_score
  else:
    return new_score < original_score



def minimax(board: Board, is_max: bool, move: CoordPair, e: Callable[[Board], int], depth: int, MAX_DEPTH: int) -> int:
  if depth == MAX_DEPTH:
    return e(board)

  # score
  best_score = None
  
  current_player = Player.get_max_player() if is_max else Player.get_min_player()

  for c_move in board.move_candidates(current_player):
    c_board = board.clone_and_move(c_move, current_player)

    if c_board is None:
      continue
    
    c_score = minimax(c_board, not is_max, c_move, e, depth + 1, MAX_DEPTH)

    if c_score is None:
       print(c_board.to_string())

    if best_score is None or better_move(is_max, best_score, c_score):
      best_score = c_score
  
  if best_score is None:
     return sys.maxsize if is_max else -1 * sys.maxsize
  else:
    return best_score

