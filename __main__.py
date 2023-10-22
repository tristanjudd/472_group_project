from __future__ import annotations
import argparse
from game import Game, GameType, Options

def main():
    default_options = Options()
    # parse command line arguments
    parser = argparse.ArgumentParser(
        prog='ai_wargame',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--max_depth', type=int, default=default_options.max_depth, help='maximum search depth')
    parser.add_argument('--max_time', type=float, default=default_options.max_time, help='maximum search time')
    parser.add_argument('--max_turns', type=float, default=default_options.max_turns, help='maximum number of turns to end the game')
    parser.add_argument('--game_type', type=str, default="manual", help='game type: auto|attacker|defender|manual')
    parser.add_argument('--broker', type=str, help='play via a game broker')
    args = parser.parse_args()

    # parse the game type
    if args.game_type == "attacker":
        game_type = GameType.AttackerVsComp
    elif args.game_type == "defender":
        game_type = GameType.CompVsDefender
    elif args.game_type == "aiwar":
        game_type = GameType.CompVsComp
    else:
        game_type = GameType.AttackerVsDefender

    # set up game options
    options = Options(game_type=game_type)

    # override class defaults via command line options
    if args.max_depth is not None:
        options.max_depth = args.max_depth
    if args.max_time is not None:
        options.max_time = args.max_time
    if args.broker is not None:
        options.broker = args.broker
    if args.max_turns is not None:
        options.max_turns = args.max_turns

    # create a new game
    game = Game(options=options)
    game.start()


##############################################################################################################

if __name__ == '__main__':
    main()
