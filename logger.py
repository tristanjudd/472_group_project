from io import TextIOWrapper
import game as GameModule
from coord import CoordPair
from player import Player


class Logger:
    output_file: TextIOWrapper
    game: GameModule.Game

    def __init__(self, game: GameModule.Game):
        self.game = game
        self.setup_output_file()
        self.log_game_parameters()

        self.log_nl()
        self.log_nl()
        self.log_nl("INITIAL CONFIGURATION")
        self.log_nl(game.board_to_string())
        self.log_nl()
        
    
    def __del__(self):
        self.output_file.close()

    def log_game_parameters(self):
        options = self.game.options
        is_alpha_beta = str(options.alpha_beta).lower()
        max_time = str(options.max_time)
        max_turns = str(options.max_turns)

        self.log_nl("GAME PARAMETERS")
        self.log_nl(f'Timeout Value: {max_time} seconds')
        if options.alpha_beta:
            self.log_nl(f' (alpha-beta={is_alpha_beta})')
            
        #TODO Real heuristic values
        if options.game_type == GameModule.GameType.AttackerVsComp or options.game_type == GameModule.GameType.AttackerVsDefender:
            self.log_nl("Player 1 is a Human")
        else:
            heuristic = "e0"
            self.log_nl(f'Player 1 is an AI with heuristic {heuristic}')

        if options.game_type == GameModule.GameType.AttackerVsDefender or options.game_type == GameModule.GameType.CompVsDefender:
            self.log_nl("Player 2 is a Human")
        else:
            heuristic = "e0"
            self.log_nl(f'Player 2 is an AI with heuristic {heuristic}')

    def setup_output_file(self):
        options = self.game.options
        is_alpha_beta = str(options.alpha_beta).lower()
        max_time = str(options.max_time)
        max_turns = str(options.max_turns)
        
        self.output_file = open(f'GameModuleTrace-{is_alpha_beta}-{max_time}-{max_turns}.txt', "w")

    def log_nl(self, str: str = ""):
        self.output_file.write(f'{str}\n')

    def log_action(self, move: CoordPair):
        self.log_nl()
        self.log_nl(f'Turn # {self.game.turns_played + 1}')
        self.log_nl(f'Current Player: {self.game.next_player}')
        self.log_nl(f'Moved from {move.src} to {move.dst}')
        self.log_nl(self.game.board_to_string())
    
    def write_winner(self, winner: str, turns: int):
        self.log_nl(f'{winner} wins in {turns} turns')

