import configargparse

p = configargparse.ArgParser(default_config_files=["config"])
p.add("-c", "--config", is_config_file=True, help="config file path with defaults")
p.add("-r", "--rounds", type=int, help="how many full rounds to generate. round means (players/match_size) matches")
p.add("-m", "--match_size", type=int, help="how many players should take part in one match")
p.add(
    "-s",
    "--matching_spread",
    type=int,
    help="how far (in terms of match size) should players be sampled from. If you use 1 then no sampling will be made and players of most similar skill will play together",
)
p.add("-p", "--players", type=int, help="how many players to genarate")
p.add("--include_human_player", action="store_true", help="true to allow human player to play")
p.add("--random_seed", help="random seed to use, pass `disabled` to turn off using seed")
p.add("-g", "--gen_min_sigma", type=float, help="minimum rank certainty before being kicked out of tournament")
p.add("-q", "--gen_worst_quantile", type=float, help="amount of worst players considered to be kicked out after each round")

p.add("--gui_draw", action="store_true", help="draw all matches in game")
p.add("--gui_draw_best_match", action="store_true", help="always draw the best match")
p.add("--gui_draw_worst_match", action="store_true", help="always draw the worst match")
p.add("--gui_max_fps", type=int)
p.add(
    "--gui_resolution",
    action="append",
    type=int,
    help="you need to pass this argument twice from command line first specifying x value then y. Better use config file for this",
)
p.add(
    "--gui_zoom",
    type=float,
    help="zoom factor at start of game. You can use mousescroll to change zoom during the game.",
    default=1,
)
p.add("--gui_zoom_change_factor", type=float, help="determines how fast zoom changes when scrolling")
p.add("--gui_offset_x", type=float, help="how much viewport should be offset horizontally when starting the game")
p.add("--gui_offset_y", type=float, help="how much viewport should be offset vertically when starting the game")

p.add("--game_frag_score", type=float, help="score for every kill")
p.add("--game_last_man_score", type=float, help="score if only you survive")
p.add(
    "--game_survived_score",
    type=float,
    help="max additional score you can get if you survive till the end of the match. Score given is proportional to time lived.",
)
p.add("--game_spawn_range", type=int, help="players will be spawn in a square of 2*spawn_range around (0,0)")
p.add("--game_movement_speed", type=int, help="what is the max speed that tanks move per game turn")
p.add("--game_rotation_speed", type=int, help="what is the max speed of rotation (turret and body) per game turn")
p.add("--game_gun_load_time", type=int, help="how many turns it takes to load a gun")
p.add("--game_ammo", type=int, help="how much ammo in reserve every player has (all players start with a loaded gun)")
p.add("--game_bullet_speed", type=int, help="how fast a turn each bullet goes")
p.add("--game_bullet_position_offset", type=int, help="how far from player does the bullet spawn - needed ")
p.add("--game_bullet_ttl", type=int, help="how many turns till the bullet will disappear")
p.add("--game_laser_range", type=int, help="maximum detection range of the lasers")
p.add("--game_max_match_turns", type=int, help="how many turns one match may last")

config = p.parse_args()

# some calculated values are added here:
config.game_survive_score_per_turn = config.game_survived_score / config.game_max_match_turns

print(config)
print("----------")
print(p.format_help())
print("----------")
print(p.format_values())
