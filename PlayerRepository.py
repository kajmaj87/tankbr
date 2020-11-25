from gamecomponents import PlayerInfo
from ai import monkeyAI, rotatorAI, fastAndSlowRotatorAI

import random


class PlayerRepository:
    def __init__(self):
        self.players = []

    def generatePlayers(self, number, includeHumanPlayer=False):
        result = []
        ais = {"monkey": monkeyAI, "rotator": rotatorAI, "fastRotator": fastAndSlowRotatorAI}
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
