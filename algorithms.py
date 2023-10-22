from __future__ import annotations
from collections.abc import Callable
from board import Board
from player import Player
from unit import UnitType
import sys
import game
from stats import Stats


##############################################################################################################

# Heuristics

# Heuristic function from handout
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


def e1(board: Board) -> int:
    h_val = 0

    for _, unit in board.player_units(Player.get_max_player()):
        u_health = unit.health

        if unit.type == UnitType.AI:
            h_val += 9999 * u_health
        else:
            h_val += 3 * u_health

    for _, unit in board.player_units(Player.get_min_player()):
        u_health = unit.health

        if unit.type == UnitType.AI:
            h_val -= 9999 * u_health
        else:
            h_val -= 3 * u_health

    return h_val


def e2(board: Board) -> int:
    h_val = 0

    for _, unit in board.player_units(Player.get_max_player()):
        u_type = unit.type

        if u_type == UnitType.AI:
            h_val += 9999
        elif u_type in [UnitType.Virus, UnitType.Tech, UnitType.Program]:
            h_val += 9
        else:
            h_val += 3

    for _, unit in board.player_units(Player.get_min_player()):
        u_type = unit.type
        u_health = unit.health

        if u_type == UnitType.AI:
            h_val -= 9999
        elif u_type in [UnitType.Virus, UnitType.Tech, UnitType.Program]:
            h_val -= 9
        else:
            h_val -= 3

    return h_val


##############################################################################################################

def suggest_move():
    return


def better_move(is_max: bool, original_score: int | None, new_score: int) -> bool:
    if original_score is None:
        return True

    if is_max:
        return new_score > original_score
    else:
        return new_score < original_score


def alpha_beta_minimax(board: Board, is_max: bool, e: Callable[[Board], int], depth: int, MAX_DEPTH: int, beta: int,
                       alpha: int, is_alpha_beta: bool, evaluate: Stats) -> int:
    evaluate.record_evaluation(depth)

    if depth == MAX_DEPTH:
        return e(board)

    # score
    best_score = None

    current_player = Player.get_max_player() if is_max else Player.get_min_player()

    for c_move in board.move_candidates(current_player):
        c_board = board.clone_and_move(c_move, current_player)

        # The move could not be performed
        if c_board is None:
            continue

        c_score = alpha_beta_minimax(c_board, not is_max, e, depth + 1, MAX_DEPTH, beta, alpha, is_alpha_beta, evaluate)

        if better_move(is_max, best_score, c_score):
            best_score = c_score

            # If we're running alpha beta minimax, then do alpha beta pruning
            if is_alpha_beta:
                if is_max:
                    alpha = max(alpha, best_score)
                else:
                    beta = min(beta, best_score)

                if beta <= alpha:
                    return best_score
        
        

    # If you cannot perform a move, you have no units and you lost
    if best_score is None:
        return game.MIN_HEURISTIC_SCORE if is_max else game.MAX_HEURISTIC_SCORE
    else:
        return best_score

def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])