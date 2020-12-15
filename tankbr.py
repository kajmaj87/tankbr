#!/usr/bin/env python
# -*- coding: utf-8 -*-

# RoadMap:
# - [ ] v0.x
#   - [ ] Multihostprocessing
# - [ ] v0.6
#   - [ ] Multiprocessing
# - [ ] v0.5
#   - [X] Genetic mutations for NN Ai
#   - [X] Simple NeuralNet AI
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
import numpy as np
import math

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
from network_processor import make_child
from ranking import processRanks

totalRemoved = []


def printScoresAndRankings(round, players, removed, quantile):
    global totalRemoved
    formatHeaders = "{:>25} | {:>3} | {:>6} | {:>5} | {:>4} | {:>4} | {:>5} |"
    formatScores = "{:>25} | {:>3} | {:>6} | {:>5.1f} | {:>4.1f} | {:>4.1f} | {:>5.2f} |"
    print(formatHeaders.format("Round " + str(round), "#", "#Games", "Score", "Rank", "Mu", "Sigma"))
    cutoff = math.floor(len(players) * (1 - quantile))
    for place, p in enumerate(sorted(players, key=lambda x: 50 if x.rank is None else -x.rank)):
        rank = -50 if p.rank is None else p.rank
        mu = -50 if p.mu is None else p.mu
        sigma = -50 if p.sigma is None else p.sigma
        print(formatScores.format(p.name, place, p.totalGames, p.score, rank, mu, sigma))
        if cutoff == place:
            totalRemoved = (totalRemoved + removed)[-10:]
            removedNames = [p.name + " ({})".format(p.totalGames) for p in totalRemoved]
            print("{} Died: {}".format("-" * 10, ",".join(removedNames).rjust(80, "-")))


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


def shouldDrawThisMatch(currentRound, currentMatch, totalMatches):
    return currentRound % config.gui_draw_every_nth_round == 0 and (
        config.gui_draw
        or (config.gui_draw_best_match and currentMatch == 0)
        or (config.gui_draw_worst_match and currentMatch == totalMatches - 1)
    )


def sampleBasedOnSigma(players, sampleSize):
    weights = [200 if p.sigma is None else p.sigma ** 2 for p in players]
    s = sum(weights)
    return np.random.choice(players, sampleSize, p=[w / s for w in weights], replace=False)


def run():
    if config.random_seed is not None and config.random_seed != "disabled":
        random.seed(config.random_seed)

    playerRepository = PlayerRepository()
    players = playerRepository.generatePlayers(number=config.players, includeHumanPlayer=config.include_human_player)
    playerRepository.setPlayers(players)
    totalMatches = config.players // config.match_size - (config.matching_spread - 1)
    for i in range(config.rounds):
        players = playerRepository.fetchPlayers(sort=True)
        for j in range(totalMatches):
            eligablePlayers = players[j * config.match_size : (j + config.matching_spread) * config.match_size]
            if config.matching_spread > 1:
                nextMatchPlayers = sampleBasedOnSigma(eligablePlayers, config.match_size)
            else:
                nextMatchPlayers = players[j * config.match_size : (j + 1) * config.match_size]
            # print("Starting match from round {} for group {}".format(i, j))

            simulateGame(nextMatchPlayers, shouldDrawThisMatch(i, j, totalMatches))
            for p in players:
                p.score = 0
        amountRemoved = playerRepository.removeWorstPlayers(
            quantile=config.gen_worst_quantile, minSigma=config.gen_min_sigma
        )
        newPlayers = []
        for n in range(len(amountRemoved)):
            players_with_nets = playerRepository.fetchPlayers(sort=True, filter=lambda p: p.neural_net is not None)
            parents = random.choices(
                players_with_nets,
                weights=range(len(players_with_nets), 0, -1),
                k=2,
            )
            child_nn = make_child(parents[0].neural_net, parents[1].neural_net)
            newPlayers.append(playerRepository.generateNNAIPlayer(child_nn))
        playerRepository.setPlayers(playerRepository.fetchPlayers() + newPlayers)
        printScoresAndRankings(i, players, amountRemoved, config.gen_worst_quantile)


if __name__ == "__main__":
    run()
    pygame.quit()
