import math

from gamecomponents import PlayerInfo
from ai import monkeyAI, dummyAI, dummyRotatorAI, rotatorAI, fastAndSlowRotatorAI

import random

from networks import neuralAI


class PlayerRepository:
    def __init__(self):
        self.players = []
        self.generatedPlayers = 0

    def generateHumanPlayer(self):
        return [PlayerInfo(name="<<Player>>")]

    def genarateAIPlayers(self):
        nonNNAis = {
            "monkey": monkeyAI,
            "dummy": dummyAI,
            "dummyRotator": dummyRotatorAI,
            "rotator": rotatorAI,
            "fastRotator": fastAndSlowRotatorAI,
        }
        return [PlayerInfo(name="Tank-{}".format(aiName), ai=aiBrain) for aiName, aiBrain in nonNNAis.items()]

    def generateNNAIPlayers(self, number):
        uptoNumber = self.generatedPlayers + number
        nnAis = {i: neuralAI(i) for i in range(self.generatedPlayers, uptoNumber)}
        self.generatedPlayers = uptoNumber
        return [PlayerInfo(name="Tank-{}".format(aiName), ai=aiBrain) for aiName, aiBrain in nnAis.items()]

    def generatePlayers(self, number, includeAIs=True, includeHumanPlayer=False):
        result = []
        if includeHumanPlayer:
            result = result + self.generateHumanPlayer()
        if includeAIs:
            result = result + self.genarateAIPlayers()
        self.generatedPlayers += len(result)
        if len(result) < number:
            result = result + self.generateNNAIPlayers(number - len(result))
        return result

    def setPlayers(self, players):
        self.players = players

    def removeWorstPlayers(self, minSigma, quantile=0.1):
        possiblePlayersToRemove = math.floor(len(self.players) * quantile)
        if possiblePlayersToRemove > 0:
            eligiblePlayers = self.sortPlayers(self.players)[-possiblePlayersToRemove:]
        else:
            return 0
        playersToRemove = self.sortPlayers([p for p in eligiblePlayers if p.sigma is not None and p.sigma < minSigma])
        self.players = [p for p in self.players if p not in playersToRemove]
        return playersToRemove

    def fetchPlayers(self, sort=False):
        if sort:
            return self.sortPlayers(self.players)
        else:
            return self.players

    def sortPlayers(self, players):
        return sorted(players, key=lambda p: 50 if p.rank is None else -p.rank)
