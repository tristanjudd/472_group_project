from __future__ import annotations
from typing import Iterable, Tuple
from player import Player
from unit import Unit, UnitType
from coord import CoordPair, Coord
from copy import deepcopy


# for (src,_) in self.player_units(self.next_player):
class Board:
    grid: list[list[Unit | None]]

    def __init__(self, grid: list[list[Unit | None]] | None = None):
        dim = 5
        self.dim = dim
        if grid is None:
            self.grid = [[None for _ in range(dim)] for _ in range(dim)]
        else:
            self.grid = grid

    def perform_move(self, coords: CoordPair, player: Player) -> Tuple[bool, str]:
        """Validate and perform a move expressed as a CoordPair"""
        unit = self.get(coords.src)
        if self.is_moveable(coords, player):
            # self.logger.log_action(coords)
            """If destination is empty, this is a move action"""
            if self.get(coords.dst) is None:
                """Check whether unit can move while engaged"""
                unit = self.get(coords.src)
                if unit.type in [UnitType.AI, UnitType.Firewall, UnitType.Program]:
                    """If not, check whether engaged"""
                    neighborhood = coords.src.iter_adjacent()
                    for n in neighborhood:
                        n_unit = self.get(n)
                        # if n_unit is not None and n_unit.player != self.next_player:
                        if n_unit is not None and n_unit.player != player:
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

                self.set(coords.dst, self.get(coords.src))
                self.set(coords.src, None)

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

                    return True, (
                        f"{src_unit.type.name} Repaired from {coords.src} to {coords.dst} repaired {total_repair}"
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
            return False, "Invalid move!"

    def is_empty(self, coord: Coord) -> bool:
        """Check if contents of a board cell of the game at Coord is empty (must be valid coord)."""
        return self.grid[coord.row][coord.col] is None

    def remove_dead(self, coord: Coord):
        """Remove unit at Coord if dead."""
        unit = self.get(coord)
        if unit is not None and not unit.is_alive():
            self.set(coord, None)
            if unit.type == UnitType.AI:
                if unit.player == Player.Attacker:
                    self._attacker_has_ai = False
                else:
                    self._defender_has_ai = False

    def mod_health(self, coord: Coord, health_delta: int):
        """Modify health of unit at Coord (positive or negative delta)."""
        target = self.get(coord)
        if target is not None:
            target.mod_health(health_delta)
            self.remove_dead(coord)

    def set(self, coord: Coord, unit: Unit | None):
        """Set contents of a board cell of the game at Coord."""
        if self.is_valid_coord(coord):
            self.grid[coord.row][coord.col] = unit

    def get_dim(self):
        return self.dim

    def move_candidates(self, player: Player) -> Iterable[CoordPair]:
        """Generate valid move candidates for the given player."""
        move = CoordPair()
        for (src, _) in self.player_units(player):
            move.src = src
            for dst in src.iter_adjacent():
                move.dst = dst
                if self.is_moveable(move, player):
                    yield move.clone()
            move.dst = src
            yield move.clone()

    def player_units(self, player: Player) -> Iterable[Tuple[Coord, Unit]]:
        """Iterates over all units belonging to a player."""
        for coord in CoordPair.from_dim(self.get_dim()).iter_rectangle():
            unit = self.get(coord)
            if unit is not None and unit.player == player:
                yield (coord, unit)

    def get(self, coord: Coord) -> Unit | None:
        """Get contents of a board cell of the game at Coord."""
        if self.is_valid_coord(coord):
            return self.grid[coord.row][coord.col]
        else:
            return None

    def is_valid_coord(self, coord: Coord) -> bool:
        """Check if a Coord is valid within out board dimensions."""
        dim = self.get_dim()
        if coord.row < 0 or coord.row >= dim or coord.col < 0 or coord.col >= dim:
            return False
        return True

    def is_moveable(self, coords: CoordPair, player: Player) -> bool:
        """Check that coords are within board dimensions"""
        if not self.is_valid_coord(coords.src) or not self.is_valid_coord(coords.dst):
            return False

        """Check that source coords are not empty and unit belongs to current player"""
        unit = self.get(coords.src)
        # if unit is None or unit.player != self.next_player:
        if unit is None or unit.player != player:
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
        # End Tristan code

        return True

    def to_string(self) -> str:
        dim = self.get_dim()
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

    ### Returns none if move invalid
    def clone_and_move(self, move: CoordPair, player: Player) -> Board:
        # TODO: clone current board and perform the given move on that board
        board = Board(deepcopy(self.grid))
        valid_move, _ = board.perform_move(move, player)
        if valid_move:
            return board
        else:
            return None


if __name__ == '__main__':
    board = Board()
    print(board.get_dim())
    print(board.to_string())
    first_coord = Coord.from_string("D3")
    second_coord = Coord.from_string("C3")
    pair = CoordPair(first_coord, second_coord)

    board.perform_move(pair, Player.Attacker)
    print(board.to_string())
