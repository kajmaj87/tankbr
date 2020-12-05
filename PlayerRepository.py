from gamecomponents import PlayerInfo
from ai import monkeyAI, dummyAI, dummyRotatorAI, rotatorAI, fastAndSlowRotatorAI

import random

from networks import neuralAI


class PlayerRepository:
    def __init__(self):
        self.players = []

    def generatePlayers(self, number, includeHumanPlayer=False):
        result = []
        nonNNAis = {
            "monkey": monkeyAI,
            "dummy": dummyAI,
            "dummyRotator": dummyRotatorAI,
            "rotator": rotatorAI,
            "fastRotator": fastAndSlowRotatorAI,
        }
        nnAis = {i: neuralAI(i) for i in range(number - 5)}
        ais = {**nonNNAis, **nnAis}
        for i in range(number):
            if includeHumanPlayer and i == 0:
                playerInfo = PlayerInfo(name="<<Player>>")
            else:
                aiName, aiBrain = list(ais.items())[i % len(ais)]
                playerInfo = PlayerInfo(name="Tank-{}->{}".format(i, aiName), ai=aiBrain)
            result.append(playerInfo)
        return result

    def setPlayers(self, players):
        self.players = players

    def fetchPlayers(self, sort=True):
        if sort:
            return sorted(self.players, key=lambda p: 50 if p.rank is None else -p.rank)
        else:
            return self.players
