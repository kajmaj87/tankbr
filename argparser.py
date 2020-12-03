import configargparse

p = configargparse.ArgParser(default_config_files=['config'])
p.add('-c', '--config', is_config_file=True, help='config file path with defaults')
p.add('-r', '--rounds', type=int, help='how many full rounds to generate. round means (players/match_size) matches')
p.add('--match_size', type=int, help='how many players should take part in one match')
p.add('--players', type=int, help='how many players to genarate')
p.add('--include_human_player', type=bool, help='true to allow human player to play')
p.add('--random_seed', help='random seed to use, pass `disabled` to turn off using seed')

p.add('--gui_draw', action='store_true', help='pass this argument to draw the game')
p.add('--gui_max_fps', type=int)
p.add('--gui_resolution', action="append", type=int, help='you need to pass this argument twice from command line first specifying x value then y. Better use config file for this')
p.add('--gui_zoom', type=float, help='zoom factor at start of game. You can use mousescroll to change zoom during the game.', default=1)
p.add('--gui_zoom_change_factor', type=float, help='determines how fast zoom changes when scrolling')
p.add('--gui_offset_x', type=float, help='how much viewport should be offset horizontally when starting the game')
p.add('--gui_offset_y', type=float, help='how much viewport should be offset vertically when starting the game')

config = p.parse_args()

print(config)
print("----------")
print(p.format_help())
print("----------")
print(p.format_values())
