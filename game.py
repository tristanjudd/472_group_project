from __future__ import annotations
import logger
from enum import Enum
import copy
from datetime import datetime
from dataclasses import dataclass, field
from time import sleep
from typing import Tuple, TypeVar, Type, Iterable, ClassVar
import random
import requests
from player import Player
from coord import CoordPair, Coord
from unit import Unit, UnitType
from gameType import GameType

# maximum and minimum values for our heuristic scores (usually represents an end of game condition)
MAX_HEURISTIC_SCORE = 2000000000
MIN_HEURISTIC_SCORE = -2000000000

@dataclass()
class Options:
    """Representation of the game options."""
    dim: int = 5
    max_depth : int | None = 4
    min_depth : int | None = 2
    max_time : float | None = 5.0
    game_type : GameType = GameType.AttackerVsDefender
    alpha_beta : bool = True
    max_turns : int | None = 100
    randomize_moves : bool = True
    broker : str | None = None

##############################################################################################################

@dataclass()
class Stats:
    """Representation of the global game statistics."""
    evaluations_per_depth : dict[int,int] = field(default_factory=dict)
    total_seconds: float = 0.0


##############################################################################################################

@dataclass()
class Game:
    """Representation of the game state."""
    board: list[list[Unit | None]] = field(default_factory=list)
    next_player: Player = Player.Attacker
    turns_played : int = 0
    options: Options = field(default_factory=Options)
    stats: Stats = field(default_factory=Stats)
    _attacker_has_ai : bool = True
    _defender_has_ai : bool = True

    def __post_init__(self):
        """Automatically called after class init to set up the default board state."""
        dim = self.options.dim
        self.board = [[None for _ in range(dim)] for _ in range(dim)]
        md = dim-1
        self.set(Coord(0,0),Unit(player=Player.Defender,type=UnitType.AI))
        self.set(Coord(1,0),Unit(player=Player.Defender,type=UnitType.Tech))
        self.set(Coord(0,1),Unit(player=Player.Defender,type=UnitType.Tech))
        self.set(Coord(2,0),Unit(player=Player.Defender,type=UnitType.Firewall))
        self.set(Coord(0,2),Unit(player=Player.Defender,type=UnitType.Firewall))
        self.set(Coord(1,1),Unit(player=Player.Defender,type=UnitType.Program))
        self.set(Coord(md,md),Unit(player=Player.Attacker,type=UnitType.AI))
        self.set(Coord(md-1,md),Unit(player=Player.Attacker,type=UnitType.Virus))
        self.set(Coord(md,md-1),Unit(player=Player.Attacker,type=UnitType.Virus))
        self.set(Coord(md-2,md),Unit(player=Player.Attacker,type=UnitType.Program))
        self.set(Coord(md,md-2),Unit(player=Player.Attacker,type=UnitType.Program))
        self.set(Coord(md-1,md-1),Unit(player=Player.Attacker,type=UnitType.Firewall))

        self.logger = logger.Logger(self)


    def clone(self) -> Game:
        """Make a new copy of a game for minimax recursion.

        Shallow copy of everything except the board (options and stats are shared).
        """
        new = copy.copy(self)
        new.board = copy.deepcopy(self.board)

        # Tristan added this line
        new.next_player = copy.deepcopy(self.next_player)

        return new
    
    def start(self):
            # the main game loop
        while True:
            print()
            print(self)
            winner = self.has_winner()
            if winner is not None:
                print(f"{winner.name} wins!")
                self.logger.write_winner()
                break
            if self.options.game_type == GameType.AttackerVsDefender:
                self.human_turn()
            elif self.options.game_type == GameType.AttackerVsComp and self.next_player == Player.Attacker:
                self.human_turn()
            elif self.options.game_type == GameType.CompVsDefender and self.next_player == Player.Defender:
                self.human_turn()
            else:
                player = self.next_player
                move = self.computer_turn()
                if move is not None:
                    self.post_move_to_broker(move)
                else:
                    print("Computer doesn't know what to do!!!")
                    exit(1)
    
    def is_empty(self, coord : Coord) -> bool:
        """Check if contents of a board cell of the game at Coord is empty (must be valid coord)."""
        return self.board[coord.row][coord.col] is None

    def get(self, coord : Coord) -> Unit | None:
        """Get contents of a board cell of the game at Coord."""
        if self.is_valid_coord(coord):
            return self.board[coord.row][coord.col]
        else:
            return None

    def set(self, coord : Coord, unit : Unit | None):
        """Set contents of a board cell of the game at Coord."""
        if self.is_valid_coord(coord):
            self.board[coord.row][coord.col] = unit

    def remove_dead(self, coord: Coord):
        """Remove unit at Coord if dead."""
        unit = self.get(coord)
        if unit is not None and not unit.is_alive():
            self.set(coord,None)
            if unit.type == UnitType.AI:
                if unit.player == Player.Attacker:
                    self._attacker_has_ai = False
                else:
                    self._defender_has_ai = False

    def mod_health(self, coord : Coord, health_delta : int):
        """Modify health of unit at Coord (positive or negative delta)."""
        target = self.get(coord)
        if target is not None:
            target.mod_health(health_delta)
            self.remove_dead(coord)

    def is_valid_move(self, coords : CoordPair) -> bool:
        """Check that coords are within board dimensions"""
        if not self.is_valid_coord(coords.src) or not self.is_valid_coord(coords.dst):
            return False

        """Check that source coords are not empty and unit belongs to current player"""
        unit = self.get(coords.src)
        if unit is None or unit.player != self.next_player:
            return False

        # Begin Tristan code
        """Check that destination cell is source (self-destruct), up, right, down or left"""
        if coords.dst != coords.src and coords.dst not in coords.src.iter_adjacent():
            return False

        """If destination coords is empty, this is a move action"""
        # if self.get(coords.dst) is None:
        #     """If unit is an AI, Firewall or Program, it cannot move while engaged"""
        #     if unit.type in [UnitType.AI, UnitType.Firewall, UnitType.Program]:
        #         neighborhood = coords.src.iter_adjacent()
        #         """Check if unit is egnaged"""
        #         for n in neighborhood:
        #             n_unit = self.get(n)
        #             if n_unit is not None and n_unit.player != self.next_player:
        #                 print("This unit cannot move while engaged")
        #                 return False
        #End Tristan code

        return True

    def perform_move(self, coords : CoordPair) -> Tuple[bool,str]:
        """Validate and perform a move expressed as a CoordPair"""
        unit = self.get(coords.src)
        if self.is_valid_move(coords):
            self.logger.log_action(coords)
            """If destination is empty, this is a move action"""
            if self.get(coords.dst) is None:
                """Check whether unit can move while engaged"""
                unit = self.get(coords.src)
                if unit.type in [UnitType.AI, UnitType.Firewall, UnitType.Program]:
                    """If not, check whether engaged"""
                    neighborhood = coords.src.iter_adjacent()
                    for n in neighborhood:
                        n_unit = self.get(n)
                        if n_unit is not None and n_unit.player != self.next_player:
                            return (False, "This unit cannot move while engaged")

                # Check if unit is AI, Firewall or tech; their movement is restricted
                if unit.type in [UnitType.AI, UnitType.Firewall, UnitType.Program]:
                    if unit.player == Player.Attacker:
                        if coords.dst.row == coords.src.row and coords.dst.col == coords.src.col + 1:
                            return (False, "This unit can't move right")
                        elif coords.dst.row == coords.src.row + 1 and coords.dst.col == coords.src.col:
                            return (False, "This unit can't move down")
                    else:
                        if coords.dst.row == coords.src.row and coords.dst.col == coords.src.col - 1:
                            return (False, "This unit can't move left")
                        elif coords.dst.row == coords.src.row - 1 and coords.dst.col == coords.src.col:
                            return (False, "This unit can't move up")


                self.set(coords.dst,self.get(coords.src))
                self.set(coords.src,None)

                return (True, f"Moved {unit.type.name} unit from {coords.src} to {coords.dst}")

            else:
                # TODO: implement attack/repair/self-destruct logic here
                src_unit = self.get(coords.src)
                target_unit = self.get(coords.dst)

                """Self-destruct mode"""
                """Check if the target is same as the source """
                if src_unit == target_unit:
                    src_unit.health = 0
                    self.remove_dead(coords.src)
                    neighborhood = coords.src.iter_range(1)
                    total_damage = 0
                    for n in neighborhood:
                        n_unit = self.get(n)
                        if n_unit is not None:
                            n_unit.mod_health(-2)
                            total_damage += 2
                            if n_unit is not n_unit.is_alive():
                                self.remove_dead(n)
                    return True, f"{unit.type.name} Self-destructed at {coords.src} for {total_damage} total damage"

                """Repair-mode"""
                """Check if the target unit is friendly"""
                if src_unit.player.name == target_unit.player.name:
                    total_repair = 0
                    if src_unit.type in [UnitType.AI, UnitType.Tech]:
                        """Check the repair move if valid, throw error if the target unit health is above 9"""
                        if target_unit.health != 9:
                            amt = src_unit.repair_amount(target_unit)
                            if src_unit.type in [UnitType.AI] and target_unit.type in [UnitType.Virus, UnitType.Tech]:
                                target_unit.mod_health(amt)
                                total_repair += amt
                            elif src_unit.type in [UnitType.Tech] and target_unit.type in [UnitType.Firewall,
                                                                                           UnitType.AI,
                                                                                           UnitType.Program]:
                                target_unit.mod_health(amt)
                                total_repair += amt
                            else:
                                return False, f"Invalid move! {target_unit.type.name} can not be repaired by {src_unit.type}"
                        else:
                            return False, "Invalid move! Can not be repaired when health is full"
                    else:
                        return False, f"Invalid move! {src_unit.type.name} can not repair"

                    return True, (f"{src_unit.type.name} Repaired from {coords.src} to {coords.dst} repaired {total_repair}"
                                  f" health points")

                else:
                    """Attack mode"""
                    trgt_damage_amt = src_unit.damage_amount(target_unit)
                    src_damage_amt = target_unit.damage_amount(src_unit)

                    src_unit.mod_health(-src_damage_amt)
                    target_unit.mod_health(-trgt_damage_amt)
                    if src_unit is not src_unit.is_alive():
                        self.remove_dead(coords.src)

                    if target_unit is not target_unit.is_alive():
                        self.remove_dead(coords.dst)

                    return True, (f"{unit.type.name} Attacked from {coords.src} to {coords.dst} \n"
                                  f"Combat Damage: to source = {src_damage_amt}, to target = {trgt_damage_amt} ")

        else:
            return False,"Invalid move!"

    def next_turn(self):
        """Transitions game to the next turn."""
        self.next_player = self.next_player.next()
        self.turns_played += 1

    def to_string(self) -> str:
        """Pretty text representation of the game."""
        output = ""
        output += f"Next player: {self.next_player.name}\n"
        output += f"Turns played: {self.turns_played}\n"
        return output + self.board_to_string()
    
    def board_to_string(self) -> str:
        dim = self.options.dim
        coord = Coord()
        output = "\n   "
        for col in range(dim):
            coord.col = col
            label = coord.col_string()
            output += f"{label:^3} "
        output += "\n"
        for row in range(dim):
            coord.row = row
            label = coord.row_string()
            output += f"{label}: "
            for col in range(dim):
                coord.col = col
                unit = self.get(coord)
                if unit is None:
                    output += " .  "
                else:
                    output += f"{str(unit):^3} "
            output += "\n"
        return output

    def __str__(self) -> str:
        """Default string representation of a game."""
        return self.to_string()
    
    def is_valid_coord(self, coord: Coord) -> bool:
        """Check if a Coord is valid within out board dimensions."""
        dim = self.options.dim
        if coord.row < 0 or coord.row >= dim or coord.col < 0 or coord.col >= dim:
            return False
        return True

    def read_move(self) -> CoordPair:
        """Read a move from keyboard and return as a CoordPair."""
        while True:
            s = input(F'Player {self.next_player.name}, enter your move: ')
            coords = CoordPair.from_string(s)
            if coords is not None and self.is_valid_coord(coords.src) and self.is_valid_coord(coords.dst):
                return coords
            else:
                print('Invalid coordinates! Try again.')
    
    def human_turn(self):
        """Human player plays a move (or get via broker)."""
        if self.options.broker is not None:
            print("Getting next move with auto-retry from game broker...")
            while True:
                mv = self.get_move_from_broker()
                if mv is not None:
                    (success,result) = self.perform_move(mv)
                    print(f"Broker {self.next_player.name}: ",end='')
                    print(result)
                    if success:
                        self.next_turn()
                        break
                sleep(0.1)
        else:
            # SHORTCUT
            # minimax returns the best move
            best_move = self.minimax_helper()
            print(f"best move: {best_move}")

            # END SHORTCUT

            while True:
                mv = self.read_move()
                (success,result) = self.perform_move(mv)
                if success:
                    print(f"Player {self.next_player.name}: ",end='')
                    print(result)
                    self.next_turn()
                    break
                else:
                    if result is not None and result != "":
                        print(result)
                    else:
                        print("The move is not valid! Try again.")

    def computer_turn(self) -> CoordPair | None:
        """Computer plays a move."""
        mv = self.suggest_move()
        if mv is not None:
            (success,result) = self.perform_move(mv)
            #TODO Log additional information (3.1 and 3.2)
            if success:
                print(f"Computer {self.next_player.name}: ",end='')
                print(result)
                self.next_turn()
        return mv

    def player_units(self, player: Player) -> Iterable[Tuple[Coord,Unit]]:
        """Iterates over all units belonging to a player."""
        for coord in CoordPair.from_dim(self.options.dim).iter_rectangle():
            unit = self.get(coord)
            if unit is not None and unit.player == player:
                yield (coord,unit)

    def is_finished(self) -> bool:
        """Check if the game is over."""
        return self.has_winner() is not None

    def has_winner(self) -> Player | None:
        """Check if the game is over and returns winner"""
        if self.options.max_turns is not None and self.turns_played >= self.options.max_turns:
            return Player.Defender
        elif self._attacker_has_ai:
            if self._defender_has_ai:
                return None
            else:
                return Player.Attacker    
        elif self._defender_has_ai:
            return Player.Defender

    def move_candidates(self) -> Iterable[CoordPair]:
        """Generate valid move candidates for the next player."""
        move = CoordPair()
        for (src,_) in self.player_units(self.next_player):
            move.src = src
            for dst in src.iter_adjacent():
                move.dst = dst
                if self.is_valid_move(move):
                    yield move.clone()
            move.dst = src
            yield move.clone()

    def minimax_helper(self) -> CoordPair:
        # clone game
        game_clone = self.clone()
        # starting depth
        depth = 0
        # k for testing purposes, will be parameterized later
        k = 14

        max_move = None, None

        # perform recursive minimax on all possible moves on given moves
        for move in self.move_candidates():
            # call recursive minimax on all subsequent moves of this move
            h_val, move = self.minmax(depth=depth+1, k=k, game_clone=game_clone, move=move,
                                      board=copy.deepcopy(self.board))
            # take max heuristic value and set node to it

            if h_val is None:
                continue
            elif max_move[0] is None:
                max_move = h_val, move
            elif h_val > max_move[0]:
                max_move = h_val, move

        return max_move[1]

    def minmax(self, depth: int, k: int, game_clone: Game, move: CoordPair, board: list[list[Unit | None]]) \
            -> (int, CoordPair) or (None, None):
        # reset game board to correct state
        game_clone.board = board
        # store current player
        current_player = copy.deepcopy(game_clone.next_player)
        # store current turns
        current_turns = game_clone.turns_played

        # check if move is valid
        is_valid, msg = game_clone.perform_move(move)
        # if not, dead branch
        if not is_valid:
            return None, None

        print('valid move')

        # and store copy of board
        next_board = copy.deepcopy(game_clone.board)

        # if we've reached max depth or game is over, return heuristic value
        if depth == k or game_clone.has_winner():
            h = game_clone.e_0(self.next_player)
            return h, move

        # if not max depth and no winner run recursive call on all possible moves
        best_move = None

        for coords in game_clone.move_candidates():
            print('inside minmax for coords')
            # set player to next
            game_clone.next_player = current_player.next()
            # get heuristic value of move
            h_val, _ = self.minmax(depth=depth+1, k=k, game_clone=game_clone, move=coords,
                                      board=copy.deepcopy(next_board))

            if h_val is None:
                continue
            elif best_move is None:
                best_move = h_val
            elif self.next_player == current_player and h_val > best_move:
                best_move = h_val
            elif self.next_player != current_player and h_val < best_move:
                best_move = h_val

        return best_move, move

    def e_0(self, player1: Player) -> int:
        """Heuristic function from handout"""
        h_val = 0

        for _, unit in self.player_units(player1):

            u_type = unit.type

            if u_type == UnitType.AI:
                h_val += 9999
            else:
                h_val += 3

        for _, unit in self.player_units(player1.next()):
            u_type = unit.type

            if u_type == UnitType.AI:
                h_val -= 9999
            else:
                h_val -= 3

        return h_val

    def e_1(self) -> int:
        """Heuristic function from handout"""
        h_val = 0

        for _, unit in self.player_units(self.next_player):

            u_type = unit.type
            u_health = unit.health

            if u_type == UnitType.AI:
                h_val += 9999 * u_health
            else:
                h_val += 3 * u_health

        for _, unit in self.player_units(self.next_player.next()):
            u_type = unit.type
            u_health = unit.health

            if u_type == UnitType.AI:
                h_val -= 9999 * u_health
            else:
                h_val -= 3 * u_health

        return h_val

    def e_2(self) -> int:
        """Heuristic function from handout"""
        h_val = 0

        for _, unit in self.player_units(self.next_player):

            u_type = unit.type

            if u_type == UnitType.AI:
                h_val += 9999
            elif u_type in [UnitType.Virus, UnitType.Tech, UnitType.Program]:
                h_val += 9
            else:
                h_val += 3

        for _, unit in self.player_units(self.next_player.next()):
            u_type = unit.type
            u_health = unit.health

            if u_type == UnitType.AI:
                h_val -= 9999
            elif u_type in [UnitType.Virus, UnitType.Tech, UnitType.Program]:
                h_val -= 9
            else:
                h_val -= 3

        return h_val

    def random_move(self) -> Tuple[int, CoordPair | None, float]:
        """Returns a random move."""
        move_candidates = list(self.move_candidates())
        random.shuffle(move_candidates)
        if len(move_candidates) > 0:
            return (0, move_candidates[0], 1)
        else:
            return (0, None, 0)

    def suggest_move(self) -> CoordPair | None:
        """Suggest the next move using minimax alpha beta. TODO: REPLACE RANDOM_MOVE WITH PROPER GAME LOGIC!!!"""
        start_time = datetime.now()
        (score, move, avg_depth) = self.random_move()
        elapsed_seconds = (datetime.now() - start_time).total_seconds()
        self.stats.total_seconds += elapsed_seconds
        print(f"Heuristic score: {score}")
        print(f"Average recursive depth: {avg_depth:0.1f}")
        print(f"Evals per depth: ",end='')
        for k in sorted(self.stats.evaluations_per_depth.keys()):
            print(f"{k}:{self.stats.evaluations_per_depth[k]} ",end='')
        print()
        total_evals = sum(self.stats.evaluations_per_depth.values())
        if self.stats.total_seconds > 0:
            print(f"Eval perf.: {total_evals/self.stats.total_seconds/1000:0.1f}k/s")
        print(f"Elapsed time: {elapsed_seconds:0.1f}s")
        return move

    def post_move_to_broker(self, move: CoordPair):
        """Send a move to the game broker."""
        if self.options.broker is None:
            return
        data = {
            "from": {"row": move.src.row, "col": move.src.col},
            "to": {"row": move.dst.row, "col": move.dst.col},
            "turn": self.turns_played
        }
        try:
            r = requests.post(self.options.broker, json=data)
            if r.status_code == 200 and r.json()['success'] and r.json()['data'] == data:
                # print(f"Sent move to broker: {move}")
                pass
            else:
                print(f"Broker error: status code: {r.status_code}, response: {r.json()}")
        except Exception as error:
            print(f"Broker error: {error}")

    def get_move_from_broker(self) -> CoordPair | None:
        """Get a move from the game broker."""
        if self.options.broker is None:
            return None
        headers = {'Accept': 'application/json'}
        try:
            r = requests.get(self.options.broker, headers=headers)
            if r.status_code == 200 and r.json()['success']:
                data = r.json()['data']
                if data is not None:
                    if data['turn'] == self.turns_played+1:
                        move = CoordPair(
                            Coord(data['from']['row'],data['from']['col']),
                            Coord(data['to']['row'],data['to']['col'])
                        )
                        print(f"Got move from broker: {move}")
                        return move
                    else:
                        # print("Got broker data for wrong turn.")
                        # print(f"Wanted {self.turns_played+1}, got {data['turn']}")
                        pass
                else:
                    # print("Got no data from broker")
                    pass
            else:
                print(f"Broker error: status code: {r.status_code}, response: {r.json()}")
        except Exception as error:
            print(f"Broker error: {error}")
        return None
