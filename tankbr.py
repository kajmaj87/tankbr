#!/usr/bin/env python
# -*- coding: utf-8 -*-

# RoadMap:
# - [ ] v0.x
#   - [ ] Multihostprocessing
# - [ ] v0.6
#   - [ ] Multiprocessing
# - [ ] v0.5
#   - [ ] Genetic mutations for NN Ai
#   - [ ] Simple NeuralNet AI
# - [X] v0.4
#   - [X] Tournaments
#   - [X] Seeding and game end checksums (replay functionality)
#   - [X] Optimization round
#   - [X] Code cleanup
#   - [X] Headless simulations
#   - [X] More different AIs
#   - [?] More rangefinders as input for AI (include constant input and random input also?)
# - [X] v0.3.1
#   - [X] Game End adds points depending on conditions (+tests)
# - [X] v0.3
#   - [X] Names
#   - [X] Zooming & Screen dragging
#   - [X] Scoring
#   - [X] Game End conditions
# Refactors & Ideas:
# - [ ] Separate Gun and change child to Mount (mount just moves around with parent)
# - [ ] Change all Move, Rotate etc to Commands
# Quality of life and bugs:
# - [ ] Player in different color
# - [ ] Countdown on start
# - [ ] Generating stating positions without overlap


import random

import esper
import pygame

import create
from PlayerRepository import PlayerRepository
from argparser import config
from gamecomponents import (
    InputEvents,
)
from gui import InputEventProcessor, RenderProcessor, InputEventCollector
from logic import (
    GameEndProcessor,
    AIProcessor,
    DecisionProcessor,
    CollisionProcessor,
    TotalScoreProcessor,
    MovementProcessor,
    RotationProcessor,
    RangeFindingProcessor,
    VelocityProcessor,
    FiringGunProcessor,
    CleanupProcessor,
    GunReloadProcessor,
)
from ranking import processRanks


def printScoresAndRankings(players):
    formatHeaders = "{:>25} | {:>3} | {:>6} | {:>5} | {:>4} | {:>4} | {:>5} |"
    formatScores = "{:>25} | {:>3} | {:>6} | {:>5.1f} | {:>4.1f} | {:>4.1f} | {:>5.2f} |"
    print(formatHeaders.format("Name", "#", "#Games", "Score", "Rank", "Mu", "Sigma"))
    for place, p in enumerate(sorted(players, key=lambda x: 50 if x.rank is None else -x.rank)):
        rank = -50 if p.rank is None else p.rank
        mu = -50 if p.mu is None else p.mu
        sigma = -50 if p.sigma is None else p.sigma
        print(formatScores.format(p.name, place, p.totalGames, p.score, rank, mu, sigma))


def initWorld():
    world = esper.World()
    events = world.create_entity()
    world.add_component(events, InputEvents())
    return world, events


def prepareProcessors(world, events, drawUI=True):
    gameEndProcessor = GameEndProcessor(turnsLeft=config.game_max_match_turns, ammoTimeout=config.game_bullet_ttl)
    world.add_processor(AIProcessor())
    world.add_processor(DecisionProcessor())
    world.add_processor(gameEndProcessor)
    world.add_processor(CollisionProcessor())
    world.add_processor(
        TotalScoreProcessor(
            gameEndProcessor=gameEndProcessor,
            survivorScore=config.game_survived_score / config.game_max_match_turns,
            lastManStandingScore=config.game_last_man_score,
        )
    )
    world.add_processor(MovementProcessor())
    world.add_processor(RotationProcessor())
    world.add_processor(RangeFindingProcessor())
    world.add_processor(VelocityProcessor())
    world.add_processor(FiringGunProcessor())
    world.add_processor(CleanupProcessor())
    world.add_processor(GunReloadProcessor())
    if drawUI:
        world.add_processor(RenderProcessor())
        world.add_processor(InputEventCollector(events))
        world.add_processor(InputEventProcessor(gameEndProcessor))
    return gameEndProcessor


def simulateGame(players, draw):
    world, events = initWorld()
    create.tanks(world, players)
    gameEndProcessor = prepareProcessors(world, events, drawUI=draw)

    while gameEndProcessor.isGameRunning():
        # A single call to world.process() will update all Processors:
        world.process()
    # rankedPlayers = processRanks([p[1] for p in world.get_component(PlayerInfo)])
    rankedPlayers = processRanks(players)
    for p in rankedPlayers:
        p.totalGames += 1
    return rankedPlayers


def run():
    if config.random_seed is not None and config.random_seed != "disabled":
        random.seed(config.random_seed)

    playerRepository = PlayerRepository()
    players = playerRepository.generatePlayers(number=config.players, includeHumanPlayer=config.include_human_player)
    playerRepository.setPlayers(players)
    randomize = False
    for i in range(config.rounds):
        players = playerRepository.fetchPlayers()
        for j in range(config.players // config.match_size):
            if randomize:
                nextMatchPlayers = random.sample(players, config.match_size)
            else:
                nextMatchPlayers = players[j * config.match_size : (j + 1) * config.match_size]
            print("Starting match from round {} for group {}".format(i, j))

            simulateGame(nextMatchPlayers, j==0)
            for p in players:
                p.score = 0
        print("Rankings after {} round:".format(i))
        printScoresAndRankings(players)

    printScoresAndRankings(players)


if __name__ == "__main__":
    run()
    pygame.quit()
