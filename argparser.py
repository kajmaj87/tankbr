import configargparse

p = configargparse.ArgParser(default_config_files=['config'])
p.add('-c', '--config', is_config_file=True, help='config file path with defaults')
p.add('-r', '--rounds', type=int, help='how many full rounds to generate. round means (players/match_size) matches')
p.add('--match_size', type=int, help='how much players should take part in one match')
p.add('--players', type=int, help='how many players to genarate')
p.add('--include_human_player', type=bool, help='true to allow human player to play')
p.add('--random_seed', help='random seed to use, pass `disabled` to turn off using seed')

config = p.parse_args()

print(config)
print("----------")
print(p.format_help())
print("----------")
print(p.format_values())
